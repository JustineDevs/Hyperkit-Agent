"""
IPFS Pinata RAG System for HyperKit Agent
Replaces Obsidian RAG with IPFS-based retrieval from Pinata
"""

import asyncio
import logging
import requests
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class IPFSRAG:
    """
    IPFS Pinata-based RAG system for HyperKit Agent.
    Retrieves and stores AI prompts, templates, and knowledge in IPFS via Pinata.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize IPFS RAG system with Pinata configuration."""
        self.config = config or {}
        self.pinata_api_key = self.config.get('PINATA_API_KEY') or self.config.get('pinata', {}).get('api_key')
        self.pinata_secret_key = self.config.get('PINATA_SECRET_KEY') or self.config.get('pinata', {}).get('secret_key')
        self.pinata_enabled = bool(self.pinata_api_key and self.pinata_secret_key)
        
        # IPFS Gateways for retrieval
        self.gateways = [
            'https://gateway.pinata.cloud/ipfs/',
            'https://ipfs.io/ipfs/',
            'https://cloudflare-ipfs.com/ipfs/',
            'https://dweb.link/ipfs/'
        ]
        
        # CID Registry cache
        self.cid_registry = {}
        self._load_cid_registry()
        
        if self.pinata_enabled:
            logger.info("IPFS RAG initialized with Pinata integration")
        else:
            logger.warning("IPFS RAG initialized without Pinata (read-only mode)")
    
    def _load_cid_registry(self):
        """Load CID registry for prompt templates."""
        try:
            registry_path = Path("docs/RAG_TEMPLATES/cid-registry.json")
            if registry_path.exists():
                with open(registry_path, 'r', encoding='utf-8') as f:
                    self.cid_registry = json.load(f)
                logger.info(f"Loaded {len(self.cid_registry)} templates from CID registry")
        except Exception as e:
            logger.warning(f"Could not load CID registry: {e}")
    
    async def retrieve(self, query: str, max_results: int = 5) -> str:
        """
        Retrieve relevant context from IPFS based on query.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            Combined context string from relevant IPFS documents
        """
        try:
            # Search CID registry for relevant templates
            results = []
            
            for name, metadata in self.cid_registry.items():
                if self._is_relevant(query, metadata):
                    try:
                        content = await self._fetch_from_ipfs(metadata.get('cid'))
                        if content:
                            results.append({
                                'name': name,
                                'content': content,
                                'cid': metadata.get('cid'),
                                'relevance': self._calculate_relevance(query, content)
                            })
                    except Exception as e:
                        logger.warning(f"Failed to fetch {name}: {e}")
            
            # Sort by relevance
            results.sort(key=lambda x: x['relevance'], reverse=True)
            
            # Combine top results
            combined_context = "\n\n".join([
                f"## {r['name']}\n{r['content']}" 
                for r in results[:max_results]
            ])
            
            return combined_context
            
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            return ""
    
    async def upload_template(self, name: str, content: str, metadata: Dict[str, Any] = None) -> str:
        """
        Upload a template to IPFS via Pinata.
        
        Args:
            name: Template name
            content: Template content
            metadata: Additional metadata
            
        Returns:
            CID of uploaded content
        """
        if not self.pinata_enabled:
            logger.warning("Pinata not configured - cannot upload")
            return None
        
        try:
            pinata_metadata = {
                'name': name,
                'description': metadata.get('description', ''),
                'tags': metadata.get('tags', []),
                'version': metadata.get('version', 'latest'),
                **(metadata or {})
            }
            
            # Upload to Pinata
            headers = {
                'pinata_api_key': self.pinata_api_key,
                'pinata_secret_api_key': self.pinata_secret_key
            }
            
            files = {'file': ('content', content)}
            
            metadata_header = json.dumps(pinata_metadata)
            
            response = requests.post(
                'https://api.pinata.cloud/pinning/pinFileToIPFS',
                files=files,
                headers={
                    **headers,
                    'pinata_metadata': metadata_header
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                cid = result.get('IpfsHash')
                
                # Update local registry cache
                self.cid_registry[name] = {
                    'cid': cid,
                    **pinata_metadata
                }
                
                logger.info(f"Uploaded template '{name}' to IPFS: {cid}")
                return cid
            else:
                logger.error(f"Pinata upload failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Template upload failed: {e}")
            return None
    
    async def _fetch_from_ipfs(self, cid: str) -> Optional[str]:
        """Fetch content from IPFS by CID."""
        for gateway in self.gateways:
            try:
                url = f"{gateway}{cid}"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    return response.text
            except Exception as e:
                logger.warning(f"Gateway {gateway} failed: {e}")
                continue
        
        logger.error(f"Could not fetch CID {cid} from any gateway")
        return None
    
    def _is_relevant(self, query: str, metadata: Dict[str, Any]) -> bool:
        """Check if template is relevant to query."""
        query_lower = query.lower()
        
        # Check name
        name = metadata.get('name', '').lower()
        if query_lower in name:
            return True
        
        # Check tags
        tags = metadata.get('tags', [])
        for tag in tags:
            if query_lower in tag.lower():
                return True
        
        # Check description
        description = metadata.get('description', '').lower()
        if query_lower in description:
            return True
        
        return False
    
    def _calculate_relevance(self, query: str, content: str) -> float:
        """Calculate relevance score (simple keyword matching)."""
        query_words = query.lower().split()
        content_lower = content.lower()
        
        matches = sum(1 for word in query_words if word in content_lower)
        return matches / len(query_words) if query_words else 0
    
    async def get_template(self, name: str) -> Optional[str]:
        """Get a specific template by name."""
        if name in self.cid_registry:
            cid = self.cid_registry[name].get('cid')
            if cid:
                return await self._fetch_from_ipfs(cid)
        return None
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template names."""
        return list(self.cid_registry.keys())


# Convenience function to create RAG instance
def get_ipfs_rag(config: Dict[str, Any] = None) -> IPFSRAG:
    """Get or create IPFS RAG instance."""
    return IPFSRAG(config)


async def test_ipfs_rag():
    """Test IPFS RAG system."""
    print("Testing IPFS RAG System...")
    
    try:
        # Create instance
        rag = IPFSRAG()
        
        # Test retrieval
        query = "smart contract generation"
        context = await rag.retrieve(query)
        
        print(f"Retrieved context length: {len(context)} characters")
        if context:
            print("IPFS RAG is working!")
            return True
        else:
            print("No context retrieved")
            return False
            
    except Exception as e:
        print(f"IPFS RAG test failed: {e}")
        return False
