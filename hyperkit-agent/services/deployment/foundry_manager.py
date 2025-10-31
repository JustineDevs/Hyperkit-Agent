"""
Foundry management utilities
Handles Foundry installation and version checking
"""

import subprocess
import os
import logging
import platform
import shutil
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class FoundryManager:
    """Manage Foundry installation and updates"""
    
    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        self.forge_path = self._find_forge_path()
        # Pinned version substring (lightweight drift detection)
        # Prefer exact version pinning via config when available
        self.pinned_version_hint = os.getenv("HYPERAGENT_FORGE_VERSION", "forge 1.4.")
        self.version_mismatch: bool = False
    
    def _find_forge_path(self):
        """Find forge executable on system"""
        # Try common locations
        search_paths = [
            Path.home() / ".foundry" / "bin" / "forge",
            Path("C:/Program Files/Foundry/bin/forge.exe"),
            Path("C:/foundry/bin/forge.exe"),
            Path("C:/Users") / os.getenv("USERNAME", "user") / ".foundry" / "bin" / "forge.exe",
        ]
        
        # Check PATH first
        forge_in_path = shutil.which("forge")
        if forge_in_path:
            return Path(forge_in_path)
        
        # Check manual locations
        for path in search_paths:
            if path.exists():
                return path
        
        return None
    
    def is_installed(self) -> bool:
        """Check if Foundry is installed"""
        if self.forge_path and self.forge_path.exists():
            try:
                result = subprocess.run(
                    [str(self.forge_path), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return result.returncode == 0
            except Exception:
                return False
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

    def is_nightly(self) -> bool:
        """Detect nightly builds from version string."""
        try:
            v = (self.get_version() or "").lower()
            return "nightly" in v
        except Exception:
            return False
    
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
    
    def ensure_installed(self):
        """Ensure Foundry is installed"""
        if self.is_installed():
            logger.info(f"✅ Foundry found at: {self.forge_path}")
            # Drift detection
            try:
                current = self.get_version()
                if isinstance(current, str) and self.pinned_version_hint and self.pinned_version_hint not in current:
                    self.version_mismatch = True
                    logger.warning(
                        "⚠️ Foundry version drift detected: current='%s' does not match expected hint '%s'",
                        current,
                        self.pinned_version_hint,
                    )
                    logger.warning(
                        "To pin a specific version, set HYPERAGENT_FORGE_VERSION or install the recommended Foundry release."
                    )
                # Nightly refusal signal (optional strictness)
                if self.is_nightly():
                    logger.warning("⚠️ Foundry nightly build detected: '%s'", current)
            except Exception:
                # Non-fatal; continue
                pass
            return True
        
        logger.warning("❌ Foundry not found")
        
        if self.is_windows:
            logger.error("""
╭──────────────────────────────────────────────────╮
│ ⚠️  Foundry Installation Required (Windows)      │
├──────────────────────────────────────────────────┤
│ 1. Download from:                                │
│    https://github.com/foundry-rs/foundry/releases│
│                                                  │
│ 2. Extract to:                                   │
│    C:\\Program Files\\Foundry\\                   │
│                                                  │
│ 3. Add to PATH:                                  │
│    C:\\Program Files\\Foundry\\bin                │
│                                                  │
│ 4. Restart terminal and verify:                 │
│    forge --version                               │
╰──────────────────────────────────────────────────╯
            """)
            return False
        
        # For Linux/Mac: auto-install
        try:
            logger.info("Installing Foundry...")
            subprocess.run(
                ["curl", "-L", "https://foundry.paradigm.xyz", "|", "bash"],
                shell=True,
                check=True
            )
            subprocess.run(["foundryup"], check=True)
            return True
        except Exception as e:
            logger.error(f"Failed to install Foundry: {e}")
            return False

    def should_refuse_deploy(self) -> bool:
        """Return True if strict mode is enabled and version drift or nightly build detected."""
        try:
            strict = os.getenv("HYPERAGENT_STRICT_FORGE", "0").lower() in ("1", "true", "yes")
            if not strict:
                return False
            # Refuse if version mismatch OR nightly build detected
            return bool(self.version_mismatch) or self.is_nightly()
        except Exception:
            return False
    
    def get_version_status(self) -> Dict[str, Any]:
        """Get comprehensive version status for diagnostics."""
        current_version = self.get_version()
        expected_hint = self.pinned_version_hint
        is_nightly_build = self.is_nightly()
        version_mismatch = self.version_mismatch
        is_installed = self.is_installed()
        
        return {
            "installed": is_installed,
            "current_version": current_version,
            "expected_version_hint": expected_hint,
            "is_nightly": is_nightly_build,
            "version_mismatch": version_mismatch,
            "strict_mode": os.getenv("HYPERAGENT_STRICT_FORGE", "0").lower() in ("1", "true", "yes"),
            "should_refuse": self.should_refuse_deploy(),
            "forge_path": str(self.forge_path) if self.forge_path else None,
        }
