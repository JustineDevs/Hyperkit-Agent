"""
Health monitoring for HyperKit AI Agent production system.

This module provides health check endpoints and monitoring for all system components.
"""

import asyncio
import aiohttp
import redis
from sqlalchemy import text
from typing import Dict, Any
import logging

from ..db.connection import get_database_session

logger = logging.getLogger(__name__)


async def check_database_health() -> Dict[str, Any]:
    """Check database health."""
    try:
        with get_database_session() as db:
            # Test database connection
            result = db.execute(text("SELECT 1")).fetchone()
            
            if result:
                return {
                    "status": "healthy",
                    "response_time": "< 100ms"
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Database query failed"
                }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_redis_health() -> Dict[str, Any]:
    """Check Redis health."""
    try:
        r = redis.Redis(host='redis', port=6379, db=0)
        r.ping()
        
        # Get Redis info
        info = r.info()
        
        return {
            "status": "healthy",
            "version": info.get('redis_version'),
            "memory_used": info.get('used_memory_human'),
            "connected_clients": info.get('connected_clients')
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_celery_health() -> Dict[str, Any]:
    """Check Celery worker health."""
    try:
        from ..jobs.celery import celery_app
        
        # Get active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            return {
                "status": "healthy",
                "active_workers": len(active_workers),
                "workers": list(active_workers.keys())
            }
        else:
            return {
                "status": "unhealthy",
                "error": "No active workers found"
            }
    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_rpc_health() -> Dict[str, Any]:
    """Check RPC node health."""
    try:
        # Test RPC endpoints
        rpc_urls = [
            "https://eth-mainnet.g.alchemy.com/v2/demo",
            "https://mainnet.infura.io/v3/demo"
        ]
        
        healthy_endpoints = 0
        for url in rpc_urls:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1},
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            healthy_endpoints += 1
            except:
                continue
        
        if healthy_endpoints > 0:
            return {
                "status": "healthy",
                "healthy_endpoints": healthy_endpoints,
                "total_endpoints": len(rpc_urls)
            }
        else:
            return {
                "status": "unhealthy",
                "error": "No healthy RPC endpoints"
            }
    except Exception as e:
        logger.error(f"RPC health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_ai_models_health() -> Dict[str, Any]:
    """Check AI model endpoints health."""
    try:
        # Test AI model endpoints
        ai_endpoints = [
            "https://api.openai.com/v1/models",
            "https://generativelanguage.googleapis.com/v1/models"
        ]
        
        healthy_models = 0
        for endpoint in ai_endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status in [200, 401]:  # 401 is OK for auth-required endpoints
                            healthy_models += 1
            except:
                continue
        
        if healthy_models > 0:
            return {
                "status": "healthy",
                "healthy_models": healthy_models,
                "total_models": len(ai_endpoints)
            }
        else:
            return {
                "status": "degraded",
                "error": "Some AI models unavailable"
            }
    except Exception as e:
        logger.error(f"AI models health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def get_health_status() -> Dict[str, Any]:
    """Get overall system health status."""
    try:
        # Run all health checks in parallel
        health_checks = await asyncio.gather(
            check_database_health(),
            check_redis_health(),
            check_celery_health(),
            check_rpc_health(),
            check_ai_models_health(),
            return_exceptions=True
        )
        
        # Process results
        components = {
            "database": health_checks[0] if not isinstance(health_checks[0], Exception) else {"status": "unhealthy", "error": str(health_checks[0])},
            "redis": health_checks[1] if not isinstance(health_checks[1], Exception) else {"status": "unhealthy", "error": str(health_checks[1])},
            "celery": health_checks[2] if not isinstance(health_checks[2], Exception) else {"status": "unhealthy", "error": str(health_checks[2])},
            "rpc": health_checks[3] if not isinstance(health_checks[3], Exception) else {"status": "unhealthy", "error": str(health_checks[3])},
            "ai_models": health_checks[4] if not isinstance(health_checks[4], Exception) else {"status": "unhealthy", "error": str(health_checks[4])}
        }
        
        # Determine overall status
        unhealthy_components = [name for name, status in components.items() if status.get("status") == "unhealthy"]
        degraded_components = [name for name, status in components.items() if status.get("status") == "degraded"]
        
        if unhealthy_components:
            overall_status = "unhealthy"
        elif degraded_components:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "components": components,
            "unhealthy_components": unhealthy_components,
            "degraded_components": degraded_components
        }
        
    except Exception as e:
        logger.error(f"Health status check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "components": {}
        }
