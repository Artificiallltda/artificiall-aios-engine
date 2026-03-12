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

from src.core.state import AgentState
from src.tools.basic_tools import get_current_time
from src.tools.web_search import search_web
from src.tools.web_reader import read_url
from src.tools.document_reader import read_document
from src.tools.doc_generator import generate_docx, generate_pdf
from src.tools.code_executor import execute_python_code
from src.tools.memory_tools import save_memory, search_memory
from src.tools.chefia_integration import ask_chefia
from src.tools.image_generator import generate_image
from src.tools.data_analyst import analyze_data_file
from src.tools.scheduler_tools import schedule_reminder
from src.tools.pptx_generator import generate_pptx
from src.tools.database_tools import audit_supabase_security, audit_database_schema
from src.tools.audio_generator import generate_audio
from src.tools.rag_tools import query_knowledge_base, upload_document_to_knowledge_base
from src.tools.excel_tools import create_excel, append_to_excel, read_excel
from src.core.capabilities import can_agent_generate, get_agent_for_file_type
from src.core.agents.growth_analyst import arth_analyst_processor
from src.config import settings

logger = logging.getLogger(__name__)

# --- Setup dos Modelos ---
supervisor_llm = ChatOpenAI(model="gpt-4o", temperature=0)
deepseek_llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=settings.DEEPSEEK_API_KEY,
    openai_api_base="https://api.deepseek.com",
    temperature=0.3
)
executor_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Gemini para agentes criativos ou especialistas de busca se necessário
gemini_llm = ChatGoogleGenerativeAI(model=settings.GEMINI_MODEL, google_api_key=settings.GEMINI_API_KEY)

def load_persona(agent_filename: str) -> str:
    path = os.path.join(settings.SQUAD_PATH, agent_filename)
    persona = ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            persona = f.read()
    except FileNotFoundError:
        logger.warning(f"[CORE] Persona não encontrada em {path}. Usando fallback.")
        persona = f"Você é o agente {agent_filename}."

    # --- INJEÇÃO DE MEMÓRIA COMPARTILHADA (Dossiê de Reputação) ---
    # Caminho ajustado para o squad de Growth v2
    shared_memory_path = os.path.join(settings.BASE_DIR, "squads", "squad-artificiall-growth-v2", "data", "ai-reputation-dossier.md")
    shared_content = ""
    if os.path.exists(shared_memory_path):
        try:
            with open(shared_memory_path, "r", encoding="utf-8", errors="replace") as f:
                shared_content = f.read()
        except Exception as e:
            logger.error(f"[CORE] Erro ao ler dossiê de reputação: {e}")

    if shared_content:
        # Garante que o dossiê não exceda um limite seguro de tokens (~30k chars)
        safe_shared = shared_content[:30000] 
        return f"{persona}\n\n### CONTEXTO COMPARTILHADO (MEMÓRIA DO SQUAD):\n{safe_shared}"
    
    return persona

def create_specialist_agent(tools, system_prompt: str, model_instance):
    safe_tools = [t for t in tools if t is not None]
    return create_react_agent(model=model_instance, tools=safe_tools, prompt=system_prompt)

# --- Instanciação dos 10 Agentes Growth ---

# 1. GEO Strategist (Pesquisador)
researcher_agent = create_specialist_agent(
    [search_web, read_url, read_document, search_memory, save_memory, query_knowledge_base], 
    load_persona("arth-geo-strategist.md"), 
    deepseek_llm
)

# 2. Content Strategist (Planejador)
planner_agent = create_specialist_agent(
    [get_current_time, search_memory, save_memory, schedule_reminder], 
    load_persona("arth-content-strategist.md"), 
    deepseek_llm
)

# 3. Performance Analyst (Analista)
analyst_agent = create_specialist_agent(
    [analyze_data_file, read_document, read_excel, audit_supabase_security, audit_database_schema, search_memory, save_memory, generate_pdf, generate_docx], 
    load_persona("arth-performance-analyst.md"), 
    deepseek_llm
)

# 4. AEO Content Architect (Executor)
executor_agent = create_specialist_agent([
    get_current_time, execute_python_code, save_memory, search_memory, 
    ask_chefia, generate_image, generate_audio, upload_document_to_knowledge_base,
    generate_docx, generate_pdf, generate_pptx, create_excel, append_to_excel
], load_persona("arth-aeo-content-architect.md"), executor_llm)

# 5. SDR Agent (Prospecção)
sdr_agent = create_specialist_agent(
    [search_web, read_url, search_memory, save_memory, schedule_reminder], 
    load_persona("arth-sdr-agent.md"), 
    deepseek_llm
)

# 6. Closer (Fechamento)
closer_agent = create_specialist_agent(
    [search_memory, save_memory, read_document, ask_chefia], 
    load_persona("arth-closer.md"), 
    deepseek_llm
)

# 7. Agentic Commerce Specialist (Vendas)
commerce_agent = create_specialist_agent(
    [search_web, read_url, audit_database_schema, search_memory], 
    load_persona("arth-agentic-commerce-specialist.md"), 
    deepseek_llm
)

# 8. E-E-A-T Auditor (Qualidade)
auditor_agent = create_specialist_agent(
    [search_web, read_document, query_knowledge_base], 
    load_persona("arth-e-eat-auditor.md"), 
    deepseek_llm
)

# 9. Creative Director (Branding)
creative_agent = create_specialist_agent(
    [generate_image, generate_pptx, search_memory], 
    load_persona("arth-creative-director.md"), 
    gemini_llm
)

# 10. Campaign Manager (Gestão)
manager_agent = create_specialist_agent(
    [get_current_time, schedule_reminder, search_memory, save_memory], 
    load_persona("arth-campaign-manager.md"), 
    deepseek_llm
)

# --- Nodes ---

async def agent_node(state, agent, name):
    messages = list(state.get("messages", []))
    
    # PROTEÇÃO DE MEMÓRIA EXPANDIDA (AUDITORIA ORION)
    # Aumentamos para 100 mensagens para garantir que pesquisas longas não sejam deletadas.
    if len(messages) > 100:
        messages = messages[-30:]
        logger.warning(f"[{name}] Histórico muito longo ({len(messages)} msgs). Aplicando poda de segurança moderada.")

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

    # --- PONTE DE DADOS DE FERRO ---
    # Acumula o conteúdo da resposta deste agente no campo 'content' do estado global
    # Isso garante que o executor de PDF/Docx receba todo o histórico acumulado.
    current_content = state.get("content", "")
    new_content = current_content
    if len(str(msg.content)) > 100: # Apenas acumula se for uma resposta substancial
        new_content += f"\n\n--- INFORMAÇÃO DO AGENTE {name.upper()} ---\n{msg.content}"

    return {
        "messages": [msg],
        "sender": name,
        "content": new_content,
        "user_input": state.get("user_input", "")
    }

async def researcher_node(state): return await agent_node(state, researcher_agent, "growth_researcher")
async def planner_node(state): return await agent_node(state, planner_agent, "growth_planner")
async def executor_node(state): return await agent_node(state, executor_agent, "growth_executor")
async def analyst_node(state): 
    updated_state = await arth_analyst_processor(state)
    return await agent_node(updated_state, analyst_agent, "growth_analyst")
async def sdr_node(state): return await agent_node(state, sdr_agent, "growth_sdr")
async def closer_node(state): return await agent_node(state, closer_agent, "growth_closer")
async def commerce_node(state): return await agent_node(state, commerce_agent, "growth_commerce")
async def auditor_node(state): return await agent_node(state, auditor_agent, "growth_auditor")
async def creative_node(state): return await agent_node(state, creative_agent, "growth_creative")
async def manager_node(state): return await agent_node(state, manager_agent, "growth_manager")

# --- Supervisor ---
members = [
    "growth_researcher", "growth_planner", "growth_executor", "growth_analyst",
    "growth_sdr", "growth_closer", "growth_commerce", "growth_auditor",
    "growth_creative", "growth_manager"
]

class RouteResponse(BaseModel):
    next_agent: Literal[
        "FINISH", "growth_researcher", "growth_planner", "growth_executor", "growth_analyst",
        "growth_sdr", "growth_closer", "growth_commerce", "growth_auditor",
        "growth_creative", "growth_manager"
    ]
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
    workflow.add_node("growth_sdr", sdr_node)
    workflow.add_node("growth_closer", closer_node)
    workflow.add_node("growth_commerce", commerce_node)
    workflow.add_node("growth_auditor", auditor_node)
    workflow.add_node("growth_creative", creative_node)
    workflow.add_node("growth_manager", manager_node)

    workflow.add_edge(START, "growth_orchestrator")
    
    for member in members: 
        workflow.add_edge(member, "growth_orchestrator")
    
    workflow.add_conditional_edges(
        "growth_orchestrator", 
        lambda state: state["next_agent"], 
        {k: k for k in members} | {"FINISH": END}
    )
    
    return workflow
