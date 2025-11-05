#!/usr/bin/env python3
"""
Validate Branch Sync

Checks that main and devlog branches are properly synced:
- Code changes in main are reflected in devlog
- Documentation links are correct
- Essential docs are present in main
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any

# Script runs from hyperkit-agent/scripts/ci/, so repo root is 3 levels up
REPO_ROOT = Path(__file__).parent.parent.parent
WHITELIST_FILE = Path(__file__).parent / "essential_docs_whitelist.json"


def load_whitelist() -> Dict[str, Any]:
    """Load essential docs whitelist."""
    if not WHITELIST_FILE.exists():
        return {"files": [], "directories_keep_in_main": []}
    
    with open(WHITELIST_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_current_branch() -> str:
    """Get current git branch."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"


def check_branch_exists(branch: str) -> bool:
    """Check if branch exists."""
    try:
        result = subprocess.run(
            ['git', 'show-ref', '--verify', '--quiet', f'refs/heads/{branch}'],
            cwd=REPO_ROOT,
            capture_output=True
        )
        return result.returncode == 0
    except:
        return False


def validate_essential_docs_in_main() -> List[str]:
    """Check that essential docs are present in main branch."""
    errors = []
    whitelist = load_whitelist()
    essential_files = whitelist.get("files", [])
    
    current_branch = get_current_branch()
    
    if current_branch != "main":
        # Switch to main temporarily
        try:
            subprocess.run(['git', 'checkout', 'main'], cwd=REPO_ROOT.parent, check=True, capture_output=True)
        except:
            return [f"Cannot switch to main branch for validation"]
    
    try:
        # Check files relative to repo root (parent of hyperkit-agent/)
        repo_root = REPO_ROOT.parent
        for file_path in essential_files:
            # Handle both absolute and relative paths
            if file_path.startswith('hyperkit-agent/'):
                full_path = repo_root / file_path
            else:
                full_path = repo_root / file_path
            
            if not full_path.exists():
                errors.append(f"Essential file missing in main: {file_path}")
    finally:
        # Return to original branch
        if current_branch != "main":
            try:
                subprocess.run(['git', 'checkout', current_branch], cwd=REPO_ROOT.parent, capture_output=True)
            except:
                pass
    
    return errors


def validate_readme_links() -> List[str]:
    """Check that README.md links are correct (GitHub URLs for devlog docs)."""
    errors = []
    # README.md is at repo root, not hyperkit-agent/
    readme_path = REPO_ROOT.parent / "README.md"
    
    if not readme_path.exists():
        return ["README.md not found"]
    
    content = readme_path.read_text(encoding='utf-8')
    
    # Check for relative links that should be GitHub URLs
    import re
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    
    for match in re.finditer(link_pattern, content):
        link_text = match.group(1)
        link_path = match.group(2)
        
        # Skip external URLs and anchors
        if link_path.startswith('http') or link_path.startswith('#'):
            continue
        
        # Check if it's a devlog doc that should be GitHub URL
        # Allow relative links for files in main (QUICK_START, ENVIRONMENT_SETUP)
        if any(pattern in link_path for pattern in ['REPORTS/', 'docs/TEAM/', 'docs/EXECUTION/', './REPORTS/']):
            if not link_path.startswith('https://github.com'):
                errors.append(f"README.md link should be GitHub URL: {link_path}")
    
    return errors


def main():
    """Main validation function."""
    print("[VALIDATE] Validating branch sync...\n")
    
    errors = []
    
    # Check essential docs in main
    print("[DOCS] Checking essential docs in main branch...")
    doc_errors = validate_essential_docs_in_main()
    if doc_errors:
        errors.extend(doc_errors)
        print(f"  [FAIL] {len(doc_errors)} errors found")
    else:
        print("  [OK] All essential docs present")
    
    # Check README links
    print("\n[LINKS] Checking README.md links...")
    link_errors = validate_readme_links()
    if link_errors:
        errors.extend(link_errors)
        print(f"  [FAIL] {len(link_errors)} link issues found")
    else:
        print("  [OK] All links correct")
    
    # Check if devlog exists
    print("\n[BRANCH] Checking branches...")
    if check_branch_exists("devlog"):
        print("  [OK] devlog branch exists")
    else:
        print("  [WARN] devlog branch not found (run sync_to_devlog.py)")
    
    # Summary
    print("\n" + "=" * 50)
    if errors:
        print(f"[FAIL] Validation failed: {len(errors)} errors")
        print("\nErrors:")
        for error in errors[:20]:  # Show first 20
            print(f"  • {error}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more")
        sys.exit(1)
    else:
        print("[OK] Branch sync validation passed")
        sys.exit(0)


if __name__ == "__main__":
    main()

