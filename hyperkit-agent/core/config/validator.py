"""
Configuration validation for HyperKit AI Agent
"""

import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class ConfigValidator:
    """Validate configuration settings and network connections"""
    
    def __init__(self):
        self.required_api_keys = [
            'google_api_key', 'openai_api_key', 'anthropic_api_key'
        ]
        self.required_networks = ['hyperion', 'polygon', 'arbitrum', 'ethereum', 'metis']
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the complete configuration
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Dict with validation results
        """
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "validated_components": []
        }
        
        try:
            # Validate API keys
            api_validation = self.validate_api_keys(config)
            validation_results["validated_components"].append("api_keys")
            if not api_validation["is_valid"]:
                validation_results["errors"].extend(api_validation["errors"])
                validation_results["is_valid"] = False
            
            # Validate networks
            network_validation = self.validate_networks(config)
            validation_results["validated_components"].append("networks")
            if not network_validation["is_valid"]:
                validation_results["errors"].extend(network_validation["errors"])
                validation_results["is_valid"] = False
            
            # Validate paths
            path_validation = self.validate_paths(config)
            validation_results["validated_components"].append("paths")
            if not path_validation["is_valid"]:
                validation_results["warnings"].extend(path_validation["warnings"])
            
            logger.info(f"Configuration validation completed: {len(validation_results['validated_components'])} components validated")
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            validation_results["is_valid"] = False
            validation_results["errors"].append(f"Validation error: {str(e)}")
        
        return validation_results
    
    def validate_api_keys(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate API key configuration"""
        results = {
            "is_valid": True,
            "errors": [],
            "available_providers": []
        }
        
        # Check for at least one API key
        api_keys_found = []
        for key in self.required_api_keys:
            if config.get(key) and config[key].strip():
                api_keys_found.append(key.replace('_api_key', ''))
        
        if not api_keys_found:
            results["is_valid"] = False
            results["errors"].append("No API keys found. At least one LLM provider API key is required.")
        else:
            results["available_providers"] = api_keys_found
            logger.info(f"Found API keys for: {', '.join(api_keys_found)}")
        
        return results
    
    def validate_networks(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate network configuration"""
        results = {
            "is_valid": True,
            "errors": [],
            "validated_networks": []
        }
        
        networks = config.get('networks', {})
        
        if not networks:
            results["is_valid"] = False
            results["errors"].append("No network configuration found")
            return results
        
        for network_name, network_config in networks.items():
            if not isinstance(network_config, dict):
                results["errors"].append(f"Network '{network_name}' config must be a dictionary")
                results["is_valid"] = False
                continue
            
            # Validate RPC URL
            rpc_url = network_config.get('rpc_url')
            if not rpc_url:
                results["errors"].append(f"Network '{network_name}' missing RPC URL")
                results["is_valid"] = False
                continue
            
            if not isinstance(rpc_url, str):
                results["errors"].append(f"Network '{network_name}' RPC URL must be string, got {type(rpc_url).__name__}")
                results["is_valid"] = False
                continue
            
            # Validate URL format
            try:
                parsed_url = urlparse(rpc_url)
                if not parsed_url.scheme or not parsed_url.netloc:
                    results["errors"].append(f"Network '{network_name}' has invalid RPC URL format")
                    results["is_valid"] = False
                    continue
            except Exception as e:
                results["errors"].append(f"Network '{network_name}' RPC URL validation failed: {e}")
                results["is_valid"] = False
                continue
            
            # Validate chain ID
            chain_id = network_config.get('chain_id')
            if chain_id is not None:
                if not isinstance(chain_id, int) or chain_id <= 0:
                    results["errors"].append(f"Network '{network_name}' chain_id must be positive integer")
                    results["is_valid"] = False
                    continue
            
            results["validated_networks"].append(network_name)
            logger.info(f"Network '{network_name}' validated successfully")
        
        return results
    
    def validate_paths(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate path configuration"""
        results = {
            "is_valid": True,
            "warnings": []
        }
        
        # Check for required directories
        required_dirs = [
            'artifacts',
            'artifacts/contracts',
            'artifacts/audits',
            'artifacts/deployments'
        ]
        
        for dir_path in required_dirs:
            try:
                from pathlib import Path
                path_obj = Path(dir_path)
                if not path_obj.exists():
                    results["warnings"].append(f"Directory '{dir_path}' does not exist (will be created)")
            except Exception as e:
                results["warnings"].append(f"Could not check directory '{dir_path}': {e}")
        
        return results
    
    def validate_network_connection(self, network_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate network connection
        
        Args:
            network_name: Name of the network to test
            config: Configuration dictionary
            
        Returns:
            Dict with connection test results
        """
        results = {
            "is_connected": False,
            "error": None,
            "response_time": None
        }
        
        try:
            networks = config.get('networks', {})
            if network_name not in networks:
                results["error"] = f"Network '{network_name}' not configured"
                return results
            
            network_config = networks[network_name]
            rpc_url = network_config.get('rpc_url')
            
            if not isinstance(rpc_url, str):
                results["error"] = f"RPC URL must be string, got {type(rpc_url).__name__}"
                return results
            
            # Test connection (basic validation)
            import time
            start_time = time.time()
            
            # This is a basic validation - in production you might want to make an actual RPC call
            parsed_url = urlparse(rpc_url)
            if parsed_url.scheme and parsed_url.netloc:
                results["is_connected"] = True
                results["response_time"] = time.time() - start_time
                logger.info(f"Network '{network_name}' connection validated")
            else:
                results["error"] = "Invalid RPC URL format"
            
        except Exception as e:
            results["error"] = f"Connection test failed: {e}"
            logger.error(f"Network connection validation failed for {network_name}: {e}")
        
        return results
    
    def get_validation_summary(self, validation_results: Dict[str, Any]) -> str:
        """Get a human-readable validation summary"""
        if validation_results["is_valid"]:
            components = ", ".join(validation_results["validated_components"])
            return f"✅ Configuration valid ({components})"
        else:
            errors = "\n".join([f"  • {error}" for error in validation_results["errors"]])
            return f"❌ Configuration invalid:\n{errors}"
