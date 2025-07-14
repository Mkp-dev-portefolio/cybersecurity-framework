"""
Redis cache implementation for PKI MCP server
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import aioredis
import structlog

logger = structlog.get_logger(__name__)


class RedisCache:
    """Redis cache operations for PKI MCP server"""
    
    def __init__(self, redis_url: str, key_prefix: str = "pki_mcp"):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.redis = None
        
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis.ping()
            
            logger.info("Redis cache connected successfully")
            
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
            
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            
    async def health_check(self) -> bool:
        """Check Redis health"""
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False
            
    def _make_key(self, key: str) -> str:
        """Make full key with prefix"""
        return f"{self.key_prefix}:{key}"
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            full_key = self._make_key(key)
            value = await self.redis.get(full_key)
            
            if value is None:
                return None
                
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error("Failed to get value from cache", key=key, error=str(e))
            return None
            
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        try:
            full_key = self._make_key(key)
            
            # Serialize value if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value, default=str)
                
            if ttl:
                await self.redis.setex(full_key, ttl, value)
            else:
                await self.redis.set(full_key, value)
                
            return True
            
        except Exception as e:
            logger.error("Failed to set value in cache", key=key, error=str(e))
            return False
            
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            full_key = self._make_key(key)
            result = await self.redis.delete(full_key)
            return result > 0
            
        except Exception as e:
            logger.error("Failed to delete value from cache", key=key, error=str(e))
            return False
            
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            full_key = self._make_key(key)
            result = await self.redis.exists(full_key)
            return result > 0
            
        except Exception as e:
            logger.error("Failed to check key existence", key=key, error=str(e))
            return False
            
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key"""
        try:
            full_key = self._make_key(key)
            result = await self.redis.expire(full_key, ttl)
            return result
            
        except Exception as e:
            logger.error("Failed to set TTL for key", key=key, error=str(e))
            return False
            
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get TTL for key"""
        try:
            full_key = self._make_key(key)
            ttl = await self.redis.ttl(full_key)
            return ttl if ttl > 0 else None
            
        except Exception as e:
            logger.error("Failed to get TTL for key", key=key, error=str(e))
            return None
            
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        try:
            full_key = self._make_key(key)
            result = await self.redis.incrby(full_key, amount)
            return result
            
        except Exception as e:
            logger.error("Failed to increment counter", key=key, error=str(e))
            return 0
            
    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement counter"""
        try:
            full_key = self._make_key(key)
            result = await self.redis.decrby(full_key, amount)
            return result
            
        except Exception as e:
            logger.error("Failed to decrement counter", key=key, error=str(e))
            return 0
            
    async def set_hash(self, key: str, field: str, value: Any) -> bool:
        """Set hash field"""
        try:
            full_key = self._make_key(key)
            
            if not isinstance(value, str):
                value = json.dumps(value, default=str)
                
            result = await self.redis.hset(full_key, field, value)
            return result
            
        except Exception as e:
            logger.error("Failed to set hash field", key=key, field=field, error=str(e))
            return False
            
    async def get_hash(self, key: str, field: str) -> Optional[Any]:
        """Get hash field"""
        try:
            full_key = self._make_key(key)
            value = await self.redis.hget(full_key, field)
            
            if value is None:
                return None
                
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error("Failed to get hash field", key=key, field=field, error=str(e))
            return None
            
    async def get_all_hash(self, key: str) -> Dict[str, Any]:
        """Get all hash fields"""
        try:
            full_key = self._make_key(key)
            result = await self.redis.hgetall(full_key)
            
            # Try to deserialize JSON values
            deserialized = {}
            for field, value in result.items():
                try:
                    deserialized[field] = json.loads(value)
                except json.JSONDecodeError:
                    deserialized[field] = value
                    
            return deserialized
            
        except Exception as e:
            logger.error("Failed to get all hash fields", key=key, error=str(e))
            return {}
            
    async def delete_hash(self, key: str, field: str) -> bool:
        """Delete hash field"""
        try:
            full_key = self._make_key(key)
            result = await self.redis.hdel(full_key, field)
            return result > 0
            
        except Exception as e:
            logger.error("Failed to delete hash field", key=key, field=field, error=str(e))
            return False
            
    async def add_to_set(self, key: str, value: Any) -> bool:
        """Add value to set"""
        try:
            full_key = self._make_key(key)
            
            if not isinstance(value, str):
                value = json.dumps(value, default=str)
                
            result = await self.redis.sadd(full_key, value)
            return result > 0
            
        except Exception as e:
            logger.error("Failed to add to set", key=key, error=str(e))
            return False
            
    async def remove_from_set(self, key: str, value: Any) -> bool:
        """Remove value from set"""
        try:
            full_key = self._make_key(key)
            
            if not isinstance(value, str):
                value = json.dumps(value, default=str)
                
            result = await self.redis.srem(full_key, value)
            return result > 0
            
        except Exception as e:
            logger.error("Failed to remove from set", key=key, error=str(e))
            return False
            
    async def get_set_members(self, key: str) -> List[Any]:
        """Get all set members"""
        try:
            full_key = self._make_key(key)
            members = await self.redis.smembers(full_key)
            
            # Try to deserialize JSON values
            deserialized = []
            for member in members:
                try:
                    deserialized.append(json.loads(member))
                except json.JSONDecodeError:
                    deserialized.append(member)
                    
            return deserialized
            
        except Exception as e:
            logger.error("Failed to get set members", key=key, error=str(e))
            return []
            
    async def is_set_member(self, key: str, value: Any) -> bool:
        """Check if value is set member"""
        try:
            full_key = self._make_key(key)
            
            if not isinstance(value, str):
                value = json.dumps(value, default=str)
                
            result = await self.redis.sismember(full_key, value)
            return result
            
        except Exception as e:
            logger.error("Failed to check set membership", key=key, error=str(e))
            return False
            
    async def push_to_list(self, key: str, value: Any, left: bool = True) -> bool:
        """Push value to list"""
        try:
            full_key = self._make_key(key)
            
            if not isinstance(value, str):
                value = json.dumps(value, default=str)
                
            if left:
                result = await self.redis.lpush(full_key, value)
            else:
                result = await self.redis.rpush(full_key, value)
                
            return result > 0
            
        except Exception as e:
            logger.error("Failed to push to list", key=key, error=str(e))
            return False
            
    async def pop_from_list(self, key: str, left: bool = True) -> Optional[Any]:
        """Pop value from list"""
        try:
            full_key = self._make_key(key)
            
            if left:
                value = await self.redis.lpop(full_key)
            else:
                value = await self.redis.rpop(full_key)
                
            if value is None:
                return None
                
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error("Failed to pop from list", key=key, error=str(e))
            return None
            
    async def get_list_length(self, key: str) -> int:
        """Get list length"""
        try:
            full_key = self._make_key(key)
            length = await self.redis.llen(full_key)
            return length
            
        except Exception as e:
            logger.error("Failed to get list length", key=key, error=str(e))
            return 0
            
    async def get_list_range(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get list range"""
        try:
            full_key = self._make_key(key)
            values = await self.redis.lrange(full_key, start, end)
            
            # Try to deserialize JSON values
            deserialized = []
            for value in values:
                try:
                    deserialized.append(json.loads(value))
                except json.JSONDecodeError:
                    deserialized.append(value)
                    
            return deserialized
            
        except Exception as e:
            logger.error("Failed to get list range", key=key, error=str(e))
            return []
            
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            full_pattern = self._make_key(pattern)
            keys = await self.redis.keys(full_pattern)
            
            if keys:
                result = await self.redis.delete(*keys)
                return result
                
            return 0
            
        except Exception as e:
            logger.error("Failed to clear pattern", pattern=pattern, error=str(e))
            return 0
            
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            info = await self.redis.info("memory")
            
            return {
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "used_memory_peak": info.get("used_memory_peak", 0),
                "used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
            
        except Exception as e:
            logger.error("Failed to get cache stats", error=str(e))
            return {}
            
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate"""
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100.0
