#!/usr/bin/env python3
"""
Onboarding Smoke Test (Non-interactive)

Runs a minimal, fast check that core CLI commands can be invoked
without user input on a blank environment. Intended for CI and
fresh developer machines.
"""

import subprocess
import sys
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def run(cmd, cwd=None, timeout=120, env=None):
    merged_env = os.environ.copy()
    merged_env.update(env or {})
    merged_env.setdefault("PYTHONIOENCODING", "utf-8")
    proc = subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=merged_env,
    )
    return proc.returncode, proc.stdout, proc.stderr


def main():
    failures = []

    # 1) Version/help should work
    cli_entry = ROOT / "hyperkit-agent" / "cli" / "main.py"
    # Help
    code, out, err = run(f"python {cli_entry} --help")
    if code != 0:
        failures.append(("cli --help", code, err or out))

    # Version (subcommand)
    code, out, err = run(f"python {cli_entry} version")
    if code != 0:
        failures.append(("cli version", code, err or out))

    # 2) Workflow status (non-networked)
    code, out, err = run(f"python {cli_entry} workflow status")
    if code != 0:
        failures.append(("workflow status", code, err or out))

    # 3) RAG test (if present) - optional, do not fail hard
    code, out, err = run(f"python {cli_entry} test_rag --help")

    # 4) Config list (non-interactive default)
    code, out, err = run(f"python {cli_entry} config list")
    if code != 0:
        failures.append(("config list", code, err or out))

    # 5) Monitor health (non-interactive)
    code, out, err = run(f"python {cli_entry} monitor health")
    if code != 0:
        failures.append(("monitor health", code, err or out))

    if failures:
        print("\nOnboarding smoke test FAILED:\n")
        for name, code, msg in failures:
            print(f" - {name}: exit={code}\n{msg[:4000]}\n")
        sys.exit(1)

    print("Onboarding smoke test PASSED")


if __name__ == "__main__":
    main()


