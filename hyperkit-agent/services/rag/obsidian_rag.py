"""
Obsidian RAG Integration for Knowledge Base
Uses Obsidian vault as a markdown-based knowledge repository
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

try:
    from langchain.document_loaders import ObsidianLoader
    from langchain.text_splitter import MarkdownTextSplitter
    from langchain.vectorstores import Chroma
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.schema import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain not available. Using simple text-based RAG.")

logger = logging.getLogger(__name__)


class ObsidianRAG:
    """RAG system using Obsidian vault as knowledge base."""
    
    def __init__(self, vault_path: str = "~/hyperkit-kb"):
        """
        Initialize Obsidian RAG system.
        
        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path).expanduser()
        self.vectorstore = None
        self.documents = []
        
        if LANGCHAIN_AVAILABLE:
            self._setup_langchain_rag()
        else:
            self._setup_simple_rag()
        
        logger.info(f"Obsidian RAG initialized with vault: {self.vault_path}")
    
    def _setup_langchain_rag(self):
        """Set up RAG using LangChain components."""
        try:
            # Use free local embeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            
            # Load Obsidian vault
            self.loader = ObsidianLoader(str(self.vault_path))
            self.documents = self.loader.load()
            
            # Split documents
            self.splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=200)
            self.chunks = self.splitter.split_documents(self.documents)
            
            # Create vector store
            self.vectorstore = Chroma.from_documents(
                documents=self.chunks,
                embedding=self.embeddings,
                persist_directory="./data/obsidian_vectors"
            )
            
            logger.info(f"Loaded {len(self.documents)} documents from Obsidian vault")
            
        except Exception as e:
            logger.error(f"Failed to setup LangChain RAG: {e}")
            self._setup_simple_rag()
    
    def _setup_simple_rag(self):
        """Set up simple text-based RAG without LangChain."""
        self.documents = self._load_markdown_files()
        logger.info(f"Loaded {len(self.documents)} documents using simple RAG")
    
    def _load_markdown_files(self) -> List[Dict[str, Any]]:
        """Load markdown files from Obsidian vault."""
        documents = []
        
        if not self.vault_path.exists():
            logger.warning(f"Obsidian vault not found at {self.vault_path}")
            return documents
        
        # Load all markdown files
        for md_file in self.vault_path.rglob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                documents.append({
                    'content': content,
                    'source': str(md_file.relative_to(self.vault_path)),
                    'title': md_file.stem
                })
            except Exception as e:
                logger.warning(f"Failed to load {md_file}: {e}")
        
        return documents
    
    def retrieve(self, query: str, k: int = 5) -> str:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            k: Number of documents to retrieve
            
        Returns:
            Retrieved context as string
        """
        if self.vectorstore and LANGCHAIN_AVAILABLE:
            return self._retrieve_with_vectorstore(query, k)
        else:
            return self._retrieve_simple(query, k)
    
    def _retrieve_with_vectorstore(self, query: str, k: int) -> str:
        """Retrieve using vector store."""
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            return "\n\n---\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            logger.error(f"Vector store retrieval failed: {e}")
            return self._retrieve_simple(query, k)
    
    def _retrieve_simple(self, query: str, k: int) -> str:
        """Simple keyword-based retrieval."""
        query_lower = query.lower()
        scored_docs = []
        
        for doc in self.documents:
            content_lower = doc['content'].lower()
            score = 0
            
            # Simple keyword matching
            for word in query_lower.split():
                if word in content_lower:
                    score += content_lower.count(word)
            
            if score > 0:
                scored_docs.append((score, doc))
        
        # Sort by score and take top k
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        top_docs = scored_docs[:k]
        
        if not top_docs:
            return "No relevant documents found."
        
        return "\n\n---\n\n".join([
            f"**{doc['title']}**\n{doc['content'][:1000]}..."
            for score, doc in top_docs
        ])
    
    def update_vault(self):
        """Re-index vault when content changes."""
        if LANGCHAIN_AVAILABLE and self.vectorstore:
            try:
                self.documents = self.loader.load()
                self.chunks = self.splitter.split_documents(self.documents)
                self.vectorstore = Chroma.from_documents(
                    documents=self.chunks,
                    embedding=self.embeddings,
                    persist_directory="./data/obsidian_vectors"
                )
                logger.info("Vault updated successfully")
            except Exception as e:
                logger.error(f"Failed to update vault: {e}")
        else:
            self.documents = self._load_markdown_files()
            logger.info("Simple RAG vault updated")
    
    def get_knowledge_categories(self) -> List[str]:
        """Get available knowledge categories from vault structure."""
        if not self.vault_path.exists():
            return []
        
        categories = set()
        for item in self.vault_path.iterdir():
            if item.is_dir():
                categories.add(item.name)
        
        return sorted(list(categories))
    
    def search_by_category(self, category: str, query: str = "") -> str:
        """Search within a specific category."""
        category_path = self.vault_path / category
        if not category_path.exists():
            return f"Category '{category}' not found."
        
        # Filter documents by category
        category_docs = []
        for doc in self.documents:
            if category in doc['source']:
                category_docs.append(doc)
        
        if not category_docs:
            return f"No documents found in category '{category}'."
        
        if not query:
            return "\n\n---\n\n".join([
                f"**{doc['title']}**\n{doc['content'][:500]}..."
                for doc in category_docs[:5]
            ])
        
        # Search within category
        query_lower = query.lower()
        scored_docs = []
        
        for doc in category_docs:
            content_lower = doc['content'].lower()
            score = sum(content_lower.count(word) for word in query_lower.split())
            if score > 0:
                scored_docs.append((score, doc))
        
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return "\n\n---\n\n".join([
            f"**{doc['title']}**\n{doc['content'][:1000]}..."
            for score, doc in scored_docs[:3]
        ])


def create_sample_vault(vault_path: str = "~/hyperkit-kb"):
    """Create a sample Obsidian vault structure."""
    vault = Path(vault_path).expanduser()
    vault.mkdir(parents=True, exist_ok=True)
    
    # Create directory structure
    (vault / "Contracts").mkdir(exist_ok=True)
    (vault / "Audits").mkdir(exist_ok=True)
    (vault / "Templates").mkdir(exist_ok=True)
    (vault / "Prompts").mkdir(exist_ok=True)
    
    # Create sample files
    sample_files = {
        "Contracts/ERC20-patterns.md": """# ERC20 Token Patterns

## Basic ERC20 Implementation
```solidity
contract ERC20Token is ERC20, Ownable {
    constructor() ERC20("Token", "TKN") {}
    
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }
}
```

## Security Considerations
- Use OpenZeppelin contracts
- Implement proper access controls
- Add reentrancy guards
- Validate all inputs
""",
        
        "Contracts/DeFi-vaults.md": """# DeFi Vault Patterns

## Staking Vault
```solidity
contract StakingVault {
    mapping(address => uint256) public stakedAmount;
    uint256 public totalStaked;
    
    function stake() external payable {
        stakedAmount[msg.sender] += msg.value;
        totalStaked += msg.value;
    }
}
```

## Yield Farming
- Compound interest calculations
- Reward distribution mechanisms
- Emergency pause functionality
""",
        
        "Audits/Common-vulnerabilities.md": """# Common Smart Contract Vulnerabilities

## Reentrancy Attacks
- Use ReentrancyGuard
- Follow Checks-Effects-Interactions pattern
- Avoid external calls in state-changing functions

## Integer Overflow/Underflow
- Use SafeMath or Solidity 0.8+
- Validate input ranges
- Check for edge cases

## Access Control Issues
- Implement proper role-based access
- Use OpenZeppelin AccessControl
- Validate caller permissions
""",
        
        "Templates/Uniswap-template.md": """# Uniswap V2 Template

## Basic AMM Contract
```solidity
contract UniswapV2Pair {
    uint public constant MINIMUM_LIQUIDITY = 10**3;
    uint public constant K_FACTOR = 1000;
    
    function addLiquidity(uint amountA, uint amountB) external {
        // Implementation
    }
}
```

## Key Features
- Constant product formula
- Fee mechanism
- Liquidity provision
""",
        
        "Prompts/generation-prompts.md": """# Contract Generation Prompts

## ERC20 Token
"Create a secure ERC20 token with minting, burning, and pausable functionality"

## DeFi Vault
"Create a yield farming vault with staking rewards and emergency pause"

## NFT Contract
"Create an NFT contract with metadata, royalties, and batch minting"

## Governance Token
"Create a governance token with voting, delegation, and proposal mechanisms"
"""
    }
    
    for file_path, content in sample_files.items():
        file_full_path = vault / file_path
        with open(file_full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    logger.info(f"Sample Obsidian vault created at {vault}")


if __name__ == "__main__":
    # Create sample vault for testing
    create_sample_vault()
    print("Sample Obsidian vault created!")
