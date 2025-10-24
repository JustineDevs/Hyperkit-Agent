#!/usr/bin/env python3
"""
Test deployer directly to isolate the error
"""
import sys
import os
import asyncio
import traceback
sys.path.insert(0, os.path.dirname(__file__))

from core.config.loader import ConfigLoader
from services.deployment.deployer import MultiChainDeployer

async def test_direct_deployer():
    """Test deployer directly"""
    print("🔍 Testing deployer directly...")
    
    try:
        # Load config
        config = ConfigLoader.load()
        print(f"✅ Config loaded: {type(config)}")
        
        # Create deployer directly
        deployer = MultiChainDeployer(config)
        print("✅ Deployer created")
        
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
        
        print("🚀 Testing deployer.deploy directly...")
        print(f"Contract code length: {len(contract_code)}")
        
        # Call deployer directly
        result = await deployer.deploy(contract_code, "hyperion")
        
        print(f"✅ Deployer result: {result}")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Print full traceback
        print("\n🔍 Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_deployer())
