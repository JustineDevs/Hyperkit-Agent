"""
Structured logging setup for HyperKit AI Agent production system.

This module configures structured JSON logging for production monitoring
and debugging.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
import structlog
from pythonjsonlogger import jsonlogger


class StructuredFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add service name
        log_record['service'] = 'hyperkit-agent'
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add request ID if available
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        
        # Add user ID if available
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        
        # Add deployment ID if available
        if hasattr(record, 'deployment_id'):
            log_record['deployment_id'] = record.deployment_id


def setup_structured_logging():
    """Setup structured logging for production."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    console_handler.setLevel(logging.INFO)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    
    # Create logger for this module
    logger = logging.getLogger(__name__)
    logger.info("Structured logging configured successfully")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with structured logging."""
    return logging.getLogger(name)


def log_request(method: str, url: str, status_code: int, duration: float, **kwargs):
    """Log HTTP request with structured data."""
    logger = get_logger("request")
    logger.info(
        "HTTP request",
        extra={
            "method": method,
            "url": url,
            "status_code": status_code,
            "duration": duration,
            **kwargs
        }
    )


def log_deployment(user_id: str, deployment_id: str, action: str, **kwargs):
    """Log deployment action with structured data."""
    logger = get_logger("deployment")
    logger.info(
        f"Deployment {action}",
        extra={
            "user_id": user_id,
            "deployment_id": deployment_id,
            "action": action,
            **kwargs
        }
    )


def log_security(event: str, user_id: str = None, ip_address: str = None, **kwargs):
    """Log security event with structured data."""
    logger = get_logger("security")
    logger.warning(
        f"Security event: {event}",
        extra={
            "event": event,
            "user_id": user_id,
            "ip_address": ip_address,
            **kwargs
        }
    )


def log_error(error: Exception, context: Dict[str, Any] = None):
    """Log error with structured data."""
    logger = get_logger("error")
    logger.error(
        f"Error occurred: {str(error)}",
        extra={
            "error": str(error),
            "error_type": type(error).__name__,
            "context": context or {}
        },
        exc_info=True
    )
