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
    """Get current version from VERSION file (root directory only - source of truth)."""
    # ROOT DIRECTORY ONLY - Single source of truth
    script_dir = Path(__file__).parent.parent.parent
    root_version = script_dir.parent / "VERSION"  # repo root VERSION
    
    if not root_version.exists():
        print("❌ VERSION file not found in repo root")
        print(f"   Expected: {root_version.resolve()}")
        sys.exit(1)
    
    version = root_version.read_text().strip()
    print(f"📊 Current version: {version}")
    print(f"📁 Using root VERSION file: {root_version.resolve()}")
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
    """Update VERSION file (root directory only - source of truth)."""
    # ROOT DIRECTORY ONLY - Single source of truth
    script_dir = Path(__file__).parent.parent.parent
    root_version = script_dir.parent / "VERSION"  # repo root VERSION
    
    root_version.write_text(f"{new_version}\n")
    print(f"✅ Updated root VERSION file: {root_version.resolve()} → {new_version}")

def update_package_json(new_version):
    """Update package.json version (root directory only - source of truth)."""
    # ROOT DIRECTORY ONLY - Single source of truth
    script_dir = Path(__file__).parent.parent.parent
    root_package_json = script_dir.parent / "package.json"  # repo root package.json
    
    if root_package_json.exists():
        content = root_package_json.read_text()
        # Update version in package.json
        pattern = r'("version"\s*:\s*")([^"]+)(")'
        updated = re.sub(pattern, f'\\g<1>{new_version}\\g<3>', content)
        root_package_json.write_text(updated)
        print(f"✅ Updated root package.json: {root_package_json.resolve()} → {new_version}")
    else:
        print(f"⚠️  Root package.json not found at {root_package_json.resolve()}, skipping")

def update_pyproject_toml(new_version):
    """Update pyproject.toml version (relative to repo root - single source of truth)."""
    script_dir = Path(__file__).parent.parent.parent
    repo_root = script_dir.parent
    pyproject_toml = repo_root / "hyperkit-agent" / "pyproject.toml"
    
    if pyproject_toml.exists():
        content = pyproject_toml.read_text()
        # Update version in pyproject.toml
        pattern = r'(version\s*=\s*")([^"]+)(")'
        updated = re.sub(pattern, f'\\g<1>{new_version}\\g<3>', content)
        pyproject_toml.write_text(updated)
        print(f"✅ Updated pyproject.toml: {pyproject_toml.relative_to(repo_root)} → {new_version}")
    else:
        print(f"⚠️  pyproject.toml not found at {pyproject_toml.resolve()}, skipping")

def get_commit_message_for_file(file_path, new_version, bump_type):
    """Generate professional commit message based on file path and context."""
    file_path_str = str(file_path)
    file_name = file_path.name.lower()
    
    # Version files - special handling
    if file_name == "version":
        return f"chore(release): bump version to {new_version} ({bump_type})"
    
    if "package.json" in file_name:
        return f"chore(release): update package.json version to {new_version}"
    
    if "pyproject.toml" in file_name:
        return f"chore(release): update pyproject.toml version to {new_version}"
    
    # Documentation files
    if file_path_str.endswith(".md"):
        if "readme" in file_name:
            return f"docs: update README version to {new_version}"
        elif "changelog" in file_name:
            return f"docs: update CHANGELOG for version {new_version}"
        elif "security" in file_name:
            return f"docs: update SECURITY version to {new_version}"
        elif "/docs/" in file_path_str.lower() or "\\docs\\" in file_path_str.lower():
            return f"docs: update documentation for version {new_version}"
        elif "/reports/" in file_path_str.lower() or "\\reports\\" in file_path_str.lower():
            return f"docs: update reports for version {new_version}"
        else:
            return f"docs: update {file_path.name} for version {new_version}"
    
    # Configuration files
    if file_name in ["config.yaml", "config.yml", ".env", ".env.example"]:
        return f"config: update {file_path.name} for version {new_version}"
    
    # Scripts
    if file_path_str.endswith((".py", ".js", ".sh", ".bash")):
        if "/scripts/" in file_path_str.lower() or "\\scripts\\" in file_path_str.lower():
            script_type = "ci" if "/ci/" in file_path_str.lower() or "\\ci\\" in file_path_str.lower() else "script"
            return f"chore({script_type}): update {file_path.name} for version {new_version}"
        else:
            return f"chore: update {file_path.name} for version {new_version}"
    
    # Workflow files
    if ".github/workflows" in file_path_str or ".github\\workflows" in file_path_str:
        return f"ci: update workflow {file_path.name} for version {new_version}"
    
    # Root-level files
    if "/" not in file_path_str.replace("\\", "/") or file_path_str.count("/") == 1 or file_path_str.count("\\") <= 2:
        if file_path_str.endswith((".json", ".yaml", ".yml", ".toml", ".txt")):
            return f"chore: update {file_path.name} for version {new_version}"
    
    # Default professional message
    return f"chore: update {file_path.name} for version {new_version}"

def get_all_changed_files(repo_root):
    """Get all changed files in the repository (including untracked)."""
    import subprocess
    
    try:
        # Get all modified, added, and untracked files
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True
        )
        
        files = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            
            # Parse git status output: "XY filename"
            # X = status of index, Y = status of work tree
            # M = modified, A = added, ?? = untracked
            status = line[:2]
            file_path = line[3:].strip().strip('"')
            
            # Skip deleted files (marked with "D" or " D")
            if status[0] == "D" or status[1] == "D":
                continue
            
            # Get full path relative to repo root
            full_path = repo_root / file_path
            if full_path.exists():
                files.append(full_path)
        
        return files
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Could not get changed files: {e}")
        return []
    except Exception as e:
        print(f"⚠️  Error getting changed files: {e}")
        return []

def commit_all_changed_files(repo_root, new_version, bump_type):
    """Commit all changed files individually with professional commit messages."""
    import subprocess
    
    changed_files = get_all_changed_files(repo_root)
    
    if not changed_files:
        print("ℹ️  No changed files detected")
        return 0
    
    print(f"\n📋 Found {len(changed_files)} changed file(s)")
    
    # Group files for better organization (but still commit individually)
    version_files = []
    doc_files = []
    config_files = []
    script_files = []
    workflow_files = []
    other_files = []
    
    for file_path in changed_files:
        file_path_str = str(file_path)
        file_name = file_path.name.lower()
        
        if file_name == "version" or "package.json" in file_name or "pyproject.toml" in file_name:
            version_files.append(file_path)
        elif file_path_str.endswith(".md"):
            doc_files.append(file_path)
        elif file_name in ["config.yaml", "config.yml", ".env", ".env.example"] or ".github" in file_path_str:
            if ".github/workflows" in file_path_str or ".github\\workflows" in file_path_str:
                workflow_files.append(file_path)
            else:
                config_files.append(file_path)
        elif file_path_str.endswith((".py", ".js", ".sh", ".bash")):
            script_files.append(file_path)
        else:
            other_files.append(file_path)
    
    committed_count = 0
    
    # Commit version files first (highest priority)
    for file_path in version_files:
        relative_path = file_path.relative_to(repo_root)
        commit_msg = get_commit_message_for_file(file_path, new_version, bump_type)
        
        try:
            subprocess.run(["git", "add", str(relative_path)], cwd=str(repo_root), check=True)
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=str(repo_root),
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✅ Committed: {relative_path}")
            committed_count += 1
        except subprocess.CalledProcessError as e:
            if "nothing to commit" in (e.stderr or "").lower():
                print(f"ℹ️  No changes: {relative_path}")
            else:
                print(f"⚠️  Failed to commit {relative_path}: {e}")
    
    # Commit documentation files
    for file_path in doc_files:
        relative_path = file_path.relative_to(repo_root)
        commit_msg = get_commit_message_for_file(file_path, new_version, bump_type)
        
        try:
            subprocess.run(["git", "add", str(relative_path)], cwd=str(repo_root), check=True)
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=str(repo_root),
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✅ Committed: {relative_path}")
            committed_count += 1
        except subprocess.CalledProcessError as e:
            if "nothing to commit" in (e.stderr or "").lower():
                print(f"ℹ️  No changes: {relative_path}")
            else:
                print(f"⚠️  Failed to commit {relative_path}: {e}")
    
    # Commit config and workflow files
    for file_path in config_files + workflow_files:
        relative_path = file_path.relative_to(repo_root)
        commit_msg = get_commit_message_for_file(file_path, new_version, bump_type)
        
        try:
            subprocess.run(["git", "add", str(relative_path)], cwd=str(repo_root), check=True)
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=str(repo_root),
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✅ Committed: {relative_path}")
            committed_count += 1
        except subprocess.CalledProcessError as e:
            if "nothing to commit" in (e.stderr or "").lower():
                print(f"ℹ️  No changes: {relative_path}")
            else:
                print(f"⚠️  Failed to commit {relative_path}: {e}")
    
    # Commit script files
    for file_path in script_files:
        relative_path = file_path.relative_to(repo_root)
        commit_msg = get_commit_message_for_file(file_path, new_version, bump_type)
        
        try:
            subprocess.run(["git", "add", str(relative_path)], cwd=str(repo_root), check=True)
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=str(repo_root),
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✅ Committed: {relative_path}")
            committed_count += 1
        except subprocess.CalledProcessError as e:
            if "nothing to commit" in (e.stderr or "").lower():
                print(f"ℹ️  No changes: {relative_path}")
            else:
                print(f"⚠️  Failed to commit {relative_path}: {e}")
    
    # Commit other files
    for file_path in other_files:
        relative_path = file_path.relative_to(repo_root)
        commit_msg = get_commit_message_for_file(file_path, new_version, bump_type)
        
        try:
            subprocess.run(["git", "add", str(relative_path)], cwd=str(repo_root), check=True)
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=str(repo_root),
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✅ Committed: {relative_path}")
            committed_count += 1
        except subprocess.CalledProcessError as e:
            if "nothing to commit" in (e.stderr or "").lower():
                print(f"ℹ️  No changes: {relative_path}")
            else:
                print(f"⚠️  Failed to commit {relative_path}: {e}")
    
    return committed_count

def create_git_commit(new_version, bump_type):
    """Create git commit and tag for version bump - commits ALL changed files individually."""
    import subprocess
    
    try:
        # ROOT DIRECTORY ONLY - Single source of truth
        script_dir = Path(__file__).parent.parent.parent
        repo_root = script_dir.parent
        
        print(f"\n🔍 Scanning repository for changed files...")
        committed_count = commit_all_changed_files(repo_root, new_version, bump_type)
        
        if committed_count == 0:
            print("⚠️  No files committed (no changes detected)")
            return
        
        print(f"\n✅ Successfully committed {committed_count} file(s)")
        
        # Create tag (from repo root) - check if exists first
        tag_name = f"v{new_version}"
        result = subprocess.run(
            ["git", "tag", "-l", tag_name],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.stdout.strip():
            print(f"⚠️  Tag {tag_name} already exists, skipping tag creation")
        else:
            subprocess.run(["git", "tag", tag_name], cwd=str(repo_root), check=True)
        print(f"✅ Created git tag: {tag_name}")
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Git operations failed: {e}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"   Error details: {e.stderr}")
        print("   You may need to commit and tag manually")
    except FileNotFoundError:
        print("⚠️  Git not found. Skipping git operations.")
        print("   Files updated but not committed. Commit manually:")
        print(f"   git add .")
        print(f"   git commit -m \"chore(release): bump version to {new_version} ({bump_type})\"")
        print(f"   git tag v{new_version}")

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
    
    # Update README.md links for devlog branch strategy
    print("\n🔗 Updating README.md links for devlog branch...")
    try:
        script_dir = Path(__file__).parent
        repo_root = script_dir.parent.parent.parent
        update_links_script = script_dir / "update_readme_links.py"
        
        if update_links_script.exists():
            import subprocess
            result = subprocess.run(
                [sys.executable, str(update_links_script)],
                cwd=repo_root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ README.md links updated")
            else:
                print(f"⚠️  Link update had issues: {result.stderr}")
        else:
            print("⚠️  update_readme_links.py not found, skipping link update")
    except Exception as e:
        print(f"⚠️  Error updating README links: {e}")
        print("   Continuing with version bump...")
    
    # Create git commit
    print("\n🏷️  Creating git commit and tag...")
    create_git_commit(new_version, bump_type)
    
    # Sync documentation to devlog branch
    print("\n📚 Syncing documentation to devlog branch...")
    try:
        sync_script = script_dir / "sync_to_devlog.py"
        if sync_script.exists():
            import subprocess
            result = subprocess.run(
                [sys.executable, str(sync_script)],
                cwd=repo_root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ Documentation synced to devlog branch")
            else:
                print(f"⚠️  Doc sync had issues: {result.stderr}")
                print("   You can manually sync later with: python scripts/ci/sync_to_devlog.py")
        else:
            print("⚠️  sync_to_devlog.py not found, skipping doc sync")
    except Exception as e:
        print(f"⚠️  Error syncing docs: {e}")
        print("   You can manually sync later with: python scripts/ci/sync_to_devlog.py")
    
    # Success message
    print("\n" + "=" * 50)
    print("🎉 VERSION BUMP SUCCESSFUL!")
    print("=" * 50)
    print(f"📊 Version: {current_version} → {new_version}")
    print(f"🔧 Bump Type: {bump_type}")
    print(f"🏷️  Git Tag: v{new_version}")
    print("\n📋 Next Steps:")
    print("  1. Review changes: git show HEAD")
    print("  2. Update docs: npm run version:update-docs")
    print("  3. Push to remote: git push origin main --tags")
    print("  4. Push devlog branch: git push origin devlog")
    print("=" * 50)

if __name__ == "__main__":
    main()
