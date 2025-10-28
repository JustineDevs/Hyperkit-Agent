"""
Test Enhanced Error Messages

Tests for Step 3 of deploy fix: User-friendly error reporting with examples
"""

import pytest
from services.deployment.error_messages import DeploymentErrorMessages


class TestConstructorValidationErrors:
    """Test constructor validation error messages"""
    
    def test_basic_validation_error(self):
        """Test basic validation error message generation"""
        error = "Expected 3 arguments, got 2"
        provided_args = ["0x123...", 1000000]
        expected_params = [
            {"name": "owner", "type": "address"},
            {"name": "supply", "type": "uint256"},
            {"name": "name", "type": "string"}
        ]
        
        result = DeploymentErrorMessages.constructor_validation_failed(
            error, provided_args, expected_params, "MyToken"
        )
        
        assert result["success"] is False
        assert "Constructor validation failed" in result["error"]
        assert result["contract_name"] == "MyToken"
        assert result["provided_args"] == provided_args
        assert len(result["suggestions"]) > 0
        assert "examples" in result
    
    def test_error_with_address_type(self):
        """Test error message includes address format guidance"""
        error = "Type mismatch for parameter owner"
        provided_args = ["invalid_address"]
        expected_params = [
            {"name": "owner", "type": "address"}
        ]
        
        result = DeploymentErrorMessages.constructor_validation_failed(
            error, provided_args, expected_params, "MyContract"
        )
        
        # Should include address format suggestions
        suggestions_text = " ".join(result["suggestions"])
        assert "0x" in suggestions_text.lower()
        assert "address" in suggestions_text.lower()
    
    def test_error_with_array_type(self):
        """Test error message includes array format guidance"""
        error = "Type mismatch for parameter owners"
        provided_args = []
        expected_params = [
            {"name": "owners", "type": "address[]"}
        ]
        
        result = DeploymentErrorMessages.constructor_validation_failed(
            error, provided_args, expected_params, "MultiSig"
        )
        
        # Should include array format suggestions
        suggestions_text = " ".join(result["suggestions"])
        assert "array" in suggestions_text.lower() or "[" in suggestions_text
    
    def test_examples_generation(self):
        """Test that examples are generated correctly"""
        error = "Validation failed"
        provided_args = []
        expected_params = [
            {"name": "owner", "type": "address"},
            {"name": "supply", "type": "uint256"},
            {"name": "name", "type": "string"}
        ]
        
        result = DeploymentErrorMessages.constructor_validation_failed(
            error, provided_args, expected_params, "MyToken"
        )
        
        assert "examples" in result
        examples = result["examples"]
        
        # Should have CLI examples
        assert "cli_inline" in examples
        assert "cli_file" in examples
        assert "hyperagent deploy" in examples["cli_inline"]
        
        # Should have JSON format examples
        assert "json_array_format" in examples
        assert "json_named_format" in examples
        
        # JSON examples should be properly formatted
        assert "content" in examples["json_array_format"]
        assert "content" in examples["json_named_format"]


class TestFileLoadErrors:
    """Test file load error messages"""
    
    def test_file_not_found_error(self):
        """Test error message for missing file"""
        file_path = "nonexistent.json"
        error = FileNotFoundError(f"No such file: {file_path}")
        
        result = DeploymentErrorMessages.file_load_failed(
            file_path, error
        )
        
        assert result["success"] is False
        assert file_path in result["file_path"]
        assert result["error_type"] == "FileNotFoundError"
        assert len(result["suggestions"]) > 0
        
        # Should suggest checking file path
        suggestions_text = " ".join(result["suggestions"])
        assert "path" in suggestions_text.lower()
    
    def test_json_decode_error(self):
        """Test error message for invalid JSON"""
        import json
        file_path = "invalid.json"
        error = json.JSONDecodeError("Expecting value", "doc", 0)
        
        result = DeploymentErrorMessages.file_load_failed(
            file_path, error
        )
        
        assert result["success"] is False
        assert result["error_type"] == "JSONDecodeError"
        
        # Should suggest JSON formatting help
        suggestions_text = " ".join(result["suggestions"])
        assert "json" in suggestions_text.lower()
        assert any("bracket" in s.lower() or "comma" in s.lower() 
                  for s in result["suggestions"])
    
    def test_file_error_with_expected_params(self):
        """Test that expected params are included in error"""
        file_path = "test.json"
        error = Exception("Test error")
        expected_params = [
            {"name": "owner", "type": "address"},
            {"name": "supply", "type": "uint256"}
        ]
        
        result = DeploymentErrorMessages.file_load_failed(
            file_path, error, expected_params
        )
        
        # Should list expected parameters
        suggestions_text = " ".join(result["suggestions"])
        assert "owner" in suggestions_text
        assert "address" in suggestions_text


class TestFoundryErrors:
    """Test Foundry installation error messages"""
    
    def test_foundry_not_available(self):
        """Test Foundry not available error message"""
        result = DeploymentErrorMessages.foundry_not_available()
        
        assert result["success"] is False
        assert "Foundry" in result["error"]
        assert result["required_tool"] == "Foundry"
        assert len(result["installation_steps"]) > 0
        assert "documentation" in result
        
        # Should have installation instructions
        steps_text = " ".join(result["installation_steps"])
        assert "curl" in steps_text or "install" in steps_text.lower()
        
        # Should suggest alternatives
        assert "alternative" in result
        assert len(result["suggestions"]) > 0


class TestDeploymentErrors:
    """Test deployment failure error messages"""
    
    def test_gas_error(self):
        """Test gas-related error message"""
        result = DeploymentErrorMessages.deployment_failed(
            "out of gas",
            "MyContract",
            133717
        )
        
        assert result["success"] is False
        assert result["contract_name"] == "MyContract"
        assert result["chain_id"] == 133717
        
        # Should have gas-specific suggestions
        suggestions_text = " ".join(result["suggestions"])
        assert "gas" in suggestions_text.lower()
    
    def test_insufficient_funds_error(self):
        """Test insufficient funds error message"""
        result = DeploymentErrorMessages.deployment_failed(
            "insufficient balance for transfer",
            "MyContract",
            1
        )
        
        # Should have balance-specific suggestions
        suggestions_text = " ".join(result["suggestions"])
        assert "balance" in suggestions_text.lower() or "fund" in suggestions_text.lower()
    
    def test_rpc_error(self):
        """Test RPC connection error message"""
        result = DeploymentErrorMessages.deployment_failed(
            "rpc connection timeout",
            "MyContract",
            1
        )
        
        # Should have RPC-specific suggestions
        suggestions_text = " ".join(result["suggestions"])
        assert "rpc" in suggestions_text.lower() or "connection" in suggestions_text.lower()
    
    def test_revert_error(self):
        """Test contract revert error message"""
        result = DeploymentErrorMessages.deployment_failed(
            "execution reverted",
            "MyContract",
            1
        )
        
        # Should have revert-specific suggestions
        suggestions_text = " ".join(result["suggestions"])
        assert "revert" in suggestions_text.lower() or "constructor" in suggestions_text.lower()
    
    def test_error_with_transaction_hash(self):
        """Test error message includes transaction hash if available"""
        tx_hash = "0x1234567890abcdef"
        result = DeploymentErrorMessages.deployment_failed(
            "unknown error",
            "MyContract",
            1,
            tx_hash
        )
        
        assert "transaction_hash" in result
        assert result["transaction_hash"] == tx_hash
        assert "explorer" in result.get("explorer_note", "").lower()


class TestExampleGeneration:
    """Test example generation for different parameter types"""
    
    def test_address_example(self):
        """Test address parameter example"""
        params = [{"name": "owner", "type": "address"}]
        examples = DeploymentErrorMessages._generate_constructor_examples(
            params, "Test"
        )
        
        # Should contain address example with 0x prefix
        assert "0x" in examples["cli_inline"]
    
    def test_uint_example(self):
        """Test uint parameter example"""
        params = [{"name": "amount", "type": "uint256"}]
        examples = DeploymentErrorMessages._generate_constructor_examples(
            params, "Test"
        )
        
        # Should contain numeric value
        assert any(char.isdigit() for char in examples["cli_inline"])
    
    def test_string_example(self):
        """Test string parameter example"""
        params = [{"name": "name", "type": "string"}]
        examples = DeploymentErrorMessages._generate_constructor_examples(
            params, "Test"
        )
        
        # Should contain quoted string
        json_content = examples["json_named_format"]["content"]
        assert '"' in json_content
    
    def test_array_example(self):
        """Test array parameter example"""
        params = [{"name": "owners", "type": "address[]"}]
        examples = DeploymentErrorMessages._generate_constructor_examples(
            params, "Test"
        )
        
        # Should contain array notation
        assert "[" in examples["cli_inline"] and "]" in examples["cli_inline"]
    
    def test_complex_constructor_example(self):
        """Test complex constructor with multiple types"""
        params = [
            {"name": "owner", "type": "address"},
            {"name": "supply", "type": "uint256"},
            {"name": "name", "type": "string"},
            {"name": "active", "type": "bool"},
            {"name": "admins", "type": "address[]"}
        ]
        examples = DeploymentErrorMessages._generate_constructor_examples(
            params, "ComplexContract"
        )
        
        # Should have all format options
        assert "cli_inline" in examples
        assert "cli_file" in examples
        assert "json_array_format" in examples
        assert "json_named_format" in examples
        
        # Named format should include all parameter names
        named_json = examples["json_named_format"]["content"]
        assert "owner" in named_json
        assert "supply" in named_json
        assert "name" in named_json
        assert "active" in named_json
        assert "admins" in named_json


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

