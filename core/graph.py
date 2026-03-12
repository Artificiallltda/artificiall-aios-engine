import os
import re
import logging
import asyncio
import json
from datetime import datetime
from typing import Literal, Optional, List, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from core.state import AgentState
from tools.basic_tools import get_current_time
from tools.web_search import search_web
from tools.web_reader import read_url
from tools.document_reader import read_document
from tools.doc_generator import generate_docx, generate_pdf
from tools.code_executor import execute_python_code
from tools.memory_tools import save_memory, search_memory
from tools.chefia_integration import ask_chefia
from tools.image_generator import generate_image
from tools.data_analyst import analyze_data_file
from tools.scheduler_tools import schedule_reminder
from tools.pptx_generator import generate_pptx
from tools.database_tools import audit_supabase_security, audit_database_schema
from tools.audio_generator import generate_audio
from tools.rag_tools import query_knowledge_base, upload_document_to_knowledge_base
from tools.excel_tools import create_excel, append_to_excel, read_excel
from core.capabilities import can_agent_generate, get_agent_for_file_type
from core.agents.growth_analyst import arth_analyst_processor
from config import settings

logger = logging.getLogger(__name__)

# --- Setup dos Modelos ---
# Using GPT-4o for supervisor (Orchestrator) and DeepSeek for specialists
supervisor_llm = ChatOpenAI(model="gpt-4o", temperature=0)
deepseek_llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=settings.DEEPSEEK_API_KEY,
    openai_api_base="https://api.deepseek.com",
    temperature=0.3
)
executor_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def load_persona(agent_filename: str) -> str:
    path = os.path.join(settings.SQUAD_PATH, agent_filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            persona = f.read()
    except FileNotFoundError:
        persona = f"VocÃª Ã© o agente {agent_filename}."

    # Injeta MemÃ³ria Compartilhada (DossiÃª de ReputacaÃ§o)
    # EVITA injetar o entity-registry.yaml que Ã© gigante
    shared_memory_path = os.path.join(settings.BASE_DIR, ".aios-core", "data", "ai-reputation-dossier.md")
    shared_content = ""
    if os.path.exists(shared_memory_path):
        try:
            with open(shared_memory_path, "r", encoding="utf-8") as f:
                shared_content = f.read()
        except: pass

    if shared_content:
        # Trunca para seguranÃ§a (max ~30k tokens de contexto fixo)
        safe_shared = shared_content[:100000] 
        return f"{persona}\n\n### CONTEXTO COMPARTILHADO (MEMÃ“RIA DO SQUAD):\n{safe_shared}"
    
    return persona

def create_specialist_agent(tools, system_prompt: str, model_instance):
    safe_tools = [t for t in tools if t is not None]
    return create_react_agent(model=model_instance, tools=safe_tools, prompt=system_prompt)

# Agentes
researcher_agent = create_specialist_agent([search_web, read_url, read_document, search_memory, save_memory, query_knowledge_base], load_persona("growth-researcher.md"), deepseek_llm)
planner_agent = create_specialist_agent([get_current_time, search_memory, save_memory, schedule_reminder], load_persona("growth-planner.md"), deepseek_llm)
analyst_agent = create_specialist_agent([analyze_data_file, read_document, read_excel, audit_supabase_security, audit_database_schema, search_memory, save_memory], load_persona("growth-analyst.md"), deepseek_llm)
executor_agent = create_specialist_agent([
    get_current_time, execute_python_code, save_memory, search_memory, 
    ask_chefia, generate_image, generate_audio, upload_document_to_knowledge_base,
    generate_docx, generate_pdf, generate_pptx, create_excel, append_to_excel
], load_persona("growth-executor.md"), executor_llm)

async def agent_node(state, agent, name):
    messages = list(state.get("messages", []))
    result = await agent.ainvoke({**state, "messages": messages}, RunnableConfig(recursion_limit=50))
    msg = result["messages"][-1]

    if not isinstance(msg.content, str):
        msg = msg.model_copy(update={"content": str(msg.content)})

    tool_messages = [m for m in result["messages"] if getattr(m, "type", "") == "tool"]
    tool_text = " ".join(str(m.content) for m in tool_messages)
    file_tags = re.findall(r'<(?:SEND_FILE|SEND_AUDIO):([^>]+)>', tool_text)
    
    msg_content = msg.content
    for tag in file_tags:
        t_str = f"<SEND_FILE:{tag}>"
        if t_str not in msg_content: msg_content += f"\n{t_str}"
        
    msg = msg.model_copy(update={"content": msg_content, "name": name})

    return {
        "messages": [msg],
        "sender": name,
        "content": state.get("content", ""),
        "user_input": state.get("user_input", "")
    }

async def researcher_node(state): return await agent_node(state, researcher_agent, "growth_researcher")
async def planner_node(state): return await agent_node(state, planner_agent, "growth_planner")
async def executor_node(state): return await agent_node(state, executor_agent, "growth_executor")
async def analyst_node(state): 
    updated_state = await arth_analyst_processor(state)
    return await agent_node(updated_state, analyst_agent, "growth_analyst")

# --- Supervisor ---
members = ["growth_researcher", "growth_planner", "growth_executor", "growth_analyst"]
class RouteResponse(BaseModel):
    next_agent: Literal["FINISH", "growth_researcher", "growth_planner", "growth_executor", "growth_analyst"]
    final_answer: str = ""

orchestrator_persona = load_persona("orchestrator.md")
prompt = ChatPromptTemplate.from_messages([
    ("system", orchestrator_persona),
    MessagesPlaceholder(variable_name="messages"),
    ("system", "Quem deve atuar agora? Escolha um de: {members} ou FINISH."),
]).partial(members=str(members))

supervisor_chain = prompt | supervisor_llm.with_structured_output(RouteResponse)

async def supervisor_node(state: AgentState):
    messages = list(state.get("messages", []))
    last_human_idx = max((i for i, m in enumerate(messages) if m.type == "human"), default=0)
    msgs_this_turn = messages[last_human_idx + 1:]
    
    specialist_runs = {}
    has_file = False
    for m in msgs_this_turn:
        if m.type == "ai" and getattr(m, "name", "") in members:
            specialist_runs[m.name] = specialist_runs.get(m.name, 0) + 1
            if "<SEND_FILE:" in str(m.content): has_file = True

    if has_file and specialist_runs.get("growth_executor", 0) > 0:
        return {"next_agent": "FINISH"}

    short_messages = messages[-15:]
    routing_result = await supervisor_chain.ainvoke({**state, "messages": short_messages})
    
    ret = {"next_agent": routing_result.next_agent}
    
    if routing_result.next_agent == "FINISH" and routing_result.final_answer:
        msg = AIMessage(content=routing_result.final_answer, name="growth_orchestrator")
        ret["messages"] = [msg]

    return ret

def build_growth_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("growth_orchestrator", supervisor_node)
    workflow.add_node("growth_researcher", researcher_node)
    workflow.add_node("growth_planner", planner_node)
    workflow.add_node("growth_executor", executor_node)
    workflow.add_node("growth_analyst", analyst_node)
    workflow.add_edge(START, "growth_orchestrator")
    for member in members: workflow.add_edge(member, "growth_orchestrator")
    workflow.add_conditional_edges("growth_orchestrator", lambda state: state["next_agent"], {k: k for k in members} | {"FINISH": END})
    return workflow
