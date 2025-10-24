"""
Global error handling for HyperKit AI Agent
"""

import logging
import traceback
from typing import Dict, Any, Optional
from functools import wraps
import asyncio
from datetime import datetime

from .errors import (
    HyperKitError, ConfigurationError, NetworkError, 
    ContractGenerationError, AuditError, DeploymentError,
    VerificationError, TestingError, ValidationError,
    SecurityError, RateLimitError, AuthenticationError, WorkflowError
)

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling and recovery"""
    
    def __init__(self):
        self.error_counts = {}
        self.max_retries = 3
        self.retry_delays = [1, 2, 5]  # seconds
    
    def handle_error(self, error: Exception, context: str = "", retry_count: int = 0) -> Dict[str, Any]:
        """
        Handle errors with appropriate recovery strategies
        
        Args:
            error: The exception that occurred
            context: Context where error occurred
            retry_count: Current retry attempt
            
        Returns:
            Dict with error details and recovery suggestions
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # Log the error
        logger.error(f"Error in {context}: {error_type}: {error_message}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # Track error frequency
        error_key = f"{context}:{error_type}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Determine recovery strategy
        recovery_strategy = self._get_recovery_strategy(error, context)
        
        return {
            "error_type": error_type,
            "error_message": error_message,
            "context": context,
            "retry_count": retry_count,
            "recovery_strategy": recovery_strategy,
            "can_retry": retry_count < self.max_retries,
            "timestamp": datetime.now().isoformat(),
            "traceback": traceback.format_exc()
        }
    
    def _get_recovery_strategy(self, error: Exception, context: str) -> str:
        """Determine appropriate recovery strategy based on error type"""
        
        if isinstance(error, ConfigurationError):
            return "Check configuration files and environment variables"
        
        elif isinstance(error, NetworkError):
            return "Check network connectivity and RPC endpoints"
        
        elif isinstance(error, ContractGenerationError):
            return "Try different prompt or check AI provider configuration"
        
        elif isinstance(error, AuditError):
            return "Review contract code for security issues"
        
        elif isinstance(error, DeploymentError):
            return "Check network status, gas settings, and account balance"
        
        elif isinstance(error, VerificationError):
            return "Try manual verification or check explorer API"
        
        elif isinstance(error, TestingError):
            return "Check contract deployment and RPC connectivity"
        
        elif isinstance(error, ValidationError):
            return "Check input parameters and data format"
        
        elif isinstance(error, SecurityError):
            return "Review security settings and access controls"
        
        elif isinstance(error, RateLimitError):
            return "Wait before retrying or check rate limits"
        
        elif isinstance(error, AuthenticationError):
            return "Check API keys and authentication credentials"
        
        elif isinstance(error, WorkflowError):
            return "Review workflow configuration and dependencies"
        
        else:
            return "Check logs and system status"
    
    def should_retry(self, error: Exception, retry_count: int) -> bool:
        """Determine if operation should be retried"""
        
        if retry_count >= self.max_retries:
            return False
        
        # Don't retry certain error types
        non_retryable_errors = [
            ConfigurationError, ValidationError, SecurityError, AuthenticationError
        ]
        
        if any(isinstance(error, error_type) for error_type in non_retryable_errors):
            return False
        
        return True
    
    def get_retry_delay(self, retry_count: int) -> float:
        """Get delay before retry (exponential backoff)"""
        if retry_count < len(self.retry_delays):
            return self.retry_delays[retry_count]
        return self.retry_delays[-1] * (2 ** (retry_count - len(self.retry_delays) + 1))

def safe_operation(operation_name: str):
    """Decorator for safe operation execution with error handling"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            error_handler = ErrorHandler()
            retry_count = 0
            
            while retry_count <= error_handler.max_retries:
                try:
                    return await func(*args, **kwargs)
                
                except Exception as e:
                    error_info = error_handler.handle_error(e, operation_name, retry_count)
                    
                    if not error_handler.should_retry(e, retry_count):
                        logger.error(f"Operation {operation_name} failed permanently: {error_info}")
                        raise
                    
                    retry_count += 1
                    delay = error_handler.get_retry_delay(retry_count - 1)
                    
                    logger.warning(f"Retrying {operation_name} in {delay}s (attempt {retry_count})")
                    await asyncio.sleep(delay)
            
            # Should never reach here
            raise Exception(f"Operation {operation_name} failed after {retry_count} retries")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            error_handler = ErrorHandler()
            retry_count = 0
            
            while retry_count <= error_handler.max_retries:
                try:
                    return func(*args, **kwargs)
                
                except Exception as e:
                    error_info = error_handler.handle_error(e, operation_name, retry_count)
                    
                    if not error_handler.should_retry(e, retry_count):
                        logger.error(f"Operation {operation_name} failed permanently: {error_info}")
                        raise
                    
                    retry_count += 1
                    delay = error_handler.get_retry_delay(retry_count - 1)
                    
                    logger.warning(f"Retrying {operation_name} in {delay}s (attempt {retry_count})")
                    import time
                    time.sleep(delay)
            
            # Should never reach here
            raise Exception(f"Operation {operation_name} failed after {retry_count} retries")
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def handle_workflow_error(stage: str, error: Exception) -> Dict[str, Any]:
    """Handle workflow-specific errors"""
    
    error_handler = ErrorHandler()
    error_info = error_handler.handle_error(error, f"workflow_stage_{stage}")
    
    # Add workflow-specific context
    error_info.update({
        "workflow_stage": stage,
        "workflow_failed": True,
        "recovery_actions": [
            "Check previous stage results",
            "Verify network connectivity",
            "Review configuration",
            "Check resource availability"
        ]
    })
    
    return error_info

def validate_input(prompt: str, network: str, **kwargs) -> None:
    """Validate workflow inputs"""
    
    if not prompt or not prompt.strip():
        raise ValidationError("Prompt cannot be empty")
    
    if len(prompt) > 1000:
        raise ValidationError("Prompt too long (max 1000 characters)")
    
    valid_networks = ["hyperion", "polygon", "arbitrum", "ethereum", "metis", "lazai"]
    if network not in valid_networks:
        raise ValidationError(f"Invalid network: {network}. Valid options: {valid_networks}")
    
    # Check for potentially malicious content
    dangerous_patterns = [
        "rm -rf", "sudo", "chmod", "wget", "curl", "bash", "sh",
        "eval(", "exec(", "system(", "shell_exec"
    ]
    
    prompt_lower = prompt.lower()
    for pattern in dangerous_patterns:
        if pattern in prompt_lower:
            raise SecurityError(f"Potentially dangerous content detected: {pattern}")

def log_operation(operation: str, details: Dict[str, Any]):
    """Log operation details for audit trail"""
    
    logger.info(f"Operation: {operation}")
    logger.info(f"Details: {details}")
    
    # In production, this would go to a proper audit log
    audit_log = {
        "timestamp": datetime.now().isoformat(),
        "operation": operation,
        "details": details,
        "user_id": details.get("user_id", "anonymous"),
        "session_id": details.get("session_id", "unknown")
    }
    
    logger.info(f"Audit log: {audit_log}")
