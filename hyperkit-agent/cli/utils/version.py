"""
Version Utilities
Dynamic version information for HyperAgent
"""

import sys
import os
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def get_git_info():
    """Get git information if available"""
    try:
        # Get git commit hash
        commit_hash = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'], 
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        # Get git branch
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        return commit_hash, branch
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None, None

def get_package_version():
    """Get package version from VERSION file or pyproject.toml"""
    try:
        # Try VERSION file in current directory
        version_file = Path("VERSION")
        if version_file.exists():
            return version_file.read_text().strip()
        
        # Try VERSION file in parent directory
        version_file = Path("../VERSION")
        if version_file.exists():
            return version_file.read_text().strip()
    except Exception:
        pass
    
    try:
        # Try pyproject.toml
        pyproject_path = Path("pyproject.toml")
        if pyproject_path.exists():
            import toml
            with open(pyproject_path, 'r') as f:
                data = toml.load(f)
                return data.get('tool', {}).get('poetry', {}).get('version', 'unknown')
    except ImportError:
        pass
    
    # Fallback to hardcoded version
    return "1.4.5"

def get_runtime_features():
    """Get runtime feature status"""
    features = {}
    
    # Check Alith SDK
    try:
        import alith
        features["Alith SDK"] = f"AVAILABLE {getattr(alith, '__version__', 'unknown')}"
    except ImportError:
        features["Alith SDK"] = "NOT INSTALLED"
    
    # Check Foundry
    try:
        result = subprocess.run(['forge', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.split()[1] if len(result.stdout.split()) > 1 else "unknown"
            features["Foundry"] = f"AVAILABLE {version}"
        else:
            features["Foundry"] = "NOT AVAILABLE"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        features["Foundry"] = "NOT INSTALLED"
    
    # Check Web3
    try:
        import web3
        features["Web3.py"] = f"AVAILABLE {web3.__version__}"
    except ImportError:
        features["Web3.py"] = "NOT INSTALLED"
    
    # Check AI providers
    ai_providers = []
    try:
        import openai
        ai_providers.append("OpenAI")
    except ImportError:
        pass
    
    try:
        import google.generativeai
        ai_providers.append("Google")
    except ImportError:
        pass
    
    if ai_providers:
        features["AI Providers"] = f"AVAILABLE {', '.join(ai_providers)}"
    else:
        features["AI Providers"] = "NONE AVAILABLE"
    
    # Check production mode
    try:
        from core.validation.production_validator import ProductionModeValidator
        validator = ProductionModeValidator()
        health_status = validator.validate_production_mode()
        critical_failures = health_status.get('critical_failures', [])
        
        if critical_failures:
            features["Production Mode"] = f"FAILED {len(critical_failures)} critical failures"
        else:
            features["Production Mode"] = "READY"
    except Exception:
        features["Production Mode"] = "UNKNOWN"
    
    return features

def show_version():
    """Display dynamic version information"""
    console.print("HyperAgent Version Information")
    console.print("=" * 50)
    
    # Get version info
    version = get_package_version()
    commit_hash, branch = get_git_info()
    
    # Basic version info
    version_info = {
        "HyperAgent": version,
        "Python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "Platform": f"{sys.platform} {os.name}",
    }
    
    if commit_hash:
        version_info["Git Commit"] = commit_hash
        version_info["Git Branch"] = branch
    
    # Display version info
    for key, value in version_info.items():
        console.print(f"{key}: {value}")
    
    # Runtime features
    console.print("\nRuntime Features:")
    features = get_runtime_features()
    
    for feature, status in features.items():
        console.print(f"  {feature}: {status}")
    
    # System status
    console.print("\nSystem Status:")
    try:
        from core.validation.production_validator import ProductionModeValidator
        validator = ProductionModeValidator()
        health_status = validator.validate_production_mode()
        critical_failures = health_status.get('critical_failures', [])
        
        if critical_failures:
            console.print(f"  CRITICAL FAILURES: {len(critical_failures)}")
            console.print(f"  SYSTEM NOT READY FOR PRODUCTION")
        else:
            console.print(f"  ALL SYSTEMS OPERATIONAL")
    except Exception as e:
        console.print(f"  Status check failed: {e}")
    
    # Build info
    console.print(f"\nBuild Information:")
    console.print(f"  Build Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    console.print(f"  Working Directory: {Path.cwd()}")
    
    # Show if this is a development build
    if commit_hash and branch != 'main':
        console.print(f"\nDEVELOPMENT BUILD")
        console.print(f"  Branch: {branch}")
        console.print(f"  Commit: {commit_hash}")
