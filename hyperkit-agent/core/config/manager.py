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
            # Validate config on startup - fail hard on critical errors
            self._validate_startup_config()
    
    def _load_config(self):
        """Load configuration from multiple sources"""
        self._config = {}
        
        # Load environment variables - check project root first
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / ".env"
        if env_file.exists():
            load_dotenv(dotenv_path=str(env_file), override=True)
        else:
            load_dotenv(override=True)
        
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
            # LAZAI_API_KEY removed - LazAI is network-only, NOT an AI agent
            # Use OPENAI_API_KEY for Alith SDK (only AI agent)
            
            # LazAI Network Configuration - DEPRECATED (network-only, not AI agent)
            # Future network support documented in ROADMAP.md only
            # 'LAZAI_EVM_ADDRESS': os.getenv('LAZAI_EVM_ADDRESS'),  # Not used
            # 'LAZAI_RSA_PRIVATE_KEY': os.getenv('LAZAI_RSA_PRIVATE_KEY'),  # Not used
            'IPFS_JWT': os.getenv('IPFS_JWT'),
            
            # Blockchain Network Configuration
            'DEFAULT_NETWORK': os.getenv('DEFAULT_NETWORK', 'hyperion'),
            'HYPERION_RPC_URL': os.getenv('HYPERION_RPC_URL'),
            'HYPERION_CHAIN_ID': os.getenv('HYPERION_CHAIN_ID', '133717'),
            'HYPERION_EXPLORER_URL': os.getenv('HYPERION_EXPLORER_URL'),
            # HYPERION-ONLY: Metis and LazAI network configs removed
            # Future network support documented in ROADMAP.md only
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
        """
        Get all API keys - HYPERION-ONLY MODE.
        
        Returns API keys for Alith SDK (OpenAI), IPFS Pinata RAG, and fallback LLMs.
        LazAI API key removed - LazAI is network-only, NOT an AI agent.
        """
        return {
            'openai': self.get('OPENAI_API_KEY'),  # Required for Alith SDK (ONLY AI agent)
            'google': self.get('GOOGLE_API_KEY'),  # Optional fallback LLM
            'anthropic': self.get('ANTHROPIC_API_KEY'),  # Optional fallback LLM
            # LAZAI_API_KEY removed - LazAI is network-only, NOT an AI agent
            'pinata': self.get('PINATA_API_KEY')  # Required for IPFS Pinata RAG (exclusive)
        }
    
    def get_network_config(self) -> Dict[str, str]:
        """
        Get network configuration - HYPERION ONLY.
        
        Returns Hyperion network configuration only.
        Future network support (LazAI, Metis) documented in ROADMAP.md only.
        """
        return {
            'default_network': 'hyperion',  # Hardcoded - Hyperion is exclusive
            'hyperion_rpc': self.get('HYPERION_RPC_URL'),
            'hyperion_chain_id': self.get('HYPERION_CHAIN_ID', '133717'),
            'hyperion_explorer': self.get('HYPERION_EXPLORER_URL'),
            'private_key': self.get('DEFAULT_PRIVATE_KEY') or self.get('PRIVATE_KEY'),
            # HYPERION-ONLY: LazAI, Metis, and other networks removed
            # Future network support documented in ROADMAP.md only
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
        """
        DEPRECATED: LazAI network configuration removed (HYPERION-ONLY MODE).
        
        LazAI is network-only (blockchain RPC), NOT an AI agent.
        Future network support documented in ROADMAP.md only.
        
        Raises:
            NotImplementedError: Always - LazAI config removed for Hyperion-only mode
        """
        raise NotImplementedError(
            "LazAI network configuration removed (HYPERION-ONLY MODE)\n"
            "  Hyperion is the exclusive deployment target\n"
            "  LazAI is network-only, NOT an AI agent\n"
            "  Future network support documented in ROADMAP.md only"
        )
    
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
    
    def _validate_startup_config(self):
        """
        Validate critical configuration on startup - abort if missing/invalid.
        This prevents runtime errors by catching config issues early.
        """
        from core.config.config_validator import ConfigValidator
        
        # Boot-time config validation - fail hard on critical errors
        validator = ConfigValidator(self._config)
        validator.fail_if_invalid()  # Raises SystemExit(1) if critical errors found
        
        # If we reach here, validation passed (no critical errors)
        # Log warnings if any (critical errors already handled by fail_if_invalid)
        result = validator.validate_all()
        if result['non_critical_issues'] > 0:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("=" * 80)
            logger.warning("CONFIGURATION WARNINGS")
            logger.warning("=" * 80)
            for warning in result['warnings']:
                logger.warning(f"\n[WARNING] {warning}")
            logger.warning("=" * 80)

# Global instance
config = ConfigManager()
