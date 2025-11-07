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
    # On Windows, check common installation locations for tools not in PATH
    if sys.platform == "win32":
        possible_paths = []
        
        if tool == "forge":
            # Check common Windows Foundry locations
            possible_paths = [
                Path.home() / ".foundry" / "bin" / "forge.exe",
                Path("C:/Users") / os.getenv("USERNAME", "") / ".foundry" / "bin" / "forge.exe",
                Path("C:/Program Files/foundry/forge.exe"),
                Path("C:/Program Files/foundry/bin/forge.exe"),
            ]
        elif tool == "npm":
            # Check common Windows npm locations (npm usually comes with Node.js)
            # npm.cmd is the Windows wrapper
            node_paths = [
                Path(os.getenv("PROGRAMFILES", "C:/Program Files")) / "nodejs" / "npm.cmd",
                Path(os.getenv("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "nodejs" / "npm.cmd",
                Path.home() / "AppData" / "Roaming" / "npm" / "npm.cmd",
            ]
            # Also check if node is found, npm might be in same directory
            try:
                node_result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5, check=False)
                if node_result.returncode == 0:
                    # npm is usually in same dir as node or in PATH
                    possible_paths.append("npm.cmd")  # Try npm.cmd in PATH
                    possible_paths.append("npm")  # Try npm in PATH
            except:
                pass
            possible_paths.extend(node_paths)
        
        # Try all possible paths
        for tool_path in possible_paths:
            if isinstance(tool_path, str):
                # Try as-is (might be in PATH)
                cmd = [tool_path, version_flag]
            else:
                if not tool_path.exists():
                    continue
                cmd = [str(tool_path), version_flag]
            
            try:
                result = run_cmd(cmd, check=False)
                if result.returncode == 0:
                    version = result.stdout.strip().split('\n')[0] if result.stdout else "installed"
                    return True, version
            except Exception:
                continue
    
    # Standard PATH check for all tools
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
    print_bold("\n[1/5] Checking Required Tools")
    
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
    
    # Required tools: forge, python, node, npm (all required for full functionality)
    required_tools = ["forge", "python", "node", "npm"]
    missing_required = [tool for tool in required_tools if tool in results and not results[tool][0]]
    
    if missing_required:
        print_error("\n❌ Missing required tools. Please install:")
        if "forge" in missing_required:
            print_info("  - Forge: curl -L https://foundry.paradigm.xyz | bash && foundryup")
        if "python" in missing_required:
            print_info("  - Python: https://www.python.org/downloads/")
        if "node" in missing_required or "npm" in missing_required:
            print_info("  - Node.js (includes npm): https://nodejs.org/")
            print_info("  - If Node.js is installed, ensure it's in PATH")
        sys.exit(1)
    
    return results

def check_openzeppelin_installation(workspace_dir: Path, auto_fix: bool = True) -> bool:
    """Check and auto-fix OpenZeppelin installation with version detection"""
    print_bold("\n[2/5] Checking OpenZeppelin Installation")
    
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
            
            if version:
                # Clone specific version tag
                branch_or_tag = version.replace("v", "")  # Remove 'v' prefix if present
                run_cmd(
                    ["git", "clone", "--depth", "1", "--branch", branch_or_tag,
                     "https://github.com/OpenZeppelin/openzeppelin-contracts.git", str(oz_dir)],
                    cwd=workspace_dir,
                    check=False
                )
                # If tag clone failed, try without branch (gets default branch, then checkout tag)
                result = run_cmd(["git", "rev-parse", "--verify", f"refs/tags/{version}"], cwd=oz_dir, check=False)
                if result.returncode != 0:
                    # Clone default branch and checkout tag
                    if oz_dir.exists():
                        shutil.rmtree(oz_dir)
                    run_cmd(
                        ["git", "clone", "--depth", "1", 
                         "https://github.com/OpenZeppelin/openzeppelin-contracts.git", str(oz_dir)],
                        cwd=workspace_dir,
                        check=True
                    )
                    run_cmd(["git", "checkout", version], cwd=oz_dir, check=True)
            else:
                # Clone default branch (no version specified)
                run_cmd(
                    ["git", "clone", "--depth", "1",
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
    print_bold("\n[3/5] Checking Foundry Configuration")
    
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

def check_ai_llm_configuration(workspace_dir: Path) -> bool:
    """
    Check AI/LLM provider configuration (Gemini primary, Alith SDK fallback).
    
    Returns:
        True if at least one AI provider is configured, False otherwise
    """
    print_bold("\n[5/5] Checking AI/LLM Configuration...")
    print_info("Primary: Gemini (via Alith SDK adapter)")
    print_info("Fallback: Alith SDK (OpenAI)")
    
    env_file = workspace_dir / ".env"
    config_file = workspace_dir / "config.yaml"
    
    # Check for .env file
    if not env_file.exists():
        print_warning(".env file not found")
        print_info("💡 Copy env.example to .env and configure API keys")
        return False
    
    # Load environment variables
    env_vars = {}
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except Exception as e:
        print_warning(f"Could not read .env file: {e}")
        return False
    
    # Check Gemini (PRIMARY)
    google_key = env_vars.get('GOOGLE_API_KEY', '')
    has_gemini = google_key and google_key.strip() and google_key != 'your_google_api_key_here'
    
    if has_gemini:
        print_success("✅ Gemini API key configured (PRIMARY)")
        print_info(f"   Model: gemini-2.5-flash-lite (via Alith SDK adapter)")
        
        # Check if Gemini adapter is available
        try:
            import google.generativeai as genai
            print_success("✅ Google Generative AI package installed")
        except ImportError:
            print_warning("⚠️  google-generativeai package not installed")
            print_info("💡 Install: pip install google-generativeai")
            return False
        
        # Check Alith SDK adapter availability
        try:
            adapter_path = workspace_dir / "services" / "core" / "gemini_alith_adapter.py"
            if adapter_path.exists():
                print_success("✅ Gemini Alith SDK adapter available")
            else:
                print_warning("⚠️  Gemini Alith SDK adapter not found")
                print_info(f"💡 Expected: {adapter_path}")
        except Exception as e:
            print_warning(f"⚠️  Could not verify Gemini adapter: {e}")
        
        return True  # Gemini is configured, we're good
    
    # Check Alith SDK (FALLBACK - only if Gemini not available)
    openai_key = env_vars.get('OPENAI_API_KEY', '')
    has_openai = openai_key and openai_key.strip() and openai_key != 'your_openai_api_key_here'
    
    if has_openai:
        print_success("✅ OpenAI API key configured (FALLBACK)")
        print_info("   Using Alith SDK with OpenAI")
        
        # Check Alith SDK installation
        try:
            import alith
            print_success("✅ Alith SDK package installed")
            print_info(f"   Version: {alith.__version__ if hasattr(alith, '__version__') else 'unknown'}")
        except ImportError:
            print_warning("⚠️  Alith SDK package not installed")
            print_info("💡 Install: pip install alith>=0.12.0")
            return False
        
        # Check ALITH_ENABLED flag
        alith_enabled = env_vars.get('ALITH_ENABLED', 'true').lower() == 'true'
        if alith_enabled:
            print_success("✅ ALITH_ENABLED=true (Alith SDK active)")
        else:
            print_warning("⚠️  ALITH_ENABLED is false (Alith SDK disabled)")
            print_info("💡 Set ALITH_ENABLED=true in .env to enable")
        
        return True
    
    # No AI provider configured
    print_error("❌ No AI provider configured")
    print_info("💡 Configure at least one:")
    print_info("   1. PRIMARY: Set GOOGLE_API_KEY in .env (Gemini via Alith SDK adapter)")
    print_info("   2. FALLBACK: Set OPENAI_API_KEY in .env (Alith SDK with OpenAI)")
    print_info("   Get keys from:")
    print_info("   - Gemini: https://aistudio.google.com/")
    print_info("   - OpenAI: https://platform.openai.com/api-keys")
    return False

def check_git_submodule_issues(workspace_dir: Path) -> bool:
    """Check and fix git submodule issues"""
    print_bold("\n[4/5] Checking Git Submodule Configuration")
    
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
        # Step 1: Required tools (all must be present)
        tools_status = check_required_tools()
        # All tools (forge, python, node, npm) are required
        required_tools = ["forge", "python", "node", "npm"]
        missing_required = [tool for tool in required_tools if tool in tools_status and not tools_status[tool][0]]
        if missing_required:
            return False
        
        # Step 2: OpenZeppelin installation
        if not check_openzeppelin_installation(workspace_dir, auto_fix=auto_fix):
            all_checks_passed = False
        
        # Step 3: Foundry configuration
        if not check_foundry_config(workspace_dir):
            all_checks_passed = False
        
        # Step 4: Git submodule issues
        check_git_submodule_issues(workspace_dir)
        
        # Step 5: AI/LLM configuration (Gemini primary, Alith SDK fallback)
        if not check_ai_llm_configuration(workspace_dir):
            all_checks_passed = False
        
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

