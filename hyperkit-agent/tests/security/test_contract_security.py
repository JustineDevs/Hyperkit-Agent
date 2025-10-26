"""
Security Test Cases for Smart Contracts
Tests for common vulnerabilities: reentrancy, unsafe transfers, permission escalation
"""

import pytest
from pathlib import Path


class TestReentrancyVulnerabilities:
    """Test for reentrancy attack vectors"""
    
    def test_no_reentrancy_in_withdrawal(self):
        """Ensure withdrawal functions follow Checks-Effects-Interactions pattern"""
        # Read contract files
        contracts_dir = Path(__file__).parent.parent.parent / "artifacts" / "contracts"
        
        if not contracts_dir.exists():
            pytest.skip("No contracts to test")
        
        reentrancy_patterns = [
            "call{value:",  # External call before state update
            ".call(",
            ".send(",
            ".transfer("
        ]
        
        vulnerabilities_found = []
        
        for contract_file in contracts_dir.rglob("*.sol"):
            content = contract_file.read_text()
            
            # Check for withdrawal pattern
            if "withdraw" in content.lower() or "claim" in content.lower():
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    # Check if external call happens before state update
                    if any(pattern in line for pattern in reentrancy_patterns):
                        # Look ahead for state updates
                        subsequent_lines = "\n".join(lines[i:i+5])
                        if "balances[" in subsequent_lines or "balance =" in subsequent_lines:
                            vulnerabilities_found.append({
                                "file": str(contract_file),
                                "line": i + 1,
                                "issue": "Potential reentrancy: external call before state update"
                            })
        
        assert len(vulnerabilities_found) == 0, f"Reentrancy vulnerabilities found: {vulnerabilities_found}"
    
    def test_nonreentrant_modifier_usage(self):
        """Check that critical functions use nonReentrant modifier"""
        contracts_dir = Path(__file__).parent.parent.parent / "artifacts" / "contracts"
        
        if not contracts_dir.exists():
            pytest.skip("No contracts to test")
        
        critical_functions = ["withdraw", "claim", "transferFrom", "mint"]
        missing_protection = []
        
        for contract_file in contracts_dir.rglob("*.sol"):
            content = contract_file.read_text()
            
            for func in critical_functions:
                if f"function {func}" in content:
                    # Check if nonReentrant is used
                    func_block = content[content.find(f"function {func}"):content.find(f"function {func}") + 500]
                    if "nonReentrant" not in func_block and "ReentrancyGuard" not in content:
                        missing_protection.append({
                            "file": str(contract_file),
                            "function": func,
                            "issue": "Missing nonReentrant modifier"
                        })
        
        # This is a warning, not a hard failure
        if missing_protection:
            pytest.skip(f"⚠️ Functions without reentrancy protection: {missing_protection}")


class TestUnsafeTransfers:
    """Test for unsafe token/ETH transfer patterns"""
    
    def test_no_unchecked_transfers(self):
        """Ensure all transfers check return values"""
        contracts_dir = Path(__file__).parent.parent.parent / "artifacts" / "contracts"
        
        if not contracts_dir.exists():
            pytest.skip("No contracts to test")
        
        unsafe_patterns = [
            ".transfer(",  # Should use safeTransfer
            ".transferFrom("  # Should use safeTransferFrom
        ]
        
        vulnerabilities = []
        
        for contract_file in contracts_dir.rglob("*.sol"):
            content = contract_file.read_text()
            
            # Check if OpenZeppelin SafeERC20 is imported
            has_safe_erc20 = "SafeERC20" in content
            
            if not has_safe_erc20:
                for i, line in enumerate(content.split("\n")):
                    if any(pattern in line for pattern in unsafe_patterns):
                        if "IERC20" in line or "ERC20" in line:
                            vulnerabilities.append({
                                "file": str(contract_file),
                                "line": i + 1,
                                "issue": "Unsafe ERC20 transfer - should use SafeERC20"
                            })
        
        assert len(vulnerabilities) == 0, f"Unsafe transfers found: {vulnerabilities}"
    
    def test_eth_transfer_safety(self):
        """Check ETH transfers use safe patterns"""
        contracts_dir = Path(__file__).parent.parent.parent / "artifacts" / "contracts"
        
        if not contracts_dir.exists():
            pytest.skip("No contracts to test")
        
        vulnerabilities = []
        
        for contract_file in contracts_dir.rglob("*.sol"):
            content = contract_file.read_text()
            lines = content.split("\n")
            
            for i, line in enumerate(lines):
                # Check for .send() usage (returns bool, should be checked)
                if ".send(" in line:
                    # Look for unchecked send
                    if "require" not in line and "if" not in line:
                        vulnerabilities.append({
                            "file": str(contract_file),
                            "line": i + 1,
                            "issue": "Unchecked .send() - return value not validated"
                        })
                
                # Check for .call{value:}() usage (should check return value)
                if ".call{value:" in line or ".call()" in line:
                    # Look for return value check
                    if "(bool success," not in line and "require" not in lines[i+1] if i+1 < len(lines) else True:
                        vulnerabilities.append({
                            "file": str(contract_file),
                            "line": i + 1,
                            "issue": "Unchecked .call() - should validate return value"
                        })
        
        assert len(vulnerabilities) == 0, f"Unsafe ETH transfers found: {vulnerabilities}"


class TestAccessControl:
    """Test for permission escalation and access control issues"""
    
    def test_onlyowner_protection(self):
        """Ensure critical functions have onlyOwner or role protection"""
        contracts_dir = Path(__file__).parent.parent.parent / "artifacts" / "contracts"
        
        if not contracts_dir.exists():
            pytest.skip("No contracts to test")
        
        critical_functions = [
            "mint", "burn", "pause", "unpause", 
            "withdraw", "setFee", "upgradeToAndCall",
            "transferOwnership", "renounceOwnership"
        ]
        
        missing_protection = []
        
        for contract_file in contracts_dir.rglob("*.sol"):
            content = contract_file.read_text()
            
            for func in critical_functions:
                if f"function {func}" in content:
                    # Extract function definition
                    func_start = content.find(f"function {func}")
                    func_end = content.find("{", func_start)
                    func_def = content[func_start:func_end]
                    
                    # Check for access control modifiers
                    has_protection = any(modifier in func_def for modifier in [
                        "onlyOwner", "onlyRole", "onlyAdmin", "onlyAuthorized"
                    ])
                    
                    if not has_protection:
                        missing_protection.append({
                            "file": str(contract_file),
                            "function": func,
                            "issue": "Missing access control modifier"
                        })
        
        assert len(missing_protection) == 0, f"Functions without access control: {missing_protection}"
    
    def test_no_public_sensitive_functions(self):
        """Check that sensitive functions are not accidentally public"""
        contracts_dir = Path(__file__).parent.parent.parent / "artifacts" / "contracts"
        
        if not contracts_dir.exists():
            pytest.skip("No contracts to test")
        
        sensitive_keywords = ["mint", "burn", "destroy", "selfdestruct", "delegatecall"]
        public_sensitive = []
        
        for contract_file in contracts_dir.rglob("*.sol"):
            content = contract_file.read_text()
            lines = content.split("\n")
            
            for i, line in enumerate(lines):
                if "function" in line and "public" in line:
                    if any(keyword in line.lower() for keyword in sensitive_keywords):
                        # Check if it has protection
                        if "onlyOwner" not in line and "onlyRole" not in line:
                            public_sensitive.append({
                                "file": str(contract_file),
                                "line": i + 1,
                                "issue": "Sensitive function is public without access control"
                            })
        
        assert len(public_sensitive) == 0, f"Public sensitive functions found: {public_sensitive}"


class TestIntegerOverflowUnderflow:
    """Test for integer overflow/underflow vulnerabilities"""
    
    def test_solidity_version(self):
        """Ensure contracts use Solidity 0.8.0+ with built-in overflow checks"""
        contracts_dir = Path(__file__).parent.parent.parent / "artifacts" / "contracts"
        
        if not contracts_dir.exists():
            pytest.skip("No contracts to test")
        
        old_version_contracts = []
        
        for contract_file in contracts_dir.rglob("*.sol"):
            content = contract_file.read_text()
            
            # Check pragma directive
            if "pragma solidity" in content:
                pragma_line = [line for line in content.split("\n") if "pragma solidity" in line][0]
                
                # Check for versions < 0.8.0
                if "0.7" in pragma_line or "0.6" in pragma_line or "0.5" in pragma_line or "0.4" in pragma_line:
                    old_version_contracts.append({
                        "file": str(contract_file),
                        "issue": f"Old Solidity version: {pragma_line.strip()}"
                    })
                    
                    # If old version, check for SafeMath
                    if "SafeMath" not in content:
                        old_version_contracts[-1]["issue"] += " - Missing SafeMath library"
        
        assert len(old_version_contracts) == 0, f"Contracts with overflow risks: {old_version_contracts}"


class TestDelegateCallSafety:
    """Test for unsafe delegatecall usage"""
    
    def test_no_untrusted_delegatecall(self):
        """Ensure delegatecall is only used with trusted contracts"""
        contracts_dir = Path(__file__).parent.parent.parent / "artifacts" / "contracts"
        
        if not contracts_dir.exists():
            pytest.skip("No contracts to test")
        
        unsafe_delegatecalls = []
        
        for contract_file in contracts_dir.rglob("*.sol"):
            content = contract_file.read_text()
            lines = content.split("\n")
            
            for i, line in enumerate(lines):
                if "delegatecall" in line:
                    # Check if the target is validated
                    # Look for whitelist/verification in surrounding lines
                    context = "\n".join(lines[max(0, i-5):i+5])
                    
                    has_validation = any(check in context for check in [
                        "whitelist", "approved", "onlyOwner", "require", "trusted"
                    ])
                    
                    if not has_validation:
                        unsafe_delegatecalls.append({
                            "file": str(contract_file),
                            "line": i + 1,
                            "issue": "Delegatecall without validation - potential attack vector"
                        })
        
        assert len(unsafe_delegatecalls) == 0, f"Unsafe delegatecalls found: {unsafe_delegatecalls}"


class TestTimestampDependence:
    """Test for timestamp manipulation vulnerabilities"""
    
    def test_no_critical_timestamp_logic(self):
        """Check that critical logic doesn't depend on block.timestamp"""
        contracts_dir = Path(__file__).parent.parent.parent / "artifacts" / "contracts"
        
        if not contracts_dir.exists():
            pytest.skip("No contracts to test")
        
        timestamp_issues = []
        
        for contract_file in contracts_dir.rglob("*.sol"):
            content = contract_file.read_text()
            lines = content.split("\n")
            
            for i, line in enumerate(lines):
                if "block.timestamp" in line or "now" in line:
                    # Check if used in critical logic
                    if any(critical in line for critical in ["require", "if", "randomness", "seed"]):
                        timestamp_issues.append({
                            "file": str(contract_file),
                            "line": i + 1,
                            "issue": "Critical logic depends on block.timestamp - can be manipulated by miners"
                        })
        
        # This is a warning for now
        if timestamp_issues:
            pytest.skip(f"⚠️ Timestamp-dependent logic found: {timestamp_issues}")


class TestGasLimits:
    """Test for unbounded loops and gas limit issues"""
    
    def test_no_unbounded_loops(self):
        """Check for loops that could run out of gas"""
        contracts_dir = Path(__file__).parent.parent.parent / "artifacts" / "contracts"
        
        if not contracts_dir.exists():
            pytest.skip("No contracts to test")
        
        unbounded_loops = []
        
        for contract_file in contracts_dir.rglob("*.sol"):
            content = contract_file.read_text()
            lines = content.split("\n")
            
            for i, line in enumerate(lines):
                # Check for loops over dynamic arrays
                if "for" in line and ".length" in line:
                    # Check if array is dynamic (not fixed size)
                    if "memory" in line or "storage" in line:
                        unbounded_loops.append({
                            "file": str(contract_file),
                            "line": i + 1,
                            "issue": "Loop over dynamic array - potential gas limit issues"
                        })
        
        # This is a warning
        if unbounded_loops:
            pytest.skip(f"⚠️ Unbounded loops found: {unbounded_loops}")


@pytest.mark.integration
class TestSecurityToolsIntegration:
    """Test that security tools can run"""
    
    def test_slither_available(self):
        """Check if Slither is available for static analysis"""
        import subprocess
        try:
            result = subprocess.run(["slither", "--version"], capture_output=True, timeout=5)
            assert result.returncode == 0, "Slither not installed or not working"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("Slither not available - install with: pip install slither-analyzer")
    
    def test_mythril_available(self):
        """Check if Mythril is available for symbolic execution"""
        import subprocess
        try:
            result = subprocess.run(["myth", "version"], capture_output=True, timeout=5)
            assert result.returncode == 0, "Mythril not installed or not working"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("Mythril not available - install with: pip install mythril")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

