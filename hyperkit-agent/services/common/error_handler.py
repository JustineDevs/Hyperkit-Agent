"""
Global Error Handler and Retry Logic for HyperKit AI Agent
Production-ready error handling with retry mechanisms
"""

import functools
import time
import logging
from typing import Callable, Any, Optional, Union, List
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)

class HyperKitError(Exception):
    """Base exception for HyperKit errors"""
    pass

class ConfigurationError(HyperKitError):
    """Configuration-related errors"""
    pass

class NetworkError(HyperKitError):
    """Network-related errors"""
    pass

class DeploymentError(HyperKitError):
    """Deployment-related errors"""
    pass

class AIProviderError(HyperKitError):
    """AI provider-related errors"""
    pass

class ValidationError(HyperKitError):
    """Validation-related errors"""
    pass

def retry_on_error(
    max_retries: int = 3, 
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    retry_delay: float = 1.0
):
    """
    Decorator for automatic retry with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff
        exceptions: Tuple of exception types to retry on
        retry_delay: Initial delay between retries in seconds
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retries = 0
            wait_time = retry_delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"Failed after {max_retries} retries: {e}")
                        raise
                    
                    logger.warning(f"Attempt {retries} failed, retrying in {wait_time:.2f}s... Error: {e}")
                    time.sleep(wait_time)
                    wait_time *= backoff_factor
                except Exception as e:
                    # Don't retry on unexpected exceptions
                    logger.error(f"Unexpected error in {func.__name__}: {e}")
                    raise
            
            return None
        return wrapper
    return decorator

def retry_with_tenacity(
    max_attempts: int = 3,
    wait_min: float = 1.0,
    wait_max: float = 60.0,
    exceptions: tuple = (Exception,)
):
    """
    Advanced retry decorator using tenacity library
    
    Args:
        max_attempts: Maximum number of attempts
        wait_min: Minimum wait time in seconds
        wait_max: Maximum wait time in seconds
        exceptions: Tuple of exception types to retry on
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=wait_min, max=wait_max),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )

class ErrorHandler:
    """Centralized error handling and recovery"""
    
    def __init__(self):
        self.error_counts = {}
        self.circuit_breakers = {}
    
    def handle_error(self, error: Exception, context: str = "") -> dict:
        """
        Handle and categorize errors
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            
        Returns:
            Dictionary with error information and recovery suggestions
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # Track error counts
        error_key = f"{error_type}:{context}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Categorize error
        if isinstance(error, ConfigurationError):
            return self._handle_configuration_error(error, context)
        elif isinstance(error, NetworkError):
            return self._handle_network_error(error, context)
        elif isinstance(error, DeploymentError):
            return self._handle_deployment_error(error, context)
        elif isinstance(error, AIProviderError):
            return self._handle_ai_provider_error(error, context)
        elif isinstance(error, ValidationError):
            return self._handle_validation_error(error, context)
        else:
            return self._handle_generic_error(error, context)
    
    def _handle_configuration_error(self, error: ConfigurationError, context: str) -> dict:
        """Handle configuration-related errors"""
        return {
            "error_type": "ConfigurationError",
            "message": str(error),
            "context": context,
            "severity": "high",
            "recovery_suggestions": [
                "Check configuration file format",
                "Verify required environment variables",
                "Validate network configurations",
                "Check API key settings"
            ],
            "retry_recommended": False
        }
    
    def _handle_network_error(self, error: NetworkError, context: str) -> dict:
        """Handle network-related errors"""
        return {
            "error_type": "NetworkError",
            "message": str(error),
            "context": context,
            "severity": "medium",
            "recovery_suggestions": [
                "Check network connectivity",
                "Verify RPC endpoint URL",
                "Check if network is online",
                "Try different RPC endpoint"
            ],
            "retry_recommended": True
        }
    
    def _handle_deployment_error(self, error: DeploymentError, context: str) -> dict:
        """Handle deployment-related errors"""
        return {
            "error_type": "DeploymentError",
            "message": str(error),
            "context": context,
            "severity": "high",
            "recovery_suggestions": [
                "Check contract source code",
                "Verify gas settings",
                "Check account balance",
                "Validate contract parameters"
            ],
            "retry_recommended": True
        }
    
    def _handle_ai_provider_error(self, error: AIProviderError, context: str) -> dict:
        """Handle AI provider-related errors"""
        return {
            "error_type": "AIProviderError",
            "message": str(error),
            "context": context,
            "severity": "medium",
            "recovery_suggestions": [
                "Check API key validity",
                "Verify API quota limits",
                "Check provider service status",
                "Try different AI provider"
            ],
            "retry_recommended": True
        }
    
    def _handle_validation_error(self, error: ValidationError, context: str) -> dict:
        """Handle validation-related errors"""
        return {
            "error_type": "ValidationError",
            "message": str(error),
            "context": context,
            "severity": "high",
            "recovery_suggestions": [
                "Check input parameters",
                "Verify data types",
                "Validate required fields",
                "Check data format"
            ],
            "retry_recommended": False
        }
    
    def _handle_generic_error(self, error: Exception, context: str) -> dict:
        """Handle generic errors"""
        return {
            "error_type": type(error).__name__,
            "message": str(error),
            "context": context,
            "severity": "unknown",
            "recovery_suggestions": [
                "Check logs for more details",
                "Verify system requirements",
                "Contact support if issue persists"
            ],
            "retry_recommended": False
        }
    
    def get_error_stats(self) -> dict:
        """Get error statistics"""
        return {
            "total_errors": sum(self.error_counts.values()),
            "error_counts": self.error_counts.copy(),
            "circuit_breakers": self.circuit_breakers.copy()
        }
    
    def reset_stats(self):
        """Reset error statistics"""
        self.error_counts.clear()
        self.circuit_breakers.clear()

# Global error handler instance
error_handler = ErrorHandler()

def safe_execute(func: Callable, *args, **kwargs) -> dict:
    """
    Safely execute a function with error handling
    
    Args:
        func: Function to execute
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Dictionary with result or error information
    """
    try:
        result = func(*args, **kwargs)
        return {
            "success": True,
            "result": result,
            "error": None
        }
    except Exception as e:
        error_info = error_handler.handle_error(e, f"{func.__name__}")
        logger.error(f"Error in {func.__name__}: {error_info}")
        return {
            "success": False,
            "result": None,
            "error": error_info
        }

def with_error_handling(func: Callable) -> Callable:
    """
    Decorator to add error handling to functions
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_info = error_handler.handle_error(e, func.__name__)
            logger.error(f"Error in {func.__name__}: {error_info}")
            raise
    return wrapper
