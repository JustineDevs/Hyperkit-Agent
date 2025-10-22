# Cloud-Based LLM Integration Guide for HyperKit Agent

## Overview
Configure your HyperKit Agent to use **cloud-based AI providers** and **MCP Docker Obsidian** for knowledge management, providing production-quality performance with scalable cloud infrastructure.

---

## Supported Cloud-Based AI Models

### 1. Google Gemini (Primary)
- **Models**: Gemini 1.5 Flash, Gemini 2.5 Pro
- **API**: https://ai.google.dev
- **Rate Limits**: 60 requests/min (free tier)
- **Best For**: Code generation, general tasks
- **Setup**:
```bash
export GOOGLE_API_KEY="your-gemini-key"
```

### 2. OpenAI (Secondary)
- **Models**: GPT-4o-mini, GPT-3.5-turbo
- **API**: https://api.openai.com
- **Rate Limits**: 200 requests/day (free tier)
- **Best For**: Complex reasoning, fallback
- **Setup**:
```bash
export OPENAI_API_KEY="your-openai-key"
```

### 3. MCP Docker Obsidian (Knowledge Base)
- **Integration**: Docker-based Model Context Protocol
- **Features**: Advanced Obsidian connectivity
- **Best For**: RAG context retrieval
- **Setup**:
```bash
export OBSIDIAN_MCP_API_KEY="your-obsidian-key"
export MCP_ENABLED=true
export DOCKER_ENABLED=true
```

---

## Cloud-Based Model Router Configuration

**core/llm/router.py**:
```python
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class HybridLLMRouter:
    """Routes requests to cloud-based AI providers: Google Gemini and OpenAI."""

    def __init__(self):
        """Initialize cloud-based AI clients."""
        self.gemini_available = False
        self.openai_available = False

        # Initialize Google Gemini
        google_key = os.getenv("GOOGLE_API_KEY")
        if google_key and google_key.strip() and google_key != "your_google_api_key_here":
            try:
                import google.generativeai as genai
                genai.configure(api_key=google_key)
                self.gemini_available = True
                logger.info("Google Gemini client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Gemini: {e}")
        else:
            logger.warning("Google Gemini API key not found or invalid")

        # Initialize OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key.strip() and openai_key != "your_openai_api_key_here":
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=openai_key)
                self.openai_available = True
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")
        else:
            logger.warning("OpenAI API key not found or invalid")

    def route(self, prompt: str, task_type: str = "general", prefer_local: bool = False) -> str:
        """
        Route requests to available cloud-based AI providers.

        Args:
            prompt: The input prompt
            task_type: Type of task (code, reasoning, general)
            prefer_local: Ignored (cloud-based only)

        Returns:
            Generated response from available AI provider
        """
        # Try Google Gemini first (preferred for most tasks)
        if self.gemini_available:
            try:
                return self._query_gemini(prompt, task_type)
            except Exception as e:
                logger.warning(f"Google Gemini failed: {e}")
        
        # Fallback to OpenAI if Gemini fails
        if self.openai_available:
            try:
                return self._query_openai(prompt, task_type)
            except Exception as e:
                logger.warning(f"OpenAI failed: {e}")
        
        # No providers available
        raise Exception("No cloud-based AI providers available. Please check your API keys.")

    def _query_gemini(self, prompt: str, task_type: str) -> str:
        """Query Google Gemini API."""
        import google.generativeai as genai

        # Select model based on task type
        if task_type == "code":
            model_name = "gemini-2.5-pro-preview-03-25"  # Best for code generation
        else:
            model_name = "gemini-1.5-flash"  # Fast and efficient for general tasks

        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text

    def _query_openai(self, prompt: str, task_type: str) -> str:
        """Query OpenAI API."""
        # Select model based on task type
        if task_type == "code":
            model_name = "gpt-4o-mini"  # Good for code generation
        else:
            model_name = "gpt-3.5-turbo"  # Cost-effective for general tasks

        response = self.openai_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.7
        )
        return response.choices[0].message.content

    def get_available_models(self) -> Dict[str, bool]:
        """Get status of available models."""
        return {
            "google_gemini": self.gemini_available,
            "openai": self.openai_available
        }
```

---

## MCP Docker Obsidian Integration for Knowledge Base

### Setup MCP Docker Obsidian
1. **Install Docker**: Download from https://docker.com
2. **Configure MCP**: Use the integrated setup command
3. **Vault Structure** (handled by MCP Docker):
```
hyperkit-kb/
├── Contracts/
│   ├── ERC20-patterns.md
│   ├── DeFi-vaults.md
│   └── Security-checklist.md
├── Audits/
│   ├── Common-vulnerabilities.md
│   └── Audit-reports/
├── Templates/
│   ├── Uniswap-template.md
│   └── Aave-template.md
└── Prompts/
    ├── generation-prompts.md
    └── audit-prompts.md
```

### Enhanced RAG Integration with MCP Docker + LangChain
**services/rag/obsidian_rag_enhanced.py**:
```python
import asyncio
from typing import List, Dict, Any, Optional
from langchain_community.document_loaders import ObsidianLoader
from langchain_text_splitters import MarkdownTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

class ObsidianRAGEnhanced:
    def __init__(
        self,
        vault_path: str = "~/hyperkit-kb",
        use_mcp: bool = True,
        mcp_config: Optional[Dict[str, Any]] = None,
    ):
        self.vault_path = vault_path
        self.use_mcp = use_mcp
        self.mcp_config = mcp_config or {}
        
        # Initialize MCP Docker client
        if self.use_mcp:
            self.mcp_client = self._initialize_mcp_client()
        else:
            self.mcp_client = None
        
        # Initialize LangChain components
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Set up RAG system
        if self.use_mcp and self.mcp_client:
            self._setup_mcp_rag()
        else:
            self._setup_langchain_rag()
    
    def _initialize_mcp_client(self):
        """Initialize MCP Docker client."""
        try:
            from services.mcp.obsidian_mcp_client import ObsidianMCPClient
            return ObsidianMCPClient()
        except Exception as e:
            logger.warning(f"Failed to initialize MCP client: {e}")
            return None
    
    def _setup_mcp_rag(self):
        """Set up RAG using MCP Docker client."""
        try:
            self.documents = asyncio.run(self._load_documents_from_mcp())
            logger.info(f"MCP Docker RAG set up with {len(self.documents)} documents")
        except Exception as e:
            logger.error(f"Failed to set up MCP RAG: {e}")
            self.documents = []
    
    def _setup_langchain_rag(self):
        """Set up RAG using LangChain."""
        try:
            loader = ObsidianLoader(str(self.vault_path))
            self.documents = loader.load()
            
            splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=200)
            self.chunks = splitter.split_documents(self.documents)
            
            self.vectorstore = Chroma.from_documents(
                documents=self.chunks,
                embedding=self.embeddings,
                persist_directory="./data/vectordb"
            )
            logger.info(f"LangChain RAG set up with {len(self.chunks)} chunks")
        except Exception as e:
            logger.error(f"Failed to set up LangChain RAG: {e}")
            self.documents = []
    
    def retrieve(self, query: str, k: int = 5) -> str:
        """Retrieve relevant context using MCP Docker or LangChain."""
        if self.use_mcp and self.mcp_client:
            return self._retrieve_from_mcp(query, k)
        elif hasattr(self, 'vectorstore'):
            docs = self.vectorstore.similarity_search(query, k=k)
            return "\n\n---\n\n".join([doc.page_content for doc in docs])
        else:
            return self._simple_keyword_search(query, k)
    
    def create_langchain_agent(self):
        """Create a LangChain agent with custom tools."""
        from langchain.agents import tool
        
        @tool
        def search_knowledge_base(query: str) -> str:
            """Search the knowledge base for relevant information."""
            return self.retrieve(query)
        
        @tool
        def get_knowledge_base_info() -> str:
            """Get information about the knowledge base."""
            return f"Knowledge base contains {len(self.documents)} documents"
        
        tools = [search_knowledge_base, get_knowledge_base_info]
        
        # Use Google Gemini for the agent
        llm = ChatOpenAI(
            model="gemini:gemini-1.5-flash",
            temperature=0.7
        )
        
        agent = create_agent(
            llm=llm,
            tools=tools,
            system_prompt="You are a helpful AI assistant with access to a smart contract knowledge base."
        )
        
        return agent
```

### MCP Docker Setup (Automated)
Use the integrated setup command:
```bash
python setup.py setup-mcp
```

This will:
- Check Docker installation
- Pull MCP Obsidian image
- Create MCP configuration
- Set up environment variables

---

## Updated Agent Workflow

**core/agent/main.py**:
```python
from core.llm.router import HybridLLMRouter
from services.rag.obsidian_rag_enhanced import ObsidianRAGEnhanced
from core.config.loader import get_config

class HyperKitAgent:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config()
        self.llm = HybridLLMRouter()
        
        # Initialize enhanced RAG with MCP Docker
        rag_config = self.config.get("rag_system", {})
        mcp_enabled = rag_config.get("mcp_enabled", False)
        
        mcp_config = {
            "obsidian_host": "host.docker.internal",
            "obsidian_api_key": self.config.get("OBSIDIAN_MCP_API_KEY")
        }
        
        self.rag = ObsidianRAGEnhanced(
            vault_path="",  # MCP Docker handles vault access
            use_mcp=mcp_enabled,
            mcp_config=mcp_config,
        )
        
        # Initialize LangChain agent if available
        try:
            self.langchain_agent = self.rag.create_langchain_agent()
        except Exception as e:
            logger.warning(f"Failed to create LangChain agent: {e}")
            self.langchain_agent = None
    
    def generate_contract(self, user_prompt: str, context: str = ""):
        # Retrieve context from MCP Docker Obsidian
        rag_context = self.rag.retrieve(user_prompt)
        
        # Combine with provided context
        full_context = f"{rag_context}\n\n{context}" if context else rag_context
        
        # Use Google Gemini for code generation
        full_prompt = f"""
        Context from knowledge base:
        {full_context}
        
        User request:
        {user_prompt}
        
        Generate a secure Solidity smart contract with proper error handling and security measures.
        """
        
        contract_code = self.llm.route(full_prompt, task_type='code')
        return {
            "contract_code": contract_code,
            "context_used": full_context,
            "provider": "google_gemini"
        }
    
    def audit_contract(self, code: str):
        # Use Google Gemini for contract auditing
        audit_prompt = f"""
        Audit this Solidity contract for security vulnerabilities and best practices:
        
        {code}
        
        Provide a detailed security analysis with:
        1. Critical issues
        2. Medium issues  
        3. Low issues
        4. Gas optimization suggestions
        5. Best practice recommendations
        """
        return self.llm.route(audit_prompt, task_type='reasoning')
    
    def run_comprehensive_workflow(self, user_prompt: str):
        """Run the complete workflow: generate, audit, deploy."""
        # Generate contract
        generation_result = self.generate_contract(user_prompt)
        
        # Audit contract
        audit_result = self.audit_contract(generation_result["contract_code"])
        
        # Deploy contract (Hyperion testnet)
        deployment_result = self.deploy_contract(
            generation_result["contract_code"],
            network="hyperion"
        )
        
        return {
            "generation": generation_result,
            "audit": audit_result,
            "deployment": deployment_result
        }
```

---

## Cost Comparison

| Model | Cost | Rate Limit | Best For |
|-------|------|------------|----------|
| Google Gemini 1.5 Flash | Free tier | 60 req/min | Fast responses, code generation |
| Google Gemini 2.5 Pro | Free tier | 60 req/min | Complex reasoning, advanced tasks |
| OpenAI GPT-4o-mini | Free credits | 200 req/day | Complex reasoning, fallback |
| OpenAI GPT-3.5-turbo | Free credits | 200 req/day | Cost-effective general tasks |
| MCP Docker Obsidian | Free (local) | Unlimited | Knowledge base access |

---

## Setup Instructions

### 1. Install Docker (Required for MCP)
```bash
# Windows: Download Docker Desktop from https://docker.com
# Linux/Mac: 
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### 2. Configure Environment Variables
```bash
# .env
# AI Provider API Keys (Cloud-Based)
GOOGLE_API_KEY=AIza...
OPENAI_API_KEY=sk-...

# MCP Configuration
MCP_ENABLED=true
MCP_CONFIG_PATH=mcp_config.json
OBSIDIAN_MCP_API_KEY=your_obsidian_api_key_here

# Docker Configuration
DOCKER_ENABLED=true
OBSIDIAN_HOST=host.docker.internal

# Blockchain Configuration (Hyperion Focus)
DEFAULT_NETWORK=hyperion
HYPERION_RPC_URL=https://hyperion-testnet.metisdevops.link
HYPERION_CHAIN_ID=133717
HYPERION_EXPLORER_URL=https://hyperion-testnet-explorer.metisdevops.link

# Wallet Configuration
DEFAULT_PRIVATE_KEY=your_wallet_private_key_here
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up MCP Docker Obsidian
```bash
# Automated setup
python setup.py setup-mcp

# Or manual setup
python setup.py setup-obsidian
```

### 5. Test Integration
```python
from core.agent.main import HyperKitAgent

agent = HyperKitAgent()
result = agent.run_comprehensive_workflow("Create an ERC20 token with minting capability")
print(result)
```

---

## Fallback Strategy

The system automatically handles fallbacks:
```python
def route_with_fallback(self, prompt, task_type):
    # Try Google Gemini first (preferred)
    if self.gemini_available:
        try:
            return self._query_gemini(prompt, task_type)
        except Exception:
            pass
    
    # Fallback to OpenAI if Gemini fails
    if self.openai_available:
        try:
            return self._query_openai(prompt, task_type)
        except Exception:
            pass
    
    # No providers available
    raise Exception("No cloud-based AI providers available. Please check your API keys.")
```

---

## Key Benefits

### ✅ **Cloud-Based Architecture**
- **Scalable**: No local resource limitations
- **Reliable**: Professional cloud infrastructure
- **Maintained**: Always up-to-date models
- **Fast**: Optimized cloud performance

### ✅ **MCP Docker Obsidian**
- **Advanced Integration**: Docker-based Model Context Protocol
- **Scalable**: Containerized knowledge base
- **Reliable**: Professional Obsidian connectivity
- **Maintainable**: Easy setup and configuration

### ✅ **LangChain Integration**
- **Semantic Search**: Advanced vector-based retrieval
- **Agent Creation**: Custom AI agents with tools
- **Flexible**: Multiple RAG strategies
- **Extensible**: Easy to add new capabilities

This configuration enables a **production-ready, cloud-based HyperKit Agent** with advanced knowledge management and scalable AI capabilities.