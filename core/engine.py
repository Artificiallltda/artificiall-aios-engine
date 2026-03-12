import logging
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from src.core.graph import build_growth_graph
from src.config import settings

logger = logging.getLogger(__name__)

class GrowthEngine:
    """
    Gerenciador do Ciclo de Vida do Grafo (Cérebro do Artificiall Growth).
    Implementa Singleton e persistência resiliente no Supabase.
    """
    _instance = None
    _brain = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GrowthEngine, cls).__new__(cls)
        return cls._instance

    async def get_brain(self):
        # Health-check: se o pool morreu, reconstrói o brain
        if self._brain is not None and self._pool is not None:
            try:
                async with self._pool.connection() as conn:
                    await conn.execute("SELECT 1")
            except Exception:
                logger.warning("[DB] Pool perdido detectado. Reconstruindo brain...")
                self._brain = None
                await self._pool.close()
                self._pool = None

        if self._brain is None:
            workflow = build_growth_graph()

            # Configurações universais de compilação
            compile_kwargs = {}

            # Persistência Cloud (Supabase / Postgres)
            if settings.SUPABASE_DATABASE_URL:
                try:
                    logger.info("[DB] Criando pool de conexões para Growth Engine...")
                    if self._pool is None:
                        self._pool = AsyncConnectionPool(
                            conninfo=settings.SUPABASE_DATABASE_URL,
                            max_size=20,
                            kwargs={
                                "autocommit": True,
                                "prepare_threshold": None,
                            },
                            open=False,
                        )
                        await self._pool.open()

                    checkpointer = AsyncPostgresSaver(self._pool)
                    await checkpointer.setup()
                    compile_kwargs["checkpointer"] = checkpointer
                    logger.info("[OK] Persistência Growth ativada via Supabase.")
                except Exception as e:
                    logger.error(f"[FAIL] Erro ao conectar no Supabase: {e}. Usando MemorySaver.")
                    compile_kwargs["checkpointer"] = MemorySaver()
            else:
                logger.warning("[!] Usando MemorySaver (volátil) para o Growth Engine.")
                compile_kwargs["checkpointer"] = MemorySaver()

            # Compila o grafo
            self._brain = workflow.compile(**compile_kwargs)
            logger.info("[OK] Cérebro Growth compilado com sucesso.")

        return self._brain

    async def cleanup(self):
        """Fecha o pool ao encerrar o servidor."""
        if self._pool is not None:
            await self._pool.close()
            logger.info("[DB] Pool de conexões encerrado.")

engine = GrowthEngine()
