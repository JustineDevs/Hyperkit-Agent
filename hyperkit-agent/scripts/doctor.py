#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HyperKit-Agent Doctor: Production-Grade Preflight & Self-Healing System
Implements hardened dependency validation and auto-repair.
"""

import os
import sys
import subprocess
import shutil
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def print_bold(msg: str):
    print(f"{Colors.BOLD}{msg}{Colors.RESET}")

def run_cmd(cmd: List[str], cwd: Optional[Path] = None, capture_output: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    """Run command with proper error handling"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            timeout=60,
            check=check
        )
        return result
    except subprocess.TimeoutExpired:
        print_error(f"Command timed out: {' '.join(cmd)}")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        if check:
            print_error(f"Command failed: {' '.join(cmd)}")
            if e.stderr:
                print_error(f"Error: {e.stderr}")
        raise
    except FileNotFoundError:
        print_error(f"Command not found: {cmd[0]}")
        print_info(f"💡 Please install {cmd[0]} or add it to PATH")
        sys.exit(1)

def check_tool(tool: str, version_flag: str = "--version") -> Tuple[bool, Optional[str]]:
    """Check if a tool is available and get its version"""
    try:
        result = run_cmd([tool, version_flag], check=False)
        if result.returncode == 0:
            version = result.stdout.strip().split('\n')[0] if result.stdout else "installed"
            return True, version
        return False, None
    except Exception:
        return False, None

def check_required_tools() -> Dict[str, Tuple[bool, Optional[str]]]:
    """Check all required tools with version detection"""
    print_bold("\nStep 1: Checking Required Tools")
    
    tools = {
        "forge": ["forge", "--version"],
        "python": ["python", "--version"],
        "node": ["node", "--version"],
        "npm": ["npm", "--version"],
    }
    
    results = {}
    all_present = True
    
    for tool, cmd in tools.items():
        present, version = check_tool(cmd[0], cmd[1] if len(cmd) > 1 else "--version")
        results[tool] = (present, version)
        
        if present:
            print_success(f"{tool}: {version}")
        else:
            print_error(f"{tool}: NOT FOUND")
            all_present = False
    
    if not all_present:
        print_error("\n❌ Missing required tools. Please install:")
        print_info("  - Forge: curl -L https://foundry.paradigm.xyz | bash && foundryup")
        print_info("  - Python: https://www.python.org/downloads/")
        print_info("  - Node.js: https://nodejs.org/")
        sys.exit(1)
    
    return results

def check_openzeppelin_installation(workspace_dir: Path, auto_fix: bool = True) -> bool:
    """Check and auto-fix OpenZeppelin installation with version detection"""
    print_bold("\nStep 2: Checking OpenZeppelin Installation")
    
    oz_dir = workspace_dir / "lib" / "openzeppelin-contracts"
    counters_path = oz_dir / "contracts" / "utils" / "Counters.sol"
    erc20_path = oz_dir / "contracts" / "token" / "ERC20" / "ERC20.sol"
    
    # Check if OZ is installed
    if not oz_dir.exists() or not erc20_path.exists():
        print_warning("OpenZeppelin contracts not found")
        if auto_fix:
            print_info("🔧 Auto-installing OpenZeppelin...")
            return install_openzeppelin(workspace_dir)
        else:
            print_error("OpenZeppelin not installed. Run: forge install OpenZeppelin/openzeppelin-contracts")
            return False
    
    # Detect OZ version by checking package.json or git tag
    oz_version = detect_openzeppelin_version(oz_dir)
    print_info(f"OpenZeppelin version detected: {oz_version}")
    
    # Check for Counters.sol (present in v4.x, removed in v5.x)
    if not counters_path.exists():
        print_warning("Counters.sol not found (removed in OpenZeppelin v5.x)")
        
        # Check foundry.toml to see if we need v4 or v5
        foundry_toml = workspace_dir / "foundry.toml"
        solc_version = get_solc_version(foundry_toml)
        
        if auto_fix and oz_version.startswith("5."):
            print_info("🔧 OpenZeppelin v5 detected - Counters.sol is deprecated")
            print_info("💡 Contract generation will auto-remove Counters.sol usage")
            print_success("OpenZeppelin v5 compatible (Counters.sol auto-removed)")
            return True
        elif auto_fix:
            print_info("🔧 Reinstalling OpenZeppelin v4.9.5 (includes Counters.sol)...")
            return install_openzeppelin(workspace_dir, version="v4.9.5")
        else:
            print_error("Counters.sol missing. Install OZ v4.9.5 or update contracts to not use Counters.sol")
            return False
    else:
        print_success("OpenZeppelin & Counters.sol present")
        return True

def detect_openzeppelin_version(oz_dir: Path) -> str:
    """Detect OpenZeppelin version from package.json or git"""
    # Try package.json first
    package_json = oz_dir / "package.json"
    if package_json.exists():
        try:
            import json
            with open(package_json) as f:
                data = json.load(f)
                version = data.get("version", "unknown")
                return version
        except Exception:
            pass
    
    # Try git tag
    try:
        result = run_cmd(["git", "describe", "--tags", "--exact-match"], cwd=oz_dir, check=False)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    
    # Try git branch/commit
    try:
        result = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=oz_dir, check=False)
        if result.returncode == 0:
            branch = result.stdout.strip()
            if branch != "HEAD":
                return branch
    except Exception:
        pass
    
    # Check for v5 indicators (presence of certain files/structure)
    if (oz_dir / "contracts" / "token" / "ERC721" / "ERC721.sol").exists():
        # Check if Counters.sol exists to distinguish v4 vs v5
        if (oz_dir / "contracts" / "utils" / "Counters.sol").exists():
            return "4.x (estimated)"
        else:
            return "5.x (estimated)"
    
    return "unknown"

def get_solc_version(foundry_toml: Path) -> str:
    """Extract Solidity compiler version from foundry.toml"""
    if not foundry_toml.exists():
        return "unknown"
    
    try:
        content = foundry_toml.read_text(encoding="utf-8")
        # Match solc = "0.8.24" or solc_version = "0.8.24"
        match = re.search(r'solc\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
        match = re.search(r'solc_version\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
    except Exception:
        pass
    
    return "unknown"

def install_openzeppelin(workspace_dir: Path, version: Optional[str] = None) -> bool:
    """Install OpenZeppelin contracts with version pinning"""
    oz_dir = workspace_dir / "lib" / "openzeppelin-contracts"
    
    # Clean up existing installation if broken
    if oz_dir.exists():
        try:
            shutil.rmtree(oz_dir)
            print_info("🧹 Cleaned up existing OpenZeppelin installation")
        except Exception as e:
            print_warning(f"Could not remove existing OZ directory: {e}")
    
    # Ensure lib directory exists
    lib_dir = workspace_dir / "lib"
    lib_dir.mkdir(parents=True, exist_ok=True)
    
    # Install OpenZeppelin
    install_cmd = ["forge", "install", "OpenZeppelin/openzeppelin-contracts"]
    if version:
        install_cmd.append(f"@{version}")
    
    try:
        print_info(f"Running: {' '.join(install_cmd)}")
        result = run_cmd(install_cmd, cwd=workspace_dir, check=False)
        
        if result.returncode != 0:
            # Try direct git clone as fallback
            print_warning("forge install failed, trying direct git clone...")
            clone_url = "https://github.com/OpenZeppelin/openzeppelin-contracts.git"
            if version:
                clone_url += f"@{version}"
            
            run_cmd(
                ["git", "clone", "--depth", "1", "--branch", version.replace("v", "") if version else "latest", 
                 "https://github.com/OpenZeppelin/openzeppelin-contracts.git", str(oz_dir)],
                cwd=workspace_dir,
                check=True
            )
        
        # Verify installation
        erc20_path = oz_dir / "contracts" / "token" / "ERC20" / "ERC20.sol"
        if erc20_path.exists():
            print_success("OpenZeppelin installed successfully")
            return True
        else:
            print_error("OpenZeppelin installation verification failed")
            return False
            
    except Exception as e:
        print_error(f"Failed to install OpenZeppelin: {e}")
        print_info("💡 Manual fix: forge install OpenZeppelin/openzeppelin-contracts")
        return False

def check_foundry_config(workspace_dir: Path) -> bool:
    """Check and validate foundry.toml configuration"""
    print_bold("\nStep 3: Checking Foundry Configuration")
    
    foundry_toml = workspace_dir / "foundry.toml"
    
    if not foundry_toml.exists():
        print_error("foundry.toml not found")
        print_info("💡 Create foundry.toml with required configuration")
        return False
    
    solc_version = get_solc_version(foundry_toml)
    
    # Check for OZ v5 compatibility
    expected_solc = "0.8.24"
    if solc_version != expected_solc:
        print_warning(f"Solc version mismatch: found {solc_version}, expected {expected_solc}")
        print_info(f"💡 Update foundry.toml: solc = \"{expected_solc}\"")
        
        # Auto-fix if possible
        try:
            content = foundry_toml.read_text(encoding="utf-8")
            # Replace solc version
            updated = re.sub(
                r'solc\s*=\s*["\'][^"\']+["\']',
                f'solc = "{expected_solc}"',
                content
            )
            if updated != content:
                foundry_toml.write_text(updated, encoding="utf-8")
                print_success(f"✅ Auto-updated foundry.toml: solc = \"{expected_solc}\"")
                return True
        except Exception as e:
            print_warning(f"Could not auto-update foundry.toml: {e}")
        
        return False
    else:
        print_success(f"Foundry config valid: solc = {solc_version}")
        return True

def check_git_submodule_issues(workspace_dir: Path) -> bool:
    """Check and fix git submodule issues"""
    print_bold("\nStep 4: Checking Git Submodule Configuration")
    
    root_repo = workspace_dir.parent if workspace_dir.name == "hyperkit-agent" else workspace_dir
    
    # Check for broken .gitmodules entries
    gitmodules = root_repo / ".gitmodules"
    if gitmodules.exists():
        try:
            content = gitmodules.read_text(encoding="utf-8")
            if "hyperkit-agent/lib/openzeppelin-contracts" in content:
                print_warning("Found broken submodule entry in root .gitmodules")
                print_info("🔧 Removing broken submodule entry...")
                gitmodules.unlink()
                print_success("✅ Cleaned up root .gitmodules")
        except Exception as e:
            print_warning(f"Could not check .gitmodules: {e}")
    
    # Check .git/config for broken submodule entries
    git_config = root_repo / ".git" / "config"
    if git_config.exists():
        try:
            content = git_config.read_text(encoding="utf-8")
            if "hyperkit-agent/lib/openzeppelin-contracts" in content:
                print_warning("Found broken submodule entry in .git/config")
                print_info("💡 Manual fix: Remove submodule section from .git/config")
        except Exception:
            pass
    
    print_success("Git submodule configuration clean")
    return True

def doctor(workspace_dir: Optional[Path] = None, auto_fix: bool = True) -> bool:
    """
    Run comprehensive doctor/preflight checks with auto-repair.
    
    Returns:
        True if all checks pass, False otherwise
    """
    if workspace_dir is None:
        # Find workspace directory
        script_dir = Path(__file__).parent
        workspace_dir = script_dir.parent
    
    print_bold("=" * 60)
    print_bold("HyperKit-Agent Doctor: Environment Preflight & Self-Healing")
    print_bold("=" * 60)
    
    all_checks_passed = True
    
    try:
        # Step 1: Required tools
        tools_status = check_required_tools()
        if not all(tool[0] for tool in tools_status.values()):
            return False
        
        # Step 2: OpenZeppelin installation
        if not check_openzeppelin_installation(workspace_dir, auto_fix=auto_fix):
            all_checks_passed = False
        
        # Step 3: Foundry configuration
        if not check_foundry_config(workspace_dir):
            all_checks_passed = False
        
        # Step 4: Git submodule issues
        check_git_submodule_issues(workspace_dir)
        
        # Final summary
        print_bold("\n" + "=" * 60)
        if all_checks_passed:
            print_success("✅ All preflight checks passed. System is ready!")
            return True
        else:
            print_error("❌ Some checks failed. Please review errors above.")
            print_info("💡 Run with --fix to attempt automatic repairs")
            return False
            
    except KeyboardInterrupt:
        print_error("\n\nDoctor preflight interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error in doctor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="HyperKit-Agent Doctor: Preflight & Self-Healing")
    parser.add_argument("--no-fix", action="store_true", help="Disable automatic fixes")
    parser.add_argument("--workspace", type=str, help="Workspace directory path")
    
    args = parser.parse_args()
    
    workspace = Path(args.workspace) if args.workspace else None
    auto_fix = not args.no_fix
    
    success = doctor(workspace_dir=workspace, auto_fix=auto_fix)
    sys.exit(0 if success else 1)

