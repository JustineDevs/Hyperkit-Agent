#!/usr/bin/env python3
"""
Test end-to-end workflow with LazAI integration
"""

import asyncio
import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.agent.main import HyperKitAgent

async def test_workflow():
    """Test the complete workflow with LazAI integration"""
    print("🧪 Testing end-to-end workflow with LazAI integration...")
    
    try:
        agent = HyperKitAgent()
        print("✅ HyperKit Agent initialized successfully")
        
        # Test contract generation
        print("\n📝 Testing contract generation...")
        result = await agent.generate_contract('Create a simple ERC20 token')
        print(f"Generation result: {result.get('status', 'unknown')}")
        print(f"Method: {result.get('method', 'unknown')}")
        print(f"Provider: {result.get('provider', 'unknown')}")
        
        # Test contract audit
        print("\n🔍 Testing contract audit...")
        test_contract = """
        pragma solidity ^0.8.0;
        contract TestToken {
            mapping(address => uint256) public balances;
            function deposit() public payable {
                balances[msg.sender] += msg.value;
            }
        }
        """
        audit_result = await agent.audit_contract(test_contract)
        print(f"Audit result: {audit_result.get('status', 'unknown')}")
        print(f"Method: {audit_result.get('method', 'unknown')}")
        print(f"Provider: {audit_result.get('provider', 'unknown')}")
        
        print("\n✅ End-to-end workflow test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow())
