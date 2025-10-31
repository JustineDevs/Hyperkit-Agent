"""
Dependency Management Service
Automatically detects and installs dependencies for contracts, tools, and libraries.
Self-healing: No manual dependency installation required.
"""

import re
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
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
        seen_deps = set()  # Avoid duplicates
        
        # Pattern for Solidity imports
        # import "@openzeppelin/contracts/...";
        # import "lib/...";
        # import "./...";
        import_pattern = r'import\s+["\']([^"\']+)["\']'
        
        imports = re.findall(import_pattern, code)
        
        # Common Solidity library mappings
        COMMON_LIBRARIES = {
            '@openzeppelin/contracts': ('OpenZeppelin/openzeppelin-contracts', 'openzeppelin-contracts'),
            '@openzeppelin/contracts-upgradeable': ('OpenZeppelin/openzeppelin-contracts-upgradeable', 'openzeppelin-contracts-upgradeable'),
            '@chainlink/contracts': ('smartcontractkit/chainlink', 'chainlink'),
            '@uniswap/v3-core': ('Uniswap/v3-core', 'v3-core'),
            '@uniswap/v3-periphery': ('Uniswap/v3-periphery', 'v3-periphery'),
            '@aave/core-v3': ('aave/core-v3', 'aave-core-v3'),
            '@ensdomains/ens': ('ensdomains/ens', 'ens'),
            '@ensdomains/resolver': ('ensdomains/resolver', 'ens-resolver'),
            '@safe-global/safe-contracts': ('safe-global/safe-contracts', 'safe-contracts'),
            '@balancer-labs/v2-core': ('balancer-labs/v2-core', 'balancer-v2-core'),
            '@balancer-labs/v2-vault': ('balancer-labs/v2-vault', 'balancer-v2-vault'),
            '@compound-finance/compound-protocol': ('compound-finance/compound-protocol', 'compound-protocol'),
            '@makerdao/dss': ('makerdao/dss', 'dss'),
            '@gnosis/multisig-wallet': ('gnosis/multisig-wallet', 'multisig-wallet'),
        }
        
        for import_path in imports:
            # Skip local relative imports
            if import_path.startswith('./') or import_path.startswith('../'):
                continue
            
            # Check for common library patterns
            matched = False
            
            # Check @namespace/library patterns
            for pattern, (repo_name, lib_name) in COMMON_LIBRARIES.items():
                if import_path.startswith(pattern):
                    if repo_name not in seen_deps:
                        dep = Dependency(
                            name=repo_name,
                            source_type="solidity",
                            install_command=f"forge install {repo_name} --no-commit",
                            install_path=self.foundry_lib_dir / lib_name,
                            detected_from=file_path or "contract"
                        )
                        deps.append(dep)
                        seen_deps.add(repo_name)
                    matched = True
                    break
            
            if matched:
                continue
            
            # Handle lib/... imports (check if already installed, if not try to infer)
            if import_path.startswith('lib/'):
                parts = import_path.split('/')
                if len(parts) >= 2:
                    lib_name = parts[1]
                    lib_path = self.foundry_lib_dir / lib_name
                    
                    # Check if already installed
                    if lib_path.exists() and (lib_path / "contracts").exists():
                        logger.debug(f"Library {lib_name} already installed at {lib_path}")
                        continue
                    
                    # Try to infer GitHub repo from common patterns
                    # Try common GitHub orgs/repos
                    inferred_repos = [
                        f"{lib_name}/{lib_name}",
                        f"makerdao/{lib_name}",
                        f"dapphub/{lib_name}",
                        f"OpenZeppelin/{lib_name}",
                    ]
                    
                    # Check foundry.toml for remappings that might hint at repo
                    foundry_toml = self.foundry_project_dir / "foundry.toml"
                    if foundry_toml.exists():
                        try:
                            with open(foundry_toml, 'r') as f:
                                toml_content = f.read()
                                # Look for remappings that might contain repo info
                                remapping_pattern = rf'{lib_name}\s*=\s*lib/([^/]+)'
                                remap_match = re.search(remapping_pattern, toml_content)
                                if remap_match:
                                    detected_repo = remap_match.group(1)
                                    inferred_repos.insert(0, detected_repo)
                        except Exception:
                            pass
                    
                    # Add dependencies for inferred repos (will try them in order)
                    if lib_name not in seen_deps:
                        # Create dependency with first inferred repo
                        dep = Dependency(
                            name=inferred_repos[0] if inferred_repos else f"unknown/{lib_name}",
                            source_type="solidity",
                            install_command=f"forge install {inferred_repos[0]} --no-commit" if inferred_repos else None,
                            install_path=self.foundry_lib_dir / lib_name,
                            detected_from=file_path or "contract",
                            version=None  # Could parse version from import if needed
                        )
                        deps.append(dep)
                        seen_deps.add(lib_name)
            
            # Handle direct GitHub repo imports (e.g., "github.com/org/repo/path")
            github_pattern = r'github\.com/([^/]+)/([^/]+)'
            github_match = re.search(github_pattern, import_path)
            if github_match:
                org = github_match.group(1)
                repo = github_match.group(2)
                repo_name = f"{org}/{repo}"
                if repo_name not in seen_deps:
                    dep = Dependency(
                        name=repo_name,
                        source_type="solidity",
                        install_command=f"forge install {repo_name} --no-commit",
                        install_path=self.foundry_lib_dir / repo,
                        detected_from=file_path or "contract"
                    )
                    deps.append(dep)
                    seen_deps.add(repo_name)
        
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
        # CRITICAL: Ensure lib directory exists before installation
        self.foundry_lib_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured lib directory exists: {self.foundry_lib_dir}")
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
        # CRITICAL: Ensure lib directory exists
        self.foundry_lib_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured lib directory exists: {self.foundry_lib_dir}")
        
        # Check if already installed
        if dep.name in self.installed_solidity:
            logger.info(f"✅ Solidity dependency already installed: {dep.name}")
            return True, f"Already installed: {dep.name}"
        
        if dep.install_path and dep.install_path.exists():
            # Verify it has contracts (check multiple possible locations)
            possible_contract_dirs = [
                dep.install_path / "contracts",
                dep.install_path,
                dep.install_path / "src",
            ]
            for contracts_dir in possible_contract_dirs:
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
        if dep.install_command or '/' in dep.name:
            logger.info(f"📦 Installing Solidity dependency: {dep.name}")
            
            for attempt in range(retry_count + 1):
                try:
                    # Extract repo from name (e.g., "OpenZeppelin/openzeppelin-contracts")
                    if '/' in dep.name:
                        repo_name = dep.name
                    else:
                        repo_name = dep.name  # Fallback
                    
                    # Handle broken git submodules first (common issue) - robust handling
                    if 'openzeppelin' in repo_name.lower():
                        lib_name = repo_name.split('/')[-1]
                        lib_path = self.foundry_lib_dir / lib_name
                        
                        # Clean up broken submodule if exists (fail-loud with fixes)
                        try:
                            import shutil
                            
                            # 1. Remove broken submodule reference in .git/modules
                            git_modules_file = self.foundry_project_dir / ".git" / "modules" / f"lib/{lib_name}"
                            if git_modules_file.exists():
                                shutil.rmtree(str(git_modules_file), ignore_errors=True)
                                logger.info(f"🧹 Cleaned up broken git submodule cache: {lib_name}")
                            
                            # 2. Check root repo .gitmodules for broken entries - delete if exists (simplest fix)
                            root_repo_dir = self.foundry_project_dir.parent  # Go up one level to root
                            root_gitmodules = root_repo_dir / ".gitmodules"
                            if root_gitmodules.exists():
                                try:
                                    gitmodules_content = root_gitmodules.read_text(encoding="utf-8")
                                    # Check if there's a broken entry for hyperkit-agent/lib/openzeppelin-contracts
                                    broken_pattern = f"hyperkit-agent/lib/{lib_name}"
                                    if broken_pattern in gitmodules_content:
                                        logger.warning(f"⚠️  Found broken submodule entry in root .gitmodules for {broken_pattern}")
                                        logger.info(f"🗑️  Deleting root .gitmodules (simplest fix)")
                                        root_gitmodules.unlink()
                                        logger.info(f"✅ Deleted root .gitmodules to fix submodule conflict")
                                except Exception as e:
                                    logger.warning(f"⚠️  Could not clean root .gitmodules: {e}")
                            
                            # 2b. Also check and clean .gitignore if it has submodule entries (WRONG LOCATION)
                            root_gitignore = root_repo_dir / ".gitignore"
                            if root_gitignore.exists():
                                try:
                                    gitignore_content = root_gitignore.read_text(encoding="utf-8")
                                    if "[submodule" in gitignore_content and lib_name in gitignore_content:
                                        logger.warning(f"⚠️  Found submodule entries in root .gitignore (WRONG LOCATION)")
                                        logger.info(f"🗑️  Removing submodule entries from .gitignore")
                                        # Remove submodule block from .gitignore
                                        lines = gitignore_content.split('\n')
                                        new_lines = []
                                        skip_submodule = False
                                        for line in lines:
                                            if line.strip().startswith("[submodule"):
                                                skip_submodule = True
                                                continue
                                            if skip_submodule and (line.strip().startswith("#") or (line.strip() and not line.startswith("\t") and not line.startswith(" "))):
                                                skip_submodule = False
                                                if not line.strip().startswith("#"):
                                                    new_lines.append(line)
                                            elif not skip_submodule:
                                                new_lines.append(line)
                                        root_gitignore.write_text('\n'.join(new_lines), encoding="utf-8")
                                        logger.info(f"✅ Removed submodule entries from root .gitignore")
                                except Exception as e:
                                    logger.warning(f"⚠️  Could not clean root .gitignore: {e}")
                            
                            # 2b. Also clean .git/config if it has broken submodule entry
                            root_git_config = root_repo_dir / ".git" / "config"
                            if root_git_config.exists():
                                try:
                                    config_content = root_git_config.read_text(encoding="utf-8")
                                    broken_pattern = f"hyperkit-agent/lib/{lib_name}"
                                    if broken_pattern in config_content:
                                        logger.warning(f"⚠️  Found broken submodule entry in root .git/config for {broken_pattern}")
                                        # Remove the submodule section from config
                                        lines = config_content.split('\n')
                                        new_lines = []
                                        skip_section = False
                                        for line in lines:
                                            if f'[submodule "{broken_pattern}"]' in line:
                                                skip_section = True
                                                continue
                                            if skip_section and (line.strip().startswith('[') or (line.strip() and not line.strip().startswith('\t') and not line.strip().startswith(' '))):
                                                # Next section starts
                                                if line.strip().startswith('['):
                                                    skip_section = False
                                                    new_lines.append(line)
                                                elif line.strip() and not line.strip()[0] in ['\t', ' ']:
                                                    # Non-indented line, new section
                                                    skip_section = False
                                                    new_lines.append(line)
                                                else:
                                                    # Still in submodule section, skip
                                                    continue
                                            if not skip_section:
                                                new_lines.append(line)
                                        
                                        root_git_config.write_text('\n'.join(new_lines), encoding="utf-8")
                                        logger.info(f"✅ Removed broken submodule entry from root .git/config")
                                except Exception as e:
                                    logger.warning(f"⚠️  Could not clean root .git/config: {e}")
                            
                            # 2c. Clean .git/modules entries from both root and project
                            root_git_modules = root_repo_dir / ".git" / "modules" / f"hyperkit-agent/lib/{lib_name}"
                            if root_git_modules.exists():
                                try:
                                    shutil.rmtree(str(root_git_modules), ignore_errors=True)
                                    logger.info(f"🧹 Cleaned up root .git/modules entry: {lib_name}")
                                except Exception as e:
                                    logger.warning(f"⚠️  Could not clean root .git/modules: {e}")
                            
                            # 3. Remove lib directory if it's broken or empty
                            if lib_path.exists():
                                try:
                                    # Check if it's a valid git repo with contracts
                                    contracts_dir = lib_path / "contracts"
                                    has_valid_contracts = contracts_dir.exists() and any(contracts_dir.rglob("*.sol"))
                                    
                                    # Try to verify if it's actually broken via git submodule
                                    test_result = subprocess.run(
                                        ['git', 'submodule', 'status', f'lib/{lib_name}'],
                                        cwd=self.foundry_project_dir,
                                        capture_output=True,
                                        text=True,
                                        timeout=5
                                    )
                                    is_broken_submodule = test_result.returncode != 0 or 'fatal' in test_result.stderr.lower()
                                    
                                    if is_broken_submodule or not has_valid_contracts:
                                        logger.warning(f"⚠️  Removing broken/empty submodule directory: {lib_name}")
                                        shutil.rmtree(str(lib_path), ignore_errors=True)
                                except Exception:
                                    # If git command fails, remove the directory anyway
                                    logger.warning(f"⚠️  Removing potentially broken directory: {lib_name}")
                                    shutil.rmtree(str(lib_path), ignore_errors=True)
                            else:
                                # Even if lib_path doesn't exist, still try deinit to clean git references
                                logger.info(f"🧹 lib/{lib_name} doesn't exist, but cleaning git references anyway")
                            
                            # 4. Also try git submodule deinit from root repo (where .gitmodules is)
                            try:
                                # Try from hyperkit-agent first
                                deinit_result = subprocess.run(
                                    ['git', 'submodule', 'deinit', '-f', f'lib/{lib_name}'],
                                    cwd=self.foundry_project_dir,
                                    capture_output=True,
                                    text=True,
                                    timeout=5
                                )
                                # Also try from root repo with full path
                                if deinit_result.returncode != 0:
                                    root_repo_dir = self.foundry_project_dir.parent
                                    root_deinit_result = subprocess.run(
                                        ['git', 'submodule', 'deinit', '-f', f'hyperkit-agent/lib/{lib_name}'],
                                        cwd=root_repo_dir,
                                        capture_output=True,
                                        text=True,
                                        timeout=5
                                    )
                                    if root_deinit_result.returncode == 0:
                                        logger.info(f"🧹 Ran git submodule deinit from root for {lib_name}")
                                else:
                                    logger.info(f"🧹 Ran git submodule deinit for {lib_name}")
                            except Exception as e:
                                logger.debug(f"git submodule deinit failed (non-fatal): {e}")
                                
                        except Exception as e:
                            logger.warning(f"⚠️  Could not clean up broken submodule: {e}")
                    
                    # Handle version pinning if specified
                    # Note: --no-commit was removed in Foundry 1.4.3, using --commit flag instead if needed
                    install_cmd = ['forge', 'install', repo_name]
                    if dep.version:
                        install_cmd.extend(['--tag', dep.version])
                    
                    # Run forge install
                    result = subprocess.run(
                        install_cmd,
                        cwd=self.foundry_project_dir,
                        capture_output=True,
                        text=True,
                        timeout=180  # Increased timeout for large repos
                    )
                    
                    # If forge install fails due to submodule error, try direct git clone as fallback
                    error_output = result.stderr or result.stdout
                    is_submodule_error = (
                        result.returncode != 0 and 
                        ("submodule" in error_output.lower() or "no submodule mapping" in error_output.lower())
                    )
                    
                    if is_submodule_error:
                        logger.warning(f"⚠️  Forge install failed due to submodule error, trying direct git clone fallback...")
                        try:
                            import shutil
                            # Ensure lib directory exists and is empty
                            if lib_path.exists():
                                logger.info(f"🧹 Removing {lib_path} before direct clone...")
                                shutil.rmtree(str(lib_path), ignore_errors=True)
                            self.foundry_lib_dir.mkdir(parents=True, exist_ok=True)
                            
                            # Direct git clone instead of submodule
                            clone_cmd = ['git', 'clone', f'https://github.com/{repo_name}.git', str(lib_path)]
                            logger.info(f"📦 Cloning {repo_name} directly (bypassing git submodule)...")
                            clone_result = subprocess.run(
                                clone_cmd,
                                cwd=str(self.foundry_project_dir),
                                capture_output=True,
                                text=True,
                                timeout=180
                            )
                            
                            if clone_result.returncode == 0:
                                logger.info(f"✅ Successfully cloned {repo_name} directly (bypassing submodule)")
                                # Verify installation
                                contracts_dir = lib_path / "contracts"
                                has_contracts = False
                                if contracts_dir.exists():
                                    has_contracts = any(contracts_dir.rglob("*.sol"))
                                elif lib_path.exists():
                                    has_contracts = any(lib_path.rglob("*.sol"))
                                
                                if has_contracts:
                                    logger.info(f"✅ Verified: {lib_name} has Solidity contracts")
                                    self.installed_solidity.add(dep.name)
                                    self._update_remappings(lib_name, lib_path)
                                    return True, f"Installed via direct clone: {dep.name}"
                                else:
                                    logger.warning(f"⚠️  Cloned but no contracts found in {lib_path}")
                            else:
                                logger.error(f"❌ Direct clone also failed: {clone_result.stderr[:300]}")
                        except Exception as e:
                            logger.error(f"❌ Fallback clone failed: {e}")
                            import traceback
                            logger.debug(traceback.format_exc())
                    
                    # Check for success (forge install returns 0 even if already installed)
                    if result.returncode == 0 or "already installed" in result.stdout.lower() or "already exists" in result.stdout.lower():
                        # Verify installation
                        lib_name = repo_name.split('/')[-1]
                        lib_path = self.foundry_lib_dir / lib_name
                        
                        # Check if library was installed
                        if lib_path.exists():
                            # Verify it has Solidity files
                            possible_contract_dirs = [
                                lib_path / "contracts",
                                lib_path,
                                lib_path / "src",
                            ]
                            for contracts_dir in possible_contract_dirs:
                                if contracts_dir.exists() and any(contracts_dir.rglob("*.sol")):
                                    logger.info(f"✅ Successfully installed: {dep.name}")
                                    self.installed_solidity.add(dep.name)
                                    
                                    # Update remappings if needed
                                    self._update_remappings(lib_name, lib_path)
                                    
                                    return True, f"Installed: {dep.name}"
                        
                        # If we get here, installation might have succeeded but structure is unexpected
                        logger.warning(f"⚠️ Dependency {dep.name} reported as installed but structure unexpected")
                        # Don't mark as installed - return False so it can try fallback
                        return False, f"Installation reported success but verification failed for {dep.name}"
                    
                    # Check for specific error messages
                    error_output = result.stderr or result.stdout
                    
                    # If submodule error, the fallback clone should have already run above
                    # But if it didn't work, return False to allow retry
                    if "submodule" in error_output.lower() or "no submodule mapping" in error_output.lower():
                        logger.error(f"❌ Submodule error persists after cleanup and fallback: {error_output[:300]}")
                        if attempt < retry_count:
                            logger.warning(f"⚠️ Install attempt {attempt + 1} failed due to submodule error, retrying with more aggressive cleanup...")
                            # More aggressive cleanup on retry
                            if lib_path.exists():
                                import shutil
                                shutil.rmtree(str(lib_path), ignore_errors=True)
                            continue
                        else:
                            return False, f"Submodule error could not be resolved: {error_output[:200]}"
                    
                    if "not found" in error_output.lower() or "does not exist" in error_output.lower():
                        if attempt < retry_count:
                            logger.warning(f"⚠️ Install attempt {attempt + 1} failed: repository not found, retrying...")
                            continue
                        else:
                            return False, f"Repository not found: {repo_name}. Check if it exists on GitHub."
                    
                    if attempt < retry_count:
                        logger.warning(f"⚠️ Install attempt {attempt + 1} failed, retrying...")
                        continue
                    else:
                        return False, f"Failed to install {dep.name}: {error_output}"
                        
                except subprocess.TimeoutExpired:
                    if attempt < retry_count:
                        logger.warning(f"⚠️ Install attempt {attempt + 1} timed out, retrying...")
                        continue
                    else:
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
    
    def _update_remappings(self, lib_name: str, lib_path: Path):
        """Update foundry.toml or remappings.txt with library remapping"""
        try:
            foundry_toml = self.foundry_project_dir / "foundry.toml"
            remappings_file = self.foundry_project_dir / "remappings.txt"
            
            # Determine remapping prefix (try common patterns)
            remapping_prefixes = [
                lib_name,
                lib_name.replace('-', '_'),
                lib_name.split('/')[-1] if '/' in lib_name else lib_name,
            ]
            
            # Find contracts directory
            contracts_dir = lib_path / "contracts"
            if not contracts_dir.exists():
                contracts_dir = lib_path / "src"
            if not contracts_dir.exists():
                contracts_dir = lib_path
            
            remapping_needed = False
            
            # Check foundry.toml
            if foundry_toml.exists():
                try:
                    with open(foundry_toml, 'r') as f:
                        content = f.read()
                    
                    # Check if remapping already exists
                    for prefix in remapping_prefixes:
                        if f'{prefix}=' in content or f'"{prefix}=' in content:
                            return  # Already mapped
                    
                    # Add remapping if not present
                    remapping_needed = True
                except Exception:
                    pass
            
            # Check remappings.txt
            if remappings_file.exists():
                try:
                    with open(remappings_file, 'r') as f:
                        content = f.read()
                    
                    for prefix in remapping_prefixes:
                        if f'{prefix}=' in content:
                            return  # Already mapped
                    remapping_needed = True
                except Exception:
                    pass
            
            # Add remapping if needed (prefer remappings.txt)
            if remapping_needed and contracts_dir.exists():
                remapping_line = f"{remapping_prefixes[0]}/={contracts_dir}/\n"
                
                if remappings_file.exists():
                    # Append to remappings.txt
                    with open(remappings_file, 'a') as f:
                        f.write(remapping_line)
                    logger.info(f"✅ Added remapping: {remapping_line.strip()}")
                elif foundry_toml.exists():
                    # Try to add to foundry.toml (requires TOML parsing, so we'll skip for now)
                    logger.debug(f"Remapping needed for {lib_name} but foundry.toml parsing not implemented")
        except Exception as e:
            logger.debug(f"Could not update remappings: {e}")
    
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
    
    def preflight_check(self) -> Dict[str, Any]:
        """
        Perform preflight checks for required system tools per ideal workflow.
        Validates Foundry version, Solidity compiler, and environment tools.
        
        Returns:
            Dictionary mapping tool names to availability status and version info
        """
        checks: Dict[str, Any] = {}
        
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
        
        missing = [name for name, available in checks.items() if isinstance(available, bool) and not available]
        if missing:
            logger.warning(f"⚠️ Missing tools: {', '.join(missing)}")
        else:
            logger.info("✅ All required tools available")
        
        # Per ideal workflow: Log version summary
        if "forge_version" in checks:
            version_info = checks["forge_version"]
            if version_info.get("is_nightly"):
                logger.warning(f"⚠️ Foundry nightly build detected: {version_info.get('version')}")
        
        return checks

