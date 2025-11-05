<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: 1.4.7  
**Last Verified**: 2025-11-05  
**Commit**: `4f52980`  
**Branch**: `main`  
<!-- AUDIT_BADGE_END -->

# Pinata IPFS Setup Guide for HyperKit Agent

## 🚀 **Quick Setup (5 Minutes)**

### **Step 1: Create Pinata Account**
1. Go to [Pinata.cloud](https://pinata.cloud)
2. Sign up for a free account
3. Verify your email address

### **Step 2: Get API Keys**
1. Log into your Pinata dashboard
2. Go to **API Keys** section
3. Click **"New Key"**
4. Name it: `HyperKit Agent`
5. Select permissions: **Pin File to IPFS**, **Pin JSON to IPFS**
6. Copy your **API Key** and **API Secret**

### **Step 3: Configure HyperKit Agent**
1. Open `config.yaml`
2. Update the Pinata section:

```yaml
# Pinata IPFS Integration
pinata:
  api_key: "your_pinata_api_key_here"
  api_secret: "your_pinata_api_secret_here"
  gateway_url: "https://gateway.pinata.cloud/ipfs/"
  enabled: true  # Set to true when API keys are configured
```

### **Step 4: Test Pinata Integration**
```bash
# Test IPFS upload
python -c "
from services.storage.ipfs_client import IPFSClient
import asyncio

async def test():
    config = {'pinata': {'api_key': 'your_key', 'api_secret': 'your_secret'}}
    client = IPFSClient(config)
    cid = await client.upload_json({'test': 'data'}, 'test.json')
    print(f'✅ Uploaded to IPFS: {cid}')

asyncio.run(test())
"
```

---

## 📊 **Pinata Features for HyperKit Agent**

### **✅ What You Get with Pinata**

| Feature | Free Tier | Pro Tier |
|---------|-----------|----------|
| **Storage** | 1 GB | 100 GB+ |
| **Bandwidth** | 1 GB/month | Unlimited |
| **Gateway Speed** | Standard | Fast |
| **API Rate Limits** | 180 requests/hour | 1000+ requests/hour |
| **Custom Domains** | ❌ | ✅ |
| **Advanced Analytics** | ❌ | ✅ |

### **🎯 Perfect for HyperKit Agent**
- **Audit Reports**: Store large JSON audit reports
- **AI Models**: Distribute vulnerability detection models
- **Datasets**: Share training data with community
- **Simulations**: Store transaction simulation traces
- **Threat Intelligence**: Community-contributed security data

---

## 🔧 **Advanced Configuration**

### **Environment Variables (Recommended)**
```bash
# .env file
PINATA_API_KEY=your_pinata_api_key
PINATA_API_SECRET=your_pinata_api_secret
```

### **Update config.yaml**
```yaml
pinata:
  api_key: "${PINATA_API_KEY}"
  api_secret: "${PINATA_API_SECRET}"
  gateway_url: "https://gateway.pinata.cloud/ipfs/"
  enabled: true
```

### **Custom Gateway (Pro Feature)**
```yaml
pinata:
  api_key: "your_key"
  api_secret: "your_secret"
  gateway_url: "https://your-custom-domain.com/ipfs/"
  enabled: true
```

---

## 🚀 **Usage Examples**

### **1. Store Audit Report**
```python
from services.storage.ipfs_client import IPFSClient

# Initialize with Pinata
config = {
    'pinata': {
        'api_key': 'your_key',
        'api_secret': 'your_secret'
    }
}
client = IPFSClient(config)

# Store audit report
audit_data = {
    'contract_address': '0xABC...',
    'risk_score': 75,
    'findings': [...]
}

cid = await client.upload_json(audit_data, 'audit_report.json')
print(f"📦 Stored on IPFS: {cid}")
print(f"🌐 View: https://gateway.pinata.cloud/ipfs/{cid}")
```

### **2. Store AI Model**
```python
# Store trained model
with open('vulnerability_model.pkl', 'rb') as f:
    model_data = f.read()

cid = await client.upload_file(model_data, 'vulnerability_model.pkl')
print(f"🤖 AI Model stored: {cid}")
```

### **3. Retrieve from IPFS**
```python
# Get audit report
audit_report = await client.get_json(cid)
print(f"📄 Retrieved audit: {audit_report['contract_address']}")
```

---

## 📈 **Performance Benefits**

### **Pinata vs Public Gateways**

| Metric | Public Gateways | Pinata Gateway |
|--------|----------------|----------------|
| **Speed** | Variable | Fast & Reliable |
| **Uptime** | 95% | 99.9% |
| **Rate Limits** | Strict | Generous |
| **Support** | None | Professional |
| **Analytics** | None | Detailed |

### **HyperKit Agent Benefits**
- **Faster Uploads**: 3-5x faster than public gateways
- **Reliable Retrieval**: 99.9% uptime for audit reports
- **Better Performance**: Optimized for AI/blockchain workloads
- **Professional Support**: Direct support for enterprise use

---

## 🔒 **Security Best Practices**

### **API Key Security**
```bash
# Never commit API keys to git
echo "PINATA_API_KEY=your_key" >> .env
echo ".env" >> .gitignore
```

### **Access Control**
- Use **read-only** keys for production
- Rotate keys monthly
- Monitor usage in Pinata dashboard

### **Data Privacy**
- Pinata is **not encrypted by default**
- For sensitive data, encrypt before upload
- Use TEE-based private inference with Alith

---

## 🎯 **Integration with HyperKit Workflow**

### **Complete Workflow with Pinata**
```bash
# 1. Generate contract
hyperagent workflow "Create secure ERC20 token" --network hyperion

# 2. Audit with AI
hyperagent audit 0xABC... --network hyperion

# 3. Store on Pinata IPFS (automatic)
# Audit report → Pinata → CID returned

# 4. Verify on-chain
hyperagent verify 0xABC... --network hyperion

# 5. RAG retrieval
# Similar audits retrieved from Pinata gateway
```

### **Expected Results**
```
✅ Contract generated and deployed
✅ Audit completed with AI analysis
📦 Audit report stored on Pinata IPFS
🌐 IPFS URL: https://gateway.pinata.cloud/ipfs/Qm...
🔍 RAG system found 3 similar audits
✅ Contract verified on Hyperion explorer
```

---

## 🆘 **Troubleshooting**

### **Common Issues**

#### **"Pinata API key not configured"**
```bash
# Check your config.yaml
grep -A 5 "pinata:" config.yaml

# Should show:
# pinata:
#   api_key: "your_key"
#   api_secret: "your_secret"
#   enabled: true
```

#### **"Upload failed: 401 Unauthorized"**
- Check API key and secret are correct
- Ensure API key has proper permissions
- Verify account is not suspended

#### **"Gateway timeout"**
- Try different gateway: `https://ipfs.io/ipfs/`
- Check Pinata status page
- Contact Pinata support

### **Test Commands**
```bash
# Test Pinata connection
python -c "
import requests
response = requests.get('https://api.pinata.cloud/data/testAuthentication', 
    headers={'pinata_api_key': 'your_key'})
print(f'Status: {response.status_code}')
"
```

---

## 🎉 **Ready to Use!**

Once configured, your HyperKit Agent will:
- ✅ **Store audit reports** on Pinata IPFS
- ✅ **Retrieve similar audits** via RAG system
- ✅ **Distribute AI models** to community
- ✅ **Share threat intelligence** across agents
- ✅ **Provide fast, reliable** IPFS access

**Your decentralized AI agent infrastructure is now complete!** 🚀

---

---

## 🔗 **Connect With Us**

- 🌐 **Website**: [Hyperionkit.xyz](http://hyperionkit.xyz/)
- 📚 **Documentation**: [GitHub Docs](https://github.com/Hyperionkit/Hyperkit-Agent)
- 💬 **Discord**: [Join Community](https://discord.com/invite/MDh7jY8vWe)
- 🐦 **Twitter**: [@HyperKit](https://x.com/HyperionKit)
- 📧 **Contact**: [Hyperkitdev@gmail.com](mailto:Hyperkitdev@gmail.com) (for security issues)
- 💰 **Bug Bounty**: See [SECURITY.md](../../../SECURITY.md)

**Last Updated**: 2025-01-29  
**Version**: 1.5.14  
*Pinata Setup Guide for HyperKit Agent*
