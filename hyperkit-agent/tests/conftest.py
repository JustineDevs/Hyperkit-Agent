"""
Test configuration and fixtures for HyperKit AI Agent tests
"""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

# Add the parent directory to the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Set test API keys for all tests
    os.environ["OPENAI_API_KEY"] = "test-openai-key"  # Required for Alith SDK
    os.environ["GOOGLE_API_KEY"] = "test-google-key"
    os.environ["PINATA_API_KEY"] = "test-pinata-key"  # Required for IPFS Pinata RAG
    os.environ["PINATA_SECRET_KEY"] = "test-pinata-secret"  # Required for IPFS Pinata RAG
    os.environ["ALITH_ENABLED"] = "true"
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
            
            # Mock Alith SDK (ONLY AI agent)
            with patch('alith.Agent') as mock_alith:
                mock_alith_agent = Mock()
                mock_alith_agent.analyze_gas = AsyncMock(return_value={"gas_optimizations": []})
                mock_alith_agent.generate_contract = AsyncMock(return_value="contract Test {}")
                mock_alith_agent.audit_contract = AsyncMock(return_value={"status": "success", "findings": []})
                mock_alith.return_value = mock_alith_agent
                
                yield

@pytest.fixture
def mock_config():
    """Provide a mock configuration for testing."""
    return {
        "openai_api_key": "test-openai-key",  # Required for Alith SDK (ONLY AI agent)
        "google_api_key": "test-google-key",
        "PINATA_API_KEY": "test-pinata-key",  # Required for IPFS Pinata RAG (exclusive)
        "PINATA_SECRET_KEY": "test-pinata-secret",  # Required for IPFS Pinata RAG
        "ALITH_ENABLED": True,
        "networks": {
            "hyperion": {
                "rpc_url": "https://hyperion-testnet.metisdevops.link",
                "chain_id": 133717,  # Correct chain ID
                "explorer_url": "https://hyperion-testnet-explorer.metisdevops.link"
            },
            "lazai": {
                "rpc_url": "https://rpc.lazai.network/testnet",
                "chain_id": 9001,  # Correct chain ID (LazAI is network-only, NOT AI agent)
                "explorer_url": "https://testnet-explorer.lazai.network"
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
