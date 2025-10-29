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
try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings

# Import our new schema
from .schema import HyperKitConfig, validate_config, get_default_config

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Configuration settings from environment"""
    
    google_api_key: str = ""
    openai_api_key: str = ""
    # Obsidian fields removed - IPFS Pinata RAG is now exclusive
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
        if os.getenv('OPENAI_API_KEY'):
            self.config.setdefault('ai_providers', {}).setdefault('openai', {})['api_key'] = os.getenv('OPENAI_API_KEY')
        if os.getenv('ANTHROPIC_API_KEY'):
            self.config.setdefault('ai_providers', {}).setdefault('anthropic', {})['api_key'] = os.getenv('ANTHROPIC_API_KEY')
        if os.getenv('LAZAI_API_KEY'):
            self.config.setdefault('ai_providers', {}).setdefault('lazai', {})['api_key'] = os.getenv('LAZAI_API_KEY')
            self.config.setdefault('ai_providers', {}).setdefault('lazai', {})['model'] = 'gpt-4o-mini'  # Default model
            self.config.setdefault('ai_providers', {}).setdefault('lazai', {})['enabled'] = True
        
        # LazAI Network Configuration
        if os.getenv('LAZAI_EVM_ADDRESS'):
            self.config.setdefault('lazai', {})['evm_address'] = os.getenv('LAZAI_EVM_ADDRESS')
        if os.getenv('LAZAI_RSA_PRIVATE_KEY'):
            self.config.setdefault('lazai', {})['rsa_private_key'] = os.getenv('LAZAI_RSA_PRIVATE_KEY')
        if os.getenv('IPFS_JWT'):
            self.config.setdefault('lazai', {})['ipfs_jwt'] = os.getenv('IPFS_JWT')
        
        # Network RPC URLs - only for networks defined in config.yaml
        defined_networks = self.config.get('networks', {}).keys()
        for network_name in defined_networks:
            rpc_key = f'{network_name.upper()}_RPC_URL'
            chain_id_key = f'{network_name.upper()}_CHAIN_ID'
            explorer_key = f'{network_name.upper()}_EXPLORER_URL'
            
            if os.getenv(rpc_key):
                self.config['networks'][network_name]['rpc_url'] = os.getenv(rpc_key)
            if os.getenv(chain_id_key):
                self.config['networks'][network_name]['chain_id'] = int(os.getenv(chain_id_key))
            if os.getenv(explorer_key):
                self.config['networks'][network_name]['explorer_url'] = os.getenv(explorer_key)
        
        # Default Network
        if os.getenv('DEFAULT_NETWORK'):
            self.config['default_network'] = os.getenv('DEFAULT_NETWORK')
        
        # Wallet Configuration
        if os.getenv('DEFAULT_PRIVATE_KEY'):
            self.config['default_private_key'] = os.getenv('DEFAULT_PRIVATE_KEY')
        elif os.getenv('PRIVATE_KEY'):  # Legacy support
            self.config['default_private_key'] = os.getenv('PRIVATE_KEY')
        
        # IPFS Storage Configuration
        if os.getenv('PINATA_API_KEY'):
            self.config.setdefault('storage', {}).setdefault('pinata', {})['api_key'] = os.getenv('PINATA_API_KEY')
        if os.getenv('PINATA_SECRET_KEY'):
            self.config.setdefault('storage', {}).setdefault('pinata', {})['secret_key'] = os.getenv('PINATA_SECRET_KEY')
        elif os.getenv('PINATA_API_SECRET'):  # Legacy support
            self.config.setdefault('storage', {}).setdefault('pinata', {})['secret_key'] = os.getenv('PINATA_API_SECRET')
        
        # MCP Configuration (deprecated - IPFS Pinata RAG now used exclusively)
        if os.getenv('MCP_ENABLED'):
            self.config.setdefault('mcp', {})['enabled'] = os.getenv('MCP_ENABLED', 'false').lower() == 'true'
        if os.getenv('MCP_DOCKER'):
            self.config.setdefault('mcp', {})['docker'] = os.getenv('MCP_DOCKER', 'false').lower() == 'true'
        if os.getenv('MCP_HOST'):
            self.config.setdefault('mcp', {})['host'] = os.getenv('MCP_HOST')
        if os.getenv('MCP_PORT'):
            self.config.setdefault('mcp', {})['port'] = os.getenv('MCP_PORT')
        
        # Explorer API Keys
        if os.getenv('ETHEREUM_EXPLORER_API_KEY'):
            self.config.setdefault('explorers', {})['ethereum'] = os.getenv('ETHEREUM_EXPLORER_API_KEY')
        if os.getenv('POLYGON_EXPLORER_API_KEY'):
            self.config.setdefault('explorers', {})['polygon'] = os.getenv('POLYGON_EXPLORER_API_KEY')
        if os.getenv('ARBITRUM_EXPLORER_API_KEY'):
            self.config.setdefault('explorers', {})['arbitrum'] = os.getenv('ARBITRUM_EXPLORER_API_KEY')
        if os.getenv('METIS_EXPLORER_API_KEY'):
            self.config.setdefault('explorers', {})['metis'] = os.getenv('METIS_EXPLORER_API_KEY')
        
        # IPFS Pinata RAG is now the exclusive RAG backend - no Obsidian config needed
        
        # Logging Configuration
        if os.getenv('LOG_LEVEL'):
            self.config.setdefault('logging', {})['level'] = os.getenv('LOG_LEVEL')
        if os.getenv('STRUCTURED_LOGGING'):
            self.config.setdefault('logging', {})['structured'] = os.getenv('STRUCTURED_LOGGING').lower() == 'true'
        if os.getenv('ENVIRONMENT'):
            self.config['environment'] = os.getenv('ENVIRONMENT')
        if os.getenv('DEBUG'):
            self.config.setdefault('logging', {})['debug'] = os.getenv('DEBUG').lower() == 'true'
        if os.getenv('VERBOSE'):
            self.config.setdefault('logging', {})['verbose'] = os.getenv('VERBOSE').lower() == 'true'
        
        # Security Configuration
        if os.getenv('SECURITY_EXTENSIONS_ENABLED'):
            self.config.setdefault('security', {})['extensions_enabled'] = os.getenv('SECURITY_EXTENSIONS_ENABLED').lower() == 'true'
        if os.getenv('SLITHER_ENABLED'):
            self.config.setdefault('security', {})['slither_enabled'] = os.getenv('SLITHER_ENABLED').lower() == 'true'
        if os.getenv('MYTHRIL_ENABLED'):
            self.config.setdefault('security', {})['mythril_enabled'] = os.getenv('MYTHRIL_ENABLED').lower() == 'true'
        if os.getenv('EDB_ENABLED'):
            self.config.setdefault('security', {})['edb_enabled'] = os.getenv('EDB_ENABLED').lower() == 'true'
        if os.getenv('RATE_LIMIT'):
            self.config.setdefault('security', {})['rate_limit'] = int(os.getenv('RATE_LIMIT'))
        
        # Deployment Configuration
        if os.getenv('GAS_PRICE_MULTIPLIER'):
            self.config.setdefault('deployment', {})['gas_price_multiplier'] = float(os.getenv('GAS_PRICE_MULTIPLIER'))
        if os.getenv('DEPLOYMENT_GAS_LIMIT'):
            self.config.setdefault('deployment', {})['gas_limit'] = int(os.getenv('DEPLOYMENT_GAS_LIMIT'))
        if os.getenv('CONFIRMATION_BLOCKS'):
            self.config.setdefault('deployment', {})['confirmation_blocks'] = int(os.getenv('CONFIRMATION_BLOCKS'))
        if os.getenv('AUTO_VERIFY'):
            self.config.setdefault('deployment', {})['auto_verify'] = os.getenv('AUTO_VERIFY').lower() == 'true'
        
        # Development Configuration
        if os.getenv('TEST_MODE'):
            self.config.setdefault('development', {})['test_mode'] = os.getenv('TEST_MODE').lower() == 'true'
        if os.getenv('CACHE_DIR'):
            self.config.setdefault('development', {})['cache_dir'] = os.getenv('CACHE_DIR')
        
        # Alith SDK Configuration
        if os.getenv('ALITH_ENABLED'):
            self.config.setdefault('alith', {})['enabled'] = os.getenv('ALITH_ENABLED').lower() == 'true'
        if os.getenv('ALITH_MODEL'):
            self.config.setdefault('alith', {})['model'] = os.getenv('ALITH_MODEL')
        if os.getenv('ALITH_SETTLEMENT'):
            self.config.setdefault('alith', {})['settlement'] = os.getenv('ALITH_SETTLEMENT').lower() == 'true'
        if os.getenv('ALITH_INFERENCE_NODE'):
            self.config.setdefault('alith', {})['inference_node'] = os.getenv('ALITH_INFERENCE_NODE')
        if os.getenv('ALITH_PRIVATE_INFERENCE'):
            self.config.setdefault('alith', {})['private_inference'] = os.getenv('ALITH_PRIVATE_INFERENCE').lower() == 'true'
    
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
                # Obsidian config removed - IPFS Pinata RAG exclusive
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