"""
Health Check System for HyperKit AI Agent
Production-ready health monitoring and status reporting
"""

import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from web3 import Web3
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

class HealthChecker:
    """Health check system for monitoring system components"""
    
    def __init__(self):
        self.checks = {}
        self.last_check_times = {}
        self.check_results = {}
        self.overall_status = "unknown"
    
    def register_check(self, name: str, check_func: callable, critical: bool = True):
        """
        Register a health check function
        
        Args:
            name: Name of the health check
            check_func: Function that returns health status
            critical: Whether this check is critical for overall health
        """
        self.checks[name] = {
            'function': check_func,
            'critical': critical,
            'enabled': True
        }
        logger.info(f"Registered health check: {name}")
    
    def run_check(self, name: str) -> Dict[str, Any]:
        """
        Run a specific health check
        
        Args:
            name: Name of the health check to run
            
        Returns:
            Dictionary with check results
        """
        if name not in self.checks:
            return {
                "status": "error",
                "message": f"Health check '{name}' not found",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        check = self.checks[name]
        if not check['enabled']:
            return {
                "status": "disabled",
                "message": f"Health check '{name}' is disabled",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            start_time = time.time()
            result = check['function']()
            duration = time.time() - start_time
            
            # Ensure result has required fields
            if isinstance(result, dict):
                result['duration'] = duration
                result['timestamp'] = datetime.utcnow().isoformat()
            else:
                result = {
                    "status": "healthy" if result else "unhealthy",
                    "message": str(result),
                    "duration": duration,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            self.check_results[name] = result
            self.last_check_times[name] = datetime.utcnow()
            
            return result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "duration": time.time() - start_time,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
            self.check_results[name] = error_result
            return error_result
    
    def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all registered health checks
        
        Returns:
            Dictionary with overall health status and individual check results
        """
        results = {}
        critical_failures = 0
        total_checks = len(self.checks)
        
        for name in self.checks:
            results[name] = self.run_check(name)
            
            # Count critical failures
            if (self.checks[name]['critical'] and 
                results[name]['status'] in ['unhealthy', 'error']):
                critical_failures += 1
        
        # Determine overall status
        if critical_failures == 0:
            self.overall_status = "healthy"
        elif critical_failures < total_checks:
            self.overall_status = "degraded"
        else:
            self.overall_status = "unhealthy"
        
        return {
            "overall_status": self.overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results,
            "summary": {
                "total_checks": total_checks,
                "critical_failures": critical_failures,
                "healthy_checks": sum(1 for r in results.values() 
                                    if r['status'] == 'healthy'),
                "unhealthy_checks": sum(1 for r in results.values() 
                                      if r['status'] in ['unhealthy', 'error'])
            }
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        return self.run_all_checks()

# Global health checker instance
health_checker = HealthChecker()

# Health check functions
def check_rpc_health() -> Dict[str, Any]:
    """Check RPC endpoint health"""
    try:
        # This would be configured based on your setup
        rpc_urls = [
            "https://hyperion-testnet.metisdevops.link",
            "https://rpc.lazai.network/testnet",
            "https://andromeda.metis.io"
        ]
        
        healthy_rpcs = 0
        for rpc_url in rpc_urls:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                if w3.is_connected():
                    healthy_rpcs += 1
            except:
                continue
        
        if healthy_rpcs > 0:
            return {
                "status": "healthy",
                "message": f"{healthy_rpcs}/{len(rpc_urls)} RPC endpoints healthy",
                "healthy_endpoints": healthy_rpcs,
                "total_endpoints": len(rpc_urls)
            }
        else:
            return {
                "status": "unhealthy",
                "message": "No RPC endpoints are healthy",
                "healthy_endpoints": 0,
                "total_endpoints": len(rpc_urls)
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"RPC health check failed: {str(e)}"
        }

def check_ai_health() -> Dict[str, Any]:
    """Check AI provider health"""
    try:
        # Check if API keys are configured
        api_keys = {
            'google': bool(os.getenv('GOOGLE_API_KEY')),
            'openai': bool(os.getenv('OPENAI_API_KEY')),
            'anthropic': bool(os.getenv('ANTHROPIC_API_KEY'))
        }
        
        configured_providers = sum(api_keys.values())
        
        if configured_providers > 0:
            return {
                "status": "healthy",
                "message": f"{configured_providers} AI providers configured",
                "configured_providers": configured_providers,
                "providers": api_keys
            }
        else:
            return {
                "status": "unhealthy",
                "message": "No AI providers configured",
                "configured_providers": 0,
                "providers": api_keys
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"AI health check failed: {str(e)}"
        }

def check_storage_health() -> Dict[str, Any]:
    """Check storage system health"""
    try:
        # Check if required directories exist and are writable
        required_dirs = [
            Path("contracts/generated"),
            Path("artifacts/deployments"),
            Path("logs")
        ]
        
        healthy_dirs = 0
        for dir_path in required_dirs:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                # Test write access
                test_file = dir_path / ".health_check"
                test_file.write_text("health_check")
                test_file.unlink()
                healthy_dirs += 1
            except:
                continue
        
        if healthy_dirs == len(required_dirs):
            return {
                "status": "healthy",
                "message": "All storage directories accessible",
                "accessible_dirs": healthy_dirs,
                "total_dirs": len(required_dirs)
            }
        else:
            return {
                "status": "unhealthy",
                "message": f"{healthy_dirs}/{len(required_dirs)} storage directories accessible",
                "accessible_dirs": healthy_dirs,
                "total_dirs": len(required_dirs)
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Storage health check failed: {str(e)}"
        }

def check_foundry_health() -> Dict[str, Any]:
    """Check Foundry installation health"""
    try:
        from services.deployment.foundry_manager import FoundryManager
        
        if FoundryManager.is_installed():
            version = FoundryManager.get_version()
            return {
                "status": "healthy",
                "message": f"Foundry installed: {version}",
                "version": version
            }
        else:
            return {
                "status": "unhealthy",
                "message": "Foundry not installed",
                "version": None
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Foundry health check failed: {str(e)}"
        }

def check_config_health() -> Dict[str, Any]:
    """Check configuration health"""
    try:
        from core.config.loader import get_config
        
        config = get_config()
        if config:
            return {
                "status": "healthy",
                "message": "Configuration loaded successfully",
                "networks_configured": len(config.get('networks', {})),
                "ai_providers_configured": len(config.get('ai_providers', {}))
            }
        else:
            return {
                "status": "unhealthy",
                "message": "Configuration not loaded"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Configuration health check failed: {str(e)}"
        }

def check_memory_health() -> Dict[str, Any]:
    """Check system memory health"""
    try:
        import psutil
        
        memory = psutil.virtual_memory()
        memory_usage_percent = memory.percent
        
        if memory_usage_percent < 80:
            status = "healthy"
        elif memory_usage_percent < 90:
            status = "warning"
        else:
            status = "unhealthy"
        
        return {
            "status": status,
            "message": f"Memory usage: {memory_usage_percent:.1f}%",
            "memory_usage_percent": memory_usage_percent,
            "available_memory_gb": memory.available / (1024**3)
        }
    except ImportError:
        return {
            "status": "warning",
            "message": "psutil not available for memory monitoring"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Memory health check failed: {str(e)}"
        }

# Register health checks
def initialize_health_checks():
    """Initialize all health checks"""
    health_checker.register_check("rpc", check_rpc_health, critical=True)
    health_checker.register_check("ai_providers", check_ai_health, critical=True)
    health_checker.register_check("storage", check_storage_health, critical=True)
    health_checker.register_check("foundry", check_foundry_health, critical=True)
    health_checker.register_check("configuration", check_config_health, critical=True)
    health_checker.register_check("memory", check_memory_health, critical=False)
    
    logger.info("Health checks initialized")

# Auto-initialize health checks
initialize_health_checks()

def get_health_status() -> Dict[str, Any]:
    """Get current system health status"""
    return health_checker.get_health_status()

def get_health_summary() -> Dict[str, Any]:
    """Get health status summary"""
    status = get_health_status()
    return {
        "overall_status": status["overall_status"],
        "timestamp": status["timestamp"],
        "summary": status["summary"]
    }
