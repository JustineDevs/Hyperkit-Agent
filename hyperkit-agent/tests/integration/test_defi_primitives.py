#!/usr/bin/env python3
"""
Test DeFi Primitives Generation
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.agent.main import HyperKitAgent
from core.config.loader import get_config

async def test_defi_primitives():
    """Test DeFi primitive generation"""
    print("🚀 Testing DeFi Primitives Generation")
    
    # Load config
    config_loader = get_config()
    config = config_loader.to_dict()
    
    # Initialize agent
    agent = HyperKitAgent(config)
    
    # Test staking primitive
    print("\n📊 Testing Staking Primitive...")
    staking_config = {
        "token_address": "0x1234567890abcdef1234567890abcdef12345678",
        "reward_token": "0xabcdef1234567890abcdef1234567890abcdef12",
        "reward_rate": "100",
        "lock_period": "7 days"
    }
    
    result = await agent.generate_defi_primitive("staking", staking_config)
    if result.get("status") == "success":
        print("✅ Staking primitive generated successfully")
        print(f"Contract length: {len(result.get('contract_code', ''))} characters")
    else:
        print(f"❌ Staking primitive failed: {result.get('error')}")
    
    # Test swap primitive
    print("\n🔄 Testing Swap Primitive...")
    swap_config = {
        "token_a": "0x1234567890abcdef1234567890abcdef12345678",
        "token_b": "0xabcdef1234567890abcdef1234567890abcdef12"
    }
    
    result = await agent.generate_defi_primitive("swap", swap_config)
    if result.get("status") == "success":
        print("✅ Swap primitive generated successfully")
        print(f"Contract length: {len(result.get('contract_code', ''))} characters")
    else:
        print(f"❌ Swap primitive failed: {result.get('error')}")
    
    # Test vault primitive
    print("\n🏦 Testing Vault Primitive...")
    vault_config = {
        "asset": "0x1234567890abcdef1234567890abcdef12345678",
        "management_fee": "200",
        "performance_fee": "2000"
    }
    
    result = await agent.generate_defi_primitive("vault", vault_config)
    if result.get("status") == "success":
        print("✅ Vault primitive generated successfully")
        print(f"Contract length: {len(result.get('contract_code', ''))} characters")
    else:
        print(f"❌ Vault primitive failed: {result.get('error')}")
    
    # Get supported primitives
    print("\n📋 Supported DeFi Primitives:")
    primitives = await agent.get_supported_defi_primitives()
    for primitive in primitives:
        print(f"  - {primitive}")
    
    # Get supported networks
    print("\n🌐 Supported Networks:")
    networks = await agent.get_supported_networks()
    for network in networks:
        print(f"  - {network}")
    
    print("\n🎉 DeFi Primitives Test Completed!")

if __name__ == "__main__":
    asyncio.run(test_defi_primitives())
