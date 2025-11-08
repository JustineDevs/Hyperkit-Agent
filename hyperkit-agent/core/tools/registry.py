"""
Tool Registry
Manages tool registration, discovery, and execution.
"""

import logging
from typing import Dict, Optional, List
from core.tools.base import Tool, ToolResult
from core.tools.schemas import get_tool_schemas

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry for managing all available tools.
    Provides tool discovery, validation, and schema access.
    """
    
    def __init__(self):
        """Initialize tool registry"""
        self._tools: Dict[str, Tool] = {}
        self._schemas = get_tool_schemas()
    
    def register(self, tool: Tool):
        """
        Register a tool.
        
        Args:
            tool: Tool instance to register
            
        Raises:
            ValueError: If tool name already exists
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
    
    def get(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance if found, None otherwise
        """
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """
        List all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
    
    def get_schema(self, name: str) -> Optional[Dict]:
        """
        Get JSON schema for a tool.
        
        Args:
            name: Tool name
            
        Returns:
            Tool schema if found, None otherwise
        """
        if name in self._tools:
            return self._tools[name].get_schema()
        return self._schemas.get(name)
    
    def get_all_schemas(self) -> Dict[str, Dict]:
        """
        Get all tool schemas.
        
        Returns:
            Dictionary mapping tool names to schemas
        """
        schemas = {}
        for name, tool in self._tools.items():
            schemas[name] = tool.get_schema()
        # Also include schemas for tools not yet registered
        for name, schema in self._schemas.items():
            if name not in schemas:
                schemas[name] = schema
        return schemas


class ToolExecutor:
    """
    Executes tools with validation and error handling.
    """
    
    def __init__(self, registry: ToolRegistry):
        """
        Initialize tool executor.
        
        Args:
            registry: ToolRegistry instance
        """
        self.registry = registry
    
    async def execute(self, tool_name: str, parameters: Dict) -> ToolResult:
        """
        Execute a tool with given parameters.
        
        Args:
            tool_name: Name of tool to execute
            parameters: Tool parameters
            
        Returns:
            ToolResult with execution outcome
        """
        tool = self.registry.get(tool_name)
        
        if not tool:
            return ToolResult(
                success=False,
                output={},
                error=f"Tool '{tool_name}' not found",
                error_type="ToolNotFoundError"
            )
        
        # Validate parameters
        is_valid, error_msg = tool.validate(parameters)
        if not is_valid:
            return ToolResult(
                success=False,
                output={},
                error=f"Invalid parameters: {error_msg}",
                error_type="ValidationError"
            )
        
        # Execute tool
        try:
            result = await tool.execute(**parameters)
            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name}", exc_info=True)
            return ToolResult(
                success=False,
                output={},
                error=str(e),
                error_type=type(e).__name__
            )

