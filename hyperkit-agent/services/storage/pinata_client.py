"""
Pinata IPFS client for HyperKit Agent.
Handles professional IPFS storage with Pinata service.
"""

import json
import logging
import requests
from typing import Dict, Any, Optional, Union
import time

logger = logging.getLogger(__name__)

class PinataClient:
    """
    Pinata IPFS client for professional IPFS storage.
    Provides reliable, fast IPFS storage with metadata support.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        self.base_url = 'https://api.pinata.cloud'
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Pinata API key and secret are required")
    
    async def upload_file(self, content: bytes, filename: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Upload file to Pinata IPFS.
        
        Args:
            content: File content as bytes
            filename: Name of the file
            metadata: Optional metadata
            
        Returns:
            Pinata response with IPFS hash
        """
        try:
            headers = {
                'pinata_api_key': self.api_key,
                'pinata_secret_api_key': self.api_secret
            }
            
            # Prepare metadata
            pinata_metadata = {
                'name': filename,
                'keyvalues': metadata or {}
            }
            
            # Prepare options
            pinata_options = {
                'cidVersion': 1
            }
            
            # Create form data
            files = {
                'file': (filename, content)
            }
            
            data = {
                'pinataMetadata': json.dumps(pinata_metadata),
                'pinataOptions': json.dumps(pinata_options)
            }
            
            # Upload to Pinata
            response = requests.post(
                f"{self.base_url}/pinning/pinFileToIPFS",
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Successfully uploaded to Pinata: {result['IpfsHash']}")
                return result
            else:
                raise Exception(f"Pinata upload failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Pinata upload error: {e}")
            raise
    
    async def upload_json(self, data: Dict[str, Any], filename: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Upload JSON data to Pinata IPFS.
        
        Args:
            data: JSON data to upload
            filename: Name of the file
            metadata: Optional metadata
            
        Returns:
            Pinata response with IPFS hash
        """
        try:
            json_content = json.dumps(data, indent=2).encode('utf-8')
            return await self.upload_file(json_content, filename, metadata)
            
        except Exception as e:
            logger.error(f"Pinata JSON upload error: {e}")
            raise
    
    async def get_file_info(self, ipfs_hash: str) -> Dict[str, Any]:
        """
        Get file information from Pinata.
        
        Args:
            ipfs_hash: IPFS hash of the file
            
        Returns:
            File information
        """
        try:
            headers = {
                'pinata_api_key': self.api_key,
                'pinata_secret_api_key': self.api_secret
            }
            
            response = requests.get(
                f"{self.base_url}/data/pinList?hashContains={ipfs_hash}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to get file info: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Pinata file info error: {e}")
            raise
    
    async def delete_file(self, ipfs_hash: str) -> bool:
        """
        Delete file from Pinata.
        
        Args:
            ipfs_hash: IPFS hash of the file to delete
            
        Returns:
            True if successful
        """
        try:
            headers = {
                'pinata_api_key': self.api_key,
                'pinata_secret_api_key': self.api_secret
            }
            
            response = requests.delete(
                f"{self.base_url}/pinning/unpin/{ipfs_hash}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully deleted from Pinata: {ipfs_hash}")
                return True
            else:
                logger.warning(f"Failed to delete from Pinata: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Pinata delete error: {e}")
            return False
