<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: 1.4.6  
**Last Verified**: 2025-10-28  
**Commit**: `d5465090`  
**Branch**: `main`  
<!-- AUDIT_BADGE_END -->

# HyperAgent Integrator Guide

**Purpose**: Guide for developers integrating HyperAgent into their projects  
**Last Updated**: 2025-10-26  
**Status**: Active

---

## 📋 Table of Contents

- [Overview](#overview)
- [Integration Methods](#integration-methods)
- [Python Library Integration](#python-library-integration)
- [CLI Integration](#cli-integration)
- [MCP Server Integration](#mcp-server-integration)
- [API Reference](#api-reference)
- [Best Practices](#best-practices)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

HyperAgent can be integrated into your project in three ways:

1. **Python Library**: Import as a package in your Python code
2. **CLI Tool**: Execute commands from shell scripts or CI/CD
3. **MCP Server**: Connect as Model Context Protocol server

---

## 📦 Integration Methods

### Method 1: Python Library

**Use Case**: Embed smart contract operations in your Python application

**Installation**:
```bash
pip install -e git+https://github.com/JustineDevs/Hyperkit-Agent.git#egg=hyperkit-agent&subdirectory=hyperkit-agent
```

**Basic Usage**:
```python
from core.agent.main import HyperKitAgent
from core.config.loader import get_config

# Initialize agent
config = get_config().to_dict()
agent = HyperKitAgent(config)

# Generate contract
result = await agent.generate_contract({
    "requirements": "ERC20 token with 1M supply",
    "network": "hyperion"
})

# Audit contract
audit_result = await agent.audit_contract(contract_code)

# Deploy contract
deploy_result = await agent.deploy_contract(
    contract_code=result['contract_code'],
    network="hyperion"
)
```

---

### Method 2: CLI Tool

**Use Case**: Automate deployments in CI/CD pipelines

**Installation**:
```bash
cd hyperkit-agent
pip install -e .
```

**Basic Usage**:
```bash
# In your CI/CD script
hyperagent generate contract "ERC20 token" --output token.sol
hyperagent audit contract token.sol --format json > audit.json
hyperagent deploy --contract token.sol --network hyperion
```

---

### Method 3: MCP Server

**Use Case**: Connect to AI assistants (Claude, ChatGPT)

**Setup**:
```json
{
  "mcpServers": {
    "hyperagent": {
      "command": "python",
      "args": ["-m", "hyperkit-agent.mcp_server"],
      "env": {
        "HYPERION_RPC_URL": "https://hyperion-testnet.metisdevops.link"
      }
    }
  }
}
```

---

## 🔧 Python Library Integration

### Core Components

#### 1. HyperKitAgent

Main agent class for smart contract operations.

```python
from core.agent.main import HyperKitAgent

agent = HyperKitAgent(config_dict)

# Available methods:
# - generate_contract(requirements: Dict) -> Dict
# - audit_contract(code: str) -> Dict
# - deploy_contract(code: str, network: str) -> Dict
# - verify_contract(address: str, network: str) -> Dict
```

#### 2. FoundryDeployer

Direct deployment without agent wrapper.

```python
from services.deployment.foundry_deployer import FoundryDeployer

deployer = FoundryDeployer()

result = deployer.deploy_contract(
    contract_source="contract MyToken is ERC20 {...}",
    contract_name="MyToken",
    constructor_args=["MyToken", "MTK", 1000000],
    network="hyperion"
)
```

#### 3. AuditService

Multi-source smart contract auditing.

```python
from services.audit.multi_source_auditor import MultiSourceAuditor

auditor = MultiSourceAuditor()

result = await auditor.audit_contract(
    contract_code="...",
    methods=["slither", "mythril", "ai"]
)
```

---

### Full Integration Example

```python
import asyncio
from pathlib import Path
from core.agent.main import HyperKitAgent
from core.config.loader import get_config

async def deploy_my_token():
    """Complete workflow: generate, audit, deploy, verify"""
    
    # 1. Initialize
    config = get_config().to_dict()
    agent = HyperKitAgent(config)
    
    # 2. Generate contract
    print("Generating contract...")
    gen_result = await agent.generate_contract({
        "requirements": "ERC20 token named MyToken with 1M supply",
        "network": "hyperion"
    })
    
    if not gen_result.get('success'):
        print(f"Generation failed: {gen_result.get('error')}")
        return
    
    contract_code = gen_result['contract_code']
    
    # 3. Audit contract
    print("Auditing contract...")
    audit_result = await agent.audit_contract(contract_code)
    
    if audit_result.get('severity') == 'critical':
        print("Critical vulnerabilities found!")
        print(audit_result)
        return
    
    # 4. Deploy contract
    print("Deploying to Hyperion testnet...")
    deploy_result = await agent.deploy_contract(
        contract_code=contract_code,
        network="hyperion"
    )
    
    if not deploy_result.get('success'):
        print(f"Deployment failed: {deploy_result.get('error')}")
        return
    
    contract_address = deploy_result['address']
    print(f"Contract deployed at: {contract_address}")
    
    # 5. Verify contract
    print("Verifying contract on explorer...")
    verify_result = await agent.verify_contract(
        address=contract_address,
        network="hyperion"
    )
    
    if verify_result.get('success'):
        print(f"Verification successful: {verify_result['explorer_url']}")
    
    return {
        'address': contract_address,
        'audit': audit_result,
        'verification': verify_result
    }

if __name__ == '__main__':
    result = asyncio.run(deploy_my_token())
    print(f"Final result: {result}")
```

---

## 🖥️ CLI Integration

### CI/CD Pipeline Example

**GitHub Actions**:
```yaml
name: Deploy Smart Contracts

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Foundry
        uses: foundry-rs/foundry-toolchain@v1
      
      - name: Install HyperAgent
        run: |
          cd hyperkit-agent
          pip install -e .
      
      - name: Generate Contract
        run: |
          hyperagent generate contract "ERC20 token" --output contracts/Token.sol
      
      - name: Audit Contract
        run: |
          hyperagent audit contract contracts/Token.sol --format json > audit.json
          # Fail if critical issues found
          if grep -q '"severity": "critical"' audit.json; then
            echo "Critical vulnerabilities found!"
            exit 1
          fi
      
      - name: Deploy to Testnet
        env:
          HYPERION_RPC_URL: ${{ secrets.HYPERION_RPC_URL }}
          PRIVATE_KEY: ${{ secrets.PRIVATE_KEY }}
        run: |
          hyperagent deploy \
            --contract contracts/Token.sol \
            --network hyperion \
            --output deployment.json
      
      - name: Verify Contract
        run: |
          ADDRESS=$(jq -r '.address' deployment.json)
          hyperagent verify contract $ADDRESS --network hyperion
```

---

### Shell Script Example

```bash
#!/bin/bash
# deploy-contract.sh - Automated contract deployment

set -e

CONTRACT_NAME="MyToken"
NETWORK="hyperion"

echo "🚀 Starting deployment workflow..."

# 1. Generate contract
echo "📝 Generating contract..."
hyperagent generate contract \
  "ERC20 token named $CONTRACT_NAME with 1M supply" \
  --output "$CONTRACT_NAME.sol"

# 2. Audit contract
echo "🔍 Auditing contract..."
hyperagent audit contract "$CONTRACT_NAME.sol" \
  --format json \
  --output "audit-$CONTRACT_NAME.json"

# Check for critical issues
CRITICAL=$(jq '.severity == "critical"' "audit-$CONTRACT_NAME.json")
if [ "$CRITICAL" = "true" ]; then
  echo "❌ Critical vulnerabilities found. Aborting."
  exit 1
fi

echo "✅ No critical issues found."

# 3. Deploy contract
echo "📦 Deploying to $NETWORK..."
hyperagent deploy \
  --contract "$CONTRACT_NAME.sol" \
  --network "$NETWORK" \
  --output "deployment-$CONTRACT_NAME.json"

# Extract address
ADDRESS=$(jq -r '.address' "deployment-$CONTRACT_NAME.json")
echo "✅ Deployed at: $ADDRESS"

# 4. Verify contract
echo "🔗 Verifying on explorer..."
hyperagent verify contract "$ADDRESS" --network "$NETWORK"

echo "🎉 Deployment complete!"
echo "Contract: $ADDRESS"
echo "Network: $NETWORK"
echo "Audit: audit-$CONTRACT_NAME.json"
echo "Deployment: deployment-$CONTRACT_NAME.json"
```

---

## 🔌 MCP Server Integration

### Configuration

Add to your MCP client config (e.g., `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "hyperagent": {
      "command": "python",
      "args": ["-m", "hyperkit-agent.mcp_server"],
      "env": {
        "HYPERION_RPC_URL": "https://hyperion-testnet.metisdevops.link",
        "GOOGLE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Available Tools

1. **generate_contract**: Generate smart contracts from description
2. **audit_contract**: Audit contracts for vulnerabilities
3. **deploy_contract**: Deploy to specified network
4. **verify_contract**: Verify on block explorer

### Example Usage in Claude

```
User: Create and deploy an ERC20 token to Hyperion testnet

Claude: I'll help you deploy an ERC20 token using HyperAgent.
[Uses generate_contract tool]
[Uses audit_contract tool]
[Uses deploy_contract tool]
[Uses verify_contract tool]

Contract deployed at: 0x...
```

---

## 📚 API Reference

### Core Classes

#### HyperKitAgent

```python
class HyperKitAgent:
    def __init__(self, config: Dict[str, Any])
    
    async def generate_contract(self, requirements: Dict) -> Dict:
        """
        Generate smart contract from requirements
        
        Args:
            requirements: Dict with 'requirements' and 'network' keys
        
        Returns:
            Dict with 'success', 'contract_code', and metadata
        """
    
    async def audit_contract(self, contract_code: str) -> Dict:
        """
        Audit smart contract for vulnerabilities
        
        Args:
            contract_code: Solidity source code
        
        Returns:
            Dict with 'status', 'severity', and 'results'
        """
    
    async def deploy_contract(
        self,
        contract_code: str,
        network: str,
        constructor_args: List = None
    ) -> Dict:
        """
        Deploy contract to specified network
        
        Args:
            contract_code: Solidity source code
            network: Network name ('hyperion', 'lazai', 'metis')
            constructor_args: Optional constructor arguments
        
        Returns:
            Dict with 'success', 'address', 'tx_hash'
        """
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Required for deployment
export PRIVATE_KEY="your-private-key"
export HYPERION_RPC_URL="https://hyperion-testnet.metisdevops.link"

# Optional: AI providers
export GOOGLE_API_KEY="your-google-api-key"
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Optional: Explorer API keys
export HYPERION_EXPLORER_API_KEY="your-explorer-api-key"
export METIS_EXPLORER_API_KEY="your-metis-api-key"
```

### Config File

Create `config.yaml`:

```yaml
ai_providers:
  google:
    api_key: ${GOOGLE_API_KEY}
    model: gemini-pro
  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4

networks:
  hyperion:
    chain_id: 1001
    rpc_url: ${HYPERION_RPC_URL}
    explorer_url: https://hyperion-testnet-explorer.metisdevops.link

deployment:
  gas_multiplier: 1.2
  confirmation_blocks: 2
```

---

## 🎯 Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
try:
    result = await agent.deploy_contract(code, network)
    if not result.get('success'):
        logger.error(f"Deployment failed: {result.get('error')}")
        # Implement retry logic or alerting
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    # Implement fallback or notification
```

### 2. Auditing Before Deployment

Never deploy without auditing:

```python
audit_result = await agent.audit_contract(code)

if audit_result.get('severity') in ['critical', 'high']:
    raise Exception("Security issues found - cannot deploy")

# Proceed with deployment only if audit passes
```

### 3. Network Configuration

Use environment-specific configs:

```python
# Development
network = "hyperion"  # Testnet

# Production
network = "metis"  # Mainnet (after audit)
```

### 4. Logging and Monitoring

Implement comprehensive logging:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"Deploying to {network}")
logger.info(f"Contract address: {address}")
logger.warning(f"Audit found {issue_count} issues")
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. Deployment Fails

**Error**: `Type error: Incorrect argument count`

**Solution**: Check constructor arguments match contract definition

```python
# Ensure constructor args match
constructor_args = ["TokenName", "TKN", 1000000]  # Must match contract
```

#### 2. Network Connection Fails

**Error**: `Failed to connect to RPC`

**Solution**: Verify RPC URL and network status

```bash
# Test RPC connection
curl -X POST https://hyperion-testnet.metisdevops.link \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

#### 3. Verification Fails

**Error**: `Contract verification failed`

**Solution**: Check explorer API key and wait for confirmations

```python
# Wait for more confirmations
time.sleep(60)  # Wait 1 minute
verify_result = await agent.verify_contract(address, network)
```

---

## 📞 Support

- **Documentation**: [GitHub Docs](https://github.com/JustineDevs/Hyperkit-Agent)
- **GitHub Issues**: [github.com/JustineDevs/Hyperkit-Agent/issues](https://github.com/JustineDevs/Hyperkit-Agent/issues)
- **Discord**: Coming Soon
- **Email**: support@hyperkit.dev

## 📍 Documentation Locations

- **User Docs**: `/docs/` - High-level guides and governance
- **Internal Docs**: `/hyperkit-agent/Docs/` - Team, execution, integration, reference
- **Technical Docs**: `/hyperkit-agent/docs/` - API reference, security, technical specs
- **Current Status**: `/hyperkit-agent/REPORTS/HONEST_STATUS_ASSESSMENT.md`
- **Historical Archive**: `/ACCOMPLISHED/` - Timestamped milestones

---

## 📝 Changelog

### v4.3.0 (2025-10-27)
- **Directory restructure completed**: Organized all documentation
- **IPFS RAG production-ready**: Real Pinata integration working
- **Status transparency**: Honest assessment of capabilities
- **Critical fixes identified**: P0-P3 priority system

### v4.1.11 (2025-10-26)
- Added comprehensive integration documentation
- Python library examples
- CLI integration guides
- MCP server setup instructions

---

**Last Updated**: October 27, 2025  
**Version**: 1.4.6  
**Maintained By**: HyperKit Development Team  
**Location**: `/hyperkit-agent/docs/INTEGRATOR_GUIDE.md`

