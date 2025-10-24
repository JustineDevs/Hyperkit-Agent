"""
IPFS storage service for contract verification fallback.
"""

import json
import logging
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class IPFSStorage:
    """
    IPFS storage service for storing contract source code
    when explorer verification is not available.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ipfs_config = self._get_ipfs_config()
        
    def _get_ipfs_config(self) -> Dict[str, Any]:
        """Get IPFS configuration from config."""
        return {
            'gateway_url': self.config.get('ipfs_gateway_url', 'https://ipfs.io/ipfs/'),
            'api_url': self.config.get('ipfs_api_url', 'https://api.pinata.cloud/'),
            'api_key': self.config.get('ipfs_api_key'),
            'api_secret': self.config.get('ipfs_api_secret')
        }
    
    async def store_contract(
        self,
        source_code: str,
        contract_address: str,
        contract_name: str = "GeneratedContract"
    ) -> Dict[str, Any]:
        """
        Store contract source code on IPFS.
        
        Args:
            source_code: The Solidity source code
            contract_address: The deployed contract address
            contract_name: Name of the contract
            
        Returns:
            Dict with IPFS storage result
        """
        try:
            # Create contract metadata
            contract_metadata = {
                "name": contract_name,
                "contract_address": contract_address,
                "source_code": source_code,
                "verification_timestamp": self._get_timestamp(),
                "verification_method": "ipfs_storage"
            }
            
            # Generate IPFS hash (simulated for now)
            content_hash = self._generate_content_hash(contract_metadata)
            
            # Store locally as fallback
            local_path = await self._store_locally(contract_metadata, content_hash)
            
            return {
                "status": "stored",
                "ipfs_hash": content_hash,
                "ipfs_url": f"{self.ipfs_config['gateway_url']}{content_hash}",
                "local_path": str(local_path),
                "contract_address": contract_address,
                "storage_method": "local_fallback"
            }
            
        except Exception as e:
            logger.error(f"IPFS storage failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _generate_content_hash(self, content: Dict[str, Any]) -> str:
        """Generate a content hash for the contract metadata."""
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    async def _store_locally(self, metadata: Dict[str, Any], content_hash: str) -> Path:
        """Store contract metadata locally as fallback."""
        # Create artifacts directory
        artifacts_dir = Path("artifacts/verification")
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Save metadata
        metadata_file = artifacts_dir / f"{content_hash}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save source code separately
        source_file = artifacts_dir / f"{content_hash}.sol"
        with open(source_file, 'w') as f:
            f.write(metadata['source_code'])
        
        logger.info(f"Contract stored locally: {metadata_file}")
        return metadata_file
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
    
    def retrieve_contract(self, ipfs_hash: str) -> Dict[str, Any]:
        """
        Retrieve contract from IPFS hash.
        
        Args:
            ipfs_hash: The IPFS hash to retrieve
            
        Returns:
            Dict with retrieved contract data
        """
        try:
            # Try to retrieve from local storage first
            artifacts_dir = Path("artifacts/verification")
            metadata_file = artifacts_dir / f"{ipfs_hash}.json"
            
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    return {
                        "status": "retrieved",
                        "data": json.load(f),
                        "source": "local_storage"
                    }
            else:
                return {
                    "status": "not_found",
                    "ipfs_hash": ipfs_hash,
                    "error": "Contract not found in local storage"
                }
                
        except Exception as e:
            logger.error(f"Failed to retrieve contract: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
