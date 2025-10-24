"""
Security features for HyperKit AI Agent
"""

import hashlib
import hmac
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class SecurityManager:
    """Centralized security management"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rate_limits = {}
        self.blocked_ips = set()
        self.suspicious_patterns = [
            r"rm\s+-rf", r"sudo", r"chmod", r"wget", r"curl",
            r"bash", r"sh", r"eval\(", r"exec\(", r"system\(",
            r"shell_exec", r"<script", r"javascript:", r"onload=",
            r"onerror=", r"onclick=", r"alert\(", r"confirm\("
        ]
    
    def validate_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Validate user prompt for security issues
        
        Args:
            prompt: User input prompt
            
        Returns:
            Dict with validation results
        """
        issues = []
        severity = "low"
        
        # Check length
        if len(prompt) > 1000:
            issues.append("Prompt too long")
            severity = "medium"
        
        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                issues.append(f"Suspicious pattern detected: {pattern}")
                severity = "high"
        
        # Check for SQL injection patterns
        sql_patterns = [r"union\s+select", r"drop\s+table", r"delete\s+from", r"insert\s+into"]
        for pattern in sql_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                issues.append("Potential SQL injection")
                severity = "critical"
        
        return {
            "is_safe": len(issues) == 0,
            "issues": issues,
            "severity": severity,
            "prompt_length": len(prompt)
        }
    
    def check_rate_limit(self, user_id: str, operation: str) -> bool:
        """
        Check if user has exceeded rate limits
        
        Args:
            user_id: User identifier
            operation: Operation being performed
            
        Returns:
            True if within limits, False if exceeded
        """
        key = f"{user_id}:{operation}"
        now = time.time()
        
        if key not in self.rate_limits:
            self.rate_limits[key] = []
        
        # Clean old entries (older than 1 hour)
        self.rate_limits[key] = [
            timestamp for timestamp in self.rate_limits[key]
            if now - timestamp < 3600
        ]
        
        # Check limits based on operation
        limits = {
            "generate": 10,  # 10 per hour
            "audit": 20,     # 20 per hour
            "deploy": 5,      # 5 per hour
            "verify": 10,    # 10 per hour
            "test": 15       # 15 per hour
        }
        
        limit = limits.get(operation, 5)
        
        if len(self.rate_limits[key]) >= limit:
            logger.warning(f"Rate limit exceeded for {user_id}:{operation}")
            return False
        
        # Add current request
        self.rate_limits[key].append(now)
        return True
    
    def validate_api_key(self, api_key: str, provider: str) -> bool:
        """
        Validate API key format and security
        
        Args:
            api_key: API key to validate
            provider: Provider name
            
        Returns:
            True if valid, False otherwise
        """
        if not api_key or len(api_key.strip()) == 0:
            return False
        
        # Check minimum length
        if len(api_key) < 10:
            return False
        
        # Check for common test keys
        test_keys = ["test", "demo", "example", "your_api_key", "sk-test"]
        if any(test_key in api_key.lower() for test_key in test_keys):
            logger.warning(f"Test API key detected for {provider}")
            return False
        
        return True
    
    def sanitize_input(self, input_str: str) -> str:
        """
        Sanitize user input to prevent injection attacks
        
        Args:
            input_str: Input string to sanitize
            
        Returns:
            Sanitized string
        """
        # Remove null bytes
        input_str = input_str.replace('\x00', '')
        
        # Remove control characters except newlines and tabs
        input_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', input_str)
        
        # Limit length
        if len(input_str) > 1000:
            input_str = input_str[:1000]
        
        return input_str.strip()
    
    def generate_audit_hash(self, data: Dict[str, Any]) -> str:
        """
        Generate audit hash for data integrity
        
        Args:
            data: Data to hash
            
        Returns:
            SHA-256 hash of the data
        """
        import json
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def validate_contract_code(self, contract_code: str) -> Dict[str, Any]:
        """
        Validate generated contract code for security issues
        
        Args:
            contract_code: Solidity contract code
            
        Returns:
            Dict with validation results
        """
        issues = []
        severity = "low"
        
        # Check for dangerous functions
        dangerous_functions = [
            "selfdestruct", "delegatecall", "assembly", "suicide"
        ]
        
        for func in dangerous_functions:
            if func in contract_code:
                issues.append(f"Dangerous function detected: {func}")
                severity = "high"
        
        # Check for unchecked external calls
        if "call(" in contract_code and "require(" not in contract_code:
            issues.append("Potential unchecked external call")
            severity = "medium"
        
        # Check for reentrancy patterns
        if "call(" in contract_code and "state" in contract_code:
            issues.append("Potential reentrancy vulnerability")
            severity = "high"
        
        return {
            "is_safe": len(issues) == 0,
            "issues": issues,
            "severity": severity,
            "code_length": len(contract_code)
        }
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """
        Log security events for monitoring
        
        Args:
            event_type: Type of security event
            details: Event details
        """
        security_log = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details,
            "severity": details.get("severity", "low")
        }
        
        logger.warning(f"Security event: {security_log}")
        
        # In production, this would go to a security monitoring system
        if details.get("severity") == "critical":
            logger.critical(f"CRITICAL SECURITY EVENT: {event_type}")

class InputValidator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_network(network: str) -> bool:
        """Validate network parameter"""
        valid_networks = ["hyperion", "polygon", "arbitrum", "ethereum", "metis", "lazai"]
        return network.lower() in valid_networks
    
    @staticmethod
    def validate_contract_address(address: str) -> bool:
        """Validate Ethereum contract address format"""
        if not address:
            return False
        
        # Check if it's a valid hex string
        if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
            return False
        
        return True
    
    @staticmethod
    def validate_constructor_args(args: List[str]) -> bool:
        """Validate constructor arguments"""
        if not args:
            return True
        
        # Check each argument
        for arg in args:
            if len(arg) > 100:  # Reasonable limit
                return False
            
            # Check for dangerous characters
            if any(char in arg for char in [';', '&', '|', '`', '$']):
                return False
        
        return True

class AccessController:
    """Access control and permissions"""
    
    def __init__(self):
        self.permissions = {
            "generate": ["user", "admin"],
            "audit": ["user", "admin"],
            "deploy": ["admin"],  # Only admins can deploy
            "verify": ["user", "admin"],
            "test": ["user", "admin"]
        }
    
    def check_permission(self, user_role: str, operation: str) -> bool:
        """Check if user has permission for operation"""
        allowed_roles = self.permissions.get(operation, [])
        return user_role in allowed_roles
    
    def get_required_role(self, operation: str) -> str:
        """Get minimum required role for operation"""
        if operation in ["deploy"]:
            return "admin"
        return "user"
