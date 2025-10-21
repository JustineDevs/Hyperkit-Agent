"""
RAG (Retrieval-Augmented Generation) Knowledge System
Provides context-aware knowledge retrieval for smart contract generation
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class RAGRetriever:
    """
    RAG system for retrieving relevant knowledge from vector database.
    Supports multiple embedding models and vector stores.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the RAG retriever.
        
        Args:
            config: Configuration dictionary for RAG settings
        """
        self.config = config or {}
        self.embeddings = None
        self.vectorstore = None
        self.knowledge_base = {}
        
        # Initialize components
        self._initialize_embeddings()
        self._initialize_vectorstore()
        self._load_knowledge_base()
        
        logger.info("RAGRetriever initialized successfully")
    
    def _initialize_embeddings(self):
        """Initialize embedding model."""
        try:
            # Try OpenAI embeddings first
            if self.config.get('openai_api_key'):
                from langchain.embeddings import OpenAIEmbeddings
                self.embeddings = OpenAIEmbeddings(
                    openai_api_key=self.config['openai_api_key']
                )
                logger.info("Using OpenAI embeddings")
            else:
                # Fallback to sentence transformers
                from langchain.embeddings import HuggingFaceEmbeddings
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
                logger.info("Using HuggingFace embeddings")
                
        except ImportError as e:
            logger.warning(f"Failed to initialize embeddings: {e}")
            self.embeddings = None
    
    def _initialize_vectorstore(self):
        """Initialize vector store."""
        try:
            if self.embeddings:
                from langchain.vectorstores import Chroma
                
                persist_directory = self.config.get('vectorstore_path', './data/vectordb')
                os.makedirs(persist_directory, exist_ok=True)
                
                self.vectorstore = Chroma(
                    persist_directory=persist_directory,
                    embedding_function=self.embeddings
                )
                logger.info("Vector store initialized")
            else:
                logger.warning("Vector store not initialized - no embeddings available")
                
        except ImportError as e:
            logger.warning(f"Failed to initialize vector store: {e}")
            self.vectorstore = None
    
    def _load_knowledge_base(self):
        """Load knowledge base with smart contract patterns and best practices."""
        self.knowledge_base = {
            'security_patterns': {
                'reentrancy_guard': {
                    'description': 'Use ReentrancyGuard to prevent reentrancy attacks',
                    'example': '''
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract MyContract is ReentrancyGuard {
    function withdraw() external nonReentrant {
        // Safe withdrawal logic
    }
}''',
                    'tags': ['security', 'reentrancy', 'guard']
                },
                'access_control': {
                    'description': 'Implement proper access control using OpenZeppelin',
                    'example': '''
import "@openzeppelin/contracts/access/Ownable.sol";

contract MyContract is Ownable {
    function sensitiveFunction() external onlyOwner {
        // Owner-only logic
    }
}''',
                    'tags': ['security', 'access-control', 'ownership']
                },
                'safe_math': {
                    'description': 'Use SafeMath or Solidity 0.8+ built-in overflow protection',
                    'example': '''
// Solidity 0.8+ has built-in overflow protection
uint256 result = a + b; // Safe addition

// For older versions, use SafeMath
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
using SafeMath for uint256;
uint256 result = a.add(b);''',
                    'tags': ['security', 'math', 'overflow']
                }
            },
            'defi_patterns': {
                'erc20_token': {
                    'description': 'Standard ERC20 token implementation with minting',
                    'example': '''
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract MyToken is ERC20, Ownable {
    constructor() ERC20("My Token", "MTK") {
        _mint(msg.sender, 1000000 * 10**decimals());
    }
    
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }
}''',
                    'tags': ['token', 'erc20', 'minting']
                },
                'staking_contract': {
                    'description': 'Basic staking contract with rewards',
                    'example': '''
contract StakingContract {
    mapping(address => uint256) public stakedAmount;
    mapping(address => uint256) public lastStakeTime;
    
    function stake() external payable {
        stakedAmount[msg.sender] += msg.value;
        lastStakeTime[msg.sender] = block.timestamp;
    }
    
    function calculateRewards(address user) public view returns (uint256) {
        uint256 staked = stakedAmount[user];
        uint256 timeStaked = block.timestamp - lastStakeTime[user];
        return staked * timeStaked / 365 days * 10; // 10% APY
    }
}''',
                    'tags': ['staking', 'rewards', 'defi']
                }
            },
            'best_practices': {
                'events': {
                    'description': 'Always emit events for important state changes',
                    'example': '''
event Transfer(address indexed from, address indexed to, uint256 value);
event Approval(address indexed owner, address indexed spender, uint256 value);

function transfer(address to, uint256 amount) external returns (bool) {
    _transfer(msg.sender, to, amount);
    emit Transfer(msg.sender, to, amount);
    return true;
}''',
                    'tags': ['events', 'logging', 'transparency']
                },
                'error_handling': {
                    'description': 'Use custom errors for gas-efficient error handling',
                    'example': '''
error InsufficientBalance(uint256 available, uint256 required);
error UnauthorizedAccess(address caller);

function withdraw(uint256 amount) external {
    if (balanceOf[msg.sender] < amount) {
        revert InsufficientBalance(balanceOf[msg.sender], amount);
    }
    // Withdrawal logic
}''',
                    'tags': ['errors', 'gas-optimization', 'custom-errors']
                }
            }
        }
    
    async def retrieve(self, query: str, k: int = 5) -> str:
        """
        Retrieve relevant knowledge based on the query.
        
        Args:
            query: Search query
            k: Number of results to retrieve
            
        Returns:
            Concatenated relevant knowledge
        """
        try:
            # First, try vector store retrieval
            if self.vectorstore:
                docs = self.vectorstore.similarity_search(query, k=k)
                if docs:
                    return "\n\n".join([doc.page_content for doc in docs])
            
            # Fallback to keyword-based retrieval
            return self._keyword_retrieval(query, k)
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return self._keyword_retrieval(query, k)
    
    def _keyword_retrieval(self, query: str, k: int) -> str:
        """Fallback keyword-based retrieval."""
        query_lower = query.lower()
        relevant_knowledge = []
        
        # Search through knowledge base
        for category, items in self.knowledge_base.items():
            for item_name, item_data in items.items():
                # Check if query matches tags or description
                if any(tag in query_lower for tag in item_data.get('tags', [])):
                    relevant_knowledge.append({
                        'category': category,
                        'name': item_name,
                        'description': item_data['description'],
                        'example': item_data.get('example', ''),
                        'relevance_score': self._calculate_relevance_score(query_lower, item_data)
                    })
        
        # Sort by relevance score and take top k
        relevant_knowledge.sort(key=lambda x: x['relevance_score'], reverse=True)
        top_k = relevant_knowledge[:k]
        
        # Format results
        formatted_results = []
        for item in top_k:
            result = f"**{item['name'].replace('_', ' ').title()}**\n"
            result += f"Description: {item['description']}\n"
            if item['example']:
                result += f"Example:\n{item['example']}\n"
            formatted_results.append(result)
        
        return "\n\n".join(formatted_results)
    
    def _calculate_relevance_score(self, query: str, item_data: Dict[str, Any]) -> float:
        """Calculate relevance score for keyword matching."""
        score = 0.0
        
        # Check description
        description = item_data.get('description', '').lower()
        if any(word in description for word in query.split()):
            score += 1.0
        
        # Check tags
        tags = item_data.get('tags', [])
        for tag in tags:
            if tag in query:
                score += 0.5
        
        # Check example
        example = item_data.get('example', '').lower()
        if any(word in example for word in query.split()):
            score += 0.3
        
        return score
    
    async def ingest_docs(self, docs_path: str) -> bool:
        """
        Ingest documents into the vector store.
        
        Args:
            docs_path: Path to documents directory
            
        Returns:
            True if ingestion successful
        """
        try:
            if not self.vectorstore:
                logger.warning("Vector store not available for ingestion")
                return False
            
            from langchain.document_loaders import DirectoryLoader
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            
            # Load documents
            loader = DirectoryLoader(docs_path)
            documents = loader.load()
            
            # Split documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            splits = text_splitter.split_documents(documents)
            
            # Add to vector store
            self.vectorstore.add_documents(splits)
            
            logger.info(f"Ingested {len(splits)} document chunks")
            return True
            
        except Exception as e:
            logger.error(f"Document ingestion failed: {e}")
            return False
    
    def add_knowledge(self, category: str, name: str, description: str, 
                     example: str = "", tags: List[str] = None):
        """
        Add knowledge to the knowledge base.
        
        Args:
            category: Knowledge category
            name: Knowledge item name
            description: Description of the knowledge
            example: Code example
            tags: List of tags
        """
        if category not in self.knowledge_base:
            self.knowledge_base[category] = {}
        
        self.knowledge_base[category][name] = {
            'description': description,
            'example': example,
            'tags': tags or []
        }
        
        logger.info(f"Added knowledge: {category}/{name}")
    
    def get_knowledge_categories(self) -> List[str]:
        """Get list of knowledge categories."""
        return list(self.knowledge_base.keys())
    
    def search_knowledge(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search knowledge base for specific information.
        
        Args:
            query: Search query
            category: Optional category filter
            
        Returns:
            List of matching knowledge items
        """
        results = []
        query_lower = query.lower()
        
        categories_to_search = [category] if category else self.knowledge_base.keys()
        
        for cat in categories_to_search:
            if cat not in self.knowledge_base:
                continue
                
            for item_name, item_data in self.knowledge_base[cat].items():
                if any(tag in query_lower for tag in item_data.get('tags', [])):
                    results.append({
                        'category': cat,
                        'name': item_name,
                        'description': item_data['description'],
                        'example': item_data.get('example', ''),
                        'tags': item_data.get('tags', [])
                    })
        
        return results


# Example usage
async def main():
    """Example usage of the RAGRetriever."""
    config = {
        'openai_api_key': 'your-api-key-here',  # Optional
        'vectorstore_path': './data/vectordb'
    }
    
    rag = RAGRetriever(config)
    
    # Test retrieval
    query = "How to implement reentrancy protection in Solidity?"
    context = await rag.retrieve(query, k=3)
    
    print("Retrieved Context:")
    print(context)
    
    # Test knowledge search
    results = rag.search_knowledge("token", category="defi_patterns")
    print("\nSearch Results:")
    for result in results:
        print(f"- {result['name']}: {result['description']}")


if __name__ == "__main__":
    asyncio.run(main())
