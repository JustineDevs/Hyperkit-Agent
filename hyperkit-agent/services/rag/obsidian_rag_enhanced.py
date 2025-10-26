"""
Enhanced Obsidian RAG Service with MCP Support

This service provides integration with Obsidian vaults through:
1. Local REST API plugin
2. MCP (Model Context Protocol) server
3. Direct file system access (fallback)

Supports both local and Docker-based MCP setups.
"""

import os
import json
import logging
import requests
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ObsidianRAGEnhanced:
    """
    Enhanced Obsidian RAG service with MCP support.
    
    Features:
    - Local REST API integration
    - MCP server support (local and Docker)
    - Intelligent content retrieval
    - Connection testing and validation
    - Fallback mechanisms
    """
    
    def __init__(self, vault_path: str = "", use_mcp: bool = True, mcp_config: dict = None):
        """
        Initialize Obsidian RAG service.
        
        Args:
            vault_path: Path to Obsidian vault (fallback)
            use_mcp: Whether to use MCP server
            mcp_config: MCP configuration overrides
        """
        self.use_mcp = use_mcp
        self.vault_path = vault_path or os.getenv("OBSIDIAN_VAULT_PATH", "")
        self.mcp_config = mcp_config or {}
        
        # MCP Configuration
        if use_mcp:
            self._setup_mcp_connection()
        else:
            self._setup_direct_access()
    
    def _setup_mcp_connection(self):
        """Setup MCP connection (local or Docker)."""
        try:
            # Get configuration from environment
            self.api_key = os.getenv("OBSIDIAN_API_KEY")
            self.mcp_enabled = os.getenv("MCP_ENABLED", "false").lower() == "true"
            self.mcp_docker = os.getenv("MCP_DOCKER", "false").lower() == "true"
            
            if not self.api_key:
                raise ValueError("OBSIDIAN_API_KEY not set in .env")
            
            # Determine API base URL
            if self.mcp_docker:
                # Docker setup
                mcp_host = os.getenv("MCP_HOST", "localhost")
                mcp_port = os.getenv("MCP_PORT", "3333")
                self.api_base_url = f"http://{mcp_host}:{mcp_port}"
                logger.info(f"Using Docker MCP server: {self.api_base_url}")
            else:
                # Local setup
                self.api_base_url = os.getenv("OBSIDIAN_API_BASE_URL", "http://localhost:27124")
                logger.info(f"Using local Obsidian REST API: {self.api_base_url}")
            
            # Test connection
            self._test_connection()
            
        except Exception as e:
            logger.error(f"Failed to setup MCP connection: {e}")
            logger.warning("Falling back to direct file access")
            self._setup_direct_access()
    
    def _setup_direct_access(self):
        """Setup direct file system access as fallback."""
        self.use_mcp = False
        self.api_base_url = None
        self.api_key = None
        
        if not self.vault_path or not Path(self.vault_path).exists():
            logger.warning("No valid vault path configured for direct access")
            return
        
        logger.info(f"Using direct file access: {self.vault_path}")
    
    def _test_connection(self):
        """Test Obsidian API connection."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            # Test basic connection
            response = requests.get(
                f"{self.api_base_url}/vault/",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info("✅ Obsidian MCP connection successful")
                return True
            else:
                raise ConnectionError(f"API returned {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Obsidian MCP connection failed: {e}")
            raise
    
    async def retrieve(self, query: str, max_results: int = 5) -> str:
        """
        Retrieve relevant content from Obsidian vault.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            Concatenated relevant content
        """
        try:
            if self.use_mcp:
                return await self._retrieve_via_mcp(query, max_results)
            else:
                return await self._retrieve_via_filesystem(query, max_results)
                
        except Exception as e:
            logger.error(f"Content retrieval failed: {e}")
            return f"Error retrieving content: {e}"
    
    async def _retrieve_via_mcp(self, query: str, max_results: int) -> str:
        """Retrieve content via MCP server."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            # Search for relevant files
            search_params = {
                "query": query,
                "limit": max_results,
                "include_content": True
            }
            
            response = requests.get(
                f"{self.api_base_url}/search",
                headers=headers,
                params=search_params,
                timeout=10
            )
            
            if response.status_code != 200:
                raise Exception(f"Search failed: {response.status_code}")
            
            results = response.json()
            
            # Extract content from results
            content_parts = []
            for result in results.get("results", []):
                file_path = result.get("path", "")
                content = result.get("content", "")
                
                if content:
                    content_parts.append(f"## {file_path}\n{content}\n")
            
            if content_parts:
                combined_content = "\n".join(content_parts)
                logger.info(f"Retrieved {len(content_parts)} files via MCP")
                return combined_content
            else:
                logger.warning("No content found via MCP")
                return "No relevant content found"
                
        except Exception as e:
            logger.error(f"MCP retrieval failed: {e}")
            raise
    
    async def _retrieve_via_filesystem(self, query: str, max_results: int) -> str:
        """Retrieve content via direct file system access."""
        try:
            if not self.vault_path or not Path(self.vault_path).exists():
                return "Vault path not configured or accessible"
            
            vault_path = Path(self.vault_path)
            content_parts = []
            
            # Search through markdown files
            for md_file in vault_path.rglob("*.md"):
                try:
                    content = md_file.read_text(encoding='utf-8')
                    
                    # Simple keyword matching
                    if any(keyword.lower() in content.lower() for keyword in query.split()):
                        content_parts.append(f"## {md_file.name}\n{content[:1000]}...\n")
                        
                        if len(content_parts) >= max_results:
                            break
                            
                except Exception as e:
                    logger.warning(f"Error reading {md_file}: {e}")
                    continue
            
            if content_parts:
                combined_content = "\n".join(content_parts)
                logger.info(f"Retrieved {len(content_parts)} files via filesystem")
                return combined_content
            else:
                logger.warning("No content found via filesystem")
                return "No relevant content found"
                
        except Exception as e:
            logger.error(f"Filesystem retrieval failed: {e}")
            raise
    
    async def get_vault_info(self) -> Dict[str, Any]:
        """Get vault information."""
        try:
            if self.use_mcp:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = requests.get(
                    f"{self.api_base_url}/vault/",
                    headers=headers,
                    timeout=5
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"Failed to get vault info: {response.status_code}")
            else:
                # Return filesystem-based info
                vault_path = Path(self.vault_path)
                if vault_path.exists():
                    md_files = list(vault_path.rglob("*.md"))
                    return {
                        "path": str(vault_path),
                        "file_count": len(md_files),
                        "access_method": "filesystem"
                    }
                else:
                    return {"error": "Vault path not accessible"}
                    
        except Exception as e:
            logger.error(f"Failed to get vault info: {e}")
            return {"error": str(e)}
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection and return status."""
        try:
            if self.use_mcp:
                self._test_connection()
                vault_info = asyncio.run(self.get_vault_info())
                return {
                    "status": "success",
                    "method": "mcp",
                    "api_url": self.api_base_url,
                    "vault_info": vault_info
                }
            else:
                vault_path = Path(self.vault_path)
                if vault_path.exists():
                    md_files = list(vault_path.rglob("*.md"))
                    return {
                        "status": "success",
                        "method": "filesystem",
                        "vault_path": str(vault_path),
                        "file_count": len(md_files)
                    }
                else:
                    return {
                        "status": "error",
                        "method": "filesystem",
                        "error": "Vault path not accessible"
                    }
                    
        except Exception as e:
            return {
                "status": "error",
                "method": "mcp" if self.use_mcp else "filesystem",
                "error": str(e)
            }


# Convenience function for easy testing
async def test_obsidian_rag():
    """Test function for Obsidian RAG connection."""
    try:
        rag = ObsidianRAGEnhanced(use_mcp=True)
        
        # Test connection
        connection_status = rag.test_connection()
        print(f"Connection Status: {connection_status}")
        
        if connection_status["status"] == "success":
            # Test retrieval
            result = await rag.retrieve("test query", max_results=3)
            print(f"Retrieval Test: {len(result)} characters returned")
            return True
        else:
            print(f"Connection failed: {connection_status}")
            return False
            
    except Exception as e:
        print(f"Test failed: {e}")
        return False


if __name__ == "__main__":
    # Run test
    success = asyncio.run(test_obsidian_rag())
    print(f"✅ Obsidian RAG test: {'PASSED' if success else 'FAILED'}")