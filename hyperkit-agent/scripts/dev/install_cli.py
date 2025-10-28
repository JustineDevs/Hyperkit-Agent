#!/usr/bin/env python3
"""
Installation script for HyperKit AI Agent CLI
This script installs the hyperagent command globally
"""

import subprocess
import sys
import os
from pathlib import Path

def install_hyperagent():
    """Install the hyperagent CLI command."""
    print("🚀 Installing HyperKit AI Agent CLI...")
    
    try:
        # Get the current directory (where this script is located)
        current_dir = Path(__file__).parent
        
        # Install in development mode
        print("📦 Installing in development mode...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-e", str(current_dir)
        ], check=True, capture_output=True, text=True)
        
        print("✅ HyperKit AI Agent CLI installed successfully!")
        print("\n🎉 You can now use the 'hyperagent' command from anywhere!")
        print("\n📖 Quick start:")
        print("  hyperagent --help")
        print("  hyperagent interactive")
        print("  hyperagent test")
        print("  hyperagent status")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def uninstall_hyperagent():
    """Uninstall the hyperagent CLI command."""
    print("🗑️ Uninstalling HyperKit AI Agent CLI...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "uninstall", "hyperkit-agent", "-y"
        ], check=True, capture_output=True, text=True)
        
        print("✅ HyperKit AI Agent CLI uninstalled successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Uninstallation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_installation():
    """Check if hyperagent is installed and working."""
    print("🔍 Checking installation...")
    
    try:
        result = subprocess.run([
            "hyperagent", "--help"
        ], check=True, capture_output=True, text=True)
        
        print("✅ HyperKit AI Agent CLI is working correctly!")
        print("\n📋 Available commands:")
        print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ CLI not working: {e}")
        return False
    except FileNotFoundError:
        print("❌ 'hyperagent' command not found. Please install first.")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="HyperKit AI Agent CLI Installer")
    parser.add_argument("--install", action="store_true", help="Install the CLI")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall the CLI")
    parser.add_argument("--check", action="store_true", help="Check installation")
    
    args = parser.parse_args()
    
    if args.install:
        success = install_hyperagent()
        if success:
            print("\n🔍 Running installation check...")
            check_installation()
    elif args.uninstall:
        uninstall_hyperagent()
    elif args.check:
        check_installation()
    else:
        print("🚀 HyperKit AI Agent CLI Installer")
        print("=" * 50)
        print("Usage:")
        print("  python install_cli.py --install    # Install the CLI")
        print("  python install_cli.py --uninstall  # Uninstall the CLI")
        print("  python install_cli.py --check      # Check installation")
        print("\nOr run without arguments to see this help.")
