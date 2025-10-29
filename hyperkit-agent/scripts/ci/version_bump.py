#!/usr/bin/env python3
"""
Version Bump Script for HyperKit Agent

Simple script to bump version numbers in the VERSION file and sync across documentation.
"""

import sys
import re
from pathlib import Path
from datetime import datetime

def get_current_version():
    """Get current version from VERSION file."""
    # Try multiple locations: current dir, parent dir, repo root
    version_paths = [
        Path("VERSION"),  # Current directory
        Path("../VERSION"),  # Parent directory (repo root)
        Path("../../VERSION"),  # Two levels up
    ]
    
    version_file = None
    for vpath in version_paths:
        if vpath.exists():
            version_file = vpath
            break
    
    if not version_file:
        print("❌ VERSION file not found")
        print("   Searched in: current directory, ../, ../../")
        sys.exit(1)
    
    version = version_file.read_text().strip()
    print(f"📊 Current version: {version}")
    print(f"📁 Found VERSION file: {version_file.resolve()}")
    return version

def bump_version(version, bump_type):
    """Bump version based on type."""
    try:
        major, minor, patch = map(int, version.split("."))
    except ValueError:
        print(f"❌ Invalid version format: {version}")
        sys.exit(1)
    
    if bump_type == "patch":
        patch += 1
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "major":
        major += 1
        minor = patch = 0
    else:
        print(f"❌ Invalid bump type: {bump_type}")
        sys.exit(1)
    
    new_version = f"{major}.{minor}.{patch}"
    print(f"📈 New version: {new_version}")
    return new_version

def update_version_file(new_version):
    """Update VERSION file."""
    # Try multiple locations: current dir, parent dir, repo root
    version_paths = [
        Path("VERSION"),  # Current directory
        Path("../VERSION"),  # Parent directory (repo root)
        Path("../../VERSION"),  # Two levels up
    ]
    
    version_file = None
    for vpath in version_paths:
        if vpath.exists():
            version_file = vpath
            break
    
    if not version_file:
        # If not found, use repo root (parent directory)
        version_file = Path("../VERSION")
    
    version_file.write_text(f"{new_version}\n")
    print(f"✅ Updated VERSION file: {version_file.resolve()} → {new_version}")

def update_package_json(new_version):
    """Update package.json version."""
    # Check both current dir and parent (repo root)
    package_json_paths = [
        Path("../package.json"),  # Repo root (most likely)
        Path("package.json"),  # Current directory
    ]
    
    package_json = None
    for pkg_path in package_json_paths:
        if pkg_path.exists():
            package_json = pkg_path
            break
    
    if package_json and package_json.exists():
        content = package_json.read_text()
        # Update version in package.json
        pattern = r'("version"\s*:\s*")([^"]+)(")'
        updated = re.sub(pattern, f'\\g<1>{new_version}\\g<3>', content)
        package_json.write_text(updated)
        print(f"✅ Updated package.json ({package_json.resolve()}): {new_version}")
    else:
        print(f"⚠️  package.json not found, skipping")

def update_pyproject_toml(new_version):
    """Update pyproject.toml version."""
    pyproject_toml = Path("hyperkit-agent/pyproject.toml")
    if pyproject_toml.exists():
        content = pyproject_toml.read_text()
        # Update version in pyproject.toml
        pattern = r'(version\s*=\s*")([^"]+)(")'
        updated = re.sub(pattern, f'\\g<1>{new_version}\\g<3>', content)
        pyproject_toml.write_text(updated)
        print(f"✅ Updated pyproject.toml: {new_version}")

def create_git_commit(new_version, bump_type):
    """Create git commit for version bump."""
    import subprocess
    
    try:
        # Find VERSION file location
        version_paths = ["VERSION", "../VERSION", "../../VERSION"]
        version_file = None
        for vpath in version_paths:
            if Path(vpath).exists():
                version_file = vpath
                break
        
        if not version_file:
            version_file = "../VERSION"  # Default to repo root
        
        # Stage changes
        files_to_add = [version_file, "../package.json", "pyproject.toml"]
        # Filter out non-existent files
        files_to_add = [f for f in files_to_add if Path(f).exists()]
        subprocess.run(["git", "add"] + files_to_add, check=True)
        
        # Create commit
        commit_msg = f"chore: bump version to {new_version} ({bump_type})"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        print(f"✅ Created git commit: {commit_msg}")
        
        # Create tag
        tag_name = f"v{new_version}"
        subprocess.run(["git", "tag", tag_name], check=True)
        print(f"✅ Created git tag: {tag_name}")
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Git operations failed: {e}")
        print("   You may need to commit manually")

def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python version_bump.py <patch|minor|major>")
        sys.exit(1)
    
    bump_type = sys.argv[1].lower()
    if bump_type not in ["patch", "minor", "major"]:
        print("❌ Invalid bump type. Use: patch, minor, or major")
        sys.exit(1)
    
    print(f"🚀 HyperKit Agent - Version Bump ({bump_type})")
    print("=" * 50)
    
    # Get current version
    current_version = get_current_version()
    
    # Calculate new version
    new_version = bump_version(current_version, bump_type)
    
    # Update files
    print("\n📝 Updating version files...")
    update_version_file(new_version)
    update_package_json(new_version)
    update_pyproject_toml(new_version)
    
    # Create git commit
    print("\n🏷️  Creating git commit and tag...")
    create_git_commit(new_version, bump_type)
    
    # Success message
    print("\n" + "=" * 50)
    print("🎉 VERSION BUMP SUCCESSFUL!")
    print("=" * 50)
    print(f"📊 Version: {current_version} → {new_version}")
    print(f"🔧 Bump Type: {bump_type}")
    print(f"🏷️  Git Tag: v{new_version}")
    print("\n📋 Next Steps:")
    print("  1. Review changes: git show HEAD")
    print("  2. Push to remote: git push origin main --tags")
    print("  3. Sync docs: npm run version:sync")
    print("=" * 50)

if __name__ == "__main__":
    main()
