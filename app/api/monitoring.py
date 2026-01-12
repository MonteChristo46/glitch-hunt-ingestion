import os
from fastapi import APIRouter, Response
from prometheus_client import multiprocess, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST, REGISTRY

router = APIRouter()

@router.get("/metrics")
def metrics():
    if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        data = generate_latest(registry)
    else:
        data = generate_latest(REGISTRY)
    
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "glitch-hunt-ingestion"}

@router.get("/")
def root_health_check():
    """Legacy root health check for convenience."""
    return {"status": "ok", "service": "glitch-hunt-ingestion"}
