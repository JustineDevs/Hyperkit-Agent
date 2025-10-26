"""
Production-ready smart contract deployer
Uses Foundry (forge) for compilation and deployment
Replaces solcx for better cross-platform support
"""

import logging
from typing import Dict, Any, Optional

# Import Foundry components
from .foundry_deployer import FoundryDeployer
from .foundry_manager import FoundryManager
from .constructor_parser import ConstructorArgumentParser

logger = logging.getLogger(__name__)

class MultiChainDeployer:
    """Production-ready smart contract deployer using Foundry (forge)"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Foundry deployer with production-ready features
        
        Args:
            config: Dictionary containing network configurations
        """
        self.config = config or {}
        
        # Ensure Foundry is installed (optional)
        self.foundry_manager = FoundryManager()
        try:
            if self.foundry_manager.ensure_installed():
                self.foundry_available = True
            else:
                logger.warning("Foundry setup failed - deployment will be simulated")
                self.foundry_available = False
        except Exception as e:
            logger.warning(f"Foundry setup failed: {e}")
            logger.warning("Deployment will be simulated without actual blockchain deployment")
            self.foundry_available = False
        
        # Initialize Foundry deployer
        self.foundry_deployer = FoundryDeployer()
        
        logger.info("✅ MultiChainDeployer initialized with Foundry")
    
    def deploy(self, contract_source_code: str, rpc_url: str, chain_id: int = 133717, contract_name: str = "Contract", deployer_address: str = None) -> dict:
        """
        Deploy contract using Foundry with proper constructor argument extraction
        
        Args:
            contract_source_code: Solidity contract code (STRING)
            rpc_url: RPC endpoint URL (STRING)
            chain_id: Blockchain chain ID (INT)
            contract_name: Contract name for deployment
            deployer_address: Address of the deployer (for constructor args)
        
        Returns:
            {"success": True/False, "transaction_hash": "...", "contract_address": "..."}
        """
        if not self.foundry_available:
            error_msg = (
                "Foundry is required for deployment but is not installed or not available.\n"
                "Install Foundry:\n"
                "  curl -L https://foundry.paradigm.xyz | bash\n"
                "  foundryup\n"
                "Or visit: https://book.getfoundry.sh/getting-started/installation"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Extract constructor arguments from contract code
        parser = ConstructorArgumentParser()
        constructor_args = parser.generate_constructor_args(contract_source_code, deployer_address or "0x0000000000000000000000000000000000000000")
        
        # Log what we're using
        logger.info(f"Constructor args extracted: {constructor_args}")
        
        # If ERC20, verify name/symbol match expectations
        name, symbol = parser.extract_erc20_name_symbol(contract_source_code)
        if name and symbol:
            logger.info(f"Deploying ERC20: {name} ({symbol})")
        
        # Validate constructor args
        validation = parser.validate_constructor_args(contract_source_code, constructor_args)
        if not validation["success"]:
            logger.error(f"Constructor validation failed: {validation['error']}")
            return {
                "success": False,
                "error": f"Constructor validation failed: {validation['error']}",
                "validation_details": validation
            }
        
        return self.foundry_deployer.deploy(
            contract_source_code=contract_source_code,
            rpc_url=rpc_url,
            chain_id=chain_id,
            contract_name=contract_name,
            constructor_args=constructor_args
        )
    
    def get_network_config(self, network_name: str) -> Dict[str, Any]:
        """
        Get network configuration
        
        Args:
            network_name: Name of the network
            
        Returns:
            Network configuration dictionary
        """
        return self.config.get('networks', {}).get(network_name, {})
    
    def deploy_to_network(self, contract_source_code: str, network_name: str, contract_name: str = "Contract") -> dict:
        """
        Deploy contract to a specific network using configuration
        
        Args:
            contract_source_code: Solidity contract code
            network_name: Name of the network to deploy to
            contract_name: Contract name for deployment
            
        Returns:
            Deployment result dictionary
        """
        network_config = self.get_network_config(network_name)
        
        if not network_config:
            return {
                "success": False,
                "error": f"Network '{network_name}' not found in configuration",
                "suggestions": ["Check network name", "Verify configuration"]
            }
        
        rpc_url = network_config.get('rpc_url')
        chain_id = network_config.get('chain_id')
        
        if not rpc_url or not chain_id:
            return {
                "success": False,
                "error": f"Network '{network_name}' missing RPC URL or chain ID",
                "suggestions": ["Check network configuration"]
            }
        
        return self.deploy(
            contract_source_code=contract_source_code,
            rpc_url=rpc_url,
            chain_id=chain_id,
            contract_name=contract_name
        )