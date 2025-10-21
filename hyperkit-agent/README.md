# HyperKit AI Agent 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

**HyperKit AI Agent** is a comprehensive AI-powered system that combines smart contract generation, auditing, debugging, and deployment capabilities. Built for the Hyperion and Andromeda ecosystems, it enables developers to rapidly prototype, deploy, and manage smart contracts with natural language prompts.

## ✨ Features

### 🤖 AI-Powered Contract Generation
- **Natural Language to Solidity**: Generate smart contracts from plain English descriptions
- **Google Gemini Integration**: Powered by Google Gemini 2.5 Pro with free $300 credits
- **Template Library**: Pre-built templates for tokens, NFTs, DeFi vaults, and more
- **Context-Aware Generation**: RAG-powered knowledge retrieval for better results

### 🔍 Comprehensive Auditing
- **Multi-Tool Analysis**: Integration with Slither, Mythril, and custom pattern detection
- **Severity Assessment**: Automated risk scoring and vulnerability classification
- **Real-time Debugging**: EDB integration for transaction replay and debugging
- **Security Best Practices**: Built-in checks for common vulnerabilities

### 🌐 Multi-Chain Deployment
- **Cross-Chain Support**: Deploy to Hyperion, Polygon, Arbitrum, and Ethereum
- **Gas Optimization**: Automatic gas estimation and optimization
- **Contract Verification**: Automated verification on blockchain explorers
- **EIP-712 Signing**: Secure structured data signing capabilities

### 🧠 RAG Knowledge System
- **Vector Database**: ChromaDB integration for semantic search
- **Smart Contract Patterns**: Comprehensive knowledge base of best practices
- **Context Retrieval**: Relevant knowledge injection for better generation
- **Continuous Learning**: Expandable knowledge base with custom patterns

## 🆓 Google Gemini Integration

The HyperKit Agent is powered by **Google Gemini** for completely free smart contract generation:

### Google Gemini Features
- **Model**: Gemini-2.5-Pro (Latest and most powerful!)
- **Free Credits**: $300 included with Google account
- **High Quality**: Professional-grade Solidity contracts
- **Fast Response**: Quick generation times
- **Reliable**: Stable and consistent results

### Obsidian Knowledge Base
- **Markdown-based**: Store contract patterns, audit checklists, templates
- **RAG Integration**: Automatic context retrieval for better generation
- **Version Control**: Sync with Git for team collaboration

### Setup Free Models
```bash
# Install Ollama and models
python setup_free_models.py

# Test free models
python test_free_models.py

# Generate with local models
python cli.py generate "Create ERC20 token" --provider local --use-rag
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Node.js 16+ (for frontend components)
- Git
- Hyperion/Andromeda wallet (for testing)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/JustineDevs/Hyperkit-Agent.git
   cd hyperkit-agent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Run the agent**
   ```bash
   python main.py
   ```

## 🤖 AI Provider Support

HyperKit AI Agent supports multiple AI providers with automatic fallback:

### Supported Providers
- **OpenAI** - GPT-4, GPT-3.5 (Recommended)
- **DeepSeek** - Cost-effective alternative with high quality
- **xAI** - Grok models for advanced reasoning
- **GPT-OSS** - Open source GPT implementations
- **Anthropic** - Claude models for safety and reliability
- **Google** - Gemini models for multimodal capabilities
- **Alibaba DashScope** - Qwen models for Chinese language support

### Provider Selection
The agent automatically selects the best available provider based on your configured API keys. You can also specify a provider manually:

```bash
# Auto-select best available provider
python cli.py generate "Create a simple ERC20 token"

# Use specific provider
python cli.py generate "Create a DeFi vault" --provider deepseek
```

## 🔧 Usage

### Command Line Interface

```bash
# Interactive mode
python main.py

# Direct prompt
python main.py "Create a simple ERC20 token with minting functionality"

# With specific network
python main.py "Deploy a staking contract" --network hyperion
```

### Python API

```python
import asyncio
from core.agent.main import HyperKitAgent

async def main():
    config = {
        'openai_api_key': 'your-api-key',
        'networks': {
            'hyperion': 'https://hyperion-testnet.metisdevops.link'
        }
    }
    
    agent = HyperKitAgent(config)
    
    # Generate and deploy a contract
    result = await agent.run_workflow(
        "Create a DeFi vault contract with yield farming"
    )
    
    print(result)

asyncio.run(main())
```

### Workflow Example

```python
# 1. Generate contract
generation_result = await agent.generate_contract(
    "Create an ERC20 token with burn functionality"
)

# 2. Audit contract
audit_result = await agent.audit_contract(
    generation_result['contract_code']
)

# 3. Deploy if audit passes
if audit_result['severity'] in ['low', 'medium']:
    deployment_result = await agent.deploy_contract(
        generation_result['contract_code'],
        network='hyperion'
    )
```

## 🏗️ Architecture

```
hyperkit-agent/
├── core/                    # Core agent implementation
│   ├── agent/              # Main agent class
│   ├── tools/              # Agent tools and utilities
│   └── prompts/            # Prompt templates
├── services/               # Service modules
│   ├── generation/         # Contract generation
│   ├── audit/             # Security auditing
│   ├── deployment/        # Multi-chain deployment
│   └── rag/              # RAG knowledge system
├── blockchain/            # Blockchain integration
│   ├── contracts/        # Smart contract templates
│   ├── scripts/         # Deployment scripts
│   └── tests/           # Contract tests
├── api/                 # API endpoints
├── frontend/           # Web interface
└── docs/              # Documentation
```

## 🤖 Supported AI Providers

| Provider | Status | Features | Use Cases |
|----------|--------|----------|-----------|
| Claude (Anthropic) | ✅ Active | Smart contract generation, security analysis | DeFi protocols, complex contracts |
| GPT-4 (OpenAI) | ✅ Active | Code completion, documentation | dApp development, testing |
| Gemini (Google) | ✅ Active | Multimodal analysis, code review | UI components, visual analysis |
| DeepSeek | ✅ Active | Code optimization, gas efficiency | Performance-critical contracts |
| Qwen (Alibaba) | ✅ Active | Multi-language support, testing | International dApps |

## 🌐 Supported Networks

| Network | Status | Features | Use Cases |
|---------|--------|----------|-----------|
| Hyperion | 🔄 Testnet | Native support, optimized | Primary development |
| Andromeda | 🔄 Testnet | Cross-chain bridging | Asset migration |
| Ethereum | 🔄 Testnet | Bridge integration | Cross-chain DeFi |
| Polygon | 🔄 Testnet | Layer 2 scaling | High-throughput dApps |
| Arbitrum | 🔄 Testnet | Optimistic rollups | Advanced DeFi protocols |

## 🔒 Security Features

- **Multi-Tool Auditing**: Slither, Mythril, and custom pattern analysis
- **Vulnerability Detection**: Automated detection of common security issues
- **Gas Optimization**: Built-in gas estimation and optimization
- **Access Control**: Secure private key management
- **Audit Logging**: Comprehensive transaction and access logging

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=services

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/contracts/    # Smart contract tests
```

## 📚 Documentation

- [Getting Started Guide](docs/getting-started.md)
- [API Reference](docs/api-reference.md)
- [Security Best Practices](docs/security.md)
- [Deployment Guide](docs/deployment.md)
- [Contributing Guide](docs/contributing.md)

## 🤝 Contributing

We welcome contributions from the HyperKit community! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Start for Contributors

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes and test**
   ```bash
   pytest
   ```
4. **Submit a Pull Request**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 [Documentation](https://hyperkit.readthedocs.io/)
- 🐛 [Issue Tracker](https://github.com/hyperionkit/hyperkit-agent/issues)
- 💬 [Discord Community](https://discord.gg/hyperionkit)
- 📧 [Email Support](mailto:support@hyperionkit.xyz)
- 🐦 [Twitter](https://twitter.com/hyperionkit)

## 🗺️ Roadmap

### Phase 1: Core Agent (Completed)
- [x] AI-powered contract generation
- [x] Multi-tool auditing system
- [x] Multi-chain deployment
- [x] RAG knowledge system

### Phase 2: Advanced Features (In Progress)
- [ ] Web interface and dashboard
- [ ] Community agent marketplace
- [ ] Advanced debugging tools
- [ ] Performance optimization

### Phase 3: Ecosystem Integration (Planned)
- [ ] Hyperion mainnet integration
- [ ] Andromeda bridge support
- [ ] DeFi protocol templates
- [ ] Governance system

## 🙏 Acknowledgments

- Thanks to all contributors who help make HyperKit Agent better
- Special thanks to the Hyperion and Andromeda communities
- Web3 and DeFi developers for inspiration and feedback
- AI and open-source communities for their continuous support

---

**Made with ❤️ by the HyperKit Team**

[Website](https://hyperionkit.xyz) • [Documentation](https://hyperkit.readthedocs.io/) • [Discord](https://discord.gg/hyperionkit) • [Twitter](https://twitter.com/hyperionkit)
