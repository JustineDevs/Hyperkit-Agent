"""
Foundry management utilities
Handles Foundry installation and version checking
"""

import subprocess
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class FoundryManager:
    """Manage Foundry installation and updates"""
    
    @staticmethod
    def is_installed() -> bool:
        """Check if Foundry is installed"""
        try:
            result = subprocess.run(
                ["forge", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def get_version() -> str:
        """Get installed Foundry version"""
        try:
            result = subprocess.run(
                ["forge", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except:
            return "unknown"
    
    @staticmethod
    def install() -> bool:
        """Install Foundry"""
        try:
            logger.info("Installing Foundry...")
            
            if os.name == 'posix':  # Linux/Mac
                cmd = "curl -L https://foundry.paradigm.xyz | bash"
                subprocess.run(cmd, shell=True, check=True)
                
                # Run foundryup
                subprocess.run("~/.foundry/bin/foundryup", shell=True)
            
            elif os.name == 'nt':  # Windows
                logger.info("For Windows, please install manually:")
                logger.info("1. Download from https://github.com/foundry-rs/foundry/releases")
                logger.info("2. Add to PATH")
                return False
            
            logger.info("✅ Foundry installed successfully")
            return True
        
        except Exception as e:
            logger.error(f"Installation failed: {e}")
            return False
    
    @staticmethod
    def ensure_installed():
        """Ensure Foundry is installed"""
        if not FoundryManager.is_installed():
            logger.warning("Foundry not installed!")
            logger.info("Version:", FoundryManager.get_version())
            
            if not FoundryManager.install():
                logger.error("Failed to install Foundry")
                raise RuntimeError("Foundry not installed and auto-install failed")
        
        logger.info(f"Foundry ready: {FoundryManager.get_version()}")
