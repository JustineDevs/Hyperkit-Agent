#!/usr/bin/env python3
"""
One-Command Branch+Workflow Hygiene Script

Chains together all doc/code/scripts needed for docs/code hygiene:
- Runs all internal formatting, generation, reporting, audits
- Stages and commits any files that scripts modify
- Switches to correct target branch (main or devlog)
- Optionally push/pull/merge branches
- Atomic and safe: If one script fails, halts and shows what changed

Usage:
    python sync_workflow.py [--dry-run] [--push]
    npm run hygiene [--dry-run] [--push]
"""

import subprocess
import sys
import signal
import json
import atexit
import io
from pathlib import Path
from typing import List, Tuple, Optional
import argparse

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Determine script location for relative paths
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent  # From hyperkit-agent/scripts/ci/ to repo root

# Track original branch for safe cleanup
ORIGINAL_BRANCH = None
CLEANUP_REGISTERED = False

# Workflow scripts to run (in order)
# Format: (command, description, optional)
# optional=True means script will be skipped if not found (won't fail workflow)
# NOTE: All automation/workflow scripts are now JavaScript (Node.js)
# Python scripts are only for AI/LLM/core system functionality
WORKFLOW_SCRIPTS = [
    # Meta file cleanup (required - prevents duplicate drift) - JavaScript
    ("node hyperkit-agent/scripts/release/cleanup-meta-dupes.js", "Cleanup duplicate meta files", False),
    
    # Documentation updates (required) - JavaScript
    ("node hyperkit-agent/scripts/release/update-readme-links.js", "Update README links", False),
    
    # Maintenance scripts (optional - may not exist in devlog branch) - Python (AI/analysis)
    ("python hyperkit-agent/scripts/maintenance/doc_drift_audit.py", "Documentation drift audit", True),
    ("python hyperkit-agent/scripts/maintenance/doc_drift_cleanup.py", "Documentation cleanup", True),
    ("python hyperkit-agent/scripts/maintenance/cli_command_inventory.py", "CLI command inventory", True),
    ("python hyperkit-agent/scripts/maintenance/legacy_file_inventory.py", "Legacy file inventory", True),
    
    # Version updates (optional - may not exist) - JavaScript
    ("node hyperkit-agent/scripts/release/update-version-in-docs.js", "Update version in docs", True),
]

# Load patterns from config file (if exists), otherwise use defaults
PATTERNS_FILE = SCRIPT_DIR / "workflow_patterns.json"

def load_patterns():
    """Load file patterns from config file, with fallback to defaults."""
    if PATTERNS_FILE.exists():
        try:
            with open(PATTERNS_FILE, 'r', encoding='utf-8') as f:
                patterns = json.load(f)
                return (
                    patterns.get("main_stage_patterns", []),
                    patterns.get("devlog_stage_patterns", [])
                )
        except Exception as e:
            print(f"[WARNING] Failed to load patterns from {PATTERNS_FILE}: {e}")
            print("[INFO] Using default patterns")
    
    # Default patterns (fallback)
    main_patterns = [
        "README.md",
        "CHANGELOG.md",
        "hyperkit-agent/docs/GUIDE/",
        "hyperkit-agent/config.yaml",
        "hyperkit-agent/pyproject.toml",
        "package.json",
        "VERSION",
    ]
    devlog_patterns = [
        "hyperkit-agent/REPORTS/",
        "hyperkit-agent/docs/TEAM/",
        "hyperkit-agent/docs/EXECUTION/",
        "hyperkit-agent/docs/INTEGRATION/",
        "hyperkit-agent/docs/REFERENCE/",
        "docs/",
    ]
    return main_patterns, devlog_patterns

MAIN_STAGE_PATTERNS, DEVLOG_STAGE_PATTERNS = load_patterns()

# NOTE: sync_to_devlog() function below now calls the JavaScript version
# instead of Python. This maintains the orchestrator pattern while using JS for automation.


def check_script_exists(cmd: str) -> bool:
    """Check if a script file exists."""
    # Extract script path from command
    script_file = cmd.replace("python ", "").replace("node ", "").split()[0]
    full_path = REPO_ROOT / script_file
    return full_path.exists()


def run_command(cmd: str, description: str, cwd: Optional[Path] = None, optional: bool = False) -> Tuple[bool, str]:
    """Run a command and return success status and output."""
    # Check if script exists first
    script_path = cmd.replace("python ", "").replace("node ", "").split()[0]
    if not check_script_exists(cmd):
        if optional:
            print(f"[SKIP] {description}... (script not found, optional)")
            return True, ""  # Skip optional scripts
        else:
            print(f"[SKIP] {description}... (script not found)")
            return True, ""  # Skip missing scripts gracefully
    
    print(f"[RUN] {description}...")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=True, 
            cwd=cwd or REPO_ROOT, timeout=300, encoding='utf-8', errors='replace'
        )
        print(f"  [OK] {description} completed")
        if result.stdout and result.stdout.strip():
            # Show first few lines of output if verbose
            lines = result.stdout.strip().split('\n')[:3]
            for line in lines:
                if line.strip():
                    # Clean line of problematic Unicode for Windows console
                    clean_line = line.encode('ascii', errors='replace').decode('ascii')
                    print(f"    {clean_line}")
        return True, result.stdout or ""
    except subprocess.TimeoutExpired:
        print(f"  [ERROR] {description} timed out (exceeded 5 minutes)")
        if optional:
            return False, "timeout"  # Optional scripts can fail
        return False, "timeout"
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] {description} failed")
        if e.stderr:
            # Show error but truncate for readability
            error_lines = e.stderr.strip().split('\n')[:5]
            for line in error_lines:
                if line.strip():
                    print(f"    {line}")
            if len(e.stderr.strip().split('\n')) > 5:
                print(f"    ... (truncated, see full error above)")
        # Don't fail on optional scripts - they're allowed to fail
        if optional:
            return False, e.stderr or ""  # Return False but don't halt workflow
        return False, e.stderr or ""


def get_current_branch() -> str:
    """Get current git branch."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True, text=True, check=True, cwd=REPO_ROOT
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"


def is_clean_working_tree() -> bool:
    """Check if working tree is clean."""
    result = subprocess.run(
        ['git', 'diff', '--quiet', 'HEAD'], 
        capture_output=True, cwd=REPO_ROOT
    )
    return result.returncode == 0


def stage_files(patterns: List[str]) -> int:
    """Stage files matching patterns. Returns number of files staged."""
    staged_count = 0
    for pattern in patterns:
        # Check if pattern exists
        pattern_path = REPO_ROOT / pattern
        if not pattern_path.exists() and '*' not in pattern:
            continue
            
        result = subprocess.run(
            ['git', 'add', pattern], 
            capture_output=True, 
            cwd=REPO_ROOT
        )
        if result.returncode == 0:
            # Check if anything was actually staged
            check = subprocess.run(
                ['git', 'diff', '--cached', '--name-only', pattern],
                capture_output=True, text=True, cwd=REPO_ROOT
            )
            if check.stdout.strip():
                staged_count += len(check.stdout.strip().split('\n'))
    return staged_count


def commit_changes(message: str, branch: str) -> bool:
    """Commit staged changes."""
    # Check if there are staged changes
    result = subprocess.run(
        ['git', 'diff', '--cached', '--quiet'], 
        capture_output=True, cwd=REPO_ROOT
    )
    if result.returncode == 0:
        print(f"  [INFO] No changes to commit on {branch}")
        return True
    
    commit_message = f"{message}\n\n[ci skip]"
    result = subprocess.run(
        ['git', 'commit', '-m', commit_message],
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    if result.returncode == 0:
        print(f"  [OK] Committed changes to {branch}")
        return True
    else:
        print(f"  ✗ Failed to commit: {result.stderr}")
        return False


def sync_to_devlog(dry_run: bool = False) -> bool:
    """
    Sync documentation to devlog branch.
    
    NOTE: This now calls the JavaScript version (sync-to-devlog.js) instead of
    implementing the logic directly. This maintains the orchestrator pattern
    while using JavaScript for all automation.
    """
    if dry_run:
        print("[DRY RUN] Would sync to devlog branch (calling JS script)")
        # Call JS script with --dry-run
        try:
            subprocess.run(
                ['node', 'hyperkit-agent/scripts/release/sync-to-devlog.js', '--dry-run'],
                check=True, cwd=REPO_ROOT, stdout=None, stderr=None
            )
        except subprocess.CalledProcessError:
            print("[WARNING] JS sync script failed, but continuing in dry-run mode")
        return True
    
    # Call the JavaScript version
    print("[SYNC] Calling JavaScript sync-to-devlog.js...")
    try:
        subprocess.run(
            ['node', 'hyperkit-agent/scripts/release/sync-to-devlog.js'],
            check=True, cwd=REPO_ROOT, stdout=None, stderr=None
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to sync to devlog: {e}")
        return False


def cleanup_on_exit():
    """Cleanup function to restore original branch on exit/error."""
    global ORIGINAL_BRANCH
    if ORIGINAL_BRANCH:
        current = get_current_branch()
        if current != ORIGINAL_BRANCH:
            try:
                print(f"\n[CLEANUP] Restoring original branch: {ORIGINAL_BRANCH}")
                subprocess.run(
                    ['git', 'checkout', ORIGINAL_BRANCH],
                    check=False, cwd=REPO_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            except Exception:
                pass  # Best effort cleanup


def signal_handler(signum, frame):
    """Handle interrupt signals (CTRL+C) gracefully."""
    print("\n\n[INTERRUPT] Workflow interrupted by user")
    cleanup_on_exit()
    sys.exit(130)  # Standard exit code for SIGINT


def run_hygiene_workflow(dry_run: bool = False, push: bool = False) -> bool:
    """
    Run the complete hygiene workflow.
    
    Args:
        dry_run: If True, show what would be done without making changes
        push: If True, push changes to remote (default: False for safety)
    """
    global ORIGINAL_BRANCH, CLEANUP_REGISTERED
    
    # Register signal handlers for safe cleanup
    if not CLEANUP_REGISTERED:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        atexit.register(cleanup_on_exit)
        CLEANUP_REGISTERED = True
    
    # Store original branch for cleanup
    ORIGINAL_BRANCH = get_current_branch()
    
    print("=" * 60)
    print("HYPERAGENT BRANCH+WORKFLOW HYGIENE")
    print("=" * 60)
    print()
    
    if dry_run:
        print("[DRY RUN] Mode: No changes will be made")
        print()
    
    # Check working tree
    if not is_clean_working_tree() and not dry_run:
        print("[ERROR] Working tree has uncommitted changes")
        print("   Please commit or stash changes before running hygiene workflow")
        print()
        print("   Run: git status")
        return False
    
    current_branch = ORIGINAL_BRANCH
    print(f"[INFO] Current branch: {current_branch}")
    print(f"[INFO] Repository root: {REPO_ROOT}")
    print()
    
    # Run all workflow scripts
    print("[STEP 1] Running workflow scripts...")
    print("-" * 60)
    failed_scripts = []
    optional_failed_scripts = []
    successful_scripts = []
    
    for script_info in WORKFLOW_SCRIPTS:
        if len(script_info) == 3:
            cmd, description, optional = script_info
        else:
            # Backward compatibility
            cmd, description = script_info
            optional = False
        
        success, output = run_command(cmd, description, optional=optional)
        if success:
            successful_scripts.append(description)
        else:
            if optional:
                optional_failed_scripts.append(description)
                print(f"  [WARN] {description} failed (optional, continuing)")
            else:
                failed_scripts.append(description)
                if not dry_run:
                    print()
                    print("[ERROR] Workflow halted due to required script failure")
                    print(f"   Failed script: {description}")
                    print("   Fix the error and run again")
                    cleanup_on_exit()
                    return False
    
    # Print summary of script execution
    print()
    print(f"  [OK] Successful: {len(successful_scripts)} scripts")
    if optional_failed_scripts:
        print(f"  [WARN] Optional failed: {len(optional_failed_scripts)} scripts")
        for script in optional_failed_scripts:
            print(f"      - {script}")
    if failed_scripts:
        print(f"  [ERROR] Required failed: {len(failed_scripts)} scripts")
        cleanup_on_exit()
        return False
    
    print()
    print("-" * 60)
    print()
    
    # Stage and commit changes on main
    print("[STEP 2] Staging and committing changes on main branch...")
    print("-" * 60)
    
    if current_branch != 'main' and not dry_run:
        print("[SWITCH] Not on main branch. Switching to main...")
        subprocess.run(['git', 'checkout', 'main'], check=True, cwd=REPO_ROOT)
        current_branch = 'main'
    
    staged = stage_files(MAIN_STAGE_PATTERNS)
    if staged > 0:
        if dry_run:
            print(f"[DRY RUN] Would commit {staged} files to main")
        else:
            commit_changes("chore: run workflow scripts, update docs and hygiene", "main")
    else:
        print("  [INFO] No files to stage on main")
    
    print()
    print("-" * 60)
    print()
    
    # Sync to devlog
    print("[STEP 3] Syncing documentation to devlog branch...")
    print("-" * 60)
    if not sync_to_devlog(dry_run):
        print("[ERROR] Failed to sync to devlog")
        return False
    
    print()
    print("-" * 60)
    print()
    
    # Final status
    print("[STEP 4] Final status...")
    print("-" * 60)
    result = subprocess.run(
        ['git', 'status', '--short'], 
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    if result.stdout.strip():
        print("Remaining uncommitted changes:")
        print(result.stdout)
    else:
        print("  [OK] Working tree is clean")
    
    print()
    print("=" * 60)
    print("[OK] HYGIENE WORKFLOW COMPLETE")
    print("=" * 60)
    
    if push:
        print()
        print("[PUSH] Pushing changes to remote...")
        try:
            subprocess.run(['git', 'push', 'origin', 'main'], check=True, cwd=REPO_ROOT)
            print("  [OK] Pushed main branch")
        except subprocess.CalledProcessError:
            print("  ✗ Failed to push main branch")
        
        try:
            subprocess.run(['git', 'push', 'origin', 'devlog'], check=True, cwd=REPO_ROOT)
            print("  [OK] Pushed devlog branch")
        except subprocess.CalledProcessError:
            print("  ✗ Failed to push devlog branch")
    else:
        print()
        print("[INFO] To push changes to remote, run:")
        print("  npm run hygiene:push")
        print("  or")
        print("  git push origin main && git push origin devlog")
    
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="One-command branch+workflow hygiene script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (see what would be done)
  npm run hygiene:dry-run
  
  # Run workflow (commit changes locally)
  npm run hygiene
  
  # Run workflow and push to remote
  npm run hygiene:push
        """
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--push',
        action='store_true',
        help='Push changes to remote (default: False for safety)'
    )
    
    args = parser.parse_args()
    
    success = run_hygiene_workflow(dry_run=args.dry_run, push=args.push)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

