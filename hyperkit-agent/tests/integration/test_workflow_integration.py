"""
Integration tests for workflow commands
"""
import pytest
import subprocess
import sys
import json
from pathlib import Path


class TestWorkflowIntegration:
    """Test end-to-end workflow integration"""
    
    def test_workflow_test_only_mode(self):
        """Test workflow in test-only mode"""
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "workflow", 
            "Create a simple ERC20 token", "--test-only"
        ], capture_output=True, text=True)
        
        # Should complete successfully in test-only mode
        assert result.returncode == 0
        assert "Workflow Completion Summary" in result.stdout
    
    def test_generate_command(self):
        """Test contract generation"""
        output_file = "artifacts/generated/test_generation.sol"
        Path("artifacts/generated").mkdir(parents=True, exist_ok=True)
        
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "generate",
            "Create a simple ERC20 token",
            "--output", output_file
        ], capture_output=True, text=True)
        
        # Should generate contract successfully
        assert result.returncode == 0
        assert Path(output_file).exists()
        
        # Clean up
        Path(output_file).unlink(missing_ok=True)
    
    def test_audit_command(self):
        """Test audit command with generated contract"""
        # First generate a contract
        test_contract = "artifacts/generated/test_audit.sol"
        Path("artifacts/generated").mkdir(parents=True, exist_ok=True)
        
        # Generate
        subprocess.run([
            sys.executable, "-m", "hyperagent", "generate",
            "Create a simple ERC20 token",
            "--output", test_contract
        ], capture_output=True, text=True)
        
        # Then audit it
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "audit", test_contract
        ], capture_output=True, text=True)
        
        # Should audit successfully
        assert result.returncode == 0
        assert "Security Audit Report" in result.stdout or "Findings" in result.stdout
        
        # Clean up
        Path(test_contract).unlink(missing_ok=True)
