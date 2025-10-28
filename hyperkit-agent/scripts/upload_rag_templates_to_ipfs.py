#!/usr/bin/env python3
"""
Upload RAG Templates to IPFS Pinata
Uploads each prepared template individually (one file per CID, no bulk packing)
Updates CID registry with real CIDs
"""

import os
import json
import asyncio
import httpx
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Directories
TEMPLATES_DIR = Path(__file__).parent.parent / "artifacts" / "rag_templates"
REGISTRY_PATH = Path(__file__).parent.parent.parent / "docs" / "RAG_TEMPLATES" / "cid-registry.json"

async def upload_to_pinata(file_path: Path, metadata: dict = None) -> dict:
    """
    Upload a single file to IPFS via Pinata
    
    Args:
        file_path: Path to file to upload
        metadata: Optional metadata dictionary
        
    Returns:
        Dictionary with upload result including CID
    """
    api_key = os.getenv("PINATA_API_KEY")
    secret_key = os.getenv("PINATA_SECRET_KEY")
    
    if not api_key or not secret_key:
        raise ValueError("PINATA_API_KEY and PINATA_SECRET_KEY must be set in .env")
    
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    headers = {
        "pinata_api_key": api_key,
        "pinata_secret_api_key": secret_key
    }
    
    # Prepare metadata
    if metadata:
        headers["pinata_metadata"] = json.dumps(metadata)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "text/plain")}
            response = await client.post(url, headers=headers, files=files)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "status": "success",
                "cid": result.get("IpfsHash"),
                "name": file_path.name,
                "size": result.get("PinSize"),
                "timestamp": result.get("Timestamp"),
                "ipfs_url": f"ipfs://{result.get('IpfsHash')}",
                "gateway_url": f"https://gateway.pinata.cloud/ipfs/{result.get('IpfsHash')}"
            }
        else:
            return {
                "status": "error",
                "error": f"HTTP {response.status_code}: {response.text}",
                "name": file_path.name
            }

async def upload_all_templates():
    """Upload all prepared RAG templates to IPFS Pinata"""
    
    print("=" * 70)
    print("Uploading RAG Templates to IPFS Pinata")
    print("=" * 70)
    
    # Check for credentials
    api_key = os.getenv("PINATA_API_KEY")
    secret_key = os.getenv("PINATA_SECRET_KEY")
    
    if not api_key or not secret_key:
        print("\nERROR: Pinata credentials not configured")
        print("Set PINATA_API_KEY and PINATA_SECRET_KEY in .env file")
        print("\nExample .env entry:")
        print("PINATA_API_KEY=your_api_key_here")
        print("PINATA_SECRET_KEY=your_secret_key_here")
        return False
    
    print(f"\nAPI Key: {api_key[:15]}...")
    print(f"Secret: {secret_key[:15]}...")
    
    # Load registry
    registry = json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))
    
    # Get all template files
    template_files = list(TEMPLATES_DIR.glob("*.txt"))
    
    if not template_files:
        print(f"\nNo template files found in {TEMPLATES_DIR}")
        return False
    
    print(f"\nFound {len(template_files)} templates to upload")
    print("=" * 70)
    
    # Upload each template individually
    upload_results = []
    
    for i, template_file in enumerate(template_files, 1):
        template_name = template_file.stem
        
        print(f"\n[{i}/{len(template_files)}] Uploading: {template_name}")
        print(f"File: {template_file.name}")
        print(f"Size: {template_file.stat().st_size} bytes")
        
        # Get metadata from registry
        template_info = registry["templates"].get(template_name, {})
        metadata = {
            "description": template_info.get("description", ""),
            "category": template_info.get("category", ""),
            "name": template_name,
            "type": "rag_template"
        }
        
        try:
            result = await upload_to_pinata(template_file, metadata)
            
            if result["status"] == "success":
                print(f"[OK] Upload successful")
                print(f"CID: {result['cid']}")
                print(f"Gateway: {result['gateway_url']}")
                
                # Update registry
                if template_name in registry["templates"]:
                    registry["templates"][template_name]["cid"] = result["cid"]
                    registry["templates"][template_name]["uploaded"] = True
                    registry["templates"][template_name]["upload_date"] = datetime.now().isoformat()
                    registry["templates"][template_name]["gateway_url"] = result["gateway_url"]
                
                upload_results.append(result)
            else:
                print(f"[FAILED] {result.get('error', 'Unknown error')}")
                upload_results.append(result)
                
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            upload_results.append({
                "status": "error",
                "name": template_name,
                "error": str(e)
            })
    
    # Save updated registry
    try:
        REGISTRY_PATH.write_text(json.dumps(registry, indent=2), encoding='utf-8')
        print(f"\n[OK] Registry updated: {REGISTRY_PATH}")
    except Exception as e:
        print(f"\n[WARNING] Failed to update registry: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("Upload Summary")
    print("=" * 70)
    
    successful = sum(1 for r in upload_results if r.get("status") == "success")
    failed = len(upload_results) - successful
    
    print(f"Total: {len(upload_results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if successful > 0:
        print("\nSuccessfully uploaded templates:")
        for result in upload_results:
            if result.get("status") == "success":
                print(f"  - {result.get('name')}: {result.get('cid')}")
    
    if failed > 0:
        print("\nFailed templates:")
        for result in upload_results:
            if result.get("status") != "success":
                print(f"  - {result.get('name')}: {result.get('error', 'Unknown error')}")
    
    # Save results to file
    results_file = Path(__file__).parent.parent / "test_logs" / "ipfs_upload_results.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    results_file.write_text(json.dumps(upload_results, indent=2))
    print(f"\n[OK] Results saved to: {results_file}")
    
    print("=" * 70)
    
    return successful == len(upload_results)

async def main():
    """Main entry point"""
    success = await upload_all_templates()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

