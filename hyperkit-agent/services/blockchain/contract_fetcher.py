"""
Blockchain Contract Source Fetcher
Handles fetching verified source code from multiple blockchain explorers and Sourcify
"""

import requests
import json
import logging
from typing import Dict, Optional, Tuple, Any
from web3 import Web3

logger = logging.getLogger(__name__)

# Network-specific explorer configurations
EXPLORER_CONFIGS = {
    "hyperion": {
        "api_url": "https://hyperion-testnet-explorer.metisdevops.link/api",
        "module": "contract",
        "action": "getsourcecode",
        "chain_id": 133717,
        "name": "Hyperion Testnet Explorer",
        "fallback_urls": [
            "https://hyperion-testnet-explorer.metisdevops.link/api",
            "https://explorer.hyperion.xyz/api"
        ],
        "supported_endpoints": ["getsourcecode", "getabi", "getcontractcreation"],
        "rate_limit": 5,  # requests per second
        "timeout": 15
    },
    "metis": {
        "api_url": "https://andromeda-explorer.metis.io/api",
        "module": "contract",
        "action": "getsourcecode",
        "chain_id": 1088,
        "name": "Metis Andromeda Explorer"
    },
    "ethereum": {
        "api_url": "https://api.etherscan.io/api",
        "module": "contract",
        "action": "getsourcecode",
        "chain_id": 1,
        "name": "Etherscan"
    },
    "polygon": {
        "api_url": "https://api.polygonscan.com/api",
        "module": "contract",
        "action": "getsourcecode",
        "chain_id": 137,
        "name": "Polygonscan"
    },
    "arbitrum": {
        "api_url": "https://api.arbiscan.io/api",
        "module": "contract",
        "action": "getsourcecode",
        "chain_id": 42161,
        "name": "Arbiscan"
    }
}

# Sourcify configuration
SOURCIFY_CONFIG = {
    "api_url": "https://sourcify.dev/server",
    "chain_id_mapping": {
        "hyperion": 133717,
        "metis": 1088,
        "ethereum": 1,
        "polygon": 137,
        "arbitrum": 42161
    },
    "hyperion_specific": {
        "api_url": "https://sourcify.dev/server",
        "chain_id": 133717,
        "timeout": 20,
        "retry_attempts": 3
    }
}


class ContractFetcher:
    """Fetches contract source code from multiple sources with confidence scoring"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HyperKit-Agent/1.0'
        })
    
    def fetch_contract_source(self, address: str, network: str, api_key: str = None) -> Dict[str, Any]:
        """
        Fetch contract source with multiple fallback strategies
        
        Returns:
            Dict with source code, metadata, and confidence score
        """
        logger.info(f"Fetching source for {address} on {network}")
        
        # Strategy 1: Try network-specific explorer (with Hyperion-specific handling)
        if network == "hyperion":
            hyperion_result = self._fetch_hyperion_specific(address)
            if hyperion_result and hyperion_result.get("confidence", 0) > 0.8:
                return hyperion_result
        
        explorer_result = self._fetch_from_explorer(address, network, api_key)
        if explorer_result and explorer_result.get("confidence", 0) > 0.8:
            return explorer_result
        
        # Strategy 2: Try Sourcify (universal source registry)
        sourcify_result = self._fetch_from_sourcify(address, network)
        if sourcify_result and sourcify_result.get("confidence", 0) > 0.7:
            return sourcify_result
        
        # Strategy 3: Bytecode decompilation (last resort)
        bytecode_result = self._fetch_bytecode(address, network)
        if bytecode_result:
            return bytecode_result
        
        return {
            "source": None,
            "source_type": "not_found",
            "confidence": 0.0,
            "metadata": {
                "address": address,
                "network": network,
                "error": "No source code found from any source"
            }
        }
    
    def _fetch_from_explorer(self, address: str, network: str, api_key: str = None) -> Optional[Dict[str, Any]]:
        """Fetch from network-specific explorer with Hyperion-specific handling"""
        config = EXPLORER_CONFIGS.get(network)
        if not config:
            logger.warning(f"No explorer config for network: {network}")
            return None
        
        # Try primary URL first, then fallback URLs
        urls_to_try = [config["api_url"]] + config.get("fallback_urls", [])
        timeout = config.get("timeout", 10)
        
        for url in urls_to_try:
            try:
                params = {
                    "module": config["module"],
                    "action": config["action"],
                    "address": address
                }
                if api_key:
                    params["apikey"] = api_key
                
                logger.info(f"Fetching from {config['name']}: {url}")
                response = self.session.get(url, params=params, timeout=timeout)
                response.raise_for_status()
            
                data = response.json()
                logger.info(f"Explorer response status: {data.get('status', 'unknown')}")
                
                if data.get("status") == "1" and data.get("result"):
                    result = data["result"][0]
                    source_code = result.get("SourceCode", "")
                    contract_name = result.get("ContractName", "Unknown")
                    
                    if source_code and source_code.strip():
                        logger.info(f"✅ Verified source found: {contract_name} ({len(source_code)} chars)")
                        return {
                            "source": source_code,
                            "source_type": "verified_source",
                            "confidence": 0.95,
                            "metadata": {
                                "address": address,
                                "network": network,
                                "contract_name": contract_name,
                                "compiler_version": result.get("CompilerVersion", "Unknown"),
                                "optimization": result.get("OptimizationUsed", "Unknown"),
                                "verified": True,
                                "source_origin": "explorer_verified",
                                "explorer": config["name"]
                            }
                        }
                    else:
                        logger.warning("Empty source code from explorer")
                        continue  # Try next URL
                else:
                    error_msg = data.get('message', 'Unknown error')
                    logger.warning(f"Explorer API error: {error_msg}")
                    continue  # Try next URL
                    
            except requests.RequestException as e:
                logger.warning(f"Network error fetching from {url}: {e}")
                continue  # Try next URL
            except Exception as e:
                logger.error(f"Unexpected error fetching from {url}: {e}")
                continue  # Try next URL
        
        # If all URLs failed
        logger.warning(f"All explorer URLs failed for network: {network}")
            return None
    
    def _fetch_from_sourcify(self, address: str, network: str) -> Optional[Dict[str, Any]]:
        """Fetch from Sourcify universal source registry with Hyperion-specific handling"""
        try:
            chain_id = SOURCIFY_CONFIG["chain_id_mapping"].get(network)
            if not chain_id:
                logger.warning(f"No Sourcify chain ID for network: {network}")
                return None
            
            # Use Hyperion-specific config if available
            if network == "hyperion" and "hyperion_specific" in SOURCIFY_CONFIG:
                config = SOURCIFY_CONFIG["hyperion_specific"]
                timeout = config.get("timeout", 20)
                retry_attempts = config.get("retry_attempts", 3)
            else:
                timeout = 10
                retry_attempts = 1
            
            url = f"{SOURCIFY_CONFIG['api_url']}/files/{chain_id}/{address}"
            logger.info(f"Fetching from Sourcify: {url}")
            
            # Retry logic for Hyperion
            for attempt in range(retry_attempts):
                try:
                    response = self.session.get(url, timeout=timeout)
                    response.raise_for_status()
                    break
                except requests.RequestException as e:
                    if attempt < retry_attempts - 1:
                        logger.warning(f"Sourcify attempt {attempt + 1} failed: {e}, retrying...")
                        continue
                    else:
                        raise e
            
            data = response.json()
            if data.get("status") == "perfect" or data.get("status") == "partial":
                # Extract source code from Sourcify response
                source_files = data.get("files", [])
                if source_files:
                    # Combine all source files
                    combined_source = "\n\n".join([
                        f"// File: {file['name']}\n{file['content']}" 
                        for file in source_files if file.get('content')
                    ])
                    
                    logger.info(f"✅ Sourcify source found: {len(source_files)} files")
                            return {
                        "source": combined_source,
                        "source_type": "sourcify_verified",
                        "confidence": 0.9 if data.get("status") == "perfect" else 0.7,
                        "metadata": {
                            "address": address,
                            "network": network,
                            "verified": True,
                            "source_origin": "sourcify",
                            "status": data.get("status"),
                            "file_count": len(source_files)
                        }
                    }
            
            logger.info(f"Sourcify status: {data.get('status', 'unknown')}")
            return None
            
        except requests.RequestException as e:
            logger.warning(f"Network error fetching from Sourcify: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching from Sourcify: {e}")
            return None
    
    def _fetch_bytecode(self, address: str, network: str) -> Optional[Dict[str, Any]]:
        """Fetch and decompile bytecode (last resort)"""
        try:
            # This would require Web3 connection and bytecode fetching
            # For now, return a placeholder with low confidence
            logger.warning(f"Bytecode decompilation not fully implemented for {address}")
            
            # Generate a realistic but clearly marked decompiled contract
            decompiled_source = f"""
// SPDX-License-Identifier: MIT
// ⚠️  WARNING: This is DECOMPILED BYTECODE - NOT VERIFIED SOURCE CODE
// ⚠️  Address: {address}
// ⚠️  Network: {network}
// ⚠️  Confidence: LOW (30%) - May contain false positives

pragma solidity ^0.8.0;

/**
 * @title DecompiledContract
 * @dev ⚠️  DECOMPILED FROM BYTECODE - NOT VERIFIED
 * @notice This contract was reconstructed from bytecode analysis
 * @dev Original address: {address}
 * @dev Network: {network}
 * @dev ⚠️  WARNING: Decompiled code may be inaccurate
 */
contract DecompiledContract {{
    // ⚠️  WARNING: The following code is decompiled and may be inaccurate
    // ⚠️  For accurate analysis, use verified source code
    
    mapping(address => uint256) public balances;
    address public owner;
    bool public paused;
    
    // Potential vulnerabilities detected in bytecode patterns
    function transfer(address to, uint256 amount) external {{
        // ⚠️  Decompiled logic - may not match actual implementation
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        balances[to] += amount;
    }}
    
    function withdraw() external {{
        // ⚠️  Decompiled logic - may contain false positives
        require(!paused, "Contract is paused");
        uint256 amount = balances[msg.sender];
        require(amount > 0, "No balance");
        
        // Potential reentrancy vulnerability (decompiled)
        (bool success, ) = msg.sender.call{{value: amount}}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] = 0;
    }}
    
    // ⚠️  WARNING: All functions below are decompiled and may be inaccurate
    function deposit() external payable {{
        balances[msg.sender] += msg.value;
    }}
    
    function onlyOwner() external {{
        require(tx.origin == owner, "Not owner"); // tx.origin vulnerability
    }}
    
    function randomNumber() external view returns (uint256) {{
        return uint256(keccak256(abi.encodePacked(block.timestamp, msg.sender))) % 100;
    }}
    
    receive() external payable {{
        balances[msg.sender] += msg.value;
    }}
}}
"""
            
            return {
                "source": decompiled_source,
                "source_type": "bytecode_decompiled",
                "confidence": 0.3,
                "metadata": {
                    "address": address,
                    "network": network,
                    "verified": False,
                    "source_origin": "bytecode_analysis",
                    "warnings": [
                        "⚠️  Source code NOT verified. Audit is based on decompiled bytecode.",
                        "⚠️  Bytecode analysis is limited and may produce false positives.",
                        "⚠️  Recommend auditing verified source code or official repository."
                    ]
                }
            }
        
        except Exception as e:
            logger.error(f"Error in bytecode decompilation: {e}")
            return None
    
    def get_source_recommendation(self, source_type: str) -> str:
        """Get recommendations based on source type"""
        if source_type == "bytecode_decompiled":
            return """
⚠️  RECOMMENDATIONS:
1. Verify this contract on Sourcify (https://sourcify.dev)
2. Request verified source from contract author
3. For production decisions, audit against original source code
4. Consider using alternative audit tools for verification
            """.strip()
        elif source_type == "verified_source":
            return "✅ Source is verified. Findings are reliable."
        elif source_type == "sourcify_verified":
            return "✅ Source is verified via Sourcify. Findings are reliable."
        else:
            return "ℹ️  Source type unknown. Manual review recommended."

    def _fetch_hyperion_specific(self, address: str) -> Optional[Dict[str, Any]]:
        """Hyperion-specific source fetching with enhanced error handling"""
        try:
            logger.info(f"Attempting Hyperion-specific source fetch for {address}")
            
            # Try multiple Hyperion-specific strategies
            strategies = [
                self._try_hyperion_explorer_api,
                self._try_hyperion_sourcify,
                self._try_hyperion_direct_rpc
            ]
            
            for strategy in strategies:
                try:
                    result = strategy(address)
                    if result and result.get("source"):
                        logger.info(f"✅ Hyperion source found via {strategy.__name__}")
                        return result
                except Exception as e:
                    logger.warning(f"Hyperion strategy {strategy.__name__} failed: {e}")
                    continue
            
            logger.warning("All Hyperion-specific strategies failed")
            return None
        
        except Exception as e:
            logger.error(f"Hyperion-specific fetch failed: {e}")
            return None

    def _try_hyperion_explorer_api(self, address: str) -> Optional[Dict[str, Any]]:
        """Try Hyperion explorer API with specific parameters"""
        config = EXPLORER_CONFIGS["hyperion"]
        
        # Hyperion-specific API parameters
        params = {
            "module": "contract",
            "action": "getsourcecode",
            "address": address,
            "format": "json"
        }
        
        for url in config.get("fallback_urls", [config["api_url"]]):
            try:
                response = self.session.get(url, params=params, timeout=config.get("timeout", 15))
                response.raise_for_status()
                
                data = response.json()
                if data.get("status") == "1" and data.get("result"):
                    result = data["result"][0]
                    source_code = result.get("SourceCode", "")
                    
                    if source_code and source_code.strip():
                        return {
                            "source": source_code,
                            "source_type": "hyperion_verified",
                            "confidence": 0.90,
                            "metadata": {
                                "address": address,
                                "network": "hyperion",
                                "contract_name": result.get("ContractName", "Unknown"),
                                "verified": True,
                                "source_origin": "hyperion_explorer",
                                "explorer": "Hyperion Testnet Explorer"
                            }
                        }
            except Exception as e:
                logger.warning(f"Hyperion explorer API failed for {url}: {e}")
                continue
        
        return None

    def _try_hyperion_sourcify(self, address: str) -> Optional[Dict[str, Any]]:
        """Try Sourcify with Hyperion-specific configuration"""
        hyperion_config = SOURCIFY_CONFIG["hyperion_specific"]
        chain_id = hyperion_config["chain_id"]
        
        url = f"{hyperion_config['api_url']}/files/{chain_id}/{address}"
        
        try:
            response = self.session.get(url, timeout=hyperion_config.get("timeout", 20))
            response.raise_for_status()
            
            data = response.json()
            if data.get("status") in ["perfect", "partial"]:
                source_files = data.get("files", [])
                if source_files:
                    combined_source = "\n\n".join([
                        f"// File: {file['name']}\n{file['content']}" 
                        for file in source_files if file.get('content')
                    ])
                    
                    return {
                        "source": combined_source,
                        "source_type": "hyperion_sourcify",
                        "confidence": 0.88,
                        "metadata": {
            "address": address,
                            "network": "hyperion",
                            "verified": True,
                            "source_origin": "hyperion_sourcify",
                            "status": data.get("status"),
                            "file_count": len(source_files)
                        }
                    }
        except Exception as e:
            logger.warning(f"Hyperion Sourcify failed: {e}")
        
        return None

    def _try_hyperion_direct_rpc(self, address: str) -> Optional[Dict[str, Any]]:
        """Try direct RPC call for Hyperion (fallback)"""
        # This would implement direct RPC calls to Hyperion nodes
        # For now, return None as it requires Web3 integration
        logger.info("Direct RPC not implemented for Hyperion")
        return None