import os
import json
import redis.asyncio as redis
from typing import Optional, Any
import sys

class CacheService:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.memory_cache = {}
        self.is_redis_enabled = False
        self.ttl_default = 3600  # 1 hour default

    async def connect(self):
        """Initialize Redis connection if URL is available"""
        redis_url = os.getenv("KV_URL") or os.getenv("REDIS_URL")
        
        if redis_url:
            try:
                self.redis = redis.from_url(redis_url, decode_responses=True)
                await self.redis.ping()
                self.is_redis_enabled = True
                print("[CACHE] Connected to Redis/Vercel KV", file=sys.stdout, flush=True)
            except Exception as e:
                print(f"[CACHE] Failed to connect to Redis: {e}", file=sys.stderr, flush=True)
                self.is_redis_enabled = False
        else:
            print("[CACHE] No Redis URL found, using in-memory cache", file=sys.stdout, flush=True)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.is_redis_enabled and self.redis:
                value = await self.redis.get(key)
                if value:
                    return json.loads(value)
            else:
                # In-memory fallback (check TTL if I were implementing full LRU, but simple dict for now)
                # For simple fallback, we won't implement TTL expiration strictly
                return self.memory_cache.get(key)
        except Exception as e:
            print(f"[CACHE] Error getting key {key}: {e}", file=sys.stderr, flush=True)
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL"""
        try:
            json_value = json.dumps(value)
            if self.is_redis_enabled and self.redis:
                await self.redis.set(key, json_value, ex=ttl)
            else:
                self.memory_cache[key] = value
                # In a real in-memory cache, we'd handle cleanup. 
                # For now, this is just a fallback for dev/testing if Redis fails.
        except Exception as e:
            print(f"[CACHE] Error setting key {key}: {e}", file=sys.stderr, flush=True)

    async def close(self):
        if self.redis:
            await self.redis.close()
    
    async def ping(self) -> bool:
        """Ping cache to check if it's alive"""
        try:
            if self.is_redis_enabled and self.redis:
                await self.redis.ping()
                return True
            else:
                # In-memory cache is always available
                return True
        except Exception as e:
            print(f"[CACHE] Ping failed: {e}", file=sys.stderr, flush=True)
            return False
    
    async def delete(self, key: str):
        """Delete a specific key from cache"""
        try:
            if self.is_redis_enabled and self.redis:
                await self.redis.delete(key)
                print(f"[CACHE] Deleted key: {key}", file=sys.stdout, flush=True)
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    print(f"[CACHE] Deleted key from memory: {key}", file=sys.stdout, flush=True)
        except Exception as e:
            print(f"[CACHE] Error deleting key {key}: {e}", file=sys.stderr, flush=True)
    
    async def clear_pattern(self, pattern: str):
        """Clear all keys matching a pattern (e.g., 'quran_search:*')"""
        try:
            if self.is_redis_enabled and self.redis:
                cursor = 0
                deleted_count = 0
                while True:
                    cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                    if keys:
                        await self.redis.delete(*keys)
                        deleted_count += len(keys)
                    if cursor == 0:
                        break
                print(f"[CACHE] Cleared {deleted_count} keys matching pattern: {pattern}", file=sys.stdout, flush=True)
            else:
                # In-memory cache: clear matching keys
                keys_to_delete = [k for k in self.memory_cache.keys() if pattern.replace('*', '') in k]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                print(f"[CACHE] Cleared {len(keys_to_delete)} keys from memory matching pattern: {pattern}", file=sys.stdout, flush=True)
        except Exception as e:
            print(f"[CACHE] Error clearing pattern {pattern}: {e}", file=sys.stderr, flush=True)

# Global cache instance
cache = CacheService()
