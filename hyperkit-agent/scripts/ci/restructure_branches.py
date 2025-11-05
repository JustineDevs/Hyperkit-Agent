#!/usr/bin/env python3
"""
Restructure Branches for Devlog Strategy

Removes code files from devlog and removes non-essential docs from main.
This creates the proper separation:
- main: Code + essential docs only
- devlog: Documentation only (.md files and related)
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import List, Set

# Load whitelist
WHITELIST_FILE = Path(__file__).parent / "essential_docs_whitelist.json"


def load_whitelist():
    """Load essential docs whitelist."""
    with open(WHITELIST_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_code_file_extensions():
    """Get list of code file extensions to remove from devlog."""
    return {
        '.py', '.pyc', '.pyo', '.pyd',
        '.sol', '.js', '.ts', '.jsx', '.tsx',
        '.java', '.cpp', '.c', '.h', '.hpp',
        '.go', '.rs', '.rb', '.php',
        '.yaml', '.yml', '.toml', '.json',
        '.lock', '.log', '.cache',
        # Keep essential config files in devlog
    }


def get_essential_config_files():
    """Files that should stay in both branches."""
    return {
        'package.json',
        'VERSION',
        'hyperkit-agent/pyproject.toml',
        'hyperkit-agent/config.yaml',
        'hyperkit-agent/env.example',
    }


def get_code_directories():
    """Directories containing code that should be removed from devlog."""
    return {
        'hyperkit-agent/core/',
        'hyperkit-agent/services/',
        'hyperkit-agent/cli/',
        'hyperkit-agent/contracts/',
        'hyperkit-agent/tests/',
        'hyperkit-agent/scripts/ci/run_all_updates.py',  # Keep sync scripts
        'hyperkit-agent/scripts/utils/branch_awareness.py',  # Keep utilities
        'hyperkit-agent/scripts/release/sync-to-devlog.js',  # ✅ JS version (replaced Python)
        'hyperkit-agent/scripts/release/update-readme-links.js',  # ✅ JS version (replaced Python)
        'hyperkit-agent/scripts/ci/validate_branch_sync.py',  # ✅ Keep (Python validation)
        'hyperkit-agent/scripts/ci/essential_docs_whitelist.json',
    }


def remove_code_from_devlog(repo_root: Path):
    """Remove all code files from devlog branch, keeping only docs."""
    import os
    
    print("[CLEAN] Removing code files from devlog branch...")
    
    code_exts = get_code_file_extensions()
    code_dirs = get_code_directories()
    essential_configs = get_essential_config_files()
    
    # Keep these scripts in devlog (needed for doc management)
    keep_scripts = {
        'hyperkit-agent/scripts/release/sync-to-devlog.js',  # ✅ JS version (replaced Python)
        'hyperkit-agent/scripts/release/update-readme-links.js',  # ✅ JS version (replaced Python)
        'hyperkit-agent/scripts/ci/validate_branch_sync.py',  # ✅ Keep (Python validation)
        'hyperkit-agent/scripts/ci/essential_docs_whitelist.json',
        'hyperkit-agent/scripts/utils/branch_awareness.py',
    }
    
    # Files to remove
    files_to_remove = []
    
    # Walk through repo
    for root, dirs, files in os.walk(repo_root):
        # Skip git and common ignored dirs
        if '.git' in root or any(skip in root for skip in 
            ['node_modules', '__pycache__', '.pytest_cache', '.venv', 'venv', '.git']):
            continue
        
        rel_root = Path(root).relative_to(repo_root)
        
        # Check if this is a code directory
        is_code_dir = any(str(rel_root).startswith(code_dir.rstrip('/')) for code_dir in code_dirs)
        
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(repo_root)
            
            # Skip essential config files
            if str(rel_path) in essential_configs:
                continue
            
            # Skip scripts needed for doc management
            if str(rel_path) in keep_scripts:
                continue
            
            # Skip if it's a markdown file
            if file_path.suffix == '.md':
                continue
            
            # Skip if it's documentation-related (images, etc.)
            if file_path.suffix in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.pdf']:
                # Only keep if in docs/REPORTS directories
                if 'docs' in str(rel_path) or 'REPORTS' in str(rel_path):
                    continue
                else:
                    files_to_remove.append(rel_path)
                    continue
            
            # Remove code files
            if file_path.suffix in code_exts:
                files_to_remove.append(rel_path)
                continue
            
            # Remove files from code directories
            if is_code_dir:
                files_to_remove.append(rel_path)
                continue
    
    # Remove files
    if files_to_remove:
        print(f"[REMOVE] Removing {len(files_to_remove)} code files from devlog...")
        for file_path in files_to_remove[:10]:  # Show first 10
            print(f"  - {file_path}")
        if len(files_to_remove) > 10:
            print(f"  ... and {len(files_to_remove) - 10} more")
        
        # Use git rm to remove files
        for file_path in files_to_remove:
            try:
                subprocess.run(['git', 'rm', '--cached', str(file_path)], 
                             cwd=repo_root, check=False, capture_output=True)
            except:
                pass
        
        return True
    
    return False


def remove_docs_from_main(repo_root: Path, whitelist):
    """Remove non-essential documentation from main branch."""
    import os
    
    print("[CLEAN] Removing non-essential docs from main branch...")
    
    essential_files = set(whitelist.get("files", []))
    keep_dirs = set(whitelist.get("directories_keep_in_main", []))
    move_dirs = set(whitelist.get("directories_move_to_devlog", []))
    
    files_to_remove = []
    
    # Find all markdown files
    for root, dirs, files in os.walk(repo_root):
        if '.git' in root:
            continue
        
        rel_root = Path(root).relative_to(repo_root)
        
        for file in files:
            if not file.endswith('.md'):
                continue
            
            file_path = Path(root) / file
            rel_path = file_path.relative_to(repo_root)
            
            # Skip if essential
            if str(rel_path) in essential_files:
                continue
            
            # Skip if in keep directory
            in_keep_dir = any(str(rel_path).startswith(keep_dir.rstrip('/')) 
                            for keep_dir in keep_dirs)
            if in_keep_dir:
                continue
            
            # Remove if in move directory
            in_move_dir = any(str(rel_path).startswith(move_dir.rstrip('/')) 
                            for move_dir in move_dirs)
            if in_move_dir:
                files_to_remove.append(rel_path)
                continue
            
            # Remove if it's a docs file not in essential list
            if 'docs' in str(rel_path) and 'GUIDE' not in str(rel_path):
                files_to_remove.append(rel_path)
                continue
            
            # Remove REPORTS files
            if 'REPORTS' in str(rel_path):
                files_to_remove.append(rel_path)
                continue
    
    if files_to_remove:
        print(f"[REMOVE] Removing {len(files_to_remove)} doc files from main...")
        for file_path in files_to_remove[:10]:
            print(f"  - {file_path}")
        if len(files_to_remove) > 10:
            print(f"  ... and {len(files_to_remove) - 10} more")
        
        # Remove directories that should be empty
        dirs_to_remove = set()
        for file_path in files_to_remove:
            dirs_to_remove.add(file_path.parent)
        
        # Use git rm
        for file_path in files_to_remove:
            try:
                subprocess.run(['git', 'rm', '--cached', str(file_path)], 
                             cwd=repo_root, check=False, capture_output=True)
            except:
                pass
        
        return True
    
    return False


def main():
    """Main restructuring function."""
    import os
    import argparse
    
    parser = argparse.ArgumentParser(description='Restructure branches for devlog strategy')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    parser.add_argument('--devlog-only', action='store_true', help='Only clean devlog branch')
    parser.add_argument('--main-only', action='store_true', help='Only clean main branch')
    
    args = parser.parse_args()
    
    repo_root = Path.cwd()
    current_branch = subprocess.run(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
        cwd=repo_root,
        capture_output=True,
        text=True
    ).stdout.strip()
    
    whitelist = load_whitelist()
    
    print("[RESTRUCTURE] Branch restructuring for devlog strategy")
    print(f"[INFO] Current branch: {current_branch}")
    print(f"[INFO] Repository root: {repo_root}")
    
    if args.dry_run:
        print("[DRY RUN] Showing what would be done...")
    
    # Process devlog branch
    if not args.main_only:
        print("\n[DEVLOG] Processing devlog branch...")
        if current_branch != 'devlog':
            print("[WARNING] Not on devlog branch. Switching...")
            if not args.dry_run:
                subprocess.run(['git', 'checkout', 'devlog'], cwd=repo_root, check=True)
        
        if args.dry_run:
            print("[DRY RUN] Would remove code files from devlog")
        else:
            remove_code_from_devlog(repo_root)
    
    # Process main branch
    if not args.devlog_only:
        print("\n[MAIN] Processing main branch...")
        if current_branch != 'main':
            print("[WARNING] Not on main branch. Switching...")
            if not args.dry_run:
                subprocess.run(['git', 'checkout', 'main'], cwd=repo_root, check=True)
        
        if args.dry_run:
            print("[DRY RUN] Would remove non-essential docs from main")
        else:
            remove_docs_from_main(repo_root, whitelist)
    
    print("\n[OK] Restructuring complete!")
    print("[NOTE] Review changes and commit when ready")


if __name__ == "__main__":
    main()

