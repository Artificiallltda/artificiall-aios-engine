import logging
import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager
from src.router.message_handler import router as message_router
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

app = FastAPI(title="Artificiall Growth Engine", version="1.0.2", lifespan=lifespan)

# Ativa CORS
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

# Rota de Health Check simplificada
@app.get("/health")
async def health():
    return {"status": "alive", "engine": "Artificiall Growth", "version": "1.0.2"}

# Rota Raiz
@app.get("/")
async def root():
    return {"status": "ok", "service": "Artificiall Growth Engine"}

# Inclui o roteador SEM prefixo para simplificar o Dashboard
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
