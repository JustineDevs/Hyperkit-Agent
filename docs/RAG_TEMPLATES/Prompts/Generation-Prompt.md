<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: 1.4.6  
**Last Verified**: 2025-10-28  
**Commit**: `d5465090`  
**Branch**: `main`  
<!-- AUDIT_BADGE_END -->

# Contract Generation Prompt Templates

## Basic Contract Generation

### ERC20 Token
```
Create a secure ERC20 token contract with the following specifications:
- Name: {TOKEN_NAME}
- Symbol: {TOKEN_SYMBOL}
- Decimals: 18
- Initial Supply: {INITIAL_SUPPLY}
- Features: Mintable, Burnable, Pausable
- Access Control: Owner-only minting
- Security: ReentrancyGuard, proper validation
- Standards: OpenZeppelin implementations
```

### ERC721 NFT
```
Create a secure ERC721 NFT contract with the following specifications:
- Name: {NFT_NAME}
- Symbol: {NFT_SYMBOL}
- Features: Enumerable, Pausable, Metadata
- Minting: Owner-controlled with supply limit
- Security: ReentrancyGuard, access controls
- Standards: OpenZeppelin implementations
- Gas Optimization: Batch operations
```

### DeFi Protocol
```
Create a secure DeFi protocol contract with the following specifications:
- Type: {PROTOCOL_TYPE} (DEX, Lending, Staking, etc.)
- Features: {FEATURES_LIST}
- Security: ReentrancyGuard, access controls, oracle integration
- Gas Optimization: Efficient storage patterns
- Standards: ERC20, ERC721, or custom interfaces
- Testing: Comprehensive test coverage
```

## Advanced Contract Generation

### Governance Contract
```
Create a secure governance contract with the following specifications:
- Type: {GOVERNANCE_TYPE} (Token-based, Multisig, etc.)
- Features: Proposal creation, voting, execution, timelock
- Security: Proper access controls, proposal validation
- Standards: OpenZeppelin Governor
- Gas Optimization: Efficient voting mechanisms
- Integration: Token integration, timelock controller
```

### Upgradeable Contract
```
Create a secure upgradeable contract with the following specifications:
- Type: {CONTRACT_TYPE}
- Upgrade Pattern: {UPGRADE_PATTERN} (Proxy, Beacon, etc.)
- Features: {FEATURES_LIST}
- Security: Proper initialization, storage layout
- Standards: OpenZeppelin upgradeable contracts
- Gas Optimization: Efficient proxy patterns
```

## Security-Focused Generation

### High-Security Contract
```
Create a high-security smart contract with the following specifications:
- Type: {CONTRACT_TYPE}
- Security Level: Maximum
- Features: {FEATURES_LIST}
- Security Measures:
  - ReentrancyGuard on all external functions
  - Access control with role-based permissions
  - Input validation and bounds checking
  - Emergency pause functionality
  - Circuit breakers for critical operations
  - Oracle price validation
  - MEV protection where applicable
- Standards: OpenZeppelin security contracts
- Gas Optimization: Efficient but secure patterns
```

### Audit-Ready Contract
```
Create an audit-ready smart contract with the following specifications:
- Type: {CONTRACT_TYPE}
- Features: {FEATURES_LIST}
- Audit Requirements:
  - Comprehensive NatSpec documentation
  - Clear function and variable naming
  - Proper error handling and custom errors
  - Event emission for all state changes
  - Gas optimization without compromising security
  - Clear separation of concerns
  - Modular design for easy testing
- Standards: OpenZeppelin implementations
- Testing: Unit test coverage considerations
```

## Prompt Engineering Tips

### Context Addition
- Always include security requirements
- Specify OpenZeppelin usage
- Mention gas optimization needs
- Include specific standards compliance
- Add testing requirements

### Feature Specification
- Be specific about required features
- Mention optional features clearly
- Specify access control patterns
- Include upgrade requirements
- Mention integration needs

### Security Focus
- Always request security best practices
- Mention common vulnerability prevention
- Request proper error handling
- Include input validation requirements
- Specify access control patterns

### Code Quality
- Request clean, readable code
- Ask for proper documentation
- Include comprehensive comments
- Request consistent naming
- Ask for modular design

## Example Prompts

### Simple ERC20
```
Create a simple ERC20 token called "MyToken" (MTK) with 1,000,000 initial supply, mintable by owner, using OpenZeppelin contracts and following security best practices.
```

### Complex DeFi
```
Create a decentralized exchange contract with liquidity pools, automated market making, fee collection, and governance integration. Use OpenZeppelin contracts, implement proper security measures, and optimize for gas efficiency.
```

### Governance System
```
Create a token-based governance system with proposal creation, voting mechanisms, timelock execution, and emergency procedures. Use OpenZeppelin Governor contracts and implement comprehensive security measures.
```
