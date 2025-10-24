"""
Blockchain explorer API integration for contract verification.
"""

import json
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ExplorerAPI:
    """
    Handles contract verification through blockchain explorer APIs.
    Supports Etherscan, BSCScan, and other explorer APIs.
    """
    
    def __init__(self, network: str, config: Dict[str, Any]):
        self.network = network
        self.config = config
        self.explorer_config = self._get_explorer_config()
        
    def _get_explorer_config(self) -> Dict[str, Any]:
        """Get explorer configuration for the network."""
        network_config = self.config.get('networks', {}).get(self.network, {})
        
        # Default explorer configurations
        explorer_configs = {
            'ethereum': {
                'api_url': 'https://api.etherscan.io/api',
                'explorer_url': 'https://etherscan.io',
                'api_key': self.config.get('etherscan_api_key')
            },
            'polygon': {
                'api_url': 'https://api.polygonscan.com/api',
                'explorer_url': 'https://polygonscan.com',
                'api_key': self.config.get('polygonscan_api_key')
            },
            'bsc': {
                'api_url': 'https://api.bscscan.com/api',
                'explorer_url': 'https://bscscan.com',
                'api_key': self.config.get('bscscan_api_key')
            },
            'arbitrum': {
                'api_url': 'https://api.arbiscan.io/api',
                'explorer_url': 'https://arbiscan.io',
                'api_key': self.config.get('arbiscan_api_key')
            },
            'hyperion': {
                'api_url': None,  # No explorer support
                'explorer_url': None,
                'api_key': None
            },
            'metis': {
                'api_url': 'https://api.andromeda-explorer.metis.io/api',
                'explorer_url': 'https://andromeda-explorer.metis.io',
                'api_key': self.config.get('metis_api_key')
            }
        }
        
        return explorer_configs.get(self.network, {
            'api_url': None,
            'explorer_url': None,
            'api_key': None
        })
    
    def has_explorer_support(self) -> bool:
        """Check if the network has explorer API support."""
        return (
            self.explorer_config.get('api_url') is not None and
            self.explorer_config.get('api_key') is not None
        )
    
    async def verify_contract(
        self,
        source_code: str,
        contract_address: str,
        constructor_args: Optional[str] = None,
        contract_name: str = "GeneratedContract"
    ) -> Dict[str, Any]:
        """
        Submit contract for verification on the explorer.
        
        Args:
            source_code: The Solidity source code
            contract_address: The deployed contract address
            constructor_args: Constructor arguments (optional)
            contract_name: Name of the contract
            
        Returns:
            Dict with verification result
        """
        try:
            if not self.has_explorer_support():
                return {
                    "status": "no_support",
                    "error": f"No explorer support for {self.network}"
                }
            
            # Prepare verification data
            verification_data = {
                'apikey': self.explorer_config['api_key'],
                'module': 'contract',
                'action': 'verifysourcecode',
                'contractaddress': contract_address,
                'sourcecode': source_code,
                'codeformat': 'solidity-single-file',
                'contractname': contract_name,
                'compilerversion': 'v0.8.20+commit.a1b79de6',
                'optimizationUsed': 1,
                'runs': 200
            }
            
            if constructor_args:
                verification_data['constructorArguements'] = constructor_args
            
            # Submit verification request
            response = requests.post(
                self.explorer_config['api_url'],
                data=verification_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == '1':
                    # Verification submitted successfully
                    return {
                        "status": "submitted",
                        "guid": result.get('result'),
                        "explorer_url": f"{self.explorer_config['explorer_url']}/address/{contract_address}",
                        "message": "Verification submitted successfully"
                    }
                else:
                    return {
                        "status": "failed",
                        "error": result.get('message', 'Unknown error'),
                        "result": result
                    }
            else:
                return {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Explorer verification failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_verification_status(self, contract_address: str) -> Dict[str, Any]:
        """
        Check the verification status of a contract.
        
        Args:
            contract_address: The contract address to check
            
        Returns:
            Dict with verification status
        """
        try:
            if not self.has_explorer_support():
                return {
                    "status": "no_support",
                    "network": self.network
                }
            
            # Check if contract is verified
            params = {
                'apikey': self.explorer_config['api_key'],
                'module': 'contract',
                'action': 'getsourcecode',
                'address': contract_address
            }
            
            response = requests.get(
                self.explorer_config['api_url'],
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == '1':
                    source_code = result.get('result', [{}])[0].get('SourceCode')
                    
                    if source_code and source_code != '':
                        return {
                            "status": "verified",
                            "contract_address": contract_address,
                            "explorer_url": f"{self.explorer_config['explorer_url']}/address/{contract_address}",
                            "has_source": True
                        }
                    else:
                        return {
                            "status": "not_verified",
                            "contract_address": contract_address,
                            "has_source": False
                        }
                else:
                    return {
                        "status": "error",
                        "error": result.get('message', 'Unknown error')
                    }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Failed to get verification status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
