#!/usr/bin/env python3
"""
RAG Connection Testing Utility

This script tests all RAG connections:
1. Obsidian MCP connection
2. IPFS storage connection
3. Local knowledge base
4. Overall system health
"""

import asyncio
import sys
import json
from pathlib import Path
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.rag.enhanced_retriever import get_rag_retriever
from services.rag.obsidian_rag_enhanced import test_obsidian_rag
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
    
    # Test 1: Obsidian RAG
    print("\n1. Testing Obsidian RAG Connection...")
    try:
        obsidian_success = await test_obsidian_rag()
        results["components"]["obsidian"] = {
            "status": "success" if obsidian_success else "failed",
            "test_result": obsidian_success
        }
        print(f"   Obsidian RAG: {'✅ PASSED' if obsidian_success else '❌ FAILED'}")
    except Exception as e:
        results["components"]["obsidian"] = {
            "status": "error",
            "error": str(e)
        }
        print(f"   Obsidian RAG: ❌ ERROR - {e}")
    
    # Test 2: Enhanced RAG Retriever
    print("\n2. Testing Enhanced RAG Retriever...")
    try:
        retriever = get_rag_retriever()
        connection_results = await retriever.test_connections()
        results["components"]["enhanced_retriever"] = connection_results
        
        # Print results
        for source, status in connection_results.items():
            status_icon = "✅" if status["status"] == "success" else "❌"
            print(f"   {source.title()}: {status_icon} {status['status']}")
            if "error" in status:
                print(f"     Error: {status['error']}")
            if "file_count" in status:
                print(f"     Files: {status['file_count']}")
                
    except Exception as e:
        results["components"]["enhanced_retriever"] = {
            "status": "error",
            "error": str(e)
        }
        print(f"   Enhanced Retriever: ❌ ERROR - {e}")
    
    # Test 3: Configuration Check
    print("\n3. Testing Configuration...")
    try:
        config = get_config().to_dict()
        
        # Check Obsidian config
        obsidian_config = config.get("rag", {}).get("obsidian", {})
        mcp_config = config.get("mcp", {})
        
        config_status = {
            "obsidian_api_key": bool(obsidian_config.get("api_key")),
            "obsidian_vault_path": bool(obsidian_config.get("vault_path")),
            "mcp_enabled": mcp_config.get("enabled", False),
            "mcp_docker": mcp_config.get("docker", False)
        }
        
        results["components"]["configuration"] = config_status
        
        print(f"   Obsidian API Key: {'✅' if config_status['obsidian_api_key'] else '❌'}")
        print(f"   Obsidian Vault Path: {'✅' if config_status['obsidian_vault_path'] else '❌'}")
        print(f"   MCP Enabled: {'✅' if config_status['mcp_enabled'] else '❌'}")
        print(f"   MCP Docker: {'✅' if config_status['mcp_docker'] else '❌'}")
        
    except Exception as e:
        results["components"]["configuration"] = {
            "status": "error",
            "error": str(e)
        }
        print(f"   Configuration: ❌ ERROR - {e}")
    
    # Test 4: Content Retrieval Test
    print("\n4. Testing Content Retrieval...")
    try:
        retriever = get_rag_retriever()
        test_content = await retriever.retrieve("smart contract security", max_results=3)
        
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
    print("Testing Obsidian MCP, IPFS, and Local Knowledge Base")
    
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
