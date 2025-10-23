#!/usr/bin/env python3
"""
Pre-commit Installation Script
Installs and configures pre-commit hooks for HyperKit Agent
Follows .cursor/rules for production-ready implementation
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9 or higher is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_precommit():
    """Install pre-commit package."""
    commands = [
        "pip install pre-commit",
        "pre-commit --version"
    ]
    
    for command in commands:
        if not run_command(command, f"Running: {command}"):
            return False
    return True

def install_precommit_hooks():
    """Install pre-commit hooks."""
    commands = [
        "pre-commit install",
        "pre-commit install --hook-type pre-push",
        "pre-commit install --hook-type commit-msg"
    ]
    
    for command in commands:
        if not run_command(command, f"Running: {command}"):
            return False
    return True

def install_additional_dependencies():
    """Install additional dependencies for pre-commit hooks."""
    dependencies = [
        "black",
        "isort", 
        "flake8",
        "mypy",
        "bandit",
        "safety",
        "pydocstyle",
        "pylint",
        "pytest",
        "pytest-cov"
    ]
    
    for dep in dependencies:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            return False
    return True

def install_solidity_tools():
    """Install Solidity development tools."""
    if platform.system() == "Windows":
        print("⚠️  Solidity tools installation on Windows requires manual setup")
        print("Please install Foundry and Slither manually:")
        print("1. Install Foundry: https://book.getfoundry.sh/getting-started/installation")
        print("2. Install Slither: pip install slither-analyzer")
        return True
    else:
        commands = [
            "curl -L https://foundry.paradigm.xyz | bash",
            "source ~/.bashrc && foundryup",
            "pip install slither-analyzer"
        ]
        
        for command in commands:
            if not run_command(command, f"Running: {command}"):
                return False
        return True

def validate_configuration():
    """Validate pre-commit configuration."""
    config_file = Path(".pre-commit-config.yaml")
    if not config_file.exists():
        print("❌ .pre-commit-config.yaml not found")
        return False
    
    print("✅ Pre-commit configuration file found")
    return True

def run_precommit_test():
    """Run pre-commit on all files to test configuration."""
    commands = [
        "pre-commit run --all-files --verbose"
    ]
    
    for command in commands:
        if not run_command(command, f"Running: {command}"):
            print("⚠️  Some pre-commit hooks failed. This is normal for the first run.")
            print("Please fix the issues and run 'pre-commit run --all-files' again")
            return False
    return True

def create_gitignore_entries():
    """Add pre-commit related entries to .gitignore."""
    gitignore_entries = [
        "",
        "# Pre-commit",
        ".pre-commit-cache/",
        "bandit-report.json",
        "safety-report.json",
        "coverage.xml",
        "htmlcov/",
        ".coverage",
        ".mypy_cache/",
        ".pytest_cache/",
        ".ruff_cache/"
    ]
    
    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            content = f.read()
        
        for entry in gitignore_entries:
            if entry not in content:
                content += entry + "\n"
        
        with open(gitignore_path, "w") as f:
            f.write(content)
        
        print("✅ Updated .gitignore with pre-commit entries")
    else:
        print("⚠️  .gitignore not found, creating one...")
        with open(gitignore_path, "w") as f:
            f.write("\n".join(gitignore_entries))
        print("✅ Created .gitignore with pre-commit entries")

def main():
    """Main installation function."""
    print("🚀 Installing Pre-commit Hooks for HyperKit Agent")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Validate configuration
    if not validate_configuration():
        sys.exit(1)
    
    # Install pre-commit
    if not install_precommit():
        print("❌ Failed to install pre-commit")
        sys.exit(1)
    
    # Install additional dependencies
    if not install_additional_dependencies():
        print("❌ Failed to install additional dependencies")
        sys.exit(1)
    
    # Install Solidity tools
    if not install_solidity_tools():
        print("❌ Failed to install Solidity tools")
        sys.exit(1)
    
    # Install pre-commit hooks
    if not install_precommit_hooks():
        print("❌ Failed to install pre-commit hooks")
        sys.exit(1)
    
    # Create gitignore entries
    create_gitignore_entries()
    
    # Test configuration
    print("\n🧪 Testing pre-commit configuration...")
    if not run_precommit_test():
        print("⚠️  Pre-commit test completed with warnings")
    
    print("\n🎉 Pre-commit installation completed successfully!")
    print("\n📋 Next steps:")
    print("1. Run 'pre-commit run --all-files' to check all files")
    print("2. Run 'pre-commit run --all-files --hook-stage manual' for manual checks")
    print("3. Run 'pre-commit run --all-files --hook-stage pre-push' for pre-push checks")
    print("4. Run 'pre-commit run --all-files --hook-stage commit-msg' for commit message checks")
    print("\n🔧 Available commands:")
    print("- pre-commit run --all-files")
    print("- pre-commit run --all-files --verbose")
    print("- pre-commit run --all-files --hook-stage manual")
    print("- pre-commit run --all-files --hook-stage pre-push")
    print("- pre-commit run --all-files --hook-stage commit-msg")
    print("- pre-commit run --all-files --hook-stage pre-commit")
    print("\n📚 Documentation:")
    print("- https://pre-commit.com/")
    print("- https://pre-commit.com/hooks.html")
    print("- https://pre-commit.com/hooks.html#local-hooks")

if __name__ == "__main__":
    main()
