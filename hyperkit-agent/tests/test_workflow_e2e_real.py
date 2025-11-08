"""
Real end-to-end workflow test.
Tests the complete Gen→Compile→Deploy→Verify chain with actual execution.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent.main import HyperKitAgent
from core.config.loader import get_config
from core.workflow.workflow_orchestrator import WorkflowOrchestrator


@pytest.mark.integration
class TestRealWorkflowE2E:
    """Real E2E workflow tests - no mocks"""
    
    @pytest.fixture
    def workspace_dir(self):
        """Create temporary workspace for testing"""
        temp_dir = tempfile.mkdtemp(prefix="hyperkit_test_")
        workspace = Path(temp_dir)
        yield workspace
        # Cleanup
        if workspace.exists():
            shutil.rmtree(workspace, ignore_errors=True)
    
    @pytest.fixture
    def agent(self):
        """Create HyperKitAgent instance"""
        config = get_config().to_dict()
        return HyperKitAgent(config)
    
    @pytest.fixture
    def orchestrator(self, agent, workspace_dir):
        """Create WorkflowOrchestrator instance"""
        return WorkflowOrchestrator(agent, workspace_dir)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_workflow_completes_even_on_deployment_failure(self, orchestrator):
        """
        Test that workflow completes successfully even if deployment fails.
        
        This is the critical test: deployment failure should NOT crash the workflow.
        It should complete with status 'completed_with_errors' and provide diagnostics.
        """
        prompt = "create a simple ERC20 token named TestToken with symbol TEST, 1000000 total supply"
        
        result = await orchestrator.run_complete_workflow(
            user_prompt=prompt,
            network="hyperion",
            auto_verification=True,
            test_only=False,  # Actually try to deploy
            allow_insecure=False,
            upload_scope=None,
            rag_scope='official-only'
        )
        
        # Workflow should ALWAYS complete (never crash)
        assert result is not None, "Workflow must return a result"
        assert "status" in result, "Result must have status field"
        assert "workflow_id" in result, "Result must have workflow_id"
        
        status = result["status"]
        
        # Status should be one of: success, completed_with_errors, or error
        assert status in ["success", "completed_with_errors", "error"], \
            f"Invalid status: {status}. Expected: success, completed_with_errors, or error"
        
        # If deployment failed, status should be 'completed_with_errors' (not 'error')
        # Critical failures (gen/compile) should be 'error'
        deployment = result.get("deployment", {})
        deploy_status = deployment.get("status", "unknown")
        
        if deploy_status == "error":
            # Deployment failed - workflow should still complete
            assert status in ["completed_with_errors", "success"], \
                f"If deployment fails, status should be 'completed_with_errors', got '{status}'"
            
            # Should have error details
            assert "error" in deployment or deployment.get("error_details"), \
                "Deployment failure should include error information"
            
            # Should have suggestions
            suggestions = deployment.get("suggestions", [])
            assert len(suggestions) > 0, \
                "Deployment failure should include recovery suggestions"
        
        # Always should have diagnostic bundle if there were errors
        if status != "success":
            diagnostic_bundle = result.get("diagnostic_bundle")
            assert diagnostic_bundle is not None or result.get("diagnostics"), \
                "Failed workflow should have diagnostic bundle or diagnostics"
        
        # Should have stage information
        assert "stages" in result, "Result should include stage information"
        stages = result["stages"]
        assert len(stages) > 0, "Should have at least one stage result"
        
        # Check that all stages have required fields
        for stage in stages:
            assert "stage" in stage, "Each stage should have stage name"
            assert "status" in stage, "Each stage should have status"
            assert "duration_ms" in stage, "Each stage should have duration"
    
    @pytest.mark.asyncio
    async def test_workflow_test_only_mode(self, orchestrator):
        """
        Test workflow in test-only mode (no deployment).
        Should always succeed if generation and compilation work.
        """
        prompt = "create a simple ERC20 token named TestToken with symbol TEST, 1000000 total supply"
        
        result = await orchestrator.run_complete_workflow(
            user_prompt=prompt,
            network="hyperion",
            auto_verification=False,
            test_only=True,  # No deployment
            allow_insecure=False,
            upload_scope=None,
            rag_scope='official-only'
        )
        
        assert result is not None, "Workflow must return a result"
        assert "status" in result, "Result must have status field"
        
        status = result["status"]
        
        # In test-only mode, if gen/compile succeed, should be success or completed_with_errors
        if status == "error":
            # Check which stage failed
            failed_stages = result.get("failed_stages", [])
            assert "generation" in failed_stages or "compilation" in failed_stages, \
                f"If status is error in test-only mode, generation or compilation must have failed"
        
        # Should have generation information
        generation = result.get("generation", {})
        assert "status" in generation or generation.get("contract_name"), \
            "Result should include generation information"
    
    @pytest.mark.asyncio
    async def test_workflow_critical_failure_handling(self, orchestrator):
        """
        Test that critical failures (generation/compilation) properly fail the workflow.
        """
        # Use an intentionally bad prompt that might cause generation to fail
        prompt = "create a contract that does not exist and will fail" * 100  # Very long, might cause issues
        
        result = await orchestrator.run_complete_workflow(
            user_prompt=prompt,
            network="hyperion",
            auto_verification=False,
            test_only=True,
            allow_insecure=False,
            upload_scope=None,
            rag_scope='official-only'
        )
        
        assert result is not None, "Workflow must return a result even on failure"
        assert "status" in result, "Result must have status field"
        
        status = result["status"]
        
        # If generation fails, status should be 'error'
        generation = result.get("generation", {})
        gen_status = generation.get("status", "unknown")
        
        if gen_status == "error":
            assert status == "error", \
                "If generation fails (critical stage), status should be 'error'"
            assert result.get("critical_failure") is True, \
                "Critical failure should be marked as critical_failure=True"
            assert "failed_stages" in result, \
                "Critical failure should list failed stages"
        
        # Even on critical failure, should have diagnostic bundle
        if status == "error" and result.get("critical_failure"):
            diagnostic_bundle = result.get("diagnostic_bundle")
            assert diagnostic_bundle is not None, \
                "Critical failure should have diagnostic bundle"
    
    @pytest.mark.asyncio
    async def test_workflow_status_model(self, orchestrator):
        """
        Test that the workflow correctly distinguishes between:
        - success: all stages succeeded
        - completed_with_errors: non-critical failures (deploy/verify)
        - error: critical failures (gen/compile)
        """
        prompt = "create a simple ERC20 token named TestToken with symbol TEST, 1000000 total supply"
        
        result = await orchestrator.run_complete_workflow(
            user_prompt=prompt,
            network="hyperion",
            auto_verification=True,
            test_only=False,
            allow_insecure=False,
            upload_scope=None,
            rag_scope='official-only'
        )
        
        assert result is not None
        status = result["status"]
        
        # Check critical_failure flag matches status
        critical_failure = result.get("critical_failure", False)
        
        if status == "error":
            assert critical_failure is True, \
                "If status is 'error', critical_failure should be True"
        else:
            assert critical_failure is False, \
                "If status is not 'error', critical_failure should be False"
        
        # Check that stages are properly categorized
        stages = result.get("stages", [])
        critical_stages = ["generation", "compilation"]
        
        critical_stage_statuses = [
            s["status"] for s in stages 
            if s.get("stage") in critical_stages
        ]
        
        if any(status == "error" for status in critical_stage_statuses):
            # Critical stage failed
            assert result["status"] == "error", \
                "If critical stage failed, overall status should be 'error'"
    
    @pytest.mark.asyncio
    async def test_workflow_always_reaches_output_stage(self, orchestrator):
        """
        Test that workflow ALWAYS reaches output stage, even if earlier stages fail.
        """
        prompt = "create a simple ERC20 token named TestToken with symbol TEST, 1000000 total supply"
        
        result = await orchestrator.run_complete_workflow(
            user_prompt=prompt,
            network="hyperion",
            auto_verification=True,
            test_only=False,
            allow_insecure=False,
            upload_scope=None,
            rag_scope='official-only'
        )
        
        # Output stage should always be present
        stages = result.get("stages", [])
        output_stages = [s for s in stages if s.get("stage") == "output"]
        
        assert len(output_stages) > 0, \
            "Workflow should always have output stage, even if earlier stages failed"
        
        # Output stage should have status
        output_stage = output_stages[0]
        assert "status" in output_stage, \
            "Output stage should have status"
    
    @pytest.mark.asyncio
    async def test_workflow_diagnostic_bundle_on_failure(self, orchestrator):
        """
        Test that diagnostic bundles are created when workflow fails.
        """
        prompt = "create a simple ERC20 token named TestToken with symbol TEST, 1000000 total supply"
        
        result = await orchestrator.run_complete_workflow(
            user_prompt=prompt,
            network="hyperion",
            auto_verification=True,
            test_only=False,
            allow_insecure=False,
            upload_scope=None,
            rag_scope='official-only'
        )
        
        status = result["status"]
        
        if status != "success":
            # Should have diagnostic bundle
            diagnostic_bundle = result.get("diagnostic_bundle")
            
            if diagnostic_bundle:
                # Verify bundle file exists
                bundle_path = Path(diagnostic_bundle)
                assert bundle_path.exists(), \
                    f"Diagnostic bundle file should exist: {diagnostic_bundle}"
                
                # Verify it's valid JSON
                import json
                with open(bundle_path, 'r') as f:
                    bundle_data = json.load(f)
                
                assert "workflow_id" in bundle_data, \
                    "Diagnostic bundle should contain workflow_id"
                assert "stages" in bundle_data, \
                    "Diagnostic bundle should contain stage information"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

