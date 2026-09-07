"""Monitoring & Model Registry API routes."""

from fastapi import APIRouter
from app.monitoring.metrics import monitoring_manager
from app.monitoring.model_registry import model_registry

router = APIRouter(prefix="/api", tags=["monitoring"])


@router.get("/models")
async def list_models():
    """Returns the UAMD model registry with versions, modalities, and verified metrics."""
    return {
        "models": model_registry.list_models(),
        "total": len(model_registry.list_models()),
    }


@router.get("/monitoring")
async def get_system_metrics():
    """Returns real-time inference latency, throughput, and risk score distributions."""
    return monitoring_manager.get_metrics_summary()
