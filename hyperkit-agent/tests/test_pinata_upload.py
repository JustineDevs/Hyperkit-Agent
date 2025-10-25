"""
Test Pinata IPFS Upload
Tests real IPFS upload functionality with Pinata
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config.loader import get_config


async def test_pinata_upload():
    """Test Pinata IPFS upload with real file"""
    
    print("Testing Pinata IPFS Upload...")
    print("=" * 60)
    
    # Get config
    config = get_config().to_dict()
    
    # Check Pinata credentials (stored under storage.pinata)
    storage_config = config.get("storage", {})
    pinata_config = storage_config.get("pinata", {})
    pinata_key = pinata_config.get("api_key")
    pinata_secret = pinata_config.get("secret_key")
    
    if not pinata_key or pinata_key == "your_pinata_api_key_here":
        print("Pinata API key not configured")
        print("Set PINATA_API_KEY in .env file")
        return False
    
    print(f"Pinata API key found: {pinata_key[:10]}...")
    print(f"Pinata secret found: {pinata_secret[:10]}...")
    
    # Create test file
    test_file = Path("test_ipfs_upload.txt")
    test_content = """
    # HyperKit Test File
    
    This is a test file for IPFS upload via Pinata.
    
    Contract Address: 0x8E42b2d0D96296aCd8C5E87be1b6E610A7AdfD3a
    Network: Hyperion Testnet
    Test Date: October 25, 2025
    Status: IPFS Upload Test
    """
    
    test_file.write_text(test_content)
    print(f"Test file created: {test_file}")
    
    try:
        # Import storage service
        from services.storage.ipfs import IPFSStorage
        
        # Create storage instance
        storage = IPFSStorage()
        
        # Test upload
        print("\nUploading to IPFS via Pinata...")
        result = await storage.upload_file(str(test_file), "test-ipfs-upload")
        
        if result.get("status") == "success":
            cid = result.get("cid")
            ipfs_url = result.get("ipfs_url")
            gateway_url = result.get("gateway_url")
            
            print("\nUpload Successful!")
            print(f"CID: {cid}")
            print(f"IPFS URL: {ipfs_url}")
            print(f"Gateway URL: {gateway_url}")
            
            # Save result
            result_file = Path("test_logs/pinata_upload_result.json")
            result_file.parent.mkdir(exist_ok=True)
            result_file.write_text(json.dumps(result, indent=2))
            print(f"\nResult saved to: {result_file}")
            
            # Verify CID format
            if cid and len(cid) > 40:
                print(f"CID format valid: {len(cid)} characters")
            else:
                print(f"CID format unexpected: {cid}")
            
            return True
        else:
            print(f"\nUpload failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"\nError during upload: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
            print(f"\nCleaned up test file")


async def test_pinata_retrieve():
    """Test retrieving file from IPFS"""
    
    print("\n" + "=" * 60)
    print("Testing IPFS File Retrieval...")
    print("=" * 60)
    
    # Read previous result
    result_file = Path("test_logs/pinata_upload_result.json")
    
    if not result_file.exists():
        print("No previous upload result found")
        print("Run upload test first")
        return False
    
    result = json.loads(result_file.read_text())
    cid = result.get("cid")
    gateway_url = result.get("gateway_url")
    
    if not cid:
        print("No CID found in previous result")
        return False
    
    print(f"CID: {cid}")
    print(f"Gateway URL: {gateway_url}")
    
    try:
        # Test retrieval via gateway
        import httpx
        
        print(f"\nRetrieving file from IPFS...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(gateway_url)
            
            if response.status_code == 200:
                content = response.text
                print(f"\nFile retrieved successfully!")
                print(f"Content preview (first 200 chars):")
                print("-" * 60)
                print(content[:200])
                print("-" * 60)
                
                # Verify content
                if "HyperKit Test File" in content:
                    print("\nContent verification successful!")
                    print("File matches uploaded content")
                    return True
                else:
                    print("\nContent verification failed")
                    print("Retrieved content doesn't match expected")
                    return False
            else:
                print(f"\nRetrieval failed: HTTP {response.status_code}")
                return False
                
    except Exception as e:
        print(f"\nError during retrieval: {e}")
        return False


async def main():
    """Run all Pinata IPFS tests"""
    
    print("\nStarting Pinata IPFS Tests")
    print("=" * 60)
    
    # Test upload
    upload_success = await test_pinata_upload()
    
    if upload_success:
        # Test retrieval
        retrieval_success = await test_pinata_retrieve()
        
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"Upload Test: {'PASSED' if upload_success else 'FAILED'}")
        print(f"Retrieval Test: {'PASSED' if retrieval_success else 'FAILED'}")
        
        if upload_success and retrieval_success:
            print("\nAll Pinata IPFS tests PASSED!")
            return True
        else:
            print("\nSome tests failed")
            return False
    else:
        print("\nUpload test failed - skipping retrieval test")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

