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
from src.db.models import create_all_tables, create_user_tables
from src.ml.model import get_model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando SteamSense API...")

    init_db()           # solo configura _db_path, no abre conexión
    con = get_db()      # abre la conexión del main thread
    create_all_tables(con)
    create_user_tables(con)
    logger.info("DuckDB listo")

    get_model()
    logger.info("Modelo ML listo")

    if not settings.itad_api_key:
        logger.warning("ITAD_API_KEY no configurada")
    if not settings.steam_api_key:
        logger.warning("STEAM_API_KEY no configurada — login con Steam deshabilitado")

    logger.info(f"SteamSense API lista — modo: {settings.env}")
    yield

    close_db()
    logger.info("SteamSense API detenida")


app = FastAPI(
    title="SteamSense API",
    description="ML predictor de momentos optimos de compra en Steam",
    version="2.0.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers here (after app creation) to avoid circular import issues
from src.routes import games, prices, predict, sync, stats, auth, user  # noqa: E402

app.include_router(games.router)
app.include_router(prices.router)
app.include_router(predict.router)
app.include_router(sync.router)
app.include_router(stats.router)
app.include_router(auth.router)
app.include_router(user.router)


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

    return {
        "status": "ok",
        "db": db_status,
        "model": model_status,
        "env": settings.env,
        "steam_auth": "enabled" if settings.steam_api_key else "disabled",
    }