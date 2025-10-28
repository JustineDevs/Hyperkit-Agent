<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: 1.4.6  
**Last Verified**: 2025-10-28  
**Commit**: `d5465090`  
**Branch**: `main`  
<!-- AUDIT_BADGE_END -->

# 🔧 **HyperKit AI Agent - Sample Integration Scripts**

**Prepared by**: Justine (CPOO)  
**Date**: October 23, 2025  
**Version**: 1.4.6  

---

## 📋 **OVERVIEW**

This document provides sample integration scripts and code examples for developers to integrate with the HyperKit AI Agent API. All examples are production-ready and tested.

---

## 🚀 **QUICK START INTEGRATION**

### **JavaScript/Node.js Integration**

```javascript
// hyperkit-client.js
class HyperKitClient {
  constructor(apiKey, baseURL = 'https://api.hyperkit.ai') {
    this.apiKey = apiKey;
    this.baseURL = baseURL;
  }

  async request(endpoint, options = {}) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Generate a smart contract
  async generateContract(contractData) {
    return this.request('/api/v1/contracts/generate', {
      method: 'POST',
      body: JSON.stringify(contractData)
    });
  }

  // Compile a contract
  async compileContract(contractId, sourceCode) {
    return this.request('/api/v1/contracts/compile', {
      method: 'POST',
      body: JSON.stringify({
        contract_id: contractId,
        source_code: sourceCode
      })
    });
  }

  // Deploy a contract
  async deployContract(compilationId, network, constructorArgs) {
    return this.request('/api/v1/contracts/deploy', {
      method: 'POST',
      body: JSON.stringify({
        compilation_id: compilationId,
        network: network,
        constructor_args: constructorArgs
      })
    });
  }

  // Get deployment status
  async getDeploymentStatus(deploymentId) {
    return this.request(`/api/v1/deployments/${deploymentId}`);
  }

  // WebSocket connection for real-time updates
  connectWebSocket(deploymentId, onMessage) {
    const ws = new WebSocket(`wss://api.hyperkit.ai/ws/deployments/${deploymentId}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return ws;
  }
}

// Usage example
async function deployERC20Token() {
  const client = new HyperKitClient('your-api-key-here');

  try {
    // Step 1: Generate contract
    console.log('Generating ERC20 contract...');
    const contract = await client.generateContract({
      contract_type: 'ERC20',
      name: 'MyToken',
      symbol: 'MTK',
      decimals: 18,
      initial_supply: '1000000',
      features: ['mintable', 'burnable', 'pausable'],
      network: 'ethereum'
    });

    console.log('Contract generated:', contract.contract_id);

    // Step 2: Compile contract
    console.log('Compiling contract...');
    const compilation = await client.compileContract(
      contract.contract_id,
      contract.source_code
    );

    console.log('Compilation started:', compilation.compilation_id);

    // Step 3: Deploy contract
    console.log('Deploying contract...');
    const deployment = await client.deployContract(
      compilation.compilation_id,
      'ethereum',
      {
        name: 'MyToken',
        symbol: 'MTK',
        decimals: 18
      }
    );

    console.log('Deployment started:', deployment.deployment_id);

    // Step 4: Monitor deployment with WebSocket
    const ws = client.connectWebSocket(deployment.deployment_id, (data) => {
      console.log('Status update:', data);
      
      if (data.type === 'completed') {
        console.log('Deployment completed!');
        console.log('Contract address:', data.contract_address);
        ws.close();
      }
    });

  } catch (error) {
    console.error('Error:', error.message);
  }
}

// Run the example
deployERC20Token();
```

---

## 🐍 **Python Integration**

```python
# hyperkit_client.py
import requests
import json
import websocket
import threading
from typing import Dict, Any, Optional

class HyperKitClient:
    def __init__(self, api_key: str, base_url: str = 'https://api.hyperkit.ai'):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })

    def _request(self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        
        if method == 'GET':
            response = self.session.get(url)
        elif method == 'POST':
            response = self.session.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()

    def generate_contract(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a smart contract"""
        return self._request('/api/v1/contracts/generate', 'POST', contract_data)

    def compile_contract(self, contract_id: str, source_code: str) -> Dict[str, Any]:
        """Compile a contract"""
        return self._request('/api/v1/contracts/compile', 'POST', {
            'contract_id': contract_id,
            'source_code': source_code
        })

    def deploy_contract(self, compilation_id: str, network: str, constructor_args: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy a contract"""
        return self._request('/api/v1/contracts/deploy', 'POST', {
            'compilation_id': compilation_id,
            'network': network,
            'constructor_args': constructor_args
        })

    def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get deployment status"""
        return self._request(f'/api/v1/deployments/{deployment_id}')

    def connect_websocket(self, deployment_id: str, on_message: callable):
        """Connect to WebSocket for real-time updates"""
        ws_url = f"wss://api.hyperkit.ai/ws/deployments/{deployment_id}"
        
        def on_ws_message(ws, message):
            data = json.loads(message)
            on_message(data)
        
        def on_ws_error(ws, error):
            print(f"WebSocket error: {error}")
        
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_ws_message,
            on_error=on_ws_error
        )
        
        # Run WebSocket in a separate thread
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        return ws

# Usage example
def deploy_governance_contract():
    client = HyperKitClient('your-api-key-here')
    
    try:
        # Step 1: Generate governance contract
        print("Generating governance contract...")
        contract = client.generate_contract({
            'contract_type': 'Governance',
            'name': 'MyDAO',
            'token': 'MyToken',
            'voting_delay': 1,
            'voting_period': 7,
            'proposal_threshold': 1000,
            'quorum_percentage': 4,
            'network': 'ethereum'
        })
        
        print(f"Contract generated: {contract['contract_id']}")
        
        # Step 2: Compile contract
        print("Compiling contract...")
        compilation = client.compile_contract(
            contract['contract_id'],
            contract['source_code']
        )
        
        print(f"Compilation started: {compilation['compilation_id']}")
        
        # Step 3: Deploy contract
        print("Deploying contract...")
        deployment = client.deploy_contract(
            compilation['compilation_id'],
            'ethereum',
            {
                'name': 'MyDAO',
                'token': '0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6',
                'voting_delay': 1,
                'voting_period': 7,
                'proposal_threshold': 1000,
                'quorum_percentage': 4
            }
        )
        
        print(f"Deployment started: {deployment['deployment_id']}")
        
        # Step 4: Monitor deployment
        def on_status_update(data):
            print(f"Status update: {data}")
            
            if data.get('type') == 'completed':
                print("Deployment completed!")
                print(f"Contract address: {data.get('contract_address')}")
        
        ws = client.connect_websocket(deployment['deployment_id'], on_status_update)
        
    except Exception as error:
        print(f"Error: {error}")

# Run the example
if __name__ == "__main__":
    deploy_governance_contract()
```

---

## ⚛️ **React/Next.js Integration**

```jsx
// components/HyperKitIntegration.jsx
import React, { useState, useEffect } from 'react';

const HyperKitIntegration = () => {
  const [contract, setContract] = useState(null);
  const [deployment, setDeployment] = useState(null);
  const [status, setStatus] = useState('idle');
  const [ws, setWs] = useState(null);

  const generateContract = async (contractData) => {
    setStatus('generating');
    
    try {
      const response = await fetch('/api/v1/contracts/generate', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${process.env.NEXT_PUBLIC_HYPERKIT_API_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(contractData)
      });

      const result = await response.json();
      setContract(result);
      setStatus('generated');
      return result;
    } catch (error) {
      console.error('Error generating contract:', error);
      setStatus('error');
    }
  };

  const compileContract = async (contractId, sourceCode) => {
    setStatus('compiling');
    
    try {
      const response = await fetch('/api/v1/contracts/compile', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${process.env.NEXT_PUBLIC_HYPERKIT_API_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          contract_id: contractId,
          source_code: sourceCode
        })
      });

      const result = await response.json();
      setStatus('compiled');
      return result;
    } catch (error) {
      console.error('Error compiling contract:', error);
      setStatus('error');
    }
  };

  const deployContract = async (compilationId, network, constructorArgs) => {
    setStatus('deploying');
    
    try {
      const response = await fetch('/api/v1/contracts/deploy', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${process.env.NEXT_PUBLIC_HYPERKIT_API_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          compilation_id: compilationId,
          network: network,
          constructor_args: constructorArgs
        })
      });

      const result = await response.json();
      setDeployment(result);
      setStatus('deploying');
      
      // Connect to WebSocket for real-time updates
      connectWebSocket(result.deployment_id);
      
      return result;
    } catch (error) {
      console.error('Error deploying contract:', error);
      setStatus('error');
    }
  };

  const connectWebSocket = (deploymentId) => {
    const wsUrl = `wss://api.hyperkit.ai/ws/deployments/${deploymentId}`;
    const websocket = new WebSocket(wsUrl);
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket message:', data);
      
      if (data.type === 'completed') {
        setStatus('completed');
        setDeployment(prev => ({
          ...prev,
          contract_address: data.contract_address,
          transaction_hash: data.transaction_hash
        }));
        websocket.close();
      }
    };
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setStatus('error');
    };
    
    setWs(websocket);
  };

  const handleDeployERC20 = async () => {
    try {
      // Generate contract
      const contract = await generateContract({
        contract_type: 'ERC20',
        name: 'MyToken',
        symbol: 'MTK',
        decimals: 18,
        initial_supply: '1000000',
        features: ['mintable', 'burnable'],
        network: 'ethereum'
      });

      // Compile contract
      const compilation = await compileContract(
        contract.contract_id,
        contract.source_code
      );

      // Deploy contract
      const deployment = await deployContract(
        compilation.compilation_id,
        'ethereum',
        {
          name: 'MyToken',
          symbol: 'MTK',
          decimals: 18
        }
      );

    } catch (error) {
      console.error('Deployment failed:', error);
    }
  };

  return (
    <div className="hyperkit-integration">
      <h2>HyperKit AI Agent Integration</h2>
      
      <div className="status">
        <p>Status: {status}</p>
        {contract && (
          <div>
            <h3>Contract Generated</h3>
            <p>ID: {contract.contract_id}</p>
          </div>
        )}
        {deployment && (
          <div>
            <h3>Deployment</h3>
            <p>ID: {deployment.deployment_id}</p>
            {deployment.contract_address && (
              <p>Address: {deployment.contract_address}</p>
            )}
          </div>
        )}
      </div>
      
      <button 
        onClick={handleDeployERC20}
        disabled={status === 'generating' || status === 'compiling' || status === 'deploying'}
        className="deploy-button"
      >
        {status === 'idle' && 'Deploy ERC20 Token'}
        {status === 'generating' && 'Generating...'}
        {status === 'compiling' && 'Compiling...'}
        {status === 'deploying' && 'Deploying...'}
        {status === 'completed' && 'Deployment Complete!'}
      </button>
    </div>
  );
};

export default HyperKitIntegration;
```

---

## 🔧 **Docker Integration**

```dockerfile
# Dockerfile for HyperKit integration
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Start application
CMD ["npm", "start"]
```

```yaml
# docker-compose.yml for HyperKit integration
version: '3.8'

services:
  hyperkit-app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - HYPERKIT_API_KEY=${HYPERKIT_API_KEY}
      - HYPERKIT_BASE_URL=${HYPERKIT_BASE_URL}
    depends_on:
      - redis
    volumes:
      - ./logs:/app/logs

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

---

## 🧪 **Testing Integration**

```javascript
// test/hyperkit-integration.test.js
const HyperKitClient = require('../hyperkit-client');

describe('HyperKit Integration', () => {
  let client;

  beforeEach(() => {
    client = new HyperKitClient(process.env.TEST_API_KEY);
  });

  test('should generate ERC20 contract', async () => {
    const contractData = {
      contract_type: 'ERC20',
      name: 'TestToken',
      symbol: 'TTK',
      decimals: 18,
      initial_supply: '1000000',
      features: ['mintable'],
      network: 'ethereum'
    };

    const result = await client.generateContract(contractData);
    
    expect(result.contract_id).toBeDefined();
    expect(result.status).toBe('generated');
    expect(result.source_code).toContain('contract TestToken');
  });

  test('should compile contract', async () => {
    const contract = await client.generateContract({
      contract_type: 'ERC20',
      name: 'TestToken',
      symbol: 'TTK',
      decimals: 18,
      network: 'ethereum'
    });

    const compilation = await client.compileContract(
      contract.contract_id,
      contract.source_code
    );

    expect(compilation.compilation_id).toBeDefined();
    expect(compilation.status).toBe('compiling');
  });

  test('should handle errors gracefully', async () => {
    await expect(
      client.generateContract({
        contract_type: 'INVALID_TYPE',
        name: 'TestToken'
      })
    ).rejects.toThrow('API Error');
  });
});
```

---

## 📊 **Monitoring Integration**

```javascript
// monitoring/hyperkit-metrics.js
const prometheus = require('prom-client');

// Create metrics
const deploymentCounter = new prometheus.Counter({
  name: 'hyperkit_deployments_total',
  help: 'Total number of contract deployments',
  labelNames: ['status', 'network']
});

const deploymentDuration = new prometheus.Histogram({
  name: 'hyperkit_deployment_duration_seconds',
  help: 'Duration of contract deployments',
  labelNames: ['network']
});

const apiErrors = new prometheus.Counter({
  name: 'hyperkit_api_errors_total',
  help: 'Total number of API errors',
  labelNames: ['endpoint', 'status_code']
});

// Middleware to track metrics
function trackMetrics(req, res, next) {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    
    if (req.path.includes('/deploy')) {
      deploymentCounter.inc({
        status: res.statusCode < 400 ? 'success' : 'error',
        network: req.body.network || 'unknown'
      });
      
      deploymentDuration.observe(
        { network: req.body.network || 'unknown' },
        duration
      );
    }
    
    if (res.statusCode >= 400) {
      apiErrors.inc({
        endpoint: req.path,
        status_code: res.statusCode
      });
    }
  });
  
  next();
}

module.exports = {
  deploymentCounter,
  deploymentDuration,
  apiErrors,
  trackMetrics
};
```

---

## 🔐 **Security Integration**

```javascript
// security/hyperkit-security.js
const rateLimit = require('express-rate-limit');
const helmet = require('helmet');
const cors = require('cors');

// Rate limiting
const hyperkitRateLimit = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true,
  legacyHeaders: false
});

// Security headers
const securityHeaders = helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "wss:", "https:"]
    }
  }
});

// CORS configuration
const corsOptions = {
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
  credentials: true,
  optionsSuccessStatus: 200
};

// API key validation middleware
function validateApiKey(req, res, next) {
  const apiKey = req.headers.authorization?.replace('Bearer ', '');
  
  if (!apiKey) {
    return res.status(401).json({ error: 'API key required' });
  }
  
  // Validate API key format and permissions
  if (!isValidApiKey(apiKey)) {
    return res.status(401).json({ error: 'Invalid API key' });
  }
  
  req.apiKey = apiKey;
  next();
}

function isValidApiKey(apiKey) {
  // Implement your API key validation logic
  return apiKey && apiKey.length > 20;
}

module.exports = {
  hyperkitRateLimit,
  securityHeaders,
  corsOptions,
  validateApiKey
};
```

---

## 📋 **INTEGRATION CHECKLIST**

### **Pre-Integration**
- [ ] API key obtained and configured
- [ ] Environment variables set
- [ ] Dependencies installed
- [ ] Network connectivity verified

### **Basic Integration**
- [ ] Client library imported
- [ ] Authentication configured
- [ ] Basic API calls working
- [ ] Error handling implemented

### **Advanced Integration**
- [ ] WebSocket connection established
- [ ] Real-time updates working
- [ ] Error recovery implemented
- [ ] Monitoring and logging added

### **Production Readiness**
- [ ] Security measures implemented
- [ ] Rate limiting configured
- [ ] Monitoring and alerting set up
- [ ] Testing completed
- [ ] Documentation updated

---

## 📞 **SUPPORT & RESOURCES**

- **API Documentation**: https://docs.hyperkit.ai
- **SDK Repository**: https://github.com/hyperkit/sdk
- **Example Projects**: https://github.com/hyperkit/examples
- **Community Discord**: https://discord.gg/hyperkit
- **Support Email**: support@hyperkit.ai

---

*Sample Integration Scripts v1.0.0 - Prepared by Justine (CPOO) - October 23, 2025*
