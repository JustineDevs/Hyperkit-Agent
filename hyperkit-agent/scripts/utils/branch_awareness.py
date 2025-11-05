#!/usr/bin/env python3
"""
Branch Awareness Utilities

Helper functions for scripts to detect current branch and handle
devlog branch strategy appropriately.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

# Devlog-only directories (should not exist in main)
DEVLOG_ONLY_DIRS = [
    "hyperkit-agent/REPORTS/",
    "hyperkit-agent/docs/TEAM/",
    "hyperkit-agent/docs/EXECUTION/",
    "hyperkit-agent/docs/INTEGRATION/",
    "hyperkit-agent/docs/REFERENCE/",
    "docs/",  # Root-level docs
]

# Essential directories that exist in main
MAIN_DIRS = [
    "hyperkit-agent/docs/GUIDE/",
]


def get_current_branch(repo_root: Optional[Path] = None) -> Optional[str]:
    """
    Get current git branch name.
    
    Args:
        repo_root: Repository root directory (defaults to auto-detect)
        
    Returns:
        Branch name or None if not a git repo
    """
    if repo_root is None:
        repo_root = Path.cwd()
    
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def is_devlog_branch(repo_root: Optional[Path] = None) -> bool:
    """
    Check if current branch is devlog.
    
    Args:
        repo_root: Repository root directory
        
    Returns:
        True if on devlog branch
    """
    branch = get_current_branch(repo_root)
    return branch == "devlog"


def is_main_branch(repo_root: Optional[Path] = None) -> bool:
    """
    Check if current branch is main.
    
    Args:
        repo_root: Repository root directory
        
    Returns:
        True if on main branch
    """
    branch = get_current_branch(repo_root)
    return branch == "main"


def check_devlog_dir_access(path: Path, warn: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Check if a path is in a devlog-only directory and warn if on main branch.
    
    Args:
        path: Path to check
        warn: If True, print warning to stderr
        
    Returns:
        Tuple of (is_devlog_only, warning_message)
    """
    path_str = str(path)
    
    # Check if path is in devlog-only directory
    is_devlog_only = any(
        path_str.startswith(devlog_dir) or devlog_dir in path_str
        for devlog_dir in DEVLOG_ONLY_DIRS
    )
    
    if is_devlog_only and is_main_branch():
        warning = (
            f"[WARNING] Writing to devlog-only directory from main branch: {path}\n"
            f"         This file will be moved to devlog branch on next sync.\n"
            f"         Consider checking out devlog branch: git checkout devlog"
        )
        if warn:
            print(warning, file=sys.stderr)
        return True, warning
    
    return False, None


def get_repo_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find repository root by looking for .git directory.
    
    Args:
        start_path: Starting directory (defaults to current directory)
        
    Returns:
        Path to repo root or None if not found
    """
    if start_path is None:
        start_path = Path.cwd()
    
    current = Path(start_path).resolve()
    
    # Look for .git directory
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    
    return None


def suggest_branch_for_operation(operation: str, target_path: Optional[Path] = None) -> str:
    """
    Suggest appropriate branch for an operation.
    
    Args:
        operation: Description of operation (e.g., "writing reports")
        target_path: Target path for operation
        
    Returns:
        Suggestion message
    """
    current_branch = get_current_branch()
    
    if target_path:
        is_devlog_only, _ = check_devlog_dir_access(target_path, warn=False)
        if is_devlog_only and current_branch != "devlog":
            return (
                f"[SUGGESTION] {operation} to devlog-only directory.\n"
                f"            Current branch: {current_branch}\n"
                f"            Suggested: git checkout devlog"
            )
    
    return f"[INFO] {operation} on branch: {current_branch or 'unknown'}"


if __name__ == "__main__":
    # Test script
    repo_root = get_repo_root()
    branch = get_current_branch(repo_root)
    
    print(f"Repository root: {repo_root}")
    print(f"Current branch: {branch}")
    print(f"Is devlog: {is_devlog_branch(repo_root)}")
    print(f"Is main: {is_main_branch(repo_root)}")
    
    # Test path checking
    test_path = Path("hyperkit-agent/REPORTS/test.md")
    is_devlog_only, warning = check_devlog_dir_access(test_path)
    if warning:
        print(f"\n{warning}")

