"""
Constructor Argument Parser

Extract constructor arguments from Solidity source code to ensure
proper deployment with correct parameters.
"""

import re
import logging
from typing import List, Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)


class ConstructorArgumentParser:
    """Extract constructor arguments from Solidity source code"""
    
    @staticmethod
    def extract_constructor_params(contract_code: str) -> Optional[Tuple[str, List[str]]]:
        """
        Extract constructor signature and parameter types from Solidity code.
        
        Args:
            contract_code: Solidity source code
            
        Returns:
            (contract_name, [param_types]) or None if no constructor found
        """
        try:
            # Find contract name - use more specific pattern
            contract_match = re.search(r'contract\s+([A-Z][a-zA-Z0-9_]*)', contract_code)
            if not contract_match:
                logger.warning("No contract declaration found")
                return None
            contract_name = contract_match.group(1)
            
            # Find constructor
            constructor_pattern = r'constructor\s*\(([^)]*)\)'
            constructor_match = re.search(constructor_pattern, contract_code)
            
            if not constructor_match:
                logger.info(f"No constructor found in {contract_name}")
                return (contract_name, [])  # No constructor
            
            # Parse constructor parameters
            params_str = constructor_match.group(1)
            if not params_str.strip():
                logger.info(f"Empty constructor found in {contract_name}")
                return (contract_name, [])  # Empty constructor
            
            # Extract parameter types and names
            params = []
            for param in params_str.split(','):
                param = param.strip()
                if param:
                    # Extract type and name (e.g., "address initialOwner" -> ("address", "initialOwner"))
                    type_name_match = re.match(r'(\w+(?:\[\])?)\s+(\w+)', param)
                    if type_name_match:
                        param_type = type_name_match.group(1)
                        param_name = type_name_match.group(2)
                        params.append((param_type, param_name))
                    else:
                        # Fallback: just extract type
                        type_match = re.match(r'(\w+(?:\[\])?)', param)
                        if type_match:
                            params.append((type_match.group(1), f"param{len(params)}"))
            
            logger.info(f"Found constructor in {contract_name} with {len(params)} parameters")
            return (contract_name, params)
            
        except Exception as e:
            logger.error(f"Error extracting constructor params: {e}")
            return None
    
    @staticmethod
    def extract_erc20_name_symbol(contract_code: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract ERC20 token name and symbol from constructor ERC20() call.
        
        Args:
            contract_code: Solidity source code
            
        Returns:
            (name, symbol) or (None, None) if not found
        """
        try:
            # Pattern: ERC20("TokenName", "SYMBOL")
            pattern = r'ERC20\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)'
            match = re.search(pattern, contract_code)
            
            if match:
                name = match.group(1)
                symbol = match.group(2)
                logger.info(f"Extracted ERC20: {name} ({symbol})")
                return (name, symbol)
            
            logger.warning("No ERC20 constructor found in code")
            return (None, None)
            
        except Exception as e:
            logger.error(f"Error extracting ERC20 name/symbol: {e}")
            return (None, None)
    
    @staticmethod
    def extract_erc721_name_symbol(contract_code: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract ERC721 token name and symbol from constructor ERC721() call.
        
        Args:
            contract_code: Solidity source code
            
        Returns:
            (name, symbol) or (None, None) if not found
        """
        try:
            # Pattern: ERC721("TokenName", "SYMBOL")
            pattern = r'ERC721\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)'
            match = re.search(pattern, contract_code)
            
            if match:
                name = match.group(1)
                symbol = match.group(2)
                logger.info(f"Extracted ERC721: {name} ({symbol})")
                return (name, symbol)
            
            logger.warning("No ERC721 constructor found in code")
            return (None, None)
            
        except Exception as e:
            logger.error(f"Error extracting ERC721 name/symbol: {e}")
            return (None, None)
    
    @staticmethod
    def generate_constructor_args(contract_code: str, deployer_address: str) -> List[str]:
        """
        Generate appropriate constructor arguments for deployment.
        
        Args:
            contract_code: Solidity source code
            deployer_address: Address of the deployer
            
        Returns:
            List of constructor arguments as strings
        """
        try:
            result = ConstructorArgumentParser.extract_constructor_params(contract_code)
            if not result:
                logger.warning("Could not extract constructor params")
                return []
            
            contract_name, param_types = result
            
            if not param_types:
                logger.info(f"No constructor parameters for {contract_name}")
                return []  # No constructor or no params
            
            args = []
            for param_type, param_name in param_types:
                if param_type == 'address':
                    # Use deployer address as default
                    args.append(deployer_address)
                    logger.info(f"Using deployer address for {param_name}: {deployer_address}")
                elif param_type == 'uint256':
                    # Try to extract from code if it's a supply parameter
                    if 'supply' in param_name.lower() or 'amount' in param_name.lower():
                        # Look for supply constants in code
                        supply_match = re.search(r'(\d+(?:_\d+)*)\s*\*\s*\(10\*\*(\d+)\)', contract_code)
                        if supply_match:
                            supply = supply_match.group(1).replace('_', '')
                            decimals = supply_match.group(2)
                            total_supply = str(int(supply) * (10 ** int(decimals)))
                            args.append(total_supply)
                            logger.info(f"Using extracted supply for {param_name}: {total_supply}")
                        else:
                            args.append('0')
                    else:
                        args.append('0')
                elif param_type == 'string':
                    # Extract from ERC20/ERC721 constructor if possible
                    name, symbol = ConstructorArgumentParser.extract_erc20_name_symbol(contract_code)
                    if not name:
                        name, symbol = ConstructorArgumentParser.extract_erc721_name_symbol(contract_code)
                    
                    if name and 'name' in param_name.lower():
                        args.append(f'"{name}"')
                        logger.info(f"Using extracted name for {param_name}: {name}")
                    elif symbol and 'symbol' in param_name.lower():
                        args.append(f'"{symbol}"')
                        logger.info(f"Using extracted symbol for {param_name}: {symbol}")
                    else:
                        args.append('""')
                elif param_type == 'bool':
                    args.append('true')
                else:
                    # Generic fallback
                    if 'uint' in param_type:
                        args.append('0')
                    else:
                        args.append('""')
            
            logger.info(f"Generated constructor args for {contract_name}: {args}")
            return args
            
        except Exception as e:
            logger.error(f"Error generating constructor args: {e}")
            return []
    
    @staticmethod
    def validate_constructor_args(contract_code: str, args: List[str]) -> Dict[str, Any]:
        """
        Validate that constructor arguments match the contract signature.
        
        Args:
            contract_code: Solidity source code
            args: Constructor arguments to validate
            
        Returns:
            Validation result with success status and details
        """
        try:
            result = ConstructorArgumentParser.extract_constructor_params(contract_code)
            if not result:
                return {"success": False, "error": "Could not extract constructor params"}
            
            contract_name, param_types = result
            
            if len(args) != len(param_types):
                return {
                    "success": False,
                    "error": f"Argument count mismatch: expected {len(param_types)}, got {len(args)}",
                    "expected": len(param_types),
                    "actual": len(args)
                }
            
            # Validate argument types
            validation_details = []
            for i, (arg, (param_type, param_name)) in enumerate(zip(args, param_types)):
                if param_type == 'address':
                    if not arg.startswith('0x') or len(arg) != 42:
                        validation_details.append(f"Invalid address format for {param_name}: {arg}")
                elif param_type == 'uint256':
                    try:
                        int(arg)
                    except ValueError:
                        validation_details.append(f"Invalid uint256 for {param_name}: {arg}")
                elif param_type == 'string':
                    if not (arg.startswith('"') and arg.endswith('"')):
                        validation_details.append(f"Invalid string format for {param_name}: {arg}")
            
            if validation_details:
                return {
                    "success": False,
                    "error": "Constructor argument validation failed",
                    "details": validation_details
                }
            
            return {
                "success": True,
                "contract_name": contract_name,
                "param_count": len(param_types),
                "args": args
            }
            
        except Exception as e:
            logger.error(f"Error validating constructor args: {e}")
            return {"success": False, "error": str(e)}


# Convenience function for testing
def test_constructor_extraction(contract_code: str, deployer_address: str = "0x1234567890123456789012345678901234567890"):
    """Test constructor extraction with sample contract code."""
    parser = ConstructorArgumentParser()
    
    print("Testing Constructor Extraction")
    print("=" * 50)
    
    # Extract constructor params
    result = parser.extract_constructor_params(contract_code)
    if result:
        contract_name, param_types = result
        print(f"Contract: {contract_name}")
        print(f"Parameters: {param_types}")
    else:
        print("No constructor found")
    
    # Extract ERC20 name/symbol
    name, symbol = parser.extract_erc20_name_symbol(contract_code)
    if name and symbol:
        print(f"ERC20: {name} ({symbol})")
    else:
        print("No ERC20 constructor found")
    
    # Generate constructor args
    args = parser.generate_constructor_args(contract_code, deployer_address)
    print(f"Generated args: {args}")
    
    # Validate args
    validation = parser.validate_constructor_args(contract_code, args)
    print(f"Validation: {validation}")
    
    return {
        "contract_name": contract_name if result else None,
        "erc20_name": name,
        "erc20_symbol": symbol,
        "constructor_args": args,
        "validation": validation
    }


if __name__ == "__main__":
    # Test with sample contract
    sample_contract = '''
    // SPDX-License-Identifier: MIT
    pragma solidity ^0.8.0;
    
    import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
    
    contract GAMEXToken is ERC20 {
        uint256 public constant INITIAL_SUPPLY = 1_000_000_000 * (10**18);
        
        constructor(address initialOwner)
            ERC20("GAMEX Token", "GAMEX")
        {
            _mint(initialOwner, INITIAL_SUPPLY);
        }
    }
    '''
    
    test_constructor_extraction(sample_contract)
