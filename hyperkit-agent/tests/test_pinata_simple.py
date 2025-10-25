"""
Simple Pinata IPFS Upload Test
Direct API call without service layer
"""

import os
import json
import asyncio
import httpx
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_pinata_direct():
    """Test Pinata upload with direct API call"""
    
    print("\nDirect Pinata IPFS Upload Test")
    print("=" * 60)
    
    # Get credentials from environment
    api_key = os.getenv("PINATA_API_KEY")
    secret_key = os.getenv("PINATA_SECRET_KEY")
    
    if not api_key:
        print("ERROR: PINATA_API_KEY not found in .env")
        return False
    
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
                        return True
                    else:
                        print("\nContent verification: FAILED")
                        return False
                else:
                    print(f"\nVerification failed: HTTP {verify_response.status_code}")
                    return False
            else:
                print(f"\nUpload failed: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
            print("\nTest file cleaned up")

if __name__ == "__main__":
    success = asyncio.run(test_pinata_direct())
    print("\n" + "=" * 60)
    if success:
        print("PINATA TEST: PASSED")
    else:
        print("PINATA TEST: FAILED")
    print("=" * 60)

