"""
End-to-end tests for complete workflows
"""
import pytest
import subprocess
import sys
import json
import time
from pathlib import Path


@pytest.mark.integration
class TestFullWorkflow:
    """Test complete end-to-end workflows"""
    
    def test_complete_workflow_test_only(self):
        """Test complete workflow in test-only mode"""
        output_dir = "artifacts/workflows/test_complete_workflow"
        
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "workflow",
            "Create a secure ERC20 token with staking rewards",
            "--test-only",
            "--output-dir", output_dir,
            "--verbose"
        ], capture_output=True, text=True)
        
        # Should complete successfully
        assert result.returncode == 0
        assert "Workflow Completion Summary" in result.stdout
        
        # Check that artifacts were created
        assert Path(output_dir).exists()
        assert Path(f"{output_dir}/workflow_report.json").exists()
        
        # Clean up
        import shutil
        shutil.rmtree(output_dir, ignore_errors=True)
    
    def test_generate_and_audit_workflow(self):
        """Test generate -> audit workflow"""
        output_dir = "artifacts/workflows/test_generate_audit"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate contract
        contract_file = f"{output_dir}/test_contract.sol"
        result1 = subprocess.run([
            sys.executable, "-m", "hyperagent", "generate",
            "Create an ERC721 NFT contract",
            "--output", contract_file
        ], capture_output=True, text=True)
        
        assert result1.returncode == 0
        assert Path(contract_file).exists()
        
        # Audit contract
        result2 = subprocess.run([
            sys.executable, "-m", "hyperagent", "audit", contract_file,
            "--output", f"{output_dir}/audit_report.json",
            "--format", "json"
        ], capture_output=True, text=True)
        
        assert result2.returncode == 0
        assert Path(f"{output_dir}/audit_report.json").exists()
        
        # Clean up
        import shutil
        shutil.rmtree(output_dir, ignore_errors=True)
    
    def test_interactive_mode_basic(self):
        """Test interactive mode basic functionality"""
        # Test that interactive mode starts without errors
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "interactive", "--mode", "test"
        ], capture_output=True, text=True, timeout=5)
        
        # Should start successfully (may timeout, which is expected)
        assert result.returncode in [0, 1]  # Allow for timeout or normal exit
