import redis.asyncio as redis
from app.core.config import settings
from app.core.logger import logger
import hashlib
import json
from typing import Optional, Any

class RedisCache:
    def __init__(self):
        self.redis_client = None

    async def connect(self):
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await self.redis_client.ping()
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    async def disconnect(self):
        if self.redis_client:
            await self.redis_client.close()

    def generate_key(self, query: str) -> str:
        """Generate a hash key for a given query."""
        return f"cache:query:{hashlib.sha256(query.encode()).hexdigest()}"

    async def get(self, query: str) -> Optional[dict]:
        if not self.redis_client:
            return None
        
        key = self.generate_key(query)
        try:
            cached_data = await self.redis_client.get(key)
            if cached_data:
                logger.info("Cache hit for query")
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Error reading from cache: {e}")
            
        return None

    async def set(self, query: str, response: dict, ttl_seconds: int = 3600):
        if not self.redis_client:
            return
            
        key = self.generate_key(query)
        try:
            await self.redis_client.setex(key, ttl_seconds, json.dumps(response))
            logger.info("Cached response for query")
        except Exception as e:
            logger.error(f"Error setting cache: {e}")

redis_cache = RedisCache()
