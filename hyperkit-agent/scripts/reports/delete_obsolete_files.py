#!/usr/bin/env python3
"""
Delete obsolete individual files after consolidation
Run this AFTER reviewing consolidated files
"""
from pathlib import Path
import shutil

# Files to keep (consolidated files and READMEs)
KEEP_FILES = {
    'IPFS_RAG': ['README.md', 'IPFS.md'],
    'ACCOMPLISHED': ['README.md', 'ACCOMPLISHED.md'],
    'AUDIT': ['README.md', 'AUDIT.md'],
    'security': ['README.md', 'SECURITY.md'],
    'COMPLIANCE': ['README.md', 'COMPLIANCE.md'],
    'TODO': ['README.md', 'TODO_TRACKER.md'],
    'INFRASTRUCTURE': ['README.md', 'INFRASTRUCTURE.md'],
    'QUALITY': ['README.md', 'QUALITY.md'],
    'STATUS': ['README.md', 'STATUS.md'],
    'integration': ['README.md', 'INTEGRATION.md'],
    'api-audits': ['README.md', 'API_AUDITS.md'],
}

# Archive directories (consolidate but don't delete old files - they're archived)
ARCHIVE_DIRS = ['archive/fixes', 'archive/old-reports']

def delete_obsolete_files():
    """Delete obsolete files after consolidation (dry-run by default)"""
    reports_root = Path(__file__).parent
    dry_run = True  # Set to False to actually delete
    
    print("=" * 80)
    print("DELETE OBSOLETE FILES - POST CONSOLIDATION")
    print("=" * 80)
    print()
    
    if dry_run:
        print("[DRY RUN MODE] Files listed will not be deleted")
        print("Set dry_run = False to actually delete files\n")
    
    total_to_delete = 0
    
    for category, keep_list in KEEP_FILES.items():
        category_dir = reports_root / category
        if not category_dir.exists():
            continue
        
        print(f"\n[{category}]")
        md_files = list(category_dir.glob('*.md'))
        
        for md_file in md_files:
            if md_file.name in keep_list:
                print(f"  [KEEP] {md_file.name}")
            else:
                total_to_delete += 1
                if dry_run:
                    print(f"  [DELETE] {md_file.name}")
                else:
                    try:
                        md_file.unlink()
                        print(f"  [DELETED] {md_file.name}")
                    except Exception as e:
                        print(f"  [ERROR] {md_file.name}: {e}")
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: {total_to_delete} files would be deleted")
    if dry_run:
        print("\nTo actually delete, set dry_run = False in the script")
    print("=" * 80)

if __name__ == "__main__":
    delete_obsolete_files()

