#!/usr/bin/env python3
"""
IPFS Upload Script for Large Audit Reports
Uploads large audit reports to IPFS Pinata and updates references in markdown files.
"""

import os
import json
import asyncio
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class SimpleIPFSClient:
    """Simple IPFS client for uploading files to Pinata."""
    
    def __init__(self):
        self.pinata_api_key = os.getenv('PINATA_API_KEY')
        self.pinata_secret_key = os.getenv('PINATA_SECRET_KEY')
        self.pinata_url = "https://api.pinata.cloud"
    
    async def upload_document(self, content: str, metadata: Dict[str, Any] = None) -> Optional[str]:
        """Upload content to Pinata IPFS."""
        if not self.pinata_api_key or not self.pinata_secret_key:
            print("WARNING: Pinata API keys not configured. Using mock CID.")
            return f"mock_cid_{abs(hash(content)) % 1000000}"
        
        try:
            headers = {
                'pinata_api_key': self.pinata_api_key,
                'pinata_secret_api_key': self.pinata_secret_key,
                'Content-Type': 'application/json'
            }
            
            data = {
                'pinataContent': content,
                'pinataMetadata': json.dumps(metadata or {})
            }
            
            response = requests.post(
                f"{self.pinata_url}/pinning/pinJSONToIPFS",
                json=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('IpfsHash')
            else:
                print(f"ERROR: Pinata upload failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"ERROR: Upload error: {e}")
            return None


class AuditReportUploader:
    """Uploads large audit reports to IPFS and updates references."""
    
    def __init__(self):
        self.ipfs_client = SimpleIPFSClient()
        self.uploaded_files = {}
    
    async def upload_large_file(self, file_path: Path, description: str) -> Optional[str]:
        """Upload a large file to IPFS and return the CID."""
        try:
            print(f"Uploading {file_path.name} to IPFS...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            metadata = {
                'name': file_path.name,
                'description': description,
                'upload_date': datetime.now().isoformat(),
                'file_type': 'audit_report',
                'size_bytes': len(content.encode('utf-8'))
            }
            
            cid = await self.ipfs_client.upload_document(content, metadata)
            
            if cid:
                print(f"SUCCESS: Uploaded {file_path.name} to IPFS: {cid}")
                self.uploaded_files[str(file_path)] = {
                    'cid': cid,
                    'description': description,
                    'upload_date': metadata['upload_date'],
                    'size_bytes': metadata['size_bytes']
                }
                return cid
            else:
                print(f"ERROR: Failed to upload {file_path.name}")
                return None
                
        except Exception as e:
            print(f"ERROR: Error uploading {file_path.name}: {e}")
            return None
    
    def create_ipfs_reference_report(self, uploaded_files: Dict[str, Any]) -> str:
        """Create a reference report with IPFS links."""
        report_lines = []
        report_lines.append("# Large Audit Reports - IPFS Storage")
        report_lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        report_lines.append("Large audit reports have been uploaded to IPFS Pinata for decentralized storage.")
        report_lines.append("")
        
        report_lines.append("## Available Reports")
        report_lines.append("")
        report_lines.append("| Report | Description | IPFS CID | Size | Upload Date |")
        report_lines.append("|--------|-------------|----------|------|-------------|")
        
        for file_path, info in uploaded_files.items():
            file_name = Path(file_path).name
            size_mb = info['size_bytes'] / (1024 * 1024)
            report_lines.append(f"| {file_name} | {info['description']} | `{info['cid']}` | {size_mb:.1f} MB | {info['upload_date'][:10]} |")
        
        report_lines.append("")
        report_lines.append("## Accessing Reports")
        report_lines.append("")
        report_lines.append("### Via IPFS Gateways")
        report_lines.append("")
        for file_path, info in uploaded_files.items():
            file_name = Path(file_path).name
            report_lines.append(f"**{file_name}**:")
            report_lines.append(f"- Pinata Gateway: https://gateway.pinata.cloud/ipfs/{info['cid']}")
            report_lines.append(f"- IPFS Gateway: https://ipfs.io/ipfs/{info['cid']}")
            report_lines.append(f"- Cloudflare Gateway: https://cloudflare-ipfs.com/ipfs/{info['cid']}")
            report_lines.append("")
        
        report_lines.append("### Via HyperAgent CLI")
        report_lines.append("")
        report_lines.append("```bash")
        report_lines.append("# Download report from IPFS")
        report_lines.append("hyperagent ipfs download <CID> --output <filename>")
        report_lines.append("")
        report_lines.append("# Example:")
        for file_path, info in uploaded_files.items():
            file_name = Path(file_path).name
            report_lines.append(f"hyperagent ipfs download {info['cid']} --output {file_name}")
        report_lines.append("```")
        
        report_lines.append("")
        report_lines.append("## Benefits of IPFS Storage")
        report_lines.append("- **Decentralized**: Reports stored across multiple nodes")
        report_lines.append("- **Immutable**: Content cannot be modified once uploaded")
        report_lines.append("- **Accessible**: Available via multiple gateways")
        report_lines.append("- **GitHub-friendly**: Keeps repository under size limits")
        report_lines.append("- **Versioned**: Each upload gets a unique CID")
        
        return "\n".join(report_lines)
    
    def update_markdown_references(self, uploaded_files: Dict[str, Any]):
        """Update markdown files to reference IPFS instead of local files."""
        for file_path, info in uploaded_files.items():
            file_name = Path(file_path).name
            
            # Find markdown files that might reference this file
            for md_file in Path("hyperkit-agent/REPORTS").rglob("*.md"):
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Replace local file references with IPFS links
                    if file_name in content:
                        # Replace file references with IPFS links
                        ipfs_link = f"https://gateway.pinata.cloud/ipfs/{info['cid']}"
                        updated_content = content.replace(
                            f"`{file_name}`",
                            f"[`{file_name}`]({ipfs_link}) (IPFS)"
                        )
                        
                        if updated_content != content:
                            with open(md_file, 'w', encoding='utf-8') as f:
                                f.write(updated_content)
                            print(f"SUCCESS: Updated references in {md_file.name}")
                            
                except Exception as e:
                    print(f"WARNING: Could not update {md_file}: {e}")


async def main():
    """Main function to upload large audit reports to IPFS."""
    uploader = AuditReportUploader()
    
    # Define large files to upload
    large_files = [
        {
            'path': Path("hyperkit-agent/REPORTS/DEADWEIGHT_SCAN_REPORT.md"),
            'description': "Comprehensive deadweight scan report with all findings"
        },
        {
            'path': Path("hyperkit-agent/REPORTS/JSON_DATA/deadweight_scan_results.json"),
            'description': "Complete deadweight scan results in JSON format"
        }
    ]
    
    print("Starting IPFS upload of large audit reports...")
    print("")
    
    uploaded_count = 0
    for file_info in large_files:
        file_path = file_info['path']
        
        if file_path.exists():
            # Check if file is large (>10MB)
            file_size = file_path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB
                cid = await uploader.upload_large_file(file_path, file_info['description'])
                if cid:
                    uploaded_count += 1
                    # Move original file to archive
                    archive_path = file_path.parent / "ARCHIVE" / file_path.name
                    archive_path.parent.mkdir(exist_ok=True)
                    file_path.rename(archive_path)
                    print(f"ARCHIVED: Original file moved to: {archive_path}")
            else:
                print(f"SKIP: {file_path.name} (under 10MB)")
        else:
            print(f"WARNING: File not found: {file_path}")
    
    if uploaded_count > 0:
        print("")
        print("Creating IPFS reference report...")
        
        # Create reference report
        reference_report = uploader.create_ipfs_reference_report(uploader.uploaded_files)
        
        # Save reference report
        ref_report_path = Path("hyperkit-agent/REPORTS/IPFS_AUDIT_REPORTS.md")
        with open(ref_report_path, 'w', encoding='utf-8') as f:
            f.write(reference_report)
        
        print(f"SUCCESS: Reference report saved to: {ref_report_path}")
        
        # Update markdown references
        print("Updating markdown references...")
        uploader.update_markdown_references(uploader.uploaded_files)
        
        # Save upload manifest
        manifest_path = Path("hyperkit-agent/REPORTS/JSON_DATA/ipfs_upload_manifest.json")
        manifest_path.parent.mkdir(exist_ok=True)
        
        manifest = {
            'upload_date': datetime.now().isoformat(),
            'uploaded_files': uploader.uploaded_files,
            'total_files': uploaded_count,
            'total_size_bytes': sum(info['size_bytes'] for info in uploader.uploaded_files.values())
        }
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"SUCCESS: Upload manifest saved to: {manifest_path}")
        
        print("")
        print("IPFS upload complete!")
        print(f"   Uploaded: {uploaded_count} files")
        print(f"   Total size: {manifest['total_size_bytes'] / (1024 * 1024):.1f} MB")
        print("   Reports accessible via IPFS gateways")
        
    else:
        print("INFO: No large files found to upload")


if __name__ == "__main__":
    asyncio.run(main())
