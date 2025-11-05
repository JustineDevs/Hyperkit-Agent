#!/usr/bin/env python3
"""
Sync Documentation to Devlog Branch

Moves all documentation files (.md, .json in docs/REPORTS) to devlog branch
while keeping only code and essential docs in main branch.

This script is called automatically during version bumps to maintain
branch separation.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Set, Dict, Any
from datetime import datetime

# Load essential docs whitelist
WHITELIST_FILE = Path(__file__).parent / "essential_docs_whitelist.json"


def load_whitelist() -> Dict[str, Any]:
    """Load essential docs whitelist configuration."""
    if not WHITELIST_FILE.exists():
        print(f"[WARNING] Whitelist file not found: {WHITELIST_FILE}")
        return {
            "files": [],
            "directories_keep_in_main": [],
            "directories_move_to_devlog": []
        }
    
    with open(WHITELIST_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_current_branch() -> str:
    """Get current git branch name."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error getting current branch: {e}")
        sys.exit(1)


def ensure_clean_working_tree() -> bool:
    """Check if working tree is clean (no uncommitted changes)."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--quiet', 'HEAD'],
            capture_output=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False


def get_doc_files_to_sync(repo_root: Path, whitelist: Dict[str, Any]) -> List[Path]:
    """
    Get all documentation files that should be moved to devlog.
    
    Args:
        repo_root: Root directory of repository
        whitelist: Whitelist configuration
        
    Returns:
        List of file paths to sync to devlog
    """
    doc_extensions = ['.md', '.json']
    doc_files = []
    
    # Directories that should be moved to devlog
    devlog_dirs = whitelist.get("directories_move_to_devlog", [])
    
    # Essential files that stay in main
    essential_files = set(whitelist.get("files", []))
    
    for root, dirs, filenames in os.walk(repo_root):
        # Skip git and ignored dirs
        if '.git' in root or any(skip in root for skip in 
            ['node_modules', '__pycache__', '.pytest_cache', '.venv', 'venv']):
            continue
        
        # Check if this directory should be moved to devlog
        rel_root = Path(root).relative_to(repo_root)
        should_move_dir = any(
            str(rel_root).startswith(d) or str(rel_root) == d
            for d in devlog_dirs
        )
        
        for filename in filenames:
            file_path = Path(root) / filename
            rel_path = file_path.relative_to(repo_root)
            
            # Skip if in essential files whitelist
            if str(rel_path) in essential_files:
                continue
            
            # If file is in a devlog directory, include it
            if should_move_dir:
                if file_path.suffix in doc_extensions:
                    doc_files.append(rel_path)
                continue
            
            # For other locations, check if it's a doc file
            if file_path.suffix in doc_extensions:
                # Check if it's in a directory that should be moved
                if any(str(rel_path).startswith(d) for d in devlog_dirs):
                    doc_files.append(rel_path)
    
    return doc_files


def sync_to_devlog(dry_run: bool = False) -> bool:
    """
    Sync documentation files to devlog branch.
    
    Args:
        dry_run: If True, show what would be done without making changes
        
    Returns:
        True if successful, False otherwise
    """
    
    repo_root = Path.cwd()
    current_branch = get_current_branch()
    
    if current_branch != 'main':
        print(f"[WARNING] Not on main branch (current: {current_branch})")
        print("   This script should typically run from main branch")
        response = input("   Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return False
    
    # Check for uncommitted changes
    if not ensure_clean_working_tree() and not dry_run:
        print("[ERROR] Working tree has uncommitted changes")
        print("   Please commit or stash changes before syncing to devlog")
        return False
    
    # Load whitelist
    whitelist = load_whitelist()
    
    # Get files to sync
    doc_files = get_doc_files_to_sync(repo_root, whitelist)
    
    if not doc_files:
        print("[INFO] No documentation files found to sync")
        return True
    
    if dry_run:
        print(f"[DRY RUN] Would sync {len(doc_files)} files to devlog branch")
        print("\nFiles that would be synced:")
        for f in doc_files[:20]:
            print(f"  {f}")
        if len(doc_files) > 20:
            print(f"  ... and {len(doc_files) - 20} more")
        return True
    
    print(f"[SYNC] Syncing {len(doc_files)} documentation files to devlog branch...")
    
    try:
        # Stash any uncommitted changes (should be clean, but safety check)
        subprocess.run(['git', 'stash'], capture_output=True)
        
        # Check if devlog branch exists
        result = subprocess.run(
            ['git', 'show-ref', '--verify', '--quiet', 'refs/heads/devlog'],
            capture_output=True
        )
        
        if result.returncode != 0:
            # Create devlog branch from main
            print("[CREATE] Creating devlog branch...")
            subprocess.run(['git', 'checkout', '-b', 'devlog'], check=True)
            subprocess.run(['git', 'checkout', current_branch], check=True)
        else:
            # Checkout devlog
            print("[CHECKOUT] Checking out devlog branch...")
            subprocess.run(['git', 'checkout', 'devlog'], check=True)
            
            # Merge latest from main to get code updates
            print("[MERGE] Merging latest from main...")
            subprocess.run(
                ['git', 'merge', current_branch, '--no-edit', '--no-ff'],
                check=True
            )
        
        # Ensure all doc files are present in devlog
        print("[FILES] Ensuring documentation files are present...")
        for doc_file in doc_files:
            file_path = repo_root / doc_file
            if file_path.exists():
                # File exists, ensure it's tracked
                subprocess.run(['git', 'add', str(doc_file)], check=False)
            else:
                # File might have been deleted, check if it exists in main
                subprocess.run(['git', 'checkout', current_branch, '--', str(doc_file)], check=False)
                if (repo_root / doc_file).exists():
                    subprocess.run(['git', 'add', str(doc_file)], check=False)
        
        # Commit changes to devlog
        if subprocess.run(['git', 'diff', '--cached', '--quiet'], capture_output=True).returncode != 0:
            subprocess.run([
                'git', 'commit',
                '-m', f'chore(devlog): sync documentation from {current_branch}\n\n'
                      f'Synced {len(doc_files)} documentation files from main branch.\n'
                      f'Generated: {datetime.now().isoformat()}'
            ], check=True)
            print("[OK] Committed documentation changes to devlog")
        
        # Return to original branch
        subprocess.run(['git', 'checkout', current_branch], check=True)
        
        # Restore stash if there was one
        subprocess.run(['git', 'stash', 'pop'], capture_output=True)
        
        print(f"[OK] Successfully synced {len(doc_files)} files to devlog branch")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error during sync: {e}")
        # Try to return to original branch
        try:
            subprocess.run(['git', 'checkout', current_branch], check=False)
        except:
            pass
        return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Sync documentation files to devlog branch'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    args = parser.parse_args()
    
    success = sync_to_devlog(dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

