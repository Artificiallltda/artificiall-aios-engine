from fastapi import APIRouter, Request, BackgroundTasks
import logging
import platform
import asyncio
import re
import hashlib
import os
import uuid
from langchain_core.messages import HumanMessage, AIMessage

from src.config import settings
from src.core.engine import engine
from src.router.adapters.whatsapp import process_whatsapp_reply, send_whatsapp_message
from src.router.adapters.telegram import process_telegram_reply, send_telegram_message, safe_send_file

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

router = APIRouter()
logger = logging.getLogger(__name__)

# Controle de sessão e deduplicação
_session_counters: dict = {}
_user_locks: dict = {}

async def notify_vercel_dashboard(payload: dict):
    """Envia eventos de agentes de volta para o Dashboard Vercel"""
    if not settings.VERCEL_WEBHOOK_URL:
        return
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            await client.post(settings.VERCEL_WEBHOOK_URL, json=payload, timeout=5.0)
            logger.info(f"✅ Dashboard Vercel notificado: {payload.get('action')}")
    except Exception as e:
        logger.error(f"❌ Falha ao notificar Vercel: {e}")

def _get_thread_id(channel: str, user_id: str) -> str:
    key = f"{channel}_{user_id}"
    counter = _session_counters.get(key, 0)
    return f"{key}_s{counter}" if counter > 0 else key

def _get_user_lock(thread_key: str) -> asyncio.Lock:
    if thread_key not in _user_locks:
        _user_locks[thread_key] = asyncio.Lock()
    return _user_locks[thread_key]

async def execute_brain(user_id: str, text: str, channel: str = "whatsapp", status_callback=None, user_name: str = "User", media_data: dict = None):
    if not text: text = ""
    thread_key = _get_thread_id(channel, user_id)
    config = {"configurable": {"thread_id": thread_key, "user_name": user_name}}

    async with _get_user_lock(thread_key):
        try:
            brain = await engine.get_brain()
            initial_state = {
                "messages": [HumanMessage(content=text)],
                "user_id": str(user_id),
                "channel": channel,
                "user_input": text,
                "content": "",
                "media_context": (media_data.get("b64") if media_data else None),
                "delivered_files": []
            }

            STATUS_NODES = {
                "growth_researcher": "Pesquisando dados GEO e mercado... 🔍🌍",
                "growth_planner": "Estruturando estratégia AEO... 📋🚀",
                "growth_executor": "Gerando criativos e ativos... 🎨💻",
                "growth_analyst": "Analisando performance e leads... 📊🎯",
                "growth_sdr": "Varrendo o mercado por CEOs/CFOs... 🕵️‍♂️📈",
                "growth_closer": "Preparando abordagem de fechamento... 🤝💰",
                "growth_commerce": "Configurando fluxos de venda... 🛒⚡",
                "growth_auditor": "Auditando qualidade E-E-A-T... ⚖️🛡️",
                "growth_creative": "Refinando branding da campanha... 🎨✨",
                "growth_manager": "Coordenando canais e fluxos... 🕹️📢",
            }
            
            sent_etas = set()
            responses_pool = [] 

            async for event in brain.astream(initial_state, config=config):
                for node, state_update in event.items():
                    if node in STATUS_NODES and node not in sent_etas:
                        status_msg = STATUS_NODES[node]
                        if status_callback: await status_callback(status_msg)
                        sent_etas.add(node)
                        
                        # Notifica Dashboard Vercel IMEDIATAMENTE sobre o progresso
                        if settings.VERCEL_WEBHOOK_URL:
                            await notify_vercel_dashboard({
                                "agent": node,
                                "action": "status_update",
                                "user_id": user_id,
                                "content": status_msg
                            })

                    msgs = state_update.get("messages", [])
                    for m in msgs:
                        if not m.content: continue
                        content_str = str(m.content)
                        if hasattr(m, "type") and m.type == "ai" and len(content_str) > 10:
                            responses_pool.append({"node": node, "text": content_str})

            # SDR e Planner agora são prioridades para resposta direta
            priority_nodes = ["growth_analyst", "growth_executor", "growth_researcher", "growth_sdr", "growth_planner"]
            final_text = ""
            
            specialist_msgs = [r for r in responses_pool if r["node"] in priority_nodes]
            if specialist_msgs:
                final_text = max(specialist_msgs, key=lambda x: len(x["text"]))["text"]
            elif responses_pool:
                final_text = max(responses_pool, key=lambda x: len(x["text"]))["text"]
            else:
                final_text = "Processado com sucesso pelo Artificiall Growth Engine."

            all_ai_text = " ".join([r["text"] for r in responses_pool])
            file_tags = re.findall(r'<(?:SEND_FILE|SEND_AUDIO):([^>]+)>', all_ai_text)
            unique_files = list(dict.fromkeys([t.strip() for t in file_tags]))

            clean_response = re.sub(r'<(?:SEND_FILE|SEND_AUDIO):([^>]+)>', '', final_text).strip()
            
            is_weak_text = not clean_response or len(clean_response) < 40 or "tarefa" in clean_response.lower()
            if unique_files and is_weak_text:
                first_file = unique_files[0].lower()
                if first_file.endswith('.png') or first_file.endswith('.jpg'):
                    clean_response = "📸 **Criativo Gerado**\n\nA sua imagem de campanha está pronta. Confira abaixo!"
                elif first_file.endswith('.pdf'):
                    clean_response = "📄 **Relatório Estratégico**\n\nConsolidei a inteligência de mercado no PDF abaixo."
                else:
                    clean_response = "✨ **Arquivo Gerado**\n\nO material solicitado está pronto!"

            if clean_response:
                if channel == "telegram":
                    await send_telegram_message(user_id, clean_response)
                elif channel == "whatsapp":
                    await send_whatsapp_message(user_id, clean_response)

                # Notifica Dashboard Vercel (Loop de Feedback)
                if settings.VERCEL_WEBHOOK_URL:
                    await notify_vercel_dashboard({
                        "agent": "Orion (Growth)",
                        "action": "task_completed",
                        "user_id": user_id,
                        "content": clean_response
                    })

            for filename in unique_files:
                full_path = os.path.join(settings.DATA_OUTPUTS_PATH, filename)
                import time
                start_wait = time.time()
                file_ready = False
                while time.time() - start_wait < 15.0:
                    if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
                        file_ready = True
                        break
                    await asyncio.sleep(0.5)
                
                if file_ready:
                    if channel == "telegram":
                        await safe_send_file(user_id, full_path)
                    elif channel == "whatsapp":
                        from src.router.adapters.whatsapp import safe_send_whatsapp_file
                        await safe_send_whatsapp_file(user_id, full_path)

            return None 

        except Exception as e:
            logger.error(f"Erro no execute_brain: {e}", exc_info=True)
            return f"Erro de processamento: {str(e)}"

@router.post("/trigger")
async def trigger_agent(request: Request, background_tasks: BackgroundTasks):
    """Gatilho direto via API (Dashboard Vercel)"""
    try:
        body = await request.json()
        agent_id = body.get("agent_id", "@aios-master")
        command = body.get("command", "")
        user_id = body.get("user_id", "dashboard_admin")
        
        if not command:
            return {"status": "error", "message": "Command is required"}

        async def run_trigger():
            await execute_brain(
                user_id=user_id, 
                text=f"{agent_id} {command}", 
                channel="api",
                user_name="Dashboard"
            )

        background_tasks.add_task(run_trigger)
        return {"status": "triggered", "agent": agent_id, "command": command}
    except Exception as e:
        logger.error(f"Erro no trigger_agent: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/telegram/webhook")
async def receive_telegram(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    if "message" not in body: return {"status": "ignored"}
    msg = body["message"]
    chat_id = str(msg.get("chat", {}).get("id", ""))
    user_name = msg.get("from", {}).get("first_name", "User")
    text = msg.get("text", "") or msg.get("caption", "")
    if not chat_id: return {"status": "ignored"}
    async def status_callback(m: str): await send_telegram_message(chat_id, f"<i>{m}</i>")
    async def run_pipeline():
        result = await execute_brain(user_id=chat_id, text=text, channel="telegram", status_callback=status_callback, user_name=user_name)
        if result:
            await send_telegram_message(chat_id, result)
    background_tasks.add_task(run_pipeline)
    return {"status": "queued"}

@router.post("/webhook/leads")
async def receive_generator_leads(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        leads = body.get("leads", [])
        source = body.get("source", "gerador_local")

        if not leads: return {"status": "ignored"}

        def process_and_insert_leads():
            if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY or not create_client:
                return

            try:
                supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
                for lead in leads:
                    db_lead = {
                        "company_name": str(lead.get("nome", "N/A")),
                        "status": "Scraping / Identified",
                        "source": str(source),
                        "website": str(lead.get("site", "")),
                        "phone": str(lead.get("telefone", "")),
                        "email": str(lead.get("email", "")),
                        "address": str(lead.get("endereco", "")),
                        "rating": str(lead.get("rating", "0.0")),
                        "raw_data": lead
                    }
                    supabase.table("leads").insert(db_lead).execute()
            except Exception as e:
                logger.error(f"Erro Supabase: {e}")

        background_tasks.add_task(process_and_insert_leads)
        return {"status": "success", "criados": len(leads)}
    except Exception as e:
        return {"status": "error", "error": str(e)}
