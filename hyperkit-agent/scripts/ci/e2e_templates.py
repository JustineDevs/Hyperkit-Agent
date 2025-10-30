#!/usr/bin/env python3
"""
E2E Test Runner for Official Templates

Runs generate → compile → (optional) deploy → verify for a small set of
official templates on Hyperion, capturing non-interactive results. Deployment
is skipped if required env (DEFAULT_PRIVATE_KEY) is missing.
"""

import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


TEMPLATES = [
    'create ERC20 token',
    'create staking contract with rewards',
]


def run(cmd, cwd=None, timeout=600):
    proc = subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return proc.returncode, proc.stdout, proc.stderr


def main():
    failures = []
    can_deploy = bool(os.getenv('DEFAULT_PRIVATE_KEY') or os.getenv('PRIVATE_KEY'))

    for prompt in TEMPLATES:
        # Generate + audit (test-only)
        cmd = f"python -m hyperkit-agent.cli.main workflow run \"{prompt}\" --test-only"
        code, out, err = run(cmd)
        if code != 0 or 'success' not in (out.lower() + err.lower()):
            failures.append((f"workflow test-only: {prompt}", code, err or out))
            continue

        # Deploy + verify when possible
        if can_deploy:
            cmd = f"python -m hyperkit-agent.cli.main workflow run \"{prompt}\""
            code, out, err = run(cmd, timeout=900)
            if code != 0:
                failures.append((f"workflow deploy: {prompt}", code, err or out))

    if failures:
        print("\nE2E templates test FAILED:\n")
        for name, code, msg in failures:
            print(f" - {name}: exit={code}\n{msg[:4000]}\n")
        sys.exit(1)

    print("E2E templates test PASSED")


if __name__ == "__main__":
    main()


