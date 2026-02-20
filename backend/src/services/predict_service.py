"""
src/services/predict_service.py
================================
Lógica de negocio para las predicciones ML.
Orquesta: DB → feature engineering → modelo → cache → respuesta.
"""

import logging

from src.db import queries
from src.db.connection import get_db
from src.ml.features import build_features
from src.ml.model import get_model, PredictionResult

logger = logging.getLogger(__name__)

CACHE_MAX_AGE_HOURS = 6


def get_prediction(game_id: str, force_refresh: bool = False) -> dict:
    """
    Genera o recupera del cache la predicción para un juego.

    Args:
        game_id:       ITAD game ID
        force_refresh: Si True, ignora el cache y recalcula

    Returns:
        Dict con score, signal, reason, confidence y metadata

    Raises:
        ValueError si el juego no existe o no hay datos suficientes
    """
    con = get_db()

    # 1. Verificar que el juego existe
    game = queries.get_game(con, game_id)
    if not game:
        raise ValueError(f"Juego no encontrado: {game_id}")

    # 2. Intentar cache
    if not force_refresh:
        cached = queries.get_cached_prediction(con, game_id, CACHE_MAX_AGE_HOURS)
        if cached:
            logger.debug(f"Cache hit para game_id={game_id}")
            return _format_response(game, cached["score"], cached["signal"],
                                    cached["reason"], 0.0, {}, from_cache=True)

    # 3. Cargar datos de precio
    stats = queries.get_price_stats(con, game_id)
    history = queries.get_price_history(con, game_id)
    seasonal = queries.get_seasonal_patterns(con, game_id)

    if not history or len(history) < 3:
        raise ValueError(f"Historial insuficiente para predecir ({len(history or [])} registros). Mínimo 3.")

    # 4. Construir features
    features = build_features(stats, history, seasonal)
    if not features:
        raise ValueError("No se pudieron construir features de predicción")

    # 5. Predecir
    model = get_model()
    result: PredictionResult = model.predict(features)

    # 6. Cachear resultado
    queries.upsert_prediction(
        con,
        game_id=game_id,
        score=result.score,
        signal=result.signal,
        reason=result.reason,
        features={k: v for k, v in features.items() if not k.startswith("_")},
    )

    return _format_response(
        game, result.score, result.signal, result.reason,
        result.confidence, result.features_used, from_cache=False
    )


def _format_response(game: dict, score: float, signal: str, reason: str,
                     confidence: float, features: dict, from_cache: bool) -> dict:
    """Formatea la respuesta de predicción para el frontend."""
    current_price = features.get("_current_price", 0)
    min_price = features.get("_min_price", 0)
    avg_price = features.get("_avg_price", 0)

    return {
        "game_id": game["id"],
        "title": game["title"],
        "appid": game.get("appid"),
        "prediction": {
            "score": score,
            "signal": signal,          # "BUY" | "WAIT"
            "reason": reason,
            "confidence": round(confidence, 2),
        },
        "price_context": {
            "current_price": current_price,
            "min_price_ever": min_price,
            "avg_price": avg_price,
            "current_discount_pct": features.get("current_discount_pct", 0),
        },
        "from_cache": from_cache,
    }
