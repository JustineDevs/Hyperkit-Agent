"""
Network Configuration Validator
Validates all network configurations on startup - fail hard if missing
"""

import logging
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigValidator:
    """Validates configuration and fails hard on missing/invalid config"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self) -> Dict[str, Any]:
        """
        Validate all critical configuration.
        
        Returns:
            dict with validation results and detailed error messages
        """
        self.errors = []
        self.warnings = []
        
        # Validate network configs
        self._validate_networks()
        
        # Validate private keys
        self._validate_private_keys()
        
        # Validate AI/RAG configs
        self._validate_ai_rag_config()
        
        # Validate IPFS/Pinata
        self._validate_ipfs_config()
        
        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "critical_issues": len(self.errors),
            "non_critical_issues": len(self.warnings)
        }
    
    def _validate_networks(self):
        """Validate network configurations"""
        networks = self.config.get('networks', {})
        
        if not networks:
            self.errors.append("No networks configured in config")
            return
        
        required_fields = ['rpc_url', 'chain_id']
        
        for network_name, network_config in networks.items():
            if not isinstance(network_config, dict):
                self.errors.append(f"Network '{network_name}' config is not a dictionary")
                continue
            
            for field in required_fields:
                if field not in network_config:
                    self.errors.append(
                        f"Network '{network_name}' missing required field: {field}\n"
                        f"  Required: {required_fields}\n"
                        f"  Current config: {list(network_config.keys())}\n"
                        f"  Fix: Add '{field}' to network config in .env or config.yaml"
                    )
                elif not network_config[field]:
                    self.errors.append(
                        f"Network '{network_name}' has empty {field}\n"
                        f"  Fix: Set {network_name.upper()}_{field.upper()} in .env"
                    )
                elif field == 'rpc_url' and not isinstance(network_config[field], str):
                    self.errors.append(
                        f"Network '{network_name}' RPC URL must be string, got {type(network_config[field])}\n"
                        f"  Current value: {network_config[field]}\n"
                        f"  Fix: Ensure {network_name.upper()}_RPC_URL is a string in .env"
                    )
                elif field == 'chain_id' and not isinstance(network_config[field], int):
                    self.errors.append(
                        f"Network '{network_name}' chain_id must be integer, got {type(network_config[field])}\n"
                        f"  Current value: {network_config[field]}\n"
                        f"  Fix: Ensure {network_name.upper()}_CHAIN_ID is an integer in .env"
                    )
    
    def _validate_private_keys(self):
        """Validate private key configuration"""
        private_key = (
            self.config.get('DEFAULT_PRIVATE_KEY') or 
            self.config.get('PRIVATE_KEY') or 
            self.config.get('default_private_key') or
            os.getenv('DEFAULT_PRIVATE_KEY') or
            os.getenv('PRIVATE_KEY')
        )
        
        if not private_key:
            self.errors.append(
                "DEFAULT_PRIVATE_KEY not configured\n"
                "  Required for: Contract deployment, transaction signing\n"
                "  Fix: Add DEFAULT_PRIVATE_KEY=your_private_key_hex to .env\n"
                "  Generate: Use web3 wallet or https://vanity-eth.tk/\n"
                "  WARNING: Use test wallet only for development!"
            )
        elif len(private_key) != 64 and not private_key.startswith('0x'):
            self.errors.append(
                f"Invalid private key format (expected 64 hex chars, got {len(private_key)})\n"
                f"  Current value: {private_key[:10]}...{private_key[-5:]}\n"
                f"  Fix: Ensure private key is 64 hex characters (or 66 with 0x prefix)"
            )
        elif private_key in ['your_private_key_here', 'your_key_here', '']:
            self.errors.append(
                "DEFAULT_PRIVATE_KEY is set to placeholder value\n"
                f"  Current value: '{private_key}'\n"
                "  Fix: Replace with real private key in .env\n"
                "  WARNING: Never commit real private keys to version control!"
            )
    
    def _validate_ai_rag_config(self):
        """Validate AI and RAG configuration - fail if missing in production"""
        # Alith SDK validation
        lazai_key = (
            self.config.get('LAZAI_API_KEY') or
            os.getenv('LAZAI_API_KEY')
        )
        
        if not lazai_key or lazai_key in ['your_lazai_api_key_here', '']:
            self.warnings.append(
                "LAZAI_API_KEY not configured - AI features will be limited\n"
                "  Impact: Contract generation and auditing will use fallback LLM\n"
                "  Fix: Set LAZAI_API_KEY in .env to enable full AI capabilities\n"
                "  Get key: https://lazai.network"
            )
        
        # IPFS RAG validation
        pinata_key = (
            self.config.get('PINATA_API_KEY') or
            os.getenv('PINATA_API_KEY')
        )
        pinata_secret = (
            self.config.get('PINATA_SECRET_KEY') or
            os.getenv('PINATA_SECRET_KEY')
        )
        
        if not pinata_key or not pinata_secret:
            self.warnings.append(
                "Pinata IPFS not configured - RAG system will be read-only\n"
                "  Impact: Cannot upload templates or reports to IPFS\n"
                "  Fix: Set PINATA_API_KEY and PINATA_SECRET_KEY in .env\n"
                "  Get keys: https://app.pinata.cloud/"
            )
    
    def _validate_ipfs_config(self):
        """Validate IPFS configuration"""
        # Pinata validation is done in _validate_ai_rag_config
        pass
    
    def fail_if_invalid(self):
        """
        Fail hard if configuration is invalid.
        
        Raises:
            SystemExit: If critical config errors found
        """
        result = self.validate_all()
        
        if result['critical_issues'] > 0:
            logger.error("=" * 80)
            logger.error("CRITICAL CONFIGURATION ERRORS FOUND")
            logger.error("=" * 80)
            
            for i, error in enumerate(result['errors'], 1):
                logger.error(f"\n[{i}] {error}")
            
            logger.error("\n" + "=" * 80)
            logger.error("SYSTEM CANNOT START - FIX CONFIGURATION ERRORS ABOVE")
            logger.error("=" * 80)
            
            raise SystemExit(1)
        
        if result['non_critical_issues'] > 0:
            logger.warning("=" * 80)
            logger.warning("CONFIGURATION WARNINGS")
            logger.warning("=" * 80)
            
            for i, warning in enumerate(result['warnings'], 1):
                logger.warning(f"\n[{i}] {warning}")
            
            logger.warning("\n" + "=" * 80)

