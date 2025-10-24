"""
Caching Layer for HyperKit AI Agent
Production-ready caching with TTL, LRU, and distributed cache support
"""

import time
import hashlib
import json
import logging
from typing import Any, Optional, Dict, Union, Callable
from functools import wraps
from cachetools import TTLCache, LRUCache
from pathlib import Path
import pickle

logger = logging.getLogger(__name__)

class HyperKitCache:
    """Production-ready caching system for HyperKit"""
    
    def __init__(
        self,
        max_size: int = 1000,
        ttl: int = 300,  # 5 minutes default
        cache_type: str = "ttl"
    ):
        """
        Initialize cache system
        
        Args:
            max_size: Maximum number of items in cache
            ttl: Time to live in seconds
            cache_type: Type of cache (ttl, lru, file)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache_type = cache_type
        
        if cache_type == "ttl":
            self.cache = TTLCache(maxsize=max_size, ttl=ttl)
        elif cache_type == "lru":
            self.cache = LRUCache(maxsize=max_size)
        elif cache_type == "file":
            self.cache_dir = Path("cache")
            self.cache_dir.mkdir(exist_ok=True)
            self.cache = {}
        else:
            raise ValueError(f"Unknown cache type: {cache_type}")
        
        self.hit_count = 0
        self.miss_count = 0
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0
        }
        
        logger.info(f"Cache initialized: {cache_type}, max_size={max_size}, ttl={ttl}")
    
    def _generate_key(self, key: Union[str, tuple]) -> str:
        """Generate cache key from input"""
        if isinstance(key, tuple):
            key_str = "|".join(str(k) for k in key)
        else:
            key_str = str(key)
        
        # Create hash for consistent key length
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_file_path(self, key: str) -> Path:
        """Get file path for file-based cache"""
        return self.cache_dir / f"{key}.cache"
    
    def _is_file_expired(self, file_path: Path) -> bool:
        """Check if cached file is expired"""
        if not file_path.exists():
            return True
        
        file_age = time.time() - file_path.stat().st_mtime
        return file_age > self.ttl
    
    def get(self, key: Union[str, tuple]) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        cache_key = self._generate_key(key)
        
        try:
            if self.cache_type == "file":
                file_path = self._get_file_path(cache_key)
                
                if self._is_file_expired(file_path):
                    if file_path.exists():
                        file_path.unlink()
                    return None
                
                with open(file_path, 'rb') as f:
                    value = pickle.load(f)
                
                self.hit_count += 1
                self.stats["hits"] += 1
                logger.debug(f"Cache hit: {cache_key}")
                return value
            else:
                value = self.cache.get(cache_key)
                if value is not None:
                    self.hit_count += 1
                    self.stats["hits"] += 1
                    logger.debug(f"Cache hit: {cache_key}")
                else:
                    self.miss_count += 1
                    self.stats["misses"] += 1
                    logger.debug(f"Cache miss: {cache_key}")
                
                return value
                
        except Exception as e:
            logger.error(f"Cache get error for key {cache_key}: {e}")
            self.miss_count += 1
            self.stats["misses"] += 1
            return None
    
    def set(self, key: Union[str, tuple], value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = self._generate_key(key)
        cache_ttl = ttl or self.ttl
        
        try:
            if self.cache_type == "file":
                file_path = self._get_file_path(cache_key)
                
                with open(file_path, 'wb') as f:
                    pickle.dump(value, f)
                
                # Set file modification time for TTL tracking
                current_time = time.time()
                file_path.touch()
                os.utime(file_path, (current_time, current_time))
                
            else:
                self.cache[cache_key] = value
            
            self.stats["size"] = len(self.cache) if self.cache_type != "file" else len(list(self.cache_dir.glob("*.cache")))
            logger.debug(f"Cache set: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {cache_key}: {e}")
            return False
    
    def delete(self, key: Union[str, tuple]) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = self._generate_key(key)
        
        try:
            if self.cache_type == "file":
                file_path = self._get_file_path(cache_key)
                if file_path.exists():
                    file_path.unlink()
            else:
                self.cache.pop(cache_key, None)
            
            logger.debug(f"Cache delete: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error for key {cache_key}: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries"""
        try:
            if self.cache_type == "file":
                for file_path in self.cache_dir.glob("*.cache"):
                    file_path.unlink()
            else:
                self.cache.clear()
            
            self.stats["size"] = 0
            logger.info("Cache cleared")
            return True
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_type": self.cache_type,
            "max_size": self.max_size,
            "ttl": self.ttl,
            "hits": self.hit_count,
            "misses": self.miss_count,
            "hit_rate": f"{hit_rate:.2f}%",
            "size": self.stats["size"],
            "evictions": self.stats["evictions"]
        }
    
    def reset_stats(self):
        """Reset cache statistics"""
        self.hit_count = 0
        self.miss_count = 0
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0
        }

# Global cache instances
rpc_cache = HyperKitCache(max_size=500, ttl=300, cache_type="ttl")
ai_cache = HyperKitCache(max_size=200, ttl=600, cache_type="ttl")  # 10 minutes for AI responses
config_cache = HyperKitCache(max_size=50, ttl=3600, cache_type="ttl")  # 1 hour for config

def cached_rpc_call(cache_ttl: int = 300):
    """
    Decorator for caching RPC calls
    
    Args:
        cache_ttl: TTL for cached RPC calls in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = (func.__name__, str(args), str(sorted(kwargs.items())))
            
            # Try to get from cache
            cached_result = rpc_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"RPC cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            rpc_cache.set(cache_key, result, ttl=cache_ttl)
            logger.debug(f"RPC cache set for {func.__name__}")
            
            return result
        return wrapper
    return decorator

def cached_ai_response(cache_ttl: int = 600):
    """
    Decorator for caching AI responses
    
    Args:
        cache_ttl: TTL for cached AI responses in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = (func.__name__, str(args), str(sorted(kwargs.items())))
            
            # Try to get from cache
            cached_result = ai_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"AI cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            ai_cache.set(cache_key, result, ttl=cache_ttl)
            logger.debug(f"AI cache set for {func.__name__}")
            
            return result
        return wrapper
    return decorator

def cached_config(cache_ttl: int = 3600):
    """
    Decorator for caching configuration
    
    Args:
        cache_ttl: TTL for cached configuration in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = (func.__name__, str(args), str(sorted(kwargs.items())))
            
            # Try to get from cache
            cached_result = config_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Config cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            config_cache.set(cache_key, result, ttl=cache_ttl)
            logger.debug(f"Config cache set for {func.__name__}")
            
            return result
        return wrapper
    return decorator

def get_cache_stats() -> Dict[str, Any]:
    """Get statistics for all cache instances"""
    return {
        "rpc_cache": rpc_cache.get_stats(),
        "ai_cache": ai_cache.get_stats(),
        "config_cache": config_cache.get_stats()
    }

def clear_all_caches():
    """Clear all cache instances"""
    rpc_cache.clear()
    ai_cache.clear()
    config_cache.clear()
    logger.info("All caches cleared")

def warm_cache():
    """Warm up cache with frequently accessed data"""
    try:
        # Warm up configuration cache
        from core.config.loader import get_config
        config = get_config()
        if config:
            logger.info("Configuration cache warmed up")
        
        # Warm up RPC cache with basic network checks
        from services.common.health import check_rpc_health
        check_rpc_health()
        logger.info("RPC cache warmed up")
        
        logger.info("Cache warming completed")
        
    except Exception as e:
        logger.error(f"Cache warming failed: {e}")

# Auto-warm cache on import
warm_cache()
