"""
MCP Docker Client for Obsidian Integration
Provides advanced Obsidian connectivity through Docker-based MCP server
"""

import asyncio
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, AsyncGenerator
import docker
from docker.errors import DockerException

logger = logging.getLogger(__name__)

class ObsidianMCPClient:
    """MCP Docker client for advanced Obsidian integration"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MCP Docker client
        
        Args:
            config: MCP configuration dictionary
        """
        self.config = config
        self.docker_client = None
        self.container = None
        self.container_name = "hyperkit-obsidian-mcp"
        self.is_running = False
        
        # MCP server configuration
        self.obsidian_host = config.get("obsidian_host", "host.docker.internal")
        self.obsidian_api_key = config.get("obsidian_api_key")
        self.vault_path = config.get("vault_path", "/vault")
        
        # Docker configuration
        self.docker_image = "mcp/obsidian:latest"
        self.port_mapping = {"27125": 27125}
        
    async def initialize(self) -> bool:
        """
        Initialize Docker client and MCP server
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Initialize Docker client
            self.docker_client = docker.from_env()
            
            # Check if Docker is running
            if not await self._check_docker_available():
                logger.error("Docker is not available or not running")
                return False
            
            # Build or pull MCP image
            if not await self._ensure_mcp_image():
                logger.error("Failed to prepare MCP Docker image")
                return False
            
            # Start MCP container
            if not await self._start_mcp_container():
                logger.error("Failed to start MCP container")
                return False
            
            # Wait for container to be ready
            if not await self._wait_for_container_ready():
                logger.error("MCP container failed to become ready")
                return False
            
            self.is_running = True
            logger.info("MCP Docker client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP Docker client: {e}")
            return False
    
    async def _check_docker_available(self) -> bool:
        """Check if Docker is available and running"""
        try:
            self.docker_client.ping()
            return True
        except DockerException:
            return False
    
    async def _ensure_mcp_image(self) -> bool:
        """Ensure MCP Docker image is available"""
        try:
            # Try to pull the image first
            logger.info("Pulling MCP Obsidian Docker image...")
            self.docker_client.images.pull("mcp/obsidian:latest")
            return True
        except Exception as e:
            logger.warning(f"Failed to pull image, trying to build: {e}")
            try:
                # Build the image if pull fails
                logger.info("Building MCP Obsidian Docker image...")
                self.docker_client.images.build(
                    path=".",
                    tag="mcp/obsidian:latest",
                    dockerfile="Dockerfile.mcp"
                )
                return True
            except Exception as build_error:
                logger.error(f"Failed to build MCP image: {build_error}")
                return False
    
    async def _start_mcp_container(self) -> bool:
        """Start MCP Docker container"""
        try:
            # Stop existing container if running
            await self._stop_existing_container()
            
            # Prepare volume mounts
            vault_path = Path(self.config.get("vault_path", "C:/Users/JustineDevs/Downloads/Hyperkit"))
            volumes = {
                str(vault_path.absolute()): {
                    "bind": "/vault",
                    "mode": "ro"  # Read-only access
                }
            }
            
            # Prepare environment variables
            environment = {
                "OBSIDIAN_HOST": self.obsidian_host,
                "OBSIDIAN_API_KEY": self.obsidian_api_key,
                "VAULT_PATH": "/vault"
            }
            
            # Start container
            self.container = self.docker_client.containers.run(
                self.docker_image,
                name=self.container_name,
                ports=self.port_mapping,
                volumes=volumes,
                environment=environment,
                detach=True,
                remove=False
                # Removed network_mode="host" to fix port binding conflict
            )
            
            logger.info(f"MCP container started: {self.container.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start MCP container: {e}")
            return False
    
    async def _stop_existing_container(self):
        """Stop existing MCP container if running"""
        try:
            existing_containers = self.docker_client.containers.list(
                filters={"name": self.container_name}
            )
            for container in existing_containers:
                logger.info(f"Stopping existing container: {container.id}")
                container.stop()
                container.remove()
        except Exception as e:
            logger.warning(f"Error stopping existing container: {e}")
    
    async def _wait_for_container_ready(self, timeout: int = 30) -> bool:
        """Wait for MCP container to be ready"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if self.container and self.container.status == "running":
                    # Test if MCP server is responding
                    if await self._test_mcp_connection():
                        return True
                
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"Error checking container status: {e}")
                await asyncio.sleep(1)
        
        return False
    
    async def _test_mcp_connection(self) -> bool:
        """Test MCP server connection"""
        try:
            # Simple health check
            result = await self.search_notes("test", limit=1)
            return result is not None
        except Exception:
            return False
    
    async def search_notes(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search notes in Obsidian vault
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching notes
        """
        try:
            if not self.is_running:
                logger.error("MCP client not initialized")
                return []
            
            # Execute search command in container
            exec_result = self.container.exec_run(
                f"python -c \"import mcp_server; print(mcp_server.search_notes('{query}', {limit}))\"",
                workdir="/app"
            )
            
            if exec_result.exit_code == 0:
                result = json.loads(exec_result.output.decode())
                return result
            else:
                logger.error(f"Search failed: {exec_result.output.decode()}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching notes: {e}")
            return []
    
    async def get_note_content(self, note_path: str) -> Optional[str]:
        """
        Get content of a specific note
        
        Args:
            note_path: Path to the note
            
        Returns:
            Note content or None if not found
        """
        try:
            if not self.is_running:
                logger.error("MCP client not initialized")
                return None
            
            # Execute get content command in container
            exec_result = self.container.exec_run(
                f"python -c \"import mcp_server; print(mcp_server.get_note_content('{note_path}'))\"",
                workdir="/app"
            )
            
            if exec_result.exit_code == 0:
                return exec_result.output.decode().strip()
            else:
                logger.error(f"Get content failed: {exec_result.output.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting note content: {e}")
            return None
    
    async def get_all_notes(self) -> List[Dict[str, Any]]:
        """
        Get all notes in the vault
        
        Returns:
            List of all notes with metadata
        """
        try:
            if not self.is_running:
                logger.error("MCP client not initialized")
                return []
            
            # Execute get all notes command in container
            exec_result = self.container.exec_run(
                "python -c \"import mcp_server; print(mcp_server.get_all_notes())\"",
                workdir="/app"
            )
            
            if exec_result.exit_code == 0:
                result = json.loads(exec_result.output.decode())
                return result
            else:
                logger.error(f"Get all notes failed: {exec_result.output.decode()}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting all notes: {e}")
            return []
    
    async def get_note_metadata(self, note_path: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific note
        
        Args:
            note_path: Path to the note
            
        Returns:
            Note metadata or None if not found
        """
        try:
            if not self.is_running:
                logger.error("MCP client not initialized")
                return None
            
            # Execute get metadata command in container
            exec_result = self.container.exec_run(
                f"python -c \"import mcp_server; print(mcp_server.get_note_metadata('{note_path}'))\"",
                workdir="/app"
            )
            
            if exec_result.exit_code == 0:
                result = json.loads(exec_result.output.decode())
                return result
            else:
                logger.error(f"Get metadata failed: {exec_result.output.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting note metadata: {e}")
            return None
    
    async def get_vault_stats(self) -> Dict[str, Any]:
        """
        Get vault statistics
        
        Returns:
            Vault statistics dictionary
        """
        try:
            if not self.is_running:
                logger.error("MCP client not initialized")
                return {}
            
            # Execute get stats command in container
            exec_result = self.container.exec_run(
                "python -c \"import mcp_server; print(mcp_server.get_vault_stats())\"",
                workdir="/app"
            )
            
            if exec_result.exit_code == 0:
                result = json.loads(exec_result.output.decode())
                return result
            else:
                logger.error(f"Get vault stats failed: {exec_result.output.decode()}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting vault stats: {e}")
            return {}
    
    async def stream_notes(self, query: str = "") -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream notes as they are found
        
        Args:
            query: Optional search query
            
        Yields:
            Note dictionaries
        """
        try:
            if not self.is_running:
                logger.error("MCP client not initialized")
                return
            
            # Execute stream command in container
            exec_result = self.container.exec_run(
                f"python -c \"import mcp_server; mcp_server.stream_notes('{query}')\"",
                workdir="/app",
                stream=True
            )
            
            for line in exec_result.output:
                try:
                    note_data = json.loads(line.decode().strip())
                    yield note_data
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            logger.error(f"Error streaming notes: {e}")
    
    async def cleanup(self):
        """Clean up MCP container and resources"""
        try:
            if self.container:
                logger.info("Stopping MCP container...")
                self.container.stop()
                self.container.remove()
                self.container = None
            
            self.is_running = False
            logger.info("MCP client cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def restart(self) -> bool:
        """Restart MCP container"""
        try:
            await self.cleanup()
            await asyncio.sleep(2)  # Wait for cleanup
            return await self.initialize()
        except Exception as e:
            logger.error(f"Error restarting MCP client: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of MCP client"""
        return {
            "is_running": self.is_running,
            "container_id": self.container.id if self.container else None,
            "container_status": self.container.status if self.container else None,
            "obsidian_host": self.obsidian_host,
            "vault_path": self.vault_path
        }