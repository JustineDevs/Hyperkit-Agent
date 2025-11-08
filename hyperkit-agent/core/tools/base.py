"""
Base Tool Interface
Defines the base Tool class that all agent tools must implement.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Result from tool execution"""
    success: bool
    output: Dict[str, Any]
    error: Optional[str] = None
    error_type: Optional[str] = None
    metadata: Dict[str, Any] = None


class Tool(ABC):
    """
    Base class for all agent tools.
    Tools are modular, reusable functions that the agent can invoke.
    """
    
    def __init__(self, name: str, description: str, parameters_schema: Dict[str, Any]):
        """
        Initialize tool.
        
        Args:
            name: Tool name (must be unique)
            description: Human-readable description of what the tool does
            parameters_schema: JSON schema for tool parameters
        """
        self.name = name
        self.description = description
        self.parameters_schema = parameters_schema
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool parameters (validated against schema)
            
        Returns:
            ToolResult with execution outcome
        """
        pass
    
    def validate(self, parameters: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate parameters against schema.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            (is_valid, error_message)
        """
        try:
            import jsonschema
            jsonschema.validate(instance=parameters, schema=self.parameters_schema)
            return True, None
        except jsonschema.ValidationError as e:
            return False, str(e)
        except ImportError:
            # Fallback validation if jsonschema not available
            logger.warning("jsonschema not available, skipping validation")
            return True, None
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get JSON schema for this tool (OpenAI function calling format).
        
        Returns:
            Dictionary with name, description, and parameters
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters_schema
        }

