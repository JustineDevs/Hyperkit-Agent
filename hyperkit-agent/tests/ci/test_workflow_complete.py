#!/usr/bin/env python3
"""
CI Test Suite for Complete Workflow

Tests full workflow from bare workspace: gen → deps → build → test → deploy
"""

import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add workspace to path
workspace_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(workspace_dir))

from core.agent.main import HyperKitAgent
from core.config.loader import get_config


class WorkflowCITest:
    """CI test suite for complete workflow"""
    
    def __init__(self):
        self.results: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "tests": [],
            "passed": 0,
            "failed": 0
        }
    
    async def run_all_tests(self) -> bool:
        """Run all CI tests"""
        print("\n" + "="*70)
        print("CI Workflow Test Suite")
        print("="*70 + "\n")
        
        # Initialize agent
        config = get_config().to_dict()
        agent = HyperKitAgent(config)
        
        # Test 1: Full workflow (test-only)
        print("Test 1: Complete workflow (test-only mode)")
        result1 = await self._test_full_workflow_test_only(agent)
        self._record_test("full_workflow_test_only", result1)
        
        # Test 2: Generation only
        print("\nTest 2: Contract generation")
        result2 = await self._test_generation(agent)
        self._record_test("generation", result2)
        
        # Test 3: Dependency detection
        print("\nTest 3: Dependency detection")
        result3 = await self._test_dependency_detection(agent)
        self._record_test("dependency_detection", result3)
        
        # Test 4: Compilation
        print("\nTest 4: Contract compilation")
        result4 = await self._test_compilation(agent)
        self._record_test("compilation", result4)
        
        # Test 5: Audit
        print("\nTest 5: Security audit")
        result5 = await self._test_audit(agent)
        self._record_test("audit", result5)
        
        # Print summary
        print("\n" + "="*70)
        print("Test Summary")
        print("="*70)
        print(f"Passed: {self.results['passed']}")
        print(f"Failed: {self.results['failed']}")
        print("="*70 + "\n")
        
        # Save results
        results_file = workspace_dir / "test_logs" / "ci_workflow_test.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"Results saved to: {results_file}")
        
        return self.results["failed"] == 0
    
    def _record_test(self, name: str, result: Dict[str, Any]):
        """Record test result"""
        passed = result.get("passed", False)
        if passed:
            print(f"✅ PASSED: {name}")
            self.results["passed"] += 1
        else:
            print(f"❌ FAILED: {name}")
            if result.get("error"):
                print(f"   Error: {result['error']}")
            self.results["failed"] += 1
        
        self.results["tests"].append({
            "name": name,
            "passed": passed,
            "error": result.get("error"),
            "details": result.get("details", {})
        })
    
    async def _test_full_workflow_test_only(self, agent: HyperKitAgent) -> Dict[str, Any]:
        """Test complete workflow in test-only mode"""
        try:
            result = await agent.run_workflow(
                user_prompt="Create a simple ERC20 token named TestToken",
                network="hyperion",
                test_only=True,
                upload_scope=None
            )
            
            if result.get("status") == "success":
                # Verify all stages completed
                stages = result.get("stages", [])
                if len(stages) >= 3:  # At least generation, compilation, audit
                    return {
                        "passed": True,
                        "details": {
                            "stages_completed": len(stages),
                            "contract_name": result.get("contract_name")
                        }
                    }
                else:
                    return {
                        "passed": False,
                        "error": f"Expected at least 3 stages, got {len(stages)}"
                    }
            else:
                return {
                    "passed": False,
                    "error": f"Workflow failed: {result.get('error', 'Unknown')}"
                }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    async def _test_generation(self, agent: HyperKitAgent) -> Dict[str, Any]:
        """Test contract generation"""
        try:
            result = await agent.generate_contract("Create an ERC20 token")
            
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
                    "error": f"Generation failed: {result.get('error', 'Unknown')}"
                }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    async def _test_dependency_detection(self, agent: HyperKitAgent) -> Dict[str, Any]:
        """Test dependency detection"""
        try:
            from services.dependencies.dependency_manager import DependencyManager
            
            dep_manager = DependencyManager(workspace_dir)
            
            test_code = '''
            pragma solidity ^0.8.20;
            import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
            contract TestToken is ERC20 {
                constructor() ERC20("Test", "TST") {}
            }
            '''
            
            deps = dep_manager.detect_dependencies(test_code, "TestToken.sol")
            
            if len(deps) > 0:
                return {
                    "passed": True,
                    "details": {
                        "dependencies_found": len(deps),
                        "dependency_names": [d.name for d in deps]
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
                "error": str(e)
            }
    
    async def _test_compilation(self, agent: HyperKitAgent) -> Dict[str, Any]:
        """Test contract compilation"""
        try:
            # Generate a simple contract first
            gen_result = await agent.generate_contract("Create a simple storage contract")
            
            if gen_result.get("status") != "success":
                return {
                    "passed": False,
                    "error": "Generation failed, cannot test compilation"
                }
            
            contract_code = gen_result["contract_code"]
            contract_name = gen_result.get("contract_name", "Contract")
            
            # Compile
            compile_result = await agent._compile_contract(contract_name, contract_code)
            
            if compile_result.get("success"):
                return {
                    "passed": True,
                    "details": {
                        "artifact_path": compile_result.get("artifact_path")
                    }
                }
            else:
                return {
                    "passed": False,
                    "error": f"Compilation failed: {compile_result.get('error', 'Unknown')}"
                }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    async def _test_audit(self, agent: HyperKitAgent) -> Dict[str, Any]:
        """Test security audit"""
        try:
            # Generate a contract
            gen_result = await agent.generate_contract("Create an ERC20 token")
            
            if gen_result.get("status") != "success":
                return {
                    "passed": False,
                    "error": "Generation failed, cannot test audit"
                }
            
            contract_code = gen_result["contract_code"]
            
            # Audit
            audit_result = await agent.audit_contract(contract_code)
            
            if audit_result.get("status") == "success":
                return {
                    "passed": True,
                    "details": {
                        "severity": audit_result.get("severity"),
                        "issues_count": len(audit_result.get("issues", []))
                    }
                }
            else:
                return {
                    "passed": False,
                    "error": f"Audit failed: {audit_result.get('error', 'Unknown')}"
                }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }


async def main():
    """Main entry point"""
    tester = WorkflowCITest()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

