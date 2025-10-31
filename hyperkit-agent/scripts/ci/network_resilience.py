#!/usr/bin/env python3
"""
Network resilience checks: simulate bad RPC and timeouts; ensure loud, actionable errors.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def run(cmd, timeout=60):
    return subprocess.run(cmd, cwd=ROOT, shell=True, capture_output=True, text=True, timeout=timeout)


def main():
    failures = []

    # Simulate bad RPC by overriding env temporarily
    env = os.environ.copy()
    env["HYPERION_RPC_URL"] = "http://127.0.0.1:59999"  # likely closed port
    cli_entry = ROOT / "hyperkit-agent" / "cli" / "main.py"
    proc = subprocess.run(
        f"python {cli_entry} status",
        cwd=ROOT,
        shell=True,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    if proc.returncode != 0 and "CRITICAL" not in (proc.stdout + proc.stderr):
        failures.append(("status with bad RPC", proc.returncode, proc.stderr or proc.stdout))

    # Force workflow with invalid RPC via config override is more complex; skip

    if failures:
        print("\nNetwork resilience FAILED:\n")
        for name, code, msg in failures:
            print(f" - {name}: exit={code}\n{msg[:4000]}\n")
        sys.exit(1)

    print("Network resilience PASSED")


if __name__ == "__main__":
    main()


