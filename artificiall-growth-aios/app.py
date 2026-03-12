import logging
import uvicorn
from fastapi import FastAPI, Query, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager
from src.router.message_handler import router as message_router, execute_brain
from src.scheduler.reminder_worker import scheduler, load_pending_reminders
from src.core.engine import engine
from src.utils.log_buffer import setup_log_buffer, get_logs_json, get_logs_text
from src.config import settings

from fastapi.middleware.cors import CORSMiddleware

# ─── Logging Config ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
setup_log_buffer(root_level=logging.DEBUG)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[SERVER] Iniciando Artificiall Growth Engine...")
    scheduler.start()
    load_pending_reminders()
    yield
    logger.info("[SERVER] Encerrando conexões graciosamente...")
    await engine.cleanup()
    scheduler.shutdown()

app = FastAPI(title="Artificiall Growth Engine", version="1.0.3", lifespan=lifespan)

# Ativa CORS Total
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 [GROWTH ENGINE] Squad de 10 Agentes Ativo!")

# ROTA CRÍTICA: Trigger Direto (Fix 404)
@app.post("/trigger")
async def trigger_agent_direct(request: Request, background_tasks: BackgroundTasks):
    """Gatilho direto via API (Dashboard Vercel) - Injetado no app principal"""
    try:
        body = await request.json()
        agent_id = body.get("agent_id", "@growth-orchestrator")
        command = body.get("command", "")
        user_id = body.get("user_id", "dashboard_admin")
        
        logger.info(f"⚡ [TRIGGER] Recebido comando para {agent_id}: {command}")

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
        logger.error(f"❌ [TRIGGER] Erro: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/health")
async def health():
    return {"status": "alive", "engine": "Artificiall Growth", "version": "1.0.3"}

@app.get("/")
async def root():
    return {"status": "ok", "service": "Artificiall Growth Engine"}

# Inclui o restante das rotas (Telegram, Webhooks de Leads, etc.)
app.include_router(message_router)

@app.get("/logs", response_class=PlainTextResponse)
async def view_logs(
    n: int = Query(default=60, description="Número de entradas"),
    level: str = Query(default=None, description="Filtro"),
    fmt: str = Query(default="text", description="Formato"),
):
    if fmt == "json":
        from fastapi.responses import JSONResponse
        return JSONResponse(content=get_logs_json(n=n, level=level))
    return get_logs_text(n=min(n, 100))

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
