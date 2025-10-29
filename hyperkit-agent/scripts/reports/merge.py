#!/usr/bin/env python3
"""
Merge Individual Markdown Files into Consolidated Files

Consolidates all individual *.md files in each REPORTS subdirectory into
the existing consolidated file, then removes the merged files.

Example:
  ACCOMPLISHED/ACCOMPLISHED.md (exists)
  ACCOMPLISHED/AUDIT_COMPLETION_SUMMARY.md (new - will be merged)
  ACCOMPLISHED/AUDIT_FIXES_APPLIED.md (new - will be merged)
  
  After running: Only ACCOMPLISHED.md remains (with all content merged)
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
        'exclude': ['README.md', 'ACCOMPLISHED.md', 'CONSOLIDATION_COMPLETE.md']
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
    'archive': {
        'dir': 'archive',
        'output': 'FIXES_ARCHIVE.md',
        'exclude': ['README.md', 'FIXES_ARCHIVE.md']
    },
}

def extract_section_title(filename):
    """Extract a clean section title from filename"""
    # Remove extension and common prefixes
    title = filename.replace('.md', '').replace('IPFS_RAG_', '').replace('_', ' ')
    # Capitalize properly
    title = ' '.join(word.capitalize() for word in title.split())
    return title

def create_section_header(title, original_file):
    """Create a section header for merged content"""
    return f"\n\n{'='*80}\n## {title}\n{'='*80}\n\n*From: `{original_file}`*\n\n"

def remove_frontmatter(content):
    """Remove YAML frontmatter if present"""
    content = re.sub(r'^---\n[\s\S]*?\n---\n', '', content, flags=re.MULTILINE)
    return content.strip()

def merge_files_into_consolidated(category_name, config, reports_root, dry_run=False):
    """
    Merge all individual markdown files into the consolidated file.
    
    Args:
        category_name: Category name (e.g., 'ACCOMPLISHED')
        config: Configuration dict with 'dir', 'output', 'exclude'
        reports_root: Path to REPORTS directory
        dry_run: If True, don't actually merge/delete, just report
    
    Returns:
        Tuple of (success: bool, files_merged: int, files_deleted: list)
    """
    category_dir = reports_root / config['dir']
    consolidated_file = category_dir / config['output']
    
    if not category_dir.exists():
        print(f"[SKIP] Category directory not found: {category_dir}")
        return False, 0, []
    
    if not consolidated_file.exists():
        print(f"[WARNING] Consolidated file not found: {consolidated_file}")
        print(f"         Creating new consolidated file...")
        if not dry_run:
            # Create basic consolidated file
            with open(consolidated_file, 'w', encoding='utf-8') as f:
                f.write(f"# {config['output'].replace('.md', '').replace('_', ' ').title()}\n\n")
                f.write(f"**Consolidated Report**\n\n")
                f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d')}\n\n")
                f.write("---\n\n")
    
    # Find all markdown files to merge
    all_md_files = sorted([f for f in category_dir.glob('*.md')])
    files_to_merge = [
        f for f in all_md_files
        if f.name not in config['exclude']
    ]
    
    if not files_to_merge:
        print(f"[INFO] No files to merge in {category_dir}")
        return True, 0, []
    
    print(f"\n[{category_name}]")
    print(f"  Consolidated file: {consolidated_file.name}")
    print(f"  Files found: {len(files_to_merge)}")
    
    # Read existing consolidated file to check for duplicates
    try:
        with open(consolidated_file, 'r', encoding='utf-8') as f:
            consolidated_content = f.read()
    except Exception as e:
        print(f"[ERROR] Could not read {consolidated_file}: {e}")
        return False, 0, []
    
    # Check for already merged files by looking for "*From: `filename`*" pattern
    # This is the standard marker used when files are merged
    already_merged = set()
    
    for md_file in files_to_merge:
        # Check if file is already referenced in consolidated content
        # Look for the standard "From: filename" pattern
        from_pattern = f'*From: `{md_file.name}`*'
        from_pattern_alt = f'*From: `{md_file.name}`'  # Without closing *
        
        # Also check for section title
        section_title = extract_section_title(md_file.name)
        section_pattern = f'## {section_title}'
        
        # Check consolidated content for these patterns
        if from_pattern in consolidated_content or from_pattern_alt in consolidated_content:
            already_merged.add(md_file)
        elif section_pattern in consolidated_content:
            # Double-check by looking at the context around the section
            # If section exists and has "From:" nearby, it's already merged
            section_idx = consolidated_content.find(section_pattern)
            if section_idx >= 0:
                # Look in the next 200 chars for "From:" reference
                context = consolidated_content[section_idx:section_idx+200]
                if '*From:' in context or '*from:' in context.lower():
                    already_merged.add(md_file)
    
    # Separate files into: need merging vs already merged (but should still delete)
    files_to_merge_new = [f for f in files_to_merge if f not in already_merged]
    files_already_merged = list(already_merged)
    
    if files_already_merged:
        print(f"  [SKIP MERGE] {len(files_already_merged)} file(s) already in consolidated file (will delete): {[f.name for f in files_already_merged]}")
    
    if not files_to_merge_new and not files_already_merged:
        print(f"  [INFO] No files to process")
        return True, 0, []
    
    # If only already-merged files exist, we just delete them without merging
    if not files_to_merge_new:
        if dry_run:
            for f in files_already_merged:
                print(f"    [WOULD DELETE] {f.name} (already merged)")
        else:
            # Delete files that are already merged
            deleted_count = 0
            deleted_files = []
            for md_file in files_already_merged:
                try:
                    md_file.unlink()
                    deleted_count += 1
                    deleted_files.append(str(md_file))
                    print(f"    [DELETED] {md_file.name} (already merged)")
                except Exception as e:
                    print(f"    [ERROR] Could not delete {md_file.name}: {e}")
            return True, 0, deleted_files
    
    # Use the new files list for merging
    files_to_merge = files_to_merge_new
    
    if dry_run:
        if files_to_merge:
            print(f"  Files to merge: {len(files_to_merge)}")
            for f in files_to_merge:
                print(f"    [WOULD MERGE] {f.name}")
        total_deleted = len(files_to_merge) + len(files_already_merged)
        return True, len(files_to_merge), [str(f) for f in files_to_merge] + [str(f) for f in files_already_merged]
    
    # Ensure there's a separator before appending
    if not consolidated_content.endswith('\n\n'):
        consolidated_content += '\n\n'
    
    # Add merge timestamp header
    consolidated_content += f"\n\n---\n\n"
    consolidated_content += f"**Merged**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    consolidated_content += f"**Files Added**: {len(files_to_merge)}\n\n"
    
    # Merge each file into consolidated file
    files_merged = 0
    merged_files = []
    
    for md_file in files_to_merge:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Remove frontmatter
            file_content = remove_frontmatter(file_content)
            
            # Create section header
            section_title = extract_section_title(md_file.name)
            header = create_section_header(section_title, md_file.name)
            
            # Append to consolidated content
            consolidated_content += header
            consolidated_content += file_content
            consolidated_content += '\n\n'
            
            files_merged += 1
            merged_files.append(md_file)
            print(f"    [MERGED] {md_file.name}")
            
        except Exception as e:
            print(f"    [ERROR] Failed to merge {md_file.name}: {e}")
            continue
    
    # Write updated consolidated file
    try:
        with open(consolidated_file, 'w', encoding='utf-8') as f:
            f.write(consolidated_content)
        print(f"    [UPDATED] {consolidated_file.name}")
    except Exception as e:
        print(f"[ERROR] Could not write {consolidated_file}: {e}")
        return False, files_merged, []
    
    # Delete merged files
    files_deleted = []
    for md_file in merged_files:
        try:
            md_file.unlink()
            files_deleted.append(str(md_file))
            print(f"    [DELETED] {md_file.name}")
        except Exception as e:
            print(f"    [ERROR] Could not delete {md_file.name}: {e}")
    
    # Also delete files that were already merged (if any)
    for md_file in files_already_merged:
        try:
            md_file.unlink()
            files_deleted.append(str(md_file))
            print(f"    [DELETED] {md_file.name} (was already merged)")
        except Exception as e:
            print(f"    [ERROR] Could not delete {md_file.name}: {e}")
    
    total_deleted = len(files_deleted)
    return True, files_merged, files_deleted

def merge_all_categories(reports_root, dry_run=False):
    """
    Merge files for all categories defined in CONSOLIDATION_MAP.
    
    Args:
        reports_root: Path to REPORTS directory
        dry_run: If True, don't actually merge/delete, just report
    
    Returns:
        Dict with category -> (success, files_merged, files_deleted)
    """
    results = {}
    total_merged = 0
    total_deleted = 0
    
    print("=" * 80)
    print("MERGE INDIVIDUAL FILES INTO CONSOLIDATED FILES")
    print("=" * 80)
    if dry_run:
        print("[DRY RUN MODE] Files will not be merged or deleted\n")
    else:
        print("[LIVE MODE] Files will be merged and deleted\n")
    print()
    
    for category_name, config in CONSOLIDATION_MAP.items():
        success, files_merged, files_deleted = merge_files_into_consolidated(
            category_name, config, reports_root, dry_run
        )
        results[category_name] = {
            'success': success,
            'files_merged': files_merged,
            'files_deleted': files_deleted
        }
        total_merged += files_merged
        total_deleted += len(files_deleted)
    
    # Summary
    print("\n" + "=" * 80)
    print("MERGE SUMMARY")
    print("=" * 80)
    
    for category, result in results.items():
        status = "[OK]" if result['success'] else "[FAIL]"
        merged = result['files_merged']
        deleted = len(result['files_deleted'])
        print(f"{status} {category}: {merged} merged, {deleted} deleted")
    
    print(f"\n[SUMMARY] Total: {total_merged} files merged, {total_deleted} files deleted")
    
    if dry_run:
        print("\n[DRY RUN] Set dry_run=False to actually merge and delete files")
    else:
        print("\n[COMPLETE] All files merged and deleted")
    
    return results

def main():
    """Main execution"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Merge individual markdown files into consolidated files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run on all directories
  python merge.py --dry-run
  
  # Process single directory
  python merge.py --directory ACCOMPLISHED
  
  # Actually merge all directories
  python merge.py
        """
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Dry run mode - preview changes without merging/deleting'
    )
    parser.add_argument(
        '--directory', '-d',
        type=str,
        metavar='CATEGORY',
        help='Specific category/directory to process (e.g., ACCOMPLISHED, AUDIT). If not provided, processes all.'
    )
    
    args = parser.parse_args()
    
    # Determine REPORTS directory location
    script_dir = Path(__file__).parent
    # REPORTS directory is at hyperkit-agent/REPORTS/
    # Script is at hyperkit-agent/scripts/reports/, so go up 2 levels
    reports_root = script_dir.parent.parent / 'REPORTS'
    
    if not reports_root.exists():
        print(f"[ERROR] REPORTS directory not found: {reports_root}")
        print(f"        Expected at: {reports_root.absolute()}")
        sys.exit(1)
    
    if args.directory:
        # Process single directory
        category_found = False
        for category_name, config in CONSOLIDATION_MAP.items():
            if category_name.lower() == args.directory.lower() or \
               config['dir'].lower() == args.directory.lower():
                print(f"[PROCESSING] Single directory: {category_name}\n")
                success, files_merged, files_deleted = merge_files_into_consolidated(
                    category_name, config, reports_root, args.dry_run
                )
                category_found = True
                if success:
                    print(f"\n[SUCCESS] {files_merged} files merged, {len(files_deleted)} deleted")
                    sys.exit(0)
                else:
                    print(f"\n[FAILED] Merge failed for {category_name}")
                    sys.exit(1)
        
        if not category_found:
            print(f"[ERROR] Category '{args.directory}' not found")
            print(f"Available categories: {', '.join(CONSOLIDATION_MAP.keys())}")
            sys.exit(1)
    else:
        # Process all categories
        results = merge_all_categories(reports_root, args.dry_run)
        
        # Check if all succeeded
        all_success = all(r['success'] for r in results.values())
        sys.exit(0 if all_success else 1)

if __name__ == "__main__":
    main()

