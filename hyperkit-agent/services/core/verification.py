"""
Verification Service
Real contract verification on block explorers for HyperKit Agent
"""

import asyncio
import json
import requests
from typing import Dict, Any, Optional, List
from core.config.manager import config

class HyperKitVerificationService:
    """
    Real contract verification service
    Handles on-chain verification for Hyperion and other networks
    """
    
    def __init__(self):
        self.config = config
        self.network_configs = {
            'hyperion': {
                'explorer_url': 'https://explorer.hyperion.network',
                'api_url': 'https://explorer.hyperion.network/api',
                'verification_endpoint': '/api/contracts/verify'
            },
            'ethereum': {
                'explorer_url': 'https://etherscan.io',
                'api_url': 'https://api.etherscan.io/api',
                'verification_endpoint': '/api'
            },
            'polygon': {
                'explorer_url': 'https://polygonscan.com',
                'api_url': 'https://api.polygonscan.com/api',
                'verification_endpoint': '/api'
            }
        }
    
    async def verify_contract(self, address: str, source_code: str, network: str = 'hyperion', 
                            constructor_args: List[str] = None, contract_name: str = None) -> Dict[str, Any]:
        """Verify contract on block explorer using real API"""
        try:
            if network not in self.network_configs:
                return {
                    "status": "error",
                    "error": f"Unsupported network: {network}",
                    "supported_networks": list(self.network_configs.keys())
                }
            
            network_config = self.network_configs[network]
            
            # Prepare verification request
            verification_data = {
                "address": address,
                "source_code": source_code,
                "contract_name": contract_name or "Contract",
                "constructor_args": constructor_args or [],
                "network": network
            }
            
            # Submit verification request
            response = await self._submit_verification(verification_data, network_config)
            
            if response.get('success'):
                return {
                    "status": "success",
                    "address": address,
                    "network": network,
                    "explorer_url": f"{network_config['explorer_url']}/address/{address}",
                    "verification_id": response.get('verification_id'),
                    "message": "Contract verification submitted successfully"
                }
            else:
                return {
                    "status": "error",
                    "error": response.get('error', 'Unknown error'),
                    "message": "Contract verification failed"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Verification request failed"
            }
    
    async def _submit_verification(self, data: Dict[str, Any], network_config: Dict[str, str]) -> Dict[str, Any]:
        """Submit verification request to block explorer"""
        try:
            # For Hyperion testnet (simplified implementation)
            if 'hyperion' in network_config['explorer_url']:
                return await self._submit_hyperion_verification(data, network_config)
            else:
                return await self._submit_etherscan_verification(data, network_config)
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _submit_hyperion_verification(self, data: Dict[str, Any], network_config: Dict[str, str]) -> Dict[str, Any]:
        """Submit verification to Hyperion explorer"""
        try:
            # Hyperion-specific verification logic
            verification_payload = {
                "address": data['address'],
                "source_code": data['source_code'],
                "contract_name": data['contract_name'],
                "constructor_args": data['constructor_args']
            }
            
            # Submit to Hyperion API
            response = requests.post(
                f"{network_config['api_url']}{network_config['verification_endpoint']}",
                json=verification_payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "verification_id": result.get('id'),
                    "message": "Verification submitted to Hyperion"
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
    
    async def _submit_etherscan_verification(self, data: Dict[str, Any], network_config: Dict[str, str]) -> Dict[str, Any]:
        """Submit verification to Etherscan-compatible explorer"""
        try:
            # Etherscan-compatible verification
            api_key = self.config.get('ETHERSCAN_API_KEY')
            if not api_key:
                return {
                    "success": False,
                    "error": "Etherscan API key not configured"
                }
            
            verification_payload = {
                "apikey": api_key,
                "module": "contract",
                "action": "verifysourcecode",
                "address": data['address'],
                "sourceCode": data['source_code'],
                "contractname": data['contract_name'],
                "constructorArguements": ''.join(data['constructor_args']) if data['constructor_args'] else ''
            }
            
            response = requests.post(
                network_config['api_url'],
                data=verification_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == '1':
                    return {
                        "success": True,
                        "verification_id": result.get('result'),
                        "message": "Verification submitted successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get('message', 'Verification failed')
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
    
    async def check_verification_status(self, address: str, network: str = 'hyperion') -> Dict[str, Any]:
        """Check verification status of contract"""
        try:
            if network not in self.network_configs:
                return {
                    "status": "error",
                    "error": f"Unsupported network: {network}"
                }
            
            network_config = self.network_configs[network]
            
            # Check verification status
            response = requests.get(
                f"{network_config['api_url']}/contracts/{address}",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "address": address,
                    "verified": data.get('verified', False),
                    "verification_status": data.get('verification_status', 'unknown'),
                    "explorer_url": f"{network_config['explorer_url']}/address/{address}"
                }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}",
                    "message": "Failed to check verification status"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to check verification status"
            }
    
    async def get_verified_contracts(self, network: str = 'hyperion', limit: int = 10) -> Dict[str, Any]:
        """Get list of verified contracts"""
        try:
            if network not in self.network_configs:
                return {
                    "status": "error",
                    "error": f"Unsupported network: {network}"
                }
            
            network_config = self.network_configs[network]
            
            # Get verified contracts
            response = requests.get(
                f"{network_config['api_url']}/contracts?verified=true&limit={limit}",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "contracts": data.get('contracts', []),
                    "count": len(data.get('contracts', [])),
                    "network": network
                }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}",
                    "message": "Failed to get verified contracts"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to get verified contracts"
            }
    
    async def get_contract_source(self, address: str, network: str = 'hyperion') -> Dict[str, Any]:
        """Get verified contract source code"""
        try:
            if network not in self.network_configs:
                return {
                    "status": "error",
                    "error": f"Unsupported network: {network}"
                }
            
            network_config = self.network_configs[network]
            
            # Get contract source
            response = requests.get(
                f"{network_config['api_url']}/contracts/{address}/source",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "address": address,
                    "source_code": data.get('source_code', ''),
                    "abi": data.get('abi', []),
                    "contract_name": data.get('contract_name', ''),
                    "verified": data.get('verified', False)
                }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}",
                    "message": "Failed to get contract source"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to get contract source"
            }
