"""
Test Enhanced Constructor Parser

Tests for all Solidity type support in constructor_parser.py
"""

import pytest
from services.deployment.constructor_parser import ConstructorArgumentParser


class TestEnhancedConstructorParser:
    """Test enhanced constructor parser with complex types"""
    
    def test_simple_erc20_contract(self):
        """Test with simple ERC20 contract (backward compatibility)"""
        contract = '''
        contract MyToken is ERC20 {
            constructor(address initialOwner) ERC20("MyToken", "MTK") {
                _mint(initialOwner, 1000000 * 10**18);
            }
        }
        '''
        
        deployer = "0x1234567890123456789012345678901234567890"
        args = ConstructorArgumentParser.generate_constructor_args(contract, deployer)
        
        assert len(args) == 1
        assert args[0] == deployer
    
    def test_contract_with_arrays(self):
        """Test contract with array parameters"""
        contract = '''
        contract MultiSig {
            constructor(address[] memory owners, uint256 required) {
                // ...
            }
        }
        '''
        
        deployer = "0x1234567890123456789012345678901234567890"
        args = ConstructorArgumentParser.generate_constructor_args(contract, deployer)
        
        assert len(args) == 2
        assert isinstance(args[0], list)  # Dynamic array
        assert isinstance(args[1], int)   # uint256
    
    def test_contract_with_fixed_array(self):
        """Test contract with fixed-size array"""
        contract = '''
        contract FixedArray {
            constructor(uint256[3] memory values) {
                // ...
            }
        }
        '''
        
        deployer = "0x1234567890123456789012345678901234567890"
        args = ConstructorArgumentParser.generate_constructor_args(contract, deployer)
        
        assert len(args) == 1
        assert isinstance(args[0], list)
        assert len(args[0]) == 3  # Fixed size 3
        assert all(isinstance(v, int) for v in args[0])
    
    def test_contract_with_bytes(self):
        """Test contract with bytes parameters"""
        contract = '''
        contract BytesContract {
            constructor(bytes memory data, bytes32 hash) {
                // ...
            }
        }
        '''
        
        deployer = "0x1234567890123456789012345678901234567890"
        args = ConstructorArgumentParser.generate_constructor_args(contract, deployer)
        
        assert len(args) == 2
        assert args[0] == '0x'  # Empty bytes
        assert args[1].startswith('0x')
        assert len(args[1]) == 66  # 0x + 64 hex chars = 32 bytes
    
    def test_contract_with_uint_variants(self):
        """Test contract with different uint types"""
        contract = '''
        contract UintVariants {
            constructor(uint8 a, uint16 b, uint32 c, uint256 d) {
                // ...
            }
        }
        '''
        
        deployer = "0x1234567890123456789012345678901234567890"
        args = ConstructorArgumentParser.generate_constructor_args(contract, deployer)
        
        assert len(args) == 4
        assert all(isinstance(arg, int) for arg in args)
        assert all(arg == 0 for arg in args)  # Default to 0
    
    def test_contract_with_mixed_types(self):
        """Test contract with complex mixed types"""
        contract = '''
        contract Complex {
            constructor(
                address owner,
                string memory name,
                uint256 supply,
                bool paused,
                address[] memory admins,
                bytes32 salt
            ) {
                // ...
            }
        }
        '''
        
        deployer = "0x1234567890123456789012345678901234567890"
        args = ConstructorArgumentParser.generate_constructor_args(contract, deployer)
        
        assert len(args) == 6
        assert args[0] == deployer  # address
        assert isinstance(args[1], str)  # string
        assert isinstance(args[2], int)  # uint256
        assert isinstance(args[3], bool)  # bool
        assert isinstance(args[4], list)  # address[]
        assert args[5].startswith('0x')  # bytes32
    
    def test_type_detection_array(self):
        """Test array type detection"""
        parser = ConstructorArgumentParser()
        
        # Dynamic array
        is_array, base_type, size = parser.is_array_type("uint256[]")
        assert is_array == True
        assert base_type == "uint256"
        assert size is None
        
        # Fixed array
        is_array, base_type, size = parser.is_array_type("address[5]")
        assert is_array == True
        assert base_type == "address"
        assert size == 5
        
        # Not an array
        is_array, base_type, size = parser.is_array_type("uint256")
        assert is_array == False
    
    def test_type_detection_bytes(self):
        """Test bytes type detection"""
        parser = ConstructorArgumentParser()
        
        # Dynamic bytes
        is_bytes, size = parser.is_bytes_type("bytes")
        assert is_bytes == True
        assert size is None
        
        # Fixed bytes
        is_bytes, size = parser.is_bytes_type("bytes32")
        assert is_bytes == True
        assert size == 32
        
        # Not bytes
        is_bytes, size = parser.is_bytes_type("string")
        assert is_bytes == False
    
    def test_type_detection_uint(self):
        """Test uint type detection"""
        parser = ConstructorArgumentParser()
        
        # Standard uint
        is_uint, bits = parser.is_uint_type("uint256")
        assert is_uint == True
        assert bits == 256
        
        # uint alias
        is_uint, bits = parser.is_uint_type("uint")
        assert is_uint == True
        assert bits == 256
        
        # uint8
        is_uint, bits = parser.is_uint_type("uint8")
        assert is_uint == True
        assert bits == 8
        
        # Not uint
        is_uint, bits = parser.is_uint_type("int256")
        assert is_uint == False
    
    def test_validation_success(self):
        """Test successful validation"""
        contract = '''
        contract Test {
            constructor(address owner, uint256 amount) {
                // ...
            }
        }
        '''
        
        args = [
            "0x1234567890123456789012345678901234567890",
            1000000
        ]
        
        result = ConstructorArgumentParser.validate_constructor_args(contract, args)
        
        assert result["success"] == True
        assert result["param_count"] == 2
    
    def test_validation_mismatch_count(self):
        """Test validation with wrong argument count"""
        contract = '''
        contract Test {
            constructor(address owner, uint256 amount) {
                // ...
            }
        }
        '''
        
        args = ["0x1234567890123456789012345678901234567890"]  # Only 1 arg
        
        result = ConstructorArgumentParser.validate_constructor_args(contract, args)
        
        assert result["success"] == False
        assert "Argument count mismatch" in result["error"]
        assert result["expected"] == 2
        assert result["actual"] == 1
    
    def test_validation_wrong_types(self):
        """Test validation with wrong argument types"""
        contract = '''
        contract Test {
            constructor(address owner, uint256 amount, bool active) {
                // ...
            }
        }
        '''
        
        args = [
            "invalid_address",  # Wrong format
            "not_a_number",      # Wrong type
            "not_a_bool"         # Wrong type
        ]
        
        result = ConstructorArgumentParser.validate_constructor_args(contract, args)
        
        assert result["success"] == False
        assert "validation failed" in result["error"].lower()
        assert len(result["details"]) > 0
    
    def test_supply_extraction(self):
        """Test that supply values are extracted from contract code"""
        contract = '''
        contract Token {
            uint256 constant INITIAL_SUPPLY = 1_000_000 * (10**18);
            
            constructor(address owner, uint256 initialSupply) {
                _mint(owner, INITIAL_SUPPLY);
            }
        }
        '''
        
        deployer = "0x1234567890123456789012345678901234567890"
        args = ConstructorArgumentParser.generate_constructor_args(contract, deployer)
        
        assert len(args) == 2
        assert args[0] == deployer
        assert args[1] == 1_000_000 * (10**18)  # Should extract supply
    
    def test_erc20_name_symbol_extraction(self):
        """Test ERC20 name/symbol extraction"""
        contract = '''
        contract MyToken is ERC20 {
            constructor() ERC20("GameX Token", "GAMEX") {
                _mint(msg.sender, 1000000);
            }
        }
        '''
        
        name, symbol = ConstructorArgumentParser.extract_erc20_name_symbol(contract)
        
        assert name == "GameX Token"
        assert symbol == "GAMEX"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

