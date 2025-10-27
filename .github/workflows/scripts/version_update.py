#!/usr/bin/env python3
"""
HyperKit AI Agent - Version Update Automation Script
Integrates with Changesets, GitHub workflows, and versioned source files.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
import json
from datetime import datetime
from typing import List, Tuple, Optional

# Key patterns for different version formats
PATTERNS = {
    "json": r'("version"\s*:\s*")(\d+\.\d+\.\d+)(")',
    "python": r'(version\s*=\s*["\'])(\d+\.\d+\.\d+)(["\'])',
    "yaml": r'(version:\s*)(\d+\.\d+\.\d+)',
    "py_string": r'("version":\s*")(\d+\.\d+\.\d+)(")',
}

# Get repository root (3 levels up from this script)
ROOT = Path(__file__).resolve().parents[3]
CHANGESET_DIR = ROOT / ".changeset"
CHANGESET_PENDING_DIR = CHANGESET_DIR / "pending"

# Files to update with version numbers
VERSION_FILES = [
    "package.json",
    "hyperkit-agent/package.json", 
    "hyperkit-agent/setup.py",
    "hyperkit-agent/services/defi/primitives_generator.py"
]

CHANGELOG_FILES = [
    "CHANGELOG.md",
    "hyperkit-agent/CHANGELOG.md"
]

def get_current_version() -> str:
    """Extract the current version from tracked files."""
    print("🔍 Detecting current version...")
    
    for vf in VERSION_FILES:
        f = ROOT / vf
        if f.exists():
            content = f.read_text()
            # Try different patterns
            for pattern_name, pattern in PATTERNS.items():
                match = re.search(pattern, content)
                if match:
                    version = match.group(2)
                    print(f"  ✅ Found version {version} in {vf}")
                    return version
    
    raise RuntimeError("❌ No version found in tracked files")

def bump_version(version: str, bump_type: str = "patch") -> str:
    """Increment semantic version based on bump type."""
    print(f"📈 Bumping version: {version} ({bump_type})")
    
    try:
        major, minor, patch = map(int, version.split("."))
    except ValueError:
        raise ValueError(f"Invalid version format: {version}")
    
    if bump_type == "patch":
        patch += 1
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "major":
        major += 1
        minor = patch = 0
    else:
        raise ValueError(f"Invalid bump type: {bump_type}. Use 'patch', 'minor', or 'major'")
    
    new_version = f"{major}.{minor}.{patch}"
    print(f"  ✅ New version: {new_version}")
    return new_version

def update_version_in_file(file_path: Path, old_version: str, new_version: str) -> bool:
    """Replace version string in file based on file type."""
    if not file_path.exists():
        return False
        
    # Read file with proper encoding handling
    try:
        content = file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        try:
            content = file_path.read_text(encoding='latin-1')
        except UnicodeDecodeError:
            content = file_path.read_text(encoding='cp1252')
    
    ext = file_path.suffix.lower()
    updated = False
    
    # JSON files
    if ext == ".json":
        pattern = PATTERNS["json"]
        if re.search(pattern, content):
            updated = re.sub(pattern, lambda m: f'{m.group(1)}{new_version}{m.group(3)}', content)
    
    # Python files
    elif ext == ".py":
        # Try both patterns for Python files
        for pattern_name in ["python", "py_string"]:
            pattern = PATTERNS[pattern_name]
            if re.search(pattern, content):
                updated = re.sub(pattern, lambda m: f'{m.group(1)}{new_version}{m.group(3)}', content)
                break
    
    # YAML files
    elif ext in [".yml", ".yaml"]:
        pattern = PATTERNS["yaml"]
        if re.search(pattern, content):
            updated = re.sub(pattern, lambda m: f'{m.group(1)}{new_version}', content)
    
    if updated and updated != content:
        # Write file with proper encoding
        try:
            file_path.write_text(updated, encoding='utf-8')
        except UnicodeEncodeError:
            file_path.write_text(updated, encoding='latin-1')
        print(f"  ✅ Updated {file_path.relative_to(ROOT)} to version {new_version}")
        return True
    else:
        print(f"  ⚠️  No version pattern found in {file_path.relative_to(ROOT)}")
        return False

def create_changeset_entry(new_version: str, bump_type: str) -> Path:
    """Create a new changeset entry for the version bump."""
    print("📝 Creating changeset entry...")
    
    # Ensure changeset pending directory exists
    CHANGESET_PENDING_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create timestamp-based filename
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    file_path = CHANGESET_PENDING_DIR / f"version-{new_version}-{ts}.md"
    
    # Determine changeset type based on bump type
    changeset_type = bump_type if bump_type in ["major", "minor", "patch"] else "patch"
    
    content = f"""---
"hyperkit": {changeset_type}
---

## Version {new_version} - Automated Release

### 🚀 Automated Version Update
- **Version**: {new_version}
- **Bump Type**: {bump_type}
- **Date**: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
- **Triggered by**: Python version automation script

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: {len(VERSION_FILES)} version files
- **Changelog Updated**: {len(CHANGELOG_FILES)} changelog files
- **Git Tag**: v{new_version}
"""
    
    try:
        file_path.write_text(content, encoding='utf-8')
    except UnicodeEncodeError:
        file_path.write_text(content, encoding='latin-1')
    print(f"  ✅ Created changeset: {file_path.relative_to(ROOT)}")
    return file_path

def update_changelog(new_version: str) -> None:
    """Update changelog files with new version entry."""
    print("📋 Updating changelog files...")
    
    date = datetime.utcnow().strftime("%Y-%m-%d")
    entry = f"""
## [{new_version}] - {date}

### 🚀 Automated Release
- **Version**: {new_version}
- **Date**: {date}
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: {len(VERSION_FILES)} version files
- **Changelog Updated**: {len(CHANGELOG_FILES)} changelog files
- **Git Tag**: v{new_version}

---
"""
    
    for changelog_file in CHANGELOG_FILES:
        file_path = ROOT / changelog_file
        if file_path.exists():
            # Read existing content with proper encoding
            try:
                content = file_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    content = file_path.read_text(encoding='latin-1')
                except UnicodeDecodeError:
                    content = file_path.read_text(encoding='cp1252')
            
            # Find the first ## heading and insert before it
            lines = content.split('\n')
            insert_index = 0
            
            for i, line in enumerate(lines):
                if line.startswith('## '):
                    insert_index = i
                    break
            
            # Insert new entry
            lines.insert(insert_index, entry.strip())
            try:
                file_path.write_text('\n'.join(lines), encoding='utf-8')
            except UnicodeEncodeError:
                file_path.write_text('\n'.join(lines), encoding='latin-1')
            print(f"  ✅ Updated {file_path.relative_to(ROOT)}")
        else:
            # Create new changelog
            content = f"# Changelog\n{entry.strip()}"
            file_path.write_text(content)
            print(f"  ✅ Created {file_path.relative_to(ROOT)}")

def git_commit_and_tag(new_version: str) -> None:
    """Stage, commit, and tag the version update."""
    print("🏷️  Creating git commit and tag...")
    
    try:
        # Stage all changes
        subprocess.run(["git", "add", "-A"], check=True, cwd=ROOT)
        print("  ✅ Staged all changes")
        
        # Create commit
        commit_msg = f"chore(release): bump version to {new_version}\n\n- Updated version numbers across all tracked files\n- Generated changeset entry\n- Updated changelog files\n- Automated via Python version script"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, cwd=ROOT)
        print(f"  ✅ Created commit: {commit_msg.split(chr(10))[0]}")
        
        # Create tag (check if it exists first)
        tag_name = f"v{new_version}"
        result = subprocess.run(["git", "tag", "-l", tag_name], capture_output=True, text=True, cwd=ROOT)
        
        if result.stdout.strip():
            print(f"  ⚠️  Tag {tag_name} already exists, skipping tag creation")
        else:
            subprocess.run(["git", "tag", tag_name], check=True, cwd=ROOT)
            print(f"  ✅ Created tag: {tag_name}")
        
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Git operation failed: {e}")
        raise

def validate_environment() -> bool:
    """Validate that we're in a git repository and have required tools."""
    print("🔍 Validating environment...")
    
    # Check if we're in a git repository
    try:
        subprocess.run(["git", "status"], check=True, capture_output=True, cwd=ROOT)
        print("  ✅ Git repository detected")
    except subprocess.CalledProcessError:
        print("  ❌ Not in a git repository")
        return False
    
    # Check if changeset directory exists
    if not CHANGESET_DIR.exists():
        print("  ❌ Changeset directory not found")
        return False
    print("  ✅ Changeset directory found")
    
    return True

def main():
    """Main version update function."""
    print("🚀 HyperKit AI Agent - Version Update Automation")
    print("=" * 60)
    
    # Validate environment
    if not validate_environment():
        print("❌ Environment validation failed")
        sys.exit(1)
    
    # Get bump type from environment or default to patch
    bump_type = os.environ.get("BUMP_TYPE", "patch").lower().strip()
    if bump_type not in ["patch", "minor", "major"]:
        print(f"❌ Invalid bump type: '{bump_type}'. Use 'patch', 'minor', or 'major'")
        print(f"   Environment variable BUMP_TYPE: '{os.environ.get('BUMP_TYPE', 'not set')}'")
        sys.exit(1)
    
    try:
        # Get current version
        old_version = get_current_version()
        print(f"📊 Current version: {old_version}")
        
        # Calculate new version
        new_version = bump_version(old_version, bump_type)
        print(f"📊 New version: {new_version}")
        
        # Update version in all tracked files
        print("\n📝 Updating version files...")
        updated_files = []
        for vf in VERSION_FILES:
            file_path = ROOT / vf
            if update_version_in_file(file_path, old_version, new_version):
                updated_files.append(vf)
        
        if not updated_files:
            print("❌ No files were updated")
            sys.exit(1)
        
        print(f"  ✅ Updated {len(updated_files)} files")
        
        # Create changeset entry
        changeset_file = create_changeset_entry(new_version, bump_type)
        
        # Update changelog
        update_changelog(new_version)
        
        # Git commit and tag
        git_commit_and_tag(new_version)
        
        # Success message
        print("\n" + "=" * 60)
        print("🎉 VERSION UPDATE SUCCESSFUL!")
        print("=" * 60)
        print(f"📊 Version: {old_version} → {new_version}")
        print(f"🔧 Bump Type: {bump_type}")
        print(f"📁 Files Updated: {len(updated_files)}")
        print(f"📝 Changeset: {changeset_file.name}")
        print(f"🏷️  Git Tag: v{new_version}")
        print("\n📋 Next Steps:")
        print("  1. Review the changes: git show HEAD")
        print("  2. Push to remote: git push origin main --tags")
        print("  3. Create release: npx changeset publish")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Version update failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
