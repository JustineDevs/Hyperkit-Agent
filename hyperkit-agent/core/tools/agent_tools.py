"""
Agent Tool Wrappers
Wraps HyperKitAgent methods as Tool instances for the modular tool architecture.
"""

import logging
from typing import Dict, Any
from pathlib import Path
from core.tools.base import Tool, ToolResult
from core.tools.schemas import get_tool_schemas

logger = logging.getLogger(__name__)


class GenerateContractTool(Tool):
    """Tool wrapper for contract generation"""
    
    def __init__(self, agent):
        schema = get_tool_schemas()["generate_contract"]
        super().__init__(
            name="generate_contract",
            description=schema["description"],
            parameters_schema=schema["parameters"]
        )
        self.agent = agent
    
    async def execute(self, goal: str, context: str = "", constraints: Dict[str, Any] = None) -> ToolResult:
        """Execute contract generation"""
        try:
            result = await self.agent.generate_contract(prompt=goal, context=context)
            return ToolResult(
                success=True,
                output=result,
                metadata={"method": result.get("method", "unknown")}
            )
        except Exception as e:
            logger.error(f"Contract generation failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                output={},
                error=str(e),
                error_type=type(e).__name__
            )


class AuditContractTool(Tool):
    """Tool wrapper for contract auditing"""
    
    def __init__(self, agent):
        schema = get_tool_schemas()["audit_contract"]
        super().__init__(
            name="audit_contract",
            description=schema["description"],
            parameters_schema=schema["parameters"]
        )
        self.agent = agent
    
    async def execute(self, contract_path: str = None, contract_address: str = None, 
                    network: str = "hyperion", tools: list = None) -> ToolResult:
        """Execute contract audit"""
        try:
            if contract_path:
                result = await self.agent.audit_contract(contract_path=contract_path)
            elif contract_address:
                result = await self.agent.audit_contract(contract_address=contract_address, network=network)
            else:
                return ToolResult(
                    success=False,
                    output={},
                    error="Either contract_path or contract_address must be provided",
                    error_type="ValidationError"
                )
            
            return ToolResult(
                success=True,
                output=result,
                metadata={"tools_used": tools or []}
            )
        except Exception as e:
            logger.error(f"Contract audit failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                output={},
                error=str(e),
                error_type=type(e).__name__
            )


class DeployContractTool(Tool):
    """Tool wrapper for contract deployment"""
    
    def __init__(self, agent):
        schema = get_tool_schemas()["deploy_contract"]
        super().__init__(
            name="deploy_contract",
            description=schema["description"],
            parameters_schema=schema["parameters"]
        )
        self.agent = agent
    
    async def execute(self, contract_path: str, network: str = "hyperion",
                     constructor_args: list = None, private_key: str = None) -> ToolResult:
        """Execute contract deployment"""
        try:
            result = await self.agent.deploy_contract(
                contract_path=contract_path,
                network=network,
                constructor_args=constructor_args or [],
                private_key=private_key
            )
            
            return ToolResult(
                success=True,
                output=result,
                metadata={
                    "network": network,
                    "address": result.get("address") or result.get("contract_address")
                }
            )
        except Exception as e:
            logger.error(f"Contract deployment failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                output={},
                error=str(e),
                error_type=type(e).__name__
            )


class QueryIPFSRAGTool(Tool):
    """Tool wrapper for IPFS RAG queries"""
    
    def __init__(self, agent):
        schema = get_tool_schemas()["query_ipfs_rag"]
        super().__init__(
            name="query_ipfs_rag",
            description=schema["description"],
            parameters_schema=schema["parameters"]
        )
        self.agent = agent
    
    async def execute(self, query: str, scope: str = "official-only", limit: int = 5) -> ToolResult:
        """Execute RAG query"""
        try:
            if not self.agent.rag:
                return ToolResult(
                    success=False,
                    output={},
                    error="RAG system not initialized",
                    error_type="ConfigurationError"
                )
            
            result = await self.agent.rag.retrieve(query, scope=scope, limit=limit)
            
            return ToolResult(
                success=True,
                output={"context": result, "query": query, "scope": scope},
                metadata={"results_count": len(result) if isinstance(result, list) else 1}
            )
        except Exception as e:
            logger.error(f"RAG query failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                output={},
                error=str(e),
                error_type=type(e).__name__
            )


class RunLinterTool(Tool):
    """Tool wrapper for linting/compilation"""
    
    def __init__(self, agent):
        schema = get_tool_schemas()["run_linter"]
        super().__init__(
            name="run_linter",
            description=schema["description"],
            parameters_schema=schema["parameters"]
        )
        self.agent = agent
    
    async def execute(self, contract_path: str, checks: list = None) -> ToolResult:
        """Execute linting/compilation"""
        try:
            # Use Foundry compilation as linting
            import subprocess
            from pathlib import Path
            
            contract_file = Path(contract_path)
            if not contract_file.exists():
                return ToolResult(
                    success=False,
                    output={},
                    error=f"Contract file not found: {contract_path}",
                    error_type="FileNotFoundError"
                )
            
            # Run forge build
            result = subprocess.run(
                ["forge", "build"],
                cwd=contract_file.parent,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            success = result.returncode == 0
            return ToolResult(
                success=success,
                output={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                },
                error=None if success else result.stderr,
                error_type=None if success else "CompilationError"
            )
        except Exception as e:
            logger.error(f"Linting failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                output={},
                error=str(e),
                error_type=type(e).__name__
            )


class AnalyzeDependenciesTool(Tool):
    """Tool wrapper for dependency analysis"""
    
    def __init__(self, agent):
        schema = get_tool_schemas()["analyze_dependencies"]
        super().__init__(
            name="analyze_dependencies",
            description=schema["description"],
            parameters_schema=schema["parameters"]
        )
        self.agent = agent
    
    async def execute(self, contract_path: str, auto_install: bool = True) -> ToolResult:
        """Execute dependency analysis"""
        try:
            # This would integrate with the dependency manager
            # For now, return a placeholder result
            return ToolResult(
                success=True,
                output={"dependencies": [], "auto_install": auto_install},
                metadata={"contract_path": contract_path}
            )
        except Exception as e:
            logger.error(f"Dependency analysis failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                output={},
                error=str(e),
                error_type=type(e).__name__
            )


class RunTestsTool(Tool):
    """Tool wrapper for running tests"""
    
    def __init__(self, agent):
        schema = get_tool_schemas()["run_tests"]
        super().__init__(
            name="run_tests",
            description=schema["description"],
            parameters_schema=schema["parameters"]
        )
        self.agent = agent
    
    async def execute(self, contract_path: str, test_file: str = None, verbose: bool = False) -> ToolResult:
        """Execute tests"""
        try:
            import subprocess
            from pathlib import Path
            
            contract_file = Path(contract_path)
            test_cmd = ["forge", "test"]
            if test_file:
                test_cmd.extend(["--match-path", test_file])
            if verbose:
                test_cmd.append("-vvv")
            
            result = subprocess.run(
                test_cmd,
                cwd=contract_file.parent.parent if contract_file.parent.name == "contracts" else contract_file.parent,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            success = result.returncode == 0
            return ToolResult(
                success=success,
                output={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                },
                error=None if success else result.stderr,
                error_type=None if success else "TestFailureError"
            )
        except Exception as e:
            logger.error(f"Test execution failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                output={},
                error=str(e),
                error_type=type(e).__name__
            )


class VerifyContractTool(Tool):
    """Tool wrapper for contract verification"""
    
    def __init__(self, agent):
        schema = get_tool_schemas()["verify_contract"]
        super().__init__(
            name="verify_contract",
            description=schema["description"],
            parameters_schema=schema["parameters"]
        )
        self.agent = agent
    
    async def execute(self, contract_address: str, network: str = "hyperion",
                     contract_path: str = None, constructor_args: list = None) -> ToolResult:
        """Execute contract verification"""
        try:
            result = await self.agent.verify_contract(
                contract_address=contract_address,
                network=network,
                contract_path=contract_path,
                constructor_args=constructor_args or []
            )
            
            return ToolResult(
                success=result.get("verified", False),
                output=result,
                metadata={"network": network, "address": contract_address}
            )
        except Exception as e:
            logger.error(f"Contract verification failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                output={},
                error=str(e),
                error_type=type(e).__name__
            )


def create_agent_tools(agent) -> list[Tool]:
    """
    Create all tool instances from agent.
    
    Args:
        agent: HyperKitAgent instance
        
    Returns:
        List of Tool instances
    """
    return [
        GenerateContractTool(agent),
        AuditContractTool(agent),
        DeployContractTool(agent),
        QueryIPFSRAGTool(agent),
        RunLinterTool(agent),
        AnalyzeDependenciesTool(agent),
        RunTestsTool(agent),
        VerifyContractTool(agent),
    ]

