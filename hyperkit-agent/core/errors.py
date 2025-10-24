"""
Custom exceptions for HyperKit AI Agent
"""

class HyperKitError(Exception):
    """Base exception for all HyperKit errors"""
    pass

class ConfigurationError(HyperKitError):
    """Configuration-related errors"""
    pass

class NetworkError(HyperKitError):
    """Network connectivity errors"""
    pass

class ContractGenerationError(HyperKitError):
    """Contract generation errors"""
    pass

class AuditError(HyperKitError):
    """Security audit errors"""
    pass

class DeploymentError(HyperKitError):
    """Contract deployment errors"""
    pass

class VerificationError(HyperKitError):
    """Contract verification errors"""
    pass

class TestingError(HyperKitError):
    """Contract testing errors"""
    pass

class ValidationError(HyperKitError):
    """Input validation errors"""
    pass

class SecurityError(HyperKitError):
    """Security-related errors"""
    pass

class RateLimitError(HyperKitError):
    """Rate limiting errors"""
    pass

class AuthenticationError(HyperKitError):
    """Authentication errors"""
    pass

class WorkflowError(HyperKitError):
    """Workflow execution errors"""
    pass
