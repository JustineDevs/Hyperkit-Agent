"""
Structured Logging Setup for HyperKit AI Agent
Production-ready logging with JSON format and proper levels
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from pythonjsonlogger import jsonlogger
import structlog
from datetime import datetime

class HyperKitJSONFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for HyperKit logs"""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add HyperKit specific fields
        if hasattr(record, 'component'):
            log_record['component'] = record.component
        if hasattr(record, 'operation'):
            log_record['operation'] = record.operation
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'network'):
            log_record['network'] = record.network
        if hasattr(record, 'contract_address'):
            log_record['contract_address'] = record.contract_address
        if hasattr(record, 'transaction_hash'):
            log_record['transaction_hash'] = record.transaction_hash

class HyperKitLogger:
    """Enhanced logger for HyperKit with structured logging"""
    
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup log handlers"""
        # Console handler with JSON formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(HyperKitJSONFormatter())
        self.logger.addHandler(console_handler)
        
        # File handler for persistent logs
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(
            log_dir / f"hyperkit_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setFormatter(HyperKitJSONFormatter())
        self.logger.addHandler(file_handler)
    
    def info(self, message: str, **kwargs):
        """Log info message with additional context"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with additional context"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with additional context"""
        self.logger.error(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with additional context"""
        self.logger.debug(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with additional context"""
        self.logger.critical(message, extra=kwargs)

def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    log_file: Optional[str] = None,
    enable_console: bool = True
) -> logging.Logger:
    """
    Setup structured logging for HyperKit
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Log format (json, text)
        log_file: Optional log file path
        enable_console: Whether to enable console logging
        
    Returns:
        Configured logger instance
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        if format_type == "json":
            console_handler.setFormatter(HyperKitJSONFormatter())
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        if format_type == "json":
            file_handler.setFormatter(HyperKitJSONFormatter())
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger

def get_logger(name: str) -> HyperKitLogger:
    """
    Get a HyperKit logger instance
    
    Args:
        name: Logger name
        
    Returns:
        HyperKitLogger instance
    """
    return HyperKitLogger(name)

def log_deployment(
    logger: HyperKitLogger,
    contract_name: str,
    network: str,
    contract_address: str,
    transaction_hash: str,
    gas_used: int,
    success: bool = True
):
    """Log deployment information"""
    logger.info(
        f"Contract deployment {'successful' if success else 'failed'}",
        component="deployment",
        operation="deploy_contract",
        contract_name=contract_name,
        network=network,
        contract_address=contract_address,
        transaction_hash=transaction_hash,
        gas_used=gas_used,
        success=success
    )

def log_ai_request(
    logger: HyperKitLogger,
    provider: str,
    model: str,
    tokens_used: int,
    success: bool = True,
    error: Optional[str] = None
):
    """Log AI provider request"""
    logger.info(
        f"AI request {'successful' if success else 'failed'}",
        component="ai_provider",
        operation="generate_response",
        provider=provider,
        model=model,
        tokens_used=tokens_used,
        success=success,
        error=error
    )

def log_network_operation(
    logger: HyperKitLogger,
    operation: str,
    network: str,
    success: bool = True,
    error: Optional[str] = None
):
    """Log network operation"""
    logger.info(
        f"Network operation {operation} {'successful' if success else 'failed'}",
        component="network",
        operation=operation,
        network=network,
        success=success,
        error=error
    )

def log_security_event(
    logger: HyperKitLogger,
    event_type: str,
    severity: str,
    details: Dict[str, Any]
):
    """Log security-related events"""
    logger.warning(
        f"Security event: {event_type}",
        component="security",
        operation="security_event",
        event_type=event_type,
        severity=severity,
        details=details
    )

def log_performance(
    logger: HyperKitLogger,
    operation: str,
    duration: float,
    component: str,
    **metrics
):
    """Log performance metrics"""
    logger.info(
        f"Performance metric: {operation}",
        component=component,
        operation=operation,
        duration=duration,
        **metrics
    )

# Configure structlog for advanced logging
def configure_structlog():
    """Configure structlog for advanced structured logging"""
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

# Initialize logging on import
def initialize_logging():
    """Initialize logging system"""
    setup_logging()
    configure_structlog()

# Auto-initialize when module is imported
initialize_logging()
