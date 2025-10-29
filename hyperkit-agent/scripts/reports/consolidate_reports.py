#!/usr/bin/env python3
"""
Markdown Consolidation Script - Brutal CTO Solution
Consolidates all sharded reports into single files per category
"""

import os
import re
from pathlib import Path
from datetime import datetime

# Category mappings: directory -> consolidated filename
CONSOLIDATION_MAP = {
    'IPFS_RAG': {
        'dir': 'IPFS_RAG',
        'output': 'IPFS.md',
        'exclude': ['README.md', 'IPFS.md']
    },
    'ACCOMPLISHED': {
        'dir': 'ACCOMPLISHED',
        'output': 'ACCOMPLISHED.md',
        'exclude': ['README.md', 'ACCOMPLISHED.md']
    },
    'AUDIT': {
        'dir': 'AUDIT',
        'output': 'AUDIT.md',
        'exclude': ['README.md', 'AUDIT.md']
    },
    'security': {
        'dir': 'security',
        'output': 'SECURITY.md',
        'exclude': ['README.md', 'SECURITY.md']
    },
    'COMPLIANCE': {
        'dir': 'COMPLIANCE',
        'output': 'COMPLIANCE.md',
        'exclude': ['README.md', 'COMPLIANCE.md']
    },
    'TODO': {
        'dir': 'TODO',
        'output': 'TODO_TRACKER.md',
        'exclude': ['README.md', 'TODO_TRACKER.md']
    },
    'INFRASTRUCTURE': {
        'dir': 'INFRASTRUCTURE',
        'output': 'INFRASTRUCTURE.md',
        'exclude': ['README.md', 'INFRASTRUCTURE.md']
    },
    'QUALITY': {
        'dir': 'QUALITY',
        'output': 'QUALITY.md',
        'exclude': ['README.md', 'QUALITY.md']
    },
    'STATUS': {
        'dir': 'STATUS',
        'output': 'STATUS.md',
        'exclude': ['README.md', 'STATUS.md']
    },
    'integration': {
        'dir': 'integration',
        'output': 'INTEGRATION.md',
        'exclude': ['README.md', 'INTEGRATION.md']
    },
    'api-audits': {
        'dir': 'api-audits',
        'output': 'API_AUDITS.md',
        'exclude': ['README.md', 'API_AUDITS.md']
    },
}

def extract_section_title(filename):
    """Extract a clean section title from filename"""
    # Remove extension and common prefixes
    title = filename.replace('.md', '').replace('IPFS_RAG_', '').replace('_', ' ')
    # Capitalize properly
    title = ' '.join(word.capitalize() for word in title.split())
    return title

def create_header(title, original_file):
    """Create a section header for merged content"""
    return f"\n\n{'='*80}\n## {title}\n{'='*80}\n\n*From: `{original_file}`*\n\n"

def consolidate_category(category_name, config, reports_root):
    """Consolidate all markdown files in a category"""
    category_dir = reports_root / config['dir']
    output_file = category_dir / config['output']
    
    if not category_dir.exists():
        print(f"[WARNING] Category directory not found: {category_dir}")
        return False
    
    # Find all markdown files
    md_files = sorted([
        f for f in category_dir.glob('*.md')
        if f.name not in config['exclude']
    ])
    
    if not md_files:
        print(f"[INFO] No files to consolidate in {category_dir}")
        return True
    
    print(f"[CONSOLIDATING] {len(md_files)} files from {config['dir']}/ into {config['output']}")
    
    # Create consolidated content
    consolidated_content = []
    consolidated_content.append(f"# {config['output'].replace('.md', '').replace('_', ' ').title()}")
    consolidated_content.append(f"\n**Consolidated Report**")
    consolidated_content.append(f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d')}")
    consolidated_content.append(f"\n**Source Files**: {len(md_files)} individual reports merged")
    consolidated_content.append("\n---")
    consolidated_content.append("\n\n## Table of Contents\n")
    
    # Build table of contents
    toc_items = []
    for md_file in md_files:
        section_title = extract_section_title(md_file.name)
        anchor = section_title.lower().replace(' ', '-')
        toc_items.append(f"- [{section_title}](#{anchor})")
    
    consolidated_content.extend(toc_items)
    consolidated_content.append("\n---")
    
    # Merge content
    files_merged = 0
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            section_title = extract_section_title(md_file.name)
            consolidated_content.append(create_header(section_title, md_file.name))
            
            # Remove frontmatter if present
            content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
            
            # Add content
            consolidated_content.append(content)
            files_merged += 1
            
        except Exception as e:
            print(f"[WARNING] Error reading {md_file}: {e}")
            continue
    
    # Write consolidated file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(consolidated_content))
        print(f"[SUCCESS] Created {output_file} ({files_merged} files merged)")
        return True
    except Exception as e:
        print(f"[ERROR] Error writing {output_file}: {e}")
        return False

def main():
    """Main consolidation process"""
    script_dir = Path(__file__).parent
    reports_root = script_dir  # REPORTS directory
    
    print("=" * 80)
    print("MARKDOWN CONSOLIDATION - BRUTAL CTO SOLUTION")
    print("=" * 80)
    print()
    
    results = {}
    for category_name, config in CONSOLIDATION_MAP.items():
        print(f"\n[Processing] {category_name}...")
        success = consolidate_category(category_name, config, reports_root)
        results[category_name] = success
    
    print("\n" + "=" * 80)
    print("CONSOLIDATION SUMMARY")
    print("=" * 80)
    
    for category, success in results.items():
        status = "[OK]" if success else "[FAIL]"
        print(f"{status} {category}")
    
    print("\n[NEXT STEP] Review consolidated files, then delete original files")
    print("   Use: Delete obsolete individual files after merging")

if __name__ == "__main__":
    main()

