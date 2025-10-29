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
            # AI/LLM Provider Configuration
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),
            'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
            'LAZAI_API_KEY': os.getenv('LAZAI_API_KEY'),
            
            # LazAI Network Configuration
            'LAZAI_EVM_ADDRESS': os.getenv('LAZAI_EVM_ADDRESS'),
            'LAZAI_RSA_PRIVATE_KEY': os.getenv('LAZAI_RSA_PRIVATE_KEY'),
            'IPFS_JWT': os.getenv('IPFS_JWT'),
            
            # Blockchain Network Configuration
            'DEFAULT_NETWORK': os.getenv('DEFAULT_NETWORK', 'hyperion'),
            'HYPERION_RPC_URL': os.getenv('HYPERION_RPC_URL'),
            'HYPERION_CHAIN_ID': os.getenv('HYPERION_CHAIN_ID', '133717'),
            'HYPERION_EXPLORER_URL': os.getenv('HYPERION_EXPLORER_URL'),
            'METIS_RPC_URL': os.getenv('METIS_RPC_URL'),
            'METIS_CHAIN_ID': os.getenv('METIS_CHAIN_ID', '1088'),
            'METIS_EXPLORER_URL': os.getenv('METIS_EXPLORER_URL'),
            'LAZAI_RPC_URL': os.getenv('LAZAI_RPC_URL'),
            'LAZAI_CHAIN_ID': os.getenv('LAZAI_CHAIN_ID', '9001'),
            'LAZAI_EXPLORER_URL': os.getenv('LAZAI_EXPLORER_URL'),
            'ETHEREUM_RPC_URL': os.getenv('ETHEREUM_RPC_URL'),
            'ETHEREUM_CHAIN_ID': os.getenv('ETHEREUM_CHAIN_ID', '1'),
            'ETHEREUM_EXPLORER_URL': os.getenv('ETHEREUM_EXPLORER_URL'),
            'POLYGON_RPC_URL': os.getenv('POLYGON_RPC_URL'),
            'POLYGON_CHAIN_ID': os.getenv('POLYGON_CHAIN_ID', '137'),
            'POLYGON_EXPLORER_URL': os.getenv('POLYGON_EXPLORER_URL'),
            'ARBITRUM_RPC_URL': os.getenv('ARBITRUM_RPC_URL'),
            'ARBITRUM_CHAIN_ID': os.getenv('ARBITRUM_CHAIN_ID', '42161'),
            'ARBITRUM_EXPLORER_URL': os.getenv('ARBITRUM_EXPLORER_URL'),
            
            # Wallet Configuration
            'DEFAULT_PRIVATE_KEY': os.getenv('DEFAULT_PRIVATE_KEY'),
            'PRIVATE_KEY': os.getenv('PRIVATE_KEY'),  # Legacy support
            
            # IPFS Storage Configuration
            'PINATA_API_KEY': os.getenv('PINATA_API_KEY'),
            'PINATA_SECRET_KEY': os.getenv('PINATA_SECRET_KEY') or os.getenv('PINATA_API_SECRET'),  # Support both names
            
            # Explorer API Keys
            'ETHEREUM_EXPLORER_API_KEY': os.getenv('ETHEREUM_EXPLORER_API_KEY'),
            'POLYGON_EXPLORER_API_KEY': os.getenv('POLYGON_EXPLORER_API_KEY'),
            'ARBITRUM_EXPLORER_API_KEY': os.getenv('ARBITRUM_EXPLORER_API_KEY'),
            'METIS_EXPLORER_API_KEY': os.getenv('METIS_EXPLORER_API_KEY'),
            
            # IPFS Pinata RAG Configuration (Obsidian removed - IPFS Pinata exclusive)
            
            # Logging and Monitoring
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
            'STRUCTURED_LOGGING': os.getenv('STRUCTURED_LOGGING', 'false').lower() == 'true',
            'ENVIRONMENT': os.getenv('ENVIRONMENT', 'development'),
            'DEBUG': os.getenv('DEBUG', 'false').lower() == 'true',
            'VERBOSE': os.getenv('VERBOSE', 'false').lower() == 'true',
            
            # Security Extensions
            'SECURITY_EXTENSIONS_ENABLED': os.getenv('SECURITY_EXTENSIONS_ENABLED', 'true').lower() == 'true',
            'SLITHER_ENABLED': os.getenv('SLITHER_ENABLED', 'true').lower() == 'true',
            'MYTHRIL_ENABLED': os.getenv('MYTHRIL_ENABLED', 'false').lower() == 'true',
            'EDB_ENABLED': os.getenv('EDB_ENABLED', 'false').lower() == 'true',
            'RATE_LIMIT': int(os.getenv('RATE_LIMIT', '60')),
            
            # Deployment Settings
            'GAS_PRICE_MULTIPLIER': float(os.getenv('GAS_PRICE_MULTIPLIER', '1.0')),
            'DEPLOYMENT_GAS_LIMIT': int(os.getenv('DEPLOYMENT_GAS_LIMIT', '8000000')),
            'CONFIRMATION_BLOCKS': int(os.getenv('CONFIRMATION_BLOCKS', '12')),
            'AUTO_VERIFY': os.getenv('AUTO_VERIFY', 'true').lower() == 'true',
            
            # Development Settings
            'TEST_MODE': os.getenv('TEST_MODE', 'true').lower() == 'true',
            'CACHE_DIR': os.getenv('CACHE_DIR', './cache'),
            
            # Alith SDK Configuration
            'ALITH_ENABLED': os.getenv('ALITH_ENABLED', 'true').lower() == 'true',
            'ALITH_MODEL': os.getenv('ALITH_MODEL', 'gpt-4o-mini'),
            'ALITH_SETTLEMENT': os.getenv('ALITH_SETTLEMENT', 'true').lower() == 'true',
            'ALITH_INFERENCE_NODE': os.getenv('ALITH_INFERENCE_NODE'),
            'ALITH_PRIVATE_INFERENCE': os.getenv('ALITH_PRIVATE_INFERENCE', 'false').lower() == 'true'
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
            'GOOGLE_API_KEY',  # Primary AI provider
            'HYPERION_RPC_URL'  # Primary network
        ]
        
        return all(self.get(key) for key in required_keys)
    
    def get_api_keys(self) -> Dict[str, str]:
        """Get all API keys"""
        return {
            'openai': self.get('OPENAI_API_KEY'),
            'google': self.get('GOOGLE_API_KEY'),
            'anthropic': self.get('ANTHROPIC_API_KEY'),
            'lazai': self.get('LAZAI_API_KEY'),
            'pinata': self.get('PINATA_API_KEY')
        }
    
    def get_network_config(self) -> Dict[str, str]:
        """Get network configuration"""
        return {
            'default_network': self.get('DEFAULT_NETWORK', 'hyperion'),
            'hyperion_rpc': self.get('HYPERION_RPC_URL'),
            'hyperion_chain_id': self.get('HYPERION_CHAIN_ID', '133717'),
            'hyperion_explorer': self.get('HYPERION_EXPLORER_URL'),
            'metis_rpc': self.get('METIS_RPC_URL'),
            'metis_chain_id': self.get('METIS_CHAIN_ID', '1088'),
            'metis_explorer': self.get('METIS_EXPLORER_URL'),
            'lazai_rpc': self.get('LAZAI_RPC_URL'),
            'lazai_chain_id': self.get('LAZAI_CHAIN_ID', '9001'),
            'lazai_explorer': self.get('LAZAI_EXPLORER_URL'),
            'ethereum_rpc': self.get('ETHEREUM_RPC_URL'),
            'ethereum_chain_id': self.get('ETHEREUM_CHAIN_ID', '1'),
            'ethereum_explorer': self.get('ETHEREUM_EXPLORER_URL'),
            'polygon_rpc': self.get('POLYGON_RPC_URL'),
            'polygon_chain_id': self.get('POLYGON_CHAIN_ID', '137'),
            'polygon_explorer': self.get('POLYGON_EXPLORER_URL'),
            'arbitrum_rpc': self.get('ARBITRUM_RPC_URL'),
            'arbitrum_chain_id': self.get('ARBITRUM_CHAIN_ID', '42161'),
            'arbitrum_explorer': self.get('ARBITRUM_EXPLORER_URL'),
            'private_key': self.get('DEFAULT_PRIVATE_KEY') or self.get('PRIVATE_KEY')  # Prefer DEFAULT_PRIVATE_KEY
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
            'structured_logging': self.get('STRUCTURED_LOGGING', False),
            'environment': self.get('ENVIRONMENT', 'development'),
            'debug': self.get('DEBUG', False),
            'verbose': self.get('VERBOSE', False)
        }
    
    def get_lazai_config(self) -> Dict[str, str]:
        """Get LazAI network configuration"""
        return {
            'evm_address': self.get('LAZAI_EVM_ADDRESS'),
            'rsa_private_key': self.get('LAZAI_RSA_PRIVATE_KEY'),
            'ipfs_jwt': self.get('IPFS_JWT'),
            'api_key': self.get('LAZAI_API_KEY')
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return {
            'extensions_enabled': self.get('SECURITY_EXTENSIONS_ENABLED', True),
            'slither_enabled': self.get('SLITHER_ENABLED', True),
            'mythril_enabled': self.get('MYTHRIL_ENABLED', False),
            'edb_enabled': self.get('EDB_ENABLED', False),
            'rate_limit': self.get('RATE_LIMIT', 60)
        }
    
    def get_deployment_config(self) -> Dict[str, Any]:
        """Get deployment configuration"""
        return {
            'gas_price_multiplier': self.get('GAS_PRICE_MULTIPLIER', 1.0),
            'gas_limit': self.get('DEPLOYMENT_GAS_LIMIT', 8000000),
            'confirmation_blocks': self.get('CONFIRMATION_BLOCKS', 12),
            'auto_verify': self.get('AUTO_VERIFY', True)
        }
    
    def get_alith_config(self) -> Dict[str, Any]:
        """Get Alith SDK configuration"""
        return {
            'enabled': self.get('ALITH_ENABLED', True),
            'model': self.get('ALITH_MODEL', 'gpt-4o-mini'),
            'settlement': self.get('ALITH_SETTLEMENT', True),
            'inference_node': self.get('ALITH_INFERENCE_NODE'),
            'private_inference': self.get('ALITH_PRIVATE_INFERENCE', False)
        }
    
    # Obsidian methods removed - IPFS Pinata RAG is now exclusive

# Global instance
config = ConfigManager()
