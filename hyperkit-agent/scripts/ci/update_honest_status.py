#!/usr/bin/env python3
"""
Automate HONEST_STATUS.md date bump after successful CI.

Note: This script updates HONEST_STATUS.md which is in devlog branch.
If run from main branch, the update will be synced to devlog on next sync.
"""

import datetime as dt
import sys
from pathlib import Path

# Add branch awareness
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
try:
    from branch_awareness import check_devlog_dir_access, is_devlog_branch
except ImportError:
    # Fallback if utils not available
    def check_devlog_dir_access(path, warn=False):
        return False, None
    def is_devlog_branch():
        return False

ROOT = Path(__file__).resolve().parents[2]
STATUS = ROOT / "hyperkit-agent" / "docs" / "HONEST_STATUS.md"


def main():
    if not STATUS.exists():
        return
    
    # Check if we're writing to devlog-only directory
    is_devlog_only, _ = check_devlog_dir_access(STATUS, warn=True)
    
    text = STATUS.read_text(encoding="utf-8").splitlines()
    today = dt.date.today().isoformat()
    out = []
    for line in text:
        if line.strip().startswith("**Last Updated**"):
            out.append(f"**Last Updated**: {today}  ")
        else:
            out.append(line)
    STATUS.write_text("\n".join(out), encoding="utf-8")
    
    if is_devlog_only and not is_devlog_branch():
        print(f"HONEST_STATUS.md date updated (will sync to devlog on next sync)")
    else:
        print("HONEST_STATUS.md date updated")


if __name__ == "__main__":
    main()


