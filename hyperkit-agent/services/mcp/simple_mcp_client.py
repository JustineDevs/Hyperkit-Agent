"""
Simple MCP Client - Direct API Integration
No Docker dependency, direct HTTP calls to Obsidian API
"""

import requests
import logging
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger(__name__)

class SimpleMCPClient:
    """Simple MCP client that works directly with Obsidian API"""
    
    def __init__(self, api_key: str, base_url: str = "http://localhost:27124"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    async def get_notes(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all notes from Obsidian"""
        try:
            response = self.session.get(f"{self.base_url}/notes", params={'limit': limit})
            response.raise_for_status()
            return response.json().get('notes', [])
        except Exception as e:
            logger.error(f"Failed to get notes: {e}")
            return []
    
    async def search_notes(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search notes by query"""
        try:
            response = self.session.get(
                f"{self.base_url}/search", 
                params={'q': query, 'limit': limit}
            )
            response.raise_for_status()
            return response.json().get('results', [])
        except Exception as e:
            logger.error(f"Failed to search notes: {e}")
            return []
    
    async def get_note_content(self, note_id: str) -> Optional[str]:
        """Get content of a specific note"""
        try:
            response = self.session.get(f"{self.base_url}/notes/{note_id}")
            response.raise_for_status()
            return response.json().get('content', '')
        except Exception as e:
            logger.error(f"Failed to get note content: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Check if MCP service is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"MCP health check failed: {e}")
            return False
    
    async def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        try:
            notes = await self.get_notes(limit=1000)
            return {
                "total_notes": len(notes),
                "status": "connected",
                "api_url": self.base_url
            }
        except Exception as e:
            logger.error(f"Failed to get knowledge base stats: {e}")
            return {
                "total_notes": 0,
                "status": "error",
                "error": str(e)
            }

# Global instance
simple_mcp_client = None

def get_simple_mcp_client(api_key: str, base_url: str = "http://localhost:27124") -> SimpleMCPClient:
    """Get or create simple MCP client instance"""
    global simple_mcp_client
    if simple_mcp_client is None:
        simple_mcp_client = SimpleMCPClient(api_key, base_url)
    return simple_mcp_client
