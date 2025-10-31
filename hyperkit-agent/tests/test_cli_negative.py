import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd):
    return subprocess.run(cmd, cwd=ROOT, shell=True, capture_output=True, text=True, timeout=60)


def test_unknown_flag():
    cli_entry = ROOT / "hyperkit-agent" / "cli" / "main.py"
    proc = run(f"python {cli_entry} --unknown-flag")
    assert proc.returncode != 0


def test_deploy_invalid_network():
    proc = run(f"python {cli_entry} workflow run \"create ERC20 token\" --network mainnet")
    # mainnet is not supported; expect non-zero and warning in output
    assert proc.returncode != 0


def test_config_get_missing_file():
    # Move config if exists
    cfg = ROOT / "hyperkit-agent" / "config.yaml"
    backup = ROOT / "hyperkit-agent" / "config.yaml.bak"
    if cfg.exists():
        cfg.rename(backup)
    try:
        proc = run(f"python {cli_entry} config get NON_EXISTENT_KEY")
        # Should not crash (non-interactive output expected)
        assert proc.returncode == 0
    finally:
        if backup.exists():
            backup.rename(cfg)


