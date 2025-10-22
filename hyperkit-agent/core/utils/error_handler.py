"""
Error Handling and User Feedback Utilities
Provides comprehensive error handling and user-friendly feedback
"""

import logging
import traceback
from typing import Dict, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories"""

    VALIDATION = "validation"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RESOURCE = "resource"
    CONFIGURATION = "configuration"
    EXTERNAL_SERVICE = "external_service"
    INTERNAL = "internal"
    USER_INPUT = "user_input"
    DEPLOYMENT = "deployment"
    AUDIT = "audit"
    GENERATION = "generation"


@dataclass
class ErrorInfo:
    """Error information structure"""

    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    user_message: str
    technical_details: str
    suggestions: list
    timestamp: datetime
    context: Dict[str, Any]


class ErrorHandler:
    """
    Comprehensive error handling and user feedback system
    """

    def __init__(self):
        self.error_patterns = self._initialize_error_patterns()
        self.suggestion_templates = self._initialize_suggestion_templates()

    def _initialize_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize error pattern recognition"""
        return {
            "api_key_invalid": {
                "patterns": [
                    "invalid api key",
                    "unauthorized",
                    "401",
                    "authentication failed",
                ],
                "category": ErrorCategory.AUTHENTICATION,
                "severity": ErrorSeverity.HIGH,
                "user_message": "API key is invalid or expired. Please check your API key configuration.",
                "suggestions": [
                    "Verify your API key is correct",
                    "Check if the API key has expired",
                    "Ensure the API key has the required permissions",
                    "Try regenerating the API key",
                ],
            },
            "network_error": {
                "patterns": [
                    "connection error",
                    "timeout",
                    "network unreachable",
                    "dns resolution failed",
                ],
                "category": ErrorCategory.NETWORK,
                "severity": ErrorSeverity.MEDIUM,
                "user_message": "Network connection failed. Please check your internet connection.",
                "suggestions": [
                    "Check your internet connection",
                    "Verify the RPC URL is correct",
                    "Try using a different RPC endpoint",
                    "Check if the service is temporarily unavailable",
                ],
            },
            "insufficient_funds": {
                "patterns": [
                    "insufficient funds",
                    "insufficient balance",
                    "not enough gas",
                ],
                "category": ErrorCategory.RESOURCE,
                "severity": ErrorSeverity.HIGH,
                "user_message": "Insufficient funds for this operation.",
                "suggestions": [
                    "Add more funds to your wallet",
                    "Check your account balance",
                    "Reduce the transaction amount",
                    "Increase gas price for faster confirmation",
                ],
            },
            "gas_estimation_failed": {
                "patterns": [
                    "gas estimation failed",
                    "out of gas",
                    "gas limit exceeded",
                ],
                "category": ErrorCategory.DEPLOYMENT,
                "severity": ErrorSeverity.MEDIUM,
                "user_message": "Gas estimation failed. The transaction may be too complex.",
                "suggestions": [
                    "Simplify the contract code",
                    "Increase gas limit",
                    "Check for infinite loops",
                    "Optimize contract functions",
                ],
            },
            "compilation_error": {
                "patterns": [
                    "compilation failed",
                    "syntax error",
                    "type error",
                    "pragma error",
                ],
                "category": ErrorCategory.VALIDATION,
                "severity": ErrorSeverity.HIGH,
                "user_message": "Contract compilation failed. Please check the Solidity code.",
                "suggestions": [
                    "Check for syntax errors",
                    "Verify pragma version compatibility",
                    "Check import statements",
                    "Validate function signatures",
                ],
            },
            "deployment_failed": {
                "patterns": [
                    "deployment failed",
                    "transaction reverted",
                    "contract creation failed",
                ],
                "category": ErrorCategory.DEPLOYMENT,
                "severity": ErrorSeverity.HIGH,
                "user_message": "Contract deployment failed.",
                "suggestions": [
                    "Check contract constructor parameters",
                    "Verify sufficient gas for deployment",
                    "Check network connectivity",
                    "Review contract code for errors",
                ],
            },
            "audit_failed": {
                "patterns": [
                    "audit failed",
                    "security scan failed",
                    "vulnerability detected",
                ],
                "category": ErrorCategory.AUDIT,
                "severity": ErrorSeverity.MEDIUM,
                "user_message": "Security audit failed. Please review the findings.",
                "suggestions": [
                    "Review security findings",
                    "Fix identified vulnerabilities",
                    "Run additional security checks",
                    "Consider professional audit",
                ],
            },
            "generation_failed": {
                "patterns": ["generation failed", "ai service error", "model error"],
                "category": ErrorCategory.GENERATION,
                "severity": ErrorSeverity.MEDIUM,
                "user_message": "Contract generation failed. Please try again.",
                "suggestions": [
                    "Check your prompt clarity",
                    "Try a different approach",
                    "Verify AI service status",
                    "Contact support if issue persists",
                ],
            },
        }

    def _initialize_suggestion_templates(self) -> Dict[str, list]:
        """Initialize suggestion templates for different error types"""
        return {
            "general": [
                "Check your input parameters",
                "Verify your configuration",
                "Try again in a few moments",
                "Contact support if the issue persists",
            ],
            "network": [
                "Check your internet connection",
                "Verify RPC endpoint URL",
                "Try a different network",
                "Check service status",
            ],
            "authentication": [
                "Verify your credentials",
                "Check API key permissions",
                "Regenerate your API key",
                "Contact service provider",
            ],
            "deployment": [
                "Check contract code",
                "Verify gas settings",
                "Ensure sufficient balance",
                "Try different network",
            ],
        }

    def handle_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> ErrorInfo:
        """
        Handle an error and return structured error information

        Args:
            error: Exception that occurred
            context: Additional context information

        Returns:
            ErrorInfo object with structured error information
        """
        error_str = str(error).lower()
        error_traceback = traceback.format_exc()

        # Find matching error pattern
        matched_pattern = None
        for pattern_name, pattern_info in self.error_patterns.items():
            for pattern in pattern_info["patterns"]:
                if pattern in error_str:
                    matched_pattern = pattern_name
                    break
            if matched_pattern:
                break

        if matched_pattern:
            pattern_info = self.error_patterns[matched_pattern]
            category = pattern_info["category"]
            severity = pattern_info["severity"]
            user_message = pattern_info["user_message"]
            suggestions = pattern_info["suggestions"]
        else:
            # Default error handling
            category = ErrorCategory.INTERNAL
            severity = ErrorSeverity.MEDIUM
            user_message = "An unexpected error occurred. Please try again."
            suggestions = self.suggestion_templates["general"]

        # Generate error ID
        error_id = self._generate_error_id(error, context)

        # Create error info
        error_info = ErrorInfo(
            error_id=error_id,
            category=category,
            severity=severity,
            message=str(error),
            user_message=user_message,
            technical_details=error_traceback,
            suggestions=suggestions,
            timestamp=datetime.now(),
            context=context or {},
        )

        # Log the error
        self._log_error(error_info)

        return error_info

    def _generate_error_id(
        self, error: Exception, context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate a unique error ID"""
        import hashlib
        import uuid

        error_data = f"{type(error).__name__}:{str(error)}:{datetime.now().isoformat()}"
        if context:
            error_data += f":{str(context)}"

        return hashlib.md5(error_data.encode()).hexdigest()[:8]

    def _log_error(self, error_info: ErrorInfo):
        """Log error information"""
        log_message = f"Error {error_info.error_id}: {error_info.message}"

        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, extra={"error_info": error_info})
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(log_message, extra={"error_info": error_info})
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, extra={"error_info": error_info})
        else:
            logger.info(log_message, extra={"error_info": error_info})

    def format_error_response(
        self, error_info: ErrorInfo, include_technical: bool = False
    ) -> Dict[str, Any]:
        """
        Format error information for user response

        Args:
            error_info: Error information
            include_technical: Whether to include technical details

        Returns:
            Formatted error response
        """
        response = {
            "status": "error",
            "error_id": error_info.error_id,
            "category": error_info.category.value,
            "severity": error_info.severity.value,
            "message": error_info.user_message,
            "suggestions": error_info.suggestions,
            "timestamp": error_info.timestamp.isoformat(),
        }

        if include_technical:
            response["technical_details"] = {
                "error_type": type(error_info).__name__,
                "original_message": error_info.message,
                "traceback": error_info.technical_details,
                "context": error_info.context,
            }

        return response

    def create_success_response(
        self, data: Any, message: str = "Operation completed successfully"
    ) -> Dict[str, Any]:
        """
        Create a standardized success response

        Args:
            data: Response data
            message: Success message

        Returns:
            Formatted success response
        """
        return {
            "status": "success",
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

    def create_validation_error(self, field: str, value: Any, reason: str) -> ErrorInfo:
        """
        Create a validation error

        Args:
            field: Field that failed validation
            value: Invalid value
            reason: Reason for validation failure

        Returns:
            ErrorInfo object
        """
        return ErrorInfo(
            error_id=self._generate_error_id(
                Exception(reason), {"field": field, "value": value}
            ),
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            message=f"Validation failed for field '{field}': {reason}",
            user_message=f"Invalid value for {field}. {reason}",
            technical_details=f"Field: {field}, Value: {value}, Reason: {reason}",
            suggestions=[
                f"Check the {field} field",
                "Verify the input format",
                "Ensure the value meets requirements",
            ],
            timestamp=datetime.now(),
            context={"field": field, "value": value, "reason": reason},
        )

    def create_network_error(
        self, operation: str, endpoint: str, error: Exception
    ) -> ErrorInfo:
        """
        Create a network error

        Args:
            operation: Operation that failed
            endpoint: Network endpoint
            error: Original error

        Returns:
            ErrorInfo object
        """
        return ErrorInfo(
            error_id=self._generate_error_id(
                error, {"operation": operation, "endpoint": endpoint}
            ),
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            message=f"Network error during {operation}: {str(error)}",
            user_message=f"Failed to connect to {endpoint}. Please check your network connection.",
            technical_details=str(error),
            suggestions=[
                "Check your internet connection",
                "Verify the endpoint URL",
                "Try again in a few moments",
                "Contact support if the issue persists",
            ],
            timestamp=datetime.now(),
            context={"operation": operation, "endpoint": endpoint},
        )

    def create_deployment_error(
        self, contract_name: str, network: str, error: Exception
    ) -> ErrorInfo:
        """
        Create a deployment error

        Args:
            contract_name: Name of the contract
            network: Target network
            error: Original error

        Returns:
            ErrorInfo object
        """
        return ErrorInfo(
            error_id=self._generate_error_id(
                error, {"contract": contract_name, "network": network}
            ),
            category=ErrorCategory.DEPLOYMENT,
            severity=ErrorSeverity.HIGH,
            message=f"Failed to deploy {contract_name} to {network}: {str(error)}",
            user_message=f"Contract deployment failed. Please check your contract code and network settings.",
            technical_details=str(error),
            suggestions=[
                "Check your contract code for errors",
                "Verify sufficient gas for deployment",
                "Ensure your wallet has enough balance",
                "Try deploying to a different network",
            ],
            timestamp=datetime.now(),
            context={"contract": contract_name, "network": network},
        )

    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get error statistics for monitoring

        Returns:
            Error statistics
        """
        # This would typically come from a logging system or database
        return {
            "total_errors": 0,
            "errors_by_category": {},
            "errors_by_severity": {},
            "recent_errors": [],
        }

    def should_retry(self, error_info: ErrorInfo, retry_count: int = 0) -> bool:
        """
        Determine if an operation should be retried

        Args:
            error_info: Error information
            retry_count: Number of retries already attempted

        Returns:
            True if should retry, False otherwise
        """
        max_retries = {
            ErrorSeverity.LOW: 3,
            ErrorSeverity.MEDIUM: 2,
            ErrorSeverity.HIGH: 1,
            ErrorSeverity.CRITICAL: 0,
        }

        return retry_count < max_retries.get(error_info.severity, 0)

    def get_retry_delay(self, error_info: ErrorInfo, retry_count: int) -> int:
        """
        Get delay before retry

        Args:
            error_info: Error information
            retry_count: Number of retries already attempted

        Returns:
            Delay in seconds
        """
        base_delays = {
            ErrorSeverity.LOW: 1,
            ErrorSeverity.MEDIUM: 2,
            ErrorSeverity.HIGH: 5,
            ErrorSeverity.CRITICAL: 10,
        }

        base_delay = base_delays.get(error_info.severity, 2)
        return base_delay * (2**retry_count)  # Exponential backoff
