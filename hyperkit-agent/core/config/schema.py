"""
Configuration Schema Validation for HyperKit AI Agent
Production-ready configuration validation with Pydantic v2
"""

from pydantic import BaseModel, Field, validator, model_validator
from typing import Optional, Dict, Any, List
import re
from urllib.parse import urlparse


class NetworkConfig(BaseModel):
    """Network configuration schema"""
    
    rpc_url: str = Field(..., description="RPC endpoint URL")
    chain_id: int = Field(..., description="Chain ID", gt=0)
    explorer_url: Optional[str] = Field(None, description="Block explorer URL")
    explorer_api: Optional[str] = Field(None, description="Block explorer API URL")
    gas_price: str = Field(default="20000000000", description="Gas price in wei")
    gas_limit: int = Field(default=8000000, description="Gas limit", gt=0)
    enabled: bool = Field(default=True, description="Whether network is enabled")
    
    @validator('rpc_url')
    def validate_rpc_url(cls, v):
        """Validate RPC URL format"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('RPC URL must start with http:// or https://')
        
        # Basic URL validation
        try:
            parsed = urlparse(v)
            if not parsed.netloc:
                raise ValueError('Invalid RPC URL format')
        except Exception:
            raise ValueError('Invalid RPC URL format')
        
        return v
    
    @validator('explorer_url', 'explorer_api')
    def validate_explorer_urls(cls, v):
        """Validate explorer URLs if provided"""
        if v is not None:
            if not v.startswith(('http://', 'https://')):
                raise ValueError('Explorer URL must start with http:// or https://')
        return v
    
    @validator('gas_price')
    def validate_gas_price(cls, v):
        """Validate gas price is numeric string"""
        try:
            int(v)
        except ValueError:
            raise ValueError('Gas price must be a numeric string')
        return v


class AIProviderConfig(BaseModel):
    """AI Provider configuration schema"""
    
    enabled: bool = Field(default=True, description="Whether provider is enabled")
    model: str = Field(..., description="Model name")
    api_key: Optional[str] = Field(None, description="API key")
    api_key_env: Optional[str] = Field(None, description="Environment variable for API key")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens", gt=0)
    temperature: Optional[float] = Field(None, description="Temperature", ge=0.0, le=2.0)
    timeout: Optional[int] = Field(None, description="Request timeout in seconds", gt=0)
    
    @validator('api_key')
    def validate_api_key(cls, v):
        """Validate API key format if provided"""
        if v is not None and len(v.strip()) == 0:
            raise ValueError('API key cannot be empty')
        return v


class RAGConfig(BaseModel):
    """RAG (Retrieval Augmented Generation) configuration"""
    
    obsidian: Optional[Dict[str, Any]] = Field(None, description="Obsidian configuration")
    vault_path: Optional[str] = Field(None, description="Obsidian vault path")
    api_key: Optional[str] = Field(None, description="Obsidian API key")
    api_url: Optional[str] = Field(None, description="Obsidian API URL")
    
    @validator('vault_path')
    def validate_vault_path(cls, v):
        """Validate vault path if provided"""
        if v is not None and not v.strip():
            raise ValueError('Vault path cannot be empty')
        return v


class LoggingConfig(BaseModel):
    """Logging configuration schema"""
    
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json", description="Log format (json/text)")
    file_path: Optional[str] = Field(None, description="Log file path")
    max_size: Optional[int] = Field(None, description="Max log file size in MB", gt=0)
    backup_count: Optional[int] = Field(None, description="Number of backup files", ge=0)
    
    @validator('level')
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {", ".join(valid_levels)}')
        return v.upper()
    
    @validator('format')
    def validate_log_format(cls, v):
        """Validate log format"""
        valid_formats = ['json', 'text']
        if v.lower() not in valid_formats:
            raise ValueError(f'Log format must be one of: {", ".join(valid_formats)}')
        return v.lower()


class SecurityConfig(BaseModel):
    """Security configuration schema"""
    
    enable_audit: bool = Field(default=True, description="Enable security auditing")
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    max_requests_per_minute: int = Field(default=100, description="Max requests per minute", gt=0)
    enable_cors: bool = Field(default=True, description="Enable CORS")
    allowed_origins: List[str] = Field(default_factory=list, description="Allowed CORS origins")
    
    @validator('allowed_origins')
    def validate_origins(cls, v):
        """Validate CORS origins"""
        for origin in v:
            if origin != "*" and not origin.startswith(('http://', 'https://')):
                raise ValueError(f'Invalid CORS origin: {origin}')
        return v


class HyperKitConfig(BaseModel):
    """Main HyperKit configuration schema"""
    
    # Core configuration
    networks: Dict[str, NetworkConfig] = Field(..., description="Network configurations")
    ai_providers: Dict[str, AIProviderConfig] = Field(..., description="AI provider configurations")
    
    # Optional configurations
    rag: Optional[RAGConfig] = Field(None, description="RAG configuration")
    logging: Optional[LoggingConfig] = Field(None, description="Logging configuration")
    security: Optional[SecurityConfig] = Field(None, description="Security configuration")
    
    # Additional optional fields from config.yaml
    defaults: Optional[Dict[str, Any]] = Field(None, description="Default settings")
    rag_system: Optional[Dict[str, Any]] = Field(None, description="RAG system configuration")
    deployment: Optional[Dict[str, Any]] = Field(None, description="Deployment configuration")
    monitoring: Optional[Dict[str, Any]] = Field(None, description="Monitoring configuration")
    api: Optional[Dict[str, Any]] = Field(None, description="API configuration")
    database: Optional[Dict[str, Any]] = Field(None, description="Database configuration")
    development: Optional[Dict[str, Any]] = Field(None, description="Development configuration")
    
    # Default settings
    default_network: str = Field(default="hyperion", description="Default network")
    default_ai_provider: str = Field(default="google", description="Default AI provider")
    default_private_key: Optional[str] = Field(None, description="Default private key")
    
    # System settings
    debug: bool = Field(default=False, description="Debug mode")
    test_mode: bool = Field(default=False, description="Test mode")
    
    @validator('default_network')
    def validate_default_network(cls, v, values):
        """Validate default network exists in networks"""
        if 'networks' in values and v not in values['networks']:
            available = list(values['networks'].keys())
            raise ValueError(f'Default network "{v}" not found. Available: {", ".join(available)}')
        return v
    
    @validator('default_ai_provider')
    def validate_default_ai_provider(cls, v, values):
        """Validate default AI provider exists in providers"""
        if 'ai_providers' in values and v not in values['ai_providers']:
            available = list(values['ai_providers'].keys())
            raise ValueError(f'Default AI provider "{v}" not found. Available: {", ".join(available)}')
        return v
    
    @validator('default_private_key')
    def validate_private_key(cls, v):
        """Validate private key format if provided"""
        if v is not None:
            # Basic validation - should be 64 hex characters
            if not re.match(r'^[0-9a-fA-F]{64}$', v):
                raise ValueError('Private key must be 64 hexadecimal characters')
        return v
    
    @model_validator(mode='after')
    def validate_configuration(self):
        """Model validator for cross-field validation"""
        # Ensure at least one network is enabled
        networks = self.networks or {}
        enabled_networks = [name for name, config in networks.items() if config.enabled]
        if not enabled_networks:
            raise ValueError('At least one network must be enabled')
        
        # Ensure at least one AI provider is enabled
        providers = self.ai_providers or {}
        enabled_providers = [name for name, config in providers.items() if config.enabled]
        if not enabled_providers:
            raise ValueError('At least one AI provider must be enabled')
        
        return self
    
    class Config:
        """Pydantic configuration"""
        validate_assignment = True
        extra = "forbid"  # Reject extra fields
        use_enum_values = True


def validate_config(config_dict: Dict[str, Any]) -> HyperKitConfig:
    """
    Validate configuration dictionary against schema
    
    Args:
        config_dict: Configuration dictionary to validate
        
    Returns:
        Validated HyperKitConfig instance
        
    Raises:
        ValidationError: If configuration is invalid
    """
    return HyperKitConfig(**config_dict)


def get_default_config() -> Dict[str, Any]:
    """Get default configuration dictionary"""
    return {
        "networks": {
            "hyperion": {
                "rpc_url": "https://hyperion-testnet.metisdevops.link",
                "chain_id": 133717,
                "explorer_url": "https://hyperion-testnet-explorer.metisdevops.link",
                "gas_price": "20000000000",
                "gas_limit": 8000000,
                "enabled": True
            },
            "lazai": {
                "rpc_url": "https://rpc.lazai.network/testnet",
                "chain_id": 9001,
                "explorer_url": "https://explorer.lazai.network",
                "gas_price": "20000000000",
                "gas_limit": 8000000,
                "enabled": True
            },
            "metis": {
                "rpc_url": "https://andromeda.metis.io",
                "chain_id": 1088,
                "explorer_url": "https://andromeda-explorer.metis.io",
                "gas_price": "20000000000",
                "gas_limit": 8000000,
                "enabled": True
            }
        },
        "ai_providers": {
            "google": {
                "enabled": True,
                "model": "gemini-2.5-pro-preview-03-25",
                "api_key_env": "GOOGLE_API_KEY"
            },
            "openai": {
                "enabled": False,
                "model": "gpt-4",
                "api_key_env": "OPENAI_API_KEY"
            },
            "anthropic": {
                "enabled": False,
                "model": "claude-3-sonnet-20240229",
                "api_key_env": "ANTHROPIC_API_KEY"
            }
        },
        "default_network": "hyperion",
        "default_ai_provider": "google",
        "debug": False,
        "test_mode": False,
        "logging": {
            "level": "INFO",
            "format": "json"
        },
        "security": {
            "enable_audit": True,
            "enable_rate_limiting": True,
            "max_requests_per_minute": 100,
            "enable_cors": True,
            "allowed_origins": []
        }
    }
