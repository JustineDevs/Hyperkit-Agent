"""
Web3 interaction service for smart contract testing.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from web3 import Web3
from web3.middleware import geth_poa_middleware

logger = logging.getLogger(__name__)

class Web3Interaction:
    """
    Web3 interaction service for contract testing and validation.
    Handles connection to blockchain networks and contract interactions.
    """
    
    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url
        self.web3 = self._initialize_web3()
        
    def _initialize_web3(self) -> Web3:
        """Initialize Web3 connection with proper middleware."""
        try:
            web3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
            # Add PoA middleware for networks like BSC, Polygon
            web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            if web3.is_connected():
                logger.info(f"Web3 connected to {self.rpc_url}")
                return web3
            else:
                logger.error(f"Failed to connect to {self.rpc_url}")
                raise ConnectionError(f"Cannot connect to {self.rpc_url}")
                
        except Exception as e:
            logger.error(f"Web3 initialization failed: {e}")
            raise
    
    async def is_contract_deployed(self, contract_address: str) -> bool:
        """
        Check if a contract is deployed at the given address.
        
        Args:
            contract_address: The contract address to check
            
        Returns:
            True if contract is deployed, False otherwise
        """
        try:
            code = self.web3.eth.get_code(contract_address)
            return len(code) > 0
        except Exception as e:
            logger.error(f"Failed to check contract deployment: {e}")
            return False
    
    async def get_contract_code(self, contract_address: str) -> str:
        """
        Get the bytecode of a deployed contract.
        
        Args:
            contract_address: The contract address
            
        Returns:
            Contract bytecode as hex string
        """
        try:
            code = self.web3.eth.get_code(contract_address)
            return code.hex()
        except Exception as e:
            logger.error(f"Failed to get contract code: {e}")
            return ""
    
    async def get_contract_balance(self, contract_address: str) -> int:
        """
        Get the ETH balance of a contract.
        
        Args:
            contract_address: The contract address
            
        Returns:
            Balance in wei
        """
        try:
            balance = self.web3.eth.get_balance(contract_address)
            return balance
        except Exception as e:
            logger.error(f"Failed to get contract balance: {e}")
            return 0
    
    async def call_contract_function(
        self,
        contract_address: str,
        function_name: str,
        parameters: List[Any] = None,
        abi: List[Dict] = None
    ) -> Any:
        """
        Call a contract function (read-only).
        
        Args:
            contract_address: The contract address
            function_name: Name of the function to call
            parameters: Function parameters
            abi: Contract ABI (optional)
            
        Returns:
            Function call result
        """
        try:
            if not abi:
                # Try to find the function in a minimal ABI
                abi = self._get_minimal_abi_for_function(function_name)
            
            if not abi:
                raise ValueError(f"No ABI available for function {function_name}")
            
            contract = self.web3.eth.contract(
                address=contract_address,
                abi=abi
            )
            
            # Call the function
            if parameters:
                result = getattr(contract.functions, function_name)(*parameters).call()
            else:
                result = getattr(contract.functions, function_name)().call()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to call function {function_name}: {e}")
            raise
    
    def _get_minimal_abi_for_function(self, function_name: str) -> List[Dict]:
        """
        Get minimal ABI for common functions.
        
        Args:
            function_name: Name of the function
            
        Returns:
            Minimal ABI for the function
        """
        # Common function ABIs
        common_abis = {
            "balanceOf": [
                {
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                }
            ],
            "totalSupply": [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "totalSupply",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "type": "function"
                }
            ],
            "name": [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "name",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function"
                }
            ],
            "symbol": [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "symbol",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function"
                }
            ],
            "decimals": [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "type": "function"
                }
            ]
        }
        
        return common_abis.get(function_name, [])
    
    async def get_latest_block(self) -> Dict[str, Any]:
        """
        Get the latest block information.
        
        Returns:
            Latest block data
        """
        try:
            block = self.web3.eth.get_block('latest')
            return {
                "block_number": block.number,
                "block_hash": block.hash.hex(),
                "timestamp": block.timestamp,
                "gas_limit": block.gasLimit,
                "gas_used": block.gasUsed
            }
        except Exception as e:
            logger.error(f"Failed to get latest block: {e}")
            return {}
    
    async def estimate_gas(
        self,
        contract_address: str,
        function_name: str,
        parameters: List[Any] = None,
        abi: List[Dict] = None
    ) -> int:
        """
        Estimate gas for a contract function call.
        
        Args:
            contract_address: The contract address
            function_name: Name of the function
            parameters: Function parameters
            abi: Contract ABI
            
        Returns:
            Estimated gas cost
        """
        try:
            if not abi:
                abi = self._get_minimal_abi_for_function(function_name)
            
            if not abi:
                return 21000  # Default gas limit
            
            contract = self.web3.eth.contract(
                address=contract_address,
                abi=abi
            )
            
            if parameters:
                gas_estimate = getattr(contract.functions, function_name)(*parameters).estimate_gas()
            else:
                gas_estimate = getattr(contract.functions, function_name)().estimate_gas()
            
            return gas_estimate
            
        except Exception as e:
            logger.error(f"Failed to estimate gas for {function_name}: {e}")
            return 21000  # Default gas limit
