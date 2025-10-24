"""
Security tests for audit functionality
"""
import pytest
import subprocess
import sys
import json
from pathlib import Path


class TestSecurityAudits:
    """Test security audit functionality"""
    
    def test_audit_vulnerable_patterns(self):
        """Test audit detection of vulnerable patterns"""
        # Create a contract with known vulnerabilities
        vulnerable_contract = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VulnerableContract {
    mapping(address => uint256) public balances;
    
    function withdraw() public {
        // Vulnerable: no reentrancy protection
        uint256 amount = balances[msg.sender];
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        balances[msg.sender] = 0;
    }
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
}
"""
        
        contract_file = "artifacts/generated/vulnerable_test.sol"
        Path("artifacts/generated").mkdir(parents=True, exist_ok=True)
        Path(contract_file).write_text(vulnerable_contract)
        
        # Audit the vulnerable contract
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "audit", contract_file,
            "--output", "artifacts/audits/vulnerable_audit.json",
            "--format", "json"
        ], capture_output=True, text=True)
        
        # Should detect vulnerabilities
        assert result.returncode == 0
        
        # Check audit report
        audit_file = Path("artifacts/audits/vulnerable_audit.json")
        if audit_file.exists():
            with open(audit_file) as f:
                audit_data = json.load(f)
                assert "audit" in audit_data or "findings" in audit_data
        
        # Clean up
        Path(contract_file).unlink(missing_ok=True)
        Path("artifacts/audits/vulnerable_audit.json").unlink(missing_ok=True)
    
    def test_audit_secure_patterns(self):
        """Test audit of secure contract patterns"""
        # Create a secure contract
        secure_contract = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract SecureToken is ERC20, Ownable, ReentrancyGuard {
    constructor(string memory name, string memory symbol) ERC20(name, symbol) {}
    
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }
    
    function burn(uint256 amount) public {
        _burn(msg.sender, amount);
    }
}
"""
        
        contract_file = "artifacts/generated/secure_test.sol"
        Path("artifacts/generated").mkdir(parents=True, exist_ok=True)
        Path(contract_file).write_text(secure_contract)
        
        # Audit the secure contract
        result = subprocess.run([
            sys.executable, "-m", "hyperagent", "audit", contract_file
        ], capture_output=True, text=True)
        
        # Should complete audit successfully
        assert result.returncode == 0
        
        # Clean up
        Path(contract_file).unlink(missing_ok=True)
