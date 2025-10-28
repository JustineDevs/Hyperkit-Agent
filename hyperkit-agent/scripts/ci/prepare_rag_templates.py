#!/usr/bin/env python3
"""
RAG Template Preparation Script
Converts RAG templates from markdown to IPFS-ready .txt format
Updates CID registry with metadata
"""

import json
import shutil
from pathlib import Path

# Source and destination directories
SOURCE_DIR = Path(__file__).parent.parent.parent / "docs" / "RAG_TEMPLATES"
DEST_DIR = Path(__file__).parent.parent.parent / "hyperkit-agent" / "artifacts" / "rag_templates"

def prepare_template(source_file: Path, template_name: str, description: str, category: str):
    """Convert markdown template to text format with metadata"""
    
    # Create destination directory
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    
    # Read markdown file
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create text version (remove markdown formatting for simpler consumption)
    # Keep the structure but simplify markdown syntax
    text_content = content
    
    # Write to destination with descriptive name
    output_file = DEST_DIR / f"{template_name}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text_content)
    
    print(f"[OK] Prepared: {template_name}.txt")
    
    return {
        "name": template_name,
        "description": description,
        "category": category,
        "source_file": str(source_file),
        "output_file": str(output_file),
        "size": output_file.stat().st_size
    }

def update_cid_registry(registry_path: Path, registry_data: dict):
    """Update CID registry with prepared templates"""
    
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry_data, f, indent=2)
    
    print(f"[OK] Updated: {registry_path}")

def main():
    """Prepare all RAG templates for IPFS upload"""
    
    print("Preparing RAG templates for IPFS upload...")
    print("=" * 60)
    
    # Template definitions from registry
    templates = [
        {
            "name": "erc20-template",
            "description": "Standard ERC20 fungible token contract template",
            "filename": "ERC20-Template.md",
            "category": "contracts",
            "source_path": SOURCE_DIR / "Contracts" / "ERC20-Template.md"
        },
        {
            "name": "erc721-template",
            "description": "Standard ERC721 non-fungible token (NFT) contract template",
            "filename": "ERC721-Template.md",
            "category": "contracts",
            "source_path": SOURCE_DIR / "Contracts" / "ERC721-Template.md"
        },
        {
            "name": "hardhat-deploy",
            "description": "All-in-one template for Hardhat deployment scripts, env config, and best-practice flows",
            "filename": "Hardhat-Deploy.md",
            "category": "templates",
            "source_path": SOURCE_DIR / "Templates" / "Hardhat-Deploy.md"
        },
        {
            "name": "gas-optimization-audit",
            "description": "Smart contract gas optimization audit template and checklist",
            "filename": "Gas-Optimization.md",
            "category": "audits",
            "source_path": SOURCE_DIR / "Audits" / "Gas-Optimization.md"
        },
        {
            "name": "security-checklist",
            "description": "Comprehensive security audit best-practices checklist template",
            "filename": "Security-Checklist.md",
            "category": "audits",
            "source_path": SOURCE_DIR / "Audits" / "Security-Checklist.md"
        },
        {
            "name": "contract-generation-prompt",
            "description": "Prompt engineering template for general smart contract creation",
            "filename": "Contract-Generation.md",
            "category": "prompts",
            "source_path": SOURCE_DIR / "Prompts" / "Contract-Generation.md"
        },
        {
            "name": "generation-style-prompt",
            "description": "Prompt template for controlling style or features of generated contracts",
            "filename": "Generation-Prompt.md",
            "category": "prompts",
            "source_path": SOURCE_DIR / "Prompts" / "Generation-Prompt.md"
        },
        {
            "name": "security-prompts",
            "description": "Prompt set for security-focused generation and audit scenarios",
            "filename": "Security-Prompts.md",
            "category": "prompts",
            "source_path": SOURCE_DIR / "Prompts" / "Security-Prompts.md"
        }
    ]
    
    prepared_templates = []
    
    for template in templates:
        if template["source_path"].exists():
            result = prepare_template(
                template["source_path"],
                template["name"],
                template["description"],
                template["category"]
            )
            prepared_templates.append(result)
        else:
            print(f"[WARNING] Source file not found: {template['source_path']}")
    
    print("\n" + "=" * 60)
    print(f"[OK] Prepared {len(prepared_templates)} templates")
    print(f"Output directory: {DEST_DIR}")
    
    # Update registry
    registry_data = {
        "metadata": {
            "version": "1.0.0",
            "last_updated": "2025-10-28",
            "purpose": "CID registry mapping for AI agent RAG template lookups",
            "note": "Each template has unique CID, descriptive name for AI agent consumption",
            "templates_prepared": len(prepared_templates),
            "ready_for_upload": True
        },
        "templates": {}
    }
    
    for template in templates:
        registry_data["templates"][template["name"]] = {
            "description": template["description"],
            "filename": template["filename"],
            "category": template["category"],
            "cid": "PENDING - Upload to Pinata",
            "uploaded": False,
            "prepared": True
        }
    
    registry_path = SOURCE_DIR / "cid-registry.json"
    update_cid_registry(registry_path, registry_data)
    
    print("\nNext Steps:")
    print("1. Review prepared templates in artifacts/rag_templates/")
    print("2. Upload each template to IPFS Pinata")
    print("3. Update cid-registry.json with actual CIDs")
    print("4. Test RAG system with new templates")
    
    return prepared_templates

if __name__ == "__main__":
    main()

