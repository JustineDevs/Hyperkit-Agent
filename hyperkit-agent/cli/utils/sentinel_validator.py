"""
Sentinel Object Validator Utility
Centralized validation for Click Sentinel objects to prevent path operation errors
"""

from typing import Any, Optional


def is_sentinel(value: Any) -> bool:
    """
    Check if a value is a Click Sentinel object.
    
    Args:
        value: Value to check
        
    Returns:
        True if value is a Sentinel object, False otherwise
    """
    if value is None:
        return False
    if hasattr(value, '__class__') and 'Sentinel' in str(type(value)):
        return True
    return False


def validate_and_convert(value: Any, default: Any = None) -> Any:
    """
    Validate and convert a value, handling Sentinel objects.
    
    Args:
        value: Value to validate
        default: Default value to return if value is Sentinel or invalid
        
    Returns:
        Validated value or default
    """
    if is_sentinel(value):
        return default
    
    if value is None:
        return default
    
    return value


def validate_string_param(value: Any, param_name: str = "parameter") -> Optional[str]:
    """
    Validate and convert a parameter to a string, handling Sentinel objects.
    
    Args:
        value: Value to validate
        param_name: Name of parameter for error messages
        
    Returns:
        String value or None if invalid/Sentinel
    """
    if is_sentinel(value):
        return None
    
    if value is None:
        return None
    
    if isinstance(value, str):
        # CRITICAL: Reject string values that look like Sentinel objects
        stripped = value.strip()
        if not stripped:
            return None
        # Reject strings that contain "Sentinel" (e.g., "Sentinel.UNSET")
        if "Sentinel" in stripped:
            return None
        return stripped
    
    try:
        str_value = str(value) if value else None
        if str_value and "Sentinel" in str_value:
            return None
        return str_value
    except (TypeError, ValueError):
        return None


def validate_path_param(value: Any, param_name: str = "path") -> Optional[str]:
    """
    Validate a parameter for use in path operations, handling Sentinel objects.
    
    Args:
        value: Value to validate
        param_name: Name of parameter for error messages
        
    Returns:
        String value safe for path operations, or None if invalid/Sentinel
    """
    validated = validate_string_param(value, param_name)
    
    if validated is None:
        return None
    
    # Additional path validation
    if not validated or validated == "":
        return None
    
    # Remove any path traversal attempts
    if ".." in validated or validated.startswith("/"):
        return None
    
    return validated

