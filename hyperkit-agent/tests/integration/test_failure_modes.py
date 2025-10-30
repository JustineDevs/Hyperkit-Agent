"""
Tests for Common Failure Modes and Recovery Logic

Tests workflow recovery mechanisms for common failure scenarios.
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add workspace to path
workspace_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(workspace_dir))

from core.agent.main import HyperKitAgent
from core.config.loader import get_config
from core.workflow.workflow_orchestrator import WorkflowOrchestrator
from services.dependencies.dependency_manager import DependencyManager


class TestFailureModes:
    """Test common failure modes and recovery logic"""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance"""
        config = get_config().to_dict()
        return HyperKitAgent(config)
    
    @pytest.fixture
    def orchestrator(self, agent):
        """Create orchestrator instance"""
        return WorkflowOrchestrator(agent, workspace_dir)
    
    @pytest.mark.asyncio
    async def test_missing_dependency_recovery(self, orchestrator):
        """Test recovery from missing dependency"""
        # Generate contract with OpenZeppelin import
        context = await orchestrator._create_context("Create an ERC20 token with OpenZeppelin")
        
        # Simulate missing dependency
        contract_code = '''
        pragma solidity ^0.8.20;
        import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
        contract TestToken is ERC20 {
            constructor() ERC20("Test", "TST") {}
        }
        '''
        context.contract_code = contract_code
        
        # Run dependency resolution (should auto-install)
        await orchestrator._stage_dependency_resolution(context)
        
        # Verify dependency was installed
        assert len(context.detected_dependencies) > 0
        assert any("openzeppelin" in dep.get("name", "").lower() for dep in context.detected_dependencies)
        
        # Verify installation succeeded
        failed = [
            name for name, (success, _) in context.installed_dependencies.items()
            if not success
        ]
        assert len(failed) == 0, f"Dependencies failed to install: {failed}"
    
    @pytest.mark.asyncio
    async def test_compilation_error_recovery(self, orchestrator):
        """Test recovery from compilation errors"""
        # Generate contract with intentional error
        context = await orchestrator._create_context("Create a simple token")
        
        # Contract with syntax error (should be auto-fixed)
        contract_code = '''
        pragma solidity ^0.8.20;
        contract BrokenToken {
            function _beforeTokenTransfer(address from, address to, uint256 amount) override internal {
                // This override doesn't exist in base - should be removed
            }
        }
        '''
        
        # Sanitize should fix override issue
        sanitized = orchestrator._sanitize_contract_code(contract_code)
        
        # Verify override was removed
        assert "_beforeTokenTransfer" not in sanitized or "override" not in sanitized
    
    @pytest.mark.asyncio
    async def test_variable_shadowing_recovery(self, orchestrator):
        """Test recovery from variable shadowing errors"""
        # Contract with shadowing issue
        contract_code = '''
        pragma solidity ^0.8.20;
        contract ShadowToken {
            function cap() public view returns (uint256) {
                return 1000000;
            }
            
            constructor(uint256 cap) {
                // cap shadows function cap() - should be fixed to _cap
            }
        }
        '''
        
        # Sanitize should fix shadowing
        sanitized = orchestrator._sanitize_contract_code(contract_code)
        
        # Verify parameter was renamed
        assert "constructor(uint256 cap)" not in sanitized or "constructor(uint256 _cap)" in sanitized
    
    @pytest.mark.asyncio
    async def test_constructor_args_recovery(self, orchestrator):
        """Test recovery from invalid constructor arguments"""
        from services.deployment.constructor_parser import ConstructorArgumentParser
        
        parser = ConstructorArgumentParser()
        
        # Contract requiring cap > 0
        contract_code = '''
        pragma solidity ^0.8.20;
        contract CappedToken {
            uint256 public cap;
            
            constructor(uint256 _cap) {
                require(_cap > 0, "Cap must be greater than 0");
                cap = _cap;
            }
        }
        '''
        
        # Generate constructor args
        args = parser.generate_constructor_args(contract_code, "CappedToken")
        
        # Verify cap is > 0
        assert "cap" in args or "_cap" in args
        cap_value = args.get("cap") or args.get("_cap")
        assert cap_value is not None
        assert cap_value > 0, f"Cap value must be > 0, got {cap_value}"
    
    @pytest.mark.asyncio
    async def test_network_failure_recovery(self, orchestrator):
        """Test recovery from network/RPC failures"""
        # This would test retry logic for RPC failures
        # For now, verify error handling exists
        context = await orchestrator._create_context("Create a token")
        
        # Simulate network error
        try:
            # This should handle errors gracefully
            result = await orchestrator._stage_deployment(
                context,
                network="invalid_network",
                allow_insecure=False
            )
            # Should either succeed (if network config exists) or fail gracefully
            assert result is not None
        except Exception as e:
            # Error should be caught and logged, not crash
            assert "network" in str(e).lower() or "rpc" in str(e).lower() or "configured" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_audit_failure_recovery(self, orchestrator):
        """Test recovery from audit failures"""
        context = await orchestrator._create_context("Create a token")
        
        # Generate contract
        await orchestrator._stage_generation(context, "Create an ERC20 token")
        
        # Run audit
        await orchestrator._stage_audit(context)
        
        # Verify audit results exist
        assert context.audit_results is not None
        
        # If audit fails, workflow should still continue (non-fatal)
        # Deployment should respect allow_insecure flag
        if context.audit_results.get("severity") == "high":
            # High severity should block deployment unless allow_insecure=True
            result = await orchestrator._stage_deployment(
                context,
                network="hyperion",
                allow_insecure=False
            )
            # Should be skipped
            assert result.get("status") == "skipped"
    
    @pytest.mark.asyncio
    async def test_workflow_context_persistence(self, orchestrator):
        """Test workflow context is properly persisted"""
        context = await orchestrator._create_context("Create a token")
        
        # Add some data
        context.contract_code = "pragma solidity ^0.8.20; contract Test {}"
        context.contract_name = "Test"
        
        # Save context
        orchestrator.context_manager.save_context(context)
        
        # Reload context
        reloaded = orchestrator.context_manager.load_context(context.workflow_id)
        
        assert reloaded is not None
        assert reloaded.workflow_id == context.workflow_id
        assert reloaded.contract_code == context.contract_code
        assert reloaded.contract_name == context.contract_name
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, orchestrator):
        """Test retry mechanism for transient failures"""
        from core.workflow.error_handler import handle_error_with_retry
        
        attempt_count = 0
        
        async def failing_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Transient failure")
            return {"status": "success"}
        
        # Should retry and eventually succeed
        result = await handle_error_with_retry(
            failing_operation,
            max_retries=3,
            retry_delay=0.1
        )
        
        assert result["status"] == "success"
        assert attempt_count == 3
    
    @pytest.mark.asyncio
    async def test_error_diagnostic_bundle(self, orchestrator):
        """Test diagnostic bundle creation on errors"""
        context = await orchestrator._create_context("Create a token")
        
        # Simulate an error
        context.add_stage_result(
            orchestrator.context_manager.PipelineStage.GENERATION,
            "error",
            error="Test error",
            error_type="test_error"
        )
        
        # Save diagnostic bundle
        bundle_path = orchestrator.context_manager.save_diagnostic_bundle(context)
        
        assert bundle_path.exists()
        
        # Verify bundle contains error info
        import json
        with open(bundle_path, 'r') as f:
            bundle = json.load(f)
        
        assert "errors" in bundle
        assert len(bundle["errors"]) > 0

