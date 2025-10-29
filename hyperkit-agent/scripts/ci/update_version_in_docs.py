#!/usr/bin/env python3
"""
Automated Version Injection Script
Syncs version numbers across all docs, reports, and markdown files
"""

import os
import re
import glob
from pathlib import Path
from datetime import datetime

def get_version():
    """Get version from VERSION file"""
    # Try current directory first, then parent
    version_paths = [Path("VERSION"), Path("../VERSION"), Path("../../VERSION")]
    
    for version_path in version_paths:
        if version_path.exists():
            try:
                with open(version_path, "r") as f:
                    return f.read().strip()
            except Exception as e:
                print(f"ERROR reading VERSION file: {e}")
                return None
    
    print("ERROR: VERSION file not found")
    return None

def get_git_info():
    """Get git commit hash and date"""
    try:
        import subprocess
        # Get current directory - script may run from hyperkit-agent/ or repo root
        script_dir = Path(__file__).parent.parent.parent
        original_dir = os.getcwd()
        try:
            os.chdir(script_dir)  # Change to repo root for git commands
            
            commit_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], 
                                                text=True, stderr=subprocess.DEVNULL).strip()
            commit_date = subprocess.check_output(["git", "log", "-1", "--format=%Y-%m-%d"], 
                                                 text=True, stderr=subprocess.DEVNULL).strip()
            
            # Fallback if date parsing fails or is invalid
            if not commit_date or len(commit_date) == 0 or not commit_date[0].isdigit():
                commit_date = datetime.now().strftime("%Y-%m-%d")
            
            return commit_hash, commit_date
        finally:
            os.chdir(original_dir)  # Restore original directory
    except Exception as e:
        print(f"Warning: Could not get git info: {e}")
        return "unknown", datetime.now().strftime("%Y-%m-%d")

def update_version_in_file(file_path, version, commit_hash, commit_date):
    """Update version markers in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Update VERSION_PLACEHOLDER blocks
        version_pattern = r'<!-- VERSION_PLACEHOLDER -->.*?<!-- /VERSION_PLACEHOLDER -->'
        version_replacement = f'''<!-- VERSION_PLACEHOLDER -->
**Version**: {version}
**Last Updated**: {commit_date}
**Commit**: {commit_hash}
<!-- /VERSION_PLACEHOLDER -->'''
        
        content = re.sub(version_pattern, version_replacement, content, flags=re.DOTALL)
        
        # Update SCRIPT_MARKER blocks
        script_pattern = r'<!-- SCRIPT_MARKER name=([^ ]+) version=([^ ]+) hash=([^ ]+) -->'
        def update_script_marker(match):
            script_name = match.group(1)
            return f'<!-- SCRIPT_MARKER name={script_name} version={version} hash={commit_hash} -->'
        
        content = re.sub(script_pattern, update_script_marker, content)
        
        # Update standalone version references
        content = re.sub(r'\*\*Version\*\*:\s*\d+\.\d+\.\d+', f'**Version**: {version}', content)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated: {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def main():
    """Main function to update all markdown files"""
    version = get_version()
    if not version:
        return 1
    
    commit_hash, commit_date = get_git_info()
    
    print(f"Updating version to {version} (commit: {commit_hash}, date: {commit_date})")
    
    # Find all markdown files
    # Script runs from hyperkit-agent/, so we need to check parent directories too
    markdown_files = []
    
    # Patterns relative to current directory (hyperkit-agent/)
    patterns = [
        "**/*.md",                    # Current directory and subdirectories
        "docs/**/*.md",               # Local docs
        "REPORTS/**/*.md",            # Local reports
    ]
    
    # Patterns for parent directory (repo root)
    parent_patterns = [
        "../README.md",               # Root README
        "../CHANGELOG.md",            # Root CHANGELOG
        "../docs/**/*.md",            # Root docs if exists
    ]
    
    # Collect files from current directory
    for pattern in patterns:
        markdown_files.extend(glob.glob(pattern, recursive=True))
    
    # Collect files from parent directory
    for pattern in parent_patterns:
        found = glob.glob(pattern, recursive=True)
        markdown_files.extend(found)
    
    # Remove duplicates and sort
    markdown_files = sorted(set(markdown_files))
    
    updated_count = 0
    for file_path in markdown_files:
        if update_version_in_file(file_path, version, commit_hash, commit_date):
            updated_count += 1
    
    print(f"Updated {updated_count} files")
    return 0

if __name__ == "__main__":
    exit(main())
