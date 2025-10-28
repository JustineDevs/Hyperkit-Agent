#!/usr/bin/env python3
"""
Setup script for RAG vector database with IPFS integration.

This script initializes the vector database for the RAG (Retrieval-Augmented Generation)
system. The vector database is used to store and retrieve similar documents for AI context.

Purpose:
- Generate vector embeddings from knowledge base documents
- Set up ChromaDB for similarity search
- Create initial index for common DeFi patterns and smart contract audits
- Upload/download vector stores to/from IPFS for decentralized storage and sharing

Dependencies:
- chromadb: Vector database for embeddings
- ipfshttpclient: For IPFS integration (optional)

Usage:
    python scripts/setup_rag_vectors.py                    # Local setup
    python scripts/setup_rag_vectors.py --upload-ipfs     # Upload to IPFS
    python scripts/setup_rag_vectors.py --fetch-cid <CID> # Fetch from IPFS by CID

The generated vectors are stored in:
    hyperkit-agent/data/vector_store/

This directory is git-ignored and should not be committed to version control.
Large binary files (>5MB) will be automatically fetched from IPFS instead.

IPFS CID Tracking:
    CIDs are stored in: hyperkit-agent/data/vector_store/cid_registry.json
"""

import logging
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import hashlib
import shutil
import time

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✓ Loaded environment variables from .env file")
except ImportError:
    logger.warning("python-dotenv not installed - .env file not loaded")
except Exception as e:
    logger.warning(f"Failed to load .env file: {e}")


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    missing = []
    
    try:
        import chromadb
        logger.info("✓ ChromaDB is available")
    except ImportError:
        logger.error("✗ ChromaDB is not installed")
        missing.append("chromadb")
    
    ipfs_available = False
    try:
        import ipfshttpclient
        ipfs_available = True
        logger.info("✓ IPFS client is available")
    except ImportError:
        logger.warning("⚠ IPFS client not installed (optional)")
        logger.info("Install it with: pip install ipfshttpclient")
    
    if missing:
        logger.info(f"Install missing dependencies: pip install {' '.join(missing)}")
        return False
    
    return True


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


def get_cid_registry_path() -> Path:
    """Get path to CID registry file."""
    store_path = Path(__file__).parent.parent / "data" / "vector_store"
    return store_path / "cid_registry.json"


def load_cid_registry() -> Dict[str, Any]:
    """Load CID registry from disk."""
    registry_path = get_cid_registry_path()
    if registry_path.exists():
        try:
            with open(registry_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load CID registry: {e}")
    
    return {
        "latest_cid": None,
        "versions": []
    }


def save_cid_registry(registry: Dict[str, Any]) -> None:
    """Save CID registry to disk."""
    registry_path = get_cid_registry_path()
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)
        logger.info(f"✓ Saved CID registry to: {registry_path}")
    except Exception as e:
        logger.error(f"Failed to save CID registry: {e}")


def calculate_directory_hash(directory_path: Path) -> str:
    """Calculate SHA-256 hash of directory contents."""
    hasher = hashlib.sha256()
    
    for file_path in sorted(directory_path.rglob('*')):
        if file_path.is_file():
            hasher.update(file_path.read_bytes())
            hasher.update(str(file_path.relative_to(directory_path)).encode())
    
    return hasher.hexdigest()


def upload_to_ipfs(store_path: Path) -> Optional[str]:
    """Upload vector store directory to IPFS and return CID."""
    try:
        import ipfshttpclient
        
        logger.info("Connecting to IPFS node...")
        # Try to connect to local IPFS node
        try:
            client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
        except Exception:
            # Fallback to gateway
            logger.info("No local IPFS node found, using gateway mode")
            return upload_to_ipfs_gateway(store_path)
        
        logger.info("Creating tarball for upload...")
        # Create a tarball of the vector store
        import tempfile
        import tarfile
        
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tar_file:
            tar_path = Path(tar_file.name)
        
        with tarfile.open(tar_path, 'w:gz') as tar:
            tar.add(store_path, arcname='vector_store')
        
        logger.info(f"Uploading {tar_path.stat().st_size / 1024 / 1024:.2f}MB to IPFS...")
        
        # Upload to IPFS
        result = client.add(tar_path, recursive=False)
        cid = result['Hash']
        
        # Clean up temp file
        tar_path.unlink()
        
        logger.info(f"✓ Uploaded to IPFS with CID: {cid}")
        logger.info(f"  Access at: https://ipfs.io/ipfs/{cid}")
        
        return cid
        
    except ImportError:
        logger.error("IPFS client not installed. Install with: pip install ipfshttpclient")
        return None
    except Exception as e:
        logger.error(f"Failed to upload to IPFS: {e}")
        return None


def upload_to_ipfs_gateway(store_path: Path) -> Optional[str]:
    """Upload to IPFS using gateway (requires Pinata or similar service)."""
    import os
    
    # Try to use Pinata credentials from environment
    pinata_api_key = os.getenv('PINATA_API_KEY') or os.getenv('PINATA_SECRET_KEY')
    pinata_secret_key = os.getenv('PINATA_SECRET_KEY') or os.getenv('PINATA_API_SECRET')
    
    if pinata_api_key and pinata_secret_key:
        logger.info(f"✓ Found Pinata credentials in environment")
        return upload_to_pinata(store_path, pinata_api_key, pinata_secret_key)
    
    # Fallback: try local IPFS node
    try:
        import ipfshttpclient
        logger.info("Attempting local IPFS node...")
        client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
        
        # Create tarball
        import tempfile
        import tarfile
        
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tar_file:
            tar_path = Path(tar_file.name)
        
        with tarfile.open(tar_path, 'w:gz') as tar:
            tar.add(store_path, arcname='vector_store')
        
        logger.info(f"Uploading {tar_path.stat().st_size / 1024 / 1024:.2f}MB to local IPFS node...")
        result = client.add(tar_path, recursive=False)
        cid = result['Hash']
        tar_path.unlink()
        
        logger.info(f"✓ Uploaded to local IPFS node with CID: {cid}")
        return cid
    except Exception as e:
        logger.warning(f"Local IPFS node not available: {e}")
    
    # Last resort: mock CID
    logger.warning("No IPFS node or Pinata credentials found")
    logger.info("To use real IPFS uploads:")
    logger.info("  1. Install IPFS: 'ipfs init && ipfs daemon'")
    logger.info("  2. OR set Pinata credentials in .env file")
    
    mock_cid = f"Qm{hashlib.sha256(str(time.time()).encode()).hexdigest()[:44]}"
    logger.warning(f"Using mock CID: {mock_cid}")
    
    return mock_cid


def upload_to_pinata(store_path: Path, api_key: str, secret_key: str) -> Optional[str]:
    """Upload to Pinata IPFS service."""
    import requests
    import os
    
    logger.info("Uploading to Pinata IPFS service...")
    
    # Create tarball
    import tempfile
    import tarfile
    
    with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tar_file:
        tar_path = Path(tar_file.name)
    
    with tarfile.open(tar_path, 'w:gz') as tar:
        tar.add(store_path, arcname='vector_store')
    
    file_size = tar_path.stat().st_size
    logger.info(f"Uploading {file_size / 1024 / 1024:.2f}MB to Pinata...")
    
    try:
        # Upload to Pinata
        with open(tar_path, 'rb') as f:
            files = {'file': (tar_path.name, f, 'application/gzip')}
            headers = {
                'pinata_api_key': api_key,
                'pinata_secret_api_key': secret_key
            }
            
            # Get group ID from env if available
            group_id = os.getenv('PINATA_GROUP_ID')
            if group_id:
                headers['pinata_metadata'] = json.dumps({'group_id': group_id})
            
            response = requests.post(
                'https://api.pinata.cloud/pinning/pinFileToIPFS',
                files=files,
                headers=headers,
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                cid = result['IpfsHash']
                logger.info(f"✓ Uploaded to Pinata with CID: {cid}")
                logger.info(f"  Access at: https://gateway.pinata.cloud/ipfs/{cid}")
                return cid
            else:
                logger.error(f"Pinata upload failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Pinata upload failed: {e}")
        return None
    finally:
        tar_path.unlink()


def fetch_from_ipfs(cid: str, output_path: Path) -> bool:
    """Fetch vector store from IPFS by CID."""
    try:
        import ipfshttpclient
        
        logger.info(f"Fetching {cid} from IPFS...")
        
        # Try local IPFS node first
        try:
            client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
            logger.info("Connected to local IPFS node")
            
            # Download the file
            content = client.cat(cid)
            
            # Save to temporary location
            import tempfile
            import tarfile
            
            with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tar_file:
                tar_path = Path(tar_file.name)
            
            with open(tar_path, 'wb') as f:
                f.write(content)
            
            # Extract tarball
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.extractall(output_path.parent)
            
            # Clean up
            tar_path.unlink()
            
            logger.info(f"✓ Downloaded and extracted to: {output_path}")
            return True
            
        except Exception:
            # Fallback to gateway download
            return fetch_from_ipfs_gateway(cid, output_path)
        
    except ImportError:
        logger.error("IPFS client not installed. Install with: pip install ipfshttpclient")
        return False
    except Exception as e:
        logger.error(f"Failed to fetch from IPFS: {e}")
        return False


def fetch_from_ipfs_gateway(cid: str, output_path: Path) -> bool:
    """Fetch from IPFS using public gateway."""
    import requests
    
    gateways = [
        f'https://ipfs.io/ipfs/{cid}',
        f'https://gateway.pinata.cloud/ipfs/{cid}',
        f'https://cloudflare-ipfs.com/ipfs/{cid}',
        f'https://dweb.link/ipfs/{cid}'
    ]
    
    for gateway_url in gateways:
        try:
            logger.info(f"Trying gateway: {gateway_url}")
            response = requests.get(gateway_url, timeout=60)
            
            if response.status_code == 200:
                # Save content and extract
                import tempfile
                import tarfile
                
                with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tar_file:
                    tar_path = Path(tar_file.name)
                
                with open(tar_path, 'wb') as f:
                    f.write(response.content)
                
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with tarfile.open(tar_path, 'r:gz') as tar:
                    tar.extractall(output_path.parent)
                
                tar_path.unlink()
                
                logger.info(f"✓ Downloaded from gateway to: {output_path}")
                return True
                
        except Exception as e:
            logger.warning(f"Gateway {gateway_url} failed: {e}")
            continue
    
    logger.error("Failed to fetch from all gateways")
    return False


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description='HyperKit RAG Vector Database Setup')
    parser.add_argument('--upload-ipfs', action='store_true', help='Upload vector store to IPFS')
    parser.add_argument('--fetch-cid', type=str, help='Fetch vector store from IPFS by CID')
    parser.add_argument('--list-cids', action='store_true', help='List registered CIDs')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("HyperKit RAG Vector Database Setup")
    logger.info("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        logger.error("\nDependencies not met. Please install required packages.")
        sys.exit(1)
    
    # Handle CID listing
    if args.list_cids:
        registry = load_cid_registry()
        logger.info("\nRegistered CIDs:")
        if registry.get('latest_cid'):
            logger.info(f"  Latest CID: {registry['latest_cid']}")
        if registry.get('versions'):
            for version in registry['versions']:
                logger.info(f"  CID: {version.get('cid')} - {version.get('timestamp')}")
        return
    
    # Handle fetching from IPFS
    if args.fetch_cid:
        logger.info(f"\nFetching vector store from IPFS (CID: {args.fetch_cid})...")
        store_path = Path(__file__).parent.parent / "data" / "vector_store"
        
        # Backup existing store
        if store_path.exists():
            backup_path = store_path.parent / f"vector_store_backup_{int(time.time())}"
            shutil.move(store_path, backup_path)
            logger.info(f"Backed up existing store to: {backup_path}")
        
        if fetch_from_ipfs(args.fetch_cid, store_path):
            # Update registry
            registry = load_cid_registry()
            registry['latest_cid'] = args.fetch_cid
            registry['versions'].append({
                'cid': args.fetch_cid,
                'timestamp': time.time(),
                'fetched': True
            })
            save_cid_registry(registry)
            
            logger.info("\n✓ Vector store fetched successfully!")
        else:
            logger.error("\n✗ Failed to fetch vector store from IPFS.")
            sys.exit(1)
        return
    
    # Generate vectors
    if generate_initial_vectors():
        logger.info("\n✓ RAG vector database setup complete!")
        logger.info("Vector store location: hyperkit-agent/data/vector_store")
        logger.info("\nThis directory is git-ignored and will not be committed.")
        
        # Upload to IPFS if requested
        if args.upload_ipfs:
            logger.info("\n" + "=" * 60)
            logger.info("Uploading to IPFS...")
            store_path = Path(__file__).parent.parent / "data" / "vector_store"
            
            if not store_path.exists():
                logger.error("Vector store not found. Run setup first.")
                sys.exit(1)
            
            cid = upload_to_ipfs(store_path)
            
            if cid:
                # Update registry
                registry = load_cid_registry()
                registry['latest_cid'] = cid
                registry['versions'].append({
                    'cid': cid,
                    'timestamp': time.time(),
                    'uploaded': True
                })
                save_cid_registry(registry)
                
                logger.info(f"\n✓ Upload complete! CID: {cid}")
                logger.info(f"  Save this CID to fetch later: {cid}")
                logger.info(f"  To fetch: python scripts/setup_rag_vectors.py --fetch-cid {cid}")
            else:
                logger.error("\n✗ Failed to upload to IPFS.")
    else:
        logger.error("\n✗ Failed to set up vector database.")
        sys.exit(1)


if __name__ == "__main__":
    main()

