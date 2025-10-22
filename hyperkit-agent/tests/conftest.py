"""
Test configuration and fixtures for HyperKit AI Agent tests
"""

import pytest
import os
from unittest.mock import Mock, patch
from pathlib import Path

# Add the parent directory to the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Set test API keys for all tests
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["GOOGLE_API_KEY"] = "test-google-key"
    os.environ["TEST_MODE"] = "true"
    os.environ["HYPERION_RPC_URL"] = "https://hyperion-testnet.metisdevops.link"
    
    # Mock external API calls to prevent actual API calls during testing
    with patch('openai.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Test contract code"))]
        )
        mock_openai.return_value = mock_client
        
        with patch('google.generativeai.GenerativeModel') as mock_gemini:
            mock_model = Mock()
            mock_model.generate_content.return_value.text = "Test contract code"
            mock_gemini.return_value = mock_model
            
            yield

@pytest.fixture
def mock_config():
    """Provide a mock configuration for testing."""
    return {
        "openai_api_key": "test-openai-key",
        "google_api_key": "test-google-key",
        "networks": {
            "hyperion": {
                "rpc_url": "https://hyperion-testnet.metisdevops.link",
                "chain_id": 133717,
                "explorer_url": "https://hyperion-testnet-explorer.metisdevops.link"
            }
        },
        "test_mode": True
    }

@pytest.fixture
def mock_contract_code():
    """Provide sample contract code for testing."""
    return """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TestContract {
    string public name;
    uint256 public value;
    
    constructor(string memory _name, uint256 _value) {
        name = _name;
        value = _value;
    }
    
    function updateValue(uint256 _newValue) public {
        value = _newValue;
    }
}
"""

@pytest.fixture
def mock_audit_result():
    """Provide mock audit result for testing."""
    return {
        "status": "success",
        "findings": [
            {
                "severity": "low",
                "title": "Test finding",
                "description": "This is a test finding",
                "line": 10
            }
        ],
        "severity": "low",
        "total_findings": 1
    }

@pytest.fixture
def mock_deployment_result():
    """Provide mock deployment result for testing."""
    return {
        "status": "success",
        "success": True,
        "address": "0x1234567890123456789012345678901234567890",
        "tx_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcde",
        "network": "hyperion",
        "gas_used": 100000,
        "gas_price": "20000000000"
    }
