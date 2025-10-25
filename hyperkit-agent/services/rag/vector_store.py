"""
Vector store for RAG system.
Handles embeddings and similarity search for IPFS content.
"""

import json
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import hashlib
import time

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Vector store for RAG system using ChromaDB.
    Handles embeddings and similarity search for IPFS content.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.store_path = Path(config.get('store_path', 'data/vector_store'))
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB if available
        try:
            import chromadb
            self.chroma_client = chromadb.PersistentClient(path=str(self.store_path))
            self.collection = self.chroma_client.get_or_create_collection(
                name="hyperkit_audits",
                metadata={"description": "HyperKit Agent audit reports and documents"}
            )
            self.chroma_available = True
            logger.info("ChromaDB initialized successfully")
        except ImportError:
            logger.warning("ChromaDB not available, using in-memory storage")
            self.chroma_available = False
            self._in_memory_store = {}
    
    async def add_document(self, cid: str, content: Dict[str, Any], metadata: Dict[str, Any] = None) -> bool:
        """
        Add document to vector store.
        
        Args:
            cid: IPFS CID of the document
            content: Document content
            metadata: Optional metadata
            
        Returns:
            True if successful
        """
        try:
            # Extract text content for embedding
            text_content = self._extract_text(content)
            
            # Generate embedding
            embedding = await self._generate_embedding(text_content)
            
            # Prepare metadata
            doc_metadata = {
                'cid': cid,
                'timestamp': int(time.time()),
                'content_type': content.get('metadata', {}).get('storage_type', 'unknown'),
                'contract_address': content.get('metadata', {}).get('contract_address', ''),
                **(metadata or {})
            }
            
            if self.chroma_available:
                # Use ChromaDB
                self.collection.add(
                    embeddings=[embedding],
                    documents=[text_content],
                    metadatas=[doc_metadata],
                    ids=[cid]
                )
            else:
                # Use in-memory storage
                self._in_memory_store[cid] = {
                    'embedding': embedding,
                    'content': text_content,
                    'metadata': doc_metadata
                }
            
            logger.info(f"Added document to vector store: {cid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document to vector store: {e}")
            return False
    
    async def search_similar(self, query: str, top_k: int = 5, filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of similar documents with scores
        """
        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)
            
            if self.chroma_available:
                # Use ChromaDB search
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=filter_metadata
                )
                
                # Format results
                similar_docs = []
                for i in range(len(results['ids'][0])):
                    similar_docs.append({
                        'cid': results['ids'][0][i],
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'score': 1 - results['distances'][0][i]  # Convert distance to similarity
                    })
                
                return similar_docs
            else:
                # Use in-memory search
                return self._in_memory_search(query_embedding, top_k, filter_metadata)
                
        except Exception as e:
            logger.error(f"Failed to search similar documents: {e}")
            return []
    
    async def get_document(self, cid: str) -> Optional[Dict[str, Any]]:
        """
        Get document by CID.
        
        Args:
            cid: IPFS CID
            
        Returns:
            Document data or None
        """
        try:
            if self.chroma_available:
                results = self.collection.get(ids=[cid])
                if results['ids']:
                    return {
                        'cid': cid,
                        'content': results['documents'][0],
                        'metadata': results['metadatas'][0]
                    }
            else:
                if cid in self._in_memory_store:
                    doc = self._in_memory_store[cid]
                    return {
                        'cid': cid,
                        'content': doc['content'],
                        'metadata': doc['metadata']
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return None
    
    def _extract_text(self, content: Dict[str, Any]) -> str:
        """Extract text content from document for embedding."""
        try:
            # Extract text from audit report
            if 'audit_results' in content:
                audit_results = content['audit_results']
                text_parts = []
                
                # Add contract info
                if 'contract_info' in audit_results:
                    text_parts.append(f"Contract: {audit_results['contract_info'].get('name', 'Unknown')}")
                
                # Add vulnerabilities
                if 'findings' in audit_results:
                    for finding in audit_results['findings']:
                        text_parts.append(f"Vulnerability: {finding.get('title', '')} - {finding.get('description', '')}")
                
                # Add risk assessment
                if 'risk_assessment' in audit_results:
                    risk = audit_results['risk_assessment']
                    text_parts.append(f"Risk Level: {risk.get('level', 'Unknown')} - Score: {risk.get('score', 0)}")
                
                return " ".join(text_parts)
            
            # Fallback to JSON string
            return json.dumps(content, indent=2)
            
        except Exception as e:
            logger.warning(f"Failed to extract text: {e}")
            return str(content)
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        try:
            # For demo purposes, generate a mock embedding
            # In production, use a real embedding model like OpenAI or Sentence-BERT
            text_hash = hashlib.md5(text.encode()).hexdigest()
            
            # Generate deterministic "embedding" based on text hash
            embedding = []
            for i in range(0, len(text_hash), 2):
                val = int(text_hash[i:i+2], 16) / 255.0
                embedding.append(val)
            
            # Pad to 384 dimensions (common embedding size)
            while len(embedding) < 384:
                embedding.append(0.0)
            
            return embedding[:384]
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return [0.0] * 384
    
    def _in_memory_search(self, query_embedding: List[float], top_k: int, filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """In-memory similarity search."""
        try:
            results = []
            
            for cid, doc in self._in_memory_store.items():
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, doc['embedding'])
                
                # Apply metadata filters
                if filter_metadata:
                    matches = True
                    for key, value in filter_metadata.items():
                        if doc['metadata'].get(key) != value:
                            matches = False
                            break
                    if not matches:
                        continue
                
                results.append({
                    'cid': cid,
                    'content': doc['content'],
                    'metadata': doc['metadata'],
                    'score': similarity
                })
            
            # Sort by similarity score
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"In-memory search failed: {e}")
            return []
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            dot_product = sum(x * y for x, y in zip(a, b))
            norm_a = sum(x * x for x in a) ** 0.5
            norm_b = sum(x * x for x in b) ** 0.5
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            return dot_product / (norm_a * norm_b)
            
        except Exception as e:
            logger.error(f"Cosine similarity calculation failed: {e}")
            return 0.0
