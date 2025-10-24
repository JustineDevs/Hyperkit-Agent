"""
Performance tests and benchmarks
"""
import pytest
import time
import subprocess
import sys
from pathlib import Path


class TestPerformanceBenchmarks:
    """Test performance benchmarks for CLI operations"""
    
    def test_generation_performance(self):
        """Test contract generation performance"""
        start_time = time.time()
        
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "generate",
            "Create a simple ERC20 token",
            "--output", "artifacts/generated/performance_test.sol"
        ], capture_output=True, text=True)
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        # Should complete within reasonable time (30 seconds)
        assert generation_time < 30
        assert result.returncode == 0
        
        # Clean up
        Path("artifacts/generated/performance_test.sol").unlink(missing_ok=True)
    
    def test_audit_performance(self):
        """Test audit performance"""
        # First generate a contract
        contract_file = "artifacts/generated/audit_performance_test.sol"
        Path("artifacts/generated").mkdir(parents=True, exist_ok=True)
        
        subprocess.run([
            sys.executable, "-m", "hyperagent", "generate",
            "Create a simple ERC20 token",
            "--output", contract_file
        ], capture_output=True, text=True)
        
        # Test audit performance
        start_time = time.time()
        
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "audit", contract_file
        ], capture_output=True, text=True)
        
        end_time = time.time()
        audit_time = end_time - start_time
        
        # Should complete within reasonable time (60 seconds)
        assert audit_time < 60
        assert result.returncode == 0
        
        # Clean up
        Path(contract_file).unlink(missing_ok=True)
    
    def test_workflow_performance(self):
        """Test complete workflow performance"""
        output_dir = "artifacts/workflows/performance_test"
        
        start_time = time.time()
        
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "workflow",
            "Create a simple ERC20 token",
            "--test-only",
            "--output-dir", output_dir
        ], capture_output=True, text=True)
        
        end_time = time.time()
        workflow_time = end_time - start_time
        
        # Should complete within reasonable time (45 seconds)
        assert workflow_time < 45
        assert result.returncode == 0
        
        # Clean up
        import shutil
        shutil.rmtree(output_dir, ignore_errors=True)
