# Developer Tools

Scripts for local development setup, installation, and workflow utilities.

## Scripts

| Script | Purpose | Arguments | OS |
|--------|---------|-----------|-----|
| `install_cli.py` | Installs HyperAgent CLI globally | - | Cross-platform |
| `install_precommit.py` | Sets up pre-commit hooks | - | Cross-platform |
| `install_mythril_windows.py` | Installs Mythril on Windows | - | Windows only |
| `setup_rag_vectors.py` | Sets up RAG vector database | - | Cross-platform |
| `setup_mcp_docker.py` | Sets up MCP Docker container | - | Cross-platform |
| `mythril_wrapper.py` | Wraps Mythril security scanner | - | Cross-platform |

## Usage

### Initial Setup
```bash
# Install CLI
python install_cli.py

# Setup pre-commit hooks
python install_precommit.py

# Setup RAG (requires Pinata API keys)
python setup_rag_vectors.py
```

### Platform-Specific
```bash
# Windows: Install Mythril
python install_mythril_windows.py
```

### MCP Setup
```bash
python setup_mcp_docker.py
```

## Requirements

- Python 3.11+
- Git
- Docker (for MCP setup)
- Pinata API keys (for RAG setup)

## Safe Usage

- `install_cli.py` requires admin privileges
- `setup_rag_vectors.py` requires `PINATA_API_KEY` in `.env`
- `setup_mcp_docker.py` requires Docker to be running

## Owner

HyperAgent Developer Experience Team
