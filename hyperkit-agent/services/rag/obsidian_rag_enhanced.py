"""
Enhanced Obsidian RAG Integration for Knowledge Base
Uses Obsidian vault as a markdown-based knowledge repository with API support
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

# LangChain is now completely optional - we use simple MCP instead
LANGCHAIN_AVAILABLE = False

try:
    from services.obsidian_api import ObsidianAPI
    from .defi_patterns import defi_patterns
    from services.mcp.simple_mcp_client import get_simple_mcp_client

    OBSIDIAN_API_AVAILABLE = True
except ImportError:
    OBSIDIAN_API_AVAILABLE = False
    defi_patterns = None

try:
    from services.mcp.obsidian_mcp_client import ObsidianMCPClient

    OBSIDIAN_MCP_AVAILABLE = True
except ImportError:
    OBSIDIAN_MCP_AVAILABLE = False

logger = logging.getLogger(__name__)


class ObsidianRAGEnhanced:
    """Enhanced RAG system using Obsidian vault as knowledge base with API support."""

    def __init__(
        self,
        vault_path: str = "~/hyperkit-kb",
        use_api: bool = True,
        api_key: Optional[str] = None,
        api_url: str = "http://localhost:27124",
        use_mcp: bool = False,
        mcp_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Enhanced Obsidian RAG system.

        Args:
            vault_path: Path to Obsidian vault
            use_api: Whether to use Obsidian API (if available)
            api_key: Obsidian API key
            api_url: Obsidian API URL
        """
        self.vault_path = Path(vault_path).expanduser()
        self.vectorstore = None
        self.documents = []
        self.use_api = use_api and OBSIDIAN_API_AVAILABLE
        self.api_client = None
        self.use_mcp = use_mcp and OBSIDIAN_MCP_AVAILABLE
        self.mcp_client = None
        self.mcp_config = mcp_config or {}

        # Initialize API client if requested and available
        if self.use_api and api_key:
            try:
                self.api_client = ObsidianAPI(api_key, api_url)
                if self.api_client.test_connection():
                    logger.info("Connected to Obsidian API successfully")
                else:
                    logger.warning(
                        "Failed to connect to Obsidian API, falling back to file-based RAG"
                    )
                    self.use_api = False
            except Exception as e:
                logger.warning(
                    f"Obsidian API initialization failed: {e}, falling back to file-based RAG"
                )
                self.use_api = False

        # Initialize MCP client if requested and available
        if self.use_mcp and self.mcp_config:
            try:
                # Use simple MCP client instead of Docker-based
                self.mcp_client = get_simple_mcp_client(
                    api_key=self.mcp_config.get('api_key', ''),
                    base_url=self.mcp_config.get('api_url', 'http://localhost:27124')
                )
                logger.info("Simple MCP client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize simple MCP client: {e}. Using API-based RAG.")
                self.use_mcp = False

        # Set up RAG system - prioritize simple MCP, then API, then DeFi patterns only
        if self.use_mcp and self.mcp_client:
            self._setup_simple_mcp_rag()
        elif self.use_api and OBSIDIAN_API_AVAILABLE:
            self._setup_api_rag()
        else:
            # Fallback to DeFi patterns only
            self.documents = []
            logger.info("Using DeFi patterns only (no external RAG system available)")

        logger.info(
            f"Enhanced Obsidian RAG initialized with {'Simple MCP' if self.use_mcp else 'API' if self.use_api else 'DeFi Patterns'} method"
        )

    def _setup_simple_mcp_rag(self):
        """Set up RAG using simple MCP client."""
        try:
            # Load all knowledge base content from simple MCP
            self.documents = self._load_documents_from_simple_mcp()
            logger.info(f"Simple MCP RAG set up with {len(self.documents)} documents")
        except Exception as e:
            logger.error(f"Failed to set up simple MCP RAG: {e}")
            self.documents = []

    def _setup_mcp_rag(self):
        """Set up RAG using MCP Docker client (deprecated)."""
        try:
            # Load all knowledge base content from MCP (synchronous fallback)
            self.documents = self._load_documents_from_mcp_sync()
            logger.info(f"MCP Docker RAG set up with {len(self.documents)} documents")
        except Exception as e:
            logger.error(f"Failed to set up MCP RAG: {e}")
            self.documents = []

    def _setup_api_rag(self):
        """Set up RAG using Obsidian API."""
        try:
            # Load all knowledge base content
            self.documents = self._load_documents_from_api()
            logger.info(f"Loaded {len(self.documents)} documents from Obsidian API")
        except Exception as e:
            logger.error(f"Failed to set up API RAG: {e}")
            self.documents = []

    def _setup_langchain_rag(self):
        """Set up RAG using LangChain components."""
        try:
            if not self.vault_path.exists():
                logger.warning(f"Obsidian vault not found at {self.vault_path}")
                return

            # Use free local embeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )

            # Load documents from vault
            self.loader = ObsidianLoader(str(self.vault_path))
            self.documents = self.loader.load()

            # Split documents into chunks
            self.splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=200)
            self.chunks = self.splitter.split_documents(self.documents)

            # Create vector store
            self.vectorstore = Chroma.from_documents(
                documents=self.chunks,
                embedding=self.embeddings,
                persist_directory="./data/obsidian_vectors",
            )

            logger.info(f"LangChain RAG set up with {len(self.chunks)} chunks")
        except Exception as e:
            logger.error(f"Failed to set up LangChain RAG: {e}")
            self.documents = []

    # File-based RAG removed - using cloud-based MCP Docker and API only

    async def _load_documents_from_mcp(self) -> List[Dict[str, Any]]:
        """Load documents from MCP Docker client."""
        if not self.mcp_client:
            return []

        try:
            # Get all notes from MCP
            notes = await self.mcp_client.get_all_notes()
            documents = []

            for note in notes:
                file_path = note.get("path", "")
                # Only include knowledge base files
                if any(
                    folder in file_path
                    for folder in ["Contracts/", "Audits/", "Templates/", "Prompts/"]
                ):
                    content = await self.mcp_client.get_note_content(file_path)
                    if content:
                        documents.append(
                            {
                                "page_content": content,
                                "metadata": {
                                    "source": file_path,
                                    "name": note.get("name", ""),
                                    "size": len(content),
                                },
                            }
                        )

            return documents
        except Exception as e:
            logger.error(f"Failed to load documents from MCP: {e}")
            return []

    def _load_documents_from_simple_mcp(self) -> List[Dict[str, Any]]:
        """Load documents from simple MCP client."""
        try:
            if not self.mcp_client:
                return []
            
            # Get notes from simple MCP
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                notes = loop.run_until_complete(self.mcp_client.get_notes(limit=1000))
                return notes
            finally:
                loop.close()
            
        except Exception as e:
            logger.error(f"Failed to load documents from simple MCP: {e}")
            return []

    def _load_documents_from_mcp_sync(self) -> List[Dict[str, Any]]:
        """Load documents from MCP Docker client (synchronous version)."""
        try:
            # For now, return empty documents to avoid async issues
            # In a real implementation, you would make synchronous HTTP calls
            logger.info("MCP Docker RAG initialized (async disabled for compatibility)")
            return []
            
        except Exception as e:
            logger.error(f"Failed to load documents from MCP: {e}")
            return []

    def _load_documents_from_api(self) -> List[Dict[str, Any]]:
        """Load documents from Obsidian API."""
        if not self.api_client:
            return []

        try:
            # Get all notes from the vault
            notes = self.api_client.get_all_notes()
            documents = []

            for note in notes:
                file_path = note.get("path", "")
                # Only include knowledge base files
                if any(
                    folder in file_path
                    for folder in ["Contracts/", "Audits/", "Templates/", "Prompts/"]
                ):
                    content = self.api_client.get_note_content(file_path)
                    if content:
                        documents.append(
                            {
                                "page_content": content,
                                "metadata": {
                                    "source": file_path,
                                    "title": note.get("name", ""),
                                    "created": note.get("created", ""),
                                    "modified": note.get("modified", ""),
                                },
                            }
                        )

            return documents
        except Exception as e:
            logger.error(f"Failed to load documents from API: {e}")
            return []

    def retrieve(self, query: str, k: int = 3) -> str:
        """
        Retrieve relevant context for a query.

        Args:
            query: Search query
            k: Number of documents to retrieve

        Returns:
            Retrieved context as string
        """
        # Get DeFi patterns context
        defi_context = ""
        if defi_patterns:
            defi_context = defi_patterns.get_patterns_for_query(query)
        
        # Get other context sources (prioritize working APIs)
        other_context = ""
        if self.use_mcp and self.mcp_client:
            other_context = self._retrieve_from_simple_mcp(query, k)
        elif self.use_api and self.api_client:
            other_context = self._retrieve_from_api(query, k)
        else:
            other_context = self._retrieve_simple(query, k)
        
        # Combine contexts
        contexts = [ctx for ctx in [defi_context, other_context] if ctx.strip()]
        return "\n\n---\n\n".join(contexts) if contexts else ""

    def _retrieve_from_simple_mcp(self, query: str, k: int) -> str:
        """Retrieve using simple MCP client."""
        try:
            if not self.mcp_client:
                return ""
            
            # Search notes using simple MCP
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(self.mcp_client.search_notes(query, limit=k))
                if results:
                    context_parts = []
                    for result in results[:k]:
                        content = result.get('content', '')
                        if content:
                            context_parts.append(content)
                    return "\n\n".join(context_parts)
                return ""
            finally:
                loop.close()
            
        except Exception as e:
            logger.error(f"Simple MCP retrieval failed: {e}")
            return ""

    def _retrieve_from_mcp(self, query: str, k: int) -> str:
        """Retrieve using MCP Docker client (deprecated)."""
        try:
            # For now, return empty context to avoid async issues
            # In a real implementation, you would make synchronous HTTP calls
            logger.info("MCP retrieval disabled (async compatibility)")
            return ""
            
        except Exception as e:
            logger.error(f"MCP retrieval failed: {e}")
            return ""

    def _retrieve_from_api(self, query: str, k: int) -> str:
        """Retrieve using loaded documents from API."""
        if not self.documents:
            return ""

        try:
            # Use simple keyword-based search on loaded documents
            relevant_docs = []
            query_lower = query.lower()

            for doc in self.documents:
                content = doc.get("page_content", "")
                if query_lower in content.lower():
                    relevant_docs.append(content)
                    if len(relevant_docs) >= k:
                        break

            # If no exact matches, get documents with partial matches
            if not relevant_docs:
                for doc in self.documents:
                    content = doc.get("page_content", "")
                    # Check for partial matches with individual words
                    query_words = query_lower.split()
                    if any(
                        word in content.lower() for word in query_words if len(word) > 3
                    ):
                        relevant_docs.append(content)
                        if len(relevant_docs) >= k:
                            break

            return "\n\n---\n\n".join(relevant_docs)
        except Exception as e:
            logger.error(f"API retrieval failed: {e}")
            return self._retrieve_simple(query, k)

    def _retrieve_with_vectorstore(self, query: str, k: int) -> str:
        """Retrieve using vector store similarity search."""
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            return "\n\n---\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            logger.error(f"Vector store retrieval failed: {e}")
            return self._retrieve_simple(query, k)

    def _retrieve_simple(self, query: str, k: int) -> str:
        """Simple keyword-based retrieval."""
        query_lower = query.lower()
        relevant_docs = []

        for doc in self.documents:
            content = doc.get("page_content", "")
            if query_lower in content.lower():
                relevant_docs.append(content)
                if len(relevant_docs) >= k:
                    break

        return "\n\n---\n\n".join(relevant_docs)

    def update_vault(self):
        """Update vault content."""
        if self.use_api:
            self.documents = self._load_documents_from_api()
            logger.info(f"Vault updated via API: {len(self.documents)} documents")
        else:
            if LANGCHAIN_AVAILABLE:
                self._setup_langchain_rag()
            else:
                self._setup_simple_rag()

    def get_contract_templates(self) -> List[Dict[str, Any]]:
        """Get contract templates from the vault."""
        if self.use_api and self.api_client:
            return self.api_client.get_contract_templates()
        else:
            return self._get_documents_by_folder("Templates/")

    def get_audit_checklists(self) -> List[Dict[str, Any]]:
        """Get audit checklists from the vault."""
        if self.use_api and self.api_client:
            return self.api_client.get_audit_checklists()
        else:
            return self._get_documents_by_folder("Audits/")

    def get_prompt_templates(self) -> List[Dict[str, Any]]:
        """Get prompt templates from the vault."""
        if self.use_api and self.api_client:
            return self.api_client.get_prompt_templates()
        else:
            return self._get_documents_by_folder("Prompts/")

    def get_contract_patterns(self) -> List[Dict[str, Any]]:
        """Get contract patterns from the vault."""
        if self.use_api and self.api_client:
            return self.api_client.get_contract_patterns()
        else:
            return self._get_documents_by_folder("Contracts/")

    def _get_documents_by_folder(self, folder_path: str) -> List[Dict[str, Any]]:
        """Get documents from a specific folder."""
        folder_docs = []
        for doc in self.documents:
            source = doc.get("metadata", {}).get("source", "")
            if folder_path in source:
                folder_docs.append(doc)
        return folder_docs

    def create_contract_note(
        self,
        contract_name: str,
        contract_code: str,
        description: str = "",
        category: str = "Custom",
    ) -> bool:
        """Create a contract note in the vault."""
        if self.use_api and self.api_client:
            return self.api_client.create_contract_note(
                contract_name, contract_code, description, category
            )
        else:
            logger.warning("Contract note creation only available with API mode")
            return False

    def create_audit_report(
        self, contract_name: str, audit_results: Dict[str, Any]
    ) -> bool:
        """Create an audit report in the vault."""
        if self.use_api and self.api_client:
            return self.api_client.create_audit_report(contract_name, audit_results)
        else:
            logger.warning("Audit report creation only available with API mode")
            return False

    def create_langchain_agent(self, tools: List = None, system_prompt: str = None) -> Optional[Any]:
        """
        Create a LangChain agent for advanced RAG operations
        
        Args:
            tools: List of tools for the agent
            system_prompt: System prompt for the agent
            
        Returns:
            LangChain agent or None if not available
        """
        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain not available for agent creation")
            return None
        
        try:
            # Default tools for RAG operations
            if tools is None:
                tools = [
                    self._create_search_tool(),
                    self._create_retrieve_tool(),
                    self._create_stats_tool()
                ]
            
            # Default system prompt
            if system_prompt is None:
                system_prompt = """You are a helpful assistant specialized in smart contract development and DeFi protocols. 
                You have access to a knowledge base of smart contract patterns, security best practices, and DeFi protocols.
                Use the available tools to search and retrieve relevant information from the knowledge base."""
            
            # Create agent with Google Gemini instead of OpenAI
            from core.llm.router import HybridLLMRouter
            llm_router = HybridLLMRouter()
            
            # Use the existing LLM router instead of OpenAI
            agent = create_agent(
                model="gemini:gemini-1.5-flash",  # Using Google Gemini model
                tools=tools,
                system_prompt=system_prompt
            )
            
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create LangChain agent: {e}")
            return None
    
    def _create_search_tool(self):
        """Create a search tool for the agent"""
        @tool
        def search_knowledge_base(query: str) -> str:
            """Search the knowledge base for relevant information"""
            return self.retrieve(query, k=5)
        
        return search_knowledge_base
    
    def _create_retrieve_tool(self):
        """Create a retrieve tool for the agent"""
        @tool
        def retrieve_document_content(query: str, limit: int = 3) -> str:
            """Retrieve specific document content from the knowledge base"""
            return self.retrieve(query, k=limit)
        
        return retrieve_document_content
    
    def _create_stats_tool(self):
        """Create a stats tool for the agent"""
        @tool
        def get_knowledge_base_info() -> str:
            """Get information about the knowledge base"""
            stats = self.get_knowledge_base_stats()
            return f"Knowledge base contains {stats['total_documents']} documents using {stats['method']} method"
        
        return get_knowledge_base_info

    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        stats = {
            "total_documents": len(self.documents),
            "method": "MCP-based" if self.use_mcp else ("API-based" if self.use_api else "File-based"),
            "langchain_available": LANGCHAIN_AVAILABLE,
            "api_available": OBSIDIAN_API_AVAILABLE,
            "mcp_available": OBSIDIAN_MCP_AVAILABLE,
            "mcp_enabled": self.use_mcp,
            "mcp_running": self.mcp_client.is_running if self.mcp_client else False,
        }

        if self.use_api and self.api_client:
            try:
                vault_info = self.api_client.get_vault_info()
                stats["vault_info"] = vault_info
            except Exception as e:
                logger.error(f"Failed to get vault info: {e}")

        return stats
