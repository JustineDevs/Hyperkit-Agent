"""
Configuration Loader for HyperKit AI Agent
Handles loading and validation of configuration from multiple sources
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Loads and manages configuration from YAML and environment variables."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to the main configuration file
        """
        self.config_path = Path(config_path)
        self.config = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file and environment variables."""
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
                self.config = self._get_default_config()
            
            # Override with environment variables
            self._apply_env_overrides()
            
            # Validate configuration
            self._validate_config()
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self.config = self._get_default_config()
    
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
    
    def _validate_config(self) -> None:
        """Validate the loaded configuration."""
        required_sections = ['networks', 'ai_providers', 'defaults']
        
        for section in required_sections:
            if section not in self.config:
                logger.warning(f"Missing required configuration section: {section}")
        
        # Validate networks
        if 'networks' in self.config:
            for network_name, network_config in self.config['networks'].items():
                required_fields = ['rpc_url', 'chain_id', 'gas_price', 'gas_limit']
                for field in required_fields:
                    if field not in network_config:
                        logger.warning(f"Network {network_name} missing required field: {field}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration when YAML file is not available."""
        return {
            'networks': {
                'hyperion': {
                    'rpc_url': 'https://hyperion-testnet.metisdevops.link',
                    'chain_id': 133717,
                    'explorer_url': 'https://hyperion-testnet-explorer.metisdevops.link',
                    'gas_price': '20000000000',
                    'gas_limit': 8000000,
                    'enabled': True
                }
            },
            'ai_providers': {
                'google': {
                    'enabled': True,
                    'model': 'gemini-2.5-pro-preview-03-25',
                    'api_key_env': 'GOOGLE_API_KEY'
                }
            },
            'defaults': {
                'network': 'hyperion',
                'ai_provider': 'google',
                'log_level': 'INFO'
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'networks.hyperion.rpc_url')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
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
        return self.config.copy()


# Global configuration instance
config_loader = ConfigLoader()


def get_config() -> ConfigLoader:
    """Get the global configuration loader instance."""
    return config_loader


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a configuration value using the global loader."""
    return config_loader.get(key, default)
