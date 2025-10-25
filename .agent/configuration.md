# Configuration

## HyperAgent Configuration

HyperAgent can be configured using environment variables for optimal smart contract development and deployment.

### Core Configuration

- `ENV`: Environment (local, staging, production)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `DEBUG`: Enable debug mode for development

### AI Model Configuration

#### Primary AI Models
- `OPENAI_API_KEY`: OpenAI API key for GPT models (Required for contract generation)
- `ANTHROPIC_API_KEY`: Claude API key for advanced reasoning (Required for security auditing)
- `GOOGLE_API_KEY`: Google Gemini API key for multimodal analysis (Optional)

#### Specialized Models
- `DEEPSEEK_API_KEY`: DeepSeek API key for cost-effective batch processing (Optional)
- `LAZAI_API_KEY`: LazAI network API key for AI-powered contract analysis (Optional)

### Blockchain Network Configuration

#### Primary Networks (HyperAgent Focus)
- `HYPERION_RPC_URL`: Hyperion testnet RPC endpoint (Default: https://hyperion-testnet.metisdevops.link)
- `METIS_RPC_URL`: Metis mainnet RPC endpoint (Production deployment)

#### Supported Networks
- `ETHEREUM_RPC_URL`: Ethereum mainnet RPC endpoint
- `POLYGON_RPC_URL`: Polygon mainnet RPC endpoint
- `ARBITRUM_RPC_URL`: Arbitrum mainnet RPC endpoint

### HyperAgent Specific Configuration

#### LazAI Network Integration
- `LAZAI_EVM_ADDRESS`: EVM address for LazAI network integration
- `LAZAI_RSA_PRIVATE_KEY`: RSA private key for LazAI authentication
- `IPFS_JWT`: Pinata IPFS JWT token for decentralized storage

#### Security & Monitoring
- `SECURITY_SCAN_ENABLED`: Enable automatic security scanning (default: true)
- `AUDIT_LEVEL`: Audit depth (basic, standard, comprehensive)
- `GAS_OPTIMIZATION`: Enable gas optimization suggestions (default: true)

#### Development Settings
- `AUTO_VERIFICATION`: Enable automatic contract verification (default: true)
- `TEST_MODE`: Enable test mode for development (default: false)
- `CACHE_ENABLED`: Enable response caching (default: true)

### Configuration Examples

#### Development Environment
```bash
ENV=local
DEBUG=true
LOG_LEVEL=DEBUG
TEST_MODE=true
HYPERION_RPC_URL=https://hyperion-testnet.metisdevops.link
```

#### Production Environment
```bash
ENV=production
LOG_LEVEL=INFO
SECURITY_SCAN_ENABLED=true
AUDIT_LEVEL=comprehensive
AUTO_VERIFICATION=true
```

### Configuration Validation

HyperAgent validates all configuration on startup:
- **Required Keys**: OPENAI_API_KEY, ANTHROPIC_API_KEY
- **Network Connectivity**: Tests RPC endpoint connectivity
- **AI Model Access**: Validates API key permissions
- **Security Settings**: Ensures security features are properly configured

See [env.example](../hyperkit-agent/env.example) for complete configuration options.