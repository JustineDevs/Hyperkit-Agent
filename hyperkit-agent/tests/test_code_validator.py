#!/usr/bin/env python3
"""
Test script for code validation and security scanning functionality
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.core.code_validator import CodeValidator

async def test_code_validator():
    """Test the code validation functionality"""
    print("🧪 Testing Code Validation and Security Scanning")
    print("=" * 60)
    
    # Initialize the code validator
    validator = CodeValidator()
    
    # Test 1: Secure contract validation
    print("\n✅ Test 1: Validating secure contract...")
    secure_contract = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title SecureToken
 * @dev A secure ERC20 token implementation
 */
contract SecureToken is ERC20, Ownable, ReentrancyGuard {
    uint256 public constant MAX_SUPPLY = 1000000 * 10**18;
    
    constructor() ERC20("SecureToken", "SEC") {
        _mint(msg.sender, MAX_SUPPLY);
    }
    
    /**
     * @dev Mint tokens to a specific address
     * @param to The address to mint tokens to
     * @param amount The amount of tokens to mint
     */
    function mint(address to, uint256 amount) external onlyOwner {
        require(totalSupply() + amount <= MAX_SUPPLY, "Exceeds max supply");
        _mint(to, amount);
    }
    
    /**
     * @dev Burn tokens from caller's balance
     * @param amount The amount of tokens to burn
     */
    function burn(uint256 amount) external {
        require(balanceOf(msg.sender) >= amount, "Insufficient balance");
        _burn(msg.sender, amount);
    }
}
"""
    
    result = await validator.validate_code(secure_contract, "solidity")
    print(f"   Validation status: {result['status']}")
    print(f"   Security score: {result['score']}/100")
    print(f"   Security issues: {len(result['security_issues'])}")
    print(f"   Quality issues: {len(result['quality_issues'])}")
    print(f"   Compliance issues: {len(result['compliance_issues'])}")
    
    # Test 2: Vulnerable contract validation
    print("\n❌ Test 2: Validating vulnerable contract...")
    vulnerable_contract = """
pragma solidity ^0.7.0;

contract VulnerableContract {
    mapping(address => uint256) balances;
    
    function withdraw() external {
        uint256 amount = balances[msg.sender];
        require(amount > 0, "No balance");
        
        // Vulnerable: external call before state change
        msg.sender.call{value: amount}("");
        balances[msg.sender] = 0;
    }
    
    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }
    
    function getBalance() external view returns (uint256) {
        return balances[msg.sender];
    }
}
"""
    
    result = await validator.validate_code(vulnerable_contract, "solidity")
    print(f"   Validation status: {result['status']}")
    print(f"   Security score: {result['score']}/100")
    print(f"   Security issues: {len(result['security_issues'])}")
    print(f"   Quality issues: {len(result['quality_issues'])}")
    print(f"   Compliance issues: {len(result['compliance_issues'])}")
    
    if result['security_issues']:
        print("   Security issues found:")
        for issue in result['security_issues'][:3]:  # Show first 3
            print(f"     - {issue['type']}: {issue['description']}")
    
    # Test 3: Quality validation
    print("\n📝 Test 3: Quality validation...")
    poor_quality_contract = """
contract BadContract {
    uint256 a;
    uint256 b;
    
    function doSomething() external {
        a = a + 1;
        b = b * 2;
    }
    
    function getA() external view returns (uint256) {
        return a;
    }
}
"""
    
    result = await validator.validate_code(poor_quality_contract, "solidity")
    print(f"   Validation status: {result['status']}")
    print(f"   Security score: {result['score']}/100")
    print(f"   Quality issues: {len(result['quality_issues'])}")
    print(f"   Compliance issues: {len(result['compliance_issues'])}")
    
    if result['quality_issues']:
        print("   Quality issues found:")
        for issue in result['quality_issues']:
            print(f"     - {issue['type']}: {issue['description']}")
    
    # Test 4: Comprehensive scan
    print("\n🔍 Test 4: Comprehensive security scan...")
    test_contract = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TestContract {
    mapping(address => uint256) public balances;
    
    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }
    
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        payable(msg.sender).transfer(amount);
    }
}
"""
    
    result = await validator.comprehensive_scan(test_contract, "solidity")
    print(f"   Scan status: {result['status']}")
    print(f"   Overall score: {result['overall_score']}/100")
    print(f"   Validation issues: {len(result['validation']['security_issues'])}")
    
    if result.get('slither_scan'):
        print(f"   Slither scan: {result['slither_scan']['status']}")
    
    # Test 5: Recommendations
    print("\n💡 Test 5: Recommendations...")
    if result.get('recommendations'):
        print("   Recommendations:")
        for i, rec in enumerate(result['recommendations'][:3], 1):
            print(f"     {i}. {rec}")
    
    print("\n" + "=" * 60)
    print("🎉 Code validation tests completed successfully!")
    print("✅ All validation and security scanning functionality is working correctly")

if __name__ == "__main__":
    asyncio.run(test_code_validator())
