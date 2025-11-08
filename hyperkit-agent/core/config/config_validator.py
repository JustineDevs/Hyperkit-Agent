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
    
    def validate_all(self, skip_private_key: bool = False) -> Dict[str, Any]:
        """
        Validate all critical configuration.
        
        Args:
            skip_private_key: If True, skip private key validation (for informational commands)
        
        Returns:
            dict with validation results and detailed error messages
        """
        self.errors = []
        self.warnings = []
        
        # Validate network configs
        self._validate_networks()
        
        # Validate private keys (unless skipped for informational commands)
        if not skip_private_key:
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
        """
        Validate network configurations - HYPERION ONLY.
        
        CRITICAL: Fail hard if non-Hyperion networks configured.
        Future network support documented in ROADMAP.md only.
        """
        networks = self.config.get('networks', {})
        
        if not networks:
            self.errors.append("CRITICAL: No networks configured - Hyperion is required")
            return
        
        # HYPERION-ONLY: Reject LazAI and Metis network configs
        unsupported_networks = ['lazai', 'metis', 'ethereum', 'polygon', 'arbitrum']
        for network_name in networks.keys():
            network_lower = network_name.lower()
            if network_lower in unsupported_networks:
                self.errors.append(
                    f"CRITICAL: Network '{network_name}' is not supported (HYPERION-ONLY MODE)\n"
                    f"  Removed networks: {', '.join(unsupported_networks)}\n"
                    f"  Supported network: hyperion only\n"
                    f"  Future network support documented in ROADMAP.md only\n"
                    f"  Fix: Remove '{network_name}' from config.yaml/.env"
                )
                continue
        
        # Validate Hyperion network exists and is properly configured
        if 'hyperion' not in networks:
            self.errors.append(
                "CRITICAL: Hyperion network not configured (HYPERION-ONLY MODE)\n"
                "  Required: Hyperion network configuration in config.yaml/.env\n"
                "  Fix: Add Hyperion network config (chain_id: 133717)"
            )
            return
        
        hyperion_config = networks.get('hyperion', {})
        required_fields = ['rpc_url', 'chain_id']
        
        for field in required_fields:
            if field not in hyperion_config:
                self.errors.append(
                    f"CRITICAL: Hyperion network missing required field: {field}\n"
                    f"  Required: {required_fields}\n"
                    f"  Current config: {list(hyperion_config.keys())}\n"
                    f"  Fix: Add '{field}' to Hyperion network config"
                )
            elif not hyperion_config[field]:
                self.errors.append(
                    f"CRITICAL: Hyperion network has empty {field}\n"
                    f"  Fix: Set HYPERION_{field.upper()} in .env"
                )
            elif field == 'rpc_url' and not isinstance(hyperion_config[field], str):
                self.errors.append(
                    f"CRITICAL: Hyperion RPC URL must be string\n"
                    f"  Current value: {hyperion_config[field]}\n"
                    f"  Fix: Ensure HYPERION_RPC_URL is a string"
                )
            elif field == 'chain_id' and hyperion_config[field] != 133717:
                self.errors.append(
                    f"CRITICAL: Hyperion chain_id must be 133717\n"
                    f"  Current value: {hyperion_config[field]}\n"
                    f"  Fix: Set HYPERION_CHAIN_ID=133717"
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
        """
        Validate AI and RAG configuration.
        
        NOTE: LazAI is network-only (blockchain RPC), NOT an AI agent.
        Alith SDK is the ONLY AI agent and uses OpenAI API key.
        """
        # Check for deprecated config keys and reject them
        deprecated_keys = {
            'OBSIDIAN_API_KEY': 'Obsidian RAG is deprecated - use IPFS Pinata RAG instead',
            'OBSIDIAN_MCP_API_KEY': 'Obsidian MCP RAG is deprecated - use IPFS Pinata RAG instead',
            'MCP_ENABLED': 'MCP/Obsidian RAG is deprecated - IPFS Pinata RAG is exclusive',
            'LAZAI_API_KEY': 'LazAI is network-only (not AI agent) - use OPENAI_API_KEY for Alith SDK',
        }
        
        for deprecated_key, message in deprecated_keys.items():
            if self.config.get(deprecated_key) or os.getenv(deprecated_key):
                self.warnings.append(
                    f"Deprecated config key detected: {deprecated_key}\n"
                    f"  {message}\n"
                    f"  Action: Remove {deprecated_key} from .env and config.yaml\n"
                    f"  Fix: Use IPFS Pinata for RAG, OpenAI key for Alith SDK"
                )
        
        # Alith SDK validation - uses OpenAI API key, not LazAI key
        openai_key = (
            self.config.get('OPENAI_API_KEY') or
            self.config.get('openai', {}).get('api_key') or
            os.getenv('OPENAI_API_KEY')
        )
        
        alith_enabled = (
            self.config.get('ALITH_ENABLED') or
            self.config.get('alith', {}).get('enabled') or
            os.getenv('ALITH_ENABLED', 'true').lower() == 'true'
        )
        
        if alith_enabled and (not openai_key or openai_key in ['your_openai_api_key_here', '']):
            self.warnings.append(
                "Alith SDK enabled but OpenAI API key not configured\n"
                "  Impact: Alith SDK requires OpenAI API key - advanced AI features disabled\n"
                "  Fix: Set OPENAI_API_KEY in .env (Alith SDK uses OpenAI key)\n"
                "  Get key: https://platform.openai.com/api-keys\n"
                "  Note: LazAI is network-only, NOT used for AI agent"
            )
        
        # IPFS RAG validation - check multiple locations
        pinata_key = (
            self.config.get('PINATA_API_KEY') or
            self.config.get('storage', {}).get('pinata', {}).get('api_key') or
            os.getenv('PINATA_API_KEY')
        )
        pinata_secret = (
            self.config.get('PINATA_SECRET_KEY') or
            self.config.get('storage', {}).get('pinata', {}).get('secret_key') or
            os.getenv('PINATA_SECRET_KEY') or
            os.getenv('PINATA_API_SECRET')  # Legacy support
        )
        
        if not pinata_key or not pinata_secret:
            self.errors.append(
                "Pinata IPFS not configured - RAG system requires Pinata\n"
                "  Required for: IPFS RAG context retrieval, template upload, report storage\n"
                "  Impact: RAG operations will fail without Pinata credentials\n"
                "  Fix: Set PINATA_API_KEY and PINATA_SECRET_KEY in .env\n"
                "  Get keys: https://app.pinata.cloud/\n"
                "  Note: IPFS Pinata is now the exclusive RAG backend - no fallbacks"
            )
    
    def _validate_ipfs_config(self):
        """Validate IPFS configuration"""
        # Pinata validation is done in _validate_ai_rag_config
        pass
    
    def fail_if_invalid(self, skip_private_key: bool = False):
        """
        Fail hard if configuration is invalid.
        
        Args:
            skip_private_key: If True, skip private key validation (for informational commands)
        
        Raises:
            SystemExit: If critical config errors found
        """
        result = self.validate_all(skip_private_key=skip_private_key)
        
        if result['critical_issues'] > 0:
            logger.error("=" * 80)
            logger.error("CRITICAL CONFIGURATION ERRORS FOUND")
            logger.error("=" * 80)
            
            for i, error in enumerate(result['errors'], 1):
                logger.error(f"\n[{i}] {error}")
            
            logger.error("\n" + "=" * 80)
            logger.error("SYSTEM CANNOT START - FIX CONFIGURATION ERRORS ABOVE")
            logger.error("=" * 80)
            logger.error("\n📖 Documentation: https://github.com/JustineDevs/HyperAgent/blob/main/docs/GUIDE/CONFIGURATION_GUIDE.md")
            logger.error("🔧 Quick Fix: Copy .env.example to .env and fill in required values")
            logger.error("=" * 80)
            
            raise SystemExit(1)
        
        if result['non_critical_issues'] > 0:
            logger.warning("=" * 80)
            logger.warning("CONFIGURATION WARNINGS")
            logger.warning("=" * 80)
            
            for i, warning in enumerate(result['warnings'], 1):
                logger.warning(f"\n[{i}] {warning}")
            
            logger.warning("\n" + "=" * 80)

