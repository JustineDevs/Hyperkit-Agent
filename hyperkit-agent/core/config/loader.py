"""
Configuration Loader for HyperKit AI Agent
Handles loading and validation of configuration from multiple sources
Production-ready with schema validation
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from pydantic import ValidationError

# Import our new schema
from .schema import HyperKitConfig, validate_config, get_default_config

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Configuration settings from environment"""
    
    google_api_key: str = ""
    openai_api_key: str = ""
    obsidian_mcp_api_key: str = ""
    obsidian_api_url: str = "http://127.0.0.1:27123"
    obsidian_vault_path: str = ""
    hyperion_rpc_url: str = "https://hyperion-testnet.metisdevops.link"
    hyperion_chain_id: int = 133717
    lazai_rpc_url: str = "https://rpc.lazai.network/testnet"
    lazai_chain_id: int = 9001
    metis_rpc_url: str = "https://andromeda.metis.io"
    metis_chain_id: int = 1088
    default_network: str = "hyperion"
    default_private_key: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields


class ConfigLoader:
    """Loads and manages configuration from YAML and environment variables with schema validation."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to the main configuration file
        """
        self.config_path = Path(config_path)
        self.config = None
        self.validated_config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file and environment variables with schema validation."""
        try:
            # Load environment variables first
            load_dotenv()
            
            # Load YAML configuration
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f) or {}
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                logger.warning(f"Configuration file {self.config_path} not found, using defaults")
                self.config = get_default_config()
            
            # Override with environment variables
            self._apply_env_overrides()
            
            # Validate configuration with schema
            self.validated_config = validate_config(self.config)
            logger.info("✅ Configuration validated successfully")
            
        except ValidationError as e:
            logger.error(f"❌ Configuration validation failed: {e}")
            logger.info("Using default configuration")
            self.config = get_default_config()
            self.validated_config = validate_config(self.config)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self.config = get_default_config()
            self.validated_config = validate_config(self.config)
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        # AI Provider API Keys
        if os.getenv('GOOGLE_API_KEY'):
            self.config.setdefault('ai_providers', {}).setdefault('google', {})['api_key'] = os.getenv('GOOGLE_API_KEY')
        
        # Network RPC URLs
        for network_name in ['hyperion', 'metis', 'lazai', 'polygon', 'arbitrum', 'ethereum']:
            rpc_key = f'{network_name.upper()}_RPC_URL'
            if os.getenv(rpc_key):
                self.config.setdefault('networks', {}).setdefault(network_name, {})['rpc_url'] = os.getenv(rpc_key)
        
        # Obsidian Configuration
        if os.getenv('OBSIDIAN_VAULT_PATH'):
            self.config.setdefault('rag', {}).setdefault('obsidian', {})['vault_path'] = os.getenv('OBSIDIAN_VAULT_PATH')
        
        if os.getenv('OBSIDIAN_API_KEY'):
            self.config.setdefault('rag', {}).setdefault('obsidian', {})['api_key'] = os.getenv('OBSIDIAN_API_KEY')
        
        if os.getenv('OBSIDIAN_API_URL'):
            self.config.setdefault('rag', {}).setdefault('obsidian', {})['api_url'] = os.getenv('OBSIDIAN_API_URL')
        
        # Private Key
        if os.getenv('DEFAULT_PRIVATE_KEY'):
            self.config['default_private_key'] = os.getenv('DEFAULT_PRIVATE_KEY')
        
        # Log Level
        if os.getenv('LOG_LEVEL'):
            self.config.setdefault('defaults', {})['log_level'] = os.getenv('LOG_LEVEL')
    
    def get_validated_config(self) -> HyperKitConfig:
        """Get the validated configuration object."""
        if self.validated_config is None:
            raise RuntimeError("Configuration not loaded or validated")
        return self.validated_config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'networks.hyperion.rpc_url')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        if self.config is None:
            return default
            
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_network_config(self, network_name: str) -> Dict[str, Any]:
        """
        Get network configuration.
        
        Args:
            network_name: Name of the network
            
        Returns:
            Network configuration dictionary
        """
        return self.get(f'networks.{network_name}', {})
    
    def get_ai_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """
        Get AI provider configuration.
        
        Args:
            provider_name: Name of the AI provider
            
        Returns:
            AI provider configuration dictionary
        """
        return self.get(f'ai_providers.{provider_name}', {})
    
    def get_enabled_networks(self) -> Dict[str, Dict[str, Any]]:
        """Get all enabled networks."""
        networks = self.get('networks', {})
        return {name: config for name, config in networks.items() 
                if config.get('enabled', True)}
    
    def get_enabled_ai_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get all enabled AI providers."""
        providers = self.get('ai_providers', {})
        return {name: config for name, config in providers.items() 
                if config.get('enabled', True)}
    
    def reload(self) -> None:
        """Reload configuration from files."""
        self._load_config()
    
    def to_dict(self) -> Dict[str, Any]:
        """Get the complete configuration as a dictionary."""
        if self.config is None:
            return {}
        return self.config.copy()
    
    @staticmethod
    def load() -> Dict[str, Any]:
        """
        Load configuration from environment
        
        Returns:
            dict with all configuration values
        
        Raises:
            ValueError: If required settings missing
        """
        try:
            load_dotenv()
            settings = Settings()
            
            # ✅ Explicitly build dict (not Pydantic model)
            config = {
                "networks": {
                    "hyperion": {
                        "rpc_url": settings.hyperion_rpc_url,  # ← STRING
                        "chain_id": settings.hyperion_chain_id,  # ← INT
                        "explorer": "https://hyperion-testnet-explorer.metisdevops.link",
                        "gas_price": "20000000000",
                        "gas_limit": 8000000,
                        "enabled": True
                    },
                    "lazai": {
                        "rpc_url": settings.lazai_rpc_url,
                        "chain_id": settings.lazai_chain_id,
                        "explorer": "https://explorer.lazai.network",
                        "gas_price": "20000000000",
                        "gas_limit": 8000000,
                        "enabled": True
                    },
                    "metis": {
                        "rpc_url": settings.metis_rpc_url,
                        "chain_id": settings.metis_chain_id,
                        "explorer": "https://andromeda-explorer.metis.io",
                        "gas_price": "20000000000",
                        "gas_limit": 8000000,
                        "enabled": True
                    }
                },
                "GOOGLE_API_KEY": settings.google_api_key,
                "OPENAI_API_KEY": settings.openai_api_key,
                "OBSIDIAN_MCP_API_KEY": settings.obsidian_mcp_api_key,
                "OBSIDIAN_API_URL": settings.obsidian_api_url,
                "OBSIDIAN_VAULT_PATH": settings.obsidian_vault_path,
                "DEFAULT_NETWORK": settings.default_network,
                "DEFAULT_PRIVATE_KEY": settings.default_private_key,
            }
            
            # ✅ Type validation
            if not isinstance(config, dict):
                raise TypeError(f"Config should be dict, got {type(config)}")
            
            if not isinstance(config['networks'], dict):
                raise TypeError("Config['networks'] should be dict")
            
            # ✅ Validate network RPC URLs are strings
            for network, net_config in config['networks'].items():
                if not isinstance(net_config['rpc_url'], str):
                    raise TypeError(
                        f"RPC URL for {network} should be string, "
                        f"got {type(net_config['rpc_url'])}"
                    )
            
            logger.info("✅ Configuration loaded successfully")
            return config
        
        except Exception as e:
            logger.error(f"❌ Error loading configuration: {e}")
            raise


# Global configuration instance
config_loader = ConfigLoader()


def get_config() -> ConfigLoader:
    """Get the global configuration loader instance."""
    return config_loader


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a configuration value using the global loader."""
    return config_loader.get(key, default)