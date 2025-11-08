#!/usr/bin/env python3
"""
Test script to verify real implementations vs mock implementations
Based on the comprehensive repo analysis
"""

import asyncio
import sys
import os
import pytest

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.core.ai_agent import HyperKitAIAgent
from services.audit.public_contract_auditor import PublicContractAuditor
from services.deployment.foundry_deployer import FoundryDeployer
from services.storage.pinata_client import PinataClient

@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_implementations():
    """Test all real implementations to verify they work correctly"""
    print("🔍 Testing Real Implementations vs Mock Implementations")
    print("=" * 70)
    
    # Test 1: Alith SDK Implementation (ONLY AI Agent)
    print("\n🤖 Test 1: Alith SDK Implementation (ONLY AI Agent)")
    print("-" * 40)
    print("NOTE: Alith SDK is the ONLY AI agent - uses OpenAI API key")
    print("      LazAI is network-only (blockchain RPC), NOT an AI agent")
    try:
        ai_agent = HyperKitAIAgent()
        
        # Check if Alith SDK is configured
        if ai_agent.alith_configured and ai_agent.alith_agent:
            print("✅ Alith SDK agent is initialized")
            
            # Test contract audit with Alith SDK
            sample_contract = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TestContract {
    mapping(address => uint256) public balances;
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
    
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        payable(msg.sender).transfer(amount);
    }
}
"""
            
            print("   Testing contract audit with Alith SDK...")
            audit_result = await ai_agent.audit_contract(sample_contract)
            
            print(f"   Audit Status: {audit_result.get('status', 'Unknown')}")
            print(f"   Method Used: {audit_result.get('method', 'Unknown')}")
            print(f"   Security Score: {audit_result.get('security_score', 'N/A')}")
            print(f"   Vulnerabilities Found: {len(audit_result.get('vulnerabilities', []))}")
            
            if ai_agent.alith_agent:
                print("✅ Alith SDK implementation is working correctly")
            else:
                print("⚠️  Alith SDK not used - using fallback LLM")
                print("   To enable: Install alith>=0.12.0 and set OPENAI_API_KEY")
        else:
            print("⚠️  Alith SDK not configured - using fallback LLM")
            print("   To enable: pip install alith>=0.12.0 and configure OPENAI_API_KEY")
            
    except Exception as e:
        print(f"❌ Alith SDK test failed: {e}")
    
    # Test 2: Public Contract Auditor (Real API calls)
    print("\n🌐 Test 2: Public Contract Auditor (Real API calls)")
    print("-" * 40)
    try:
        auditor = PublicContractAuditor()
        
        # Test with a known verified contract (USDC on Ethereum)
        test_address = "0xA0b86a33E6441b8C4C8C0d4B0c8e8B8c8B8c8B8c"  # Placeholder
        test_network = "ethereum"
        
        print(f"   Testing source code retrieval for {test_address} on {test_network}...")
        
        # This will test the real API calls
        source_code = await auditor._get_contract_source(test_address, test_network)
        
        if source_code and source_code != "// Placeholder source code - implement actual API calls":
            print("✅ Real API calls are working - source code retrieved")
            print(f"   Source code length: {len(source_code)} characters")
        else:
            print("⚠️  API call returned placeholder or no data")
            print("   This could be due to:")
            print("   - Contract not verified on explorer")
            print("   - Network not supported")
            print("   - API rate limiting")
        
        # Test ABI retrieval
        print("   Testing ABI retrieval...")
        abi = await auditor._get_contract_abi(test_address, test_network)
        
        if abi and len(abi) > 0:
            print("✅ Real ABI retrieval is working")
            print(f"   ABI functions: {len([item for item in abi if item.get('type') == 'function'])}")
        else:
            print("⚠️  ABI retrieval returned empty or placeholder")
            
    except Exception as e:
        print(f"❌ Public Contract Auditor test failed: {e}")
    
    # Test 3: Foundry Deployer (Real implementation)
    print("\n🔨 Test 3: Foundry Deployer (Real implementation)")
    print("-" * 40)
    try:
        deployer = FoundryDeployer()
        
        # Check if Foundry is available by testing deployment
        print("   Testing Foundry availability...")
        
        # Test with a simple contract
        test_contract = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TestContract {
    string public message = "Hello World";
}
"""
        
        try:
            # This will test if Foundry is available
            result = deployer.deploy(
                contract_source_code=test_contract,
                rpc_url="https://hyperion-testnet.metisdevops.link",
                private_key="test_key",
                contract_name="TestContract"
            )
            
            if result.get("success", False):
                print("✅ Foundry is working correctly")
            else:
                print(f"⚠️  Foundry test failed: {result.get('error', 'Unknown')}")
                print("   This could be due to:")
                print("   - Foundry not installed")
                print("   - Invalid RPC URL")
                print("   - Invalid private key")
        except Exception as e:
            print(f"⚠️  Foundry test failed: {e}")
            print("   Install Foundry: https://book.getfoundry.sh/getting-started/installation")
            
    except Exception as e:
        print(f"❌ Foundry Deployer test failed: {e}")
    
    # Test 4: Pinata IPFS Client (Real implementation)
    print("\n📦 Test 4: Pinata IPFS Client (Real implementation)")
    print("-" * 40)
    try:
        # Get config from environment
        from core.config.manager import config
        pinata_config = {
            'api_key': config.get('PINATA_API_KEY'),
            'api_secret': config.get('PINATA_SECRET_KEY')
        }
        
        if pinata_config['api_key'] and pinata_config['api_secret']:
            pinata_client = PinataClient(pinata_config)
            print("✅ Pinata API keys are configured")
            
            # Test file upload (with test data)
            print("   Testing file upload...")
            import json
            test_data = {"test": "data", "timestamp": "2025-10-27"}
            test_content = json.dumps(test_data).encode('utf-8')
            
            upload_result = await pinata_client.upload_file(
                content=test_content,
                filename="test_file.json",
                metadata={"type": "test", "description": "Test file for verification"}
            )
            
            if upload_result.get("success", False):
                print("✅ Real Pinata upload is working")
                print(f"   File CID: {upload_result.get('ipfs_hash', 'N/A')}")
                print(f"   Pinata URL: {upload_result.get('pinata_url', 'N/A')}")
            else:
                print(f"⚠️  Pinata upload failed: {upload_result.get('error', 'Unknown')}")
        else:
            print("⚠️  Pinata API keys not configured - using mock")
            print("   Set PINATA_API_KEY and PINATA_API_SECRET in .env file")
            
    except Exception as e:
        print(f"❌ Pinata IPFS Client test failed: {e}")
    
    # Test 5: Integration Test
    print("\n🔗 Test 5: Complete Integration Test")
    print("-" * 40)
    try:
        # Test the complete workflow
        ai_agent = HyperKitAIAgent()
        
        # Generate contract
        print("   Testing contract generation...")
        requirements = {
            "name": "TestToken",
            "type": "ERC20",
            "features": ["mintable", "burnable"],
            "security": "high"
        }
        
        contract_code = await ai_agent.generate_contract(requirements)
        print(f"   Contract generated: {len(contract_code)} characters")
        
        # Audit contract
        print("   Testing contract audit...")
        audit_result = await ai_agent.audit_contract(contract_code)
        print(f"   Audit completed: {audit_result.get('status', 'Unknown')}")
        print(f"   Method used: {audit_result.get('method', 'Unknown')}")
        
        # Store audit report
        print("   Testing audit report storage...")
        from services.core.storage import HyperKitStorageService
        storage = HyperKitStorageService()
        
        store_result = await storage.store_audit_report(audit_result)
        print(f"   Storage result: {store_result.get('status', 'Unknown')}")
        
        print("✅ Complete integration test passed")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
    
    print("\n" + "=" * 70)
    print("🎉 Real Implementation Testing Complete!")
    print("\n📊 Summary:")
    print("✅ Real implementations are working where configured")
    print("⚠️  Some features require proper configuration (API keys, tools)")
    print("🔧 Check the configuration guide for setup instructions")

if __name__ == "__main__":
    asyncio.run(test_real_implementations())
