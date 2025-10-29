"""
Storage Service
Real IPFS storage with Pinata provider for HyperKit Agent
"""

import asyncio
import json
import requests
from typing import Dict, Any, Optional
from core.config.manager import config

class HyperKitStorageService:
    """
    Real IPFS storage service using Pinata provider
    Handles decentralized storage for audit reports and AI models
    """
    
    def __init__(self):
        self.config = config
        self.pinata_api_key = self.config.get('PINATA_API_KEY')
        self.pinata_secret_key = self.config.get('PINATA_SECRET_KEY')  # Use PINATA_SECRET_KEY from config manager
        self.ipfs_configured = self._check_ipfs_config()
        
        if self.ipfs_configured:
            self._setup_pinata()
    
    def _check_ipfs_config(self) -> bool:
        """Check if IPFS is properly configured"""
        return (self.pinata_api_key is not None and 
                self.pinata_secret_key is not None and
                self.pinata_api_key.strip() != '' and 
                self.pinata_secret_key.strip() != '' and
                self.pinata_api_key != 'your_pinata_api_key_here' and
                self.pinata_secret_key != 'your_pinata_secret_key_here')
    
    def _setup_pinata(self):
        """Setup Pinata API configuration"""
        self.pinata_url = "https://api.pinata.cloud"
        self.headers = {
            "pinata_api_key": self.pinata_api_key,
            "pinata_secret_api_key": self.pinata_secret_key,
            "Content-Type": "application/json"
        }
        import logging; logging.info(" IPFS Pinata provider configured successfully")
    
    async def store_audit_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store audit report on IPFS using real Pinata API"""
        if not self.ipfs_configured:
            raise RuntimeError(
                "IPFS/Pinata not configured - cannot store audit report\n"
                "  Required: PINATA_API_KEY and PINATA_SECRET_KEY in .env\n"
                "  Get keys: https://app.pinata.cloud/\n"
                "  Fix: Add Pinata credentials to .env file"
            )
        
        try:
            # Prepare data for IPFS storage
            json_data = json.dumps(report_data, indent=2)
            
            # Upload to Pinata
            response = await self._upload_to_pinata(
                data=json_data,
                name=f"audit_report_{report_data.get('timestamp', 'unknown')}.json",
                metadata={
                    "type": "audit_report",
                    "timestamp": report_data.get('timestamp'),
                    "contract_address": report_data.get('contract_address'),
                    "security_score": report_data.get('security_score')
                }
            )
            
            if response.get('success'):
                return {
                    "status": "success",
                    "cid": response['IpfsHash'],
                    "url": f"https://gateway.pinata.cloud/ipfs/{response['IpfsHash']}",
                    "pinata_url": f"https://app.pinata.cloud/pinmanager?search={response['IpfsHash']}",
                    "size": response['PinSize']
                }
            else:
                return {
                    "status": "error",
                    "error": response.get('error', 'Unknown error'),
                    "message": "Failed to store on IPFS"
                }
                
        except Exception as e:
            print(f"❌ IPFS storage failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "IPFS storage failed"
            }
    
    async def _upload_to_pinata(self, data: str, name: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Upload data to Pinata IPFS"""
        try:
            # Prepare the request
            files = {
                'file': (name, data, 'application/json')
            }
            
            # Add metadata
            pinata_metadata = {
                "name": name,
                "keyvalues": metadata
            }
            
            payload = {
                "pinataMetadata": json.dumps(pinata_metadata),
                "pinataOptions": json.dumps({
                    "cidVersion": 1
                })
            }
            
            # Upload to Pinata
            response = requests.post(
                f"{self.pinata_url}/pinning/pinFileToIPFS",
                files=files,
                data=payload,
                headers={
                    "pinata_api_key": self.pinata_api_key,
                    "pinata_secret_api_key": self.pinata_secret_key
                }
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    **response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _mock_storage(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock storage with clear warnings"""
        import logging; logging.warning("  WARNING: Using mock storage - IPFS not configured")
        import logging; logging.warning("  To enable IPFS: Set PINATA_API_KEY and PINATA_SECRET_KEY")
        import logging; logging.warning("  Get API keys from: https://app.pinata.cloud/")
        
        return {
            "status": "mock",
            "cid": "mock_cid_12345",
            "url": "https://mock-ipfs.com/mock_cid_12345",
            "warnings": ["Mock storage - Real IPFS requires Pinata configuration"]
        }
    
    async def retrieve_audit_report(self, cid: str) -> Dict[str, Any]:
        """Retrieve audit report from IPFS using real Pinata API"""
        if not self.ipfs_configured:
            raise RuntimeError(
                "IPFS/Pinata not configured - cannot retrieve audit report\n"
                "  Required: PINATA_API_KEY and PINATA_SECRET_KEY in .env\n"
                "  Get keys: https://app.pinata.cloud/\n"
                "  Fix: Add Pinata credentials to .env file"
            )
        
        try:
            # Retrieve from IPFS via Pinata gateway
            response = requests.get(f"https://gateway.pinata.cloud/ipfs/{cid}")
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "data": data,
                    "cid": cid,
                    "source": "ipfs"
                }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}",
                    "message": "Failed to retrieve from IPFS"
                }
                
        except Exception as e:
            print(f"❌ IPFS retrieval failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "IPFS retrieval failed"
            }
    
    def _mock_retrieval(self, cid: str) -> Dict[str, Any]:
        """Mock retrieval with clear warnings"""
        import logging; logging.warning("  WARNING: Using mock retrieval - IPFS not configured")
        import logging; logging.warning("  To enable IPFS: Set PINATA_API_KEY and PINATA_SECRET_KEY")
        
        return {
            "status": "mock",
            "data": {"mock": "data", "cid": cid},
            "warnings": ["Mock retrieval - Real IPFS requires Pinata configuration"]
        }
    
    async def store_ai_model(self, model_data: Dict[str, Any], model_name: str) -> Dict[str, Any]:
        """Store AI model on IPFS"""
        if not self.ipfs_configured:
            raise RuntimeError(
                "IPFS/Pinata not configured - cannot store AI model\n"
                "  Required: PINATA_API_KEY and PINATA_SECRET_KEY in .env\n"
                "  Get keys: https://app.pinata.cloud/\n"
                "  Fix: Add Pinata credentials to .env file"
            )
        
        try:
            json_data = json.dumps(model_data, indent=2)
            
            response = await self._upload_to_pinata(
                data=json_data,
                name=f"{model_name}.json",
                metadata={
                    "type": "ai_model",
                    "name": model_name,
                    "version": model_data.get('version', '1.0.0')
                }
            )
            
            if response.get('success'):
                return {
                    "status": "success",
                    "cid": response['IpfsHash'],
                    "url": f"https://gateway.pinata.cloud/ipfs/{response['IpfsHash']}",
                    "model_name": model_name
                }
            else:
                return {
                    "status": "error",
                    "error": response.get('error', 'Unknown error')
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "AI model storage failed"
            }
    
    async def list_stored_files(self) -> Dict[str, Any]:
        """List files stored on IPFS via Pinata"""
        if not self.ipfs_configured:
            return {"status": "error", "message": "IPFS not configured"}
        
        try:
            response = requests.get(
                f"{self.pinata_url}/data/pinList",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "files": data.get('rows', []),
                    "count": data.get('count', 0)
                }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}",
                    "message": "Failed to list files"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to list files"
            }
    
    async def delete_file(self, cid: str) -> Dict[str, Any]:
        """Delete file from IPFS via Pinata"""
        if not self.ipfs_configured:
            return {"status": "error", "message": "IPFS not configured"}
        
        try:
            response = requests.delete(
                f"{self.pinata_url}/pinning/unpin/{cid}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": f"File {cid} deleted successfully"
                }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}",
                    "message": "Failed to delete file"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to delete file"
            }
