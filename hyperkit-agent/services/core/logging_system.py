"""
Structured Logging System
Comprehensive logging and error reporting for HyperKit Agent
"""

import os
import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum
import sys

class LogLevel(Enum):
    """Log levels for the system"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """Log categories for different system components"""
    AI_AGENT = "ai_agent"
    BLOCKCHAIN = "blockchain"
    STORAGE = "storage"
    SECURITY = "security"
    MONITORING = "monitoring"
    RAG = "rag"
    VERIFICATION = "verification"
    API = "api"
    CLI = "cli"
    SYSTEM = "system"

class HyperKitLogger:
    """
    Comprehensive logging system for HyperKit Agent
    Provides structured logging, error reporting, and monitoring
    """
    
    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup loggers for different components
        self.loggers = {}
        self._setup_loggers()
        
        # Error tracking
        self.error_count = 0
        self.warning_count = 0
        self.critical_errors = []
        
        # Performance tracking
        self.performance_metrics = {}
        
        # Initialize main logger
        self.main_logger = self.get_logger(LogCategory.SYSTEM)
        self.main_logger.info("HyperKit Logger initialized successfully")
    
    def _setup_loggers(self):
        """Setup loggers for all system components"""
        for category in LogCategory:
            logger = self._create_logger(category.value)
            self.loggers[category.value] = logger
    
    def _create_logger(self, category: str) -> logging.Logger:
        """Create a logger for a specific category"""
        logger = logging.getLogger(f"hyperkit.{category}")
        logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        json_formatter = self._create_json_formatter()
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(
            self.log_dir / f"{category}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # JSON file handler for structured logs
        json_handler = logging.FileHandler(
            self.log_dir / f"{category}_structured.json",
            encoding='utf-8'
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(json_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(detailed_formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(json_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _create_json_formatter(self):
        """Create a JSON formatter for structured logging"""
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno
                }
                
                # Add exception info if present
                if record.exc_info:
                    log_entry["exception"] = {
                        "type": record.exc_info[0].__name__,
                        "message": str(record.exc_info[1]),
                        "traceback": traceback.format_exception(*record.exc_info)
                    }
                
                # Add extra fields if present
                if hasattr(record, 'extra_data'):
                    log_entry["extra_data"] = record.extra_data
                
                return json.dumps(log_entry, ensure_ascii=False)
        
        return JSONFormatter()
    
    def get_logger(self, category: LogCategory) -> logging.Logger:
        """Get logger for a specific category"""
        return self.loggers.get(category.value, self.loggers['system'])
    
    def log(self, level: LogLevel, category: LogCategory, message: str, 
            extra_data: Optional[Dict[str, Any]] = None, exception: Optional[Exception] = None):
        """Log a message with structured data"""
        logger = self.get_logger(category)
        
        # Prepare extra data
        log_data = extra_data or {}
        if exception:
            log_data['exception'] = {
                'type': type(exception).__name__,
                'message': str(exception),
                'traceback': traceback.format_exc()
            }
        
        # Update counters
        if level == LogLevel.ERROR:
            self.error_count += 1
        elif level == LogLevel.WARNING:
            self.warning_count += 1
        elif level == LogLevel.CRITICAL:
            self.critical_errors.append({
                'timestamp': datetime.now().isoformat(),
                'category': category.value,
                'message': message,
                'extra_data': log_data
            })
        
        # Log the message
        log_level = getattr(logging, level.value)
        if extra_data:
            logger.log(log_level, message, extra={'extra_data': log_data})
        else:
            logger.log(log_level, message)
    
    def log_ai_operation(self, operation: str, model: str, status: str, 
                        duration: Optional[float] = None, tokens_used: Optional[int] = None):
        """Log AI operations with specific metrics"""
        extra_data = {
            'operation': operation,
            'model': model,
            'status': status,
            'duration_ms': duration * 1000 if duration else None,
            'tokens_used': tokens_used
        }
        
        level = LogLevel.INFO if status == 'success' else LogLevel.ERROR
        self.log(level, LogCategory.AI_AGENT, f"AI {operation} {status}", extra_data)
    
    def log_blockchain_operation(self, operation: str, network: str, tx_hash: Optional[str] = None,
                                gas_used: Optional[int] = None, status: str = 'success'):
        """Log blockchain operations"""
        extra_data = {
            'operation': operation,
            'network': network,
            'transaction_hash': tx_hash,
            'gas_used': gas_used,
            'status': status
        }
        
        level = LogLevel.INFO if status == 'success' else LogLevel.ERROR
        self.log(level, LogCategory.BLOCKCHAIN, f"Blockchain {operation} {status}", extra_data)
    
    def log_security_event(self, event_type: str, severity: str, contract_address: Optional[str] = None,
                          vulnerability: Optional[str] = None, recommendation: Optional[str] = None):
        """Log security events"""
        extra_data = {
            'event_type': event_type,
            'severity': severity,
            'contract_address': contract_address,
            'vulnerability': vulnerability,
            'recommendation': recommendation
        }
        
        level = LogLevel.WARNING if severity in ['LOW', 'MEDIUM'] else LogLevel.ERROR
        self.log(level, LogCategory.SECURITY, f"Security {event_type}: {severity}", extra_data)
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = 'ms',
                              category: LogCategory = LogCategory.SYSTEM):
        """Log performance metrics"""
        extra_data = {
            'metric_name': metric_name,
            'value': value,
            'unit': unit
        }
        
        # Store in performance metrics
        if metric_name not in self.performance_metrics:
            self.performance_metrics[metric_name] = []
        
        self.performance_metrics[metric_name].append({
            'timestamp': datetime.now().isoformat(),
            'value': value,
            'unit': unit
        })
        
        self.log(LogLevel.INFO, category, f"Performance metric: {metric_name} = {value} {unit}", extra_data)
    
    def log_api_request(self, endpoint: str, method: str, status_code: int, 
                       duration: float, user_id: Optional[str] = None):
        """Log API requests"""
        extra_data = {
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'duration_ms': duration * 1000,
            'user_id': user_id
        }
        
        level = LogLevel.INFO if 200 <= status_code < 400 else LogLevel.WARNING
        self.log(level, LogCategory.API, f"API {method} {endpoint} -> {status_code}", extra_data)
    
    def log_error(self, category: LogCategory, message: str, exception: Optional[Exception] = None,
                  extra_data: Optional[Dict[str, Any]] = None):
        """Log an error with full context"""
        self.log(LogLevel.ERROR, category, message, extra_data, exception)
    
    def log_critical(self, category: LogCategory, message: str, exception: Optional[Exception] = None,
                    extra_data: Optional[Dict[str, Any]] = None):
        """Log a critical error"""
        self.log(LogLevel.CRITICAL, category, message, extra_data, exception)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors and warnings"""
        return {
            'total_errors': self.error_count,
            'total_warnings': self.warning_count,
            'critical_errors': len(self.critical_errors),
            'critical_error_details': self.critical_errors[-5:] if self.critical_errors else [],  # Last 5
            'performance_metrics': {
                name: {
                    'count': len(values),
                    'latest': values[-1] if values else None,
                    'average': sum(v['value'] for v in values) / len(values) if values else 0
                }
                for name, values in self.performance_metrics.items()
            }
        }
    
    def export_logs(self, start_date: Optional[datetime] = None, 
                   end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Export logs for analysis"""
        logs = {}
        
        for category in LogCategory:
            log_file = self.log_dir / f"{category.value}_structured.json"
            if log_file.exists():
                category_logs = []
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            
                            # Filter by date if specified
                            if start_date or end_date:
                                log_time = datetime.fromisoformat(log_entry['timestamp'])
                                if start_date and log_time < start_date:
                                    continue
                                if end_date and log_time > end_date:
                                    continue
                            
                            category_logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue
                
                logs[category.value] = category_logs
        
        return logs
    
    def cleanup_old_logs(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """Clean up old log files"""
        import time
        current_time = time.time()
        cutoff_time = current_time - (days_to_keep * 24 * 60 * 60)
        
        cleaned_files = []
        for log_file in self.log_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                cleaned_files.append(str(log_file))
        
        for json_file in self.log_dir.glob("*.json"):
            if json_file.stat().st_mtime < cutoff_time:
                json_file.unlink()
                cleaned_files.append(str(json_file))
        
        return {
            'cleaned_files': cleaned_files,
            'files_removed': len(cleaned_files),
            'days_kept': days_to_keep
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status based on logs"""
        error_summary = self.get_error_summary()
        
        # Determine health status
        if error_summary['critical_errors'] > 0:
            health_status = 'critical'
        elif error_summary['total_errors'] > 10:
            health_status = 'warning'
        elif error_summary['total_warnings'] > 20:
            health_status = 'warning'
        else:
            health_status = 'healthy'
        
        return {
            'status': health_status,
            'error_summary': error_summary,
            'log_files': len(list(self.log_dir.glob("*.log"))),
            'json_files': len(list(self.log_dir.glob("*.json"))),
            'last_updated': datetime.now().isoformat()
        }

# Global logger instance
logger = HyperKitLogger()

# Convenience functions
def log_info(category: LogCategory, message: str, extra_data: Optional[Dict[str, Any]] = None):
    """Log info message"""
    logger.log(LogLevel.INFO, category, message, extra_data)

def log_warning(category: LogCategory, message: str, extra_data: Optional[Dict[str, Any]] = None):
    """Log warning message"""
    logger.log(LogLevel.WARNING, category, message, extra_data)

def log_error(category: LogCategory, message: str, exception: Optional[Exception] = None,
              extra_data: Optional[Dict[str, Any]] = None):
    """Log error message"""
    logger.log_error(category, message, exception, extra_data)

def log_critical(category: LogCategory, message: str, exception: Optional[Exception] = None,
                extra_data: Optional[Dict[str, Any]] = None):
    """Log critical message"""
    logger.log_critical(category, message, exception, extra_data)
