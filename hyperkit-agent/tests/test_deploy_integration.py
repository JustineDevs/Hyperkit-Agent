"""
Integration Tests for Deploy Command Fix

End-to-end tests for P1 Deploy Fix - validates complete workflow
from constructor parsing through deployment with error handling.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from services.deployment.deployer import MultiChainDeployer
from services.deployment.constructor_parser import ConstructorArgumentParser


@pytest.mark.integration
class TestDeployIntegration:
    """Integration tests for the complete deploy workflow"""
    
    @pytest.fixture
    def deployer(self):
        """Create a deployer instance with Foundry mocked"""
        with patch('services.deployment.deployer.FoundryManager'):
            deployer = MultiChainDeployer()
            deployer.foundry_available = True
            return deployer
    
    @pytest.fixture
    def simple_erc20(self):
        """Simple ERC20 contract for testing"""
        return '''
        pragma solidity ^0.8.0;
        
        contract SimpleToken {
            constructor(address owner, uint256 initialSupply) {
                // Token setup
            }
        }
        '''
    
    @pytest.fixture
    def complex_contract(self):
        """Complex contract with multiple parameter types"""
        return '''
        pragma solidity ^0.8.0;
        
        contract ComplexContract {
            constructor(
                address owner,
                uint256 supply,
                string memory name,
                bool active,
                address[] memory admins
            ) {
                // Complex setup
            }
        }
        '''
    
    def test_auto_detection_workflow(self, deployer, simple_erc20):
        """Test complete workflow with auto-detected constructor args"""
        parser = ConstructorArgumentParser()
        
        # Step 1: Parse constructor
        result = parser.extract_constructor_params(simple_erc20)
        assert result is not None
        contract_name, params = result
        assert len(params) == 2
        assert params[0][1] == 'owner'  # (type, name) tuple
        assert params[1][1] == 'initialSupply'
        
        # Step 2: Generate args
        args = parser.generate_constructor_args(
            simple_erc20,
            "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        )
        assert len(args) == 2
        assert args[0].startswith('0x')
        assert isinstance(args[1], int)
        
        # Verifies that parsing and generation work correctly
        # Note: Full validation tested in other tests
    
    def test_cli_args_override_workflow(self, deployer, simple_erc20):
        """Test workflow with CLI-provided constructor args"""
        custom_args = ["0x1234567890123456789012345678901234567890", 1000000]
        
        # Mock Foundry deployer
        with patch.object(deployer, 'foundry_deployer') as mock_foundry:
            mock_foundry.deploy.return_value = {
                "success": True,
                "contract_address": "0xABC...",
                "transaction_hash": "0xDEF..."
            }
            
            # Deploy with custom args
            result = deployer.deploy(
                contract_source_code=simple_erc20,
                rpc_url="http://localhost:8545",
                chain_id=1,
                contract_name="SimpleToken",
                constructor_args=custom_args
            )
            
            # Verify deployment called with custom args
            assert result["success"] is True
            mock_foundry.deploy.assert_called_once()
            call_args = mock_foundry.deploy.call_args[1]
            assert call_args["constructor_args"] == custom_args
    
    def test_json_file_workflow(self, deployer, complex_contract):
        """Test workflow with JSON file constructor args"""
        # Create JSON file with array format
        args_data = [
            "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",  # owner
            1000000,  # supply
            "Test Token",  # name
            True,  # active
            [  # admins
                "0x1111111111111111111111111111111111111111",
                "0x2222222222222222222222222222222222222222"
            ]
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(args_data, f)
            temp_file = f.name
        
        try:
            # Test file loading mechanism
            args = deployer.load_constructor_args_from_file(
                temp_file,
                complex_contract,
                deployer_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            )
            
            # Verify args were loaded correctly
            assert len(args) == 5
            assert args[0] == args_data[0]
            assert args[1] == args_data[1]
            assert args[2] == args_data[2]
            assert args[3] == args_data[3]
            assert args[4] == args_data[4]
        finally:
            Path(temp_file).unlink()
    
    def test_validation_error_workflow(self, deployer, simple_erc20):
        """Test complete error handling workflow for validation failures"""
        # Provide wrong number of args
        invalid_args = ["0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"]  # Missing supply
        
        result = deployer.deploy(
            contract_source_code=simple_erc20,
            rpc_url="http://localhost:8545",
            chain_id=1,
            contract_name="SimpleToken",
            constructor_args=invalid_args
        )
        
        # Verify error response
        assert result["success"] is False
        assert "error" in result
        assert "suggestions" in result
        assert "examples" in result
        
        # Verify examples were generated
        examples = result["examples"]
        assert "cli_inline" in examples
        assert "json_named_format" in examples
    
    def test_file_not_found_workflow(self, deployer, simple_erc20):
        """Test error handling for missing JSON file"""
        result = deployer.deploy(
            contract_source_code=simple_erc20,
            rpc_url="http://localhost:8545",
            chain_id=1,
            contract_name="SimpleToken",
            constructor_file="nonexistent.json"
        )
        
        # Verify error response
        assert result["success"] is False
        assert "FileNotFoundError" in result["error_type"]
        assert len(result["suggestions"]) > 0
    
    def test_invalid_json_workflow(self, deployer, simple_erc20):
        """Test error handling for invalid JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json ")
            temp_file = f.name
        
        try:
            result = deployer.deploy(
                contract_source_code=simple_erc20,
                rpc_url="http://localhost:8545",
                chain_id=1,
                contract_name="SimpleToken",
                constructor_file=temp_file
            )
            
            # Verify error response
            assert result["success"] is False
            assert "JSONDecodeError" in result["error_type"]
            assert any("json" in s.lower() for s in result["suggestions"])
        finally:
            Path(temp_file).unlink()
    
    def test_type_mismatch_workflow(self, deployer, simple_erc20):
        """Test error handling for type mismatches"""
        # Provide string instead of uint
        invalid_args = ["0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "not_a_number"]
        
        result = deployer.deploy(
            contract_source_code=simple_erc20,
            rpc_url="http://localhost:8545",
            chain_id=1,
            contract_name="SimpleToken",
            constructor_args=invalid_args
        )
        
        # Verify error response with guidance (may include address/type guidance)
        assert result["success"] is False
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0  # Should have suggestions
    
    def test_foundry_not_available_workflow(self, simple_erc20):
        """Test error handling when Foundry is not available"""
        with patch('services.deployment.deployer.FoundryManager'):
            deployer = MultiChainDeployer()
            deployer.foundry_available = False
            
            result = deployer.deploy(
                contract_source_code=simple_erc20,
                rpc_url="http://localhost:8545",
                chain_id=1,
                contract_name="SimpleToken"
            )
            
            # Verify Foundry error message
            assert result["success"] is False
            assert "Foundry" in result["error"]
            assert "installation_steps" in result
            assert len(result["installation_steps"]) > 0


class TestComplexTypeIntegration:
    """Integration tests for complex Solidity types"""
    
    @pytest.fixture
    def deployer(self):
        """Create a deployer instance with Foundry mocked"""
        with patch('services.deployment.deployer.FoundryManager'):
            deployer = MultiChainDeployer()
            deployer.foundry_available = True
            return deployer
    
    def test_array_type_integration(self, deployer):
        """Test integration with array constructor parameters"""
        contract = '''
        contract MultiSig {
            constructor(address[] memory owners, uint256 required) {
                // Setup
            }
        }
        '''
        
        args_data = {
            "owners": [
                "0x1111111111111111111111111111111111111111",
                "0x2222222222222222222222222222222222222222"
            ],
            "required": 2
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(args_data, f)
            temp_file = f.name
        
        try:
            with patch.object(deployer, 'foundry_deployer') as mock_foundry:
                mock_foundry.deploy.return_value = {"success": True}
                
                result = deployer.deploy(
                    contract_source_code=contract,
                    rpc_url="http://localhost:8545",
                    constructor_file=temp_file
                )
                
                assert result["success"] is True
                call_args = mock_foundry.deploy.call_args[1]["constructor_args"]
                assert isinstance(call_args[0], list)
                assert len(call_args[0]) == 2
        finally:
            Path(temp_file).unlink()
    
    def test_bytes_type_integration(self, deployer):
        """Test integration with bytes constructor parameters"""
        contract = '''
        contract BytesContract {
            constructor(bytes32 data, bytes memory dynamicData) {
                // Setup
            }
        }
        '''
        
        with patch.object(deployer, 'foundry_deployer') as mock_foundry:
            mock_foundry.deploy.return_value = {"success": True}
            
            # Auto-detect should handle bytes types
            result = deployer.deploy(
                contract_source_code=contract,
                rpc_url="http://localhost:8545",
                deployer_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            )
            
            # Should not fail validation
            assert result["success"] is True
    
    def test_fixed_array_integration(self, deployer):
        """Test integration with fixed-size arrays"""
        contract = '''
        contract FixedArrayContract {
            constructor(uint256[3] memory values) {
                // Setup
            }
        }
        '''
        
        args = [[100, 200, 300]]
        
        with patch.object(deployer, 'foundry_deployer') as mock_foundry:
            mock_foundry.deploy.return_value = {"success": True}
            
            result = deployer.deploy(
                contract_source_code=contract,
                rpc_url="http://localhost:8545",
                constructor_args=args
            )
            
            assert result["success"] is True


class TestErrorMessageIntegration:
    """Integration tests for error message generation"""
    
    def test_error_includes_examples(self):
        """Test that errors include usage examples"""
        with patch('services.deployment.deployer.FoundryManager'):
            deployer = MultiChainDeployer()
            deployer.foundry_available = True
            
            contract = '''
            contract Test {
                constructor(address owner, uint256 supply) {}
            }
            '''
            
            # Provide wrong args
            result = deployer.deploy(
                contract_source_code=contract,
                rpc_url="http://localhost:8545",
                constructor_args=["wrong"]
            )
            
            # Error should include examples
            assert result["success"] is False
            assert "examples" in result
            assert "cli_inline" in result["examples"]
            
            # Examples should match the contract
            assert "owner" in str(result["examples"])
            assert "supply" in str(result["examples"])
    
    def test_error_includes_expected_signature(self):
        """Test that errors show expected constructor signature"""
        with patch('services.deployment.deployer.FoundryManager'):
            deployer = MultiChainDeployer()
            deployer.foundry_available = True
            
            contract = '''
            contract Test {
                constructor(address owner, uint256 supply, string memory name) {}
            }
            '''
            
            result = deployer.deploy(
                contract_source_code=contract,
                rpc_url="http://localhost:8545",
                constructor_args=["0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"]
            )
            
            # Should show expected signature
            assert result["success"] is False
            assert "expected_signature" in result
            assert "owner" in result["expected_signature"]
            assert "supply" in result["expected_signature"]
            assert "name" in result["expected_signature"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

