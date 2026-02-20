"""
src/routes/predict.py
=====================
Endpoints de predicción ML.
"""

from fastapi import APIRouter, HTTPException, Query

from src.services import predict_service

router = APIRouter(prefix="/predict", tags=["predict"])


@router.get("/{game_id}")
def predict(
    game_id: str,
    force_refresh: bool = Query(False, description="Ignorar cache y recalcular"),
):
    """
    Predicción ML: ¿Es buen momento para comprar este juego?

    Retorna:
    - score (0–100): mayor = mejor momento
    - signal: "BUY" | "WAIT"
    - reason: explicación legible
    - price_context: precio actual vs histórico
    """
    try:
        return predict_service.get_prediction(game_id, force_refresh=force_refresh)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
