from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.ingest import router as ingest_router
from app.redis.client import redis_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Redis connection is lazy, so we don't strictly need to do anything here
    # unless we want to ping it to ensure connectivity.
    yield
    # Shutdown
    await redis_client.close()

app = FastAPI(
    title="Glitch Hunt Ingestion API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(ingest_router, prefix="/v1/ingest", tags=["Ingest"])

@app.get("/")
def health_check():
    return {"status": "ok", "service": "glitch-hunt-ingestion"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
