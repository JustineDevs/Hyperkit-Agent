<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: 1.4.6  
**Last Verified**: 2025-10-28  
**Commit**: `6f63afe4`  
**Branch**: `main`  
<!-- AUDIT_BADGE_END -->

# HyperAgent CLI Commands Reference

**Generated**: October 28, 2025  
**Purpose**: Complete reference of all available CLI commands

---

## Main Command Structure

```bash
hyperagent [GLOBAL_OPTIONS] <command> [COMMAND_OPTIONS]
```

### Global Options
- `--verbose, -v` - Enable verbose output
- `--debug, -d` - Enable debug mode

---

## Available Commands

### 1. Status & Information

#### `hyperagent status`
Check system health and production mode status

```bash
hyperagent status
```

#### `hyperagent version`
Show version information

```bash
hyperagent version
```

#### `hyperagent limitations`
Show all known limitations and broken features

```bash
hyperagent limitations
```

---

### 2. Generate Contracts

#### `hyperagent generate contract`
Generate smart contracts with AI

```bash
hyperagent generate contract --type <TYPE> --name <NAME> [OPTIONS]
```

**Options:**
- `--type, -t` - Contract type (ERC20, ERC721, DeFi, etc.)
- `--name, -n` - Contract name
- `--output, -o` - Output directory
- `--network` - Target network (default: hyperion)
- `--template` - Use specific template

**Examples:**
```bash
hyperagent generate contract --type ERC20 --name MyToken
hyperagent generate contract --type ERC721 --name MyNFT --network hyperion
```

---

### 3. Deploy Contracts

#### `hyperagent deploy contract`
Deploy a smart contract

```bash
hyperagent deploy contract --contract <FILE> [OPTIONS]
```

**Options:**
- `--contract, -c` - Contract file path (required)
- `--network, -n` - Target network (default: hyperion)
- `--private-key, -k` - Private key for deployment
- `--gas-limit, -g` - Gas limit for deployment
- `--gas-price` - Gas price for deployment
- `--args` - Constructor arguments as JSON array
- `--file` - Path to JSON file with constructor arguments

**Examples:**
```bash
hyperagent deploy contract --contract MyToken.sol
hyperagent deploy contract --contract MyToken.sol --args '["0x1234...", 1000000]'
hyperagent deploy contract --contract MyToken.sol --file args.json
```

#### `hyperagent deploy status`
Check deployment status

```bash
hyperagent deploy status [--network NETWORK]
```

#### `hyperagent deploy info`
Get deployment information

```bash
hyperagent deploy info --address <ADDRESS> [--network NETWORK]
```

---

### 4. Audit Contracts

#### `hyperagent audit contract`
Audit a smart contract for security issues

```bash
hyperagent audit contract [OPTIONS]
```

**Options:**
- `--contract, -c` - Contract file path
- `--address, -a` - Contract address to audit
- `--network, -n` - Network for address-based audit (default: hyperion)
- `--output, -o` - Output file for audit report
- `--format, -f` - Output format (json, markdown, html)
- `--severity, -s` - Minimum severity level (low, medium, high, critical)

**Examples:**
```bash
hyperagent audit contract --contract MyToken.sol
hyperagent audit contract --address 0x1234... --network hyperion
hyperagent audit contract --contract MyToken.sol --format markdown
```

---

### 5. Batch Audit

#### `hyperagent batch-audit contracts`
Audit multiple contracts in batch

```bash
hyperagent batch-audit contracts --files <FILE1> [--files <FILE2> ...] [OPTIONS]
```

**Options:**
- `--files, -f` - Contract files to audit (required, multiple allowed)
- `--output, -o` - Output directory (default: artifacts/batch-audits)
- `--format, -fmt` - Output format (json, markdown, html, csv, pdf, excel, all)
- `--batch-name, -n` - Name for this batch audit

**Examples:**
```bash
hyperagent batch-audit contracts -f Contract1.sol -f Contract2.sol
hyperagent batch-audit contracts -f *.sol --format all
hyperagent batch-audit contracts -f contracts/ --format excel -n "Q4 Audit"
```

---

### 6. Verify Contracts

#### `hyperagent verify contract`
Verify a smart contract on block explorer

```bash
hyperagent verify contract --address <ADDRESS> [OPTIONS]
```

**Options:**
- `--address, -a` - Contract address (required)
- `--network, -n` - Network (default: hyperion)
- `--source, -s` - Source code file
- `--args` - Constructor arguments

**Examples:**
```bash
hyperagent verify contract --address 0x1234... --network hyperion
hyperagent verify contract --address 0x1234... --source MyToken.sol
```

---

### 7. Monitor

#### `hyperagent monitor health`
Check contract health

```bash
hyperagent monitor health [OPTIONS]
```

#### `hyperagent monitor transaction`
Monitor transaction

```bash
hyperagent monitor transaction --tx-hash <HASH> [OPTIONS]
```

#### `hyperagent monitor events`
Monitor contract events

```bash
hyperagent monitor events --address <ADDRESS> [OPTIONS]
```

#### `hyperagent monitor dashboard`
Show monitoring dashboard

```bash
hyperagent monitor dashboard
```

---

### 8. Configuration

#### `hyperagent config set`
Set configuration value

```bash
hyperagent config set --key <KEY> --value <VALUE>
```

#### `hyperagent config get`
Get configuration value

```bash
hyperagent config get --key <KEY>
```

#### `hyperagent config list`
List all configuration

```bash
hyperagent config list
```

#### `hyperagent config reset`
Reset configuration

```bash
hyperagent config reset
```

---

### 9. Workflow

#### `hyperagent workflow run`
Run complete AI-powered smart contract workflow

```bash
hyperagent workflow run "<PROMPT>" [OPTIONS]
```

**Options:**
- `--network, -n` - Target network (default: hyperion)
- `--no-audit` - Skip security audit stage
- `--no-verify` - Skip contract verification stage
- `--test-only` - Generate and audit only (no deployment)
- `--allow-insecure` - Deploy even with high-severity audit issues

**Examples:**
```bash
hyperagent workflow run "create pausable ERC20 token"
hyperagent workflow run "create staking contract with rewards" --network hyperion
hyperagent workflow run "create NFT contract" --test-only
hyperagent workflow run "create token" --allow-insecure
```

#### `hyperagent workflow status`
Check workflow status

```bash
hyperagent workflow status [--network NETWORK]
```

#### `hyperagent workflow list`
List available workflow templates

```bash
hyperagent workflow list
```

---

### 10. Testing & Utilities

#### `hyperagent test_rag`
Test RAG connections (Obsidian, IPFS, Local)

```bash
hyperagent test_rag
```

---

## Command Categories

### Core Commands
- `generate` - Generate contracts
- `deploy` - Deploy contracts
- `audit` - Audit contracts
- `verify` - Verify contracts

### Batch Operations
- `batch-audit` - Batch auditing

### Monitoring
- `monitor` - Monitor contracts

### Configuration
- `config` - Manage configuration
- `status` - System status
- `version` - Version info

### Advanced
- `workflow` - End-to-end workflows

---

## Common Patterns

### Full Contract Lifecycle
```bash
# Generate
hyperagent generate contract --type ERC20 --name MyToken

# Audit
hyperagent audit contract --contract MyToken.sol

# Deploy
hyperagent deploy contract --contract MyToken.sol --network hyperion

# Verify
hyperagent verify contract --address <DEPLOYED_ADDRESS> --network hyperion
```

### Workflow Approach
```bash
hyperagent workflow run "create ERC20 token named MyToken" --network hyperion
```

### Batch Audit
```bash
hyperagent batch-audit contracts -f contracts/*.sol --format all -n "Production Audit"
```

---

## Network Support

Supported networks:
- `hyperion` (default) - Hyperion testnet
- `metis` - Metis mainnet
- `polygon` - Polygon mainnet
- `arbitrum` - Arbitrum one

---

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Configuration error
- `3` - Network connection error
- `4` - Contract deployment error

