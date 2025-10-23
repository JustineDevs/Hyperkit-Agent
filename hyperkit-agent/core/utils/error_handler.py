"""
Enhanced Error Handling System for HyperKit AI Agent

This module provides comprehensive error handling, classification, and recovery
mechanisms for the HyperKit AI Agent.
"""

import logging
import traceback
import json
from typing import Dict, Any, Optional, List, Union, Callable
from enum import Enum
from datetime import datetime
import functools
import asyncio
from pathlib import Path


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    NETWORK = "network"
    API = "api"
    VALIDATION = "validation"
    COMPILATION = "compilation"
    DEPLOYMENT = "deployment"
    SECURITY = "security"
    CONFIGURATION = "configuration"
    FILE_SYSTEM = "file_system"
    PERMISSION = "permission"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


class ErrorContext:
    """Context information for error handling."""
    
    def __init__(self, operation: str, component: str, user_id: Optional[str] = None):
        self.operation = operation
        self.component = component
        self.user_id = user_id
        self.timestamp = datetime.now()
        self.metadata = {}


class HyperKitError(Exception):
    """Base exception class for HyperKit AI Agent."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[ErrorContext] = None,
        original_error: Optional[Exception] = None,
        recovery_suggestion: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context
        self.original_error = original_error
        self.recovery_suggestion = recovery_suggestion
        self.timestamp = datetime.now()
        self.error_id = self._generate_error_id()
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID."""
        import uuid
        return f"HK-{uuid.uuid4().hex[:8].upper()}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging."""
        return {
            'error_id': self.error_id,
            'message': self.message,
            'category': self.category.value,
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat(),
            'context': {
                'operation': self.context.operation if self.context else None,
                'component': self.context.component if self.context else None,
                'user_id': self.context.user_id if self.context else None,
                'metadata': self.context.metadata if self.context else {}
            } if self.context else None,
            'original_error': str(self.original_error) if self.original_error else None,
            'recovery_suggestion': self.recovery_suggestion,
            'traceback': traceback.format_exc()
        }


class ErrorHandler:
    """Comprehensive error handling system."""
    
    def __init__(self, log_file: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.error_log = []
        self.recovery_strategies = {}
        self.circuit_breakers = {}
        self.retry_configs = {}
        
        # Setup logging
        if log_file:
            self._setup_file_logging(log_file)
        
        # Initialize recovery strategies
        self._setup_recovery_strategies()
    
    def _setup_file_logging(self, log_file: str):
        """Setup file logging for errors."""
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def _setup_recovery_strategies(self):
        """Setup automatic recovery strategies."""
        self.recovery_strategies = {
            ErrorCategory.NETWORK: self._recover_network_error,
            ErrorCategory.API: self._recover_api_error,
            ErrorCategory.CONFIGURATION: self._recover_configuration_error,
            ErrorCategory.FILE_SYSTEM: self._recover_filesystem_error,
            ErrorCategory.PERMISSION: self._recover_permission_error
        }
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None,
        auto_recover: bool = True
    ) -> HyperKitError:
        """
        Handle and classify an error.
        
        Args:
            error: The original exception
            context: Error context information
            auto_recover: Whether to attempt automatic recovery
            
        Returns:
            Classified HyperKitError
        """
        # Classify the error
        category = self._classify_error(error)
        severity = self._determine_severity(error, category)
        
        # Create HyperKitError
        hk_error = HyperKitError(
            message=str(error),
            category=category,
            severity=severity,
            context=context,
            original_error=error,
            recovery_suggestion=self._get_recovery_suggestion(category, error)
        )
        
        # Log the error
        self._log_error(hk_error)
        
        # Store in error log
        self.error_log.append(hk_error)
        
        # Attempt recovery if enabled
        if auto_recover and category in self.recovery_strategies:
            try:
                recovery_result = self.recovery_strategies[category](hk_error)
                if recovery_result:
                    self.logger.info(f"Error {hk_error.error_id} recovered successfully")
            except Exception as recovery_error:
                self.logger.error(f"Recovery failed for error {hk_error.error_id}: {recovery_error}")
        
        return hk_error
    
    def _classify_error(self, error: Exception) -> ErrorCategory:
        """Classify error into categories."""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Network errors
        if any(keyword in error_message for keyword in ['connection', 'timeout', 'network', 'unreachable']):
            return ErrorCategory.NETWORK
        
        # API errors
        if any(keyword in error_message for keyword in ['api', 'http', 'request', 'response', 'endpoint']):
            return ErrorCategory.API
        
        # Validation errors
        if any(keyword in error_message for keyword in ['validation', 'invalid', 'required', 'missing']):
            return ErrorCategory.VALIDATION
        
        # Compilation errors
        if any(keyword in error_message for keyword in ['compilation', 'syntax', 'solidity', 'compile']):
            return ErrorCategory.COMPILATION
        
        # Deployment errors
        if any(keyword in error_message for keyword in ['deploy', 'deployment', 'transaction', 'gas']):
            return ErrorCategory.DEPLOYMENT
        
        # Security errors
        if any(keyword in error_message for keyword in ['security', 'unauthorized', 'forbidden', 'access']):
            return ErrorCategory.SECURITY
        
        # Configuration errors
        if any(keyword in error_message for keyword in ['config', 'configuration', 'setting', 'environment']):
            return ErrorCategory.CONFIGURATION
        
        # File system errors
        if any(keyword in error_message for keyword in ['file', 'directory', 'path', 'permission']):
            return ErrorCategory.FILE_SYSTEM
        
        return ErrorCategory.UNKNOWN
    
    def _determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity level."""
        error_message = str(error).lower()
        
        # Critical errors
        if any(keyword in error_message for keyword in ['critical', 'fatal', 'crash', 'abort']):
            return ErrorSeverity.CRITICAL
        
        # High severity
        if category in [ErrorCategory.SECURITY, ErrorCategory.DEPLOYMENT]:
            return ErrorSeverity.HIGH
        
        if any(keyword in error_message for keyword in ['error', 'failed', 'exception']):
            return ErrorSeverity.HIGH
        
        # Medium severity
        if category in [ErrorCategory.NETWORK, ErrorCategory.API, ErrorCategory.COMPILATION]:
            return ErrorSeverity.MEDIUM
        
        # Low severity
        if category in [ErrorCategory.VALIDATION, ErrorCategory.CONFIGURATION]:
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    def _get_recovery_suggestion(self, category: ErrorCategory, error: Exception) -> str:
        """Get recovery suggestion based on error category."""
        suggestions = {
            ErrorCategory.NETWORK: "Check network connection and retry. Consider using a different RPC endpoint.",
            ErrorCategory.API: "Verify API keys and endpoints. Check rate limits and quotas.",
            ErrorCategory.VALIDATION: "Review input parameters and ensure they meet requirements.",
            ErrorCategory.COMPILATION: "Check Solidity syntax and dependencies. Ensure compiler version compatibility.",
            ErrorCategory.DEPLOYMENT: "Verify gas settings and account balance. Check contract constructor parameters.",
            ErrorCategory.SECURITY: "Review access controls and permissions. Check for security vulnerabilities.",
            ErrorCategory.CONFIGURATION: "Verify configuration files and environment variables.",
            ErrorCategory.FILE_SYSTEM: "Check file permissions and disk space. Ensure paths exist.",
            ErrorCategory.PERMISSION: "Verify user permissions and access rights.",
            ErrorCategory.RESOURCE: "Check system resources (memory, CPU, disk space).",
            ErrorCategory.UNKNOWN: "Review error logs and contact support if issue persists."
        }
        
        return suggestions.get(category, "Review error details and try again.")
    
    def _log_error(self, error: HyperKitError):
        """Log error with appropriate level."""
        error_data = error.to_dict()
        
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"CRITICAL ERROR {error.error_id}: {error.message}", extra=error_data)
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(f"HIGH ERROR {error.error_id}: {error.message}", extra=error_data)
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"MEDIUM ERROR {error.error_id}: {error.message}", extra=error_data)
        else:
            self.logger.info(f"LOW ERROR {error.error_id}: {error.message}", extra=error_data)
    
    def _recover_network_error(self, error: HyperKitError) -> bool:
        """Attempt to recover from network errors."""
        # Implement network recovery logic
        self.logger.info(f"Attempting network recovery for error {error.error_id}")
        return False  # Placeholder
    
    def _recover_api_error(self, error: HyperKitError) -> bool:
        """Attempt to recover from API errors."""
        # Implement API recovery logic
        self.logger.info(f"Attempting API recovery for error {error.error_id}")
        return False  # Placeholder
    
    def _recover_configuration_error(self, error: HyperKitError) -> bool:
        """Attempt to recover from configuration errors."""
        # Implement configuration recovery logic
        self.logger.info(f"Attempting configuration recovery for error {error.error_id}")
        return False  # Placeholder
    
    def _recover_filesystem_error(self, error: HyperKitError) -> bool:
        """Attempt to recover from filesystem errors."""
        # Implement filesystem recovery logic
        self.logger.info(f"Attempting filesystem recovery for error {error.error_id}")
        return False  # Placeholder
    
    def _recover_permission_error(self, error: HyperKitError) -> bool:
        """Attempt to recover from permission errors."""
        # Implement permission recovery logic
        self.logger.info(f"Attempting permission recovery for error {error.error_id}")
        return False  # Placeholder
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics and analytics."""
        if not self.error_log:
            return {'total_errors': 0}
        
        total_errors = len(self.error_log)
        severity_counts = {}
        category_counts = {}
        
        for error in self.error_log:
            severity = error.severity.value
            category = error.category.value
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            'total_errors': total_errors,
            'severity_distribution': severity_counts,
            'category_distribution': category_counts,
            'recent_errors': [error.to_dict() for error in self.error_log[-10:]]
        }
    
    def export_error_log(self, output_path: str) -> bool:
        """Export error log to JSON file."""
        try:
            error_data = [error.to_dict() for error in self.error_log]
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Failed to export error log: {e}")
            return False

    def create_validation_error(self, field: str, value: str, errors: str) -> HyperKitError:
        """Create a validation error."""
        context = ErrorContext("validation", "validator")
        context.metadata = {"field": field, "value": value}
        return HyperKitError(
            message=f"Validation failed for {field}: {errors}",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            context=context,
            recovery_suggestion=f"Please provide a valid {field}"
        )

    def create_deployment_error(self, contract_type: str, network: str, error: Exception) -> HyperKitError:
        """Create a deployment error."""
        context = ErrorContext("deployment", "deployer")
        context.metadata = {"contract_type": contract_type, "network": network}
        return HyperKitError(
            message=f"Failed to deploy {contract_type} to {network}: {str(error)}",
            category=ErrorCategory.DEPLOYMENT,
            severity=ErrorSeverity.HIGH,
            context=context,
            original_error=error,
            recovery_suggestion="Check network configuration and contract code"
        )

    def format_error_response(self, error: HyperKitError) -> Dict[str, Any]:
        """Format error response for API."""
        return {
            "success": False,
            "error": {
                "id": error.error_id,
                "message": error.message,
                "category": error.category.value,
                "severity": error.severity.value,
                "recovery_suggestion": error.recovery_suggestion
            }
        }


def error_handler(
    context: Optional[ErrorContext] = None,
    auto_recover: bool = True,
    reraise: bool = False
):
    """Decorator for automatic error handling."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = ErrorHandler()
                hk_error = handler.handle_error(e, context, auto_recover)
                
                if reraise:
                    raise hk_error
                else:
                    return None
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                handler = ErrorHandler()
                hk_error = handler.handle_error(e, context, auto_recover)
                
                if reraise:
                    raise hk_error
                else:
                    return None
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator


def create_error_context(operation: str, component: str, **metadata) -> ErrorContext:
    """Create error context with metadata."""
    context = ErrorContext(operation, component)
    context.metadata.update(metadata)
    return context


def main():
    """Test the error handling system."""
    handler = ErrorHandler()
    
    # Test different error types
    test_errors = [
        ConnectionError("Network connection failed"),
        ValueError("Invalid input parameter"),
        FileNotFoundError("Configuration file not found"),
        PermissionError("Access denied"),
        RuntimeError("Unknown runtime error")
    ]
    
    for error in test_errors:
        context = create_error_context("test_operation", "test_component")
        hk_error = handler.handle_error(error, context)
        print(f"Handled error: {hk_error.error_id} - {hk_error.message}")
    
    # Print statistics
    stats = handler.get_error_statistics()
    print(f"\nError Statistics: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    main()