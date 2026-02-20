import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.ingest import router as ingest_router
from app.api.monitoring import router as monitoring_router
from app.api.pairing import router as pairing_router
from app.api.devices import router as devices_router
from app.redis.client import redis_client
from app.db.session import db_manager
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.logging import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up application...")
    await db_manager.connect()
    
    yield
    # Shutdown
    logger.info("Shutting down application...")
    await redis_client.close()
    await db_manager.disconnect()

app = FastAPI(
    title="Glitch Hunt Ingestion API",
    version="1.0.0",
    lifespan=lifespan
)

# Prometheus Instrumentation
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=[".*admin.*", "/metrics"],
    inprogress_name="inprogress",
    inprogress_labels=True,
)
instrumentator.instrument(app)

# Include Routers
app.include_router(ingest_router, prefix="/v1/ingest", tags=["Ingest"])
app.include_router(pairing_router, prefix="/v1/pairing", tags=["Pairing"])
app.include_router(devices_router, prefix="/v1/devices", tags=["Devices"])
app.include_router(monitoring_router, tags=["Monitoring"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug",
    )