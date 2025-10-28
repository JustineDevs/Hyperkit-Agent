"""
Production-ready smart contract deployer
Uses Foundry (forge) for compilation and deployment
Replaces solcx for better cross-platform support

Enhanced with user override for constructor arguments:
- Command-line arguments via --constructor-args
- JSON file support via --constructor-file
- Type coercion and validation
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

# Import Foundry components
from .foundry_deployer import FoundryDeployer
from .foundry_manager import FoundryManager
from .constructor_parser import ConstructorArgumentParser
from .error_messages import DeploymentErrorMessages

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
    
    def deploy(
        self, 
        contract_source_code: str, 
        rpc_url: str, 
        chain_id: int = 133717, 
        contract_name: str = "Contract", 
        deployer_address: str = None,
        constructor_args: Optional[List[Any]] = None,
        constructor_file: Optional[str] = None
    ) -> dict:
        """
        Deploy contract using Foundry with proper constructor argument extraction.
        
        Enhanced with user override capabilities for constructor arguments.
        
        Args:
            contract_source_code: Solidity contract code
            rpc_url: RPC endpoint URL
            chain_id: Blockchain chain ID
            contract_name: Contract name for deployment
            deployer_address: Address of the deployer (for auto-generated args)
            constructor_args: Optional list of constructor arguments (overrides auto-detection)
            constructor_file: Optional path to JSON file with constructor arguments
        
        Returns:
            {"success": True/False, "transaction_hash": "...", "contract_address": "..."}
            
        Examples:
            # Auto-detect constructor args
            deploy(contract_code, rpc_url)
            
            # Provide custom args
            deploy(contract_code, rpc_url, constructor_args=["0x1234...", 1000000])
            
            # Load from JSON file
            deploy(contract_code, rpc_url, constructor_file="args.json")
        """
        if not self.foundry_available:
            error_result = DeploymentErrorMessages.foundry_not_available()
            logger.error(error_result["error"])
            for step in error_result["installation_steps"]:
                logger.error(f"  {step}")
            return error_result
        
        parser = ConstructorArgumentParser()
        
        # Determine constructor arguments source
        if constructor_file:
            # Load from JSON file
            logger.info(f"Loading constructor args from file: {constructor_file}")
            try:
                final_args = self.load_constructor_args_from_file(
                    constructor_file, 
                    contract_source_code, 
                    deployer_address
                )
                logger.info(f"✓ Loaded constructor args from file: {final_args}")
            except Exception as e:
                # Extract expected parameters for better error message
                expected_params = parser.extract_constructor_params(contract_source_code)
                error_result = DeploymentErrorMessages.file_load_failed(
                    constructor_file,
                    e,
                    expected_params
                )
                logger.error(error_result["error"])
                for suggestion in error_result["suggestions"]:
                    logger.error(f"  {suggestion}")
                return error_result
        
        elif constructor_args is not None:
            # Use provided arguments
            logger.info(f"Using provided constructor args: {constructor_args}")
            final_args = constructor_args
        
        else:
            # Auto-detect from contract code
            logger.info("Auto-detecting constructor args from contract code")
            final_args = parser.generate_constructor_args(
                contract_source_code, 
                deployer_address or "0x0000000000000000000000000000000000000000"
            )
            logger.info(f"✓ Auto-detected constructor args: {final_args}")
        
        # Log contract info if ERC20/ERC721
        name, symbol = parser.extract_erc20_name_symbol(contract_source_code)
        if name and symbol:
            logger.info(f"📝 Deploying ERC20: {name} ({symbol})")
        
        # Validate constructor args
        logger.info("Validating constructor arguments...")
        validation = parser.validate_constructor_args(contract_source_code, final_args)
        
        if not validation["success"]:
            error_details = validation.get("details", [])
            expected_params = parser.extract_constructor_params(contract_source_code)
            
            error_result = DeploymentErrorMessages.constructor_validation_failed(
                validation['error'],
                final_args,
                expected_params,
                contract_name
            )
            
            logger.error(f"❌ {error_result['error']}")
            for suggestion in error_result["suggestions"]:
                logger.error(f"  {suggestion}")
            
            # Show examples in logs
            if "examples" in error_result:
                logger.info("\n📚 Usage Examples:")
                logger.info(f"  CLI: {error_result['examples']['cli_inline']}")
                logger.info(f"  File: {error_result['examples']['cli_file']}")
            
            return error_result
        
        logger.info(f"✓ Constructor validation passed")
        logger.info(f"📋 Deploying with args: {final_args}")
        
        return self.foundry_deployer.deploy(
            contract_source_code=contract_source_code,
            rpc_url=rpc_url,
            chain_id=chain_id,
            contract_name=contract_name,
            constructor_args=final_args
        )
    
    def load_constructor_args_from_file(
        self, 
        file_path: str, 
        contract_source_code: str,
        deployer_address: Optional[str] = None
    ) -> List[Any]:
        """
        Load constructor arguments from a JSON file.
        
        Supports two formats:
        1. Array format: ["0x1234...", 1000000, "MyToken"]
        2. Named format: {"owner": "0x1234...", "supply": 1000000, "name": "MyToken"}
        
        Args:
            file_path: Path to JSON file
            contract_source_code: Contract code (for parameter matching)
            deployer_address: Default address for address parameters
            
        Returns:
            List of constructor arguments in correct order
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Constructor args file not found: {file_path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        # If already an array, return as-is
        if isinstance(data, list):
            logger.info(f"Using array format from {file_path}")
            return data
        
        # If dictionary, match to constructor parameters
        if isinstance(data, dict):
            logger.info(f"Using named format from {file_path}")
            
            # Extract constructor parameter names
            parser = ConstructorArgumentParser()
            result = parser.extract_constructor_params(contract_source_code)
            
            if not result:
                raise ValueError("Could not extract constructor parameters from contract")
            
            contract_name, param_types = result
            
            # Build argument list in correct order
            args = []
            for param_type, param_name in param_types:
                if param_name in data:
                    args.append(data[param_name])
                    logger.debug(f"  {param_name}: {data[param_name]}")
                else:
                    # Generate default for missing parameters
                    default_arg = parser.generate_constructor_arg(
                        param_type, param_name, contract_source_code, 
                        deployer_address or "0x0000000000000000000000000000000000000000"
                    )
                    args.append(default_arg)
                    logger.warning(f"  {param_name}: {default_arg} (default, not in JSON)")
            
            return args
        
        raise ValueError(f"Invalid JSON format in {file_path}. Expected array or object.")
    
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