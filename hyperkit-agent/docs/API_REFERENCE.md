<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: 1.5.14  
**Last Verified**: 2025-10-28  
**Commit**: `d5465090`  
**Branch**: `main`  
<!-- AUDIT_BADGE_END -->

# HyperKit AI Agent - API Reference

**Version**: 1.5.14  
**Base URL**: `https://api.hyperkit.ai`  
**Last Updated**: October 27, 2025

## Table of Contents

1. [Authentication](#authentication)
2. [AI Agent API](#ai-agent-api)
3. [Blockchain API](#blockchain-api)
4. [Storage API](#storage-api)
5. [Security API](#security-api)
6. [Monitoring API](#monitoring-api)
7. [RAG API](#rag-api)
8. [Verification API](#verification-api)
9. [Error Handling](#error-handling)
10. [Rate Limits](#rate-limits)

---

## Authentication

All API requests require authentication using API keys passed in the request headers:

```http
Authorization: Bearer YOUR_API_KEY
X-API-Key: YOUR_API_KEY
```

### API Key Types

- **LazAI API Key**: For AI agent operations
- **Pinata API Key**: For IPFS storage operations
- **Obsidian API Key**: For RAG operations

---

## AI Agent API

### Generate Contract

Generate a smart contract from natural language requirements.

**Endpoint**: `POST /api/v1/generate`

**Request Body**:
```json
{
  "requirements": {
    "name": "MyToken",
    "type": "ERC20",
    "features": ["mintable", "burnable", "pausable"],
    "security": "high",
    "gas_optimization": true,
    "description": "A secure ERC20 token with advanced features"
  },
  "model": "alith-contract-v1",
  "options": {
    "include_tests": true,
    "include_documentation": true,
    "optimize_gas": true
  }
}
```

**Response**:
```json
{
  "status": "success",
  "contract_code": "pragma solidity ^0.8.0;\n...",
  "metadata": {
    "name": "MyToken",
    "type": "ERC20",
    "features": ["mintable", "burnable", "pausable"],
    "security_score": 95,
    "gas_optimized": true,
    "generation_time": 2.5
  },
  "files": {
    "contract": "MyToken.sol",
    "tests": "test_MyToken.js",
    "deployment": "deploy_MyToken.js"
  }
}
```

### Audit Contract

Audit a smart contract for security vulnerabilities.

**Endpoint**: `POST /api/v1/audit`

**Request Body**:
```json
{
  "contract_code": "pragma solidity ^0.8.0;\n...",
  "model": "alith-security-v1",
  "options": {
    "security_level": "high",
    "include_gas_analysis": true,
    "include_recommendations": true
  }
}
```

**Response**:
```json
{
  "status": "success",
  "audit_report": {
    "security_score": 85,
    "vulnerabilities": [
      {
        "type": "reentrancy",
        "severity": "HIGH",
        "line": 45,
        "description": "Potential reentrancy vulnerability",
        "recommendation": "Use checks-effects-interactions pattern"
      }
    ],
    "warnings": [
      "Consider adding more comprehensive error handling"
    ],
    "recommendations": [
      "Implement proper access controls",
      "Add event logging for important state changes"
    ],
    "gas_analysis": {
      "estimated_gas": 2100000,
      "optimization_opportunities": [
        "Use uint256 instead of uint8 for better gas efficiency"
      ]
    }
  }
}
```

### Get Available Models

Get information about available AI models.

**Endpoint**: `GET /api/v1/models`

**Response**:
```json
{
  "status": "success",
  "models": {
    "contract_generator": {
      "name": "alith-contract-v1",
      "type": "generation",
      "capabilities": ["solidity", "vyper", "rust"],
      "status": "active"
    },
    "security_auditor": {
      "name": "alith-security-v1",
      "type": "auditing",
      "capabilities": ["vulnerability_detection", "gas_optimization"],
      "status": "active"
    },
    "code_analyzer": {
      "name": "alith-analysis-v1",
      "type": "analysis",
      "capabilities": ["pattern_recognition", "complexity_analysis"],
      "status": "active"
    }
  },
  "total_models": 3
}
```

### Switch Model

Switch to a different AI model for a specific task.

**Endpoint**: `POST /api/v1/models/switch`

**Request Body**:
```json
{
  "task_type": "generation",
  "model_name": "alith-contract-v2"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Switched to alith-contract-v2 for generation",
  "model": {
    "name": "alith-contract-v2",
    "type": "generation",
    "status": "active"
  }
}
```

---

## Blockchain API

### Deploy Contract

Deploy a smart contract to the blockchain.

**Endpoint**: `POST /api/v1/blockchain/deploy`

**Request Body**:
```json
{
  "contract_code": "pragma solidity ^0.8.0;\n...",
  "constructor_args": ["TokenName", "TokenSymbol", 1000000],
  "network": "hyperion",
  "options": {
    "gas_limit": 3000000,
    "gas_price": 20000000000
  }
}
```

**Response**:
```json
{
  "status": "success",
  "deployment": {
    "address": "0x1234567890123456789012345678901234567890",
    "transaction_hash": "0xabcdef...",
    "gas_used": 2100000,
    "block_number": 12345,
    "network": "hyperion"
  }
}
```

### Verify Contract

Verify a deployed contract on a block explorer.

**Endpoint**: `POST /api/v1/blockchain/verify`

**Request Body**:
```json
{
  "address": "0x1234567890123456789012345678901234567890",
  "source_code": "pragma solidity ^0.8.0;\n...",
  "compiler_version": "0.8.19",
  "license_type": "MIT",
  "network": "hyperion"
}
```

**Response**:
```json
{
  "status": "success",
  "verification": {
    "verification_id": "ver_12345",
    "explorer_url": "https://explorer.hyperion.network/address/0x123...",
    "status": "verified"
  }
}
```

### Get Contract Info

Get information about a deployed contract.

**Endpoint**: `GET /api/v1/blockchain/contract/{address}`

**Response**:
```json
{
  "status": "success",
  "contract": {
    "address": "0x1234567890123456789012345678901234567890",
    "is_contract": true,
    "balance": "1.5 ETH",
    "code_length": 2048,
    "network": "hyperion"
  }
}
```

### Get Network Info

Get information about the blockchain network.

**Endpoint**: `GET /api/v1/blockchain/network`

**Response**:
```json
{
  "status": "success",
  "network": {
    "network_id": 123,
    "latest_block": 12345,
    "gas_price": 20000000000,
    "connected": true,
    "network_name": "Hyperion Testnet"
  }
}
```

---

## Storage API

### Store Audit Report

Store an audit report on IPFS.

**Endpoint**: `POST /api/v1/storage/audit-report`

**Request Body**:
```json
{
  "audit_data": {
    "contract_address": "0x123...",
    "security_score": 85,
    "vulnerabilities": [...],
    "recommendations": [...]
  },
  "metadata": {
    "contract_name": "MyToken",
    "audit_date": "2025-10-27T10:00:00Z"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "storage": {
    "cid": "QmXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXx",
    "url": "https://gateway.pinata.cloud/ipfs/QmXx...",
    "pinata_url": "https://app.pinata.cloud/pinmanager?search=QmXx...",
    "size": 2048
  }
}
```

### Retrieve Audit Report

Retrieve an audit report from IPFS.

**Endpoint**: `GET /api/v1/storage/audit-report/{cid}`

**Response**:
```json
{
  "status": "success",
  "data": {
    "contract_address": "0x123...",
    "security_score": 85,
    "vulnerabilities": [...],
    "recommendations": [...]
  },
  "cid": "QmXx...",
  "source": "ipfs"
}
```

### Store AI Model

Store an AI model on IPFS.

**Endpoint**: `POST /api/v1/storage/ai-model`

**Request Body**:
```json
{
  "model_data": {
    "name": "custom-model-v1",
    "type": "generation",
    "weights": {...},
    "config": {...}
  },
  "model_name": "custom-model-v1"
}
```

**Response**:
```json
{
  "status": "success",
  "storage": {
    "cid": "QmYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYy",
    "url": "https://gateway.pinata.cloud/ipfs/QmYy...",
    "model_name": "custom-model-v1"
  }
}
```

### List Stored Files

List all files stored on IPFS.

**Endpoint**: `GET /api/v1/storage/files`

**Response**:
```json
{
  "status": "success",
  "files": [
    {
      "cid": "QmXx...",
      "name": "audit_report_20251027.json",
      "type": "audit_report",
      "size": 2048,
      "created": "2025-10-27T10:00:00Z"
    }
  ],
  "count": 1
}
```

---

## Security API

### Audit Contract Security

Perform comprehensive security audit of a contract.

**Endpoint**: `POST /api/v1/security/audit`

**Request Body**:
```json
{
  "contract_code": "pragma solidity ^0.8.0;\n...",
  "options": {
    "include_slither": true,
    "include_mythril": false,
    "security_level": "high"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "security_audit": {
    "vulnerabilities": [
      {
        "type": "reentrancy",
        "severity": "CRITICAL",
        "line": 45,
        "code": "msg.sender.call{value: amount}(\"\");",
        "description": "Potential reentrancy vulnerability",
        "recommendation": "Use checks-effects-interactions pattern"
      }
    ],
    "warnings": [
      "Consider adding more comprehensive error handling"
    ],
    "recommendations": [
      "Implement proper access controls",
      "Add event logging for important state changes"
    ],
    "security_score": 60,
    "tools_used": ["pattern_detection", "slither"]
  }
}
```

### Monitor Transaction Security

Monitor a transaction for security issues.

**Endpoint**: `POST /api/v1/security/monitor-transaction`

**Request Body**:
```json
{
  "tx_hash": "0xabcdef...",
  "options": {
    "include_analysis": true,
    "alert_threshold": "medium"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "monitoring": {
    "tx_hash": "0xabcdef...",
    "alerts": [],
    "risk_score": 25,
    "analysis": {
      "gas_usage": 21000,
      "gas_price": 20000000000,
      "status": "success"
    }
  }
}
```

---

## Monitoring API

### Get System Health

Get overall system health status.

**Endpoint**: `GET /api/v1/monitoring/health`

**Response**:
```json
{
  "status": "success",
  "health": {
    "status": "healthy",
    "cpu_usage": "20%",
    "memory_usage": "30%",
    "disk_usage": "50%",
    "network_status": "online",
    "services": {
      "ai_agent": "healthy",
      "blockchain": "healthy",
      "storage": "healthy",
      "security": "healthy"
    }
  }
}
```

### Get Performance Metrics

Get system performance metrics.

**Endpoint**: `GET /api/v1/monitoring/metrics`

**Response**:
```json
{
  "status": "success",
  "metrics": {
    "response_time_avg": "100ms",
    "api_calls_per_min": 120,
    "error_rate": "0.5%",
    "contract_generation_time": "2.5s",
    "audit_processing_time": "1.8s",
    "storage_operations": 45
  }
}
```

### Monitor Transactions

Monitor recent transactions.

**Endpoint**: `GET /api/v1/monitoring/transactions`

**Response**:
```json
{
  "status": "success",
  "transactions": [
    {
      "tx_hash": "0x123...",
      "status": "success",
      "gas_used": 21000,
      "block_number": 12345,
      "timestamp": "2025-10-27T10:00:00Z"
    }
  ]
}
```

---

## RAG API

### Similarity Search

Perform similarity search on the knowledge base.

**Endpoint**: `POST /api/v1/rag/search`

**Request Body**:
```json
{
  "query": "DeFi lending protocols",
  "limit": 5,
  "options": {
    "include_metadata": true,
    "threshold": 0.7
  }
}
```

**Response**:
```json
{
  "status": "success",
  "results": [
    {
      "id": "doc_123",
      "content": "DeFi lending protocols enable users to...",
      "similarity": 0.95,
      "metadata": {
        "type": "technical_doc",
        "source": "whitepaper",
        "date": "2025-10-01"
      }
    }
  ],
  "total_results": 1
}
```

### Add Document

Add a document to the knowledge base.

**Endpoint**: `POST /api/v1/rag/document`

**Request Body**:
```json
{
  "document": {
    "content": "Document content here...",
    "title": "DeFi Security Best Practices",
    "type": "technical_doc",
    "metadata": {
      "author": "HyperKit Team",
      "date": "2025-10-27"
    }
  }
}
```

**Response**:
```json
{
  "status": "success",
  "document": {
    "id": "doc_456",
    "title": "DeFi Security Best Practices",
    "added": true
  }
}
```

### Get Document

Get a document by ID.

**Endpoint**: `GET /api/v1/rag/document/{doc_id}`

**Response**:
```json
{
  "status": "success",
  "document": {
    "id": "doc_456",
    "content": "Document content here...",
    "title": "DeFi Security Best Practices",
    "metadata": {
      "author": "HyperKit Team",
      "date": "2025-10-27"
    }
  }
}
```

---

## Verification API

### Verify Contract

Verify a contract on a block explorer.

**Endpoint**: `POST /api/v1/verification/verify`

**Request Body**:
```json
{
  "address": "0x1234567890123456789012345678901234567890",
  "source_code": "pragma solidity ^0.8.0;\n...",
  "compiler_version": "0.8.19",
  "license_type": "MIT",
  "network": "hyperion"
}
```

**Response**:
```json
{
  "status": "success",
  "verification": {
    "verification_id": "ver_12345",
    "explorer_url": "https://explorer.hyperion.network/address/0x123...#code",
    "status": "verified",
    "network": "hyperion"
  }
}
```

### Get Verification Status

Get the status of a verification request.

**Endpoint**: `GET /api/v1/verification/status/{verification_id}`

**Response**:
```json
{
  "status": "success",
  "verification": {
    "verification_id": "ver_12345",
    "status": "verified",
    "explorer_url": "https://explorer.hyperion.network/address/0x123...#code",
    "created": "2025-10-27T10:00:00Z",
    "completed": "2025-10-27T10:01:00Z"
  }
}
```

---

## Error Handling

### Error Response Format

All API errors follow a consistent format:

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid contract code provided",
    "details": {
      "field": "contract_code",
      "reason": "Missing pragma directive"
    }
  },
  "request_id": "req_12345",
  "timestamp": "2025-10-27T10:00:00Z"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `AUTHENTICATION_ERROR` | 401 | Invalid or missing API key |
| `AUTHORIZATION_ERROR` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### Common Error Scenarios

#### Invalid API Key
```json
{
  "status": "error",
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "Invalid API key provided"
  }
}
```

#### Rate Limit Exceeded
```json
{
  "status": "error",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 60 seconds",
    "retry_after": 60
  }
}
```

#### Service Unavailable
```json
{
  "status": "error",
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "AI service temporarily unavailable",
    "retry_after": 300
  }
}
```

---

## Rate Limits

### Rate Limit Headers

All API responses include rate limit information:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

### Rate Limits by Endpoint

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/v1/generate` | 100 | 1 hour |
| `/api/v1/audit` | 200 | 1 hour |
| `/api/v1/blockchain/deploy` | 50 | 1 hour |
| `/api/v1/storage/*` | 500 | 1 hour |
| `/api/v1/monitoring/*` | 1000 | 1 hour |
| All others | 1000 | 1 hour |

### Rate Limit Exceeded

When rate limits are exceeded:

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640995200
Retry-After: 3600
```

---

## SDKs and Libraries

### Python SDK

```python
from hyperkit_agent import HyperKitClient

client = HyperKitClient(api_key="your_api_key")

# Generate contract
contract = await client.generate_contract({
    "name": "MyToken",
    "type": "ERC20",
    "features": ["mintable", "burnable"]
})

# Audit contract
audit = await client.audit_contract(contract.code)

# Deploy contract
deployment = await client.deploy_contract(contract.code)
```

### JavaScript SDK

```javascript
import { HyperKitClient } from '@hyperkit/agent-sdk';

const client = new HyperKitClient('your_api_key');

// Generate contract
const contract = await client.generateContract({
  name: 'MyToken',
  type: 'ERC20',
  features: ['mintable', 'burnable']
});

// Audit contract
const audit = await client.auditContract(contract.code);

// Deploy contract
const deployment = await client.deployContract(contract.code);
```

---

## Webhooks

### Webhook Events

| Event | Description |
|-------|-------------|
| `contract.generated` | Contract generation completed |
| `contract.audited` | Contract audit completed |
| `contract.deployed` | Contract deployment completed |
| `contract.verified` | Contract verification completed |
| `security.alert` | Security alert triggered |
| `system.health` | System health status changed |

### Webhook Payload

```json
{
  "event": "contract.generated",
  "data": {
    "contract_id": "contract_123",
    "name": "MyToken",
    "type": "ERC20",
    "security_score": 95
  },
  "timestamp": "2025-10-27T10:00:00Z",
  "webhook_id": "webhook_123"
}
```

---

## Related Documentation

- **[Technical Documentation](TECHNICAL_DOCUMENTATION.md)** - System architecture and implementation details
- **[Integration Guide](INTEGRATOR_GUIDE.md)** - Integration patterns and best practices  
- **[Security Setup](SECURITY_SETUP.md)** - Security configuration and best practices
- **[Production Mode](PRODUCTION_MODE.md)** - Production deployment guidelines
- **[Emergency Response](EMERGENCY_RESPONSE.md)** - Incident response procedures

---

*Last Updated: October 27, 2025*  
*Location*: `/hyperkit-agent/docs/API_REFERENCE.md`
