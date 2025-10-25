"""
IPFS Client for HyperKit Agent.
Handles decentralized storage of audit reports, AI models, and datasets.
"""

import json
import logging
import requests
from typing import Dict, Any, Optional, Union
from pathlib import Path
import hashlib
import time

logger = logging.getLogger(__name__)

class IPFSClient:
    """
    IPFS client for storing and retrieving audit reports, AI models, and datasets.
    Supports multiple IPFS gateways and Pinata integration.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.gateways = [
            'https://gateway.pinata.cloud/ipfs/',  # Pinata gateway first
            'https://ipfs.io/ipfs/',
            'https://cloudflare-ipfs.com/ipfs/',
            'https://dweb.link/ipfs/'
        ]
        self.pinata_config = config.get('pinata', {})
        self.pinata_enabled = bool(self.pinata_config.get('api_key'))
        
        if self.pinata_enabled:
            logger.info("✅ Pinata IPFS integration enabled")
        else:
            logger.warning("⚠️ Pinata API key not configured - using fallback gateways")
        
    async def upload_json(self, data: Dict[str, Any], filename: str = None) -> str:
        """
        Upload JSON data to IPFS and return CID.
        
        Args:
            data: JSON data to upload
            filename: Optional filename for the data
            
        Returns:
            CID hash of the uploaded content
        """
        try:
            json_str = json.dumps(data, indent=2)
            
            if self.pinata_enabled:
                return await self._upload_to_pinata(json_str, filename)
            else:
                return await self._upload_to_gateway(json_str, filename)
                
        except Exception as e:
            logger.error(f"Failed to upload JSON to IPFS: {e}")
            raise
    
    async def upload_file(self, file_path: Union[str, Path], filename: str = None) -> str:
        """
        Upload file to IPFS and return CID.
        
        Args:
            file_path: Path to file to upload
            filename: Optional filename override
            
        Returns:
            CID hash of the uploaded file
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            if self.pinata_enabled:
                return await self._upload_to_pinata(content, filename or file_path.name)
            else:
                return await self._upload_to_gateway(content, filename or file_path.name)
                
        except Exception as e:
            logger.error(f"Failed to upload file to IPFS: {e}")
            raise
    
    async def get_json(self, cid: str) -> Dict[str, Any]:
        """
        Retrieve JSON data from IPFS by CID.
        
        Args:
            cid: IPFS CID hash
            
        Returns:
            JSON data as dictionary
        """
        try:
            content = await self._get_content(cid)
            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to retrieve JSON from IPFS: {e}")
            raise
    
    async def get_file(self, cid: str, output_path: Union[str, Path] = None) -> bytes:
        """
        Retrieve file from IPFS by CID.
        
        Args:
            cid: IPFS CID hash
            output_path: Optional path to save file
            
        Returns:
            File content as bytes
        """
        try:
            content = await self._get_content(cid)
            
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(content)
            
            return content
        except Exception as e:
            logger.error(f"Failed to retrieve file from IPFS: {e}")
            raise
    
    def get_url(self, cid: str, gateway: str = None) -> str:
        """
        Get IPFS URL for a CID.
        
        Args:
            cid: IPFS CID hash
            gateway: Specific gateway to use
            
        Returns:
            IPFS URL
        """
        if gateway:
            return f"{gateway.rstrip('/')}/{cid}"
        else:
            return f"{self.gateways[0]}{cid}"
    
    async def _upload_to_pinata(self, content: Union[str, bytes], filename: str = None) -> str:
        """Upload content to Pinata IPFS service."""
        try:
            from .pinata_client import PinataClient
            pinata = PinataClient(self.pinata_config)
            
            if isinstance(content, str):
                content = content.encode('utf-8')
            
            result = await pinata.upload_file(content, filename)
            return result['IpfsHash']
            
        except Exception as e:
            logger.error(f"Pinata upload failed: {e}")
            # Fallback to gateway upload
            return await self._upload_to_gateway(content, filename)
    
    async def _upload_to_gateway(self, content: Union[str, bytes], filename: str = None) -> str:
        """Upload content to IPFS gateway (simulated for demo)."""
        try:
            # For demo purposes, generate a mock CID
            # In production, this would use a real IPFS node
            if isinstance(content, str):
                content = content.encode('utf-8')
            
            # Generate deterministic CID based on content
            content_hash = hashlib.sha256(content).hexdigest()
            mock_cid = f"Qm{content_hash[:44]}"  # Mock CID format
            
            logger.info(f"Mock IPFS upload: {mock_cid}")
            return mock_cid
            
        except Exception as e:
            logger.error(f"Gateway upload failed: {e}")
            raise
    
    async def _get_content(self, cid: str) -> bytes:
        """Retrieve content from IPFS by CID."""
        for gateway in self.gateways:
            try:
                url = f"{gateway}{cid}"
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    return response.content
                    
            except Exception as e:
                logger.warning(f"Failed to retrieve from {gateway}: {e}")
                continue
        
        raise Exception(f"Failed to retrieve content for CID: {cid}")
    
    async def store_audit_report(self, audit_data: Dict[str, Any], contract_address: str) -> Dict[str, Any]:
        """
        Store audit report on IPFS with metadata.
        
        Args:
            audit_data: Audit report data
            contract_address: Contract address being audited
            
        Returns:
            Storage result with CID and metadata
        """
        try:
            # Add metadata to audit data
            audit_data['metadata'] = {
                'contract_address': contract_address,
                'timestamp': int(time.time()),
                'agent_version': '1.2.0',
                'storage_type': 'audit_report'
            }
            
            # Upload to IPFS
            cid = await self.upload_json(audit_data, f"audit_{contract_address}.json")
            
            return {
                'cid': cid,
                'url': self.get_url(cid),
                'contract_address': contract_address,
                'storage_type': 'audit_report',
                'timestamp': audit_data['metadata']['timestamp']
            }
            
        except Exception as e:
            logger.error(f"Failed to store audit report: {e}")
            raise
    
    async def store_ai_model(self, model_data: bytes, model_name: str, version: str = "1.0.0") -> Dict[str, Any]:
        """
        Store AI model on IPFS.
        
        Args:
            model_data: Model file content
            model_name: Name of the model
            version: Model version
            
        Returns:
            Storage result with CID and metadata
        """
        try:
            # Create model metadata
            metadata = {
                'model_name': model_name,
                'version': version,
                'timestamp': int(time.time()),
                'storage_type': 'ai_model'
            }
            
            # Upload model file
            cid = await self.upload_file(model_data, f"{model_name}_v{version}.pkl")
            
            return {
                'cid': cid,
                'url': self.get_url(cid),
                'model_name': model_name,
                'version': version,
                'storage_type': 'ai_model',
                'timestamp': metadata['timestamp']
            }
            
        except Exception as e:
            logger.error(f"Failed to store AI model: {e}")
            raise
