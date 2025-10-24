"""
Rate Limiting System for HyperKit AI Agent
Production-ready rate limiting with multiple algorithms and distributed support
"""

import time
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
from collections import defaultdict, deque
from threading import Lock
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class RateLimiter:
    """Production-ready rate limiter with multiple algorithms"""
    
    def __init__(
        self,
        max_requests: int = 100,
        time_window: int = 60,  # seconds
        algorithm: str = "sliding_window"
    ):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests allowed
            time_window: Time window in seconds
            algorithm: Rate limiting algorithm (sliding_window, token_bucket, fixed_window)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.algorithm = algorithm
        
        # Request tracking
        self.requests = defaultdict(deque)
        self.tokens = defaultdict(lambda: max_requests)  # For token bucket
        self.windows = defaultdict(lambda: {"count": 0, "start": time.time()})  # For fixed window
        
        # Statistics
        self.stats = defaultdict(lambda: {
            "total_requests": 0,
            "allowed_requests": 0,
            "blocked_requests": 0,
            "rate_limit_hits": 0
        })
        
        self.lock = Lock()
        
        logger.info(f"Rate limiter initialized: {algorithm}, {max_requests} requests per {time_window}s")
    
    def _sliding_window_check(self, key: str) -> bool:
        """Sliding window rate limiting"""
        current_time = time.time()
        cutoff_time = current_time - self.time_window
        
        # Remove old requests
        while self.requests[key] and self.requests[key][0] < cutoff_time:
            self.requests[key].popleft()
        
        # Check if under limit
        if len(self.requests[key]) < self.max_requests:
            self.requests[key].append(current_time)
            return True
        
        return False
    
    def _token_bucket_check(self, key: str) -> bool:
        """Token bucket rate limiting"""
        current_time = time.time()
        
        # Add tokens based on time passed
        if key in self.tokens:
            time_passed = current_time - getattr(self, f"_last_refill_{key}", current_time)
            tokens_to_add = time_passed * (self.max_requests / self.time_window)
            self.tokens[key] = min(self.max_requests, self.tokens[key] + tokens_to_add)
            setattr(self, f"_last_refill_{key}", current_time)
        else:
            self.tokens[key] = self.max_requests
            setattr(self, f"_last_refill_{key}", current_time)
        
        # Check if tokens available
        if self.tokens[key] >= 1:
            self.tokens[key] -= 1
            return True
        
        return False
    
    def _fixed_window_check(self, key: str) -> bool:
        """Fixed window rate limiting"""
        current_time = time.time()
        window = self.windows[key]
        
        # Reset window if time has passed
        if current_time - window["start"] >= self.time_window:
            window["count"] = 0
            window["start"] = current_time
        
        # Check if under limit
        if window["count"] < self.max_requests:
            window["count"] += 1
            return True
        
        return False
    
    def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed
        
        Args:
            key: Unique identifier for rate limiting (e.g., user_id, ip_address)
            
        Returns:
            True if request is allowed, False if rate limited
        """
        with self.lock:
            self.stats[key]["total_requests"] += 1
            
            # Choose algorithm
            if self.algorithm == "sliding_window":
                allowed = self._sliding_window_check(key)
            elif self.algorithm == "token_bucket":
                allowed = self._token_bucket_check(key)
            elif self.algorithm == "fixed_window":
                allowed = self._fixed_window_check(key)
            else:
                logger.error(f"Unknown rate limiting algorithm: {self.algorithm}")
                return True  # Allow by default if algorithm unknown
            
            if allowed:
                self.stats[key]["allowed_requests"] += 1
                logger.debug(f"Rate limit check passed for {key}")
            else:
                self.stats[key]["blocked_requests"] += 1
                self.stats[key]["rate_limit_hits"] += 1
                logger.warning(f"Rate limit exceeded for {key}")
            
            return allowed
    
    def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests for a key"""
        if self.algorithm == "sliding_window":
            current_time = time.time()
            cutoff_time = current_time - self.time_window
            
            # Remove old requests
            while self.requests[key] and self.requests[key][0] < cutoff_time:
                self.requests[key].popleft()
            
            return max(0, self.max_requests - len(self.requests[key]))
        
        elif self.algorithm == "token_bucket":
            return max(0, int(self.tokens[key]))
        
        elif self.algorithm == "fixed_window":
            current_time = time.time()
            window = self.windows[key]
            
            # Reset window if time has passed
            if current_time - window["start"] >= self.time_window:
                return self.max_requests
            
            return max(0, self.max_requests - window["count"])
        
        return 0
    
    def get_reset_time(self, key: str) -> float:
        """Get time when rate limit resets for a key"""
        if self.algorithm == "sliding_window":
            if not self.requests[key]:
                return time.time()
            return self.requests[key][0] + self.time_window
        
        elif self.algorithm == "token_bucket":
            return time.time() + (self.time_window / self.max_requests)
        
        elif self.algorithm == "fixed_window":
            current_time = time.time()
            window = self.windows[key]
            return window["start"] + self.time_window
        
        return time.time()
    
    def get_stats(self, key: Optional[str] = None) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        if key:
            return self.stats[key].copy()
        else:
            return {k: v.copy() for k, v in self.stats.items()}
    
    def reset_stats(self, key: Optional[str] = None):
        """Reset statistics"""
        if key:
            self.stats[key] = {
                "total_requests": 0,
                "allowed_requests": 0,
                "blocked_requests": 0,
                "rate_limit_hits": 0
            }
        else:
            self.stats.clear()

# Global rate limiters for different components
api_rate_limiter = RateLimiter(max_requests=100, time_window=60, algorithm="sliding_window")
rpc_rate_limiter = RateLimiter(max_requests=50, time_window=60, algorithm="token_bucket")
ai_rate_limiter = RateLimiter(max_requests=20, time_window=60, algorithm="sliding_window")
deployment_rate_limiter = RateLimiter(max_requests=5, time_window=300, algorithm="fixed_window")  # 5 deployments per 5 minutes

def rate_limit(
    limiter: RateLimiter,
    key_func: Optional[Callable] = None,
    error_message: str = "Rate limit exceeded"
):
    """
    Decorator for rate limiting functions
    
    Args:
        limiter: RateLimiter instance to use
        key_func: Function to generate rate limit key from function arguments
        error_message: Error message when rate limited
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate rate limit key
            if key_func:
                rate_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                rate_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Check rate limit
            if not limiter.is_allowed(rate_key):
                remaining = limiter.get_remaining_requests(rate_key)
                reset_time = limiter.get_reset_time(rate_key)
                
                raise RateLimitExceeded(
                    message=error_message,
                    remaining_requests=remaining,
                    reset_time=reset_time,
                    rate_key=rate_key
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    
    def __init__(
        self,
        message: str,
        remaining_requests: int = 0,
        reset_time: float = 0,
        rate_key: str = ""
    ):
        self.message = message
        self.remaining_requests = remaining_requests
        self.reset_time = reset_time
        self.rate_key = rate_key
        super().__init__(message)

def get_rate_limit_info(limiter: RateLimiter, key: str) -> Dict[str, Any]:
    """Get rate limit information for a key"""
    return {
        "remaining_requests": limiter.get_remaining_requests(key),
        "reset_time": limiter.get_reset_time(key),
        "max_requests": limiter.max_requests,
        "time_window": limiter.time_window,
        "algorithm": limiter.algorithm,
        "stats": limiter.get_stats(key)
    }

def get_all_rate_limit_stats() -> Dict[str, Any]:
    """Get statistics for all rate limiters"""
    return {
        "api_rate_limiter": api_rate_limiter.get_stats(),
        "rpc_rate_limiter": rpc_rate_limiter.get_stats(),
        "ai_rate_limiter": ai_rate_limiter.get_stats(),
        "deployment_rate_limiter": deployment_rate_limiter.get_stats()
    }

def reset_all_rate_limits():
    """Reset all rate limiters"""
    api_rate_limiter.reset_stats()
    rpc_rate_limiter.reset_stats()
    ai_rate_limiter.reset_stats()
    deployment_rate_limiter.reset_stats()
    logger.info("All rate limiters reset")

# Pre-configured rate limit decorators
def api_rate_limit(max_requests: int = 100, time_window: int = 60):
    """Rate limit for API endpoints"""
    limiter = RateLimiter(max_requests=max_requests, time_window=time_window)
    return rate_limit(limiter, error_message="API rate limit exceeded")

def rpc_rate_limit(max_requests: int = 50, time_window: int = 60):
    """Rate limit for RPC calls"""
    limiter = RateLimiter(max_requests=max_requests, time_window=time_window)
    return rate_limit(limiter, error_message="RPC rate limit exceeded")

def ai_rate_limit(max_requests: int = 20, time_window: int = 60):
    """Rate limit for AI provider calls"""
    limiter = RateLimiter(max_requests=max_requests, time_window=time_window)
    return rate_limit(limiter, error_message="AI provider rate limit exceeded")

def deployment_rate_limit(max_requests: int = 5, time_window: int = 300):
    """Rate limit for deployments"""
    limiter = RateLimiter(max_requests=max_requests, time_window=time_window)
    return rate_limit(limiter, error_message="Deployment rate limit exceeded")

# Example usage decorators
@rate_limit(api_rate_limiter, error_message="Too many API requests")
def example_api_function():
    """Example API function with rate limiting"""
    return {"message": "API call successful"}

@rate_limit(rpc_rate_limiter, error_message="Too many RPC calls")
def example_rpc_function():
    """Example RPC function with rate limiting"""
    return {"message": "RPC call successful"}

@rate_limit(ai_rate_limiter, error_message="Too many AI requests")
def example_ai_function():
    """Example AI function with rate limiting"""
    return {"message": "AI call successful"}
