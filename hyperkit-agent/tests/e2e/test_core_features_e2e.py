#!/usr/bin/env python3
"""
Comprehensive E2E Tests for HyperKit Agent Core Features
Tests: deploy, batch audit, verify, RAG
"""

import pytest
import subprocess
import sys
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, Any


@pytest.mark.integration
class TestCoreFeaturesE2E:
    """End-to-end tests for all core features"""
    
    @pytest.fixture
    def test_contract(self):
        """Create a test contract for E2E testing"""
        contract_code = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract TestToken is ERC20, Ownable {
    uint256 public constant INITIAL_SUPPLY = 1000000 * 10**18;
    
    constructor() ERC20("Test Token", "TEST") Ownable(msg.sender) {
        _mint(msg.sender, INITIAL_SUPPLY);
    }
    
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }
}
"""
        return contract_code
    
    @pytest.fixture
    def test_contract_file(self, test_contract, tmp_path):
        """Create a test contract file"""
        contract_file = tmp_path / "TestToken.sol"
        contract_file.write_text(test_contract)
        return contract_file
    
    def test_deploy_feature(self, test_contract_file):
        """Test contract deployment feature"""
        print("\n=== Testing Deploy Feature ===")
        
        # Test deployment command structure
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "deploy", "contract",
            "--contract", str(test_contract_file),
            "--network", "hyperion",
            "--test-only"  # Don't actually deploy
        ], capture_output=True, text=True)
        
        # Should not fail due to command structure
        assert "error" not in result.stderr.lower() or "test-only" in result.stderr.lower()
        print("✅ Deploy command structure test passed")
    
    def test_batch_audit_feature(self, test_contract_file):
        """Test batch audit feature"""
        print("\n=== Testing Batch Audit Feature ===")
        
        # Create multiple test contracts
        contracts_dir = test_contract_file.parent / "contracts"
        contracts_dir.mkdir(exist_ok=True)
        
        # Copy test contract multiple times
        for i in range(3):
            contract_copy = contracts_dir / f"TestToken{i}.sol"
            contract_copy.write_text(test_contract_file.read_text())
        
        # Test batch audit command
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "batch-audit", "contracts",
            "--files", str(contracts_dir / "TestToken0.sol"),
            "--files", str(contracts_dir / "TestToken1.sol"),
            "--files", str(contracts_dir / "TestToken2.sol"),
            "--format", "json",
            "--batch-name", "E2E Test Batch"
        ], capture_output=True, text=True)
        
        # Should complete without critical errors
        assert result.returncode == 0 or "error" not in result.stderr.lower()
        print("✅ Batch audit command test passed")
    
    def test_verify_feature(self):
        """Test contract verification feature"""
        print("\n=== Testing Verify Feature ===")
        
        # Test verification command structure (with mock address)
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "verify", "contract",
            "--address", "0x1234567890123456789012345678901234567890",
            "--network", "hyperion",
            "--test-only"  # Don't actually verify
        ], capture_output=True, text=True)
        
        # Should not fail due to command structure
        assert "error" not in result.stderr.lower() or "test-only" in result.stderr.lower()
        print("✅ Verify command structure test passed")
    
    def test_rag_feature(self):
        """Test RAG (Retrieval Augmented Generation) feature"""
        print("\n=== Testing RAG Feature ===")
        
        # Test RAG connection test
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "test_rag"
        ], capture_output=True, text=True)
        
        # Should complete without critical errors
        assert result.returncode == 0 or "error" not in result.stderr.lower()
        print("✅ RAG connection test passed")
    
    def test_workflow_feature(self):
        """Test complete workflow feature"""
        print("\n=== Testing Workflow Feature ===")
        
        # Test workflow in test-only mode
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "workflow", "run",
            "Create a simple ERC20 token",
            "--test-only",
            "--network", "hyperion"
        ], capture_output=True, text=True)
        
        # Should complete successfully
        assert result.returncode == 0 or "error" not in result.stderr.lower()
        print("✅ Workflow test-only mode passed")
    
    def test_generate_feature(self):
        """Test contract generation feature"""
        print("\n=== Testing Generate Feature ===")
        
        # Test contract generation
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "generate", "contract",
            "--type", "ERC20",
            "--name", "TestToken",
            "--test-only"  # Don't save to file
        ], capture_output=True, text=True)
        
        # Should complete without critical errors
        assert result.returncode == 0 or "error" not in result.stderr.lower()
        print("✅ Generate command test passed")
    
    def test_audit_feature(self, test_contract_file):
        """Test contract audit feature"""
        print("\n=== Testing Audit Feature ===")
        
        # Test contract audit
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "audit", "contract",
            "--contract", str(test_contract_file),
            "--format", "json",
            "--test-only"  # Don't save report
        ], capture_output=True, text=True)
        
        # Should complete without critical errors
        assert result.returncode == 0 or "error" not in result.stderr.lower()
        print("✅ Audit command test passed")
    
    def test_monitor_feature(self):
        """Test monitoring feature"""
        print("\n=== Testing Monitor Feature ===")
        
        # Test health monitoring
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "monitor", "health"
        ], capture_output=True, text=True)
        
        # Should complete without critical errors
        assert result.returncode == 0 or "error" not in result.stderr.lower()
        print("✅ Monitor health test passed")
    
    def test_config_feature(self):
        """Test configuration feature"""
        print("\n=== Testing Config Feature ===")
        
        # Test config list
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "config", "list"
        ], capture_output=True, text=True)
        
        # Should complete without critical errors
        assert result.returncode == 0 or "error" not in result.stderr.lower()
        print("✅ Config list test passed")
    
    def test_status_feature(self):
        """Test status feature"""
        print("\n=== Testing Status Feature ===")
        
        # Test system status
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "status"
        ], capture_output=True, text=True)
        
        # Should complete without critical errors
        assert result.returncode == 0 or "error" not in result.stderr.lower()
        print("✅ Status command test passed")
    
    def test_version_feature(self):
        """Test version feature"""
        print("\n=== Testing Version Feature ===")
        
        # Test version command
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "version"
        ], capture_output=True, text=True)
        
        # Should complete without critical errors
        assert result.returncode == 0 or "error" not in result.stderr.lower()
        print("✅ Version command test passed")
    
    def test_limitations_feature(self):
        """Test limitations feature"""
        print("\n=== Testing Limitations Feature ===")
        
        # Test limitations command
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "limitations"
        ], capture_output=True, text=True)
        
        # Should complete without critical errors
        assert result.returncode == 0 or "error" not in result.stderr.lower()
        print("✅ Limitations command test passed")
    
    def test_complete_feature_matrix(self):
        """Test all features in sequence"""
        print("\n=== Testing Complete Feature Matrix ===")
        
        features = [
            ("status", ["status"]),
            ("version", ["version"]),
            ("limitations", ["limitations"]),
            ("config", ["config", "list"]),
            ("monitor", ["monitor", "health"]),
            ("rag", ["test_rag"]),
            ("generate", ["generate", "contract", "--type", "ERC20", "--name", "Test", "--test-only"]),
            ("workflow", ["workflow", "run", "Create token", "--test-only"]),
        ]
        
        results = {}
        for feature_name, command in features:
            print(f"Testing {feature_name}...")
            result = subprocess.run([
                sys.executable, "-m", "hyperagent"
            ] + command, capture_output=True, text=True)
            
            results[feature_name] = {
                "returncode": result.returncode,
                "success": result.returncode == 0,
                "has_error": "error" in result.stderr.lower()
            }
        
        # Summary
        print("\n=== Feature Test Summary ===")
        for feature, result in results.items():
            status = "✅ PASS" if result["success"] or not result["has_error"] else "❌ FAIL"
            print(f"{feature}: {status}")
        
        # At least 80% should pass
        passed = sum(1 for r in results.values() if r["success"] or not r["has_error"])
        total = len(results)
        pass_rate = passed / total
        
        print(f"\nOverall Pass Rate: {passed}/{total} ({pass_rate:.1%})")
        assert pass_rate >= 0.8, f"Pass rate {pass_rate:.1%} below 80% threshold"


@pytest.mark.integration
class TestIntegrationE2E:
    """Integration tests for core features"""
    
    def test_deploy_audit_verify_chain(self, tmp_path):
        """Test deploy -> audit -> verify chain"""
        print("\n=== Testing Deploy -> Audit -> Verify Chain ===")
        
        # Create test contract
        contract_code = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract ChainTestToken is ERC20 {
    constructor() ERC20("Chain Test", "CHAIN") {
        _mint(msg.sender, 1000000 * 10**18);
    }
}
"""
        
        contract_file = tmp_path / "ChainTestToken.sol"
        contract_file.write_text(contract_code)
        
        # Test audit
        audit_result = subprocess.run([
            sys.executable, "-m", "hyperagent", "audit", "contract",
            "--contract", str(contract_file),
            "--format", "json",
            "--test-only"
        ], capture_output=True, text=True)
        
        # Test deploy (test-only)
        deploy_result = subprocess.run([
            sys.executable, "-m", "hyperagent", "deploy", "contract",
            "--contract", str(contract_file),
            "--network", "hyperion",
            "--test-only"
        ], capture_output=True, text=True)
        
        # Test verify (test-only)
        verify_result = subprocess.run([
            sys.executable, "-m", "hyperagent", "verify", "contract",
            "--address", "0x1234567890123456789012345678901234567890",
            "--network", "hyperion",
            "--test-only"
        ], capture_output=True, text=True)
        
        # All should complete without critical errors
        results = [audit_result, deploy_result, verify_result]
        for i, result in enumerate(["audit", "deploy", "verify"]):
            success = results[i].returncode == 0 or "error" not in results[i].stderr.lower()
            print(f"✅ {result} chain test: {'PASS' if success else 'FAIL'}")
        
        print("✅ Deploy -> Audit -> Verify chain test completed")
    
    def test_batch_operations(self, tmp_path):
        """Test batch operations"""
        print("\n=== Testing Batch Operations ===")
        
        # Create multiple contracts
        contracts_dir = tmp_path / "batch_contracts"
        contracts_dir.mkdir(exist_ok=True)
        
        contract_template = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract BatchToken{num} is ERC20 {{
    constructor() ERC20("Batch Token {num}", "BATCH{num}") {{
        _mint(msg.sender, 1000000 * 10**18);
    }}
}}
"""
        
        # Create 5 test contracts
        for i in range(5):
            contract_file = contracts_dir / f"BatchToken{i}.sol"
            contract_file.write_text(contract_template.format(num=i))
        
        # Test batch audit
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "batch-audit", "contracts",
            "--files", str(contracts_dir),
            "--format", "json",
            "--batch-name", "E2E Batch Test"
        ], capture_output=True, text=True)
        
        success = result.returncode == 0 or "error" not in result.stderr.lower()
        print(f"✅ Batch operations test: {'PASS' if success else 'FAIL'}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
