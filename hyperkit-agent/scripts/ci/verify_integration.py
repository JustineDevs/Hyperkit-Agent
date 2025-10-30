#!/usr/bin/env python3
"""
Core System Integration Verification

Verifies that all core system components work together correctly.
Checks parameter flow, data sharing, and integration points.
"""

import sys
import inspect
from pathlib import Path
from typing import Dict, Any, List

# Add workspace to path
workspace_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(workspace_dir))


class IntegrationVerifier:
    """Verify core system integration"""
    
    def __init__(self):
        self.issues: List[Dict[str, Any]] = []
        self.verified: List[Dict[str, Any]] = []
    
    def verify_all(self) -> Dict[str, Any]:
        """Run all integration checks"""
        print("\n" + "="*70)
        print("Core System Integration Verification")
        print("="*70 + "\n")
        
        # 1. CLI to Agent Parameter Flow
        self._verify_cli_to_agent_flow()
        
        # 2. Agent to Orchestrator Parameter Flow
        self._verify_agent_to_orchestrator_flow()
        
        # 3. Orchestrator Stage Integration
        self._verify_orchestrator_stages()
        
        # 4. RAG System Integration
        self._verify_rag_integration()
        
        # 5. Dependency Manager Integration
        self._verify_dependency_integration()
        
        # 6. Deployer Integration
        self._verify_deployer_integration()
        
        # 7. Pinata Integration
        self._verify_pinata_integration()
        
        # Print summary
        print("\n" + "="*70)
        print("Verification Summary")
        print("="*70)
        print(f"PASSED: {len(self.verified)}")
        print(f"FAILED: {len(self.issues)}")
        
        if self.issues:
            print("\nIssues Found:")
            for issue in self.issues:
                print(f"  - {issue['component']}: {issue['issue']}")
        else:
            print("\nAll integration checks passed!")
        
        print("="*70 + "\n")
        
        return {
            "verified": self.verified,
            "issues": self.issues,
            "all_passed": len(self.issues) == 0
        }
    
    def _verify_cli_to_agent_flow(self):
        """Verify CLI parameters flow to agent"""
        try:
            from cli.commands.workflow import run_workflow
            from core.agent.main import HyperKitAgent
            
            # Check CLI function signature
            sig = inspect.signature(run_workflow)
            cli_params = set(sig.parameters.keys())
            
            # Check agent.run_workflow signature
            sig = inspect.signature(HyperKitAgent.run_workflow)
            agent_params = set(sig.parameters.keys())
            
            # Required parameters
            required = {'upload_scope', 'rag_scope', 'test_only', 'allow_insecure'}
            
            missing = required - agent_params
            if missing:
                self.issues.append({
                    "component": "CLI->Agent",
                    "issue": f"Missing parameters in agent.run_workflow(): {missing}",
                    "severity": "high"
                })
            else:
                self.verified.append({
                    "component": "CLI->Agent",
                    "check": "Parameter flow verified",
                    "params": list(required)
                })
        except Exception as e:
            self.issues.append({
                "component": "CLI->Agent",
                "issue": f"Verification failed: {e}",
                "severity": "high"
            })
    
    def _verify_agent_to_orchestrator_flow(self):
        """Verify agent parameters flow to orchestrator"""
        try:
            from core.agent.main import HyperKitAgent
            from core.workflow.workflow_orchestrator import WorkflowOrchestrator
            
            # Check agent.run_workflow signature
            agent_sig = inspect.signature(HyperKitAgent.run_workflow)
            agent_params = set(agent_sig.parameters.keys())
            
            # Check orchestrator.run_complete_workflow signature
            orch_sig = inspect.signature(WorkflowOrchestrator.run_complete_workflow)
            orch_params = set(orch_sig.parameters.keys())
            
            # Required parameters
            required = {'upload_scope', 'rag_scope', 'test_only', 'allow_insecure'}
            
            missing_in_agent = required - agent_params
            missing_in_orch = required - orch_params
            
            if missing_in_agent or missing_in_orch:
                self.issues.append({
                    "component": "Agent->Orchestrator",
                    "issue": f"Missing parameters - Agent: {missing_in_agent}, Orchestrator: {missing_in_orch}",
                    "severity": "high"
                })
            else:
                self.verified.append({
                    "component": "Agent->Orchestrator",
                    "check": "Parameter flow verified",
                    "params": list(required)
                })
        except Exception as e:
            self.issues.append({
                "component": "Agent->Orchestrator",
                "issue": f"Verification failed: {e}",
                "severity": "high"
            })
    
    def _verify_orchestrator_stages(self):
        """Verify orchestrator stage integration"""
        try:
            from core.workflow.workflow_orchestrator import WorkflowOrchestrator
            
            # Check that stages accept rag_scope parameter
            sig = inspect.signature(WorkflowOrchestrator._stage_input_parsing)
            if 'rag_scope' not in sig.parameters:
                self.issues.append({
                    "component": "Orchestrator Stages",
                    "issue": "_stage_input_parsing missing rag_scope parameter",
                    "severity": "high"
                })
            else:
                self.verified.append({
                    "component": "Orchestrator Stages",
                    "check": "_stage_input_parsing accepts rag_scope"
                })
            
            sig = inspect.signature(WorkflowOrchestrator._stage_generation)
            if 'rag_scope' not in sig.parameters:
                self.issues.append({
                    "component": "Orchestrator Stages",
                    "issue": "_stage_generation missing rag_scope parameter",
                    "severity": "high"
                })
            else:
                self.verified.append({
                    "component": "Orchestrator Stages",
                    "check": "_stage_generation accepts rag_scope"
                })
            
            sig = inspect.signature(WorkflowOrchestrator._stage_output)
            if 'upload_scope' not in sig.parameters:
                self.issues.append({
                    "component": "Orchestrator Stages",
                    "issue": "_stage_output missing upload_scope parameter",
                    "severity": "high"
                })
            else:
                self.verified.append({
                    "component": "Orchestrator Stages",
                    "check": "_stage_output accepts upload_scope"
                })
                
        except Exception as e:
            self.issues.append({
                "component": "Orchestrator Stages",
                "issue": f"Verification failed: {e}",
                "severity": "medium"
            })
    
    def _verify_rag_integration(self):
        """Verify RAG system integration"""
        try:
            from services.rag.ipfs_rag import IPFSRAG
            
            # Check retrieve method signature
            sig = inspect.signature(IPFSRAG.retrieve)
            if 'rag_scope' not in sig.parameters:
                self.issues.append({
                    "component": "RAG System",
                    "issue": "IPFSRAG.retrieve missing rag_scope parameter",
                    "severity": "high"
                })
            else:
                self.verified.append({
                    "component": "RAG System",
                    "check": "retrieve() accepts rag_scope parameter"
                })
                
        except Exception as e:
            self.issues.append({
                "component": "RAG System",
                "issue": f"Verification failed: {e}",
                "severity": "medium"
            })
    
    def _verify_dependency_integration(self):
        """Verify dependency manager integration"""
        try:
            from services.dependencies.dependency_manager import DependencyManager
            
            # Check that remapping update method exists
            if not hasattr(DependencyManager, '_update_remappings'):
                self.issues.append({
                    "component": "Dependency Manager",
                    "issue": "_update_remappings method missing",
                    "severity": "medium"
                })
            else:
                self.verified.append({
                    "component": "Dependency Manager",
                    "check": "_update_remappings method exists"
                })
                
        except Exception as e:
            self.issues.append({
                "component": "Dependency Manager",
                "issue": f"Verification failed: {e}",
                "severity": "low"
            })
    
    def _verify_deployer_integration(self):
        """Verify deployer integration"""
        try:
            from services.deployment.deployer import MultiChainDeployer
            from services.deployment.constructor_parser import ConstructorArgumentParser
            
            # Check that deployer uses constructor parser
            deployer_source = inspect.getsource(MultiChainDeployer.deploy)
            if 'ConstructorArgumentParser' not in deployer_source:
                self.issues.append({
                    "component": "Deployer",
                    "issue": "Deployer may not be using ConstructorArgumentParser",
                    "severity": "medium"
                })
            else:
                self.verified.append({
                    "component": "Deployer",
                    "check": "Uses ConstructorArgumentParser"
                })
                
        except Exception as e:
            self.issues.append({
                "component": "Deployer",
                "issue": f"Verification failed: {e}",
                "severity": "low"
            })
    
    def _verify_pinata_integration(self):
        """Verify Pinata integration"""
        try:
            from services.storage.dual_scope_pinata import PinataScopeClient, UploadScope
            
            # Check that auto-upload uses PinataScopeClient
            from core.workflow.workflow_orchestrator import WorkflowOrchestrator
            source = inspect.getsource(WorkflowOrchestrator._auto_upload_artifacts)
            
            if 'PinataScopeClient' not in source:
                self.issues.append({
                    "component": "Pinata Integration",
                    "issue": "_auto_upload_artifacts may not use PinataScopeClient",
                    "severity": "high"
                })
            else:
                self.verified.append({
                    "component": "Pinata Integration",
                    "check": "Uses PinataScopeClient"
                })
            
            # Check moderation integration
            if 'CommunityModeration' in source:
                self.verified.append({
                    "component": "Pinata Integration",
                    "check": "Integrated with CommunityModeration"
                })
            
            if 'CommunityAnalytics' in source:
                self.verified.append({
                    "component": "Pinata Integration",
                    "check": "Integrated with CommunityAnalytics"
                })
                
        except Exception as e:
            self.issues.append({
                "component": "Pinata Integration",
                "issue": f"Verification failed: {e}",
                "severity": "medium"
            })


def main():
    """Main entry point"""
    verifier = IntegrationVerifier()
    results = verifier.verify_all()
    
    # Save results
    import json
    results_file = workspace_dir / "test_logs" / "integration_verification.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    sys.exit(0 if results["all_passed"] else 1)


if __name__ == "__main__":
    main()

