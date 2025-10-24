"""
Main contract verification logic for blockchain explorers.
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .explorer_api import ExplorerAPI
from .ipfs_storage import IPFSStorage

logger = logging.getLogger(__name__)

class ContractVerifier:
    """
    Main contract verification service that handles verification
    on blockchain explorers or IPFS as fallback.
    """
    
    def __init__(self, network: str, config: Dict[str, Any]):
        self.network = network
        self.config = config
        self.explorer_api = ExplorerAPI(network, config)
        self.ipfs_storage = IPFSStorage(config)
        
    async def verify_contract(
        self, 
        source_code: str, 
        contract_address: str,
        constructor_args: Optional[str] = None,
        contract_name: str = "GeneratedContract"
    ) -> Dict[str, Any]:
        """
        Verify a smart contract on the blockchain explorer.
        
        Args:
            source_code: The Solidity source code
            contract_address: The deployed contract address
            constructor_args: Constructor arguments (optional)
            contract_name: Name of the contract
            
        Returns:
            Dict with verification status and details
        """
        try:
            logger.info(f"Starting verification for {contract_address} on {self.network}")
            
            # Check if network has explorer support
            if self.explorer_api.has_explorer_support():
                logger.info("Network has explorer support, attempting verification")
                result = await self.explorer_api.verify_contract(
                    source_code=source_code,
                    contract_address=contract_address,
                    constructor_args=constructor_args,
                    contract_name=contract_name
                )
                
                if result.get("status") == "success":
                    return {
                        "status": "verified",
                        "network": self.network,
                        "contract_address": contract_address,
                        "explorer_url": result.get("explorer_url"),
                        "verification_method": "explorer_api"
                    }
                else:
                    logger.warning(f"Explorer verification failed: {result.get('error')}")
            
            # Fallback to IPFS storage
            logger.info("Using IPFS fallback for verification")
            ipfs_result = await self.ipfs_storage.store_contract(
                source_code=source_code,
                contract_address=contract_address,
                contract_name=contract_name
            )
            
            return {
                "status": "stored_on_ipfs",
                "network": self.network,
                "contract_address": contract_address,
                "ipfs_hash": ipfs_result.get("ipfs_hash"),
                "ipfs_url": ipfs_result.get("ipfs_url"),
                "verification_method": "ipfs_storage"
            }
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {
                "status": "failed",
                "network": self.network,
                "contract_address": contract_address,
                "error": str(e),
                "verification_method": "none"
            }
    
    def get_verification_status(self, contract_address: str) -> Dict[str, Any]:
        """
        Check the current verification status of a contract.
        
        Args:
            contract_address: The contract address to check
            
        Returns:
            Dict with current verification status
        """
        try:
            if self.explorer_api.has_explorer_support():
                return self.explorer_api.get_verification_status(contract_address)
            else:
                return {
                    "status": "no_explorer_support",
                    "network": self.network,
                    "contract_address": contract_address
                }
        except Exception as e:
            logger.error(f"Failed to get verification status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
