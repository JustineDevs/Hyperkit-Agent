#!/usr/bin/env python3
"""
Setup script for RAG vector database.

This script initializes the vector database for the RAG (Retrieval-Augmented Generation)
system. The vector database is used to store and retrieve similar documents for AI context.

Purpose:
- Generate vector embeddings from knowledge base documents
- Set up ChromaDB for similarity search
- Create initial index for common DeFi patterns and smart contract audits

Dependencies:
- chromadb: Vector database for embeddings
- sentence-transformers or OpenAI API: For generating embeddings (optional)

Usage:
    python scripts/setup_rag_vectors.py

The generated vectors are stored in:
    hyperkit-agent/data/vector_store/

This directory is git-ignored and should not be committed to version control.
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    try:
        import chromadb
        logger.info("✓ ChromaDB is available")
        return True
    except ImportError:
        logger.error("✗ ChromaDB is not installed")
        logger.info("Install it with: pip install chromadb")
        return False


def generate_initial_vectors() -> bool:
    """Generate initial vector embeddings from knowledge base."""
    try:
        import chromadb
        
        # Initialize ChromaDB
        store_path = Path(__file__).parent.parent / "data" / "vector_store"
        store_path.mkdir(parents=True, exist_ok=True)
        
        client = chromadb.PersistentClient(path=str(store_path))
        
        # Create or get collection
        collection = client.get_or_create_collection(
            name="hyperkit_knowledge_base",
            metadata={"description": "HyperKit AI Agent knowledge base for RAG"}
        )
        
        logger.info(f"Initialized vector store at: {store_path}")
        
        # Add sample documents for testing
        sample_docs = get_sample_documents()
        
        if sample_docs:
            collection.add(
                documents=[doc['content'] for doc in sample_docs],
                metadatas=[doc['metadata'] for doc in sample_docs],
                ids=[doc['id'] for doc in sample_docs]
            )
            logger.info(f"✓ Added {len(sample_docs)} sample documents to vector store")
        
        # Test retrieval
        results = collection.query(
            query_texts=["How do I deploy a contract?"],
            n_results=2
        )
        logger.info(f"✓ Test query successful: {len(results['ids'][0])} results")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to generate vectors: {e}")
        return False


def get_sample_documents() -> List[Dict[str, Any]]:
    """Get sample documents for initial vector database."""
    return [
        {
            'id': 'doc_001',
            'content': 'HyperKit AI Agent supports smart contract deployment on Hyperion, LazAI, and Metis networks. Use the "deploy" command to deploy your contracts.',
            'metadata': {'type': 'deployment', 'category': 'guide'}
        },
        {
            'id': 'doc_002',
            'content': 'Security audits are performed using Slither and Mythril static analysis tools. Always run an audit before deploying to mainnet.',
            'metadata': {'type': 'security', 'category': 'best_practices'}
        },
        {
            'id': 'doc_003',
            'content': 'ERC20 tokens can be generated using the workflow command. Example: hyperagent workflow run "Create an ERC20 token"',
            'metadata': {'type': 'token', 'category': 'tutorial'}
        },
        {
            'id': 'doc_004',
            'content': 'Batch auditing allows you to audit multiple contracts at once. Use the --directory flag to scan entire directories.',
            'metadata': {'type': 'audit', 'category': 'feature'}
        }
    ]


def main():
    """Main setup function."""
    logger.info("=" * 60)
    logger.info("HyperKit RAG Vector Database Setup")
    logger.info("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        logger.error("\nDependencies not met. Please install required packages.")
        sys.exit(1)
    
    # Generate vectors
    if generate_initial_vectors():
        logger.info("\n✓ RAG vector database setup complete!")
        logger.info("Vector store location: hyperkit-agent/data/vector_store")
        logger.info("\nThis directory is git-ignored and will not be committed.")
    else:
        logger.error("\n✗ Failed to set up vector database.")
        sys.exit(1)


if __name__ == "__main__":
    main()

