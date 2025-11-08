"""
Tool JSON Schemas
Defines JSON schemas for all agent tools in OpenAI function calling format.
"""

from typing import Dict, Any


def get_tool_schemas() -> Dict[str, Dict[str, Any]]:
    """
    Get all tool schemas.
    
    Returns:
        Dictionary mapping tool names to their schemas
    """
    return {
        "generate_contract": {
            "name": "generate_contract",
            "description": "Create a smart contract from a high-level goal and context using AI",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal": {
                        "type": "string",
                        "description": "User's contract goal or requirement"
                    },
                    "context": {
                        "type": "string",
                        "description": "RAG context or template information"
                    },
                    "constraints": {
                        "type": "object",
                        "description": "Technical constraints (network, standards, etc.)",
                        "properties": {
                            "network": {"type": "string"},
                            "standards": {"type": "array", "items": {"type": "string"}},
                            "gas_optimization": {"type": "boolean"}
                        }
                    }
                },
                "required": ["goal"]
            }
        },
        "audit_contract": {
            "name": "audit_contract",
            "description": "Audit a smart contract for security vulnerabilities and best practices",
            "parameters": {
                "type": "object",
                "properties": {
                    "contract_path": {
                        "type": "string",
                        "description": "Path to contract file"
                    },
                    "contract_address": {
                        "type": "string",
                        "description": "Deployed contract address (optional)"
                    },
                    "network": {
                        "type": "string",
                        "description": "Blockchain network"
                    },
                    "tools": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Audit tools to use (slither, mythril, ai)"
                    }
                },
                "required": []
            }
        },
        "deploy_contract": {
            "name": "deploy_contract",
            "description": "Deploy a smart contract to a blockchain network",
            "parameters": {
                "type": "object",
                "properties": {
                    "contract_path": {
                        "type": "string",
                        "description": "Path to contract file"
                    },
                    "network": {
                        "type": "string",
                        "description": "Target blockchain network"
                    },
                    "constructor_args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Constructor arguments"
                    },
                    "private_key": {
                        "type": "string",
                        "description": "Private key for deployment (optional, uses env if not provided)"
                    }
                },
                "required": ["contract_path", "network"]
            }
        },
        "query_ipfs_rag": {
            "name": "query_ipfs_rag",
            "description": "Retrieve relevant context/templates from IPFS RAG system",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query or user prompt"
                    },
                    "scope": {
                        "type": "string",
                        "enum": ["official-only", "opt-in-community"],
                        "description": "RAG scope"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results"
                    }
                },
                "required": ["query"]
            }
        },
        "run_linter": {
            "name": "run_linter",
            "description": "Run linter and static analysis on contract code",
            "parameters": {
                "type": "object",
                "properties": {
                    "contract_path": {
                        "type": "string",
                        "description": "Path to contract file"
                    },
                    "checks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific checks to run"
                    }
                },
                "required": ["contract_path"]
            }
        },
        "analyze_dependencies": {
            "name": "analyze_dependencies",
            "description": "Analyze and install contract dependencies",
            "parameters": {
                "type": "object",
                "properties": {
                    "contract_path": {
                        "type": "string",
                        "description": "Path to contract file"
                    },
                    "auto_install": {
                        "type": "boolean",
                        "description": "Automatically install missing dependencies"
                    }
                },
                "required": ["contract_path"]
            }
        },
        "run_tests": {
            "name": "run_tests",
            "description": "Run Foundry tests for a contract",
            "parameters": {
                "type": "object",
                "properties": {
                    "contract_path": {
                        "type": "string",
                        "description": "Path to contract file"
                    },
                    "test_file": {
                        "type": "string",
                        "description": "Specific test file to run (optional)"
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "Verbose test output"
                    }
                },
                "required": ["contract_path"]
            }
        },
        "verify_contract": {
            "name": "verify_contract",
            "description": "Verify a deployed contract on blockchain explorer",
            "parameters": {
                "type": "object",
                "properties": {
                    "contract_address": {
                        "type": "string",
                        "description": "Deployed contract address"
                    },
                    "network": {
                        "type": "string",
                        "description": "Blockchain network"
                    },
                    "contract_path": {
                        "type": "string",
                        "description": "Path to contract source file"
                    },
                    "constructor_args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Constructor arguments used during deployment"
                    }
                },
                "required": ["contract_address", "network"]
            }
        },
        "revert_state": {
            "name": "revert_state",
            "description": "Revert workflow to a previous state",
            "parameters": {
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "Workflow ID to revert"
                    },
                    "stage": {
                        "type": "string",
                        "description": "Stage to revert to"
                    }
                },
                "required": ["workflow_id"]
            }
        },
        "save_result": {
            "name": "save_result",
            "description": "Save workflow result to persistent storage",
            "parameters": {
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "Workflow ID"
                    },
                    "result": {
                        "type": "object",
                        "description": "Result data to save"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["json", "yaml", "markdown"],
                        "description": "Output format"
                    }
                },
                "required": ["workflow_id", "result"]
            }
        }
    }

