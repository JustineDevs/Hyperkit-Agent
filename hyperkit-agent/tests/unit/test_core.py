"""
HyperKit AI Agent - Unit Tests
Test cases for core functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json

# Import the modules to test
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent.main import HyperKitAgent
from core.tools.utils import (
    validate_solidity_code,
    extract_contract_info,
    calculate_code_metrics,
    generate_contract_hash,
)
from services.generation.generator import ContractGenerator
from services.audit.auditor import SmartContractAuditor
from services.deployment.deployer import MultiChainDeployer
from services.rag.retriever import RAGRetriever


class TestHyperKitAgent:
    """Test cases for the main HyperKit Agent."""

    @pytest.fixture
    def agent(self):
        """Create a test agent instance."""
        config = {
            "openai_api_key": "test-key",
            "networks": {"hyperion": "https://test-rpc.com"},
        }
        return HyperKitAgent(config)

    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent is not None
        assert agent.config is not None
        assert "generate" in agent.tools
        assert "audit" in agent.tools
        assert "deploy" in agent.tools

    @pytest.mark.asyncio
    async def test_generate_contract(self, agent):
        """Test contract generation."""
        with patch(
            "core.llm.router.HybridLLMRouter.route"
        ) as mock_route:
            mock_route.return_value = "pragma solidity ^0.8.0;\n\ncontract Test {\n    string public name = \"Test Contract\";\n}"

            result = await agent.generate_contract("Create a simple contract")

            assert result["status"] == "success"
            assert "contract_code" in result
            assert "pragma solidity" in result["contract_code"]

    @pytest.mark.asyncio
    async def test_audit_contract(self, agent):
        """Test contract auditing."""
        with patch("services.audit.auditor.SmartContractAuditor.audit") as mock_audit:
            mock_audit.return_value = {"findings": [], "severity": "low"}

            result = await agent.audit_contract("contract Test {}")

            assert result["status"] == "success"
            assert result["severity"] == "low"

    @pytest.mark.asyncio
    async def test_deploy_contract(self, agent):
        """Test contract deployment."""
        # Set a test private key
        agent.config["DEFAULT_PRIVATE_KEY"] = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        
        with patch(
            "services.deployment.deployer.MultiChainDeployer.deploy"
        ) as mock_deploy:
            mock_deploy.return_value = {
                "success": True,
                "address": "0x123",
                "tx_hash": "0xabc",
            }

            result = await agent.deploy_contract("pragma solidity ^0.8.0;\n\ncontract Test {\n    string public name = \"Test Contract\";\n}", "hyperion")

            assert result["status"] == "success"
            assert result["network"] == "hyperion"

    @pytest.mark.asyncio
    async def test_run_workflow_success(self, agent):
        """Test successful workflow execution."""
        with patch.object(
            agent, "generate_contract", new_callable=AsyncMock
        ) as mock_gen, patch.object(
            agent, "audit_contract", new_callable=AsyncMock
        ) as mock_audit, patch.object(
            agent, "deploy_contract", new_callable=AsyncMock
        ) as mock_deploy:

            mock_gen.return_value = {
                "status": "success",
                "contract_code": "contract Test {}",
            }
            mock_audit.return_value = {
                "status": "success",
                "severity": "low",
                "results": {},
            }
            mock_deploy.return_value = {
                "status": "success",
                "deployment": {"address": "0x123"},
            }

            result = await agent.run_workflow("Create a simple contract")

            assert result["status"] == "success"
            assert result["workflow"] == "complete"

    @pytest.mark.asyncio
    async def test_run_workflow_audit_failed(self, agent):
        """Test workflow with failed audit."""
        with patch.object(
            agent, "generate_contract", new_callable=AsyncMock
        ) as mock_gen, patch.object(
            agent, "audit_contract", new_callable=AsyncMock
        ) as mock_audit:

            mock_gen.return_value = {
                "status": "success",
                "contract_code": "contract Test {}",
            }
            mock_audit.return_value = {
                "status": "success",
                "severity": "critical",
                "results": {},
            }

            result = await agent.run_workflow("Create a simple contract")

            assert result["status"] == "audit_failed"
            assert result["workflow"] == "stopped_at_audit"


class TestContractGenerator:
    """Test cases for contract generation."""

    @pytest.fixture
    def generator(self):
        """Create a test generator instance."""
        return ContractGenerator("test-key", "openai")

    def test_generator_initialization(self, generator):
        """Test generator initialization."""
        assert generator is not None
        assert generator.api_key == "test-key"
        assert generator.provider == "openai"
        assert generator.templates is not None

    def test_determine_contract_type(self, generator):
        """Test contract type determination."""
        assert generator._determine_contract_type("Create a token") == "token"
        assert generator._determine_contract_type("Create an NFT") == "nft"
        assert generator._determine_contract_type("Create a vault") == "defi_vault"

    def test_get_available_templates(self, generator):
        """Test getting available templates."""
        templates = generator.get_available_templates()
        assert "token" in templates
        assert "nft" in templates
        assert "defi_vault" in templates

    def test_get_template(self, generator):
        """Test getting specific template."""
        token_template = generator.get_template("token")
        assert token_template is not None
        assert "contract" in token_template


class TestSmartContractAuditor:
    """Test cases for smart contract auditing."""

    @pytest.fixture
    def auditor(self):
        """Create a test auditor instance."""
        return SmartContractAuditor()

    def test_auditor_initialization(self, auditor):
        """Test auditor initialization."""
        assert auditor is not None
        assert auditor.severity_weights is not None
        assert "critical" in auditor.severity_weights

    @pytest.mark.asyncio
    async def test_custom_patterns(self, auditor):
        """Test custom pattern analysis."""
        contract_code = """
        contract Test {
            function withdraw() public {
                msg.sender.call{value: amount}("");
            }
            
            function badRandom() public view returns (uint) {
                return block.timestamp;
            }
        }
        """

        result = await auditor._run_custom_patterns(contract_code)

        assert result["status"] == "success"
        assert "findings" in result
        # Should find at least the block.timestamp pattern
        assert len(result["findings"]) >= 1

    def test_calculate_severity(self, auditor):
        """Test severity calculation."""
        findings = [
            {"severity": "critical"},
            {"severity": "high"},
            {"severity": "medium"},
        ]

        severity = auditor._calculate_severity(findings)
        assert severity in ["critical", "high", "medium", "low"]

    def test_get_audit_summary(self, auditor):
        """Test audit summary generation."""
        audit_results = {
            "findings": [
                {"severity": "high", "description": "Test finding"},
                {"severity": "medium", "description": "Another finding"},
            ],
            "tools_used": ["slither", "custom"],
            "severity": "high",
        }

        summary = auditor.get_audit_summary(audit_results)

        assert "total_findings" in summary
        assert "severity_distribution" in summary
        assert "recommendations" in summary
        assert summary["total_findings"] == 2


class TestMultiChainDeployer:
    """Test cases for multi-chain deployment."""

    @pytest.fixture
    def deployer(self):
        """Create a test deployer instance."""
        return MultiChainDeployer()

    def test_deployer_initialization(self, deployer):
        """Test deployer initialization."""
        assert deployer is not None
        assert deployer.networks is not None
        assert "hyperion" in deployer.networks
        assert "metis" in deployer.networks
        assert "lazai" in deployer.networks

    def test_get_supported_networks(self, deployer):
        """Test getting supported networks."""
        networks = deployer.get_supported_networks()
        assert "hyperion" in networks
        assert "metis" in networks
        assert "lazai" in networks
        assert len(networks) == 3  # Exactly 3 networks supported

    def test_get_network_info(self, deployer):
        """Test getting network information."""
        info = deployer.get_network_info("hyperion")
        assert "rpc_url" in info
        assert "chain_id" in info
        assert "explorer" in info

    @pytest.mark.asyncio
    async def test_estimate_gas(self, deployer):
        """Test gas estimation."""
        contract_code = "contract Test {}"

        with patch.object(deployer, "_compile_contract") as mock_compile:
            mock_compile.return_value = {"success": True, "bytecode": "0x123456"}

            result = await deployer.estimate_gas(contract_code, "hyperion")

            assert result["status"] == "success"
            assert "estimated_gas" in result
            assert "gas_price" in result


class TestRAGRetriever:
    """Test cases for RAG knowledge retrieval."""

    @pytest.fixture
    def rag(self):
        """Create a test RAG instance."""
        return RAGRetriever()

    def test_rag_initialization(self, rag):
        """Test RAG initialization."""
        assert rag is not None
        assert rag.knowledge_base is not None
        assert "security_patterns" in rag.knowledge_base

    def test_keyword_retrieval(self, rag):
        """Test keyword-based retrieval."""
        query = "reentrancy protection"
        result = rag._keyword_retrieval(query, k=3)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_calculate_relevance_score(self, rag):
        """Test relevance score calculation."""
        query = "reentrancy"
        item_data = {
            "description": "Use ReentrancyGuard to prevent reentrancy attacks",
            "tags": ["security", "reentrancy"],
            "example": "contract Test is ReentrancyGuard {}",
        }

        score = rag._calculate_relevance_score(query, item_data)
        assert score > 0

    def test_search_knowledge(self, rag):
        """Test knowledge search."""
        results = rag.search_knowledge("token", category="defi_patterns")

        assert isinstance(results, list)
        if results:
            assert "category" in results[0]
            assert "name" in results[0]
            assert "description" in results[0]

    def test_get_knowledge_categories(self, rag):
        """Test getting knowledge categories."""
        categories = rag.get_knowledge_categories()

        assert isinstance(categories, list)
        assert "security_patterns" in categories
        assert "defi_patterns" in categories


class TestUtils:
    """Test cases for utility functions."""

    def test_validate_solidity_code(self):
        """Test Solidity code validation."""
        valid_code = """
        // SPDX-License-Identifier: MIT
        pragma solidity ^0.8.0;
        
        contract Test {
            function test() public {}
        }
        """

        result = validate_solidity_code(valid_code)

        assert result["valid"] == True
        assert len(result["errors"]) == 0

    def test_extract_contract_info(self):
        """Test contract information extraction."""
        contract_code = """
        // SPDX-License-Identifier: MIT
        pragma solidity ^0.8.0;
        
        import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
        
        contract MyToken is ERC20 {
            event Transfer(address from, address to, uint256 amount);
            
            modifier onlyOwner() {
                require(msg.sender == owner);
                _;
            }
            
            function mint() public onlyOwner {}
        }
        """

        info = extract_contract_info(contract_code)

        assert info["contract_name"] == "MyToken"
        assert "ERC20" in info["inheritance"]
        assert "mint" in info["functions"]
        assert "Transfer" in info["events"]
        assert "onlyOwner" in info["modifiers"]
        assert "@openzeppelin" in info["imports"][0]

    def test_calculate_code_metrics(self):
        """Test code metrics calculation."""
        contract_code = """
        contract Test {
            function test1() public {}
            function test2() public {}
            event TestEvent();
        }
        """

        metrics = calculate_code_metrics(contract_code)

        assert metrics["total_lines"] > 0
        assert metrics["functions_count"] == 2
        assert metrics["events_count"] == 1
        assert metrics["complexity_score"] > 0

    def test_generate_contract_hash(self):
        """Test contract hash generation."""
        code1 = "contract Test {}"
        code2 = "contract Test {}"
        code3 = "contract Test { function test() {} }"

        hash1 = generate_contract_hash(code1)
        hash2 = generate_contract_hash(code2)
        hash3 = generate_contract_hash(code3)

        assert hash1 == hash2  # Same code should produce same hash
        assert hash1 != hash3  # Different code should produce different hash
        assert len(hash1) == 64  # SHA-256 hash length


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
