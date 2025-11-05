#!/usr/bin/env python3
"""
Update README.md Links for Devlog Branch Strategy

Converts relative links pointing to documentation in devlog branch
to GitHub URLs, ensuring links work from main branch (code-only).

This script is automatically run during version bumps to maintain
link integrity across branches.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# Repository configuration
REPO_URL = "https://github.com/JustineDevs/Hyperkit-Agent"
REPO_OWNER = "JustineDevs"
REPO_NAME = "Hyperkit-Agent"

# Links that should point to devlog branch (convert to GitHub URLs)
DEVLOG_LINK_PATTERNS = [
    r'hyperkit-agent/REPORTS/',
    r'hyperkit-agent/docs/TEAM/',
    r'hyperkit-agent/docs/EXECUTION/',
    r'hyperkit-agent/docs/INTEGRATION/',
    r'hyperkit-agent/docs/ROADMAP\.md',
    r'hyperkit-agent/docs/API_REFERENCE\.md',
    r'hyperkit-agent/docs/SECURITY_SETUP\.md',
    r'^docs/',
    r'^REPORTS/',
]

# Links to keep relative (these files exist in main branch)
KEEP_RELATIVE_PATTERNS = [
    r'README\.md',
    r'CHANGELOG\.md',
    r'LICENSE\.md',
    r'SECURITY\.md',
    r'CONTRIBUTING\.md',
    r'CODE_OF_CONDUCT\.md',
    r'hyperkit-agent/docs/GUIDE/QUICK_START\.md',
    r'hyperkit-agent/docs/GUIDE/ENVIRONMENT_SETUP\.md',
    r'hyperkit-agent/config\.yaml',
    r'hyperkit-agent/pyproject\.toml',
    r'package\.json',
    r'VERSION',
]

# External URLs, anchors, and special patterns to skip
SKIP_PATTERNS = [
    r'^https?://',  # Already external URLs
    r'^#',          # Anchor links
    r'^mailto:',    # Email links
    r'^ftp://',     # FTP links
]


def should_convert_to_github_url(link_path: str) -> bool:
    """
    Determine if a link should be converted to GitHub URL pointing to devlog.
    
    Args:
        link_path: Relative path from the link
        
    Returns:
        True if link should be converted to GitHub URL
    """
    # Skip if already external URL or anchor
    for pattern in SKIP_PATTERNS:
        if re.match(pattern, link_path):
            return False
    
    # Check if it's in KEEP_RELATIVE list (exists in main)
    for pattern in KEEP_RELATIVE_PATTERNS:
        if re.search(pattern, link_path):
            return False
    
    # Check if it matches DEVLOG_LINKS patterns (should be in devlog)
    for pattern in DEVLOG_LINK_PATTERNS:
        if re.search(pattern, link_path):
            return True
    
    # Default: keep relative (might be code files or other assets)
    return False


def convert_to_github_url(link_path: str) -> str:
    """
    Convert relative link to GitHub blob URL pointing to devlog branch.
    
    Args:
        link_path: Relative path from the link
        
    Returns:
        GitHub blob URL pointing to devlog branch
    """
    # Remove leading ./ if present
    link_path = link_path.lstrip('./')
    
    # Remove leading / if present
    link_path = link_path.lstrip('/')
    
    # Convert to GitHub blob URL
    github_url = f"{REPO_URL}/blob/devlog/{link_path}"
    return github_url


def update_readme_links(readme_path: Path, dry_run: bool = False) -> Tuple[str, List[Tuple[str, str]]]:
    """
    Update links in README.md and return updated content and list of changes.
    
    Args:
        readme_path: Path to README.md file
        dry_run: If True, don't write changes, just return them
        
    Returns:
        Tuple of (updated_content, list_of_changes)
    """
    if not readme_path.exists():
        print(f"❌ README.md not found: {readme_path}")
        sys.exit(1)
    
    content = readme_path.read_text(encoding='utf-8')
    changes = []
    
    # Pattern to match markdown links: [text](path) or [text](path "title")
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    
    def replace_link(match):
        link_text = match.group(1)
        link_path = match.group(2)
        
        # Remove title if present (e.g., "title" in [text](path "title"))
        if ' "' in link_path:
            link_path = link_path.split(' "')[0]
        
        # Skip if already a GitHub URL or external URL
        if link_path.startswith('http'):
            return match.group(0)
        
        # Skip if it's an anchor link
        if link_path.startswith('#'):
            return match.group(0)
        
        # Check if should convert
        if should_convert_to_github_url(link_path):
            new_url = convert_to_github_url(link_path)
            changes.append((link_path, new_url))
            return f'[{link_text}]({new_url})'
        
        return match.group(0)
    
    updated_content = re.sub(link_pattern, replace_link, content)
    
    return updated_content, changes


def main():
    """Main function to update README.md links."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Update README.md links for devlog branch strategy'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    parser.add_argument(
        '--file',
        type=str,
        default='README.md',
        help='Path to README.md file (default: README.md)'
    )
    
    args = parser.parse_args()
    
    readme_path = Path(args.file)
    
    if not readme_path.exists():
        print(f"❌ README.md not found: {readme_path}")
        sys.exit(1)
    
    updated_content, changes = update_readme_links(readme_path, dry_run=args.dry_run)
    
    if changes:
        if args.dry_run:
            print(f"[DRY RUN] Would update {len(changes)} links in {readme_path}")
            print("\nChanges that would be made:")
            for old, new in changes[:20]:  # Show first 20
                print(f"  {old}")
                print(f"    -> {new}")
            if len(changes) > 20:
                print(f"\n  ... and {len(changes) - 20} more changes")
            print(f"\n[INFO] Run without --dry-run to apply changes")
        else:
            readme_path.write_text(updated_content, encoding='utf-8')
            print(f"[OK] Updated {len(changes)} links in {readme_path}")
            print("\nSample changes:")
            for old, new in changes[:5]:  # Show first 5
                print(f"  {old} -> {new}")
            if len(changes) > 5:
                print(f"  ... and {len(changes) - 5} more")
    else:
        print(f"[INFO] No links needed updating in {readme_path}")


if __name__ == "__main__":
    main()

