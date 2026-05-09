from app.core.cache import redis_cache

async def get_cache():
    return redis_cache
