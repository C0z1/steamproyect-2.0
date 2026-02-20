"""
main.py — SteamSense API entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from src.db.connection import init_db, get_db, close_db
from src.db.models import create_all_tables
from src.ml.model import get_model
from src.routes import games, prices, predict, sync, stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Iniciando SteamSense API...")

    init_db()                    # configura la ruta
    con = get_db()               # abre conexión del thread principal
    create_all_tables(con)       # crea tablas si no existen
    logger.info("✅ DuckDB listo")

    get_model()
    logger.info("✅ Modelo ML listo")

    if not settings.itad_api_key:
        logger.warning("⚠️  ITAD_API_KEY no configurada.")

    logger.info(f"✅ SteamSense API lista — modo: {settings.env}")
    yield

    close_db()
    logger.info("👋 SteamSense API detenida")


app = FastAPI(
    title="SteamSense API",
    description="ML predictor de momentos óptimos de compra en Steam",
    version="2.0.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,  # handles NaN → null automatically
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games.router)
app.include_router(prices.router)
app.include_router(predict.router)
app.include_router(sync.router)
app.include_router(stats.router)


@app.get("/", tags=["health"])
def root():
    return {"app": "SteamSense API", "version": "2.0.0", "status": "ok"}


@app.get("/health", tags=["health"])
def health():
    try:
        get_db().execute("SELECT 1").fetchone()
        db_status = "ok"
    except Exception:
        db_status = "error"

    model = get_model()
    model_status = "trained" if model._model is not None else "heuristic"

    return {"status": "ok", "db": db_status, "model": model_status, "env": settings.env}
