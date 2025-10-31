"""
Self-Healing Error Handler
Parses errors, detects automatable issues, and triggers auto-fix attempts.
"""

import re
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can be auto-fixed"""
    DEPENDENCY_MISSING = "dependency_missing"
    IMPORT_NOT_FOUND = "import_not_found"
    COMPILATION_ERROR = "compilation_error"
    NETWORK_ERROR = "network_error"
    CONFIG_MISSING = "config_missing"
    PERMISSION_ERROR = "permission_error"
    TIMEOUT_ERROR = "timeout_error"
    FATAL = "fatal"  # Cannot be auto-fixed


@dataclass
class ParsedError:
    """Parsed error information"""
    error_type: ErrorType
    original_message: str
    automatable: bool
    suggested_fix: Optional[str] = None
    auto_fix_action: Optional[str] = None
    fix_parameters: Dict[str, Any] = None


class SelfHealingErrorHandler:
    """
    Self-healing error handler that parses errors and attempts automatic fixes.
    """
    
    def __init__(self):
        """Initialize error handler"""
        self.error_patterns = self._build_error_patterns()
        logger.info("SelfHealingErrorHandler initialized")
    
    def _build_error_patterns(self) -> Dict[ErrorType, List[re.Pattern]]:
        """Build regex patterns for error detection"""
        patterns = {
            ErrorType.DEPENDENCY_MISSING: [
                re.compile(r"Source\s+[\"']([^\"']+)[\"']\s+not found", re.IGNORECASE),
                re.compile(r"Import\s+[\"']([^\"']+)[\"']\s+not found", re.IGNORECASE),
                re.compile(r"Could not find\s+[\"']([^\"']+)[\"']", re.IGNORECASE),
                re.compile(r"Module\s+['\"]([^\"']+)['\"]\s+not found", re.IGNORECASE),
            ],
            ErrorType.IMPORT_NOT_FOUND: [
                re.compile(r"import\s+[\"']([^\"']+)[\"']\s+not found", re.IGNORECASE),
                re.compile(r"cannot resolve import\s+[\"']([^\"']+)[\"']", re.IGNORECASE),
                re.compile(r"failed to resolve\s+[\"']([^\"']+)[\"']", re.IGNORECASE),
            ],
            ErrorType.COMPILATION_ERROR: [
                re.compile(r"compilation failed", re.IGNORECASE),
                re.compile(r"compiler run failed", re.IGNORECASE),
                re.compile(r"syntax error", re.IGNORECASE),
                re.compile(r"type error", re.IGNORECASE),
                re.compile(r"function has override specified but does not override", re.IGNORECASE),
                re.compile(r"override.*does not override anything", re.IGNORECASE),
                re.compile(r"shadows an existing declaration", re.IGNORECASE),
                re.compile(r"declaration shadows", re.IGNORECASE),
                re.compile(r"Counters\.sol.*not found", re.IGNORECASE),
                re.compile(r"invalid solc version", re.IGNORECASE),
                re.compile(r"no solc version exists.*0\.8\.\d+", re.IGNORECASE),
                re.compile(r"version requirement.*0\.8\.\d+", re.IGNORECASE),
                re.compile(r"No arguments passed to the base constructor", re.IGNORECASE),
                re.compile(r"Base constructor parameters", re.IGNORECASE),
            ],
            ErrorType.NETWORK_ERROR: [
                re.compile(r"network error", re.IGNORECASE),
                re.compile(r"connection.*refused", re.IGNORECASE),
                re.compile(r"timeout", re.IGNORECASE),
                re.compile(r"ECONNREFUSED", re.IGNORECASE),
            ],
            ErrorType.CONFIG_MISSING: [
                re.compile(r"config.*not found", re.IGNORECASE),
                re.compile(r"missing.*config", re.IGNORECASE),
                re.compile(r"required.*config.*missing", re.IGNORECASE),
            ],
            ErrorType.PERMISSION_ERROR: [
                re.compile(r"permission denied", re.IGNORECASE),
                re.compile(r"access denied", re.IGNORECASE),
                re.compile(r"EACCES", re.IGNORECASE),
            ],
            ErrorType.TIMEOUT_ERROR: [
                re.compile(r"operation.*timeout", re.IGNORECASE),
                re.compile(r"request.*timeout", re.IGNORECASE),
            ],
        }
        return patterns
    
    def parse_error(self, error_message: str, error_type: Optional[str] = None) -> ParsedError:
        """
        Parse an error message and determine if it can be auto-fixed.
        
        Args:
            error_message: The error message to parse
            error_type: Optional pre-classified error type
            
        Returns:
            ParsedError with fix suggestions
        """
        error_str = str(error_message).lower()
        
        # Check each error pattern
        for err_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                match = pattern.search(error_message)
                if match:
                    # Extract dependency/module name if available
                    fix_params = {}
                    if match.lastindex is not None and match.lastindex >= 1:
                        extracted = match.group(1)
                        fix_params["dependency"] = extracted
                        fix_params["import_path"] = extracted
                    
                    suggested_fix = self._get_suggested_fix(err_type, fix_params)
                    auto_fix_action = self._get_auto_fix_action(err_type, fix_params)
                    
                    return ParsedError(
                        error_type=err_type,
                        original_message=error_message,
                        automatable=err_type != ErrorType.FATAL,
                        suggested_fix=suggested_fix,
                        auto_fix_action=auto_fix_action,
                        fix_parameters=fix_params
                    )
        
        # Default: unclassified error
        return ParsedError(
            error_type=ErrorType.FATAL,
            original_message=error_message,
            automatable=False,
            suggested_fix="Manual intervention required"
        )
    
    def _get_suggested_fix(self, error_type: ErrorType, params: Dict[str, Any]) -> Optional[str]:
        """Get human-readable fix suggestion"""
        fixes = {
            ErrorType.DEPENDENCY_MISSING: f"Install missing dependency: {params.get('dependency', 'unknown')}",
            ErrorType.IMPORT_NOT_FOUND: f"Install or verify import path: {params.get('import_path', 'unknown')}",
            ErrorType.COMPILATION_ERROR: "Check contract syntax and dependencies",
            ErrorType.NETWORK_ERROR: "Check network connection and retry",
            ErrorType.CONFIG_MISSING: "Create or update configuration file",
            ErrorType.PERMISSION_ERROR: "Check file permissions and access rights",
            ErrorType.TIMEOUT_ERROR: "Retry operation with longer timeout",
        }
        return fixes.get(error_type, "Manual review required")
    
    def _get_auto_fix_action(self, error_type: ErrorType, params: Dict[str, Any]) -> Optional[str]:
        """Get auto-fix action identifier"""
        actions = {
            ErrorType.DEPENDENCY_MISSING: "install_dependency",
            ErrorType.IMPORT_NOT_FOUND: "install_dependency",
            ErrorType.COMPILATION_ERROR: "retry_compile",
            ErrorType.NETWORK_ERROR: "retry_network",
            ErrorType.CONFIG_MISSING: "create_config",
            ErrorType.TIMEOUT_ERROR: "retry_with_timeout",
        }
        return actions.get(error_type)
    
    async def attempt_auto_fix(self, parsed_error: ParsedError, context: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Attempt to automatically fix an error.
        
        Args:
            parsed_error: The parsed error
            context: Context with dependencies, workspace, etc.
            
        Returns:
            Tuple of (success, message)
        """
        if not parsed_error.automatable:
            return False, "Error cannot be auto-fixed"
        
        action = parsed_error.auto_fix_action
        if not action:
            return False, "No auto-fix action available"
        
        try:
            if action == "install_dependency":
                return await self._auto_fix_dependency(parsed_error, context)
            elif action == "retry_compile":
                return await self._auto_fix_compilation(parsed_error, context)
            elif action == "retry_network":
                return await self._auto_fix_network(parsed_error, context)
            elif action == "create_config":
                return await self._auto_fix_config(parsed_error, context)
            elif action == "retry_with_timeout":
                return await self._auto_fix_timeout(parsed_error, context)
            else:
                return False, f"Unknown auto-fix action: {action}"
        except Exception as e:
            logger.error(f"Auto-fix attempt failed: {e}")
            return False, f"Auto-fix error: {str(e)}"
    
    async def _auto_fix_dependency(self, parsed_error: ParsedError, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Auto-fix missing dependency"""
        dependency = parsed_error.fix_parameters.get("dependency") or parsed_error.fix_parameters.get("import_path")
        if not dependency:
            return False, "No dependency specified"
        
        # Import dependency manager
        from services.dependencies.dependency_manager import DependencyManager
        
        workspace = context.get("workspace_dir")
        if not workspace:
            return False, "Workspace directory not in context"
        
        dep_manager = DependencyManager(workspace)
        
        # Detect dependency from import path
        # Create a dummy contract code to detect dependency
        dummy_code = f'import "{dependency}";'
        deps = dep_manager.detect_dependencies(dummy_code, "auto_fix.sol")
        
        if deps:
            result = await dep_manager.install_all_dependencies(deps)
            success = all(success for success, _ in result.values())
            if success:
                return True, f"Auto-installed dependency: {dependency}"
            else:
                return False, f"Failed to install dependency: {dependency}"
        else:
            return False, f"Could not detect dependency from: {dependency}"
    
    async def _auto_fix_compilation(self, parsed_error: ParsedError, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Auto-fix compilation errors including override issues"""
        contract_code = context.get("contract_code")
        error_message = parsed_error.original_message  # Keep original case for pattern matching
        error_message_lower = error_message.lower()

        # Missing 'override' specifier for functions/modifiers – attempt auto-insert
        if "missing 'override' specifier" in error_message or "is missing override specifier" in error_message:
            if contract_code:
                import re
                fixed = contract_code
                # Add override to function definitions lacking it
                # Matches: function name(...) <visibility> [virtual]? [returns ...] { ... }
                func_pattern = re.compile(r"(function\s+[A-Za-z_][A-Za-z0-9_]*\s*\([^)]*\)\s+)(?!.*\boverride\b)([a-zA-Z\s]*)(\{)")
                def add_override_to_func(m):
                    head, attrs, brace = m.groups()
                    attrs_clean = attrs.strip()
                    if attrs_clean:
                        attrs_clean = attrs_clean + " override "
                    else:
                        attrs_clean = "override "
                    return f"{head}{attrs_clean}{brace}"
                fixed = func_pattern.sub(add_override_to_func, fixed)

                # Add override to modifier definitions lacking it (Solidity >=0.8.8)
                mod_pattern = re.compile(r"(modifier\s+[A-Za-z_][A-Za-z0-9_]*\s*\([^)]*\)\s*)(?!.*\boverride\b)(\{)")
                fixed = mod_pattern.sub(lambda m: f"{m.group(1)}override {m.group(2)}", fixed)

                if fixed != contract_code:
                    context["contract_code"] = fixed
                    logger.info("🔧 Inserted missing 'override' specifiers into functions/modifiers")
                    return True, "Inserted missing 'override' specifiers and retrying"

        # Has override but base doesn't define it (common OZ v5 hook changes)
        if "does not override anything" in error_message:
            if contract_code:
                import re
                fixed = contract_code
                # Extract function name from error if possible
                func_match = re.search(r"Function\s+(\w+)\s+has override", error_message, re.IGNORECASE)
                func_name = func_match.group(1) if func_match else None
                
                # Remove problematic hook functions (_beforeTokenTransfer, _afterTokenTransfer)
                problematic_hooks = ["_beforeTokenTransfer", "_afterTokenTransfer"]
                if func_name in problematic_hooks or not func_name:
                    # Improved regex: handles multiline, comments, nested braces
                    hook_name = func_name or "_beforeTokenTransfer"
                    patterns = [
                        rf"function\s+{re.escape(hook_name)}\s*\([^)]*\)\s*internal[\s\S]*?override[\s\S]*?\{{[^{{}}]*(?:\{{[^{{}}]*\}}[^{{}}]*)*\}}",
                        rf"function\s+{re.escape(hook_name)}\s*\([^)]*\)\s*internal\s+virtual\s+override[\s\S]*?\{{[^{{}}]*(?:\{{[^{{}}]*\}}[^{{}}]*)*\}}",
                        rf"function\s+{re.escape(hook_name)}\s*\([^)]*\)\s*internal[\s\S]*?\{{[\s\S]*?\}}",
                    ]
                    for pat in patterns:
                        if re.search(pat, fixed, re.MULTILINE | re.DOTALL):
                            fixed = re.sub(pat, "", fixed, flags=re.MULTILINE | re.DOTALL)
                            logger.info(f"🔧 Removed invalid {hook_name} override (OZ v5 hook change)")
                            break
                else:
                    # For other functions, try removing just the override keyword
                    func_pattern = rf"function\s+{func_name}\s*\([^)]*\)\s*([\s\S]*?)\{{"
                    match = re.search(func_pattern, fixed, re.MULTILINE | re.DOTALL)
                    if match and "override" in match.group(1):
                        # Remove override keyword
                        fixed = re.sub(rf"(\s+){func_name}(\s*\([^)]*\)\s*)([\s\S]*?)(\s+override\s+)", r"\1\2\3", fixed)
                        logger.info(f"🔧 Removed override keyword from {func_name}")
                
                if fixed != contract_code:
                    context["contract_code"] = fixed
                    return True, f"Removed invalid override from {func_name or 'hook function'} and retrying"

        # Ensure OpenZeppelin deps when imports present or error mentions them
        try:
            if (contract_code and "@openzeppelin/" in contract_code) or "openzeppelin" in error_message:
                from services.dependencies.dependency_manager import DependencyManager
                workspace = context.get("workspace_dir")
                if workspace:
                    # Fix common OZ v5 import path changes (security -> utils)
                    try:
                        import re as _re
                        fixed_code = contract_code
                        # Comprehensive OZ v5 path mapping
                        oz_v5_path_fixes = {
                            "@openzeppelin/contracts/security/Pausable.sol": "@openzeppelin/contracts/utils/Pausable.sol",
                            "@openzeppelin/contracts/security/ReentrancyGuard.sol": "@openzeppelin/contracts/utils/ReentrancyGuard.sol",
                            "@openzeppelin/contracts/utils/security/Pausable.sol": "@openzeppelin/contracts/utils/Pausable.sol",
                        }
                        for old_path, new_path in oz_v5_path_fixes.items():
                            if old_path in fixed_code:
                                fixed_code = fixed_code.replace(old_path, new_path)
                        if fixed_code != contract_code:
                            context["contract_code"] = fixed_code
                            contract_code = fixed_code
                            logger.info("🔧 Rewrote OZ import paths for v5 compatibility")
                    except Exception:
                        pass
                    dep_manager = DependencyManager(workspace)
                    deps = dep_manager.detect_dependencies(contract_code or "", "AutoFix.sol")
                    if deps:
                        result = await dep_manager.install_all_dependencies(deps)
                        if all(success for success, _ in result.values()):
                            return True, "Installed OpenZeppelin dependencies"
        except Exception as e:
            logger.warning(f"Dependency auto-fix skipped: {e}")

        # OpenZeppelin v5 Ownable constructor fix - add Ownable(msg.sender) if missing
        if "No arguments passed to the base constructor" in error_message and "Ownable" in error_message:
            if contract_code:
                import re
                fixed = contract_code
                # Check if contract inherits Ownable
                if 'is Ownable' in fixed or re.search(r'contract\s+\w+\s+is\s+[^{]*Ownable', fixed):
                    # Check if constructor exists
                    constructor_match = re.search(r'constructor\s*\(([^)]*)\)\s*([^{]*)\{', fixed)
                    if constructor_match:
                        constructor_calls = constructor_match.group(2).strip()
                        # Check if Ownable constructor is NOT already called
                        if 'Ownable(' not in constructor_calls:
                            # Add Ownable(msg.sender) to constructor calls
                            fixed = re.sub(
                                r'(constructor\s*\([^)]*\)\s*)([^{]*?)(\{)',
                                lambda m: m.group(1) + m.group(2).rstrip() + ' Ownable(msg.sender) ' + m.group(3),
                                fixed,
                                count=1
                            )
                            logger.info("🔧 Auto-fixed: Added Ownable(msg.sender) to constructor for OpenZeppelin v5")
                            context["contract_code"] = fixed
                            return True, "Added Ownable(msg.sender) to constructor and retrying compilation"
                        elif 'Ownable()' in constructor_calls:
                            # Ownable() with no args - needs fixing
                            fixed = re.sub(
                                r'Ownable\(\)',
                                'Ownable(msg.sender)',
                                fixed,
                                count=1
                            )
                            logger.info("🔧 Auto-fixed: Changed Ownable() to Ownable(msg.sender) for OpenZeppelin v5")
                            context["contract_code"] = fixed
                            return True, "Fixed Ownable constructor call and retrying compilation"

        # Parameter shadowing errors - rename parameters with underscore prefix
        if "shadows an existing declaration" in error_message or "declaration shadows" in error_message:
            if contract_code:
                import re
                fixed = contract_code
                # Extract parameter name from error: "contracts/X.sol:18:59: parameter _initialSupply shadows..."
                shadow_match = re.search(r"parameter\s+(\w+)\s+shadows|(\w+)\s+shadows an existing", error_message, re.IGNORECASE)
                if shadow_match:
                    param_name = shadow_match.group(1) or shadow_match.group(2)
                    # Rename parameter in constructor signature
                    # Pattern: constructor(... param_name) or constructor(... param_name, ...)
                    constructor_pattern = rf"constructor\s*\(([^)]+)\)"
                    constructor_match = re.search(constructor_pattern, fixed)
                    if constructor_match:
                        params_str = constructor_match.group(1)
                        # Find and rename the parameter
                        # Match: type memory/calldata param_name or type param_name
                        param_pattern = rf"(\w+(?:\s+\w+)?\s+)({re.escape(param_name)})(\s*,|\s*\))"
                        if re.search(param_pattern, params_str):
                            new_param_name = f"_{param_name}" if not param_name.startswith("_") else f"{param_name}_renamed"
                            params_fixed = re.sub(
                                rf"(\w+(?:\s+\w+)?\s+)({re.escape(param_name)})(\s*,|\s*\)|$)",
                                rf"\1{new_param_name}\3",
                                params_str
                            )
                            # Update constructor signature
                            fixed = fixed.replace(f"constructor({params_str})", f"constructor({params_fixed})")
                            # Update references in constructor body
                            constructor_body_pattern = rf"constructor\s*\([^)]+\)\s*{{([^}}]+)}}"
                            body_match = re.search(constructor_body_pattern, fixed, re.DOTALL)
                            if body_match:
                                body = body_match.group(1)
                                body_fixed = re.sub(rf"\b{re.escape(param_name)}\b", new_param_name, body)
                                fixed = fixed.replace(body, body_fixed)
                            logger.info(f"🔧 Renamed shadowing parameter '{param_name}' to '{new_param_name}'")
                            if fixed != contract_code:
                                context["contract_code"] = fixed
                                return True, f"Renamed shadowing parameter and retrying"

        # Counters.sol not found (deprecated in OZ v5) - replace with manual counter
        # Check multiple error message formats (case-insensitive check)
        counters_error_patterns = [
            "counters.sol" in error_message_lower,
            ("counters" in error_message_lower and ("not found" in error_message_lower or "file not found" in error_message_lower)),
            "Source.*Counters" in error_message and "not found" in error_message_lower
        ]
        
        if any(counters_error_patterns):
            if contract_code:
                import re
                fixed = contract_code
                logger.info("🔧 Detected Counters.sol error - applying auto-fix...")
                
                # Step 1: Remove Counters import statement (handle various quote styles)
                import_pattern = r"import\s+['\"]@openzeppelin/contracts/utils/Counters\.sol['\"];?\s*\n?"
                fixed = re.sub(import_pattern, "", fixed, flags=re.IGNORECASE | re.MULTILINE)
                
                # Step 2: Remove "using Counters for Counters.Counter;" statement
                using_pattern = r"using\s+Counters\s+for\s+Counters\.Counter;?\s*\n?"
                fixed = re.sub(using_pattern, "", fixed, flags=re.IGNORECASE | re.MULTILINE)
                
                # Step 3: Replace "Counters.Counter private _tokenIdCounter;" with "uint256 private _tokenIdCounter;"
                counter_decl_pattern = r"Counters\.Counter\s+(private|internal|public)?\s*(\w+);"
                fixed = re.sub(counter_decl_pattern, r"uint256 \1 \2;", fixed, flags=re.IGNORECASE)
                # Also handle without visibility modifier
                fixed = re.sub(r"Counters\.Counter\s+(\w+);", r"uint256 private \1;", fixed, flags=re.IGNORECASE)
                
                # Step 4: Replace Counters method calls with direct operations
                # _tokenIdCounter.current() -> _tokenIdCounter (just the variable)
                fixed = re.sub(r"(\w+TokenIdCounter|\w+Counter)\.current\(\)", r"\1", fixed)
                
                # _tokenIdCounter.increment() -> _tokenIdCounter++
                fixed = re.sub(r"(\w+TokenIdCounter|\w+Counter)\.increment\(\)", r"\1++", fixed)
                
                # Step 5: Initialize counter in constructor if needed
                if "_tokenIdCounter" in fixed or "Counter" in fixed:
                    constructor_match = re.search(r"constructor\s*\([^)]*\)\s*\{([^}]+)\}", fixed, re.DOTALL)
                    if constructor_match:
                        constructor_body = constructor_match.group(1)
                        # Check if _tokenIdCounter exists and isn't initialized
                        if "uint256 private _tokenIdCounter" in fixed or "uint256 private tokenIdCounter" in fixed:
                            counter_var = "_tokenIdCounter" if "_tokenIdCounter" in fixed else "tokenIdCounter"
                            if f"{counter_var} = " not in constructor_body and f"{counter_var}++" not in constructor_body:
                                # Insert initialization at the end of constructor body (before closing brace)
                                # Find the closing brace position
                                brace_pos = fixed.find(constructor_match.group(0)) + len(constructor_match.group(0)) - 1
                                indent = "        "  # 8 spaces
                                init_line = f"\n{indent}{counter_var} = 0;"
                                # Insert before the closing brace
                                fixed = fixed[:brace_pos] + init_line + fixed[brace_pos:]
                                logger.info(f"🔧 Added {counter_var} = 0; initialization in constructor")
                
                if fixed != contract_code:
                    context["contract_code"] = fixed
                    logger.info("✅ Replaced deprecated Counters.sol with manual counter")
                    # CRITICAL: Also write back to file immediately
                    try:
                        from pathlib import Path
                        workspace = context.get("workspace_dir")
                        if workspace:
                            contract_name = context.get("contract_name", "Contract")
                            contracts_dir = Path(workspace) / "contracts"
                            contracts_dir.mkdir(parents=True, exist_ok=True)
                            contract_file = contracts_dir / f"{contract_name}.sol"
                            contract_file.write_text(fixed, encoding="utf-8")
                            logger.info(f"✅ Wrote fixed contract to: {contract_file}")
                    except Exception as write_err:
                        logger.warning(f"⚠️ Could not write fixed contract to file: {write_err}")
                    
                    return True, "Replaced deprecated Counters with manual counter and retrying"
                else:
                    logger.warning("⚠️ Counters fix detected but no changes made to contract code")
        
        # Missing import/remapping style errors -> allow retry after deps
        if (
            "file import callback not supported" in error_message
            or "source not found" in error_message
            or ("import" in error_message and "not found" in error_message)
        ):
            return True, "Retry after ensuring remappings and dependencies"
        
        # Fix override errors for ERC20 _beforeTokenTransfer
        if "override" in error_message and "_beforetokentransfer" in error_message and "erc20" in error_message:
            if contract_code:
                import re
                pattern = r'function _beforeTokenTransfer\([^)]+\)\s+internal\s+virtual\s+override\([^)]+\)\s*\{[^}]*super\._beforeTokenTransfer[^}]*\}'
                if re.search(pattern, contract_code, re.MULTILINE | re.DOTALL):
                    fixed_code = re.sub(pattern, '', contract_code, flags=re.MULTILINE | re.DOTALL).strip()
                    context["contract_code"] = fixed_code
                    logger.info("🔧 Fixed _beforeTokenTransfer override issue")
                    return True, "Removed invalid _beforeTokenTransfer override"
        
        # Solidity version mismatch - update foundry.toml and contract pragma
        if "invalid solc version" in error_message.lower() or "no solc version exists" in error_message.lower():
            # Extract required version from error message
            version_match = re.search(r'0\.8\.(\d+)', error_message)
            if version_match:
                required_minor = int(version_match.group(1))
                required_version = f"0.8.{required_minor}"
                
                # Update foundry.toml
                try:
                    from pathlib import Path
                    foundry_project_dir = context.get("workspace_dir") or Path(__file__).parent.parent.parent
                    foundry_toml = foundry_project_dir / "foundry.toml"
                    
                    if foundry_toml.exists():
                        toml_content = foundry_toml.read_text(encoding="utf-8")
                        # Update solc version
                        updated = re.sub(
                            r'solc\s*=\s*["\']0\.8\.\d+["\']',
                            f'solc = "{required_version}"',
                            toml_content
                        )
                        if updated != toml_content:
                            foundry_toml.write_text(updated, encoding="utf-8")
                            logger.info(f"✅ Updated foundry.toml: solc = {required_version}")
                except Exception as e:
                    logger.warning(f"⚠️  Could not update foundry.toml: {e}")
                
                # Update contract pragma if needed
                if contract_code:
                    # Update pragma solidity to match
                    updated_code = re.sub(
                        r'pragma solidity\s+[^;]+;',
                        f'pragma solidity ^{required_version};',
                        contract_code,
                        count=1
                    )
                    if updated_code != contract_code:
                        context["contract_code"] = updated_code
                        logger.info(f"✅ Updated contract pragma: ^0.8.{required_minor}")
                
                # Clear Foundry cache after version update
                try:
                    import subprocess
                    from pathlib import Path
                    foundry_project_dir = context.get("workspace_dir") or Path(__file__).parent.parent.parent
                    subprocess.run(
                        ["forge", "clean"],
                        cwd=foundry_project_dir,
                        capture_output=True,
                        timeout=30
                    )
                    logger.info("🧹 Cleared Foundry cache after Solidity version update")
                except Exception as e:
                    logger.warning(f"⚠️  Could not clear Foundry cache: {e}")
                
                return True, f"Updated Solidity version to {required_version} and retrying"
        
        # As a general fallback, try dependency detection and re-run
        if contract_code:
            from services.dependencies.dependency_manager import DependencyManager
            workspace = context.get("workspace_dir")
            if workspace:
                dep_manager = DependencyManager(workspace)
                deps = dep_manager.detect_dependencies(contract_code, "contract.sol")
                if deps:
                    await dep_manager.install_all_dependencies(deps)
        
        return True, "Retried compilation after dependency check"
    
    async def _auto_fix_network(self, parsed_error: ParsedError, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Auto-fix network error by retrying"""
        return True, "Network operation will be retried"
    
    async def _auto_fix_config(self, parsed_error: ParsedError, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Auto-fix missing config"""
        # Could create default config
        return False, "Config creation not yet automated"
    
    async def _auto_fix_timeout(self, parsed_error: ParsedError, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Auto-fix timeout by retrying with longer timeout"""
        return True, "Operation will be retried with longer timeout"


async def handle_error_with_retry(error_handler: SelfHealingErrorHandler, error: Exception,
                           context: Dict[str, Any], max_retries: int = 3) -> Tuple[bool, Optional[str]]:
    """
    Handle an error with automatic retry and self-healing.
    
    Args:
        error_handler: The error handler instance
        error: The exception that occurred
        context: Workflow context
        max_retries: Maximum number of retry attempts
        
    Returns:
        Tuple of (success, message)
    """
    error_message = str(error)
    parsed = error_handler.parse_error(error_message)
    
    logger.info(f"🔍 Error detected: {parsed.error_type.value} - {error_message[:100]}")
    
    if not parsed.automatable:
        logger.error(f"❌ Non-recoverable error: {error_message}")
        return False, error_message
    
    # Attempt auto-fix with retries
    for attempt in range(max_retries):
        logger.info(f"🔧 Auto-fix attempt {attempt + 1}/{max_retries}: {parsed.suggested_fix}")
        
        success, message = await error_handler.attempt_auto_fix(parsed, context)
        
        if success:
            logger.info(f"✅ Auto-fix successful: {message}")
            return True, message
        
        if attempt < max_retries - 1:
            logger.warning(f"⚠️ Auto-fix attempt {attempt + 1} failed, retrying...")
    
    logger.error(f"❌ Auto-fix failed after {max_retries} attempts")
    return False, f"Auto-fix failed: {parsed.suggested_fix}"

