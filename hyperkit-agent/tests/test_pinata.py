"""
Comprehensive Pinata IPFS Tests
Consolidated from test_pinata_simple.py and test_pinata_upload.py

Tests IPFS upload functionality with Pinata:
- Direct API calls (without service layer)
- Service layer integration
- File retrieval and verification
"""

import os
import sys
import json
import asyncio
import pytest
import httpx
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config.loader import get_config

# Load environment
load_dotenv()


# ============================================================================
# Section 1: Direct API Tests (Without Service Layer)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_pinata_direct():
    """Test Pinata upload with direct API call (without service layer)"""
    
    print("\nDirect Pinata IPFS Upload Test")
    print("=" * 60)
    
    # Get credentials from environment
    api_key = os.getenv("PINATA_API_KEY")
    secret_key = os.getenv("PINATA_SECRET_KEY")
    
    if not api_key:
        pytest.skip("PINATA_API_KEY not found in .env")
    
    print(f"API Key: {api_key[:10]}...")
    print(f"Secret: {secret_key[:10]}...")
    
    # Create test file
    test_file = Path("test_pinata.txt")
    test_file.write_text(f"""
HyperKit Pinata Test
Contract: 0x8E42b2d0D96296aCd8C5E87be1b6E610A7AdfD3a
Date: October 25, 2025
Status: Testing IPFS Upload
""")
    
    print(f"\nTest file created: {test_file}")
    print(f"File size: {test_file.stat().st_size} bytes")
    
    try:
        # Upload to Pinata
        print("\nUploading to Pinata...")
        
        url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
        headers = {
            "pinata_api_key": api_key,
            "pinata_secret_api_key": secret_key
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            with open(test_file, "rb") as f:
                files = {"file": f}
                response = await client.post(url, headers=headers, files=files)
            
            if response.status_code == 200:
                result = response.json()
                cid = result.get("IpfsHash")
                
                print("\n" + "=" * 60)
                print("SUCCESS! File uploaded to IPFS via Pinata")
                print("=" * 60)
                print(f"CID: {cid}")
                print(f"IPFS URL: ipfs://{cid}")
                print(f"Gateway URL: https://gateway.pinata.cloud/ipfs/{cid}")
                print(f"Pinned Size: {result.get('PinSize')} bytes")
                print(f"Timestamp: {result.get('Timestamp')}")
                
                # Save result
                result_file = Path("test_logs/pinata_success.json")
                result_file.parent.mkdir(exist_ok=True)
                result_file.write_text(json.dumps(result, indent=2))
                print(f"\nResult saved: {result_file}")
                
                # Try to retrieve
                print("\nVerifying upload...")
                gateway_url = f"https://gateway.pinata.cloud/ipfs/{cid}"
                verify_response = await client.get(gateway_url)
                
                if verify_response.status_code == 200:
                    content = verify_response.text
                    print("\nFile retrieved successfully from IPFS!")
                    print("Content preview:")
                    print("-" * 60)
                    print(content[:200])
                    print("-" * 60)
                    
                    if "HyperKit" in content:
                        print("\nContent verification: PASSED")
                        assert True
                    else:
                        print("\nContent verification: FAILED")
                        assert False, "Content verification failed"
                else:
                    print(f"\nVerification failed: HTTP {verify_response.status_code}")
                    assert False, f"Verification failed: HTTP {verify_response.status_code}"
            else:
                print(f"\nUpload failed: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                assert False, f"Upload failed: HTTP {response.status_code}"
                
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
            print("\nTest file cleaned up")


# ============================================================================
# Section 2: Service Layer Integration Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_pinata_upload():
    """Test Pinata IPFS upload with service layer"""
    
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
        pytest.skip("Pinata API key not configured - Set PINATA_API_KEY in .env file")
    
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
                assert len(cid) > 40, "CID format should be valid"
            else:
                print(f"CID format unexpected: {cid}")
                assert False, f"CID format unexpected: {cid}"
            
            assert result.get("status") == "success"
        else:
            print(f"\nUpload failed: {result.get('error', 'Unknown error')}")
            assert False, f"Upload failed: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        print(f"\nError during upload: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
            print(f"\nCleaned up test file")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pinata_retrieve():
    """Test retrieving file from IPFS"""
    
    print("\n" + "=" * 60)
    print("Testing IPFS File Retrieval...")
    print("=" * 60)
    
    # Read previous result
    result_file = Path("test_logs/pinata_upload_result.json")
    
    if not result_file.exists():
        pytest.skip("No previous upload result found - Run upload test first")
    
    result = json.loads(result_file.read_text())
    cid = result.get("cid")
    gateway_url = result.get("gateway_url")
    
    if not cid:
        pytest.skip("No CID found in previous result")
    
    print(f"CID: {cid}")
    print(f"Gateway URL: {gateway_url}")
    
    try:
        # Test retrieval via gateway
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
                    assert True
                else:
                    print("\nContent verification failed")
                    print("Retrieved content doesn't match expected")
                    assert False, "Content verification failed"
            else:
                print(f"\nRetrieval failed: HTTP {response.status_code}")
                assert False, f"Retrieval failed: HTTP {response.status_code}"
                
    except Exception as e:
        print(f"\nError during retrieval: {e}")
        raise


# ============================================================================
# Section 3: Integration Test Suite
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_pinata_full_workflow():
    """Test complete Pinata workflow: upload and retrieve"""
    
    print("\nStarting Pinata IPFS Full Workflow Test")
    print("=" * 60)
    
    # Test upload
    upload_success = False
    try:
        await test_pinata_upload()
        upload_success = True
    except Exception as e:
        print(f"Upload test failed: {e}")
    
    if upload_success:
        # Test retrieval
        retrieval_success = False
        try:
            await test_pinata_retrieve()
            retrieval_success = True
        except Exception as e:
            print(f"Retrieval test failed: {e}")
        
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"Upload Test: {'PASSED' if upload_success else 'FAILED'}")
        print(f"Retrieval Test: {'PASSED' if retrieval_success else 'FAILED'}")
        
        if upload_success and retrieval_success:
            print("\nAll Pinata IPFS tests PASSED!")
            assert True
        else:
            print("\nSome tests failed")
            assert False, "Some Pinata tests failed"
    else:
        print("\nUpload test failed - skipping retrieval test")
        pytest.skip("Upload test failed - cannot test retrieval")


if __name__ == "__main__":
    # Allow running as standalone script
    async def main():
        """Run all Pinata IPFS tests"""
        print("\nStarting Pinata IPFS Tests")
        print("=" * 60)
        
        # Test upload
        upload_success = False
        try:
            await test_pinata_upload()
            upload_success = True
        except Exception as e:
            print(f"Upload test failed: {e}")
        
        if upload_success:
            # Test retrieval
            retrieval_success = False
            try:
                await test_pinata_retrieve()
                retrieval_success = True
            except Exception as e:
                print(f"Retrieval test failed: {e}")
            
            print("\n" + "=" * 60)
            print("Test Summary")
            print("=" * 60)
            print(f"Upload Test: {'PASSED' if upload_success else 'FAILED'}")
            print(f"Retrieval Test: {'PASSED' if retrieval_success else 'FAILED'}")
            
            if upload_success and retrieval_success:
                print("\nAll Pinata IPFS tests PASSED!")
                return 0
            else:
                print("\nSome tests failed")
                return 1
        else:
            print("\nUpload test failed - skipping retrieval test")
            return 1
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

