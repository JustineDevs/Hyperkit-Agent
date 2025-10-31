"""
HyperKit AI Agent - Core Implementation
Combines smart contract generation, auditing, and deployment capabilities
"""

import asyncio
import json
import logging
import subprocess
import functools
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
from core.config.loader import get_config
from core.intent_router import IntentRouter, IntentType
from services.debug.edb_integration import EDBIntegration
from services.audit.public_contract_auditor import public_contract_auditor
from services.monitoring.enhanced_monitor import enhanced_monitor, MonitorConfig, MonitorType
from services.defi.primitives_generator import defi_primitives_generator, DeFiPrimitive
from services.core.ai_agent import HyperKitAIAgent
from core.validation.production_validator import enforce_production_mode, is_production_mode

# Security and error handling imports
from core.handlers import safe_operation, handle_workflow_error, validate_input, log_operation, ErrorHandler
from core.security import SecurityManager, InputValidator, AccessController
from core.utils.validation import Validator
from core.errors import (
    ConfigurationError, NetworkError, ContractGenerationError, 
    AuditError, DeploymentError, VerificationError, TestingError,
    ValidationError, SecurityError, WorkflowError
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_operation(operation_name: str):
    """Decorator for safe error handling on all operations (async-aware)"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> dict:
            try:
                logger.info(f"Starting operation: {operation_name}")
                result = await func(*args, **kwargs)
                
                # Ensure result is dict with status
                if not isinstance(result, dict):
                    result = {"status": "success", "data": result}
                
                if "status" not in result:
                    result["status"] = "success"
                
                return result
            
            except KeyError as e:
                logger.error(f"Missing key in {operation_name}: {e}")
                return {
                    "status": "error",
                    "error": f"Missing configuration: {str(e)}",
                    "operation": operation_name
                }
            
            except TypeError as e:
                logger.error(f"Type error in {operation_name}: {e}")
                return {
                    "status": "error",
                    "error": f"Invalid type: {str(e)}",
                    "operation": operation_name
                }
            
            except Exception as e:
                logger.error(f"Error in {operation_name}: {e}", exc_info=True)
                return {
                    "status": "error",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "operation": operation_name
                }
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> dict:
            try:
                logger.info(f"Starting operation: {operation_name}")
                result = func(*args, **kwargs)
                
                # Ensure result is dict with status
                if not isinstance(result, dict):
                    result = {"status": "success", "data": result}
                
                if "status" not in result:
                    result["status"] = "success"
                
                return result
            
            except KeyError as e:
                logger.error(f"Missing key in {operation_name}: {e}")
                return {
                    "status": "error",
                    "error": f"Missing configuration: {str(e)}",
                    "operation": operation_name
                }
            
            except TypeError as e:
                logger.error(f"Type error in {operation_name}: {e}")
                return {
                    "status": "error",
                    "error": f"Invalid type: {str(e)}",
                    "operation": operation_name
                }
            
            except Exception as e:
                logger.error(f"Error in {operation_name}: {e}", exc_info=True)
                return {
                    "status": "error",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "operation": operation_name
                }
        
        # Return async wrapper for async functions, sync for others
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator


class HyperKitAgent:
    """
    Main HyperKit AI Agent that orchestrates smart contract generation,
    auditing, debugging, and deployment workflows.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the HyperKit Agent with configuration."""
        # Use provided config or load from configuration system
        if config:
            self.config = config
        else:
            config_loader = get_config()
            self.config = config_loader.to_dict()

        # Validate configuration - fail hard if critical errors
        from core.config.config_validator import ConfigValidator
        validator = ConfigValidator(self.config)
        validator.fail_if_invalid()  # Raises SystemExit if critical errors

        # Initialize free LLM router
        from core.llm.router import HybridLLMRouter

        self.llm_router = HybridLLMRouter()

        # Initialize Intent Router
        self.intent_router = IntentRouter()
        
        # Initialize IPFS RAG system (replaces Obsidian)
        try:
            from services.rag.ipfs_rag import get_ipfs_rag
            self.rag = get_ipfs_rag(self.config)
            logger.info("IPFS RAG system initialized successfully")
        except Exception as e:
            logger.warning(f"IPFS RAG initialization failed: {e}")
            self.rag = None
        
        # Scaffolder removed - focusing on smart contracts only
        
        # Initialize Alith SDK AI Agent (only AI integration - no LazAI)
        self.ai_agent = HyperKitAIAgent()
        
        # Initialize EDB Integration
        self.edb = EDBIntegration()
        
        # Initialize Security Pipeline (if enabled)
        security_config = self.config.get("security_extensions", {})
        if security_config.get("enabled", False):
            try:
                from services.security import SecurityAnalysisPipeline
                self.security_pipeline = SecurityAnalysisPipeline(security_config)
                logger.info("✅ Security Analysis Pipeline initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize security pipeline: {e}")
                self.security_pipeline = None
        else:
            self.security_pipeline = None
        
        
        # Initialize LangChain agent if available
        self.langchain_agent = None
        if hasattr(self.rag, 'create_langchain_agent'):
            self.langchain_agent = self.rag.create_langchain_agent()

        # Initialize transaction monitor
        from services.monitoring.transaction_monitor import (
            TransactionMonitor,
            MonitoringConfig,
        )

        monitor_config = MonitoringConfig(
            rpc_url=self.config.get("networks", {}).get(
                "hyperion", "https://hyperion-testnet.metisdevops.link"
            ),
            confirmation_blocks=12,
            check_interval=5,
        )
        self.transaction_monitor = TransactionMonitor(monitor_config)

        # Register available tools
        self.tools = {
            "generate": self.generate_contract,
            "audit": self.audit_contract,
            "deploy": self.deploy_contract,
            "debug": self.debug_contract,
            "analyze": self.analyze_contract,
            "optimize": self.optimize_contract,
            "monitor": self.monitor_transaction,
        }

        logger.info("HyperKit Agent initialized successfully")

    @safe_operation("generate_contract")
    async def generate_contract(self, prompt: str, context: str = "") -> Dict[str, Any]:
        """
        Generate a smart contract based on natural language prompt.
        ENFORCES PRODUCTION MODE - no silent fallbacks to mock implementations.
        Uses Alith SDK ONLY - fails hard if Alith unavailable (no fallback).

        Args:
            prompt: Natural language description of the contract
            context: Additional context from RAG system

        Returns:
            Dictionary containing generated contract code and metadata
        """
        # Enforce production mode for contract generation
        enforce_production_mode("Contract Generation")
        
        try:
            # Try Alith SDK AI generation (if configured)
            if self.ai_agent and self.ai_agent.alith_configured:
                try:
                    logger.info("Using Alith SDK for contract generation")
                    requirements = {
                        "prompt": prompt,
                        "context": context,
                        "name": prompt[:50],  # Extract name from prompt
                        "type": "smart_contract"
                    }
                    result = await self.ai_agent.generate_contract(requirements)
                    if result:
                        # Extract contract name and determine category - MUST extract AFTER cleaning
                        from core.tools.utils import extract_contract_info
                        from services.generation.contract_namer import ContractNamer
                        from core.config.paths import PathManager
                        import re
                        
                        # Extract contract name with validation
                        contract_info = extract_contract_info(result)
                        contract_name = contract_info.get("contract_name")
                        
                        # Validate contract name - ensure it's a valid identifier and not from comments
                        if not contract_name or len(contract_name) < 3 or not re.match(r'^[A-Z][a-zA-Z0-9_]*$', contract_name):
                            # Try more robust extraction
                            contract_match = re.search(r'contract\s+([A-Z][a-zA-Z0-9_]+)', result)
                            if contract_match:
                                contract_name = contract_match.group(1)
                            else:
                                # Last resort: use default
                                contract_name = "Contract"
                                logger.warning(f"Could not extract valid contract name, using default: {contract_name}")
                        
                        logger.info(f"📝 Extracted contract name: {contract_name}")
                        
                        # Determine category from prompt or contract code
                        namer = ContractNamer()
                        category = namer.get_category(prompt)  # Get category from prompt
                        
                        # If category couldn't be determined from prompt, infer from contract code
                        if category == "other":
                            category = namer._infer_category_from_code(result)
                        
                        logger.info(f"📁 Determined category: {category}")
                        
                        # Use PathManager for proper organization
                        path_manager = PathManager(command_type="workflow")
                        workflow_dir = path_manager.get_workflow_dir()
                        category_dir = workflow_dir / category
                        category_dir.mkdir(parents=True, exist_ok=True)
                        
                        # PRIMARY: Save to organized location: artifacts/workflows/{category}/
                        organized_file = category_dir / f"{contract_name}.sol"
                        try:
                            organized_file.write_text(result, encoding="utf-8")
                            logger.info(f"✅ Contract saved to organized location: {organized_file}")
                        except Exception as e:
                            logger.error(f"❌ Failed to save to organized location: {e}")
                            raise
                        
                        # SECONDARY: ALSO save to foundry contracts/ directory for compilation
                        from pathlib import Path
                        foundry_project_dir = Path(__file__).parent.parent.parent
                        foundry_contracts_dir = foundry_project_dir / "contracts"
                        foundry_contracts_dir.mkdir(exist_ok=True)
                        
                        foundry_contract_file = foundry_contracts_dir / f"{contract_name}.sol"
                        try:
                            foundry_contract_file.write_text(result, encoding="utf-8")
                            logger.info(f"✅ Contract also saved for Foundry compilation: {foundry_contract_file}")
                        except Exception as e:
                            logger.warning(f"⚠️ Could not save to foundry directory (non-fatal): {e}")
                            # Don't raise - organized location is primary
                        # RAG sanitization: ensure import paths and overrides are consistent
                        try:
                            from services.core.ai_agent import HyperKitAIAgent  # reuse fix helpers if needed
                            # No-op here; generation step already applies sanitization in AI agent
                        except Exception:
                            pass
                        
                        return {
                            "status": "success",
                            "contract_code": result,
                            "contract_name": contract_name,
                            "category": category,
                            "path": str(organized_file),  # Primary path (organized)
                            "foundry_path": str(foundry_contract_file),  # Foundry compilation path
                            "method": "alith",
                            "provider": "Alith SDK",
                            "metadata": {
                                "ai_powered": True,
                                "alith_integration": True,
                                "category": category
                            }
                        }
                except Exception as e:
                    logger.error(f"CRITICAL: Alith SDK generation failed: {e}")
                    # HARD FAIL - NO FALLBACK: Alith SDK is the ONLY AI agent
                    raise RuntimeError(
                        f"CRITICAL: Contract generation failed - Alith SDK unavailable\n"
                        f"  Error: {e}\n"
                        f"  Required: Alith SDK with OpenAI API key\n"
                        f"  Fix: Install alith>=0.12.0 and configure OPENAI_API_KEY\n"
                        f"  NO FALLBACK MODE: System will not silently switch to other providers"
                    )

            # HARD FAIL - No fallback LLM allowed
            logger.error("CRITICAL: Alith SDK not configured and no fallback allowed")
            raise RuntimeError(
                "CRITICAL: Alith SDK is the ONLY AI agent and is not configured\n"
                "  Required: Install alith>=0.12.0 and configure OPENAI_API_KEY\n"
                "  NO FALLBACK: System fails hard if Alith SDK unavailable\n"
                "  Fix: Set ALITH_ENABLED=true and OPENAI_API_KEY in .env"
            )

        except RuntimeError:
            # Re-raise RuntimeErrors (hard fails) - don't catch them
            raise
        except Exception as e:
            logger.error(f"Contract generation failed: {e}")
            from core.handlers import ErrorHandler
            error_handler = ErrorHandler()
            return error_handler.handle_error(e, f"Contract generation failed: {e}")

    @safe_operation("audit_contract")
    async def audit_contract(self, contract_code: str) -> Dict[str, Any]:
        """
        Audit a smart contract using AI-powered analysis.
        Uses Alith SDK for AI auditing - falls back to static analysis tools only.

        Args:
            contract_code: Solidity contract code to audit

        Returns:
            Dictionary containing audit results and severity level
        """
        try:
            # Try Alith SDK AI-powered audit (if configured)
            if self.ai_agent and self.ai_agent.alith_configured:
                try:
                    logger.info("Using Alith SDK for AI-powered contract audit")
                    result = await self.ai_agent.audit_contract(contract_code)
                    if result:
                        return {
                            "status": "success",
                            "results": result,
                            "severity": result.get("severity", "unknown"),
                            "method": "alith",
                            "provider": "Alith SDK",
                            "metadata": {
                                "ai_powered": True,
                                "alith_integration": True
                            }
                        }
                except Exception as e:
                    logger.warning(f"Alith SDK audit failed, falling back to static analysis: {e}")

            # Fallback to existing static analysis implementation
            logger.info("🔍 Using static analysis tools for contract audit")
            from services.audit.auditor import SmartContractAuditor

            auditor = SmartContractAuditor()
            audit_results = await auditor.audit(contract_code)

            return {
                "status": "success",
                "results": audit_results,
                "severity": audit_results.get("severity", "unknown"),
                "method": "static_analysis",
                "provider": "Slither/Mythril",
                "metadata": {
                    "ai_powered": False,
                    "static_analysis": True
                }
            }
        except Exception as e:
            logger.error(f"Contract audit failed: {e}")
            return {"status": "error", "error": str(e), "severity": "critical"}

    async def _compile_contract(self, contract_name: str, contract_code: str) -> Dict[str, Any]:
        """
        Compile contract with Foundry before deployment.
        
        Args:
            contract_name: Name of the contract
            contract_code: Contract source code
            
        Returns:
            Compilation result dictionary
        """
        try:
            import subprocess
            from pathlib import Path
            
            # Determine correct paths: foundry.toml is in hyperkit-agent/, not root
            # Path from core/agent/main.py: .. -> core, .. -> hyperkit-agent (foundry project root)
            foundry_project_dir = Path(__file__).parent.parent.parent
            project_root = foundry_project_dir.parent  # Root of HyperAgent repo
            
            # Contracts are now saved directly to foundry project directory (from generate_contract)
            foundry_contracts_dir = foundry_project_dir / "contracts"
            
            # Foundry project configuration
            lib_dir = foundry_project_dir / "lib"
            openzeppelin_dir = lib_dir / "openzeppelin-contracts"
            foundry_toml = foundry_project_dir / "foundry.toml"
            
            # Verify contract file exists - check multiple locations in priority order
            contract_file = None
            
            # Priority 1: Foundry contracts/ directory (primary location for compilation)
            potential_file = foundry_contracts_dir / f"{contract_name}.sol"
            if potential_file.exists():
                contract_file = potential_file
                logger.debug(f"Contract found in foundry directory: {contract_file}")
            else:
                # Priority 2: Check organized workflows/{category}/ location
                from services.generation.contract_namer import ContractNamer
                from core.config.paths import PathManager
                
                # Try to infer category from code or prompt
                namer = ContractNamer()
                category = namer._infer_category_from_code(contract_code)
                
                path_manager = PathManager(command_type="workflow")
                workflow_dir = path_manager.get_workflow_dir()
                organized_file = workflow_dir / category / f"{contract_name}.sol"
                
                if organized_file.exists():
                    contract_file = organized_file
                    logger.info(f"Contract found in organized location: {contract_file}")
                    # Copy to foundry directory for compilation
                    foundry_contracts_dir.mkdir(exist_ok=True)
                    import shutil
                    foundry_target = foundry_contracts_dir / f"{contract_name}.sol"
                    shutil.copy2(contract_file, foundry_target)
                    contract_file = foundry_target  # Use the foundry location for compilation
                    logger.info(f"Copied to foundry directory for compilation: {contract_file}")
                else:
                    # Priority 3: Check root contracts/ directory (backward compatibility)
                    root_contracts_dir = project_root / "contracts"
                    root_contract_file = root_contracts_dir / f"{contract_name}.sol"
                    if root_contract_file.exists():
                        logger.info(f"Contract found in root directory, copying to foundry project...")
                        foundry_contracts_dir.mkdir(exist_ok=True)
                        import shutil
                        shutil.copy2(root_contract_file, potential_file)
                        contract_file = potential_file
                        logger.info(f"Copied {root_contract_file} to {contract_file}")
            
            # If still not found, return error with all locations checked
            if not contract_file or not contract_file.exists():
                return {
                    "success": False,
                    "error": f"Contract file not found: {contract_name}.sol",
                    "suggestions": [
                        f"Checked foundry directory: {foundry_contracts_dir / f'{contract_name}.sol'}",
                        f"Checked organized workflows location (if category known)",
                        f"Checked root directory: {project_root / 'contracts' / f'{contract_name}.sol'}",
                        "Verify contract generation completed successfully and saved the file",
                        "Check artifacts/workflows/{category}/ for organized location"
                    ],
                    "searched_locations": [
                        str(foundry_contracts_dir),
                        f"artifacts/workflows/{category} (if category determined)",
                        str(project_root / "contracts")
                    ]
                }
            
            logger.info(f"Compiling {contract_name} with Foundry...")
            logger.info(f"Contract file: {contract_file}")
            logger.info(f"Foundry project directory: {foundry_project_dir}")
            
            # Professional dependency management: check if already installed
            needs_openzeppelin = "@openzeppelin" in contract_code
            
            if needs_openzeppelin:
                logger.info(f"Contract requires OpenZeppelin - checking installation...")
                
                # Professional check: verify OpenZeppelin is installed and has contracts
                # Check for contracts/ subdirectory (required for imports)
                contracts_dir = openzeppelin_dir / "contracts"
                
                # More thorough verification: check multiple indicators
                dir_exists = openzeppelin_dir.exists()
                contracts_dir_exists = contracts_dir.exists()
                has_sol_files = False
                has_package_json = False
                
                if contracts_dir_exists:
                    try:
                        sol_files = list(contracts_dir.rglob("*.sol"))
                        has_sol_files = len(sol_files) > 0
                        if has_sol_files:
                            logger.debug(f"   Found {len(sol_files)} Solidity files in OpenZeppelin contracts")
                    except Exception as e:
                        logger.warning(f"   Error checking for .sol files: {e}")
                
                if openzeppelin_dir.exists():
                    package_json = openzeppelin_dir / "package.json"
                    has_package_json = package_json.exists()
                
                openzeppelin_installed = (
                    dir_exists and
                    contracts_dir_exists and
                    has_sol_files  # Must have actual contract files
                )
                
                logger.debug(f"   OpenZeppelin check: dir={dir_exists}, contracts_dir={contracts_dir_exists}, sol_files={has_sol_files}, package_json={has_package_json}")
                
                if openzeppelin_installed:
                    logger.info(f"✅ OpenZeppelin contracts already installed at {openzeppelin_dir}")
                else:
                    logger.warning(f"⚠️  OpenZeppelin not properly installed")
                    logger.info(f"   Attempting installation to {openzeppelin_dir}...")
                    
                    # Verify foundry.toml exists (required for forge install)
                    if not foundry_toml.exists():
                        return {
                            "success": False,
                            "error": f"foundry.toml not found - cannot install dependencies",
                            "suggestions": [
                                f"Initialize Foundry in {foundry_project_dir}: cd hyperkit-agent && forge init",
                                f"Or ensure foundry.toml exists at: {foundry_toml}",
                                "Foundry configuration is required for dependency management"
                            ],
                            "foundry_project_path": str(foundry_project_dir)
                        }
                    
                    # Verify Foundry is installed and accessible
                    try:
                        forge_check = subprocess.run(
                            ["forge", "--version"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if forge_check.returncode != 0:
                            return {
                                "success": False,
                                "error": "Foundry (forge) not found or not working",
                                "suggestions": [
                                    "Install Foundry: curl -L https://foundry.paradigm.xyz | bash",
                                    "Then run: foundryup",
                                    "Verify: forge --version"
                                ]
                            }
                    except FileNotFoundError:
                        return {
                            "success": False,
                            "error": "Foundry (forge) not installed",
                            "suggestions": [
                                "Install Foundry: curl -L https://foundry.paradigm.xyz | bash",
                                "Then run: foundryup",
                                "Verify: forge --version"
                            ]
                        }
                    
                    # Install OpenZeppelin (use foundry project directory as cwd)
                    logger.info(f"Installing OpenZeppelin contracts to {openzeppelin_dir}...")
                    logger.info(f"   Running: forge install OpenZeppelin/openzeppelin-contracts --no-commit")
                    logger.info(f"   Working directory: {foundry_project_dir}")
                    
                    # Ensure lib directory exists
                    lib_dir.mkdir(exist_ok=True)
                    
                    install_result = subprocess.run(
                        ["forge", "install", "OpenZeppelin/openzeppelin-contracts", "--no-commit"],
                        cwd=str(foundry_project_dir),
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    
                    # Log forge output for debugging (show to user at info level for visibility)
                    if install_result.stdout:
                        logger.info(f"Forge install output: {install_result.stdout[:1000]}")
                    if install_result.stderr:
                        logger.info(f"Forge install stderr: {install_result.stderr[:1000]}")
                    
                    # Check installation result - handle already installed case gracefully
                    if install_result.returncode != 0:
                        error_msg = install_result.stderr or install_result.stdout
                        
                        # Check if error is "already installed" - verify it actually exists
                        if "already installed" in error_msg.lower() or "exists" in error_msg.lower():
                            logger.info("⚠️  Forge reports OpenZeppelin already installed - verifying...")
                            # Re-check if it actually exists now
                            contracts_check = openzeppelin_dir / "contracts"
                            if contracts_check.exists() and any(contracts_check.rglob("*.sol")):
                                logger.info("✅ Verified: OpenZeppelin contracts are installed")
                                openzeppelin_installed = True
                            else:
                                logger.warning("⚠️  Forge says installed but files not found - may need git submodule update")
                                # Try to force reinstall
                                logger.info("   Attempting forced reinstall...")
                                # Remove broken submodule first
                                import shutil
                                broken_lib = foundry_project_dir / "lib" / "openzeppelin-contracts"
                                if broken_lib.exists():
                                    try:
                                        shutil.rmtree(str(broken_lib), ignore_errors=True)
                                        logger.info("🧹 Removed broken OpenZeppelin directory before reinstall")
                                    except Exception as e:
                                        logger.warning(f"⚠️  Could not remove broken directory: {e}")
                                
                                # Reinstall without --no-commit (removed in Foundry 1.4.3)
                                force_result = subprocess.run(
                                    ["forge", "install", "OpenZeppelin/openzeppelin-contracts"],
                                    cwd=str(foundry_project_dir),
                                    capture_output=True,
                                    text=True,
                                    timeout=120
                                )
                                if force_result.returncode == 0:
                                    logger.info("✅ Forced reinstall successful")
                                else:
                                    error_msg = force_result.stderr or force_result.stdout
                                    logger.error(f"❌ Forced reinstall failed: {error_msg[:300]}")
                        else:
                            logger.error(f"❌ Dependency installation failed: {error_msg[:500]}")
                            return {
                                "success": False,
                                "error": f"Failed to install OpenZeppelin dependencies: {error_msg[:300]}",
                                "suggestions": [
                                    f"Run manually: cd {foundry_project_dir} && forge install OpenZeppelin/openzeppelin-contracts",
                                    f"If already installed, try: cd {foundry_project_dir} && rm -rf lib/openzeppelin-contracts && forge install OpenZeppelin/openzeppelin-contracts",
                                    f"Check foundry.toml configuration at: {foundry_toml}",
                                    "Verify Foundry is installed: forge --version",
                                    "Check network connectivity for GitHub access",
                                    f"Verify lib/ directory is writable: {lib_dir}",
                                    "Try: git submodule update --init --recursive (if using git)"
                                ],
                                "forge_output": error_msg[:500]
                            }
                    else:
                        logger.info("✅ Forge install command completed successfully")
                    
                    # Verify installation succeeded (re-check after potential install)
                    # Only re-verify if we attempted installation (don't skip if already verified)
                    if not openzeppelin_installed:
                        logger.info("Verifying OpenZeppelin installation...")
                        contracts_dir_check = openzeppelin_dir / "contracts"
                        
                        try:
                            sol_file_count = len(list(contracts_dir_check.rglob("*.sol"))) if contracts_dir_check.exists() else 0
                            openzeppelin_installed_final = (
                                openzeppelin_dir.exists() and
                                contracts_dir_check.exists() and
                                sol_file_count > 0
                            )
                            logger.debug(f"   Verification: dir={openzeppelin_dir.exists()}, contracts={contracts_dir_check.exists()}, files={sol_file_count}")
                        except Exception as e:
                            logger.error(f"   Error during verification: {e}")
                            openzeppelin_installed_final = False
                    else:
                        openzeppelin_installed_final = True
                    
                    if not openzeppelin_installed_final:
                        contracts_dir_check = openzeppelin_dir / "contracts"
                        return {
                            "success": False,
                            "error": f"OpenZeppelin installation completed but verification failed",
                            "suggestions": [
                                f"Check lib/ directory: {lib_dir}",
                                f"Expected OpenZeppelin at: {openzeppelin_dir}",
                                f"Expected contracts at: {contracts_dir_check}",
                                f"Run manually to debug: cd {foundry_project_dir} && forge install OpenZeppelin/openzeppelin-contracts",
                                "Check file system permissions",
                                f"Verify foundry.toml remappings include: @openzeppelin/contracts/=lib/openzeppelin-contracts/contracts/"
                            ],
                            "checked_path": str(openzeppelin_dir),
                            "contracts_path": str(contracts_dir_check)
                        }
                    
                    logger.info(f"✅ OpenZeppelin dependencies installed successfully at {openzeppelin_dir}")
                    logger.debug(f"   Contracts available at: {contracts_dir_check}")
            
            # Contract is already in foundry project directory (contracts/)
            # CRITICAL: Clean stale contracts before compilation to avoid conflicts
            # Keep only the current contract file to ensure compilation succeeds
            if contract_file and contract_file.exists():
                import shutil
                # Backup and remove other .sol files (except the current one)
                for old_file in foundry_contracts_dir.glob("*.sol"):
                    if old_file != contract_file:
                        # Create backup in artifacts/cleanup/ before removing
                        backup_dir = foundry_project_dir / "artifacts" / "cleanup"
                        backup_dir.mkdir(parents=True, exist_ok=True)
                        try:
                            shutil.move(str(old_file), str(backup_dir / old_file.name))
                            logger.info(f"🧹 Moved stale contract to cleanup: {old_file.name}")
                        except Exception as e:
                            logger.warning(f"⚠️ Could not move stale contract {old_file.name}: {e}")
                            # If move fails, try delete as fallback
                            try:
                                old_file.unlink()
                                logger.info(f"🗑️ Deleted stale contract: {old_file.name}")
                            except Exception:
                                pass
            
            # Run forge build from foundry project directory
            logger.info(f"Building contract with Foundry from {foundry_project_dir}...")
            logger.debug(f"   Contract file: {contract_file}")
            logger.debug(f"   Foundry remappings should resolve @openzeppelin/contracts/ to {openzeppelin_dir / 'contracts'}")
            
            # Verify remappings are correct before building
            if needs_openzeppelin and openzeppelin_dir.exists():
                remapping_file = foundry_project_dir / "remappings.txt"
                if remapping_file.exists():
                    logger.debug(f"   Found remappings.txt: {remapping_file}")
                else:
                    logger.debug(f"   Using foundry.toml remappings (remappings.txt not found)")
            
            result = subprocess.run(
                ["forge", "build"],
                cwd=str(foundry_project_dir),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                error_output = result.stderr or result.stdout
                return {
                    "success": False,
                    "error": f"Foundry compilation failed: {error_output[:500]}",
                    "suggestions": [
                        "Check contract syntax errors",
                        "Verify all imports are available",
                        f"Check foundry.toml configuration at: {foundry_toml}",
                        f"Run 'cd {foundry_project_dir} && forge build' manually to see full error",
                        "Verify contract is in contracts/ directory"
                    ],
                    "forge_output": error_output,
                    "foundry_project_path": str(foundry_project_dir)
                }
            
            # Verify artifact was created - check foundry project's out/ directory
            artifact_path = foundry_project_dir / "out" / f"{contract_name}.sol" / f"{contract_name}.json"
            if not artifact_path.exists():
                # Try alternative paths (contract name might vary)
                alternative_paths = [
                    foundry_project_dir / "out" / f"{contract_name}.json",
                    foundry_project_dir / "out" / contract_name / f"{contract_name}.json",
                    # Also check root out/ in case of symlink setup
                    project_root / "out" / f"{contract_name}.sol" / f"{contract_name}.json",
                ]
                for alt_path in alternative_paths:
                    if alt_path.exists():
                        artifact_path = alt_path
                        break
                
            if not artifact_path.exists():
                # List actual artifacts found to help debug
                out_dir = foundry_project_dir / "out"
                found_artifacts = []
                if out_dir.exists():
                    for json_file in out_dir.rglob("*.json"):
                        # Only show contract artifacts, not test artifacts
                        if "Test" not in json_file.name:
                            found_artifacts.append(str(json_file.relative_to(foundry_project_dir)))
                # Also check root out/ as fallback
                root_out_dir = project_root / "out"
                if root_out_dir.exists():
                    for json_file in root_out_dir.rglob("*.json"):
                        if "Test" not in json_file.name:
                            found_artifacts.append(str(json_file.relative_to(project_root)))
                
                error_msg = (
                    f"Artifact not found after compilation\n"
                    f"  Expected: out/{contract_name}.sol/{contract_name}.json\n"
                    f"  Or: out/{contract_name}.json\n"
                    f"  Contract name: {contract_name}"
                )
                
                if found_artifacts:
                    error_msg += f"\n  \n  Actual artifacts found in out/:\n"
                    for artifact in found_artifacts[:10]:  # Show first 10
                        error_msg += f"    - {artifact}\n"
                    if len(found_artifacts) > 10:
                        error_msg += f"    ... and {len(found_artifacts) - 10} more"
                else:
                    error_msg += "\n  No artifacts found in out/ directory"
                
                return {
                    "success": False,
                    "error": error_msg,
                    "expected_path": f"out/{contract_name}.sol/{contract_name}.json",
                    "contract_name": contract_name,
                    "found_artifacts": found_artifacts,
                    "suggestions": [
                        f"Check if contract name in code matches '{contract_name}' exactly",
                        "Verify foundry.toml output configuration",
                        "Check compilation output for errors",
                        "Run 'forge build' manually to see full compilation log",
                        f"Expected artifact paths:\n"
                        f"  - out/{contract_name}.sol/{contract_name}.json\n"
                        f"  - out/{contract_name}.json"
                    ]
                }
            
            logger.info(f"✅ Artifact created at: {artifact_path}")
            
            return {
                "success": True,
                "artifact_path": str(artifact_path),
                "contract_name": contract_name,
                "forge_output": result.stdout
            }
            
        except FileNotFoundError:
            return {
                "success": False,
                "error": "Foundry not installed or not in PATH",
                "suggestions": [
                    "Install Foundry: curl -L https://foundry.paradigm.xyz | bash",
                    "Run: foundryup",
                    "Verify forge is in your PATH"
                ]
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Compilation timed out after 120 seconds",
                "suggestions": [
                    "Contract may be too complex",
                    "Check for infinite loops in constructor",
                    "Verify all dependencies are available"
                ]
            }
        except Exception as e:
            logger.error(f"Compilation error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Compilation failed: {str(e)}",
                "suggestions": [
                    "Check contract code for syntax errors",
                    "Verify Foundry installation",
                    "Check system logs for details"
                ]
            }

    @safe_operation("deploy_contract")
    async def deploy_contract(
        self, contract_code: str, network: str = "hyperion", contract_name: str = None
    ) -> Dict[str, Any]:
        """Deploy contract to blockchain - ENFORCES PRODUCTION MODE"""
        # Enforce production mode for deployment
        enforce_production_mode("Contract Deployment")
        
        try:
            logger.info(f"🚀 Deploy contract: {network}")
            
            # Get network configuration
            if not isinstance(self.config, dict):
                logger.error(f"Config is {type(self.config)}, expected dict")
                return {"status": "error", "error": "Invalid config type"}
            
            networks_config = self.config.get('networks', {})
            if network not in networks_config:
                return {
                    "status": "error",
                    "error": f"Network '{network}' not configured",
                    "available_networks": list(networks_config.keys())
                }
            
            network_config = networks_config[network]
            
            # ✅ Extract ONLY RPC URL as STRING
            rpc_url = network_config.get('rpc_url')
            chain_id = network_config.get('chain_id', 133717)
            
            # Type validation
            if not isinstance(rpc_url, str):
                logger.error(f"RPC URL type: {type(rpc_url)}")
                return {
                    "status": "error",
                    "error": f"RPC URL must be string, got {type(rpc_url).__name__}",
                    "hint": "Check your .env file for HYPERION_RPC_URL"
                }
            
            logger.debug(f"RPC URL: {rpc_url[:40]}..., Chain ID: {chain_id}")
            
            # ✅ Call deployer with correct parameters
            from services.deployment.deployer import MultiChainDeployer
            from services.deployment.foundry_manager import FoundryManager
            from services.deployment.verifier import DeploymentVerifier
            from web3 import Web3
            
            # Initialize deployer (handles Foundry check internally)
            # Refuse deployment if strict Foundry drift or nightly detected
            fm = FoundryManager()
            if fm.should_refuse_deploy():
                current_version = fm.get_version()
                expected_hint = getattr(fm, "pinned_version_hint", "forge 1.4.")
                is_nightly = fm.is_nightly()
                error_msg = (
                    "Foundry version issue detected in strict mode. "
                    f"Current: '{current_version}', Expected hint: '{expected_hint}'. "
                    f"{'Nightly build detected.' if is_nightly else 'Version mismatch.'} "
                    "Refusing to deploy."
                )
                return {
                    "status": "error",
                    "error": error_msg,
                    "details": {
                        "current": current_version,
                        "expected": expected_hint,
                        "is_nightly": is_nightly,
                        "version_mismatch": getattr(fm, "version_mismatch", False)
                    },
                    "recovery_suggestions": [
                        "Run 'hyperagent config foundry-check' for detailed diagnostics",
                        "Install stable Foundry: foundryup (or download from GitHub releases)",
                        "Remove nightly build from PATH: which -a forge",
                        "Set HYPERAGENT_FORGE_VERSION to match your stable version",
                        "Or disable strict mode: export HYPERAGENT_STRICT_FORGE=0 (not recommended)"
                    ]
                }

            deployer = MultiChainDeployer(self.config)
            
            # Get deployer address for constructor args
            deployer_address = self.config.get('default_private_key')
            if deployer_address:
                from eth_account import Account
                account = Account.from_key(deployer_address)
                deployer_address = account.address
            
            # Use provided contract name or extract from code
            if not contract_name:
                import re
                contract_match = re.search(r'contract\s+([A-Z][a-zA-Z0-9_]*)', contract_code)
                contract_name = contract_match.group(1) if contract_match else "Contract"
            
            logger.info(f"Deploying contract: {contract_name}")
            
            result = deployer.deploy(
                contract_code,  # Contract code (STRING)
                rpc_url,       # RPC URL (STRING) ← NOT dict!
                chain_id,      # Chain ID (INT)
                contract_name=contract_name,  # Pass contract name for better arg generation
                deployer_address=deployer_address
            )
            
            if result.get("success"):
                contract_address = result.get("contract_address", "")
                
                # ✅ Post-deployment verification
                try:
                    w3 = Web3(Web3.HTTPProvider(rpc_url))
                    verifier = DeploymentVerifier(w3)
                    
                    verification_result = verifier.verify_contract_deployment(
                        contract_address, 
                        contract_code
                    )
                    
                    if verification_result["success"]:
                        logger.info("✅ Deployment verification passed")
                    else:
                        logger.error("❌ Deployment verification failed")
                        logger.error(f"Verification error: {verification_result.get('error', 'Unknown')}")
                        
                        # Add verification details to result
                        result["verification"] = verification_result
                        
                except Exception as e:
                    logger.warning(f"Post-deployment verification failed: {e}")
                    result["verification"] = {"success": False, "error": str(e)}
                
                return {
                    "status": "deployed",
                    "tx_hash": result.get("transaction_hash", ""),
                    "address": contract_address,
                    "network": network,
                    "block": result.get("block_number", ""),
                    "verification": result.get("verification", {"success": True})
                }
            else:
                return {
                    "status": "error",
                    "error": result.get("error", "Deployment failed"),
                    "recovery_suggestions": result.get("suggestions", [])
                }
        
        except TypeError as te:
            logger.error(f"Type error: {te}")
            return {
                "status": "error",
                "error": f"Type mismatch: {str(te)}",
                "fix": "Verify all parameters are correct types"
            }
        except Exception as e:
            logger.error(f"Deployment error: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    async def debug_contract(self, tx_hash: str, rpc_url: str) -> Dict[str, Any]:
        """
        Debug a transaction using EDB debugger.

        Args:
            tx_hash: Transaction hash to debug
            rpc_url: RPC URL for the network

        Returns:
            Dictionary containing debug results
        """
        try:
            # Integration with EDB debugger
            cmd = f"edb --rpc-urls {rpc_url} replay {tx_hash}"
            result = subprocess.run(cmd.split(), capture_output=True, text=True)

            return {
                "status": "success",
                "debug_output": result.stdout,
                "tx_hash": tx_hash,
                "rpc_url": rpc_url,
            }
        except Exception as e:
            logger.error(f"Contract debugging failed: {e}")
            return {"status": "error", "error": str(e), "tx_hash": tx_hash}

    async def analyze_contract(self, contract_code: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a smart contract.

        Args:
            contract_code: Solidity contract code to analyze

        Returns:
            Dictionary containing analysis results
        """
        try:
            # Perform static analysis
            analysis_results = {
                "gas_estimation": self._estimate_gas(contract_code),
                "complexity_score": self._calculate_complexity(contract_code),
                "security_patterns": self._check_security_patterns(contract_code),
                "best_practices": self._check_best_practices(contract_code),
            }

            return {"status": "success", "analysis": analysis_results}
        except Exception as e:
            logger.error(f"Contract analysis failed: {e}")
            return {"status": "error", "error": str(e)}

    @safe_operation("run_workflow")
    async def run_workflow(
        self, 
        user_prompt: str, 
        network: str = "hyperion",
        auto_verification: bool = True,
        test_only: bool = False,
        allow_insecure: bool = False,
        use_orchestrator: bool = True,
        upload_scope: Optional[str] = None,  # 'team' or 'community'
        rag_scope: str = 'official-only'  # 'official-only' or 'opt-in-community'
    ) -> Dict[str, Any]:
        """
        Execute the complete self-healing workflow with dependency management and auto-recovery.

        Args:
            user_prompt: User's natural language request
            network: Target blockchain network
            auto_verification: Whether to auto-verify contract
            test_only: Whether to run in test-only mode
            allow_insecure: Allow deployment despite audit issues
            use_orchestrator: Use new self-healing orchestrator (default: True)

        Returns:
            Dictionary containing complete workflow results
        """
        # Use new self-healing orchestrator if enabled
        if use_orchestrator:
            try:
                from core.workflow.workflow_orchestrator import WorkflowOrchestrator
                from pathlib import Path
                
                # Get workspace directory
                workspace_dir = Path(__file__).parent.parent.parent
                orchestrator = WorkflowOrchestrator(self, workspace_dir)
                
                logger.info("🚀 Using self-healing workflow orchestrator")
                return await orchestrator.run_complete_workflow(
                    user_prompt=user_prompt,
                    network=network,
                    auto_verification=auto_verification,
                    test_only=test_only,
                    allow_insecure=allow_insecure,
                    upload_scope=upload_scope,
                    rag_scope=rag_scope
                )
            except ImportError as e:
                logger.warning(f"Orchestrator not available, falling back to legacy workflow: {e}")
                # Fall through to legacy workflow
        
        # Legacy workflow (for backward compatibility)
        try:
            logger.info(f"Starting 5-stage workflow for prompt: {user_prompt}")

            # Stage 1: RAG-enhanced context retrieval
            context = ""
            if self.rag:
                try:
                    # Use default official-only scope for legacy workflow
                    context = await self.rag.retrieve(user_prompt, rag_scope='official-only')
                except Exception as e:
                    logger.warning(f"RAG context retrieval failed: {e}")
                    context = ""

            # Stage 1: Generate contract
            logger.info("Stage 1/5: Generating Contract")
            generation_result = await self.generate_contract(user_prompt, context)
            if generation_result["status"] != "success":
                return generation_result

            contract_code = generation_result["contract_code"]
            contract_name = generation_result.get("contract_name", "Contract")
            
            # Stage 1.5: Compile contract with Foundry
            logger.info("Stage 1.5/5: Compiling Contract with Foundry")
            compilation_result = await self._compile_contract(contract_name, contract_code)
            if not compilation_result.get("success"):
                logger.error(f"Compilation failed: {compilation_result.get('error', 'Unknown error')}")
                return {
                    "status": "error",
                    "error": f"Contract compilation failed: {compilation_result.get('error', 'Unknown error')}",
                    "workflow": "aborted",
                    "generation": generation_result,
                    "compilation": compilation_result,
                    "message": "Workflow terminated due to compilation failure"
                }
            
            logger.info("✅ Contract compiled successfully")

            # Stage 2: Audit contract
            logger.info("Stage 2/5: Auditing Contract")
            audit_result = await self.audit_contract(contract_code)
            if audit_result["status"] != "success":
                return audit_result

            # Stage 2.5: Enhanced Security Analysis (NEW)
            security_analysis = None
            if hasattr(self, 'security_pipeline') and self.security_pipeline:
                logger.info("Stage 2.5/5: Running Enhanced Security Analysis")
                try:
                    from services.security import SecurityAnalysisPipeline
                    if not hasattr(self, 'security_pipeline'):
                        self.security_pipeline = SecurityAnalysisPipeline()
                    
                    # Analyze the generated contract before deployment
                    tx_params = {
                        "to": None,  # Not deployed yet
                        "from": self.config.get("deployer_address", "0x0000000000000000000000000000000000000000"),
                        "data": contract_code,
                        "value": 0,
                        "network": network
                    }
                    
                    security_analysis = await self.security_pipeline.analyze_transaction(tx_params)
                    
                    # Log security analysis results
                    logger.info(f"Security Analysis: Risk Level = {security_analysis.get('risk_level', 'unknown')}")
                    logger.info(f"Security Analysis: Risk Score = {security_analysis.get('risk_score', 0)}/100")
                    
                    # Print security summary
                    print("\n" + self.security_pipeline.get_analysis_summary(security_analysis))
                    
                except Exception as e:
                    logger.warning(f"Security analysis failed: {e}")
                    security_analysis = {"risk_level": "unknown", "error": str(e)}

            # Stage 3: Deploy if audit passes or user confirms
            deployment_result = None
            audit_severity = audit_result.get("severity", "low")
            
            if not test_only:
                if audit_severity in ["low", "medium"]:
                    logger.info("Stage 3/5: Deploying to Blockchain")
                    deployment_result = await self.deploy_contract(contract_code, network, contract_name)
                elif audit_severity == "high":
                    if allow_insecure:
                        # Auto-proceed if --allow-insecure flag is set
                        print(f"\n⚠️  Audit found HIGH severity issues.")
                        print(f"   Severity: {audit_severity}")
                        print(f"   Issues found: {len(audit_result.get('results', {}).get('issues', []))}")
                        print("⚠️  Proceeding with deployment as --allow-insecure flag is set.")
                        logger.info("Stage 3/5: Deploying to Blockchain (--allow-insecure flag set)")
                        deployment_result = await self.deploy_contract(contract_code, network, contract_name)
                    else:
                        # Interactive confirmation for high-severity issues
                        print(f"\n⚠️  Audit found HIGH severity issues.")
                        print(f"   Severity: {audit_severity}")
                        print(f"   Issues found: {len(audit_result.get('results', {}).get('issues', []))}")
                        
                        try:
                            user_input = input("Do you want to proceed with deployment anyway? (Y/n): ").strip().lower()
                            if user_input in ['', 'y', 'yes']:
                                print("⚠️  Proceeding with deployment as per user request.")
                                logger.info("Stage 3/5: Deploying to Blockchain (user confirmed despite high severity)")
                                deployment_result = await self.deploy_contract(contract_code, network, contract_name)
                            else:
                                print("🚫 Deployment cancelled by user due to audit issues.")
                                logger.info("Stage 3/5: Skipped (user cancelled due to high severity audit)")
                                deployment_result = {"status": "skipped", "reason": "user_cancelled_audit"}
                        except (EOFError, KeyboardInterrupt):
                            print("\n🚫 Deployment cancelled due to input error.")
                            logger.info("Stage 3/5: Skipped (input error during user confirmation)")
                            deployment_result = {"status": "skipped", "reason": "input_error"}
                else:
                    logger.info("Stage 3/5: Skipped (unknown audit severity)")
                    deployment_result = {"status": "skipped", "reason": "unknown_audit_severity"}
                
                # ABORT workflow if deployment fails - NO SIMULATION MODE
                if deployment_result.get("status") not in ["success", "deployed"]:
                    error_msg = deployment_result.get('error', 'Unknown deployment error')
                    logger.error(f"CRITICAL: Deployment failed: {error_msg}")
                    logger.error("Workflow aborted - cannot continue without successful deployment")
                    
                    # Return error result and stop workflow
                    return {
                        "status": "error",
                        "error": f"Deployment failed: {error_msg}",
                        "workflow": "aborted",
                        "generation": generation_result,
                        "audit": audit_result,
                        "deployment": deployment_result,
                        "message": "Workflow terminated due to deployment failure"
                    }
            else:
                logger.info("Stage 3/5: Skipped (test-only mode or audit failed)")
                deployment_result = {"status": "skipped", "reason": "test_only" if test_only else "audit_failed"}

            # Stage 4: Verify contract (if deployed)
            verification_result = None
            if deployment_result and deployment_result.get("status") in ["success", "deployed"] and auto_verification:
                logger.info("Stage 4/5: Verifying Contract")
                from services.verification.verifier import ContractVerifier
                
                verifier = ContractVerifier(network, self.config)
                contract_address = deployment_result.get("contract_address")
                
                if contract_address:
                    verification_result = await verifier.verify_contract(
                        source_code=contract_code,
                        contract_address=contract_address
                    )
                else:
                    verification_result = {"status": "skipped", "reason": "no_contract_address"}
            elif not deployment_result:
                logger.warning("Stage 4/5: Skipped (deployment failed)")
                verification_result = {"status": "skipped", "reason": "deployment_failed"}
            elif not auto_verification:
                logger.info("Stage 4/5: Skipped (verification disabled)")
                verification_result = {"status": "skipped", "reason": "verification_disabled"}

            # Stage 5: Test contract (if deployed)
            testing_result = None
            if deployment_result and deployment_result.get("status") in ["success", "deployed"]:
                logger.info("Stage 5/5: Testing Contract Functionality")
                from services.testing.contract_tester import ContractTester
                
                contract_address = deployment_result.get("contract_address")
                rpc_url = self.config.get('networks', {}).get(network, {}).get('rpc_url')
                
                if contract_address and rpc_url:
                    tester = ContractTester(rpc_url, contract_address)
                    testing_result = await tester.run_tests(contract_code)
                else:
                    testing_result = {"status": "skipped", "reason": "missing_rpc_or_address"}
            elif not deployment_result:
                logger.warning("Stage 5/5: Skipped (deployment failed)")
                testing_result = {"status": "skipped", "reason": "deployment_failed"}
            else:
                logger.info("Stage 5/5: Skipped (no deployment)")
                testing_result = {"status": "skipped", "reason": "no_deployment"}

            # Log audit results with deployment (if Alith SDK supports on-chain logging)
            # Note: Alith SDK on-chain audit logging can be added here when available

            # FIXED: Validate deployment actually succeeded before marking workflow as success
            if not test_only:
                # Check that deployment was attempted and succeeded
                if not deployment_result:
                    return {
                        "status": "error",
                        "error": "Deployment was not attempted",
                        "workflow": "failed",
                        "generation": generation_result,
                        "audit": audit_result,
                        "deployment": {"status": "error", "error": "Deployment not attempted"}
                    }
                
                # Double-check deployment status (don't trust single check)
                deploy_status = deployment_result.get("status")
                if deploy_status not in ["success", "deployed"]:
                    error_msg = deployment_result.get('error', 'Unknown deployment error')
                    return {
                        "status": "error",
                        "error": f"Deployment failed: {error_msg}",
                        "workflow": "failed",
                        "generation": generation_result,
                        "audit": audit_result,
                        "deployment": deployment_result,
                        "message": "Workflow failed at deployment stage"
                    }
            
            # Return complete workflow results
            return {
                "status": "success",
                "workflow": "complete_5_stages",
                "stages_completed": 6,  # Updated to include compilation
                "generation": generation_result,
                "compilation": compilation_result,  # Include compilation results
                "audit": audit_result,
                "deployment": deployment_result,
                "verification": verification_result,
                "testing": testing_result,
                "network": network,
                "test_only": test_only
            }

        except Exception as e:
            logger.error(f"5-stage workflow execution failed: {e}")
            return {"status": "error", "error": str(e), "workflow": "failed"}

    def _estimate_gas(self, contract_code: str) -> Dict[str, Any]:
        """Estimate gas usage for contract functions."""
        try:
            from core.optimization.gas_optimizer import GasOptimizer

            optimizer = GasOptimizer()
            optimizations = optimizer.analyze_contract(contract_code)
            savings_estimate = optimizer.estimate_gas_savings(optimizations)

            # Basic gas estimation (simplified)
            base_deployment = 1000000
            base_function = 50000

            # Apply optimization savings
            optimized_deployment = max(
                base_deployment - savings_estimate["total_savings"], 500000
            )
            optimized_function = max(
                base_function - (savings_estimate["total_savings"] // 10), 20000
            )

            return {
                "deployment": {
                    "original": base_deployment,
                    "optimized": optimized_deployment,
                    "savings": base_deployment - optimized_deployment,
                },
                "average_function": {
                    "original": base_function,
                    "optimized": optimized_function,
                    "savings": base_function - optimized_function,
                },
                "complex_function": {
                    "original": base_function * 4,
                    "optimized": optimized_function * 4,
                    "savings": (base_function - optimized_function) * 4,
                },
                "optimizations": {
                    "count": savings_estimate["optimization_count"],
                    "high_impact": savings_estimate["high_impact_count"],
                    "medium_impact": savings_estimate["medium_impact_count"],
                    "low_impact": savings_estimate["low_impact_count"],
                },
            }
        except Exception as e:
            logger.error(f"Gas estimation failed: {e}")
            return {
                "deployment": 1000000,
                "average_function": 50000,
                "complex_function": 200000,
                "error": str(e),
            }

    async def optimize_contract(self, contract_code: str) -> Dict[str, Any]:
        """
        Optimize contract for gas efficiency.

        Args:
            contract_code: Solidity contract code to optimize

        Returns:
            Dictionary containing optimization results
        """
        try:
            from core.optimization.gas_optimizer import GasOptimizer

            optimizer = GasOptimizer()
            optimizations = optimizer.analyze_contract(contract_code)
            savings_estimate = optimizer.estimate_gas_savings(optimizations)

            # Generate optimized code
            optimized_code = optimizer.generate_optimized_code(
                contract_code, optimizations
            )

            # Generate report
            report = optimizer.generate_report(optimizations)

            return {
                "status": "success",
                "original_code": contract_code,
                "optimized_code": optimized_code,
                "optimizations": optimizations,
                "savings_estimate": savings_estimate,
                "report": report,
                "optimization_count": len(optimizations),
            }
        except Exception as e:
            logger.error(f"Contract optimization failed: {e}")
            return {"status": "error", "error": str(e), "original_code": contract_code}

    async def monitor_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """
        Monitor a blockchain transaction.

        Args:
            tx_hash: Transaction hash to monitor

        Returns:
            Dictionary containing monitoring results
        """
        try:
            # Start monitoring the transaction
            tx_status = await self.transaction_monitor.monitor_transaction(tx_hash)

            # Start monitoring if not already started
            if not self.transaction_monitor.is_monitoring:
                await self.transaction_monitor.start_monitoring()

            return {
                "status": "success",
                "tx_hash": tx_hash,
                "monitoring_started": True,
                "initial_status": {
                    "status": tx_status.status,
                    "block_number": tx_status.block_number,
                    "gas_used": tx_status.gas_used,
                    "confirmations": tx_status.confirmations,
                    "timestamp": tx_status.timestamp.isoformat(),
                },
            }
        except Exception as e:
            logger.error(f"Transaction monitoring failed: {e}")
            return {"status": "error", "error": str(e), "tx_hash": tx_hash}

    async def get_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get current status of a monitored transaction.

        Args:
            tx_hash: Transaction hash

        Returns:
            Dictionary containing transaction status
        """
        try:
            tx_status = await self.transaction_monitor.get_transaction_status(tx_hash)

            if not tx_status:
                return {
                    "status": "error",
                    "error": "Transaction not found or not being monitored",
                    "tx_hash": tx_hash,
                }

            return {
                "status": "success",
                "tx_hash": tx_hash,
                "transaction_status": {
                    "status": tx_status.status,
                    "block_number": tx_status.block_number,
                    "gas_used": tx_status.gas_used,
                    "gas_price": tx_status.gas_price,
                    "from_address": tx_status.from_address,
                    "to_address": tx_status.to_address,
                    "value": tx_status.value,
                    "confirmations": tx_status.confirmations,
                    "timestamp": tx_status.timestamp.isoformat(),
                    "error_message": tx_status.error_message,
                },
            }
        except Exception as e:
            logger.error(f"Failed to get transaction status: {e}")
            return {"status": "error", "error": str(e), "tx_hash": tx_hash}

    async def get_monitoring_summary(self) -> Dict[str, Any]:
        """
        Get summary of all monitored transactions.

        Returns:
            Dictionary containing monitoring summary
        """
        try:
            summary = await self.transaction_monitor.get_monitoring_summary()
            return {"status": "success", "monitoring_summary": summary}
        except Exception as e:
            logger.error(f"Failed to get monitoring summary: {e}")
            return {"status": "error", "error": str(e)}

    def _calculate_complexity(self, contract_code: str) -> int:
        """Calculate cyclomatic complexity of the contract."""
        # Placeholder for complexity calculation
        return len(contract_code.split("\n")) // 10

    def _check_security_patterns(self, contract_code: str) -> Dict[str, bool]:
        """Check for common security patterns."""
        return {
            "has_reentrancy_guard": "ReentrancyGuard" in contract_code,
            "has_access_control": "onlyOwner" in contract_code
            or "onlyRole" in contract_code,
            "has_pausable": "Pausable" in contract_code,
            "uses_safe_math": "SafeMath" in contract_code
            or "unchecked" not in contract_code,
        }

    def _check_best_practices(self, contract_code: str) -> Dict[str, bool]:
        """Check for Solidity best practices."""
        return {
            "has_nat_spec": "/**" in contract_code and "*/" in contract_code,
            "has_events": "event " in contract_code,
            "has_modifiers": "modifier " in contract_code,
            "uses_openzeppelin": 'import "@openzeppelin' in contract_code,
        }

    def _select_ai_provider(self) -> tuple[str, str]:
        """
        Select the best available AI provider based on configured API keys.

        Returns:
            Tuple of (provider_name, api_key)
        """
        # Priority order for AI providers
        providers = [
            ("openai", "OPENAI_API_KEY"),
            ("deepseek", "DEEPSEEK_API_KEY"),
            ("xai", "XAI_API_KEY"),
            ("gpt-oss", "GPT_OSS_API_KEY"),
            ("anthropic", "ANTHROPIC_API_KEY"),
            ("google", "GOOGLE_API_KEY"),
            ("dashscope", "DASHSCOPE_API_KEY"),
        ]

        for provider, key_name in providers:
            api_key = self.config.get(key_name)
            if api_key and api_key != f"your_{key_name.lower()}_here":
                logger.info(f"Selected AI provider: {provider}")
                return provider, api_key

        # Fallback to OpenAI with a placeholder
        logger.warning("No valid API keys found, using OpenAI with placeholder")
        return "openai", "placeholder-key"

    def _create_contract_generation_prompt(
        self, user_prompt: str, context: str = "", contract_name: str = None
    ) -> str:
        """Create enhanced prompt for contract generation."""
        contract_name_instruction = ""
        if contract_name:
            contract_name_instruction = f"\nCRITICAL: The contract MUST be named exactly '{contract_name}'. Use 'contract {contract_name}' as the contract declaration."
        
        base_prompt = f"""
You are an expert Solidity smart contract developer. Generate a secure, production-ready smart contract based on the user's request.

User Request: {user_prompt}

Additional Context:
{context}
{contract_name_instruction}

Requirements:
1. Use Solidity ^0.8.0
2. Follow security best practices
3. Include proper access controls
4. Add events for important actions
5. Include NatSpec documentation
6. Use OpenZeppelin contracts when appropriate
7. Implement proper error handling
8. Add reentrancy guards where needed
9. Contract name MUST match the specified name exactly

Generate only the Solidity contract code, no explanations or markdown formatting.
"""
        return base_prompt.strip()

    def _post_process_contract(self, contract_code: str) -> str:
        """Post-process generated contract code."""
        # Remove markdown formatting if present
        if contract_code.startswith("```solidity"):
            contract_code = contract_code.replace("```solidity", "").replace("```", "")

        if contract_code.startswith("```"):
            contract_code = contract_code.replace("```", "")

        # Clean up extra whitespace
        contract_code = contract_code.strip()

        return contract_code

    async def run_comprehensive_workflow(self, user_prompt: str) -> Dict[str, Any]:
        """
        Run comprehensive end-to-end workflow based on user intent
        
        Args:
            user_prompt: User's natural language request
            
        Returns:
            Complete workflow results
        """
        try:
            # 1. Classify user intent
            intent_type, parameters = self.intent_router.classify_intent(user_prompt)
            logger.info(f"Intent classified as: {intent_type.value}")
            
            # 2. Get RAG context
            context = ""
            if self.rag:
                try:
                    context = await self.rag.retrieve(user_prompt, rag_scope='official-only')
                    logger.info(f"RAG context retrieved: {len(context)} characters")
                except Exception as e:
                    logger.warning(f"RAG context retrieval failed: {e}")
                    context = ""
            
            # 3. Generate smart contracts
            contract_result = await self.generate_contract(user_prompt, context)
            if not contract_result.get("success"):
                return contract_result
            
            contract_code = contract_result.get("contract_code", "")
            
            # 4. Run security audit
            audit_result = await self.audit_contract(contract_code)
            if not audit_result.get("success"):
                return audit_result
            
            # 5. Deploy contracts
            # Extract contract name from generation result
            contract_name = contract_result.get("contract_name") or "Contract"
            deployment_result = await self.deploy_contract(contract_code, "hyperion", contract_name)
            if not deployment_result.get("success"):
                return deployment_result
            
            # 6. Handle different intent types
            if intent_type == IntentType.DEBUG_TRANSACTION:
                return await self._handle_debug_workflow(parameters, deployment_result)
            else:
                # Simple contract workflow
                return await self._handle_simple_contract_workflow(
                    contract_code, audit_result, deployment_result
                )
                
        except Exception as e:
            logger.error(f"Comprehensive workflow failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "workflow": "failed"
            }

    # dApp scaffolding removed - focusing on smart contracts only

    async def _handle_debug_workflow(
        self, 
        parameters: Dict[str, Any], 
        deployment_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle debugging workflow"""
        try:
            tx_hash = parameters.get("tx_hash", deployment_result.get("tx_hash", ""))
            rpc_url = "https://hyperion-testnet.metisdevops.link"
            
            if not tx_hash:
                return {
                    "status": "error",
                    "workflow": "debug",
                    "error": "No transaction hash provided for debugging"
                }
            
            # Start debug session
            debug_session = await self.edb.start_debug_session(tx_hash, rpc_url)
            
            return {
                "status": "success",
                "workflow": "debug",
                "debug_session": {
                    "session_id": debug_session.session_id,
                    "tx_hash": tx_hash,
                    "status": debug_session.status
                },
                "instructions": [
                    "Use step_through_transaction() to step through execution",
                    "Use inspect_variable() to inspect variable values",
                    "Use get_call_stack() to view call stack"
                ]
            }
            
        except Exception as e:
            logger.error(f"Debug workflow failed: {e}")
            return {
                "status": "error",
                "workflow": "debug",
                "error": str(e)
            }

    async def _handle_simple_contract_workflow(
        self, 
        contract_code: str, 
        audit_result: Dict[str, Any], 
        deployment_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle simple contract workflow"""
        # Log audit onchain
        audit_log_result = None
        # Note: On-chain audit logging can be implemented with Alith SDK when available
        
        result = {
            "status": "success",
            "workflow": "simple_contract",
            "contract_code": contract_code,
            "audit_result": audit_result,
            "deployment_result": deployment_result,
            "audit_logged": audit_log_result
        }
        return result

    async def debug_transaction(self, tx_hash: str, steps: int = 1) -> Dict[str, Any]:
        """
        Debug a transaction using EDB
        
        Args:
            tx_hash: Transaction hash to debug
            steps: Number of steps to execute
            
        Returns:
            Debug results
        """
        try:
            rpc_url = "https://hyperion-testnet.metisdevops.link"
            
            # Start debug session
            session = await self.edb.start_debug_session(tx_hash, rpc_url)
            
            if session.status != "active":
                return {
                    "status": "error",
                    "error": f"Failed to start debug session: {session.variables.get('error', 'Unknown error')}"
                }
            
            # Step through transaction
            step_result = await self.edb.step_through_transaction(session.session_id, steps)
            
            return {
                "status": "success",
                "debug_session": {
                    "session_id": session.session_id,
                    "tx_hash": tx_hash
                },
                "step_result": step_result
            }
            
        except Exception as e:
            logger.error(f"Transaction debugging failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def scaffold_dapp(self, requirements: str, contract_code: str) -> Dict[str, Any]:
        """
        Scaffold a complete dApp
        
        Args:
            requirements: User requirements for the dApp
            contract_code: Generated smart contract code
            
        Returns:
            Scaffold results
        """
        try:
            # Classify requirements
            intent_type, parameters = self.intent_router.classify_intent(requirements)
            
            # Create scaffold configuration
            scaffold_config = ScaffoldConfig(
                project_name=parameters.get("project_name", "hyperkit_dapp"),
                frontend_framework=parameters.get("frontend_framework", "nextjs"),
                backend_framework=parameters.get("backend_framework", "express"),
                blockchain=parameters.get("blockchain", "hyperion"),
                features=parameters.get("features", [])
            )
            
            # Scaffold the dApp
            result = await self.scaffolder.scaffold_dapp(scaffold_config, contract_code)
            
            return {
                "status": "success",
                "scaffold_result": result
            }
            
        except Exception as e:
            logger.error(f"dApp scaffolding failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_langchain_agent(self):
        """Get the LangChain agent for advanced RAG operations"""
        return self.langchain_agent
    
    def create_custom_langchain_agent(self, tools=None, system_prompt=None):
        """Create a custom LangChain agent with specific tools and prompt"""
        if hasattr(self.rag, 'create_langchain_agent'):
            return self.rag.create_langchain_agent(tools, system_prompt)
        return None

    async def audit_public_contract(self, address: str, network: str = "hyperion") -> Dict[str, Any]:
        """
        Audit a public contract by address
        
        Args:
            address: Contract address
            network: Network to query
            
        Returns:
            Audit results
        """
        try:
            logger.info(f"Auditing public contract: {address} on {network}")
            
            result = await public_contract_auditor.audit_by_address(address, network)
            
            if result.get("status") == "success":
                # Note: On-chain audit logging can be implemented with Alith SDK when available
                result["audit_logged"] = None
            
            return result
            
        except Exception as e:
            logger.error(f"Public contract audit failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "address": address,
                "network": network
            }

    async def start_monitoring(self, target: str, monitor_type: str, network: str = "hyperion", 
                             interval: int = 30, duration: Optional[int] = None) -> str:
        """
        Start monitoring a target
        
        Args:
            target: Contract address or transaction hash
            monitor_type: Type of monitoring (transaction, contract, gas, events)
            network: Network to monitor
            interval: Monitoring interval in seconds
            duration: Monitoring duration in seconds (None for indefinite)
            
        Returns:
            Monitor ID
        """
        try:
            monitor_type_enum = MonitorType(monitor_type)
            config = MonitorConfig(
                target=target,
                monitor_type=monitor_type_enum,
                network=network,
                interval=interval,
                duration=duration
            )
            
            monitor_id = await enhanced_monitor.start_monitoring(config)
            logger.info(f"Started monitoring {target} ({monitor_type})")
            
            return monitor_id
            
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            raise

    async def stop_monitoring(self, monitor_id: str) -> bool:
        """
        Stop monitoring a target
        
        Args:
            monitor_id: Monitor ID to stop
            
        Returns:
            True if stopped successfully
        """
        try:
            return await enhanced_monitor.stop_monitoring(monitor_id)
        except Exception as e:
            logger.error(f"Failed to stop monitoring: {e}")
            return False

    async def get_monitoring_metrics(self) -> Dict[str, Any]:
        """Get monitoring metrics"""
        try:
            return enhanced_monitor.get_metrics()
        except Exception as e:
            logger.error(f"Failed to get monitoring metrics: {e}")
            return {"error": str(e)}

    async def generate_defi_primitive(self, primitive_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a DeFi primitive contract
        
        Args:
            primitive_type: Type of DeFi primitive (staking, swap, vault, lending, governance)
            config: Configuration for the primitive
            
        Returns:
            Generated contract code and metadata
        """
        try:
            primitive_enum = DeFiPrimitive(primitive_type)
            result = await defi_primitives_generator.generate_primitive(primitive_enum, config)
            
            if result.get("status") == "success":
                logger.info(f"Generated {primitive_type} primitive successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"DeFi primitive generation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "primitive_type": primitive_type
            }

    @safe_operation("generate_defi_protocol")
    async def generate_defi_protocol(self, protocol_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate DeFi protocol contract based on specifications.
        Focus: Blockchain/DeFi protocol generation with advanced features.

        Args:
            protocol_spec: Dictionary containing protocol specifications

        Returns:
            Dictionary containing generated protocol code and metadata
        """
        try:
            from services.defi.protocols_generator import DeFiProtocolsGenerator
            
            generator = DeFiProtocolsGenerator()
            result = await generator.generate_protocol(protocol_spec)
            
            logger.info(f"DeFi protocol generated: {result.get('protocol_type')}")
            return {
                "status": "success",
                "protocol_code": result.get("source_code"),
                "protocol_id": result.get("protocol_id"),
                "protocol_type": result.get("protocol_type"),
                "network": result.get("network"),
                "features": result.get("features"),
                "gas_estimate": result.get("gas_estimate"),
                "security_level": result.get("security_level"),
                "defi_complexity": result.get("defi_complexity"),
                "created_at": result.get("created_at")
            }
            
        except Exception as e:
            logger.error(f"DeFi protocol generation failed: {e}")
            return {"status": "error", "error": str(e), "severity": "critical"}

    async def get_supported_defi_primitives(self) -> List[str]:
        """Get list of supported DeFi primitives"""
        return [primitive.value for primitive in DeFiPrimitive]

    async def get_supported_networks(self) -> List[str]:
        """Get list of supported networks for public contract auditing"""
        return public_contract_auditor.get_supported_networks()

    @safe_operation("verify_contract")
    async def verify_contract(self, contract_address: str, source_code: str, network: str = "hyperion") -> Dict[str, Any]:
        """
        Verify a smart contract on the blockchain explorer.
        
        Args:
            contract_address: The deployed contract address
            source_code: The Solidity source code
            network: Target network for verification
            
        Returns:
            Dictionary containing verification results
        """
        try:
            from services.verification.verifier import ContractVerifier
            
            logger.info(f"Starting contract verification for {contract_address} on {network}")
            
            verifier = ContractVerifier(network, self.config)
            result = await verifier.verify_contract(
                source_code=source_code,
                contract_address=contract_address
            )
            
            return {
                "status": "success",
                "verification_result": result,
                "contract_address": contract_address,
                "network": network
            }
            
        except Exception as e:
            logger.error(f"Contract verification failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "contract_address": contract_address,
                "network": network
            }

    @safe_operation("test_contract")
    async def test_contract(self, contract_address: str, source_code: str, network: str = "hyperion") -> Dict[str, Any]:
        """
        Test a deployed smart contract functionality.
        
        Args:
            contract_address: The deployed contract address
            source_code: The Solidity source code
            network: Target network for testing
            
        Returns:
            Dictionary containing test results
        """
        try:
            from services.testing.contract_tester import ContractTester
            
            # Get network configuration
            networks_config = self.config.get('networks', {})
            if network not in networks_config:
                return {
                    "status": "error",
                    "error": f"Network '{network}' not configured",
                    "available_networks": list(networks_config.keys())
                }
            
            network_config = networks_config[network]
            rpc_url = network_config.get('rpc_url')
            
            if not isinstance(rpc_url, str):
                return {
                    "status": "error",
                    "error": f"RPC URL must be string, got {type(rpc_url).__name__}"
                }
            
            logger.info(f"Starting contract testing for {contract_address} on {network}")
            
            tester = ContractTester(rpc_url, contract_address)
            result = await tester.run_tests(source_code)
            
            return {
                "status": "success",
                "test_results": result,
                "contract_address": contract_address,
                "network": network
            }
            
        except Exception as e:
            logger.error(f"Contract testing failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "contract_address": contract_address,
                "network": network
            }


# Example usage and testing
async def main():
    """Example usage of the HyperKit Agent."""
    # HYPERION-ONLY configuration
    config = {
        "openai_api_key": "your-api-key-here",  # Required for Alith SDK
        "networks": {
            "hyperion": {
                "rpc_url": "https://hyperion-testnet.metisdevops.link",
                "chain_id": 133717,
                "explorer_url": "https://hyperion-testnet-explorer.metisdevops.link"
            }
            # Future network support (LazAI, Metis) documented in ROADMAP.md only
        },
    }

    agent = HyperKitAgent(config)

    # Test workflow
    prompt = "Create a simple ERC20 token contract with minting functionality"
    result = await agent.run_workflow(prompt)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
