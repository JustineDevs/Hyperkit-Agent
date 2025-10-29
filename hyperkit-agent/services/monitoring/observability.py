"""
Observability and Monitoring System
Tracks metrics, traces, and health checks for HyperAgent
"""

import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class TraceEvent:
    """Single trace event"""
    timestamp: str
    event_type: str
    operation: str
    duration_ms: float
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self):
        return asdict(self)

class ObservabilitySystem:
    """Observability system for HyperAgent"""
    
    def __init__(self, enable_file_logging: bool = True):
        self.enable_file_logging = enable_file_logging
        self.traces: List[TraceEvent] = []
        self.metrics = defaultdict(list)
        self.health_checks: Dict[str, Any] = {}
        
        if enable_file_logging:
            self.log_dir = Path("logs/observability")
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.trace_file = self.log_dir / "traces.jsonl"
            self.metrics_file = self.log_dir / "metrics.json"
    
    def trace_operation(self, operation: str, event_type: str = "operation", 
                       metadata: Dict[str, Any] = None, 
                       func=None, *args, **kwargs):
        """
        Trace an operation execution.
        
        Usage as decorator:
            @obs.trace_operation("generate_contract")
            def generate(...):
                ...
        """
        if func is None:
            # Used as decorator
            def decorator(f):
                async def async_wrapper(*args, **kwargs):
                    start = time.time()
                    success = True
                    error = None
                    try:
                        result = await f(*args, **kwargs)
                        return result
                    except Exception as e:
                        success = False
                        error = str(e)
                        raise
                    finally:
                        duration = (time.time() - start) * 1000
                        event = TraceEvent(
                            timestamp=datetime.now().isoformat(),
                            event_type=event_type,
                            operation=operation or f.__name__,
                            duration_ms=duration,
                            success=success,
                            error=error,
                            metadata=metadata
                        )
                        self._record_trace(event)
                
                def sync_wrapper(*args, **kwargs):
                    start = time.time()
                    success = True
                    error = None
                    try:
                        result = f(*args, **kwargs)
                        return result
                    except Exception as e:
                        success = False
                        error = str(e)
                        raise
                    finally:
                        duration = (time.time() - start) * 1000
                        event = TraceEvent(
                            timestamp=datetime.now().isoformat(),
                            event_type=event_type,
                            operation=operation or f.__name__,
                            duration_ms=duration,
                            success=success,
                            error=error,
                            metadata=metadata
                        )
                        self._record_trace(event)
                
                import inspect
                if inspect.iscoroutinefunction(f):
                    return async_wrapper
                return sync_wrapper
            
            return decorator
        
        # Used as context manager or direct call
        start = time.time()
        try:
            result = func(*args, **kwargs)
            duration = (time.time() - start) * 1000
            event = TraceEvent(
                timestamp=datetime.now().isoformat(),
                event_type=event_type,
                operation=operation,
                duration_ms=duration,
                success=True,
                metadata=metadata
            )
            self._record_trace(event)
            return result
        except Exception as e:
            duration = (time.time() - start) * 1000
            event = TraceEvent(
                timestamp=datetime.now().isoformat(),
                event_type=event_type,
                operation=operation,
                duration_ms=duration,
                success=False,
                error=str(e),
                metadata=metadata
            )
            self._record_trace(event)
            raise
    
    def _record_trace(self, event: TraceEvent):
        """Record trace event"""
        self.traces.append(event)
        
        # Keep only last 1000 traces in memory
        if len(self.traces) > 1000:
            self.traces = self.traces[-1000:]
        
        # Write to file if enabled
        if self.enable_file_logging:
            try:
                with open(self.trace_file, 'a') as f:
                    f.write(json.dumps(event.to_dict()) + '\n')
            except Exception as e:
                logger.warning(f"Failed to write trace: {e}")
    
    def record_metric(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Record a metric"""
        metric_entry = {
            "timestamp": datetime.now().isoformat(),
            "value": value,
            "labels": labels or {}
        }
        self.metrics[metric_name].append(metric_entry)
        
        # Keep only last 1000 entries per metric
        if len(self.metrics[metric_name]) > 1000:
            self.metrics[metric_name] = self.metrics[metric_name][-1000:]
        
        # Write to file if enabled
        if self.enable_file_logging:
            try:
                with open(self.metrics_file, 'w') as f:
                    json.dump(dict(self.metrics), f, indent=2)
            except Exception as e:
                logger.warning(f"Failed to write metrics: {e}")
    
    def record_health_check(self, component: str, status: str, details: Dict[str, Any] = None):
        """Record health check result"""
        self.health_checks[component] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get observability summary"""
        recent_traces = self.traces[-100] if len(self.traces) > 100 else self.traces
        
        success_count = sum(1 for t in recent_traces if t.success)
        failure_count = len(recent_traces) - success_count
        
        avg_duration = sum(t.duration_ms for t in recent_traces) / len(recent_traces) if recent_traces else 0
        
        return {
            "traces": {
                "total": len(self.traces),
                "recent": len(recent_traces),
                "success_rate": success_count / len(recent_traces) if recent_traces else 0,
                "failure_count": failure_count,
                "avg_duration_ms": avg_duration
            },
            "metrics": {
                name: {
                    "count": len(entries),
                    "latest": entries[-1] if entries else None
                }
                for name, entries in self.metrics.items()
            },
            "health_checks": self.health_checks
        }

# Global observability instance
_observability = None

def get_observability() -> ObservabilitySystem:
    """Get global observability instance"""
    global _observability
    if _observability is None:
        _observability = ObservabilitySystem()
    return _observability

