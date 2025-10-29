"""
Blockchain explorer API integration for contract verification.
"""

import json
import logging
import requests
import subprocess
import tempfile
import os
from typing import Dict, Any, Optional
from pathlib import Path

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
                'api_url': 'https://hyperion-testnet-explorer.metisdevops.link/api',
                'explorer_url': 'https://hyperion-testnet-explorer.metisdevops.link',
                'api_key': None,  # Blockscout doesn't require API key
                'verifier_type': 'blockscout'
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
            (self.explorer_config.get('api_key') is not None or 
             self.explorer_config.get('verifier_type') == 'blockscout')
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
            
            # Use Foundry verification for Blockscout (Hyperion)
            if self.explorer_config.get('verifier_type') == 'blockscout':
                return await self._verify_with_foundry(
                    source_code, contract_address, constructor_args, contract_name
                )
            
            # Use traditional API for other explorers
            return await self._verify_with_api(
                source_code, contract_address, constructor_args, contract_name
            )
                
        except Exception as e:
            logger.error(f"Explorer verification failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _verify_with_foundry(
        self,
        source_code: str,
        contract_address: str,
        constructor_args: Optional[str] = None,
        contract_name: str = "GeneratedContract"
    ) -> Dict[str, Any]:
        """Verify contract using Blockscout API directly (Foundry-compatible)."""
        try:
            # Use Blockscout API directly for verification
            verification_data = {
                'addressHash': contract_address,
                'name': contract_name,
                'compilerVersion': '0.8.20',
                'optimization': True,
                'contractSourceCode': source_code,
                'constructorArguments': constructor_args or '',
                'autodetectConstructorArguments': False
            }
            
            logger.info(f"Submitting verification to Blockscout API: {self.explorer_config['api_url']}")
            
            # Submit verification request to Blockscout
            # Blockscout uses /api endpoint but different endpoint path for verification
            api_base = self.explorer_config['api_url'].rstrip('/api')
            if not api_base:
                api_base = self.explorer_config.get('explorer_url', '')
            
            # Try Blockscout verification endpoint
            verify_url = f"{api_base}/api/v2/smart-contracts/{contract_address}/verifying-via-flattened-code"
            
            response = requests.post(
                verify_url,
                json={
                    'contractSourceCode': source_code,
                    'compilerVersion': 'v0.8.20+commit.a1b79de6',
                    'optimization': True,
                    'constructorArguments': constructor_args or ''
                },
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            # If that fails, try alternative endpoint
            if response.status_code not in [200, 201, 202]:
                logger.warning(f"Primary verification endpoint failed, trying alternative...")
                verify_url = f"{api_base}/api?module=contract&action=verifysourcecode"
                
                verification_form = {
                    'addressHash': contract_address,
                    'name': contract_name,
                    'compilerVersion': 'v0.8.20',
                    'optimization': 'true',
                    'contractSourceCode': source_code,
                    'constructorArguments': constructor_args or '',
                    'autodetectConstructorArguments': 'false'
                }
                
                response = requests.post(
                    verify_url,
                    data=verification_form,
                    timeout=60
                )
            
            if response.status_code in [200, 201, 202]:
                try:
                    result = response.json() if response.text else {}
                except:
                    result = {}
                
                # Check various success patterns
                if (response.status_code == 201 or 
                    result.get('status') == 'ok' or 
                    result.get('success') == True or
                    'submitted' in response.text.lower() or
                    'queued' in response.text.lower()):
                    return {
                        "status": "submitted",
                        "explorer_url": f"{self.explorer_config['explorer_url']}/address/{contract_address}",
                        "message": "Verification submitted successfully to Blockscout. Check explorer for status.",
                        "verification_method": "blockscout_api",
                        "result": result if result else {"message": "Verification queued"}
                    }
                elif result.get('status') == '0' or result.get('error'):
                    return {
                        "status": "failed",
                        "error": result.get('message') or result.get('error') or 'Verification failed',
                        "verification_method": "blockscout_api",
                        "result": result
                    }
                else:
                    # Assume success if we got 200/201/202
                    return {
                        "status": "submitted",
                        "explorer_url": f"{self.explorer_config['explorer_url']}/address/{contract_address}",
                        "message": "Verification submitted to Blockscout",
                        "verification_method": "blockscout_api",
                        "result": result
                    }
            else:
                error_text = response.text[:500] if response.text else "No response"
                return {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {error_text}",
                    "verification_method": "blockscout_api",
                    "explorer_url": f"{self.explorer_config['explorer_url']}/address/{contract_address}"
                }
                    
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "verification_method": "blockscout_api"
            }
    
    async def _verify_with_api(
        self,
        source_code: str,
        contract_address: str,
        constructor_args: Optional[str] = None,
        contract_name: str = "GeneratedContract"
    ) -> Dict[str, Any]:
        """Verify contract using traditional explorer API."""
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
                    "message": "Verification submitted successfully",
                    "verification_method": "explorer_api"
                }
            else:
                return {
                    "status": "failed",
                    "error": result.get('message', 'Unknown error'),
                    "result": result,
                    "verification_method": "explorer_api"
                }
        else:
            return {
                "status": "failed",
                "error": f"HTTP {response.status_code}: {response.text}",
                "verification_method": "explorer_api"
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
            
            # Handle Blockscout (Hyperion) differently
            if self.explorer_config.get('verifier_type') == 'blockscout':
                return self._get_blockscout_verification_status(contract_address)
            
            # Check if contract is verified (Etherscan-compatible APIs)
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
    
    def _get_blockscout_verification_status(self, contract_address: str) -> Dict[str, Any]:
        """Get verification status from Blockscout API (Hyperion)."""
        try:
            # Blockscout API endpoint for contract info
            api_url = self.explorer_config.get('api_url', '').rstrip('/api')
            if not api_url:
                api_url = self.explorer_config.get('explorer_url', '')
            
            # Get contract info from Blockscout API
            response = requests.get(
                f"{api_url}/api",
                params={
                    'module': 'contract',
                    'action': 'getsourcecode',
                    'address': contract_address
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == '1' and result.get('result'):
                    contract_info = result['result'][0] if isinstance(result['result'], list) else result['result']
                    source_code = contract_info.get('SourceCode', '')
                    
                    if source_code and source_code != '' and source_code != '{{  }}':
                        return {
                            "status": "verified",
                            "contract_address": contract_address,
                            "explorer_url": f"{self.explorer_config['explorer_url']}/address/{contract_address}",
                            "has_source": True,
                            "contract_name": contract_info.get('ContractName', 'Unknown')
                        }
                    else:
                        return {
                            "status": "not_verified",
                            "contract_address": contract_address,
                            "explorer_url": f"{self.explorer_config['explorer_url']}/address/{contract_address}",
                            "has_source": False
                        }
                else:
                    return {
                        "status": "not_verified",
                        "contract_address": contract_address,
                        "explorer_url": f"{self.explorer_config['explorer_url']}/address/{contract_address}",
                        "error": result.get('message', 'Contract not found or not verified')
                    }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                }
                
        except Exception as e:
            logger.error(f"Blockscout verification status check failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_deployment_info(self, contract_address: str) -> Dict[str, Any]:
        """
        Get deployment information for a contract (tx hash, block number, etc.).
        
        Args:
            contract_address: The contract address to check
            
        Returns:
            Dict with deployment information
        """
        try:
            if not self.has_explorer_support():
                return {
                    "status": "no_support",
                    "network": self.network
                }
            
            # Handle Blockscout (Hyperion) differently
            if self.explorer_config.get('verifier_type') == 'blockscout':
                return self._get_blockscout_deployment_info(contract_address)
            
            # For Etherscan-compatible APIs, use contract creation transaction
            params = {
                'apikey': self.explorer_config['api_key'],
                'module': 'contract',
                'action': 'getcontractcreation',
                'contractaddresses': contract_address
            }
            
            response = requests.get(
                self.explorer_config['api_url'],
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == '1' and result.get('result'):
                    deployment = result['result'][0]
                    return {
                        "status": "found",
                        "contract_address": contract_address,
                        "tx_hash": deployment.get('txHash', ''),
                        "block_number": deployment.get('blockNumber', ''),
                        "creator": deployment.get('contractCreator', ''),
                        "explorer_url": f"{self.explorer_config['explorer_url']}/address/{contract_address}"
                    }
                else:
                    return {
                        "status": "not_found",
                        "contract_address": contract_address,
                        "error": "Deployment information not available"
                    }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Failed to get deployment info: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _get_blockscout_deployment_info(self, contract_address: str) -> Dict[str, Any]:
        """Get deployment information from Blockscout API (Hyperion)."""
        try:
            api_url = self.explorer_config.get('api_url', '').rstrip('/api')
            if not api_url:
                api_url = self.explorer_config.get('explorer_url', '')
            
            # Get transaction info for contract creation
            response = requests.get(
                f"{api_url}/api",
                params={
                    'module': 'transaction',
                    'action': 'gettxinfo',
                    'txhash': contract_address  # Blockscout can find by contract address
                },
                timeout=10
            )
            
            # Alternative: Get contract info which includes creation tx
            contract_response = requests.get(
                f"{api_url}/api",
                params={
                    'module': 'contract',
                    'action': 'getsourcecode',
                    'address': contract_address
                },
                timeout=10
            )
            
            if contract_response.status_code == 200:
                contract_result = contract_response.json()
                
                if contract_result.get('status') == '1' and contract_result.get('result'):
                    contract_info = contract_result['result'][0] if isinstance(contract_result['result'], list) else contract_result['result']
                    
                    # Get transaction hash from contract creation
                    tx_response = requests.get(
                        f"{api_url}/api",
                        params={
                            'module': 'account',
                            'action': 'txlist',
                            'address': contract_address,
                            'startblock': 0,
                            'endblock': 99999999,
                            'page': 1,
                            'offset': 1,
                            'sort': 'asc'
                        },
                        timeout=10
                    )
                    
                    tx_hash = None
                    block_number = None
                    
                    if tx_response.status_code == 200:
                        tx_result = tx_response.json()
                        if tx_result.get('status') == '1' and tx_result.get('result'):
                            txs = tx_result['result']
                            if txs:
                                tx_hash = txs[0].get('hash', '')
                                block_number = txs[0].get('blockNumber', '')
                    
                    return {
                        "status": "found",
                        "contract_address": contract_address,
                        "tx_hash": tx_hash or contract_info.get('TxHash', ''),
                        "block_number": block_number or contract_info.get('BlockNumber', ''),
                        "creator": contract_info.get('Creator', ''),
                        "explorer_url": f"{self.explorer_config['explorer_url']}/address/{contract_address}"
                    }
                else:
                    return {
                        "status": "not_found",
                        "contract_address": contract_address,
                        "error": "Contract not found on explorer"
                    }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {contract_response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Blockscout deployment info check failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
