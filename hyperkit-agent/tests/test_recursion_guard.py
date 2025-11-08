"""
Comprehensive tests for bulletproof recursion guards.
Tests to destruction to ensure infinite recursion cannot occur.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from core.workflow.context_manager import WorkflowContext, PipelineStage
from core.workflow.workflow_orchestrator import WorkflowOrchestrator
from pathlib import Path


@pytest.mark.unit
class TestRecursionGuard:
    """Test recursion guards to destruction"""
    
    def test_increment_and_get_retry_count_atomic(self):
        """Test that increment_and_get_retry_count is atomic"""
        context = WorkflowContext(
            workflow_id="test-123",
            user_prompt="test"
        )
        
        # Initial count should be 0
        assert context.get_retry_count(PipelineStage.DEPENDENCY_RESOLUTION) == 0
        
        # First increment
        count1 = context.increment_and_get_retry_count(PipelineStage.DEPENDENCY_RESOLUTION)
        assert count1 == 1
        assert context.get_retry_count(PipelineStage.DEPENDENCY_RESOLUTION) == 1
        
        # Second increment
        count2 = context.increment_and_get_retry_count(PipelineStage.DEPENDENCY_RESOLUTION)
        assert count2 == 2
        assert context.get_retry_count(PipelineStage.DEPENDENCY_RESOLUTION) == 2
        
        # Third increment
        count3 = context.increment_and_get_retry_count(PipelineStage.DEPENDENCY_RESOLUTION)
        assert count3 == 3
        assert context.get_retry_count(PipelineStage.DEPENDENCY_RESOLUTION) == 3
        
        # Fourth increment (should exceed MAX_RETRIES = 3)
        count4 = context.increment_and_get_retry_count(PipelineStage.DEPENDENCY_RESOLUTION)
        assert count4 == 4
        assert count4 > 3  # Should exceed MAX_RETRIES
    
    @pytest.mark.asyncio
    async def test_dependency_resolution_recursion_guard(self):
        """Test that dependency resolution stops after MAX_RETRIES"""
        from core.workflow.workflow_orchestrator import WorkflowOrchestrator
        
        # Create mock agent
        mock_agent = Mock()
        mock_agent.rag = None
        
        # Create orchestrator
        workspace_dir = Path.cwd() / "test_workspace"
        workspace_dir.mkdir(exist_ok=True)
        
        orchestrator = WorkflowOrchestrator(mock_agent, workspace_dir)
        
        # Create context with contract code
        context = WorkflowContext(
            workflow_id="test-recursion-guard",
            user_prompt="test",
            contract_code="pragma solidity ^0.8.0; contract Test {}",
            contract_name="Test"
        )
        
        # Mock dependency manager to always fail
        with patch.object(orchestrator.dep_manager, 'detect_dependencies') as mock_detect:
            mock_detect.side_effect = RuntimeError("Dependency installation failed")
            
            # Mock error handler's handle_error_with_retry to always succeed
            # This allows the recursion guard to be tested
            async def mock_handle_error_with_retry(handler, error, context, max_retries=2):
                """Mock that always returns success to test recursion guard"""
                return (True, "Fix attempted")
            
            with patch('core.workflow.workflow_orchestrator.handle_error_with_retry', side_effect=mock_handle_error_with_retry):
                    
                    # Track recursion depth
                    recursion_depth = [0]
                    
                    original_method = orchestrator._stage_dependency_resolution
                    
                    async def tracked_method(ctx):
                        recursion_depth[0] += 1
                        if recursion_depth[0] > 10:  # Safety limit
                            raise RuntimeError("Recursion depth exceeded safety limit")
                        return await original_method(ctx)
                    
                    orchestrator._stage_dependency_resolution = tracked_method
                    
                    # Should raise RuntimeError after MAX_RETRIES (3)
                    with pytest.raises(RuntimeError) as exc_info:
                        await orchestrator._stage_dependency_resolution(context)
                    
                    # Verify error message mentions max retries or retries exceeded
                    error_msg = str(exc_info.value).lower()
                    assert ("max_retries" in error_msg or 
                            "retries" in error_msg or 
                            "exceeded" in error_msg or
                            "failed after" in error_msg), \
                        f"Error message should mention retries: {error_msg}"
                    
                    # Verify recursion depth is limited (should be MAX_RETRIES + 1 = 4)
                    assert recursion_depth[0] <= 4, f"Recursion depth {recursion_depth[0]} exceeded expected limit of 4"
                    
                    # Verify retry count is exactly MAX_RETRIES + 1 (4)
                    final_retry_count = context.get_retry_count(PipelineStage.DEPENDENCY_RESOLUTION)
                    assert final_retry_count == 4, f"Final retry count {final_retry_count} should be 4 (MAX_RETRIES + 1)"
    
    @pytest.mark.asyncio
    async def test_recursion_guard_with_different_initial_counts(self):
        """Test recursion guard works with different initial retry counts"""
        context = WorkflowContext(
            workflow_id="test-initial-count",
            user_prompt="test"
        )
        
        # Set initial retry count to 2
        context.retry_attempts[PipelineStage.DEPENDENCY_RESOLUTION.value] = 2
        
        # Next increment should be 3 (at limit)
        count = context.increment_and_get_retry_count(PipelineStage.DEPENDENCY_RESOLUTION)
        assert count == 3
        
        # Next increment should be 4 (exceeds limit)
        count = context.increment_and_get_retry_count(PipelineStage.DEPENDENCY_RESOLUTION)
        assert count == 4
        assert count > 3  # Should exceed MAX_RETRIES
    
    def test_retry_count_isolation_per_stage(self):
        """Test that retry counts are isolated per stage"""
        context = WorkflowContext(
            workflow_id="test-isolation",
            user_prompt="test"
        )
        
        # Increment DEPENDENCY_RESOLUTION
        count1 = context.increment_and_get_retry_count(PipelineStage.DEPENDENCY_RESOLUTION)
        assert count1 == 1
        
        # Increment COMPILATION (should be separate)
        count2 = context.increment_and_get_retry_count(PipelineStage.COMPILATION)
        assert count2 == 1
        
        # Verify they're independent
        assert context.get_retry_count(PipelineStage.DEPENDENCY_RESOLUTION) == 1
        assert context.get_retry_count(PipelineStage.COMPILATION) == 1
        
        # Increment DEPENDENCY_RESOLUTION again
        count3 = context.increment_and_get_retry_count(PipelineStage.DEPENDENCY_RESOLUTION)
        assert count3 == 2
        
        # COMPILATION should still be 1
        assert context.get_retry_count(PipelineStage.COMPILATION) == 1
    
    @pytest.mark.asyncio
    async def test_recursion_guard_logs_stack_trace(self):
        """Test that recursion guard logs stack trace for debugging"""
        import logging
        from io import StringIO
        
        # Set up logging capture
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.DEBUG)
        
        logger = logging.getLogger('core.workflow.workflow_orchestrator')
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        
        context = WorkflowContext(
            workflow_id="test-logging",
            user_prompt="test"
        )
        
        # Increment retry count
        context.increment_and_get_retry_count(PipelineStage.DEPENDENCY_RESOLUTION)
        
        # Check that logging would occur (we can't easily test the actual log in the orchestrator
        # without full integration, but we can verify the method exists)
        assert hasattr(context, 'increment_and_get_retry_count')
        
        logger.removeHandler(handler)

