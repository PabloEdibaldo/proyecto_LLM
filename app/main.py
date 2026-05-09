from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.endpoints import router
from app.core.cache import redis_cache
from app.core.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to Redis
    logger.info("Starting up application...")
    await redis_cache.connect()
    yield
    # Shutdown: Disconnect from Redis
    logger.info("Shutting down application...")
    await redis_cache.disconnect()

app = FastAPI(
    title="Market Research Assistant API",
    description="A multi-agent market research system using FastAPI, LangChain, and LangGraph.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to the Market Research Assistant API. Go to /docs for Swagger UI."}
