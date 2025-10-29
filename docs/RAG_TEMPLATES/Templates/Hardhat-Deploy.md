<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: 1.5.0  
**Last Verified**: 2025-10-28  
**Commit**: `d5465090`  
**Branch**: `main`  
<!-- AUDIT_BADGE_END -->

# Hardhat Deployment Template

## Basic Deployment Script

```javascript
const { ethers } = require("hardhat");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with the account:", deployer.address);
  console.log("Account balance:", (await deployer.getBalance()).toString());

  // Deploy contract
  const Contract = await ethers.getContractFactory("YourContract");
  const contract = await Contract.deploy(/* constructor args */);
  
  await contract.deployed();
  console.log("Contract deployed to:", contract.address);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
```

## Advanced Deployment with Verification

```javascript
const { ethers, run } = require("hardhat");

async function main() {
  const [deployer] = await ethers.getSigners();
  
  // Deploy contract
  const Contract = await ethers.getContractFactory("YourContract");
  const contract = await Contract.deploy(/* constructor args */);
  
  await contract.deployed();
  console.log("Contract deployed to:", contract.address);
  
  // Wait for block confirmations
  await contract.deployTransaction.wait(6);
  
  // Verify contract
  try {
    await run("verify:verify", {
      address: contract.address,
      constructorArguments: [/* constructor args */],
    });
    console.log("Contract verified successfully");
  } catch (error) {
    console.log("Verification failed:", error.message);
  }
}
```

## Multi-Network Deployment

```javascript
const { ethers } = require("hardhat");

async function main() {
  const networks = ["mainnet", "polygon", "arbitrum"];
  
  for (const network of networks) {
    console.log(`\nDeploying to ${network}...`);
    
    // Switch to network
    await hre.changeNetwork(network);
    
    const [deployer] = await ethers.getSigners();
    const Contract = await ethers.getContractFactory("YourContract");
    const contract = await Contract.deploy(/* constructor args */);
    
    await contract.deployed();
    console.log(`${network} deployment:`, contract.address);
  }
}
```

## Environment Configuration

### .env file
```bash
# Network RPC URLs
MAINNET_RPC_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID
POLYGON_RPC_URL=https://polygon-rpc.com
ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc

# Private Keys
MAINNET_PRIVATE_KEY=your_private_key_here
POLYGON_PRIVATE_KEY=your_private_key_here
ARBITRUM_PRIVATE_KEY=your_private_key_here

# Etherscan API Keys
ETHERSCAN_API_KEY=your_etherscan_api_key
POLYGONSCAN_API_KEY=your_polygonscan_api_key
ARBISCAN_API_KEY=your_arbiscan_api_key
```

### hardhat.config.js
```javascript
require("@nomiclabs/hardhat-ethers");
require("@nomiclabs/hardhat-etherscan");
require("dotenv").config();

module.exports = {
  solidity: "0.8.19",
  networks: {
    mainnet: {
      url: process.env.MAINNET_RPC_URL,
      accounts: [process.env.MAINNET_PRIVATE_KEY],
    },
    polygon: {
      url: process.env.POLYGON_RPC_URL,
      accounts: [process.env.POLYGON_PRIVATE_KEY],
    },
    arbitrum: {
      url: process.env.ARBITRUM_RPC_URL,
      accounts: [process.env.ARBITRUM_PRIVATE_KEY],
    },
  },
  etherscan: {
    apiKey: {
      mainnet: process.env.ETHERSCAN_API_KEY,
      polygon: process.env.POLYGONSCAN_API_KEY,
      arbitrumOne: process.env.ARBISCAN_API_KEY,
    },
  },
};
```

## Deployment Best Practices

### Gas Optimization
- Use `--gas-price` flag for manual gas price
- Monitor gas prices before deployment
- Consider using gas estimation tools
- Batch operations when possible

### Security
- Use multi-sig wallets for mainnet deployments
- Test on testnets first
- Verify contracts after deployment
- Keep private keys secure

### Monitoring
- Set up monitoring for deployed contracts
- Track contract interactions
- Monitor for unusual activity
- Set up alerts for critical functions

### Documentation
- Document deployment addresses
- Record constructor parameters
- Update ABI files
- Maintain deployment logs
