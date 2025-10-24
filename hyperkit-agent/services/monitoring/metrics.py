"""
Monitoring and Metrics System for HyperKit AI Agent
Production-ready metrics collection with Prometheus support
"""

import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
from threading import Lock
import json
from pathlib import Path

# Try to import Prometheus client, fallback to basic metrics if not available
try:
    from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Prometheus client not available, using basic metrics")

logger = logging.getLogger(__name__)

class BasicMetrics:
    """Basic metrics implementation when Prometheus is not available"""
    
    def __init__(self):
        self.counters = defaultdict(int)
        self.histograms = defaultdict(list)
        self.gauges = defaultdict(float)
        self.summaries = defaultdict(list)
        self.lock = Lock()
    
    def counter_inc(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Increment counter"""
        with self.lock:
            key = f"{name}:{labels or {}}"
            self.counters[key] += value
    
    def histogram_observe(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record histogram value"""
        with self.lock:
            key = f"{name}:{labels or {}}"
            self.histograms[key].append(value)
    
    def gauge_set(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set gauge value"""
        with self.lock:
            key = f"{name}:{labels or {}}"
            self.gauges[key] = value
    
    def summary_observe(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record summary value"""
        with self.lock:
            key = f"{name}:{labels or {}}"
            self.summaries[key].append(value)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        with self.lock:
            return {
                "counters": dict(self.counters),
                "histograms": {k: {"count": len(v), "sum": sum(v), "avg": sum(v)/len(v) if v else 0} 
                             for k, v in self.histograms.items()},
                "gauges": dict(self.gauges),
                "summaries": {k: {"count": len(v), "sum": sum(v), "avg": sum(v)/len(v) if v else 0} 
                            for k, v in self.summaries.items()}
            }

class HyperKitMetrics:
    """Production-ready metrics system for HyperKit"""
    
    def __init__(self):
        self.registry = CollectorRegistry() if PROMETHEUS_AVAILABLE else None
        self.basic_metrics = BasicMetrics() if not PROMETHEUS_AVAILABLE else None
        
        # Initialize metrics
        self._init_metrics()
        
        # Performance tracking
        self.performance_data = defaultdict(list)
        self.performance_lock = Lock()
        
        # Health tracking
        self.health_history = deque(maxlen=1000)
        self.health_lock = Lock()
        
        logger.info("Metrics system initialized")
    
    def _init_metrics(self):
        """Initialize all metrics"""
        if PROMETHEUS_AVAILABLE:
            # Deployment metrics
            self.deployment_counter = Counter(
                'hyperkit_deployments_total',
                'Total number of deployments',
                ['network', 'status'],
                registry=self.registry
            )
            
            self.deployment_duration = Histogram(
                'hyperkit_deployment_duration_seconds',
                'Deployment duration in seconds',
                ['network'],
                registry=self.registry
            )
            
            # AI provider metrics
            self.ai_requests_counter = Counter(
                'hyperkit_ai_requests_total',
                'Total AI provider requests',
                ['provider', 'model', 'status'],
                registry=self.registry
            )
            
            self.ai_response_time = Histogram(
                'hyperkit_ai_response_time_seconds',
                'AI response time in seconds',
                ['provider', 'model'],
                registry=self.registry
            )
            
            # RPC metrics
            self.rpc_requests_counter = Counter(
                'hyperkit_rpc_requests_total',
                'Total RPC requests',
                ['network', 'status'],
                registry=self.registry
            )
            
            self.rpc_response_time = Histogram(
                'hyperkit_rpc_response_time_seconds',
                'RPC response time in seconds',
                ['network'],
                registry=self.registry
            )
            
            # System metrics
            self.active_connections = Gauge(
                'hyperkit_active_connections',
                'Number of active connections',
                registry=self.registry
            )
            
            self.cache_hit_rate = Gauge(
                'hyperkit_cache_hit_rate',
                'Cache hit rate',
                ['cache_type'],
                registry=self.registry
            )
            
            # Error metrics
            self.error_counter = Counter(
                'hyperkit_errors_total',
                'Total number of errors',
                ['error_type', 'component'],
                registry=self.registry
            )
            
            # Rate limiting metrics
            self.rate_limit_hits = Counter(
                'hyperkit_rate_limit_hits_total',
                'Total rate limit hits',
                ['limiter_type'],
                registry=self.registry
            )
    
    def record_deployment(self, network: str, success: bool, duration: float):
        """Record deployment metrics"""
        status = "success" if success else "failure"
        
        if PROMETHEUS_AVAILABLE:
            self.deployment_counter.labels(network=network, status=status).inc()
            self.deployment_duration.labels(network=network).observe(duration)
        else:
            self.basic_metrics.counter_inc('deployments_total', labels={'network': network, 'status': status})
            self.basic_metrics.histogram_observe('deployment_duration_seconds', duration, labels={'network': network})
    
    def record_ai_request(self, provider: str, model: str, success: bool, response_time: float):
        """Record AI provider request metrics"""
        status = "success" if success else "failure"
        
        if PROMETHEUS_AVAILABLE:
            self.ai_requests_counter.labels(provider=provider, model=model, status=status).inc()
            self.ai_response_time.labels(provider=provider, model=model).observe(response_time)
        else:
            self.basic_metrics.counter_inc('ai_requests_total', labels={'provider': provider, 'model': model, 'status': status})
            self.basic_metrics.histogram_observe('ai_response_time_seconds', response_time, labels={'provider': provider, 'model': model})
    
    def record_rpc_request(self, network: str, success: bool, response_time: float):
        """Record RPC request metrics"""
        status = "success" if success else "failure"
        
        if PROMETHEUS_AVAILABLE:
            self.rpc_requests_counter.labels(network=network, status=status).inc()
            self.rpc_response_time.labels(network=network).observe(response_time)
        else:
            self.basic_metrics.counter_inc('rpc_requests_total', labels={'network': network, 'status': status})
            self.basic_metrics.histogram_observe('rpc_response_time_seconds', response_time, labels={'network': network})
    
    def record_error(self, error_type: str, component: str):
        """Record error metrics"""
        if PROMETHEUS_AVAILABLE:
            self.error_counter.labels(error_type=error_type, component=component).inc()
        else:
            self.basic_metrics.counter_inc('errors_total', labels={'error_type': error_type, 'component': component})
    
    def record_rate_limit_hit(self, limiter_type: str):
        """Record rate limit hit"""
        if PROMETHEUS_AVAILABLE:
            self.rate_limit_hits.labels(limiter_type=limiter_type).inc()
        else:
            self.basic_metrics.counter_inc('rate_limit_hits_total', labels={'limiter_type': limiter_type})
    
    def set_active_connections(self, count: int):
        """Set active connections gauge"""
        if PROMETHEUS_AVAILABLE:
            self.active_connections.set(count)
        else:
            self.basic_metrics.gauge_set('active_connections', count)
    
    def set_cache_hit_rate(self, cache_type: str, hit_rate: float):
        """Set cache hit rate gauge"""
        if PROMETHEUS_AVAILABLE:
            self.cache_hit_rate.labels(cache_type=cache_type).set(hit_rate)
        else:
            self.basic_metrics.gauge_set('cache_hit_rate', hit_rate, labels={'cache_type': cache_type})
    
    def record_performance(self, operation: str, duration: float, **metadata):
        """Record performance metrics"""
        with self.performance_lock:
            self.performance_data[operation].append({
                'timestamp': time.time(),
                'duration': duration,
                'metadata': metadata
            })
    
    def record_health_status(self, status: str, component: str, details: Dict[str, Any]):
        """Record health status"""
        with self.health_lock:
            self.health_history.append({
                'timestamp': datetime.utcnow().isoformat(),
                'status': status,
                'component': component,
                'details': details
            })
    
    def get_performance_summary(self, operation: Optional[str] = None, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary"""
        cutoff_time = time.time() - (hours * 3600)
        
        with self.performance_lock:
            if operation:
                data = [d for d in self.performance_data[operation] if d['timestamp'] > cutoff_time]
            else:
                data = []
                for op_data in self.performance_data.values():
                    data.extend([d for d in op_data if d['timestamp'] > cutoff_time])
            
            if not data:
                return {"message": "No performance data available"}
            
            durations = [d['duration'] for d in data]
            
            return {
                "operation": operation or "all",
                "time_range_hours": hours,
                "total_operations": len(data),
                "avg_duration": sum(durations) / len(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "p95_duration": sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
                "p99_duration": sorted(durations)[int(len(durations) * 0.99)] if durations else 0
            }
    
    def get_health_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get health summary"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with self.health_lock:
            recent_health = [h for h in self.health_history 
                           if datetime.fromisoformat(h['timestamp']) > cutoff_time]
            
            if not recent_health:
                return {"message": "No health data available"}
            
            status_counts = defaultdict(int)
            component_status = defaultdict(lambda: {"healthy": 0, "unhealthy": 0, "error": 0})
            
            for health in recent_health:
                status_counts[health['status']] += 1
                component = health['component']
                component_status[component][health['status']] += 1
            
            return {
                "time_range_hours": hours,
                "total_checks": len(recent_health),
                "status_distribution": dict(status_counts),
                "component_health": dict(component_status)
            }
    
    def get_metrics_export(self) -> str:
        """Export metrics in Prometheus format"""
        if PROMETHEUS_AVAILABLE:
            return generate_latest(self.registry).decode('utf-8')
        else:
            return json.dumps(self.basic_metrics.get_metrics(), indent=2)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics as dictionary"""
        if PROMETHEUS_AVAILABLE:
            # Convert Prometheus metrics to dictionary
            metrics_data = {}
            for metric in self.registry.collect():
                metric_name = metric.name
                metrics_data[metric_name] = {
                    'type': metric.type,
                    'help': metric.documentation,
                    'samples': [
                        {
                            'name': sample.name,
                            'labels': sample.labels,
                            'value': sample.value
                        }
                        for sample in metric.samples
                    ]
                }
            return metrics_data
        else:
            return self.basic_metrics.get_metrics()
    
    def reset_metrics(self):
        """Reset all metrics"""
        if PROMETHEUS_AVAILABLE:
            # Clear registry and reinitialize
            self.registry.clear()
            self._init_metrics()
        else:
            self.basic_metrics = BasicMetrics()
        
        with self.performance_lock:
            self.performance_data.clear()
        
        with self.health_lock:
            self.health_history.clear()
        
        logger.info("Metrics reset")

# Global metrics instance
metrics = HyperKitMetrics()

# Convenience functions
def record_deployment_metrics(network: str, success: bool, duration: float):
    """Record deployment metrics"""
    metrics.record_deployment(network, success, duration)

def record_ai_metrics(provider: str, model: str, success: bool, response_time: float):
    """Record AI provider metrics"""
    metrics.record_ai_request(provider, model, success, response_time)

def record_rpc_metrics(network: str, success: bool, response_time: float):
    """Record RPC metrics"""
    metrics.record_rpc_request(network, success, response_time)

def record_error_metrics(error_type: str, component: str):
    """Record error metrics"""
    metrics.record_error(error_type, component)

def record_rate_limit_metrics(limiter_type: str):
    """Record rate limit metrics"""
    metrics.record_rate_limit_hit(limiter_type)

def get_metrics_summary() -> Dict[str, Any]:
    """Get metrics summary"""
    return {
        "performance": metrics.get_performance_summary(),
        "health": metrics.get_health_summary(),
        "metrics": metrics.get_all_metrics()
    }

# Performance monitoring decorator
def monitor_performance(operation_name: str):
    """Decorator to monitor function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                metrics.record_performance(operation_name, duration, success=True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_performance(operation_name, duration, success=False, error=str(e))
                raise
        return wrapper
    return decorator
