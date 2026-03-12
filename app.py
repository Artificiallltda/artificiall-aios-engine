import logging
import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from router.message_handler import router as message_router
from scheduler.reminder_worker import scheduler, load_pending_reminders
from core.engine import engine
from utils.log_buffer import setup_log_buffer, get_logs_json, get_logs_text

# ─── Logging Config ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
# Reduz ruído de libs externas
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("langchain").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("google").setLevel(logging.WARNING)

# Ativa buffer em memória com nível DEBUG para capturar tudo
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

app = FastAPI(title="Artificiall Growth Engine", version="1.0.0", lifespan=lifespan)

# --- CONFIGURAÇÃO DE CORS (LIBERA DASHBOARD VERCEL) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def log_resources():
    try:
        import psutil
        m = psutil.virtual_memory()
        logger.info(f"[INFRA] RAM: {m.percent}% | CPU: {psutil.cpu_percent()}%")
    except: pass

@app.middleware("http")
async def monitor_infra(request, call_next):
    log_resources()
    return await call_next(request)

app.include_router(message_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"status": "ok", "service": "Artificiall Growth Engine"}

@app.get("/api/v1/logs", response_class=PlainTextResponse)
async def view_logs(
    n: int = Query(default=60, description="Número de entradas"),
    level: str = Query(default=None, description="Filtro: ERROR, WARNING, INFO, DEBUG"),
    fmt: str = Query(default="text", description="Formato: text | json"),
):
    if fmt == "json":
        from fastapi.responses import JSONResponse
        return JSONResponse(content=get_logs_json(n=n, level=level))
    return get_logs_text(n=min(n, 100))

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
