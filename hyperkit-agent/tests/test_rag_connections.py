#!/usr/bin/env python3
"""
RAG Connection Testing Utility

This script tests IPFS Pinata RAG connections:
1. IPFS Pinata connection
2. CID registry loading
3. Template retrieval
4. Overall system health

Note: Obsidian RAG has been removed - IPFS Pinata is now exclusive
"""

import asyncio
import sys
import json
from pathlib import Path
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.rag.ipfs_rag import get_ipfs_rag
from core.config.loader import get_config

# Suppress warnings
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('web3').setLevel(logging.WARNING)
logging.getLogger('alith').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)


async def test_all_rag_connections():
    """Test all RAG connections and return comprehensive results."""
    
    print("🔍 Testing RAG Connections...")
    print("=" * 60)
    
    results = {
        "timestamp": str(asyncio.get_event_loop().time()),
        "overall_status": "unknown",
        "components": {}
    }
    
    # Test 1: IPFS Pinata RAG
    print("\n1. Testing IPFS Pinata RAG Connection...")
    try:
        config = get_config().to_dict()
        ipfs_rag = get_ipfs_rag(config)
        connection_results = await ipfs_rag.test_connections()
        results["components"]["ipfs_pinata"] = connection_results
        
        status = connection_results.get("status", "failed")
        pinata_enabled = connection_results.get("pinata_enabled", False)
        registry_loaded = connection_results.get("cid_registry_loaded", False)
        
        print(f"   Pinata Enabled: {'✅' if pinata_enabled else '❌'}")
        print(f"   CID Registry: {'✅' if registry_loaded else '❌'}")
        print(f"   Overall Status: {'✅ PASSED' if status == 'success' else '❌ FAILED'}")
        
    except Exception as e:
        results["components"]["ipfs_pinata"] = {
            "status": "error",
            "error": str(e)
        }
        print(f"   IPFS Pinata RAG: ❌ ERROR - {e}")
    
    # Test 2: Configuration Check
    print("\n2. Testing Configuration...")
    try:
        config = get_config().to_dict()
        
        # Check Pinata IPFS config
        pinata_config = config.get("storage", {}).get("pinata", {})
        
        config_status = {
            "pinata_api_key": bool(pinata_config.get("api_key")),
            "pinata_secret_key": bool(pinata_config.get("secret_key")),
            "cid_registry_exists": Path("docs/RAG_TEMPLATES/cid-registry.json").exists()
        }
        
        results["components"]["configuration"] = config_status
        
        print(f"   Pinata API Key: {'✅' if config_status['pinata_api_key'] else '❌'}")
        print(f"   Pinata Secret Key: {'✅' if config_status['pinata_secret_key'] else '❌'}")
        print(f"   CID Registry File: {'✅' if config_status['cid_registry_exists'] else '❌'}")
        
    except Exception as e:
        results["components"]["configuration"] = {
            "status": "error",
            "error": str(e)
        }
        print(f"   Configuration: ❌ ERROR - {e}")
    
    # Test 3: Content Retrieval Test
    print("\n3. Testing Content Retrieval...")
    try:
        config = get_config().to_dict()
        ipfs_rag = get_ipfs_rag(config)
        test_content = await ipfs_rag.retrieve("smart contract security", max_results=3)
        
        retrieval_status = {
            "content_length": len(test_content),
            "has_content": len(test_content) > 100,
            "preview": test_content[:200] + "..." if len(test_content) > 200 else test_content
        }
        
        results["components"]["content_retrieval"] = retrieval_status
        
        print(f"   Content Length: {retrieval_status['content_length']} characters")
        print(f"   Has Content: {'✅' if retrieval_status['has_content'] else '❌'}")
        print(f"   Preview: {retrieval_status['preview']}")
        
    except Exception as e:
        results["components"]["content_retrieval"] = {
            "status": "error",
            "error": str(e)
        }
        print(f"   Content Retrieval: ❌ ERROR - {e}")
    
    # Determine overall status
    print("\n" + "=" * 60)
    print("📊 Overall Status Assessment")
    print("=" * 60)
    
    success_count = 0
    total_tests = 0
    
    for component, status in results["components"].items():
        if isinstance(status, dict):
            if status.get("status") == "success":
                success_count += 1
            total_tests += 1
    
    if success_count == total_tests and total_tests > 0:
        results["overall_status"] = "success"
        print("🎉 ALL TESTS PASSED!")
    elif success_count > 0:
        results["overall_status"] = "partial"
        print(f"⚠️  PARTIAL SUCCESS: {success_count}/{total_tests} components working")
    else:
        results["overall_status"] = "failed"
        print("❌ ALL TESTS FAILED!")
    
    # Save results
    results_file = Path("test_logs/rag_connection_test_results.json")
    results_file.parent.mkdir(exist_ok=True)
    results_file.write_text(json.dumps(results, indent=2))
    print(f"\n📄 Results saved to: {results_file}")
    
    return results


async def main():
    """Main test function."""
    print("🚀 RAG Connection Test Suite")
    print("Testing IPFS Pinata RAG (Obsidian removed - IPFS Pinata exclusive)")
    
    try:
        results = await test_all_rag_connections()
        
        # Return appropriate exit code
        if results["overall_status"] == "success":
            print("\n✅ All RAG connections are working correctly!")
            return 0
        elif results["overall_status"] == "partial":
            print("\n⚠️  Some RAG connections are working, but issues detected.")
            return 1
        else:
            print("\n❌ RAG connections are not working properly.")
            return 2
            
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 3


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
