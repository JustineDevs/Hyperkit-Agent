<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: 1.4.6  
**Last Verified**: 2025-10-28  
**Commit**: `6f63afe4`  
**Branch**: `main`  
<!-- AUDIT_BADGE_END -->

---
up: 
related: 
created: 2025-01-25 12:00
aliases: HyperKit MCP Builder, MCP Server Specification
tags: [mcp, builder, specification, ai-agent]
---

# HyperKit MCP Builder Prompt Specification

**Project Status**: ✅ **PRODUCTION READY**  
**Current Version**: v1.2.0  
**Last Updated**: October 27, 2025

***

## Overview

This document provides a comprehensive specification for building **HyperKit Model Context Protocol (MCP) Servers**—AI-powered smart contract lifecycle management with RAG integration, comprehensive auditing, batch operations, and multi-chain deployment capabilities for the Hyperion ecosystem.

**Core Purpose**: Enable AI assistants (Claude Desktop, custom AI agents) to interact with HyperKit's complete smart contract workflow through a standardized MCP interface.

**Status**: Fully implemented and production-ready. All MCP specifications operational.

***

## INITIAL CLARIFICATIONS

Before generating the HyperKit MCP server, please provide:

1. **Service/Tool Name**: Briefly describe which HyperKit capability the MCP server should expose (e.g., AI contract generation, multi-source audit, dApp scaffolding, deployment, batch operations)
2. **API Documentation**: Specify any network, block explorer, audit, AI, or RAG API documentation URLs required for integration (Hyperion, Metis, Polygon, Pinata, etc.)
3. **Required Features**: List every feature/function you want exposed via MCP tools (e.g., batch audit, on-chain registry logging, context retrieval, vector fetch, contract generation)
4. **Authentication**: Detail secrets/environment (API keys, RPC endpoints, .env usage), NOT inline values—use Docker secrets or environment variables
5. **Data Sources**: What files, networks, APIs, vector databases, or registries need to be accessible? (Smart contracts, RAG vector stores, IPFS/Pinata, explorer APIs, Obsidian vaults)

**If clarification is needed, ask for more information before generating code.**

***

# INSTRUCTIONS FOR THE LLM

## YOUR ROLE

You are a **Model Context Protocol (MCP) server developer** building a complete, working MCP server for HyperKit-Agent—covering smart contract generation, auditing, reporting, deployment, registry logging, batch tooling, and RAG/vector integration.

## CLARIFICATION PROCESS

Do NOT proceed unless you have:

- **Service name & description**—what this server uniquely enables for HyperKit
- **API documentation/links**—integrations with Hyperion/LazAI, audit/report endpoints, RAG/Obsidian vector APIs, explorer APIs
- **Tool requirements** (explicit list)—e.g., "ERC20 deploy", "Security audit", "RAG retrieval", "IPFS upload/fetch", "batch operations", "registry logging"
- **Authentication method**—.env, Docker secrets, environment variables—NOT inline values
- **Output preference**—JSON, Markdown, transaction metadata, formatted strings, etc.

**ASK for missing items before proceeding.**

***

## YOUR OUTPUT STRUCTURE

Organize your response in **TWO sections**:

### SECTION 1: FILES TO CREATE

Generate **EXACTLY these 5 files (no duplication)**:

1. **Dockerfile**:  
   - Python 3.11-slim  
   - Non-root user (`mcpuser`), workdir `/app`  
   - Install only required dependencies  
   - Production-ready for HyperKit MCP Server

2. **requirements.txt**:  
   - `mcp[cli]>=1.2.0`  
   - `httpx`, `web3`, `eth-account`, `py-solc-x`, `jinja2`  
   - Any required HyperKit/AI/RAG dependencies  
   - Additional libraries for context retrieval, batch processing, vector operations

3. **hyperkit_mcp_server.py**:  
   - Implement ALL specified MCP tools matching the repo's feature set  
   - Logging to stderr  
   - **NO** `@mcp.prompt()` decorators or complex type hints  
   - All tool params default to empty string  
   - Each function is error-safe, returns formatted strings only  
   - Use httpx/web3/obsidian/IPFS/AI APIs as per feature spec

4. **README.txt**:  
   - Covers role, features, installation, dev usage, tool list, troubleshooting, secret handling, architecture, license

5. **CATALOG.md**:  
   - MCP catalog entry: version, name, displayName, registry section, description, type, dateAdded (ISO 8601), image, ref, tools, secrets, metadata

**No file duplication or placeholder content.**

***

### SECTION 2: Installation Instructions for the User

Present commands as a clean, numbered sequence:

1. **Create Project Directory**
```bash
mkdir hyperkit-mcp-server
cd hyperkit-mcp-server
# Save all 5 files here
```

2. **Build Docker Image**
```bash
docker build -t hyperkit-mcp-server .
```

3. **Configure Secrets** (if required)
```bash
docker mcp secret set HYPERKIT_API_KEY="your-api-key"
docker mcp secret set PRIVATE_KEY="your-private-key"
docker mcp secret list  # Verify secrets
```

4. **Create MCP Catalog**
```bash
mkdir -p ~/.docker/mcp/catalogs
nano ~/.docker/mcp/catalogs/hyperkit-catalog.yaml
# Paste provided catalog entry here
```

5. **Update MCP Registry**
```bash
nano ~/.docker/mcp/registry.yaml
# Add hyperkit-mcp-server to registry: section
```

6. **Configure Claude Desktop/AI Gateway**
Add this to config (exact JSON, no comments):
```json
{
  "mcpServers": {
    "mcp-toolkit-gateway": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "-v", "~/.docker/mcp:/mcp",
        "docker/mcp-gateway",
        "--catalog=/mcp/catalogs/docker-mcp.yaml",
        "--catalog=/mcp/catalogs/hyperkit-catalog.yaml",
        "--config=/mcp/config.yaml",
        "--registry=/mcp/registry.yaml",
        "--transport=stdio"
      ]
    }
  }
}
```

7. **Restart Claude Desktop/AI Gateway**

8. **Test MCP Server**
```bash
docker mcp server list
docker logs <container_name>
```

***

## Critical Rules for Code Generation

### DO NOT USE
- `@mcp.prompt()` decorators—they break Claude Desktop
- `prompt` parameter to FastMCP()—breaks integration
- Complex type hints (`Optional`, `Union`, `List[str]`, etc.)
- Multi-line docstrings—causes gateway panic errors
- Default values as `None`—use empty strings instead

### MUST USE
- `@mcp.tool()` decorators only
- Single-line docstrings: `"""What this tool does - one line max."""`
- Empty string defaults: `param: str = ""`
- Error handling: try/except blocks for all operations
- Return strings: All tools must return formatted strings
- Logging to stderr with proper configuration
- Non-root user in Docker container

### Parameter Validation Pattern
```python
if not param.strip():
    return "❌ Error: Parameter is required"
```

### Error Handling Pattern
```python
try:
    # Implementation
    return f"✅ Success: {result}"
except Exception as e:
    logger.error(f"Error: {e}")
    return f"❌ Error: {str(e)}"
```

***

## HyperKit MCP Server Architecture

### Current Project Structure Reference

```
hyperkit-agent/
├── cli/                      # CLI commands (generate, deploy, audit, etc.)
│   ├── commands/
│   │   ├── generate.py      # Contract generation
│   │   ├── deploy.py        # Deployment
│   │   ├── audit.py         # Auditing
│   │   └── batch_audit.py   # Batch operations
│   └── main.py             # CLI entry point
├── services/                 # Core services
│   ├── core/
│   │   ├── ai_agent.py     # AI agent service
│   │   ├── security.py     # Security auditing
│   │   └── rag.py           # RAG integration
│   ├── audit/               # Audit services
│   ├── deployment/          # Deployment (Foundry integration)
│   ├── generation/           # Contract generation
│   ├── monitoring/           # Monitoring services
│   ├── rag/                 # RAG/vector search
│   └── storage/             # IPFS/Pinata integration
├── mcp_server.py            # Current Obsidian MCP server
├── contracts/               # Solidity contracts
├── docs/                    # Documentation
└── tests/                   # Test suite
```

### MCP Integration Points

The HyperKit MCP server should expose these core functionalities:

1. **Contract Generation** (`cli/commands/generate.py`)
   - ERC20, ERC721, ERC1155 templates
   - Custom contract scaffolding
   - Template selection and customization

2. **Security Auditing** (`services/audit/auditor.py`)
   - Static analysis
   - Vulnerability detection
   - Gas optimization
   - Compliance checking

3. **Deployment** (`services/deployment/foundry_deployer.py`)
   - Multi-chain support (Hyperion, Metis, Polygon, etc.)
   - Constructor argument handling
   - Transaction simulation
   - Verification

4. **RAG Integration** (`services/rag/` & `services/storage/ipfs_client.py`)
   - Vector search in IPFS/Pinata
   - Obsidian vault integration
   - Template retrieval

5. **Monitoring** (`services/monitoring/`)
   - Transaction monitoring
   - Contract health checks
   - Performance metrics

***

## HyperKit-Specific Tools

### Tool 1: `hyperkit-generate-contract`

Generate secure Solidity smart contracts using HyperKit's AI agent.

**Parameters**:
- `contract_type` (string, required): "ERC20", "ERC721", "ERC1155", "custom"
- `name` (string, required): Contract name
- `features` (string, optional): Comma-separated features ("mintable,burnable,pausable")
- `network` (string, optional): Target network ("hyperion", "metis", "polygon")

**Returns**: Solidity contract code as string

**Example**:
```python
@mcp.tool()
async def hyperkit_generate_contract(contract_type: str = "", name: str = "", features: str = "", network: str = "") -> str:
    """Generate a secure Solidity smart contract with specified features."""
    if not contract_type.strip() or not name.strip():
        return "❌ Error: contract_type and name are required"
    
    try:
        # Call HyperKit generation service
        from services.generation.generator import ContractGenerator
        generator = ContractGenerator()
        contract_code = generator.generate(contract_type, name, features)
        return f"✅ Generated contract:\n\n{contract_code}"
    except Exception as e:
        return f"❌ Error: {str(e)}"
```

### Tool 2: `hyperkit-audit-contract`

Analyze smart contracts for vulnerabilities using HyperKit's audit system.

**Parameters**:
- `contract_source` (string, required): Solidity code or contract address
- `network` (string, optional): "hyperion", "metis", "polygon"
- `severity` (string, optional): "high", "medium", "low", "all"

**Returns**: Audit report as formatted string

**Example**:
```python
@mcp.tool()
async def hyperkit_audit_contract(contract_source: str = "", network: str = "", severity: str = "all") -> str:
    """Analyze smart contract for security vulnerabilities and issues."""
    if not contract_source.strip():
        return "❌ Error: contract_source is required"
    
    try:
        from services.audit.auditor import ContractAuditor
        auditor = ContractAuditor()
        report = await auditor.audit(contract_source, network, severity)
        return f"✅ Audit Report:\n\n{report}"
    except Exception as e:
        return f"❌ Error: {str(e)}"
```

### Tool 3: `hyperkit-deploy-contract`

Deploy smart contracts using HyperKit's Foundry-based deployment system.

**Parameters**:
- `contract_path` (string, required): Path to Solidity contract
- `network` (string, required): Target network
- `constructor_args` (string, optional): JSON string of constructor arguments

**Returns**: Deployment details (address, tx hash, explorer URL)

**Example**:
```python
@mcp.tool()
async def hyperkit_deploy_contract(contract_path: str = "", network: str = "", constructor_args: str = "") -> str:
    """Deploy a smart contract to specified network using Foundry."""
    if not contract_path.strip() or not network.strip():
        return "❌ Error: contract_path and network are required"
    
    try:
        from services.deployment.foundry_deployer import FoundryDeployer
        deployer = FoundryDeployer()
        result = await deployer.deploy(contract_path, network, constructor_args)
        return f"✅ Deployed:\nAddress: {result['address']}\nTx: {result['tx_hash']}\nExplorer: {result['url']}"
    except Exception as e:
        return f"❌ Error: {str(e)}"
```

### Tool 4: `hyperkit-search-rag`

Search RAG templates and documents from IPFS/Pinata or Obsidian vault.

**Parameters**:
- `query` (string, required): Search query
- `source` (string, optional): "ipfs", "obsidian", "local"
- `limit` (string, optional): Number of results (default "10")

**Returns**: Search results as formatted string

**Example**:
```python
@mcp.tool()
async def hyperkit_search_rag(query: str = "", source: str = "ipfs", limit: str = "10") -> str:
    """Search RAG templates and documents from IPFS, Obsidian, or local storage."""
    if not query.strip():
        return "❌ Error: query is required"
    
    try:
        from services.rag.retriever import RAGRetriever
        retriever = RAGRetriever()
        results = await retriever.search(query, source, int(limit))
        formatted = "\n".join([f"- {r['title']}: {r['summary']}" for r in results])
        return f"✅ Found {len(results)} results:\n\n{formatted}"
    except Exception as e:
        return f"❌ Error: {str(e)}"
```

### Tool 5: `hyperkit-upload-to-ipfs`

Upload documents or RAG templates to IPFS via Pinata.

**Parameters**:
- `content` (string, required): Content to upload
- `filename` (string, required): Filename
- `metadata` (string, optional): JSON metadata string

**Returns**: IPFS CID and gateway URL

**Example**:
```python
@mcp.tool()
async def hyperkit_upload_to_ipfs(content: str = "", filename: str = "", metadata: str = "") -> str:
    """Upload content to IPFS via Pinata and return CID."""
    if not content.strip() or not filename.strip():
        return "❌ Error: content and filename are required"
    
    try:
        from services.storage.ipfs_client import IPFSClient
        client = IPFSClient()
        cid = await client.upload_document(content, filename, metadata)
        return f"✅ Uploaded to IPFS:\nCID: {cid}\nGateway: https://gateway.pinata.cloud/ipfs/{cid}"
    except Exception as e:
        return f"❌ Error: {str(e)}"
```

***

## Security Considerations

### Environment Variables

All sensitive data must be loaded from environment variables:

```python
import os

# Load from environment
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
PINATA_API_KEY = os.getenv("PINATA_API_KEY")
PINATA_SECRET_KEY = os.getenv("PINATA_SECRET_KEY")

if not PRIVATE_KEY:
    logger.warning("PRIVATE_KEY not set")
```

### Docker Secrets Configuration

```yaml
secrets:
  - name: PRIVATE_KEY
    env: PRIVATE_KEY
    example: "0x..."
  - name: PINATA_API_KEY
    env: PINATA_API_KEY
    example: "your_pinata_api_key"
  - name: PINATA_SECRET_KEY
    env: PINATA_SECRET_KEY
    example: "your_pinata_secret_key"
```

***

## Response Format

All MCP responses should follow this format:

### Success Response
```python
return f"""✅ Success: {operation_name}

Details:
- Field 1: {value1}
- Field 2: {value2}

{additional_info}
"""
```

### Error Response
```python
return f"❌ Error: {error_message}"
```

### Multi-line Data
```python
return f"""📊 Results:

{sorted_results}
"""
```

### File Operations
```python
return f"""📁 File Operations:

- Created: {file1}
- Updated: {file2}
"""
```

### Blockchain Operations
```python
return f"""🌐 Transaction Details:

Address: {address}
Tx Hash: {tx_hash}
Network: {network}
Explorer: {explorer_url}
"""
```

***

## Testing

### Local Testing

```bash
# Set environment variables
export PRIVATE_KEY="0x..."
export PINATA_API_KEY="..."
export PINATA_SECRET_KEY="..."

# Run directly
python hyperkit_mcp_server.py

# Test MCP protocol
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python hyperkit_mcp_server.py
```

### Docker Testing

```bash
# Build image
docker build -t hyperkit-mcp-server .

# Run with environment variables
docker run -e PRIVATE_KEY="..." hyperkit-mcp-server

# Test with docker mcp
docker mcp server list
```

***

## Troubleshooting

### Common Issues

1. **Tools not appearing in Claude Desktop**
   - Verify Docker image built successfully
   - Check catalog and registry files
   - Ensure Claude Desktop config includes custom catalog
   - Restart Claude Desktop

2. **Authentication errors**
   - Verify secrets with `docker mcp secret list`
   - Ensure secret names match in code and catalog

3. **Import errors**
   - Check `requirements.txt` includes all dependencies
   - Verify relative imports match project structure

4. **Network connection errors**
   - Verify RPC endpoints are accessible
   - Check API keys and permissions
   - Ensure Docker network configuration is correct

***

## Complete README Template

```markdown
# HyperKit MCP Server

A Model Context Protocol (MCP) server that enables AI assistants to interact with HyperKit's smart contract development platform.

## Purpose

This MCP server provides AI assistants (Claude Desktop, custom AI agents) with secure, automated access to HyperKit's complete smart contract workflow:
- Contract generation (ERC20, ERC721, ERC1155, custom)
- Security auditing and vulnerability detection
- Multi-chain deployment (Hyperion, Metis, Polygon, etc.)
- RAG template search and IPFS integration
- Gas optimization and compliance checking

## Features

### Current Implementation
- `hyperkit-generate-contract` - Generate secure Solidity contracts
- `hyperkit-audit-contract` - Analyze contracts for vulnerabilities
- `hyperkit-deploy-contract` - Deploy contracts to EVM networks
- `hyperkit-search-rag` - Search RAG templates from IPFS/Obsidian
- `hyperkit-upload-to-ipfs` - Upload content to IPFS via Pinata

## Prerequisites

- Docker Desktop with MCP Toolkit enabled
- Docker MCP CLI plugin (`docker mcp` command)
- API keys for:
  - RPC endpoints (Hyperion, Metis, Polygon)
  - Pinata IPFS (for RAG templates)
  - Private key for deployment (stored securely)

## Installation

See the step-by-step instructions provided with the files.

## Usage Examples

In Claude Desktop, you can ask:
- "Generate an ERC20 token contract named GAMEX with mint and burn features"
- "Audit this contract address 0x... for security risks"
- "Deploy this contract to Hyperion network"
- "Search for gas optimization templates in RAG"
- "Upload this document to IPFS"

## Architecture

```
Claude Desktop → MCP Gateway → HyperKit MCP Server → HyperKit Services
                                        ↓
                        Docker Desktop Secrets
                        (API keys, private keys)
```

## Development

### Local Testing

```bash
# Set environment variables
export PRIVATE_KEY="0x..."
export PINATA_API_KEY="..."
export PINATA_SECRET_KEY="..."

# Run directly
python hyperkit_mcp_server.py

# Test MCP protocol
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python hyperkit_mcp_server.py
```

### Adding New Tools

1. Add the function to `hyperkit_mcp_server.py`
2. Decorate with `@mcp.tool()`
3. Add to catalog entry with tool name
4. Rebuild Docker image

## Security Considerations

- All secrets stored in Docker Desktop secrets
- Never hardcode credentials
- Running as non-root user (mcpuser)
- Sensitive data never logged
- Private keys never appear in responses

## License

MIT License
```

***

## Final Checklist for LLM

Before presenting your response, verify:

- [ ] Created all 5 files with proper naming
- [ ] No `@mcp.prompt()` decorators used
- [ ] No `prompt` parameter in FastMCP()
- [ ] No complex type hints from typing module
- [ ] ALL tool docstrings are SINGLE-LINE only
- [ ] ALL parameters default to empty strings (`""`) not None
- [ ] All tools return strings (formatted with emojis)
- [ ] Check for empty strings with `.strip()`
- [ ] Error handling in every tool
- [ ] Clear separation between files and user instructions
- [ ] All placeholders replaced with actual values
- [ ] Usage examples provided for each tool
- [ ] Security handled via Docker secrets
- [ ] Catalog includes version, name, displayName, registry
- [ ] Registry entries under `registry:` key
- [ ] Date format is ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
- [ ] Claude config JSON has no comments
- [ ] Each file appears exactly once
- [ ] Instructions are clear and numbered

---

## FINAL GENERATION CHECKLIST FOR THE LLM

Before presenting your response, verify:

- [ ] Created all 5 files with proper naming
- [ ] No `@mcp.prompt()` decorators used
- [ ] No `prompt` parameter in FastMCP()
- [ ] No complex type hints (`Optional`, `Union`, `List[str]`, etc.)
- [ ] ALL tool docstrings are SINGLE-LINE only
- [ ] ALL parameters default to empty strings (`""`) not None
- [ ] All tools return strings (formatted with emojis)
- [ ] Check for empty strings with `.strip()`
- [ ] Error handling in every tool
- [ ] Clear separation between files and user instructions
- [ ] All placeholders replaced with actual values
- [ ] Usage examples provided for each tool
- [ ] Security handled via Docker secrets/environment
- [ ] Catalog includes version, name, displayName, registry
- [ ] Registry entries under `registry:` key with `ref: ""`
- [ ] Date format is ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
- [ ] Claude config JSON has no comments
- [ ] Each file appears exactly once
- [ ] Instructions are clear and numbered
- [ ] Dockerfile uses `python:3.11-slim` (not 3.12)
- [ ] Non-root user `mcpuser` with UID 1000
- [ ] All secrets set via Docker MCP plugin
- [ ] Requirements.txt includes all necessary dependencies
- [ ] README.txt covers all essential sections

### Dockerfile Template
```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY hyperkit_mcp_server.py .
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser
CMD ["python", "hyperkit_mcp_server.py"]
```

### Requirements.txt Template
```
mcp[cli]>=1.2.0
httpx
web3
eth-account
py-solc-x
jinja2
# Add more dependencies as needed for specific tools
```

### Key Features to Support
- AI-powered contract generation
- Multi-source security auditing
- Batch audit operations
- dApp scaffolding (full-stack)
- Multi-chain deployment (Hyperion, Metis, Polygon)
- On-chain audit registry logging
- RAG template search and retrieval
- IPFS/Pinata integration
- Obsidian vault integration
- Context retrieval from vector databases

### Output Format Guidelines

Use emojis for visual clarity:
- ✅ Success operations
- ❌ Errors or failures
- ⏱️ Time-related information
- 📊 Data or statistics
- 🔍 Search or lookup operations
- ⚡ Actions or commands
- 🔒 Security-related information
- 📁 File operations
- 🌐 Network operations
- ⚠️ Warnings

### Example Response Format
```python
# Success Response
return f"""✅ Success: {operation_name}

Details:
- Field 1: {value1}
- Field 2: {value2}

{additional_info}
"""

# Error Response
return f"❌ Error: {error_message}"

# Multi-line Data
return f"""📊 Results:

{sorted_results}
"""
```

---

**If you were your most brutally honest CTO/Auditor:**  
"This MCP Builder Prompt is enterprise-grade, no-stub, all-real, and instantly actionable. Your HyperKit infrastructure can scale, integrate new tools, audit compliance, and go multi-chain, **if you keep every feature, tool, and secret as explicit, documented, and error-safe as shown. Ship it, upgrade it, never fall behind in implementation vs. documentation. This is the spec OSS teams wish they had.**"

---

<div align="center">⁂</div>

**References**:
- [MCP Specification](https://modelcontextprotocol.io/specification/2025-06-18/server/prompts)
- [MCP Documentation](https://modelcontextprotocol.io/docs/develop/build-server)
- [NetworkChuck Tutorial](https://www.youtube.com/watch?v=ZoZxQwp1PiM)
- [HyperKit Project](https://github.com/JustineDevs/HyperAgent)
- [HyperKit Repository Structure](https://github.com/JustineDevs/HyperAgent/tree/main/hyperkit-agent)
- [HyperKit Services](https://github.com/JustineDevs/HyperAgent/tree/main/hyperkit-agent/services)
- [HyperKit Documentation](https://github.com/JustineDevs/HyperAgent/tree/main/docs)
