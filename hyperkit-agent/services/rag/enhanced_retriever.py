"""
Enhanced RAG Retriever with Obsidian MCP Support

This module provides intelligent content retrieval using:
1. Obsidian vaults via MCP
2. IPFS decentralized storage
3. Local knowledge bases
4. Hybrid retrieval strategies
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from services.rag.obsidian_rag_enhanced import ObsidianRAGEnhanced
from services.storage.ipfs_client import IPFSClient
from core.config.loader import get_config

logger = logging.getLogger(__name__)


class EnhancedRAGRetriever:
    """
    Enhanced RAG retriever with multiple data sources.
    
    Features:
    - Obsidian vault integration via MCP
    - IPFS decentralized storage
    - Local knowledge base fallback
    - Intelligent content ranking
    - Context-aware retrieval
    """
    
    def __init__(self):
        """Initialize the enhanced RAG retriever."""
        self.config = get_config().to_dict()
        self.obsidian_rag = None
        self.ipfs_storage = None
        
        # Initialize components
        self._initialize_obsidian()
        self._initialize_ipfs()
        
        logger.info("Enhanced RAG Retriever initialized")
    
    def _initialize_obsidian(self):
        """Initialize Obsidian RAG service."""
        try:
            rag_config = self.config.get("rag", {}).get("obsidian", {})
            mcp_config = self.config.get("mcp", {})
            
            if rag_config.get("api_key"):
                self.obsidian_rag = ObsidianRAGEnhanced(
                    vault_path=rag_config.get("vault_path", ""),
                    use_mcp=mcp_config.get("enabled", True),
                    mcp_config=mcp_config
                )
                logger.info("Obsidian RAG service initialized")
            else:
                logger.warning("Obsidian API key not configured")
                
        except Exception as e:
            logger.error(f"Failed to initialize Obsidian RAG: {e}")
    
    def _initialize_ipfs(self):
        """Initialize IPFS storage service."""
        try:
            storage_config = self.config.get("storage", {}).get("pinata", {})
            
            if storage_config.get("api_key"):
                self.ipfs_storage = IPFSClient()
                logger.info("IPFS storage service initialized")
            else:
                logger.warning("IPFS/Pinata API key not configured")
                
        except Exception as e:
            logger.error(f"Failed to initialize IPFS storage: {e}")
    
    async def retrieve(self, query: str, context: str = "", max_results: int = 5) -> str:
        """
        Retrieve relevant content from all available sources.
        
        Args:
            query: Search query
            context: Additional context
            max_results: Maximum number of results
            
        Returns:
            Combined relevant content
        """
        try:
            content_sources = []
            
            # 1. Retrieve from Obsidian vault
            if self.obsidian_rag:
                try:
                    obsidian_content = await self.obsidian_rag.retrieve(query, max_results)
                    if obsidian_content and "Error retrieving content" not in obsidian_content:
                        content_sources.append({
                            "source": "obsidian",
                            "content": obsidian_content,
                            "relevance": self._calculate_relevance(query, obsidian_content)
                        })
                except Exception as e:
                    logger.warning(f"Obsidian retrieval failed: {e}")
            
            # 2. Retrieve from IPFS storage
            if self.ipfs_storage:
                try:
                    ipfs_content = await self._retrieve_from_ipfs(query, max_results)
                    if ipfs_content:
                        content_sources.append({
                            "source": "ipfs",
                            "content": ipfs_content,
                            "relevance": self._calculate_relevance(query, ipfs_content)
                        })
                except Exception as e:
                    logger.warning(f"IPFS retrieval failed: {e}")
            
            # 3. Retrieve from local knowledge base
            local_content = await self._retrieve_from_local(query, max_results)
            if local_content:
                content_sources.append({
                    "source": "local",
                    "content": local_content,
                    "relevance": self._calculate_relevance(query, local_content)
                })
            
            # Rank and combine content
            if content_sources:
                ranked_content = self._rank_and_combine(content_sources, max_results)
                logger.info(f"Retrieved content from {len(content_sources)} sources")
                return ranked_content
            else:
                logger.warning("No content retrieved from any source")
                return self._get_fallback_content(query)
                
        except Exception as e:
            logger.error(f"Content retrieval failed: {e}")
            return self._get_fallback_content(query)
    
    async def _retrieve_from_ipfs(self, query: str, max_results: int) -> str:
        """Retrieve content from IPFS storage."""
        try:
            # This would implement IPFS content search
            # For now, return empty string as IPFS search is complex
            return ""
        except Exception as e:
            logger.error(f"IPFS retrieval error: {e}")
            return ""
    
    async def _retrieve_from_local(self, query: str, max_results: int) -> str:
        """Retrieve content from local knowledge base."""
        try:
            # Check for local knowledge files
            knowledge_path = Path("knowledge")
            if not knowledge_path.exists():
                return ""
            
            content_parts = []
            for md_file in knowledge_path.rglob("*.md"):
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
            
            return "\n".join(content_parts) if content_parts else ""
            
        except Exception as e:
            logger.error(f"Local retrieval error: {e}")
            return ""
    
    def _calculate_relevance(self, query: str, content: str) -> float:
        """Calculate relevance score for content."""
        try:
            query_words = set(query.lower().split())
            content_words = set(content.lower().split())
            
            # Simple Jaccard similarity
            intersection = len(query_words.intersection(content_words))
            union = len(query_words.union(content_words))
            
            return intersection / union if union > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def _rank_and_combine(self, content_sources: List[Dict], max_results: int) -> str:
        """Rank and combine content from multiple sources."""
        try:
            # Sort by relevance
            ranked_sources = sorted(content_sources, key=lambda x: x["relevance"], reverse=True)
            
            # Take top results
            top_sources = ranked_sources[:max_results]
            
            # Combine content
            combined_parts = []
            for i, source in enumerate(top_sources, 1):
                source_header = f"## Source {i}: {source['source'].title()} (Relevance: {source['relevance']:.2f})\n"
                combined_parts.append(source_header + source["content"])
            
            return "\n\n".join(combined_parts)
            
        except Exception as e:
            logger.error(f"Content ranking failed: {e}")
            return "\n\n".join([source["content"] for source in content_sources])
    
    def _get_fallback_content(self, query: str) -> str:
        """Get fallback content when no sources are available."""
        return f"""
# Knowledge Base Context

Query: {query}

## General Smart Contract Best Practices

- Use Solidity ^0.8.0 for built-in overflow protection
- Import OpenZeppelin libraries for security
- Implement proper access control (Ownable, AccessControl)
- Use checks-effects-interactions pattern
- Add reentrancy guards where needed
- Include comprehensive error handling
- Use events for important state changes
- Follow NatSpec documentation standards

## Security Considerations

- Validate all external inputs
- Use SafeMath or built-in overflow protection
- Implement circuit breakers for emergency situations
- Use proper random number generation
- Avoid delegatecall with untrusted contracts
- Implement proper upgrade patterns if needed

Note: This is fallback content. Configure Obsidian RAG or IPFS storage for enhanced knowledge retrieval.
"""
    
    async def test_connections(self) -> Dict[str, Any]:
        """Test all available connections."""
        results = {
            "obsidian": {"status": "not_configured"},
            "ipfs": {"status": "not_configured"},
            "local": {"status": "not_configured"}
        }
        
        # Test Obsidian
        if self.obsidian_rag:
            try:
                obsidian_status = self.obsidian_rag.test_connection()
                results["obsidian"] = obsidian_status
            except Exception as e:
                results["obsidian"] = {"status": "error", "error": str(e)}
        
        # Test IPFS
        if self.ipfs_storage:
            try:
                # Simple IPFS test would go here
                results["ipfs"] = {"status": "configured", "note": "IPFS test not implemented"}
            except Exception as e:
                results["ipfs"] = {"status": "error", "error": str(e)}
        
        # Test Local
        try:
            knowledge_path = Path("knowledge")
            if knowledge_path.exists():
                md_files = list(knowledge_path.rglob("*.md"))
                results["local"] = {
                    "status": "success",
                    "file_count": len(md_files),
                    "path": str(knowledge_path)
                }
            else:
                results["local"] = {"status": "no_files", "path": str(knowledge_path)}
        except Exception as e:
            results["local"] = {"status": "error", "error": str(e)}
        
        return results


# Global instance
_rag_retriever = None


def get_rag_retriever() -> EnhancedRAGRetriever:
    """Get the global RAG retriever instance."""
    global _rag_retriever
    if _rag_retriever is None:
        _rag_retriever = EnhancedRAGRetriever()
    return _rag_retriever


async def retrieve_context(query: str, context: str = "") -> str:
    """
    Convenience function for content retrieval.
    
    Args:
        query: Search query
        context: Additional context
        
    Returns:
        Retrieved content
    """
    retriever = get_rag_retriever()
    return await retriever.retrieve(query, context)
