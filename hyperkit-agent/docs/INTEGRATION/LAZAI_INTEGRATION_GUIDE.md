<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: 1.4.6  
**Last Verified**: 2025-10-28  
**Commit**: `d5465090`  
**Branch**: `main`  
<!-- AUDIT_BADGE_END -->

# 🚀 LazAI/Alith SDK Integration Guide

## EVM Address: `0xa43b752b6e941263eb5a7e3b96e2e0dea1a586ff`

This guide provides step-by-step instructions for integrating the LazAI/Alith SDK with the HyperKit AI Agent.

## 📋 Prerequisites

1. **Python 3.8+** (recommended 3.10+)
2. **MetaMask wallet** with the specified EVM address
3. **Testnet tokens** for the EVM address
4. **Pinata IPFS account** for decentralized storage

## 🔧 Installation Steps

### 1. Install LazAI SDK
```bash
pip install lazai alith
```

### 2. Configure Environment Variables
Add to your `.env` file:
```env
# LazAI Configuration
LAZAI_EVM_ADDRESS=0xa43b752b6e941263eb5a7e3b96e2e0dea1a586ff
LAZAI_RSA_PRIVATE_KEY=your_rsa_private_key_from_admin
IPFS_JWT=your_pinata_jwt_token

# Existing configuration
PRIVATE_KEY=your_ethereum_private_key_here
PINATA_API_KEY=your_pinata_api_key
PINATA_API_SECRET=your_pinata_secret_key
```

### 3. Get Testnet Tokens
- Visit LazAI testnet faucet
- Fund your address: `0xa43b752b6e941263eb5a7e3b96e2e0dea1a586ff`
- Ensure you have enough tokens for registration and inference

### 4. Register with LazAI Admins
- Join LazAI Discord/community
- Request registration for your EVM address
- Provide your development server details
- Receive RSA private key from admins

### 5. Set up Pinata IPFS
- Create account at https://pinata.cloud/
- Generate JWT token in API Keys section
- Add JWT token to your `.env` file

## 🧪 Testing the Integration

Run the integration test:
```bash
python test_lazai_integration.py
```

## 🔄 Complete Workflow

### 1. User Registration
```python
from services.core.ai_agent import HyperKitAIAgent

ai_agent = HyperKitAIAgent()

# Register user on LazAI network
result = await ai_agent.register_lazai_user(amount=10000000)
```

### 2. Contract Generation
```python
requirements = {
    "name": "MyToken",
    "type": "ERC20",
    "features": ["mintable", "burnable"],
    "security": "high"
}

contract = await ai_agent.generate_contract(requirements)
```

### 3. Contract Auditing
```python
audit_result = await ai_agent.audit_contract(contract_code)
```

### 4. Data Token Minting
```python
mint_result = await ai_agent.mint_lazai_data_token(
    "data_file.json",
    {"type": "contract_data", "description": "Smart contract data"}
)
```

### 5. Private Inference
```python
inference_result = await ai_agent.run_lazai_inference(
    file_id="your_file_id",
    prompt="Analyze this smart contract for security issues",
    model="gpt-4o-mini"
)
```

## 🛠️ Troubleshooting

### Common Issues:
1. **LazAI SDK not available**: Install with `pip install lazai alith`
2. **User not registered**: Call `register_lazai_user()` first
3. **Insufficient funds**: Deposit more tokens for inference
4. **IPFS not configured**: Set up Pinata JWT token

### Debug Commands:
```python
# Check integration status
status = ai_agent.get_lazai_status()
print(status)

# Get user information
user_info = await ai_agent.get_lazai_user_info()
print(user_info)
```

## 📊 Integration Status

The integration provides:
- ✅ Real LazAI network connectivity
- ✅ Private inference capabilities
- ✅ Data token minting
- ✅ User registration and management
- ✅ Fund deposit and management
- ✅ Contract generation with LazAI
- ✅ Contract auditing with LazAI
- ✅ IPFS storage integration

## 🚀 Production Deployment

For production use:
1. Ensure all environment variables are set
2. Complete user registration on LazAI network
3. Deposit sufficient funds for inference operations
4. Test all functionality with real data
5. Monitor integration status regularly

## 📞 Support

- **LazAI Discord**: Join for community support
- **Builder Guild**: Technical assistance
- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: https://docs.lazai.network/

---

**Ready to use LazAI integration with EVM address: `0xa43b752b6e941263eb5a7e3b96e2e0dea1a586ff`**
