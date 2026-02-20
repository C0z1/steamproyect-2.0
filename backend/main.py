"""
main.py
=======
Entry point de la aplicación FastAPI SteamSense.

Ciclo de vida:
  1. Startup: conectar DuckDB, crear tablas, cargar modelo ML
  2. Serve: FastAPI con todos los routes registrados
  3. Shutdown: cerrar DuckDB limpiamente

Arranque local:
  uvicorn main:app --reload --port 8000

Producción (Render.com):
  uvicorn main:app --host 0.0.0.0 --port $PORT
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from src.db.connection import init_db, close_db
from src.db.models import create_all_tables
from src.ml.model import get_model
from src.routes import games, prices, predict, sync

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──
    logger.info("🚀 Iniciando SteamSense API...")

    con = init_db()
    create_all_tables(con)
    logger.info("✅ DuckDB listo")

    get_model()  # precarga el modelo (o logea que usará heurística)
    logger.info("✅ Modelo ML listo")

    if not settings.itad_api_key:
        logger.warning("⚠️  ITAD_API_KEY no configurada. Los endpoints de sync no funcionarán.")

    logger.info(f"✅ SteamSense API lista en modo: {settings.env}")

    yield

    # ── Shutdown ──
    close_db()
    logger.info("👋 SteamSense API detenida")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SteamSense API",
    description="ML predictor de momentos óptimos de compra en Steam",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────

app.include_router(games.router)
app.include_router(prices.router)
app.include_router(predict.router)
app.include_router(sync.router)


# ── Health & root ─────────────────────────────────────────────────────────────

@app.get("/", tags=["health"])
def root():
    return {"app": "SteamSense API", "version": "2.0.0", "status": "ok"}


@app.get("/health", tags=["health"])
def health():
    from src.db.connection import get_db
    try:
        get_db().execute("SELECT 1").fetchone()
        db_status = "ok"
    except Exception:
        db_status = "error"

    from src.ml.model import get_model
    model = get_model()
    model_status = "trained" if model._model is not None else "heuristic"

    return {
        "status": "ok",
        "db": db_status,
        "model": model_status,
        "env": settings.env,
    }
