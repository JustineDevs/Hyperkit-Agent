"""
Constructor Argument Parser - Enhanced Version

Extract constructor arguments from Solidity source code to ensure
proper deployment with correct parameters.

Enhanced with support for:
- Array types (dynamic and fixed-size)
- Bytes types (bytes, bytes32, bytes1-bytes31)
- All uint/int variants (uint8-uint256, int8-int256)
- Better type inference and validation
"""

import re
import logging
from typing import List, Tuple, Optional, Dict, Any, Union

logger = logging.getLogger(__name__)


class ConstructorArgumentParser:
    """
    Extract constructor arguments from Solidity source code.
    
    Supports all Solidity types:
    - Basic: address, bool, string
    - Integers: uint8-uint256, int8-int256
    - Bytes: bytes, bytes1-bytes32
    - Arrays: type[], type[N]
    - Complex: tuples, structs (basic support)
    """
    
    @staticmethod
    def extract_constructor_params(contract_code: str) -> Optional[Tuple[str, List[Tuple[str, str]]]]:
        """
        Extract constructor signature and parameter types from Solidity code.
        
        Supports all Solidity types including arrays, bytes, and complex types.
        
        Args:
            contract_code: Solidity source code
            
        Returns:
            (contract_name, [(param_type, param_name), ...]) or None if no constructor found
        """
        try:
            # Find contract name - use more specific pattern
            contract_match = re.search(r'contract\s+([A-Z][a-zA-Z0-9_]*)', contract_code)
            if not contract_match:
                logger.warning("No contract declaration found")
                return None
            contract_name = contract_match.group(1)
            
            # Find constructor - improved pattern to handle complex params
            constructor_pattern = r'constructor\s*\((.*?)\)\s*(?:public|internal|external|payable|ERC\w+)?'
            constructor_match = re.search(constructor_pattern, contract_code, re.DOTALL)
            
            if not constructor_match:
                logger.info(f"No constructor found in {contract_name}")
                return (contract_name, [])  # No constructor
            
            # Parse constructor parameters
            params_str = constructor_match.group(1)
            if not params_str.strip():
                logger.info(f"Empty constructor found in {contract_name}")
                return (contract_name, [])  # Empty constructor
            
            # Extract parameter types and names - enhanced for complex types
            params = []
            # Handle parameters with complex types (arrays, fixed arrays, bytes, etc.)
            # Pattern: type (memory|storage|calldata)? name
            param_pattern = r'([\w\[\]]+)(?:\s+(?:memory|storage|calldata))?\s+(\w+)'
            
            for param in params_str.split(','):
                param = param.strip()
                if param:
                    match = re.match(param_pattern, param)
                    if match:
                        param_type = match.group(1)
                        param_name = match.group(2)
                        params.append((param_type, param_name))
                        logger.debug(f"Extracted param: {param_type} {param_name}")
                    else:
                        # Fallback: try to extract just the type
                        type_match = re.match(r'([\w\[\]]+)', param)
                        if type_match:
                            param_type = type_match.group(1)
                            param_name = f"param{len(params)}"
                            params.append((param_type, param_name))
                            logger.debug(f"Extracted param (no name): {param_type}")
            
            logger.info(f"Found constructor in {contract_name} with {len(params)} parameters")
            for param_type, param_name in params:
                logger.debug(f"  - {param_type} {param_name}")
            
            return (contract_name, params)
            
        except Exception as e:
            logger.error(f"Error extracting constructor params: {e}")
            return None
    
    @staticmethod
    def is_array_type(param_type: str) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check if parameter is an array type and extract base type.
        
        Args:
            param_type: Solidity type string
            
        Returns:
            (is_array, base_type, size)
            - is_array: True if array type
            - base_type: Base type (e.g., "uint256" for "uint256[]")
            - size: Array size for fixed arrays, None for dynamic arrays
        """
        # Dynamic array: type[]
        if param_type.endswith('[]'):
            base_type = param_type[:-2]
            return (True, base_type, None)
        
        # Fixed-size array: type[N]
        fixed_array_match = re.match(r'([\w]+)\[(\d+)\]', param_type)
        if fixed_array_match:
            base_type = fixed_array_match.group(1)
            size = int(fixed_array_match.group(2))
            return (True, base_type, size)
        
        return (False, None, None)
    
    @staticmethod
    def is_bytes_type(param_type: str) -> Tuple[bool, Optional[int]]:
        """
        Check if parameter is a bytes type.
        
        Args:
            param_type: Solidity type string
            
        Returns:
            (is_bytes, size)
            - is_bytes: True if bytes type
            - size: Byte size for fixed bytes (1-32), None for dynamic bytes
        """
        if param_type == 'bytes':
            return (True, None)  # Dynamic bytes
        
        # Fixed bytes: bytes1-bytes32
        bytes_match = re.match(r'bytes(\d+)', param_type)
        if bytes_match:
            size = int(bytes_match.group(1))
            if 1 <= size <= 32:
                return (True, size)
        
        return (False, None)
    
    @staticmethod
    def is_uint_type(param_type: str) -> Tuple[bool, Optional[int]]:
        """
        Check if parameter is a uint type and extract bit size.
        
        Args:
            param_type: Solidity type string
            
        Returns:
            (is_uint, bits)
            - is_uint: True if uint type
            - bits: Bit size (8-256), defaults to 256 for 'uint'
        """
        if param_type == 'uint' or param_type == 'uint256':
            return (True, 256)
        
        uint_match = re.match(r'uint(\d+)', param_type)
        if uint_match:
            bits = int(uint_match.group(1))
            if bits % 8 == 0 and 8 <= bits <= 256:
                return (True, bits)
        
        return (False, None)
    
    @staticmethod
    def is_int_type(param_type: str) -> Tuple[bool, Optional[int]]:
        """
        Check if parameter is an int type and extract bit size.
        
        Args:
            param_type: Solidity type string
            
        Returns:
            (is_int, bits)
            - is_int: True if int type
            - bits: Bit size (8-256), defaults to 256 for 'int'
        """
        if param_type == 'int' or param_type == 'int256':
            return (True, 256)
        
        int_match = re.match(r'int(\d+)', param_type)
        if int_match:
            bits = int(int_match.group(1))
            if bits % 8 == 0 and 8 <= bits <= 256:
                return (True, bits)
        
        return (False, None)
    
    @staticmethod
    def is_struct_type(param_type: str, contract_code: str) -> Tuple[bool, Optional[str]]:
        """
        Check if parameter is a struct type and extract struct name.
        
        Args:
            param_type: Solidity type string
            contract_code: Contract source code for struct definitions
            
        Returns:
            (is_struct, struct_name)
            - is_struct: True if struct type
            - struct_name: Name of the struct
        """
        # Check for custom struct types (basically any uppercase type that's not a built-in)
        builtin_types = {
            'address', 'bool', 'string', 'bytes', 'uint', 'int',
            'bytes1', 'bytes2', 'bytes3', 'bytes4', 'bytes5', 'bytes6', 'bytes7', 'bytes8',
            'bytes9', 'bytes10', 'bytes11', 'bytes12', 'bytes13', 'bytes14', 'bytes15', 'bytes16',
            'bytes17', 'bytes18', 'bytes19', 'bytes20', 'bytes21', 'bytes22', 'bytes23', 'bytes24',
            'bytes25', 'bytes26', 'bytes27', 'bytes28', 'bytes29', 'bytes30', 'bytes31', 'bytes32',
            'uint8', 'uint16', 'uint32', 'uint64', 'uint128', 'uint256',
            'int8', 'int16', 'int32', 'int64', 'int128', 'int256'
        }
        
        # Simple heuristic: if it starts with uppercase and is not a built-in, it's likely a struct
        if param_type and param_type[0].isupper() and param_type not in builtin_types:
            return (True, param_type)
        
        return (False, None)
    
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
    def generate_constructor_arg(param_type: str, param_name: str, contract_code: str, deployer_address: str) -> Any:
        """
        Generate a single constructor argument based on its type.
        
        Args:
            param_type: Solidity type string
            param_name: Parameter name
            contract_code: Contract source (for extracting context)
            deployer_address: Deployer address for address types
            
        Returns:
            Generated argument value
        """
        # Check for array types first
        is_array, base_type, array_size = ConstructorArgumentParser.is_array_type(param_type)
        if is_array:
            if array_size is not None:
                # Fixed-size array - generate N default values
                base_arg = ConstructorArgumentParser.generate_constructor_arg(base_type, param_name, contract_code, deployer_address)
                return [base_arg] * array_size
            else:
                # Dynamic array - return empty array as safe default
                logger.info(f"Using empty array for {param_name}: {param_type}")
                return []
        
        # Check for bytes types
        is_bytes, bytes_size = ConstructorArgumentParser.is_bytes_type(param_type)
        if is_bytes:
            if bytes_size is not None:
                # Fixed bytes (bytes1-bytes32) - return zero bytes
                zero_bytes = '0x' + ('00' * bytes_size)
                logger.info(f"Using zero bytes for {param_name}: {zero_bytes}")
                return zero_bytes
            else:
                # Dynamic bytes - return empty bytes
                logger.info(f"Using empty bytes for {param_name}")
                return '0x'
        
        # Check for uint types
        is_uint, uint_bits = ConstructorArgumentParser.is_uint_type(param_type)
        if is_uint:
            # Try to extract supply from code for supply-related parameters
            if 'supply' in param_name.lower() or 'amount' in param_name.lower():
                supply_match = re.search(r'(\d+(?:_\d+)*)\s*\*\s*\(10\*\*(\d+)\)', contract_code)
                if supply_match:
                    supply = supply_match.group(1).replace('_', '')
                    decimals = supply_match.group(2)
                    total_supply = int(supply) * (10 ** int(decimals))
                    logger.info(f"Extracted supply for {param_name}: {total_supply}")
                    return total_supply
            
            # Default to 0 for other uint parameters
            logger.info(f"Using 0 for {param_name}: {param_type}")
            return 0
        
        # Check for int types
        is_int, int_bits = ConstructorArgumentParser.is_int_type(param_type)
        if is_int:
            logger.info(f"Using 0 for {param_name}: {param_type}")
            return 0
        
        # Basic types
        if param_type == 'address':
            logger.info(f"Using deployer address for {param_name}: {deployer_address}")
            return deployer_address
        
        elif param_type == 'string':
            # Try to extract from ERC20/ERC721 constructor
            name, symbol = ConstructorArgumentParser.extract_erc20_name_symbol(contract_code)
            if not name:
                name, symbol = ConstructorArgumentParser.extract_erc721_name_symbol(contract_code)
            
            if name and 'name' in param_name.lower():
                logger.info(f"Extracted name for {param_name}: {name}")
                return name
            elif symbol and 'symbol' in param_name.lower():
                logger.info(f"Extracted symbol for {param_name}: {symbol}")
                return symbol
            else:
                logger.info(f"Using empty string for {param_name}")
                return ""
        
        elif param_type == 'bool':
            logger.info(f"Using false for {param_name}")
            return False
        
        # Check for struct types
        is_struct, struct_name = ConstructorArgumentParser.is_struct_type(param_type, contract_code)
        if is_struct:
            logger.info(f"Using empty struct for {param_name}: {param_type}")
            return {}  # Return empty dict for struct (will need to be filled by user)
        
        else:
            # Unknown type - log warning and return safe default
            logger.warning(f"Unknown type '{param_type}' for {param_name}, using empty string")
            return ""
    
    @staticmethod
    def generate_constructor_args(contract_code: str, deployer_address: str) -> List[Any]:
        """
        Generate appropriate constructor arguments for deployment.
        
        Enhanced version supporting all Solidity types including arrays, bytes, etc.
        
        Args:
            contract_code: Solidity source code
            deployer_address: Address of the deployer
            
        Returns:
            List of constructor arguments (typed values, not strings)
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
                arg = ConstructorArgumentParser.generate_constructor_arg(
                    param_type, param_name, contract_code, deployer_address
                )
                args.append(arg)
            
            logger.info(f"Generated constructor args for {contract_name}:")
            for i, ((param_type, param_name), arg) in enumerate(zip(param_types, args)):
                logger.info(f"  [{i}] {param_type} {param_name} = {arg}")
            
            return args
            
        except Exception as e:
            logger.error(f"Error generating constructor args: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    @staticmethod
    def validate_constructor_args(contract_code: str, args: List[Any]) -> Dict[str, Any]:
        """
        Validate that constructor arguments match the contract signature.
        
        Enhanced version supporting all Solidity types.
        
        Args:
            contract_code: Solidity source code
            args: Constructor arguments to validate (typed values)
            
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
                    "actual": len(args),
                    "expected_signature": [f"{t} {n}" for t, n in param_types]
                }
            
            # Validate argument types
            validation_details = []
            for i, (arg, (param_type, param_name)) in enumerate(zip(args, param_types)):
                # Check array types
                is_array, base_type, array_size = ConstructorArgumentParser.is_array_type(param_type)
                if is_array:
                    if not isinstance(arg, list):
                        validation_details.append(f"Expected array for {param_name}, got {type(arg).__name__}")
                    elif array_size is not None and len(arg) != array_size:
                        validation_details.append(f"Expected array of size {array_size} for {param_name}, got {len(arg)}")
                    continue
                
                # Check bytes types
                is_bytes, bytes_size = ConstructorArgumentParser.is_bytes_type(param_type)
                if is_bytes:
                    if not isinstance(arg, (str, bytes)):
                        validation_details.append(f"Expected bytes for {param_name}, got {type(arg).__name__}")
                    elif isinstance(arg, str) and not arg.startswith('0x'):
                        validation_details.append(f"Expected hex bytes (0x...) for {param_name}")
                    continue
                
                # Check uint/int types
                is_uint, _ = ConstructorArgumentParser.is_uint_type(param_type)
                is_int, _ = ConstructorArgumentParser.is_int_type(param_type)
                if is_uint or is_int:
                    if not isinstance(arg, int):
                        validation_details.append(f"Expected integer for {param_name}, got {type(arg).__name__}")
                    continue
                
                # Basic types
                if param_type == 'address':
                    if not isinstance(arg, str):
                        validation_details.append(f"Expected string address for {param_name}")
                    elif not arg.startswith('0x') or len(arg) != 42:
                        validation_details.append(f"Invalid address format for {param_name}: {arg}")
                
                elif param_type == 'string':
                    if not isinstance(arg, str):
                        validation_details.append(f"Expected string for {param_name}, got {type(arg).__name__}")
                
                elif param_type == 'bool':
                    if not isinstance(arg, bool):
                        validation_details.append(f"Expected boolean for {param_name}, got {type(arg).__name__}")
            
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
                "args": args,
                "signature": [f"{t} {n}" for t, n in param_types]
            }
            
        except Exception as e:
            logger.error(f"Error validating constructor args: {e}")
            import traceback
            logger.error(traceback.format_exc())
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
