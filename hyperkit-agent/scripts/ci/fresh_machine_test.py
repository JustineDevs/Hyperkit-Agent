#!/usr/bin/env python3
"""
Fresh Machine Test Script

Simulates a fresh environment to verify workflow works on clean installations.
Tests all critical functionality without assuming existing dependencies or state.
"""

import sys
import subprocess
import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class FreshMachineTester:
    """Test workflow on a fresh machine environment"""
    
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = Path(workspace_dir)
        self.test_dir = self.workspace_dir / ".fresh_test"
        self.results: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "tests": [],
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }
    
    def run(self) -> bool:
        """Run all fresh machine tests"""
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}Fresh Machine Test Suite{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        # Setup test environment
        print(f"{YELLOW}Setting up test environment...{RESET}")
        self._setup_test_env()
        
        # Run tests
        tests = [
            ("check_python", self._test_python_installed),
            ("check_foundry", self._test_foundry_installed),
            ("check_npm", self._test_npm_installed),
            ("test_workflow_generation", self._test_workflow_generation),
            ("test_dependency_detection", self._test_dependency_detection),
            ("test_compilation", self._test_compilation),
        ]
        
        for test_name, test_func in tests:
            print(f"\n{YELLOW}Running: {test_name}{RESET}")
            try:
                result = test_func()
                if result["passed"]:
                    print(f"{GREEN}✅ PASSED: {test_name}{RESET}")
                    self.results["passed"] += 1
                else:
                    print(f"{RED}❌ FAILED: {test_name}{RESET}")
                    if result.get("error"):
                        print(f"   {RED}Error: {result['error']}{RESET}")
                    self.results["failed"] += 1
                self.results["tests"].append({
                    "name": test_name,
                    "passed": result["passed"],
                    "error": result.get("error"),
                    "details": result.get("details", {})
                })
            except Exception as e:
                print(f"{RED}❌ ERROR: {test_name} - {e}{RESET}")
                self.results["tests"].append({
                    "name": test_name,
                    "passed": False,
                    "error": str(e)
                })
                self.results["failed"] += 1
        
        # Cleanup
        self._cleanup()
        
        # Print summary
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}Test Summary{RESET}")
        print(f"{BLUE}{'='*70}{RESET}")
        print(f"{GREEN}Passed: {self.results['passed']}{RESET}")
        print(f"{RED}Failed: {self.results['failed']}{RESET}")
        print(f"{YELLOW}Skipped: {self.results['skipped']}{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        # Save results
        results_file = self.workspace_dir / "test_logs" / "fresh_machine_test.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"Results saved to: {results_file}")
        
        return self.results["failed"] == 0
    
    def _setup_test_env(self):
        """Setup isolated test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(parents=True, exist_ok=True)
    
    def _cleanup(self):
        """Cleanup test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def _run_command(self, cmd: List[str], cwd: Path = None, capture_output: bool = True) -> Dict[str, Any]:
        """Run a command and return result"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.workspace_dir,
                capture_output=capture_output,
                text=True,
                timeout=60
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out",
                "stdout": "",
                "stderr": "",
                "returncode": -1
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"Command not found: {cmd[0]}",
                "stdout": "",
                "stderr": "",
                "returncode": -1
            }
    
    def _test_python_installed(self) -> Dict[str, Any]:
        """Test Python is installed and accessible"""
        result = self._run_command(["python", "--version"])
        if result["success"]:
            return {
                "passed": True,
                "details": {"version": result["stdout"].strip()}
            }
        else:
            # Try python3
            result = self._run_command(["python3", "--version"])
            if result["success"]:
                return {
                    "passed": True,
                    "details": {"version": result["stdout"].strip()}
                }
            return {
                "passed": False,
                "error": "Python not found. Please install Python 3.8+"
            }
    
    def _test_foundry_installed(self) -> Dict[str, Any]:
        """Test Foundry is installed"""
        result = self._run_command(["forge", "--version"])
        if result["success"]:
            return {
                "passed": True,
                "details": {"version": result["stdout"].strip()}
            }
        else:
            return {
                "passed": False,
                "error": "Foundry not found. Install from: https://book.getfoundry.sh/getting-started/installation"
            }
    
    def _test_npm_installed(self) -> Dict[str, Any]:
        """Test npm is installed"""
        result = self._run_command(["npm", "--version"])
        if result["success"]:
            return {
                "passed": True,
                "details": {"version": result["stdout"].strip()}
            }
        else:
            return {
                "passed": False,
                "error": "npm not found. Install Node.js from: https://nodejs.org/"
            }
    
    def _test_workflow_generation(self) -> Dict[str, Any]:
        """Test basic workflow generation"""
        try:
            # Import agent
            sys.path.insert(0, str(self.workspace_dir))
            from core.agent.main import HyperKitAgent
            from core.config.loader import get_config
            
            config = get_config().to_dict()
            agent = HyperKitAgent(config)
            
            # Test generation (simple prompt)
            import asyncio
            result = asyncio.run(agent.generate_contract("Create a simple ERC20 token"))
            
            if result.get("status") == "success" and result.get("contract_code"):
                return {
                    "passed": True,
                    "details": {
                        "contract_name": result.get("contract_name"),
                        "code_length": len(result.get("contract_code", ""))
                    }
                }
            else:
                return {
                    "passed": False,
                    "error": f"Generation failed: {result.get('error', 'Unknown error')}"
                }
        except Exception as e:
            return {
                "passed": False,
                "error": f"Test failed: {str(e)}"
            }
    
    def _test_dependency_detection(self) -> Dict[str, Any]:
        """Test dependency detection"""
        try:
            sys.path.insert(0, str(self.workspace_dir))
            from services.dependencies.dependency_manager import DependencyManager
            
            dep_manager = DependencyManager(self.workspace_dir)
            
            # Test contract with OpenZeppelin import
            test_code = '''
            pragma solidity ^0.8.20;
            import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
            contract TestToken is ERC20 {
                constructor() ERC20("Test", "TST") {}
            }
            '''
            
            deps = dep_manager.detect_dependencies(test_code, "TestToken.sol")
            
            if len(deps) > 0:
                ozeppelin_found = any("openzeppelin" in dep.name.lower() for dep in deps)
                return {
                    "passed": True,
                    "details": {
                        "dependencies_found": len(deps),
                        "openzeppelin_detected": ozeppelin_found
                    }
                }
            else:
                return {
                    "passed": False,
                    "error": "No dependencies detected"
                }
        except Exception as e:
            return {
                "passed": False,
                "error": f"Dependency detection failed: {str(e)}"
            }
    
    def _test_compilation(self) -> Dict[str, Any]:
        """Test contract compilation"""
        try:
            # Create a simple test contract
            test_contract = '''
            pragma solidity ^0.8.20;
            contract SimpleTest {
                uint256 public value;
                function setValue(uint256 _value) public {
                    value = _value;
                }
            }
            '''
            
            test_file = self.test_dir / "SimpleTest.sol"
            with open(test_file, 'w') as f:
                f.write(test_contract)
            
            # Try to compile with forge
            result = self._run_command(
                ["forge", "build", "--contracts", str(test_file.parent)],
                cwd=self.test_dir
            )
            
            if result["success"]:
                return {
                    "passed": True,
                    "details": {"compilation": "success"}
                }
            else:
                return {
                    "passed": False,
                    "error": f"Compilation failed: {result.get('stderr', 'Unknown error')}"
                }
        except Exception as e:
            return {
                "passed": False,
                "error": f"Compilation test failed: {str(e)}"
            }


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        workspace_dir = Path(sys.argv[1])
    else:
        script_dir = Path(__file__).resolve().parent.parent.parent
        workspace_dir = script_dir
    
    tester = FreshMachineTester(workspace_dir)
    success = tester.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

