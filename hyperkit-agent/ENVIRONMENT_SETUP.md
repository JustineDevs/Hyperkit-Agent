# Environment Setup Guide

## Required API Keys

To use the HyperKit AI Agent, you'll need to configure the following API keys in your `.env` file:

### 1. AI Provider API Keys (Google Gemini Only)

```bash
# Google Gemini (Only Provider - Free $300 credits)
GOOGLE_API_KEY=your_google_api_key_here
```

### 2. Disabled Providers (Not Used)

```bash
# These providers are not used in this version
# OPENAI_API_KEY=your_openai_api_key_here
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# DASHSCOPE_API_KEY=your_dashscope_api_key_here
# DEEPSEEK_API_KEY=your_deepseek_api_key_here
# XAI_API_KEY=your_xai_api_key_here
# GPT_OSS_API_KEY=your_gpt_oss_api_key_here
```

### 2. Blockchain Network RPC URLs

```bash
# Hyperion Testnet (Primary)
HYPERION_RPC_URL=https://hyperion-testnet.metisdevops.link

# Polygon Mainnet
POLYGON_RPC_URL=https://polygon-rpc.com

# Arbitrum One
ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc

# Ethereum Mainnet (requires Infura/Alchemy)
ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID
```

### 3. Wallet Configuration

```bash
# Your wallet private key (for deployment)
WALLET_PRIVATE_KEY=your_wallet_private_key_here
```

## Getting API Keys

### Google Gemini API Key (Required)
1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Sign up or log in with your Google account
3. Click "Get API Key" in the left sidebar
4. Create a new API key
5. Copy and paste into `.env` file
6. **Free $300 credits included!**

### No Other Providers Needed
The HyperKit Agent uses **only Google Gemini** for all AI-powered contract generation. No other API keys or local setups are required.

## Obsidian Integration Setup

### 1. Install Obsidian
1. Download [Obsidian](https://obsidian.md/) for your platform
2. Install and create a new vault
3. Set the vault path in your `.env` file: `OBSIDIAN_VAULT_PATH=/path/to/your/vault`

### 2. Create Knowledge Base
1. Create markdown files with smart contract patterns
2. Add security best practices documentation
3. Include common contract templates
4. The RAG system will automatically index these files

## Configuration Examples

### Complete .env File Example
```bash
# AI Provider API Keys (Google Gemini Only)
GOOGLE_API_KEY=your_google_api_key_here

# Obsidian Integration
OBSIDIAN_VAULT_PATH=~/hyperkit-kb

# Blockchain Configuration
DEFAULT_NETWORK=hyperion
HYPERION_RPC_URL=https://hyperion-testnet.metisdevops.link
POLYGON_RPC_URL=https://polygon-rpc.com
ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc
ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID

# Security Tools
SLITHER_ENABLED=true
MYTHRIL_ENABLED=true
EDB_ENABLED=true

# Logging
LOG_LEVEL=INFO
```

## Network RPC URLs

### Free RPC Providers
- **Polygon**: `https://polygon-rpc.com`
- **Arbitrum**: `https://arb1.arbitrum.io/rpc`
- **Ethereum**: Use Infura, Alchemy, or QuickNode

### Paid RPC Providers (Recommended for production)
- **Infura**: `https://mainnet.infura.io/v3/YOUR_PROJECT_ID`
- **Alchemy**: `https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY`
- **QuickNode**: `https://your-endpoint.quiknode.pro/YOUR_API_KEY/`

## Security Best Practices

1. **Never commit your `.env` file** to version control
2. **Use environment-specific keys** for development vs production
3. **Rotate API keys regularly**
4. **Use read-only keys** when possible
5. **Monitor API usage** to detect unauthorized access

## Testing Your Configuration

After setting up your `.env` file, test the configuration:

```bash
# Test the agent
python main.py

# Test specific services
python -m pytest tests/unit/test_core.py -v

# Test CLI interface
python cli.py --help
```

## Troubleshooting

### Common Issues

1. **API Key Not Working**
   - Verify the key is correct and active
   - Check if you have sufficient credits/quota
   - Ensure the key has the right permissions

2. **RPC Connection Failed**
   - Verify the RPC URL is correct
   - Check if the network is accessible
   - Try a different RPC provider

3. **Wallet Issues**
   - Ensure the private key is valid
   - Check if the wallet has sufficient funds
   - Verify the network matches your wallet

### Getting Help

- Check the [Issues](https://github.com/JustineDevs/Hyperkit-Agent/issues) page
- Review the [Documentation](https://github.com/JustineDevs/Hyperkit-Agent#readme)
- Contact support: [team@hyperionkit.xyz](mailto:team@hyperionkit.xyz)
