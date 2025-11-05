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
from datetime import datetime

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
    
    # Reports consolidation (optional - merges individual reports into consolidated files)
    ("python hyperkit-agent/scripts/reports/merge.py", "Consolidate individual reports", True),
    
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

def stage_all_modified_files() -> int:
    """Stage ALL modified files (not just patterns). Returns number of files staged."""
    # Get all modified files
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    
    if not result.stdout.strip():
        return 0
    
    # Parse status output and stage all modified files
    staged_count = 0
    already_staged = set()
    
    # First, get list of already staged files
    staged_result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only'],
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    if staged_result.stdout.strip():
        already_staged = set(staged_result.stdout.strip().split('\n'))
    
    for line in result.stdout.strip().split('\n'):
        if not line.strip():
            continue
        # Status format: XY filename
        # X = staged status, Y = working tree status
        status = line[:2]
        filename = line[3:].strip()
        
        # Remove quotes if present
        if filename.startswith('"') and filename.endswith('"'):
            filename = filename[1:-1]
        
        # Skip if already staged
        if filename in already_staged:
            continue
        
        # Stage if file is modified (M), deleted (D), or untracked (?)
        # Only stage files in working tree (Y != ' ')
        if status[1] in ['M', 'D', '?']:
            try:
                subprocess.run(
                    ['git', 'add', filename],
                    capture_output=True,
                    cwd=REPO_ROOT,
                    check=False
                )
                staged_count += 1
            except Exception:
                pass  # Skip files that can't be staged
    
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
        print("\n❌ [ERROR] Working tree has uncommitted changes")
        print("   Hygiene workflow requires a clean working tree for safety.")
        print("   Branch switching and merging with uncommitted changes can cause data loss.\n")
        
        # Show what files have changes
        try:
            result = subprocess.run(
                ['git', 'status', '--short'],
                capture_output=True, text=True, cwd=REPO_ROOT
            )
            if result.stdout.strip():
                lines = result.stdout.strip().split('\n')[:10]
                print("   Uncommitted changes detected:")
                for line in lines:
                    print(f"     {line}")
                if len(result.stdout.strip().split('\n')) > 10:
                    print(f"     ... and {len(result.stdout.strip().split('\n')) - 10} more files")
                print()
        except:
            pass
        
        print("   📋 Next steps:")
        print("   1. Review changes: git status")
        print("   2. Commit changes: git add . && git commit -m 'your message'")
        print("      OR stash changes: git stash")
        print("   3. Re-run: npm run hygiene")
        print()
        print("   ⚠️  Never bypass this check - it protects your repository integrity!\n")
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
    
    # CRITICAL: Commit all generated/modified files immediately after scripts run
    # This ensures files like legacy_file_inventory.json are captured before sync
    print("[STEP 1.5] Committing generated files from scripts...")
    print("-" * 60)
    
    if not dry_run:
        # Stage ALL modified files (including generated files from scripts)
        generated_files_staged = stage_all_modified_files()
        
        if generated_files_staged > 0:
            # Commit generated files with a descriptive message
            commit_message = f"chore: commit generated files from workflow scripts\n\n" \
                           f"Auto-committed {generated_files_staged} file(s) generated by:\n" \
                           f"- Legacy file inventory\n" \
                           f"- Documentation drift audit\n" \
                           f"- Report consolidation\n" \
                           f"- Other maintenance scripts\n\n" \
                           f"Generated: {datetime.now().isoformat()}"
            
            try:
                result = subprocess.run(
                    ['git', 'diff', '--cached', '--quiet'],
                    capture_output=True, cwd=REPO_ROOT
                )
                if result.returncode != 0:
                    # There are staged changes, commit them
                    subprocess.run(
                        ['git', 'commit', '-m', commit_message],
                        check=True, cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    print(f"  ✅ Committed {generated_files_staged} generated file(s)")
                else:
                    print(f"  [INFO] No generated files to commit")
            except subprocess.CalledProcessError as e:
                print(f"  ⚠️  Could not commit generated files: {e}")
                print(f"     Continuing anyway - files will be committed in STEP 2")
        else:
            print(f"  [INFO] No generated files detected")
    else:
        print(f"  [DRY RUN] Would commit generated files from scripts")
    
    print("-" * 60)
    print()
    
    # Stage and commit changes on main
    print("[STEP 2] Staging and committing changes on main branch...")
    print("-" * 60)
    
    if current_branch != 'main' and not dry_run:
        print("[SWITCH] Not on main branch. Switching to main...")
        subprocess.run(['git', 'checkout', 'main'], check=True, cwd=REPO_ROOT)
        current_branch = 'main'
    
    # Stage files matching patterns first
    staged = stage_files(MAIN_STAGE_PATTERNS)
    
    # Also stage ALL other modified files (from scripts that modified files)
    # This catches any files that weren't committed in STEP 1.5
    additional_staged = stage_all_modified_files()
    total_staged = staged + additional_staged
    
    if total_staged > 0:
        if dry_run:
            print(f"[DRY RUN] Would commit {total_staged} files to main")
            if staged > 0:
                print(f"         ({staged} from patterns, {additional_staged} additional modified files)")
        else:
            commit_changes("chore: run workflow scripts, update docs and hygiene", "main")
    else:
        print("  [INFO] No files to stage on main")
    
    print()
    print("-" * 60)
    print()
    
    # Verify working tree is clean before syncing
    print("[STEP 2.5] Verifying working tree is clean...")
    print("-" * 60)
    
    if not dry_run:
        if not is_clean_working_tree():
            # Try to commit any remaining uncommitted changes
            remaining_staged = stage_all_modified_files()
            if remaining_staged > 0:
                try:
                    commit_message = f"chore: commit remaining workflow changes\n\n" \
                                   f"Auto-committed {remaining_staged} remaining file(s) from workflow.\n" \
                                   f"Generated: {datetime.now().isoformat()}"
                    result = subprocess.run(
                        ['git', 'diff', '--cached', '--quiet'],
                        capture_output=True, cwd=REPO_ROOT
                    )
                    if result.returncode != 0:
                        subprocess.run(
                            ['git', 'commit', '-m', commit_message],
                            check=True, cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                        )
                        print(f"  ✅ Committed {remaining_staged} remaining file(s)")
                    else:
                        print(f"  [INFO] No remaining files to commit")
                except subprocess.CalledProcessError as e:
                    print(f"  ⚠️  Could not commit remaining files: {e}")
            
            # Check again
            if not is_clean_working_tree():
                print(f"  ⚠️  Working tree still has uncommitted changes")
                print(f"     This may cause sync-to-devlog to fail")
                result = subprocess.run(
                    ['git', 'status', '--short'],
                    capture_output=True, text=True, cwd=REPO_ROOT
                )
                if result.stdout.strip():
                    lines = result.stdout.strip().split('\n')[:5]
                    print(f"     Uncommitted files:")
                    for line in lines:
                        print(f"       {line}")
            else:
                print(f"  ✅ Working tree is clean")
        else:
            print(f"  ✅ Working tree is clean")
    else:
        print(f"  [DRY RUN] Would verify working tree is clean")
    
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

