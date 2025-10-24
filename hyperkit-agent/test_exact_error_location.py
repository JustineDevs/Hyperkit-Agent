#!/usr/bin/env python3
"""
Test to find the exact location of the dict/string error
"""
import sys
import os
import asyncio
import traceback
sys.path.insert(0, os.path.dirname(__file__))

from core.config.loader import ConfigLoader
from core.agent.main import HyperKitAgent

async def test_exact_error():
    """Test deployment with detailed error tracing"""
    print("🔍 Testing exact error location...")
    
    try:
        # Load config
        config = ConfigLoader.load()
        print(f"✅ Config loaded: {type(config)}")
        
        # Create agent
        agent = HyperKitAgent(config)
        print("✅ Agent created")
        
        # Simple contract
        contract_code = """
        pragma solidity ^0.8.0;
        
        contract SimpleToken {
            string public name = "Test Token";
            string public symbol = "TEST";
            uint256 public totalSupply = 1000000;
            
            constructor() {}
        }
        """
        
        print("🚀 Testing deployment with detailed tracing...")
        print(f"Contract code length: {len(contract_code)}")
        
        # Call deploy_contract directly
        result = await agent.deploy_contract(contract_code, "hyperion")
        
        print(f"✅ Deployment result: {result}")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Print full traceback
        print("\n🔍 Full traceback:")
        traceback.print_exc()
        
        # Check if it's the specific error we're looking for
        if "expected string or bytes-like object, got 'dict'" in str(e):
            print("\n🎯 FOUND THE EXACT ERROR!")
            print("This is the dict/string error we're trying to fix.")
            
            # Find the line in the traceback
            tb_lines = traceback.format_exc().split('\n')
            for line in tb_lines:
                if "expected string or bytes-like object, got 'dict'" in line:
                    print(f"Error line: {line}")
                elif "File" in line and ".py" in line:
                    print(f"File: {line}")

if __name__ == "__main__":
    asyncio.run(test_exact_error())
