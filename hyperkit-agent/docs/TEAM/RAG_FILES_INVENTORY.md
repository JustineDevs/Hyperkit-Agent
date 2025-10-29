# RAG-Related Files Inventory

## Overview
Complete list of all RAG (Retrieval-Augmented Generation) related files in the HyperKit-Agent codebase.

---

## 📁 Core RAG Services

### Primary RAG Implementation
- **`services/rag/__init__.py`** - RAG module exports (VectorStore, DocumentRetriever)
- **`services/rag/ipfs_rag.py`** - IPFS Pinata RAG implementation (main RAG service)
- **`services/rag/vector_store.py`** - Vector store implementation for embeddings
- **`services/rag/retriever.py`** - Document retrieval service
- **`services/rag/enhanced_retriever.py`** - Enhanced RAG retriever with advanced features
- **`services/rag/defi_patterns.py`** - DeFi-specific pattern matching for RAG

### Core RAG Service
- **`services/core/rag.py`** - Consolidated RAG service wrapper
- **`services/core/rag_template_fetcher.py`** - Template fetcher from IPFS CID registry

---

## 📦 Template Files

### Template Registry
- **`docs/RAG_TEMPLATES/cid-registry.json`** - CID registry for all IPFS templates

### Template Source Files (`.txt`)
All templates in `artifacts/rag_templates/`:
- `contract-generation-prompt.txt` - Contract generation prompts
- `dao-governance-template.txt` - DAO governance template
- `dex-template.txt` - DEX (AMM) template
- `erc20-template.txt` - ERC20 token template
- `erc721-template.txt` - ERC721 NFT template
- `gas-optimization-audit.txt` - Gas optimization audit template
- `generation-style-prompt.txt` - Style prompt template
- `hardhat-deploy.txt` - Hardhat deployment template
- `lending-pool-template.txt` - Lending pool template
- `nft-collection-template.txt` - NFT collection template
- `security-checklist.txt` - Security audit checklist
- `security-prompts.txt` - Security prompt templates
- `staking-pool-template.txt` - Staking pool template

---

## 🔧 IPFS/Storage Services

### IPFS Integration
- **`services/storage/ipfs_client.py`** - IPFS client for uploading/retrieving content
- **`services/storage/pinata_client.py`** - Pinata-specific IPFS client
- **`services/verification/ipfs_storage.py`** - IPFS storage for verification data

### Storage Services
- **`services/core/storage.py`** - Core storage service with IPFS support

---

## 🛠️ Scripts & Automation

### CI/CD Scripts
- **`scripts/ci/upload_rag_templates_to_ipfs.py`** - Upload templates to IPFS Pinata
- **`scripts/ci/prepare_rag_templates.py`** - Prepare templates for IPFS upload
- **`scripts/ci/run_all_updates.py`** - Automation script (includes RAG updates)

### Development Scripts
- **`scripts/dev/setup_rag_vectors.py`** - Setup vector stores with IPFS support

---

## 📋 CLI Commands

### Test Command
- **`cli/commands/test_rag.py`** - CLI command to test RAG functionality

### Command Integration
RAG is integrated into:
- `cli/commands/generate.py` - Uses templates for contract generation
- `cli/commands/deploy.py` - Uses deployment templates
- `cli/commands/audit.py` - Uses security templates
- `cli/commands/workflow.py` - Uses all templates

---

## 📚 Documentation

### Guides
- **`docs/GUIDE/IPFS_RAG_GUIDE.md`** - IPFS RAG integration guide
- **`docs/GUIDE/PINATA_SETUP_GUIDE.md`** - Pinata setup and configuration
- **`docs/GUIDE/CONFIGURATION_GUIDE.md`** - Configuration including RAG settings
- **`docs/GUIDE/MIGRATION_GUIDE.md`** - Migration guide (includes RAG migration)

### Technical Documentation
- **`docs/TEAM/TECHNICAL_DOCUMENTATION.md`** - Technical docs including RAG architecture
- **`docs/TEAM/ARCHITECTURE_DIAGRAMS.md`** - Architecture diagrams (includes RAG)

### Template Documentation
- **`docs/RAG_TEMPLATES/README.md`** - RAG templates documentation
- **`docs/RAG_TEMPLATES/UPLOAD_PROCESS.md`** - Template upload process guide

---

## 🧪 Tests

### RAG-Specific Tests
- **`tests/test_rag_cli_integration.py`** - CLI integration tests for RAG
- **`tests/test_rag_template_integration.py`** - Template integration tests
- **`tests/test_rag_connections.py`** - Connection and IPFS tests
- **`tests/test_real_implementations.py`** - Real implementation tests (includes RAG)
- **`tests/test_pinata_simple.py`** - Simple Pinata upload test
- **`tests/test_pinata_upload.py`** - Pinata upload integration test

---

## 💾 Data & Storage Directories

### Vector Stores
- **`data/vector_store/`** - Local vector store (ChromaDB)
- **`data/vectordb/`** - Alternative vector database location
- **`data/obsidian_vectors/`** - Legacy Obsidian vectors (deprecated)

### Backup Directories
- **`data/vector_store_backup_1761550480/`** - Vector store backup
- **`data/vector_store_backup_1761550710/`** - Vector store backup

### Cache/Artifacts
- **`artifacts/rag_templates/`** - Local cache of RAG templates

---

## ⚙️ Configuration Files

### Core Configuration
- **`config.yaml`** - Main config (includes RAG settings)
- **`hyperkit-agent/config.yaml`** - Agent-specific config (includes RAG/IPFS)

### Environment
- **`hyperkit-agent/env.example`** - Example env with RAG credentials

---

## 🔗 Integration Points

### Main Agent Integration
- **`core/agent/main.py`** - Main agent (initializes IPFS RAG system)

### Service Initialization
- **`services/__init__.py`** - Service exports (includes HyperKitRAGService)

### Generation Integration
- **`services/generation/generator.py`** - Contract generator (uses RAG templates)
- **`services/generation/prompt_parser.py`** - Prompt parser (integrates with RAG)

---

## 📊 Logs & Results

### Upload Results
- **`scripts/test_logs/ipfs_upload_results.json`** - IPFS upload results log

### Test Logs
- **`test_logs/`** - Test execution logs (may include RAG test results)

---

## 📝 Summary Statistics

- **Total RAG Python Files**: 9 core files
- **Total Template Files**: 13 `.txt` templates
- **Total Documentation Files**: 7+ markdown files
- **Total Test Files**: 6 test files
- **Total Scripts**: 3 automation scripts
- **Total Storage Directories**: 5+ data directories

---

## 🎯 Key RAG Components by Function

### Template Management
1. **Registry**: `docs/RAG_TEMPLATES/cid-registry.json`
2. **Fetcher**: `services/core/rag_template_fetcher.py`
3. **Templates**: `artifacts/rag_templates/*.txt`

### IPFS Integration
1. **Main Service**: `services/rag/ipfs_rag.py`
2. **Client**: `services/storage/ipfs_client.py`
3. **Pinata**: `services/storage/pinata_client.py`

### Vector Storage
1. **Vector Store**: `services/rag/vector_store.py`
2. **Retriever**: `services/rag/retriever.py`
3. **Enhanced**: `services/rag/enhanced_retriever.py`

### Automation
1. **Upload Script**: `scripts/ci/upload_rag_templates_to_ipfs.py`
2. **Prepare Script**: `scripts/ci/prepare_rag_templates.py`
3. **Setup Script**: `scripts/dev/setup_rag_vectors.py`

---

**Last Updated**: 2025-01-29
**Total RAG Files**: 50+

