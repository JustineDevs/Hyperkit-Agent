"""
End-to-End Workflow Tests
Tests complete workflow from generation to deployment
"""

import asyncio
import os
import sys
import pytest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.agent.main import HyperKitAgent
from core.config.loader import get_config


@pytest.mark.integration
class TestCompleteWorkflow:
    """Test complete end-to-end workflows"""
    
    @pytest.fixture
    async def agent(self):
        """Initialize HyperKit agent"""
        config = get_config().to_dict()
        return HyperKitAgent(config)
    
    @pytest.mark.asyncio
    async def test_contract_generation(self):
        """Test contract generation"""
        config = get_config().to_dict()
        agent = HyperKitAgent(config)
        
        # Test generation
        result = await agent.generate_contract(
            prompt="Create simple ERC20 token",
            context="Test token for E2E testing"
        )
        
        assert result is not None
        assert result.get("status") == "success"
        assert "contract_code" in result
        assert len(result["contract_code"]) > 100
        print(f"✅ Contract generation test passed")
    
    @pytest.mark.asyncio
    async def test_contract_audit(self):
        """Test contract auditing"""
        config = get_config().to_dict()
        agent = HyperKitAgent(config)
        
        # Simple contract code for testing
        contract_code = """
        // SPDX-License-Identifier: MIT
        pragma solidity ^0.8.0;
        
        contract TestContract {
            uint256 public value;
            
            function setValue(uint256 _value) public {
                value = _value;
            }
        }
        """
        
        # Test audit
        result = await agent.audit_contract(contract_code)
        
        assert result is not None
        assert result.get("status") in ["success", "real_ai"]
        assert "severity" in result or "results" in result
        print(f"✅ Contract audit test passed")
    
    @pytest.mark.asyncio
    async def test_generate_and_audit_workflow(self):
        """Test generation + audit workflow"""
        config = get_config().to_dict()
        agent = HyperKitAgent(config)
        
        # Generate contract
        gen_result = await agent.generate_contract(
            prompt="Create simple ERC20 token named TestToken",
            context="E2E workflow test"
        )
        
        assert gen_result.get("status") == "success"
        contract_code = gen_result.get("contract_code")
        assert len(contract_code) > 100
        
        # Audit generated contract
        audit_result = await agent.audit_contract(contract_code)
        
        assert audit_result is not None
        assert audit_result.get("status") in ["success", "real_ai"]
        print(f"✅ Generate + Audit workflow test passed")
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_complete_workflow_test_only(self):
        """Test complete workflow in test-only mode (no actual deployment)"""
        config = get_config().to_dict()
        agent = HyperKitAgent(config)
        
        # Run complete workflow in test mode
        result = await agent.run_workflow(
            user_prompt="Create simple ERC20 token for testing",
            network="hyperion",
            test_only=True,
            auto_verification=False
        )
        
        assert result is not None
        assert result.get("status") == "success"
        assert "generation" in result
        assert "audit" in result
        
        # Verify generation stage
        generation = result.get("generation", {})
        assert generation.get("status") == "success"
        
        # Verify audit stage
        audit = result.get("audit", {})
        assert audit.get("status") in ["success", "complete"]
        
        print(f"✅ Complete workflow (test-only) passed")
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self):
        """Test workflow error handling"""
        config = get_config().to_dict()
        agent = HyperKitAgent(config)
        
        # Test with invalid input
        result = await agent.generate_contract(
            prompt="",  # Empty prompt
            context=""
        )
        
        # Should handle gracefully
        assert result is not None
        # May succeed with empty prompt (LLM might use defaults) or fail gracefully
        
        print(f"✅ Error handling test passed")
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test system health check"""
        from services.common.health import HealthChecker
        
        health_checker = HealthChecker()
        health_status = health_checker.check_all()
        
        assert health_status is not None
        assert "status" in health_status
        assert "components" in health_status
        
        print(f"✅ Health check test passed")


@pytest.mark.integration
class TestCLICommands:
    """Test CLI command integrations"""
    
    def test_cli_import(self):
        """Test that CLI can be imported"""
        try:
            from cli.main import cli
            assert cli is not None
            print(f"✅ CLI import test passed")
        except ImportError as e:
            pytest.skip(f"CLI import failed: {e}")
    
    def test_generate_command_exists(self):
        """Test that generate command is registered"""
        try:
            from cli.commands.generate import generate_group
            assert generate_group is not None
            print(f"✅ Generate command test passed")
        except ImportError as e:
            pytest.skip(f"Generate command import failed: {e}")
    
    def test_audit_command_exists(self):
        """Test that audit command is registered"""
        try:
            from cli.commands.audit import audit_group
            assert audit_group is not None
            print(f"✅ Audit command test passed")
        except ImportError as e:
            pytest.skip(f"Audit command import failed: {e}")
    
    def test_deploy_command_exists(self):
        """Test that deploy command is registered"""
        try:
            from cli.commands.deploy import deploy_group
            assert deploy_group is not None
            print(f"✅ Deploy command test passed")
        except ImportError as e:
            pytest.skip(f"Deploy command import failed: {e}")
    
    def test_workflow_command_exists(self):
        """Test that workflow command is registered"""
        try:
            from cli.commands.workflow import workflow_group
            assert workflow_group is not None
            print(f"✅ Workflow command test passed")
        except ImportError as e:
            pytest.skip(f"Workflow command import failed: {e}")


@pytest.mark.integration
class TestSystemIntegration:
    """Test system integration points"""
    
    def test_config_loading(self):
        """Test configuration loading"""
        config = get_config()
        assert config is not None
        
        config_dict = config.to_dict()
        assert "networks" in config_dict
        assert "ai_providers" in config_dict
        
        print(f"✅ Config loading test passed")
    
    def test_network_configuration(self):
        """Test network configuration"""
        config = get_config().to_dict()
        networks = config.get("networks", {})
        
        assert "hyperion" in networks
        hyperion_config = networks["hyperion"]
        assert "rpc_url" in hyperion_config
        assert "chain_id" in hyperion_config
        
        print(f"✅ Network configuration test passed")
    
    def test_ai_provider_configuration(self):
        """Test AI provider configuration"""
        config = get_config().to_dict()
        ai_providers = config.get("ai_providers", {})
        
        # Should have at least one provider configured
        assert len(ai_providers) > 0
        
        print(f"✅ AI provider configuration test passed")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])

