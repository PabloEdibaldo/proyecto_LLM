from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.endpoints import router
from app.core.cache import redis_cache
from app.core.structured_logger import logger, RequestContext
from app.core.middleware import RequestContextMiddleware, PrometheusMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to Redis and initialize session
    logger.info("Starting up application...")
    RequestContext.generate_session_id()
    await redis_cache.connect()
    yield
    # Shutdown: Disconnect from Redis
    logger.info("Shutting down application...")
    await redis_cache.disconnect()

app = FastAPI(
    title="Market Research Assistant API",
    description="A multi-agent market research system using FastAPI, LangChain, LangGraph, and Observability Stack.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# Add observability middleware (order matters)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(PrometheusMiddleware, group_paths=True)

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Market Research Assistant API",
        "docs": "/docs",
        "swagger": "/docs",
        "metrics": "/api/v1/metrics",
        "health": "/api/v1/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    return {"status": "healthy", "version": "1.0.0"}
