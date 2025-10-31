#!/usr/bin/env python3
"""
Automate HONEST_STATUS.md date bump after successful CI.
"""

import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATUS = ROOT / "hyperkit-agent" / "docs" / "HONEST_STATUS.md"


def main():
    if not STATUS.exists():
        return
    text = STATUS.read_text(encoding="utf-8").splitlines()
    today = dt.date.today().isoformat()
    out = []
    for line in text:
        if line.strip().startswith("**Last Updated**"):
            out.append(f"**Last Updated**: {today}  ")
        else:
            out.append(line)
    STATUS.write_text("\n".join(out), encoding="utf-8")
    print("HONEST_STATUS.md date updated")


if __name__ == "__main__":
    main()


