#!/usr/bin/env python3
"""
CI aggregator: runs onboarding, E2E, failure modes, network resilience, pytest.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def run(name, cmd, timeout=900):
    print(f"\n=== {name} ===\n{cmd}\n")
    proc = subprocess.run(cmd, cwd=ROOT, shell=True, capture_output=True, text=True, timeout=timeout)
    print(proc.stdout)
    if proc.returncode != 0:
        print(proc.stderr)
        raise SystemExit(f"{name} failed: exit {proc.returncode}")


def main():
    run("Onboarding Smoke", "python hyperkit-agent/scripts/ci/onboarding_smoke.py", timeout=240)
    run("E2E Templates", "python hyperkit-agent/scripts/ci/e2e_templates.py", timeout=900)
    run("Failure Modes", "python hyperkit-agent/scripts/ci/failure_modes.py", timeout=120)
    run("Network Resilience", "python hyperkit-agent/scripts/ci/network_resilience.py", timeout=240)
    run("Pytest", "pytest -q", timeout=900)
    run("Update Honest Status", "python hyperkit-agent/scripts/ci/update_honest_status.py", timeout=60)
    print("\nAll CI tasks completed successfully.")


if __name__ == "__main__":
    main()


