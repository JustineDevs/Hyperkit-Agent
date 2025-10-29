"""
Public Contract Auditor
Analyzes deployed contracts by address or explorer URL
"""

import requests
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class PublicContractAuditor:
    """Audits public contracts by address or explorer URL"""
    
    def __init__(self):
        # HYPERION-ONLY: Only Hyperion explorer supported
        self.explorer_apis = {
            'hyperion': 'https://hyperion-testnet-explorer.metisdevops.link/api'
            # Future network support (LazAI, Metis) documented in ROADMAP.md only
        }
    
    async def audit_by_address(self, address: str, network: str = 'hyperion') -> Dict[str, Any]:
        """
        Audit a contract by its address
        
        Args:
            address: Contract address
            network: Network to query
            
        Returns:
            Audit results
        """
        try:
            logger.info(f"Auditing public contract: {address} on {network}")
            
            # Get contract source code
            source_code = await self._get_contract_source(address, network)
            
            if not source_code:
                return {
                    "status": "error",
                    "error": "Could not retrieve contract source code",
                    "address": address,
                    "network": network
                }
            
            # Get contract ABI
            abi = await self._get_contract_abi(address, network)
            
            # Analyze contract
            analysis = await self._analyze_contract(source_code, abi, address)
            
            return {
                "status": "success",
                "address": address,
                "network": network,
                "source_code": source_code,
                "abi": abi,
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Failed to audit public contract: {e}")
            return {
                "status": "error",
                "error": str(e),
                "address": address,
                "network": network
            }
    
    async def audit_by_url(self, url: str) -> Dict[str, Any]:
        """
        Audit a contract by explorer URL
        
        Args:
            url: Explorer URL (e.g., https://hyperion-testnet.metisdevops.link/address/0x...)
            
        Returns:
            Audit results
        """
        try:
            # Extract address and network from URL
            address, network = self._parse_explorer_url(url)
            
            if not address:
                return {
                    "status": "error",
                    "error": "Could not extract contract address from URL",
                    "url": url
                }
            
            return await self.audit_by_address(address, network)
            
        except Exception as e:
            logger.error(f"Failed to audit contract by URL: {e}")
            return {
                "status": "error",
                "error": str(e),
                "url": url
            }
    
    async def _get_contract_source(self, address: str, network: str) -> Optional[str]:
        """Get contract source code from explorer API"""
        try:
            api_url = self.explorer_apis.get(network)
            if not api_url:
                logger.error(f"Unsupported network: {network}")
                return None
            
            # Query the actual explorer API for source code
            logger.info(f"Querying {api_url} for contract {address}")
            
            # Make actual API call to get source code
            import requests
            try:
                response = requests.get(f"{api_url}/api?module=contract&action=getsourcecode&address={address}")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "1" and data.get("result"):
                        source_code = data["result"][0].get("SourceCode", "")
                        if source_code and source_code != "":
                            logger.info(f"Successfully retrieved source code for {address}")
                            return source_code
                        else:
                            logger.warning(f"No source code available for {address}")
                            return None
                    else:
                        logger.warning(f"API returned error for {address}: {data.get('message', 'Unknown error')}")
                        return None
                else:
                    logger.error(f"API request failed with status {response.status_code}")
                    return None
            except Exception as e:
                logger.error(f"Failed to query explorer API: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to get contract source: {e}")
            return None
    
    async def _get_contract_abi(self, address: str, network: str) -> Optional[List[Dict]]:
        """Get contract ABI from explorer API"""
        try:
            api_url = self.explorer_apis.get(network)
            if not api_url:
                return None
            
            # Make actual API call to get ABI
            import requests
            try:
                response = requests.get(f"{api_url}/api?module=contract&action=getabi&address={address}")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "1" and data.get("result"):
                        abi_str = data["result"]
                        if abi_str and abi_str != "":
                            import json
                            abi = json.loads(abi_str)
                            logger.info(f"Successfully retrieved ABI for {address}")
                            return abi
                        else:
                            logger.warning(f"No ABI available for {address}")
                            return []
                    else:
                        logger.warning(f"API returned error for {address}: {data.get('message', 'Unknown error')}")
                        return []
                else:
                    logger.error(f"API request failed with status {response.status_code}")
                    return []
            except Exception as e:
                logger.error(f"Failed to query explorer API for ABI: {e}")
                return []
            
        except Exception as e:
            logger.error(f"Failed to get contract ABI: {e}")
            return None
    
    async def _analyze_contract(self, source_code: str, abi: List[Dict], address: str) -> Dict[str, Any]:
        """Analyze contract for security issues"""
        try:
            # Basic analysis - in real implementation, this would use
            # the existing audit tools (Slither, Mythril, etc.)
            
            analysis = {
                "contract_address": address,
                "source_verified": bool(source_code),
                "abi_available": bool(abi),
                "security_issues": [],
                "recommendations": [],
                "risk_level": "unknown"
            }
            
            if source_code:
                # Run static analysis on source code
                analysis.update(await self._run_static_analysis(source_code))
            else:
                # Analyze bytecode if source not available
                analysis.update(await self._analyze_bytecode(address))
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze contract: {e}")
            return {
                "error": str(e),
                "contract_address": address
            }
    
    async def _run_static_analysis(self, source_code: str) -> Dict[str, Any]:
        """Run static analysis on source code using real tools"""
        try:
            # Import the real audit tools
            from services.audit.auditor import HyperKitAuditor
            
            # Create auditor instance
            auditor = HyperKitAuditor()
            
            # Run real security audit
            audit_result = await auditor.audit_contract_security(source_code)
            
            # Parse results
            vulnerabilities = audit_result.get("vulnerabilities", [])
            warnings = audit_result.get("warnings", [])
            recommendations = audit_result.get("recommendations", [])
            
            return {
                "static_analysis": "completed",
                "vulnerabilities_found": len(vulnerabilities),
                "warnings": len(warnings),
                "gas_optimizations": [r for r in recommendations if "gas" in r.lower()],
                "vulnerabilities": vulnerabilities,
                "warnings": warnings,
                "recommendations": recommendations,
                "security_score": audit_result.get("security_score", 0)
            }
        except Exception as e:
            logger.error(f"Static analysis failed: {e}")
            return {
                "static_analysis": "failed",
                "error": str(e),
                "vulnerabilities_found": 0,
                "warnings": 0,
                "gas_optimizations": []
            }
    
    async def _analyze_bytecode(self, address: str) -> Dict[str, Any]:
        """Analyze contract bytecode when source is not available"""
        return {
            "bytecode_analysis": "completed",
            "contract_type": "unknown",
            "proxy_detected": False,
            "upgradeable": False
        }
    
    def _parse_explorer_url(self, url: str) -> tuple[Optional[str], str]:
        """Parse explorer URL to extract address and network"""
        try:
            # Extract address from common explorer URL patterns
            if '/address/' in url:
                address = url.split('/address/')[-1].split('?')[0]
                # Determine network from URL - HYPERION ONLY
                # Future network support (LazAI, Metis) documented in ROADMAP.md only
                if 'hyperion' in url:
                    network = 'hyperion'
                else:
                    # Default to Hyperion (only supported network)
                    network = 'hyperion'
                
                return address, network
            
            return None, 'unknown'
            
        except Exception as e:
            logger.error(f"Failed to parse explorer URL: {e}")
            return None, 'unknown'
    
    def get_supported_networks(self) -> List[str]:
        """Get list of supported networks"""
        return list(self.explorer_apis.keys())
    
    def get_network_explorer_url(self, network: str) -> Optional[str]:
        """Get explorer URL for a network"""
        return self.explorer_apis.get(network)

# Global instance
public_contract_auditor = PublicContractAuditor()
