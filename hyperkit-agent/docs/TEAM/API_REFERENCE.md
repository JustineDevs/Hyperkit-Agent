<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: 1.5.0  
**Last Verified**: 2025-10-28  
**Commit**: `d5465090`  
**Branch**: `main`  
<!-- AUDIT_BADGE_END -->

# 🔌 **HyperKit AI Agent - API Reference**

**Version**: 1.5.0  
**Base URL**: `https://api.hyperionkit.xyz`  
**Authentication**: Bearer Token  
**Last Updated**: October 23, 2025  

---

## 📋 **OVERVIEW**

The HyperKit AI Agent API provides endpoints for smart contract generation, compilation, deployment, and management. All endpoints return JSON responses and support real-time updates via WebSocket.

---

## 🔐 **AUTHENTICATION**

### **API Key Authentication**
```http
Authorization: Bearer YOUR_API_KEY
```

### **Get API Key**
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## 📝 **CONTRACT GENERATION**

### **Generate Smart Contract**
```http
POST /api/v1/contracts/generate
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "contract_type": "ERC20",
  "name": "MyToken",
  "symbol": "MTK",
  "decimals": 18,
  "initial_supply": "1000000",
  "features": ["mintable", "burnable", "pausable"],
  "network": "ethereum"
}
```

**Response:**
```json
{
  "contract_id": "uuid-here",
  "status": "generated",
  "source_code": "pragma solidity ^0.8.19;\n\ncontract MyToken {\n...",
  "created_at": "2025-10-23T10:00:00Z"
}
```

### **Available Contract Types**
- `ERC20` - Fungible tokens
- `ERC721` - Non-fungible tokens
- `ERC1155` - Multi-token standard
- `Governance` - DAO governance
- `Staking` - Staking contracts
- `Vesting` - Token vesting
- `Auction` - Auction contracts
- `Custom` - Custom Solidity

---

## ⚙️ **CONTRACT COMPILATION**

### **Compile Contract**
```http
POST /api/v1/contracts/compile
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "contract_id": "uuid-here",
  "source_code": "pragma solidity ^0.8.19;\n...",
  "compiler_version": "0.8.19",
  "optimization": true
}
```

**Response:**
```json
{
  "compilation_id": "uuid-here",
  "status": "compiling",
  "job_id": "celery-job-id",
  "estimated_time": 30
}
```

### **Get Compilation Status**
```http
GET /api/v1/contracts/compile/{compilation_id}
Authorization: Bearer YOUR_API_KEY
```

**Response:**
```json
{
  "compilation_id": "uuid-here",
  "status": "completed",
  "bytecode": "0x608060405234801561001057600080fd5b50...",
  "abi": [
    {
      "inputs": [],
      "name": "constructor",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "constructor"
    }
  ],
  "gas_estimate": 150000,
  "created_at": "2025-10-23T10:05:00Z"
}
```

---

## 🚀 **CONTRACT DEPLOYMENT**

### **Deploy Contract**
```http
POST /api/v1/contracts/deploy
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "compilation_id": "uuid-here",
  "network": "ethereum",
  "constructor_args": {
    "name": "MyToken",
    "symbol": "MTK",
    "decimals": 18
  },
  "gas_limit": 200000,
  "gas_price": "20000000000"
}
```

**Response:**
```json
{
  "deployment_id": "uuid-here",
  "status": "deploying",
  "job_id": "celery-job-id",
  "estimated_time": 60
}
```

### **Get Deployment Status**
```http
GET /api/v1/deployments/{deployment_id}
Authorization: Bearer YOUR_API_KEY
```

**Response:**
```json
{
  "deployment_id": "uuid-here",
  "status": "deployed",
  "contract_address": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
  "transaction_hash": "0x1234567890abcdef...",
  "gas_used": 185000,
  "block_number": 18500000,
  "network": "ethereum",
  "created_at": "2025-10-23T10:10:00Z"
}
```

---

## 🔍 **REAL-TIME UPDATES**

### **WebSocket Connection**
```javascript
const ws = new WebSocket('wss://api.hyperkit.ai/ws/deployments/{deployment_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Status update:', data);
};
```

### **WebSocket Message Format**
```json
{
  "type": "status_update",
  "deployment_id": "uuid-here",
  "status": "compiling",
  "progress": 45,
  "message": "Compiling contract...",
  "timestamp": "2025-10-23T10:05:30Z"
}
```

### **Message Types**
- `status_update` - Status change
- `progress_update` - Progress percentage
- `error` - Error occurred
- `completed` - Task completed
- `log` - Log message

---

## 📊 **DEPLOYMENT MANAGEMENT**

### **List User Deployments**
```http
GET /api/v1/deployments
Authorization: Bearer YOUR_API_KEY
Query Parameters:
  - limit: 20 (default)
  - offset: 0 (default)
  - status: pending|deploying|deployed|failed
  - network: ethereum|polygon|bsc
```

**Response:**
```json
{
  "deployments": [
    {
      "deployment_id": "uuid-here",
      "contract_name": "MyToken",
      "contract_address": "0x742d35Cc...",
      "network": "ethereum",
      "status": "deployed",
      "created_at": "2025-10-23T10:00:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

### **Get Deployment Details**
```http
GET /api/v1/deployments/{deployment_id}
Authorization: Bearer YOUR_API_KEY
```

**Response:**
```json
{
  "deployment_id": "uuid-here",
  "contract_name": "MyToken",
  "contract_address": "0x742d35Cc...",
  "network": "ethereum",
  "status": "deployed",
  "transaction_hash": "0x1234567890abcdef...",
  "gas_used": 185000,
  "block_number": 18500000,
  "source_code": "pragma solidity ^0.8.19;\n...",
  "abi": [...],
  "created_at": "2025-10-23T10:00:00Z"
}
```

---

## 🔒 **SECURITY AUDIT**

### **Request Security Audit**
```http
POST /api/v1/contracts/audit
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "deployment_id": "uuid-here",
  "audit_type": "security",
  "tools": ["slither", "mythril", "echidna"]
}
```

**Response:**
```json
{
  "audit_id": "uuid-here",
  "status": "auditing",
  "job_id": "celery-job-id",
  "estimated_time": 300
}
```

### **Get Audit Results**
```http
GET /api/v1/audits/{audit_id}
Authorization: Bearer YOUR_API_KEY
```

**Response:**
```json
{
  "audit_id": "uuid-here",
  "status": "completed",
  "findings": [
    {
      "severity": "medium",
      "title": "Reentrancy vulnerability",
      "description": "Function may be vulnerable to reentrancy attacks",
      "recommendation": "Use checks-effects-interactions pattern"
    }
  ],
  "score": 85,
  "created_at": "2025-10-23T10:15:00Z"
}
```

---

## 🏥 **HEALTH & MONITORING**

### **Health Check**
```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-23T10:00:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "celery": "healthy",
    "ai_models": "healthy"
  },
  "version": "1.0.0"
}
```

### **System Metrics**
```http
GET /api/v1/metrics
Authorization: Bearer YOUR_API_KEY
```

**Response:**
```json
{
  "deployments_total": 1250,
  "active_jobs": 5,
  "average_compilation_time": 25.5,
  "average_deployment_time": 45.2,
  "success_rate": 98.5
}
```

---

## ⚠️ **ERROR HANDLING**

### **Error Response Format**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid contract type provided",
    "details": {
      "field": "contract_type",
      "value": "INVALID_TYPE",
      "allowed_values": ["ERC20", "ERC721", "ERC1155", "Governance"]
    },
    "timestamp": "2025-10-23T10:00:00Z",
    "request_id": "uuid-here"
  }
}
```

### **Common Error Codes**
- `VALIDATION_ERROR` - Invalid request data
- `AUTHENTICATION_ERROR` - Invalid API key
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `COMPILATION_ERROR` - Contract compilation failed
- `DEPLOYMENT_ERROR` - Contract deployment failed
- `NETWORK_ERROR` - Blockchain network issue
- `INTERNAL_ERROR` - Server error

---

## 📈 **RATE LIMITS**

### **Free Tier**
- 5 deployments per month
- 10 API calls per minute
- 1 concurrent job

### **Pro Tier**
- 100 deployments per month
- 100 API calls per minute
- 5 concurrent jobs

### **Enterprise Tier**
- Unlimited deployments
- 1000 API calls per minute
- 20 concurrent jobs

---

## 🔗 **SDK & INTEGRATION**

### **JavaScript SDK**
```javascript
import { HyperKitAPI } from '@hyperkit/sdk';

const api = new HyperKitAPI({
  apiKey: 'your-api-key',
  baseURL: 'https://api.hyperkit.ai'
});

// Generate contract
const contract = await api.contracts.generate({
  contract_type: 'ERC20',
  name: 'MyToken',
  symbol: 'MTK'
});

// Deploy contract
const deployment = await api.contracts.deploy({
  compilation_id: contract.id,
  network: 'ethereum'
});
```

### **Python SDK**
```python
from hyperkit import HyperKitAPI

api = HyperKitAPI(api_key='your-api-key')

# Generate contract
contract = api.contracts.generate(
    contract_type='ERC20',
    name='MyToken',
    symbol='MTK'
)

# Deploy contract
deployment = api.contracts.deploy(
    compilation_id=contract.id,
    network='ethereum'
)
```

---

## 📞 **SUPPORT**

- **Documentation**: https://docs.hyperionkit.xyz
- **Status Page**: https://status.hyperionkit.xyz
- **Support Email**: support@hyperionkit.xyz
- **Discord**: https://discord.gg/hyperkit

---

*API Reference v1.0.0 - Last Updated: October 23, 2025*
