"""
Document retriever for RAG system.
Handles retrieval of similar documents from IPFS for AI context.
"""

import logging
from typing import Dict, Any, List, Optional
from .vector_store import VectorStore

logger = logging.getLogger(__name__)

class DocumentRetriever:
    """
    Document retriever for RAG system.
    Retrieves similar documents from IPFS for AI context.
    """
    
    def __init__(self, vector_store: VectorStore, ipfs_client):
        self.vector_store = vector_store
        self.ipfs_client = ipfs_client
    
    async def find_similar_audits(self, contract_address: str, query: str = None, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Find similar audit reports for a contract.
        
        Args:
            contract_address: Contract address to find similar audits for
            query: Optional search query
            top_k: Number of similar audits to return
            
        Returns:
            List of similar audit reports
        """
        try:
            # Build search query
            if not query:
                query = f"audit report for contract {contract_address}"
            
            # Search for similar documents
            similar_docs = await self.vector_store.search_similar(
                query=query,
                top_k=top_k,
                filter_metadata={'content_type': 'audit_report'}
            )
            
            # Retrieve full documents from IPFS
            results = []
            for doc in similar_docs:
                try:
                    # Get full document from IPFS
                    full_doc = await self.ipfs_client.get_json(doc['cid'])
                    
                    results.append({
                        'cid': doc['cid'],
                        'similarity_score': doc['score'],
                        'contract_address': doc['metadata'].get('contract_address', ''),
                        'timestamp': doc['metadata'].get('timestamp', 0),
                        'audit_data': full_doc,
                        'ipfs_url': self.ipfs_client.get_url(doc['cid'])
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to retrieve document {doc['cid']}: {e}")
                    continue
            
            logger.info(f"Found {len(results)} similar audits for {contract_address}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to find similar audits: {e}")
            return []
    
    async def find_similar_vulnerabilities(self, vulnerability_type: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar vulnerability reports.
        
        Args:
            vulnerability_type: Type of vulnerability to search for
            top_k: Number of results to return
            
        Returns:
            List of similar vulnerability reports
        """
        try:
            query = f"vulnerability {vulnerability_type} security issue"
            
            similar_docs = await self.vector_store.search_similar(
                query=query,
                top_k=top_k,
                filter_metadata={'content_type': 'audit_report'}
            )
            
            results = []
            for doc in similar_docs:
                try:
                    full_doc = await self.ipfs_client.get_json(doc['cid'])
                    
                    # Extract vulnerability information
                    vulnerabilities = []
                    if 'audit_results' in full_doc and 'findings' in full_doc['audit_results']:
                        for finding in full_doc['audit_results']['findings']:
                            if vulnerability_type.lower() in finding.get('title', '').lower():
                                vulnerabilities.append(finding)
                    
                    if vulnerabilities:
                        results.append({
                            'cid': doc['cid'],
                            'similarity_score': doc['score'],
                            'contract_address': doc['metadata'].get('contract_address', ''),
                            'vulnerabilities': vulnerabilities,
                            'ipfs_url': self.ipfs_client.get_url(doc['cid'])
                        })
                        
                except Exception as e:
                    logger.warning(f"Failed to retrieve vulnerability document {doc['cid']}: {e}")
                    continue
            
            logger.info(f"Found {len(results)} similar {vulnerability_type} vulnerabilities")
            return results
            
        except Exception as e:
            logger.error(f"Failed to find similar vulnerabilities: {e}")
            return []
    
    async def get_context_for_audit(self, contract_address: str, audit_data: Dict[str, Any]) -> str:
        """
        Get relevant context for audit from similar reports.
        
        Args:
            contract_address: Contract address being audited
            audit_data: Current audit data
            
        Returns:
            Context string for AI
        """
        try:
            # Find similar audits
            similar_audits = await self.find_similar_audits(contract_address, top_k=3)
            
            if not similar_audits:
                return "No similar audits found for context."
            
            # Build context string
            context_parts = ["Similar audit reports found:"]
            
            for i, audit in enumerate(similar_audits, 1):
                context_parts.append(f"\n{i}. Contract: {audit['contract_address']}")
                context_parts.append(f"   Similarity: {audit['similarity_score']:.2f}")
                context_parts.append(f"   IPFS: {audit['ipfs_url']}")
                
                # Add key findings
                if 'audit_data' in audit and 'audit_results' in audit['audit_data']:
                    audit_results = audit['audit_data']['audit_results']
                    
                    if 'risk_assessment' in audit_results:
                        risk = audit_results['risk_assessment']
                        context_parts.append(f"   Risk Level: {risk.get('level', 'Unknown')} (Score: {risk.get('score', 0)})")
                    
                    if 'findings' in audit_results and audit_results['findings']:
                        context_parts.append(f"   Key Findings: {len(audit_results['findings'])} issues found")
                        
                        # Add top findings
                        for finding in audit_results['findings'][:2]:
                            context_parts.append(f"     - {finding.get('title', 'Unknown issue')}")
            
            context = "\n".join(context_parts)
            logger.info(f"Generated context for audit: {len(similar_audits)} similar reports")
            return context
            
        except Exception as e:
            logger.error(f"Failed to get context for audit: {e}")
            return "Error retrieving context from similar audits."
    
    async def index_new_audit(self, cid: str, audit_data: Dict[str, Any]) -> bool:
        """
        Index a new audit report in the vector store.
        
        Args:
            cid: IPFS CID of the audit report
            audit_data: Audit report data
            
        Returns:
            True if successful
        """
        try:
            # Add to vector store
            success = await self.vector_store.add_document(
                cid=cid,
                content=audit_data,
                metadata={
                    'content_type': 'audit_report',
                    'contract_address': audit_data.get('metadata', {}).get('contract_address', ''),
                    'timestamp': audit_data.get('metadata', {}).get('timestamp', 0)
                }
            )
            
            if success:
                logger.info(f"Successfully indexed audit report: {cid}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to index audit report: {e}")
            return False