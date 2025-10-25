"""
ConfigManager Singleton
Centralized configuration management for HyperKit Agent
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

class ConfigManager:
    """
    Singleton configuration manager for HyperKit Agent
    Centralizes all configuration loading and management
    """
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._load_config()
    
    def _load_config(self):
        """Load configuration from multiple sources"""
        self._config = {}
        
        # Load environment variables
        load_dotenv()
        
        # Load from config.yaml
        config_file = Path(__file__).parent.parent.parent / "config.yaml"
        if config_file.exists():
            with open(config_file, 'r') as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config:
                    self._config.update(yaml_config)
        
        # Load from environment variables
        env_config = {
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),
            'PINATA_API_KEY': os.getenv('PINATA_API_KEY'),
            'PINATA_SECRET_KEY': os.getenv('PINATA_SECRET_KEY') or os.getenv('PINATA_API_SECRET'),  # Support both names
            'LAZAI_API_KEY': os.getenv('LAZAI_API_KEY'),
            'HYPERION_RPC_URL': os.getenv('HYPERION_RPC_URL'),
            'PRIVATE_KEY': os.getenv('PRIVATE_KEY'),
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
            'DEBUG': os.getenv('DEBUG', 'false').lower() == 'true'
        }
        
        # Update config with environment variables (non-None values)
        for key, value in env_config.items():
            if value is not None:
                self._config[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self._config[key] = value
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration"""
        return self._config.copy()
    
    def is_configured(self) -> bool:
        """Check if essential configuration is present"""
        required_keys = [
            'OPENAI_API_KEY',
            'GOOGLE_API_KEY',
            'HYPERION_RPC_URL'
        ]
        
        return all(self.get(key) for key in required_keys)
    
    def get_api_keys(self) -> Dict[str, str]:
        """Get all API keys"""
        return {
            'openai': self.get('OPENAI_API_KEY'),
            'google': self.get('GOOGLE_API_KEY'),
            'pinata': self.get('PINATA_API_KEY'),
            'lazai': self.get('LAZAI_API_KEY')
        }
    
    def get_network_config(self) -> Dict[str, str]:
        """Get network configuration"""
        return {
            'hyperion_rpc': self.get('HYPERION_RPC_URL'),
            'private_key': self.get('PRIVATE_KEY')
        }
    
    def get_storage_config(self) -> Dict[str, str]:
        """Get storage configuration"""
        return {
            'pinata_api_key': self.get('PINATA_API_KEY'),
            'pinata_secret_key': self.get('PINATA_SECRET_KEY')
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            'level': self.get('LOG_LEVEL', 'INFO'),
            'debug': self.get('DEBUG', False)
        }

# Global instance
config = ConfigManager()
