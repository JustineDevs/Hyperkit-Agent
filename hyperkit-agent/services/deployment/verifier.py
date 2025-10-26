"""
Post-Deployment Verification Service

Verify deployed contracts have correct name/symbol on-chain
to catch deployment issues early.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from web3 import Web3

logger = logging.getLogger(__name__)


class DeploymentVerifier:
    """Verify deployed contracts have correct parameters on-chain"""
    
    def __init__(self, w3: Web3 = None):
        """
        Initialize deployment verifier
        
        Args:
            w3: Web3 instance for blockchain interaction
        """
        self.w3 = w3
    
    def verify_erc20_deployment(
        self, 
        contract_address: str, 
        expected_name: str, 
        expected_symbol: str,
        expected_decimals: int = 18
    ) -> Dict[str, Any]:
        """
        Verify ERC20 contract has correct name/symbol on-chain
        
        Args:
            contract_address: Deployed contract address
            expected_name: Expected token name
            expected_symbol: Expected token symbol
            expected_decimals: Expected decimals
            
        Returns:
            Verification result with success status and details
        """
        try:
            if not self.w3:
                return {
                    "success": False,
                    "error": "Web3 instance not provided"
                }
            
            # ERC20 ABI for name(), symbol(), decimals()
            erc20_abi = [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "name",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "symbol",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "type": "function"
                }
            ]
            
            contract = self.w3.eth.contract(address=contract_address, abi=erc20_abi)
            
            # Get on-chain values
            actual_name = contract.functions.name().call()
            actual_symbol = contract.functions.symbol().call()
            actual_decimals = contract.functions.decimals().call()
            
            # Compare with expected values
            name_match = actual_name == expected_name
            symbol_match = actual_symbol == expected_symbol
            decimals_match = actual_decimals == expected_decimals
            
            verification_result = {
                "success": name_match and symbol_match and decimals_match,
                "contract_address": contract_address,
                "expected": {
                    "name": expected_name,
                    "symbol": expected_symbol,
                    "decimals": expected_decimals
                },
                "actual": {
                    "name": actual_name,
                    "symbol": actual_symbol,
                    "decimals": actual_decimals
                },
                "matches": {
                    "name": name_match,
                    "symbol": symbol_match,
                    "decimals": decimals_match
                }
            }
            
            if verification_result["success"]:
                logger.info(f"✅ Deployment verified: {actual_name} ({actual_symbol})")
            else:
                logger.error(f"❌ DEPLOYMENT MISMATCH!")
                logger.error(f"Expected: {expected_name} ({expected_symbol})")
                logger.error(f"Actual: {actual_name} ({actual_symbol})")
                
                # Add suggestions for fixing
                suggestions = []
                if not name_match:
                    suggestions.append(f"Name mismatch: expected '{expected_name}', got '{actual_name}'")
                if not symbol_match:
                    suggestions.append(f"Symbol mismatch: expected '{expected_symbol}', got '{actual_symbol}'")
                if not decimals_match:
                    suggestions.append(f"Decimals mismatch: expected {expected_decimals}, got {actual_decimals}")
                
                verification_result["suggestions"] = suggestions
            
            return verification_result
            
        except Exception as e:
            logger.error(f"Error verifying deployment: {e}")
            return {
                "success": False,
                "error": str(e),
                "contract_address": contract_address
            }
    
    def verify_erc721_deployment(
        self, 
        contract_address: str, 
        expected_name: str, 
        expected_symbol: str
    ) -> Dict[str, Any]:
        """
        Verify ERC721 contract has correct name/symbol on-chain
        
        Args:
            contract_address: Deployed contract address
            expected_name: Expected token name
            expected_symbol: Expected token symbol
            
        Returns:
            Verification result with success status and details
        """
        try:
            if not self.w3:
                return {
                    "success": False,
                    "error": "Web3 instance not provided"
                }
            
            # ERC721 ABI for name(), symbol()
            erc721_abi = [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "name",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "symbol",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function"
                }
            ]
            
            contract = self.w3.eth.contract(address=contract_address, abi=erc721_abi)
            
            # Get on-chain values
            actual_name = contract.functions.name().call()
            actual_symbol = contract.functions.symbol().call()
            
            # Compare with expected values
            name_match = actual_name == expected_name
            symbol_match = actual_symbol == expected_symbol
            
            verification_result = {
                "success": name_match and symbol_match,
                "contract_address": contract_address,
                "expected": {
                    "name": expected_name,
                    "symbol": expected_symbol
                },
                "actual": {
                    "name": actual_name,
                    "symbol": actual_symbol
                },
                "matches": {
                    "name": name_match,
                    "symbol": symbol_match
                }
            }
            
            if verification_result["success"]:
                logger.info(f"✅ ERC721 deployment verified: {actual_name} ({actual_symbol})")
            else:
                logger.error(f"❌ ERC721 DEPLOYMENT MISMATCH!")
                logger.error(f"Expected: {expected_name} ({expected_symbol})")
                logger.error(f"Actual: {actual_name} ({actual_symbol})")
                
                suggestions = []
                if not name_match:
                    suggestions.append(f"Name mismatch: expected '{expected_name}', got '{actual_name}'")
                if not symbol_match:
                    suggestions.append(f"Symbol mismatch: expected '{expected_symbol}', got '{actual_symbol}'")
                
                verification_result["suggestions"] = suggestions
            
            return verification_result
            
        except Exception as e:
            logger.error(f"Error verifying ERC721 deployment: {e}")
            return {
                "success": False,
                "error": str(e),
                "contract_address": contract_address
            }
    
    def verify_contract_deployment(
        self, 
        contract_address: str, 
        contract_code: str,
        contract_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        Automatically verify contract deployment based on contract type
        
        Args:
            contract_address: Deployed contract address
            contract_code: Original contract source code
            contract_type: Contract type (erc20, erc721, auto)
            
        Returns:
            Verification result
        """
        try:
            from .constructor_parser import ConstructorArgumentParser
            
            parser = ConstructorArgumentParser()
            
            # Auto-detect contract type if not specified
            if contract_type == "auto":
                if "ERC20" in contract_code:
                    contract_type = "erc20"
                elif "ERC721" in contract_code:
                    contract_type = "erc721"
                else:
                    return {
                        "success": False,
                        "error": "Could not auto-detect contract type"
                    }
            
            if contract_type == "erc20":
                name, symbol = parser.extract_erc20_name_symbol(contract_code)
                if name and symbol:
                    return self.verify_erc20_deployment(contract_address, name, symbol)
                else:
                    return {
                        "success": False,
                        "error": "Could not extract ERC20 name/symbol from contract code"
                    }
            
            elif contract_type == "erc721":
                name, symbol = parser.extract_erc721_name_symbol(contract_code)
                if name and symbol:
                    return self.verify_erc721_deployment(contract_address, name, symbol)
                else:
                    return {
                        "success": False,
                        "error": "Could not extract ERC721 name/symbol from contract code"
                    }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported contract type: {contract_type}"
                }
                
        except Exception as e:
            logger.error(f"Error in automatic verification: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Convenience function for testing
def test_deployment_verification(contract_address: str, rpc_url: str, expected_name: str, expected_symbol: str):
    """Test deployment verification with sample contract"""
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        verifier = DeploymentVerifier(w3)
        
        result = verifier.verify_erc20_deployment(contract_address, expected_name, expected_symbol)
        
        print("Deployment Verification Test")
        print("=" * 50)
        print(f"Contract: {contract_address}")
        print(f"Expected: {expected_name} ({expected_symbol})")
        print(f"Actual: {result['actual']['name']} ({result['actual']['symbol']})")
        print(f"Success: {result['success']}")
        
        if not result['success']:
            print("Suggestions:")
            for suggestion in result.get('suggestions', []):
                print(f"  - {suggestion}")
        
        return result
        
    except Exception as e:
        print(f"Verification test failed: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Test with sample contract address
    test_address = "0x1234567890123456789012345678901234567890"
    test_rpc = "https://hyperion-testnet.metisdevops.link"
    test_name = "GAMEX Token"
    test_symbol = "GAMEX"
    
    test_deployment_verification(test_address, test_rpc, test_name, test_symbol)
