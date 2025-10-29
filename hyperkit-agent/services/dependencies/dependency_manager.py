"""
Dependency Management Service
Automatically detects and installs dependencies for contracts, tools, and libraries.
Self-healing: No manual dependency installation required.
"""

import re
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Dependency:
    """Represents a dependency requirement"""
    name: str
    source_type: str  # 'solidity', 'npm', 'python'
    install_command: Optional[str] = None
    install_path: Optional[Path] = None
    version: Optional[str] = None
    detected_from: Optional[str] = None  # Which file/import detected this


class DependencyManager:
    """
    Self-healing dependency manager for HyperKit Agent.
    Automatically detects and installs all required dependencies.
    """
    
    def __init__(self, workspace_dir: Path, temp_dir: Optional[Path] = None):
        """
        Initialize dependency manager.
        
        Args:
            workspace_dir: Base workspace directory (hyperkit-agent/)
            temp_dir: Temporary directory for isolated installs (optional)
        """
        self.workspace_dir = Path(workspace_dir)
        self.temp_dir = temp_dir or self.workspace_dir / ".temp_deps"
        self.temp_dir.mkdir(exist_ok=True, parents=True)
        
        self.foundry_project_dir = self.workspace_dir
        self.foundry_lib_dir = self.foundry_project_dir / "lib"
        
        # Track installed dependencies
        self.installed_solidity: Set[str] = set()
        self.installed_npm: Set[str] = set()
        self.installed_python: Set[str] = set()
        
        logger.info(f"DependencyManager initialized - workspace: {self.workspace_dir}")
    
    def detect_dependencies(self, contract_code: str, file_path: Optional[str] = None) -> List[Dependency]:
        """
        Detect all dependencies from contract code, JavaScript, or Python files.
        
        Args:
            contract_code: Code content to analyze
            file_path: Optional file path for context
            
        Returns:
            List of detected dependencies
        """
        dependencies: List[Dependency] = []
        
        # Detect Solidity dependencies
        solidity_deps = self._detect_solidity_dependencies(contract_code, file_path)
        dependencies.extend(solidity_deps)
        
        # Detect npm/JavaScript dependencies (if any JS code in file)
        if file_path and (file_path.endswith('.js') or file_path.endswith('.ts')):
            npm_deps = self._detect_npm_dependencies(contract_code, file_path)
            dependencies.extend(npm_deps)
        
        # Detect Python dependencies
        if file_path and file_path.endswith('.py'):
            python_deps = self._detect_python_dependencies(contract_code, file_path)
            dependencies.extend(python_deps)
        
        logger.info(f"Detected {len(dependencies)} dependencies from {file_path or 'code'}")
        return dependencies
    
    def _detect_solidity_dependencies(self, code: str, file_path: Optional[str]) -> List[Dependency]:
        """Detect Solidity import dependencies"""
        deps: List[Dependency] = []
        
        # Pattern for Solidity imports
        # import "@openzeppelin/contracts/...";
        # import "lib/...";
        # import "./...";
        import_pattern = r'import\s+["\']([^"\']+)["\']'
        
        imports = re.findall(import_pattern, code)
        
        for import_path in imports:
            # Skip local relative imports
            if import_path.startswith('./') or import_path.startswith('../'):
                continue
            
            # OpenZeppelin and other external contracts
            if '@openzeppelin' in import_path:
                # Extract contract path: @openzeppelin/contracts/access/Ownable.sol
                # Dependency is: openzeppelin-contracts
                dep = Dependency(
                    name="OpenZeppelin/openzeppelin-contracts",
                    source_type="solidity",
                    install_command="forge install OpenZeppelin/openzeppelin-contracts --no-commit",
                    install_path=self.foundry_lib_dir / "openzeppelin-contracts",
                    detected_from=file_path or "contract"
                )
                deps.append(dep)
            
            # Other forge/lib dependencies
            elif import_path.startswith('lib/'):
                # lib/dependency-name/contracts/...
                parts = import_path.split('/')
                if len(parts) >= 2:
                    lib_name = parts[1]
                    # Try to detect if it's a GitHub repo
                    # For now, we'll need to track common ones or infer from lib structure
                    dep = Dependency(
                        name=f"lib/{lib_name}",
                        source_type="solidity",
                        install_path=self.foundry_lib_dir / lib_name,
                        detected_from=file_path or "contract"
                    )
                    deps.append(dep)
        
        return deps
    
    def _detect_npm_dependencies(self, code: str, file_path: Optional[str]) -> List[Dependency]:
        """Detect npm/JavaScript dependencies"""
        deps: List[Dependency] = []
        
        # Pattern for require/import
        require_pattern = r"(?:require|import).+['\"]([@]?[a-zA-Z0-9\-_/]+)['\"]"
        matches = re.findall(require_pattern, code)
        
        for match in matches:
            # Skip built-ins and relative imports
            if match.startswith('.') or match.startswith('/'):
                continue
            
            # Check if it's already in package.json
            # For now, add common ones or parse package.json
            dep = Dependency(
                name=match,
                source_type="npm",
                install_command=f"npm install {match}",
                detected_from=file_path or "javascript"
            )
            deps.append(dep)
        
        return deps
    
    def _detect_python_dependencies(self, code: str, file_path: Optional[str]) -> List[Dependency]:
        """Detect Python import dependencies"""
        deps: List[Dependency] = []
        
        # Pattern for Python imports
        import_pattern = r'^(?:from\s+|import\s+)([a-zA-Z0-9_]+)'
        lines = code.split('\n')
        
        for line in lines:
            match = re.match(import_pattern, line.strip())
            if match:
                module_name = match.group(1)
                # Skip stdlib modules
                if module_name not in ['os', 'sys', 'json', 'pathlib', 'typing', 'logging', 'asyncio']:
                    dep = Dependency(
                        name=module_name,
                        source_type="python",
                        install_command=f"pip install {module_name}",
                        detected_from=file_path or "python"
                    )
                    deps.append(dep)
        
        return deps
    
    async def install_dependency(self, dep: Dependency, retry_count: int = 2) -> Tuple[bool, str]:
        """
        Install a single dependency with retry logic.
        
        Args:
            dep: Dependency to install
            retry_count: Number of retry attempts
            
        Returns:
            Tuple of (success, message)
        """
        if dep.source_type == "solidity":
            return await self._install_solidity_dependency(dep, retry_count)
        elif dep.source_type == "npm":
            return await self._install_npm_dependency(dep, retry_count)
        elif dep.source_type == "python":
            return await self._install_python_dependency(dep, retry_count)
        else:
            return False, f"Unknown dependency type: {dep.source_type}"
    
    async def _install_solidity_dependency(self, dep: Dependency, retry_count: int) -> Tuple[bool, str]:
        """Install Solidity dependency using forge install"""
        # Check if already installed
        if dep.name in self.installed_solidity:
            logger.info(f"✅ Solidity dependency already installed: {dep.name}")
            return True, f"Already installed: {dep.name}"
        
        if dep.install_path and dep.install_path.exists():
            # Verify it has contracts
            contracts_dir = dep.install_path / "contracts"
            if contracts_dir.exists() and any(contracts_dir.rglob("*.sol")):
                logger.info(f"✅ Solidity dependency verified: {dep.name}")
                self.installed_solidity.add(dep.name)
                return True, f"Already installed: {dep.name}"
        
        # Check if forge is available
        try:
            result = subprocess.run(['forge', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False, "Forge not found - please install Foundry"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False, "Forge not found - please install Foundry"
        
        # Install using forge install
        if dep.install_command:
            logger.info(f"📦 Installing Solidity dependency: {dep.name}")
            
            for attempt in range(retry_count + 1):
                try:
                    # Extract repo from name (e.g., "OpenZeppelin/openzeppelin-contracts")
                    if '/' in dep.name:
                        repo_name = dep.name
                    else:
                        repo_name = dep.name  # Fallback
                    
                    # Run forge install
                    cmd = ['forge', 'install', repo_name, '--no-commit']
                    result = subprocess.run(
                        cmd,
                        cwd=self.foundry_project_dir,
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    
                    if result.returncode == 0 or "already installed" in result.stdout.lower():
                        # Verify installation
                        if dep.install_path:
                            contracts_dir = dep.install_path / "contracts"
                            if contracts_dir.exists() and any(contracts_dir.rglob("*.sol")):
                                logger.info(f"✅ Successfully installed: {dep.name}")
                                self.installed_solidity.add(dep.name)
                                return True, f"Installed: {dep.name}"
                        
                        # If install_path not specified, check lib/ directory
                        lib_name = repo_name.split('/')[-1]
                        lib_path = self.foundry_lib_dir / lib_name
                        if lib_path.exists():
                            logger.info(f"✅ Successfully installed: {dep.name}")
                            self.installed_solidity.add(dep.name)
                            return True, f"Installed: {dep.name}"
                    
                    if attempt < retry_count:
                        logger.warning(f"⚠️ Install attempt {attempt + 1} failed, retrying...")
                        continue
                    else:
                        return False, f"Failed to install {dep.name}: {result.stderr}"
                        
                except subprocess.TimeoutExpired:
                    return False, f"Installation timeout for {dep.name}"
                except Exception as e:
                    if attempt < retry_count:
                        logger.warning(f"⚠️ Install attempt {attempt + 1} failed: {e}, retrying...")
                        continue
                    else:
                        return False, f"Installation error: {str(e)}"
            
            return False, f"Failed to install {dep.name} after {retry_count + 1} attempts"
        else:
            return False, f"No install command for {dep.name}"
    
    async def _install_npm_dependency(self, dep: Dependency, retry_count: int) -> Tuple[bool, str]:
        """Install npm dependency"""
        if dep.name in self.installed_npm:
            return True, f"Already installed: {dep.name}"
        
        # Check npm
        try:
            subprocess.run(['npm', '--version'], capture_output=True, check=True, timeout=10)
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            return False, "npm not found - please install Node.js"
        
        logger.info(f"📦 Installing npm dependency: {dep.name}")
        
        for attempt in range(retry_count + 1):
            try:
                cmd = ['npm', 'install', dep.name]
                result = subprocess.run(
                    cmd,
                    cwd=self.workspace_dir,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    self.installed_npm.add(dep.name)
                    return True, f"Installed: {dep.name}"
                
                if attempt < retry_count:
                    continue
                else:
                    return False, f"Failed: {result.stderr}"
                    
            except Exception as e:
                if attempt < retry_count:
                    continue
                else:
                    return False, f"Error: {str(e)}"
        
        return False, f"Failed after {retry_count + 1} attempts"
    
    async def _install_python_dependency(self, dep: Dependency, retry_count: int) -> Tuple[bool, str]:
        """Install Python dependency"""
        if dep.name in self.installed_python:
            return True, f"Already installed: {dep.name}"
        
        # Check pip
        try:
            subprocess.run(['pip', '--version'], capture_output=True, check=True, timeout=10)
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            return False, "pip not found - please install Python"
        
        logger.info(f"📦 Installing Python dependency: {dep.name}")
        
        for attempt in range(retry_count + 1):
            try:
                cmd = ['pip', 'install', dep.name]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    self.installed_python.add(dep.name)
                    return True, f"Installed: {dep.name}"
                
                if attempt < retry_count:
                    continue
                else:
                    return False, f"Failed: {result.stderr}"
                    
            except Exception as e:
                if attempt < retry_count:
                    continue
                else:
                    return False, f"Error: {str(e)}"
        
        return False, f"Failed after {retry_count + 1} attempts"
    
    async def install_all_dependencies(self, dependencies: List[Dependency]) -> Dict[str, Tuple[bool, str]]:
        """
        Install all dependencies with parallel execution where possible.
        
        Args:
            dependencies: List of dependencies to install
            
        Returns:
            Dictionary mapping dependency names to (success, message) tuples
        """
        results: Dict[str, Tuple[bool, str]] = {}
        
        logger.info(f"📦 Installing {len(dependencies)} dependencies...")
        
        # Group by type for better logging
        solidity_deps = [d for d in dependencies if d.source_type == "solidity"]
        npm_deps = [d for d in dependencies if d.source_type == "npm"]
        python_deps = [d for d in dependencies if d.source_type == "python"]
        
        # Install sequentially (to avoid conflicts)
        for dep in dependencies:
            success, message = await self.install_dependency(dep)
            results[dep.name] = (success, message)
            
            if not success:
                logger.error(f"❌ Failed to install {dep.name}: {message}")
            else:
                logger.info(f"✅ {message}")
        
        # Summary
        success_count = sum(1 for success, _ in results.values() if success)
        logger.info(f"📦 Dependency installation complete: {success_count}/{len(dependencies)} successful")
        
        return results
    
    def preflight_check(self) -> Dict[str, bool]:
        """
        Perform preflight checks for required system tools.
        
        Returns:
            Dictionary mapping tool names to availability status
        """
        checks: Dict[str, bool] = {}
        
        tools = {
            "forge": ["forge", "--version"],
            "npm": ["npm", "--version"],
            "node": ["node", "--version"],
            "python": ["python", "--version"],
            "pip": ["pip", "--version"],
        }
        
        for tool_name, cmd in tools.items():
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=10
                )
                checks[tool_name] = result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                checks[tool_name] = False
        
        missing = [name for name, available in checks.items() if not available]
        if missing:
            logger.warning(f"⚠️ Missing tools: {', '.join(missing)}")
        else:
            logger.info("✅ All required tools available")
        
        return checks

