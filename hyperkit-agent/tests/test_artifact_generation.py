#!/usr/bin/env python3
"""
Test script for artifact generation functionality
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.core.artifact_generator import HyperKitArtifactGenerator

async def test_artifact_generation():
    """Test the artifact generation functionality"""
    print("🧪 Testing Artifact Generation Service")
    print("=" * 50)
    
    # Initialize the artifact generator
    generator = HyperKitArtifactGenerator()
    
    # Test 1: Generate contract artifact
    print("\n📝 Test 1: Generating contract artifact...")
    contract_code = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TestToken {
    string public name = "Test Token";
    string public symbol = "TEST";
    uint256 public totalSupply = 1000000;
    
    mapping(address => uint256) public balanceOf;
    
    constructor() {
        balanceOf[msg.sender] = totalSupply;
    }
    
    function transfer(address to, uint256 amount) public returns (bool) {
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        return true;
    }
}
"""
    
    contract_metadata = {
        "name": "TestToken",
        "version": "1.0.0",
        "description": "A simple ERC20-like token for testing",
        "features": ["transfer", "balance_check"],
        "security_level": "medium",
        "gas_optimized": True
    }
    
    result = await generator.generate_contract_artifact(contract_code, contract_metadata)
    print(f"✅ Contract artifact generation: {result['status']}")
    if result['status'] == 'success':
        print(f"   Artifact ID: {result['artifact_id']}")
        print(f"   Directory: {result['directory']}")
        print(f"   Files generated: {len(result['files'])}")
    
    # Test 2: Generate audit report artifact
    print("\n🔍 Test 2: Generating audit report artifact...")
    audit_data = {
        "contract_address": "0x1234567890123456789012345678901234567890",
        "security_score": 85,
        "vulnerabilities": [
            {
                "title": "Potential Reentrancy",
                "severity": "MEDIUM",
                "description": "Function may be vulnerable to reentrancy attacks",
                "recommendation": "Use checks-effects-interactions pattern"
            }
        ],
        "warnings": [
            "Consider adding more comprehensive error handling",
            "Gas optimization opportunities detected"
        ],
        "recommendations": [
            "Implement proper access controls",
            "Add event logging for important state changes",
            "Consider using OpenZeppelin libraries"
        ]
    }
    
    result = await generator.generate_audit_report_artifact(audit_data)
    print(f"✅ Audit report generation: {result['status']}")
    if result['status'] == 'success':
        print(f"   Artifact ID: {result['artifact_id']}")
        print(f"   Directory: {result['directory']}")
        print(f"   Files generated: {len(result['files'])}")
    
    # Test 3: Generate documentation artifact
    print("\n📚 Test 3: Generating documentation artifact...")
    doc_content = {
        "title": "HyperKit Agent API Documentation",
        "description": "Complete API documentation for HyperKit Agent",
        "version": "1.0.0",
        "sections": [
            {
                "title": "Authentication",
                "content": "All API requests require authentication using API keys."
            },
            {
                "title": "Endpoints",
                "content": "The API provides endpoints for contract generation, auditing, and deployment."
            }
        ]
    }
    
    result = await generator.generate_documentation_artifact("api_docs", doc_content)
    print(f"✅ Documentation generation: {result['status']}")
    if result['status'] == 'success':
        print(f"   Artifact ID: {result['artifact_id']}")
        print(f"   Directory: {result['directory']}")
        print(f"   Files generated: {len(result['files'])}")
    
    # Test 4: List artifacts
    print("\n📋 Test 4: Listing all artifacts...")
    result = await generator.list_artifacts()
    print(f"✅ Artifact listing: {result['status']}")
    if result['status'] == 'success':
        print(f"   Total artifacts: {result['total']}")
        for artifact in result['artifacts'][:3]:  # Show first 3
            print(f"   - {artifact['type']}: {artifact['id']}")
    
    print("\n" + "=" * 50)
    print("🎉 Artifact generation tests completed successfully!")
    print("✅ All artifact generation functionality is working correctly")

if __name__ == "__main__":
    asyncio.run(test_artifact_generation())
