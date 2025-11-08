# HyperAgent CLI Commands Reference

**Version**: 1.6.7  
**Last Updated**: 2025-01-25  
**Purpose**: Complete reference of all CLI commands, subcommands, and RAG template integration

---

## Table of Contents

1. [Command Structure](#command-structure)
2. [Deployment & Projects Commands](#deployment--projects-commands)
3. [AI & Audit Automation Commands](#ai--audit-automation-commands)
4. [Status & Documentation Commands](#status--documentation-commands)
5. [RAG Template Integration](#rag-template-integration)
6. [Command Implementation Details](#command-implementation-details)
7. [Examples & Usage Patterns](#examples--usage-patterns)

---

## Command Structure

All commands are registered in `hyperkit-agent/cli/main.py` and organized into three groups:

**1. Deployment & Projects**: `deploy`, `verify`, `config`, `monitor`, `workflow`  
**2. AI & Audit Automation**: `audit`, `batch-audit`, `generate`, `context`  
**3. Status & Docs**: `status`, `doctor`, `docs`, `limitations`, `test-rag`, `version`

### Global Options

- `--verbose, -v` - Enable verbose output
- `--debug, -d` - Enable debug mode
- `--help, -h` - Show command help

---

## Deployment & Projects Commands

### `deploy` Command Group

**File**: `hyperkit-agent/cli/commands/deploy.py`  
**Purpose**: Deploy smart contracts to blockchain networks (Hyperion exclusive)

#### Subcommands

##### `deploy contract`

Deploy a smart contract using RAG deployment templates.

**Implementation**: ```20:193:hyperkit-agent/cli/commands/deploy.py```

**Options**:
- `--contract, -c` - Contract file path (required)
- `--network, -n` - Target network (default: hyperion, deprecated - Hyperion only)
- `--private-key, -k` - Private key for deployment
- `--gas-limit, -g` - Gas limit for deployment
- `--gas-price` - Gas price for deployment
- `--args` - Constructor arguments as JSON array (e.g., `'["0x1234...", 1000000]'`)
- `--file` - Path to JSON file with constructor arguments
- `--use-rag/--no-use-rag` - Use RAG deployment templates (default: true)

**RAG Integration**: Fetches `hardhat-deploy` template from IPFS Pinata for enhanced deployment context.

**Examples**:
```bash
# Auto-detect constructor arguments
hyperagent deploy contract MyToken.sol

# Provide custom constructor arguments
hyperagent deploy contract MyToken.sol --args '["0x1234...", 1000000]'

# Load constructor arguments from JSON file
hyperagent deploy contract MyToken.sol --file args.json
```

##### `deploy status`

Check deployment status for a network.

**Implementation**: ```160:175:hyperkit-agent/cli/commands/deploy.py```

**Options**:
- `--network, -n` - Network to check (default: hyperion)

**Example**:
```bash
hyperagent deploy status --network hyperion
```

##### `deploy info`

Get deployment information for a contract address.

**Implementation**: ```177:193:hyperkit-agent/cli/commands/deploy.py```

**Options**:
- `--address, -a` - Contract address (required)
- `--network, -n` - Network (default: hyperion)

**Example**:
```bash
hyperagent deploy info --address 0x1234... --network hyperion
```

---

### `verify` Command Group

**File**: `hyperkit-agent/cli/commands/verify.py`  
**Purpose**: Verify smart contracts on block explorers

#### Subcommands

##### `verify contract`

Verify a smart contract on block explorer.

**Implementation**: ```19:94:hyperkit-agent/cli/commands/verify.py```

**Options**:
- `--address, -a` - Contract address (required)
- `--network, -n` - Network (default: hyperion)
- `--source, -s` - Source code file
- `--args` - Constructor arguments

**Examples**:
```bash
hyperagent verify contract --address 0x1234... --network hyperion
hyperagent verify contract --address 0x1234... --source MyToken.sol
```

##### `verify status`

Check verification status.

**Implementation**: ```99:134:hyperkit-agent/cli/commands/verify.py```

##### `verify list`

List verified contracts.

**Implementation**: ```135:175:hyperkit-agent/cli/commands/verify.py```

---

### `config` Command Group

**File**: `hyperkit-agent/cli/commands/config.py`  
**Purpose**: Manage configuration settings and AI/LLM providers

#### Subcommands

##### `config set`

Set configuration value.

**Implementation**: ```32:73:hyperkit-agent/cli/commands/config.py```

**Options**:
- `--key` - Configuration key
- `--value` - Configuration value

##### `config get`

Get configuration value.

**Implementation**: ```186:224:hyperkit-agent/cli/commands/config.py```

##### `config list`

List all configuration.

**Implementation**: ```225:254:hyperkit-agent/cli/commands/config.py```

##### `config reset`

Reset configuration to defaults.

**Implementation**: ```255:309:hyperkit-agent/cli/commands/config.py```

##### `config foundry-check`

Check Foundry installation and configuration.

**Implementation**: ```74:185:hyperkit-agent/cli/commands/config.py```

##### `config llm`

Configure LLM provider (Gemini, OpenAI, Claude).

**Implementation**: ```310:346:hyperkit-agent/cli/commands/config.py```

---

### `monitor` Command Group

**File**: `hyperkit-agent/cli/commands/monitor.py`  
**Purpose**: Monitor system health and contract performance

#### Subcommands

##### `monitor health`

Check contract health.

**Implementation**: ```26:75:hyperkit-agent/cli/commands/monitor.py```

##### `monitor transaction`

Monitor transaction status.

**Implementation**: ```76:131:hyperkit-agent/cli/commands/monitor.py```

**Options**:
- `--tx-hash` - Transaction hash (required)

##### `monitor status`

Show monitoring status.

**Implementation**: ```135:191:hyperkit-agent/cli/commands/monitor.py```

##### `monitor dashboard`

Show monitoring dashboard.

**Implementation**: ```192:220:hyperkit-agent/cli/commands/monitor.py```

---

### `workflow` Command Group

**File**: `hyperkit-agent/cli/commands/workflow.py`  
**Purpose**: Run end-to-end smart contract workflows with autonomous loop

#### Subcommands

##### `workflow run`

Run complete AI-powered smart contract workflow.

**Implementation**: ```22:534:hyperkit-agent/cli/commands/workflow.py```

**Options**:
- `--network, -n` - Target network (default: hyperion)
- `--no-audit` - Skip security audit stage
- `--no-verify` - Skip contract verification stage
- `--test-only` - Generate and audit only (no deployment)
- `--allow-insecure` - Deploy even with high-severity audit issues

**RAG Integration**: Automatically fetches relevant templates from IPFS Pinata based on user prompt:
- Contract generation templates (`erc20-template`, `erc721-template`, etc.)
- Security checklists (`security-checklist`)
- Deployment templates (`hardhat-deploy`)

**Workflow Stages**:
1. **Generate** - AI generates contract code using RAG templates
2. **Audit** - Security audit using RAG security checklists
3. **Deploy** - Contract deployment to Hyperion
4. **Verify** - Contract verification on explorer
5. **Test** - Automated testing (optional)

**Examples**:
```bash
hyperagent workflow run "create pausable ERC20 token"
hyperagent workflow run "create staking contract with rewards" --network hyperion
hyperagent workflow run "create NFT contract" --test-only
```

##### `workflow status`

Check workflow status.

**Implementation**: ```535:629:hyperkit-agent/cli/commands/workflow.py```

**Options**:
- `--network, -n` - Network to check

##### `workflow inspect`

Inspect workflow details.

**Implementation**: ```630:685:hyperkit-agent/cli/commands/workflow.py```

##### `workflow list`

**List available RAG templates from IPFS Pinata.**

**Implementation**: ```686:792:hyperkit-agent/cli/commands/workflow.py```

**Enhancement**: This command now fetches actual RAG templates from the IPFS Pinata registry instead of showing hardcoded examples.

**Features**:
- Fetches templates from CID registry (`hyperkit-agent/docs/RAG_TEMPLATES/cid-registry.json`)
- Groups templates by category
- Shows template metadata (CID, gateway URL, description, upload status)
- Displays template statistics (total, uploaded, categories)
- Falls back to example templates if RAG fetch fails

**Output Format**:
```
Available RAG Templates from IPFS Pinata

Contracts:
  ✅ erc20-template
      Standard ERC20 fungible token contract template
      CID: QmYWkBLnCwUHtA4vgsFM4ePrCG9xpo2taHRsvEbbyz2JYs
      URL: https://gateway.pinata.cloud/ipfs/QmYWkBLnCwUHtA4vgsFM4ePrCG9xpo2taHRsvEbbyz2JYs

Template Statistics:
  Total Templates: 13
  Uploaded: 13
  Categories: 5
```

**Example**:
```bash
hyperagent workflow list
```

---

## AI & Audit Automation Commands

### `audit` Command Group

**File**: `hyperkit-agent/cli/commands/audit.py`  
**Purpose**: Audit smart contracts for security vulnerabilities

#### Subcommands

##### `audit contract`

Audit a smart contract for security issues using RAG checklists.

**Implementation**: ```20:138:hyperkit-agent/cli/commands/audit.py```

**Options**:
- `--contract, -c` - Contract file path
- `--address, -a` - Contract address to audit
- `--network, -n` - Network for address-based audit (default: hyperion)
- `--output, -o` - Output file for audit report
- `--format, -f` - Output format (json, markdown, html, default: json)
- `--severity, -s` - Minimum severity level (low, medium, high, critical)
- `--use-rag/--no-use-rag` - Use RAG security checklists (default: true)

**RAG Integration**: Fetches `security-checklist` template from IPFS Pinata for comprehensive security auditing.

**Examples**:
```bash
hyperagent audit contract --contract MyToken.sol
hyperagent audit contract --address 0x1234... --network hyperion
hyperagent audit contract --contract MyToken.sol --format markdown
```

##### `audit batch`

Batch audit multiple contracts.

**Implementation**: ```139:337:hyperkit-agent/cli/commands/audit.py```

##### `audit view`

View audit results.

**Implementation**: ```338:425:hyperkit-agent/cli/commands/audit.py```

---

### `batch-audit` Command Group

**File**: `hyperkit-agent/cli/commands/batch_audit.py`  
**Purpose**: Audit multiple contracts in batch

#### Subcommands

##### `batch-audit contracts`

Audit multiple contracts in batch.

**Implementation**: ```18:200:hyperkit-agent/cli/commands/batch_audit.py```

**Options**:
- `--files, -f` - Contract files to audit (required, multiple allowed)
- `--output, -o` - Output directory (default: artifacts/batch-audits)
- `--format, -fmt` - Output format (json, markdown, html, csv, pdf, excel, all)
- `--batch-name, -n` - Name for this batch audit

**Examples**:
```bash
hyperagent batch-audit contracts -f Contract1.sol -f Contract2.sol
hyperagent batch-audit contracts -f *.sol --format all
hyperagent batch-audit contracts -f contracts/ --format excel -n "Q4 Audit"
```

---

### `generate` Command Group

**File**: `hyperkit-agent/cli/commands/generate.py`  
**Purpose**: Generate smart contracts and templates with AI

#### Subcommands

##### `generate contract`

Generate a smart contract with AI using RAG templates for context.

**Implementation**: ```20:284:hyperkit-agent/cli/commands/generate.py```

**Options**:
- `--type, -t` - Contract type (ERC20, ERC721, DeFi, etc.)
- `--name, -n` - Contract name
- `--output, -o` - Output directory
- `--network` - Target network (default: hyperion, deprecated)
- `--template` - Use specific template
- `--use-rag/--no-use-rag` - Use RAG templates for enhanced context (default: true)

**RAG Integration**: 
- Fetches `contract-generation-prompt` template for prompt engineering
- Fetches contract-specific templates (e.g., `erc20-template`, `erc721-template`) based on type
- Uses `generation-style-prompt` for style control

**Examples**:
```bash
hyperagent generate contract --type ERC20 --name MyToken
hyperagent generate contract --type ERC721 --name MyNFT --network hyperion
```

##### `generate templates`

List available contract templates from RAG (IPFS Pinata).

**Implementation**: ```169:283:hyperkit-agent/cli/commands/generate.py```

**Options**:
- `--category, -c` - Filter templates by category

**RAG Integration**: Fetches actual templates from IPFS Pinata registry, similar to `workflow list`.

**Features**:
- Fetches templates from CID registry
- Groups templates by category
- Shows template metadata (CID, gateway URL, description, upload status)
- Displays template statistics
- Supports category filtering
- Falls back to example templates if RAG fetch fails

**Examples**:
```bash
# List all templates
hyperagent generate templates

# List templates by category
hyperagent generate templates --category contracts
hyperagent generate templates --category defi
```

##### `generate prompt`

Generate a prompt template.

**Implementation**: ```196:220:hyperkit-agent/cli/commands/generate.py```

---

### `context` Command

**File**: `hyperkit-agent/cli/main.py`  
**Purpose**: Advanced debug output & troubleshooting

**Implementation**: ```292:331:hyperkit-agent/cli/main.py```

**Options**:
- `--workflow-id` - Workflow ID to dump context for

**Functionality**:
- Dumps workflow context for troubleshooting
- Lists all available workflow contexts
- Generates diagnostic bundles

**Examples**:
```bash
# List all workflow contexts
hyperagent context

# Dump specific workflow context
hyperagent context --workflow-id abc123
```

---

## Status & Documentation Commands

### `status` Command

**File**: `hyperkit-agent/cli/main.py`  
**Purpose**: Show CLI and system status

**Implementation**: ```278:282:hyperkit-agent/cli/main.py```

**Functionality**:
- Checks system health
- Shows production mode status
- Displays configuration status

**Example**:
```bash
hyperagent status
```

---

### `doctor` Command

**File**: `hyperkit-agent/cli/commands/doctor.py`  
**Purpose**: Run environment preflight checks

**Implementation**: ```13:83:hyperkit-agent/cli/commands/doctor.py```

**Options**:
- `--no-fix` - Disable automatic fixes (report only)
- `--workspace` - Workspace directory path

**Checks**:
- Required tools (forge, python, node, npm)
- OpenZeppelin installation & version compatibility
- Foundry configuration (solc version)
- Git submodule issues
- AI/LLM configuration (Gemini primary, Alith SDK fallback)

**Auto-Fixes**:
- Installs missing OpenZeppelin contracts
- Fixes version mismatches in foundry.toml
- Cleans broken git submodule entries

**Examples**:
```bash
# Run with auto-fix (default)
hyperagent doctor

# Report only (no fixes)
hyperagent doctor --no-fix

# Custom workspace
hyperagent doctor --workspace /path/to/hyperkit-agent
```

---

### `docs` Command Group

**File**: `hyperkit-agent/cli/commands/docs.py`  
**Purpose**: Access documentation

#### Subcommands

##### `docs open`

Open documentation in browser.

**Implementation**: ```22:96:hyperkit-agent/cli/commands/docs.py```

##### `docs checkout`

Checkout documentation branch.

**Implementation**: ```97:142:hyperkit-agent/cli/commands/docs.py```

##### `docs info`

Show documentation information.

**Implementation**: ```143:150:hyperkit-agent/cli/commands/docs.py```

---

### `limitations` Command

**File**: `hyperkit-agent/cli/main.py`  
**Purpose**: Show broken features and limitations

**Implementation**: ```333:337:hyperkit-agent/cli/main.py```

**Functionality**:
- Lists all known limitations
- Shows broken features
- Provides workarounds where available

**Example**:
```bash
hyperagent limitations
```

---

### `test-rag` Command

**File**: `hyperkit-agent/cli/commands/test_rag.py`  
**Purpose**: Test IPFS Pinata RAG connections

**Implementation**: ```75:83:hyperkit-agent/cli/commands/test_rag.py```

**Functionality**:
- Tests IPFS Pinata RAG connections
- Tests content retrieval
- Displays connection status
- Shows content preview

**Note**: Obsidian RAG has been removed - IPFS Pinata is now exclusive.

**Example**:
```bash
hyperagent test-rag
```

---

### `version` Command

**File**: `hyperkit-agent/cli/main.py`  
**Purpose**: Show version information

**Implementation**: ```284:287:hyperkit-agent/cli/main.py```

**Example**:
```bash
hyperagent version
```

---

## RAG Template Integration

### Overview

HyperAgent uses **Retrieval-Augmented Generation (RAG)** with **IPFS Pinata** for decentralized template storage. All templates are stored on IPFS and fetched on-demand for enhanced AI context.

### Template Registry

**Location**: `hyperkit-agent/docs/RAG_TEMPLATES/cid-registry.json`

The registry contains metadata for all available templates:
- Template name
- Description
- Category
- IPFS CID
- Gateway URL
- Upload status
- Upload date

### Available Templates

**Total**: 13 templates across 5 categories

#### Contracts (2)
- `erc20-template` - Standard ERC20 fungible token contract template
- `erc721-template` - Standard ERC721 non-fungible token (NFT) contract template

#### DeFi (3)
- `dex-template` - Automated Market Maker (AMM) DEX with liquidity provision
- `lending-pool-template` - Collateralized lending protocol with interest rate model
- `staking-pool-template` - DeFi staking pool with rewards distribution

#### Governance (1)
- `dao-governance-template` - Complete DAO governance system with proposal creation

#### NFT (1)
- `nft-collection-template` - Advanced ERC721 NFT collection with public/whitelist minting

#### Prompts (3)
- `contract-generation-prompt` - Prompt engineering template for general smart contract creation
- `generation-style-prompt` - Prompt template for controlling style or features
- `security-prompts` - Prompt set for security-focused generation and audit scenarios

#### Audits (2)
- `security-checklist` - Comprehensive security audit best-practices checklist template
- `gas-optimization-audit` - Smart contract gas optimization audit template and checklist

#### Templates (1)
- `hardhat-deploy` - All-in-one template for Hardhat deployment scripts

### Template Fetcher

**File**: `hyperkit-agent/services/core/rag_template_fetcher.py`

**Key Methods**:
- `get_template(template_name)` - Fetch template content from IPFS
- `list_templates()` - List all available templates from registry
- `get_template_statistics()` - Get template statistics (total, uploaded, categories)
- `get_templates_by_category(category)` - Get templates by category

### Caching Strategy

Templates are cached locally to reduce IPFS gateway calls:
- Cache directory: `hyperkit-agent/data/template_cache/`
- Cache files: `{template_name}.txt`
- Cache invalidation: Manual via `clear_cache()` method

### Template Usage by Command

| Command | Templates Used | Purpose |
|---------|---------------|---------|
| `generate contract` | `contract-generation-prompt`, `{type}-template`, `generation-style-prompt` | Enhanced contract generation context |
| `deploy contract` | `hardhat-deploy` | Deployment best practices and scripts |
| `audit contract` | `security-checklist`, `gas-optimization-audit` | Comprehensive security auditing |
| `workflow run` | All relevant templates | End-to-end workflow context |

### RAG Integration Flow

1. **User Command** → Command handler receives request
2. **Template Selection** → Command determines which templates are needed
3. **RAG Fetcher** → `RAGTemplateFetcher` loads registry and fetches templates
4. **IPFS Retrieval** → Templates fetched from IPFS Pinata gateway
5. **Cache Check** → Local cache checked first (if enabled)
6. **Context Enhancement** → Templates added to AI prompt context
7. **AI Processing** → Enhanced prompt sent to AI model (Gemini/OpenAI)
8. **Result** → AI generates response with template-enhanced context

### Template Statistics

The `workflow list` command displays:
- Total templates: 13
- Uploaded templates: 13
- Categories: 5 (Contracts, DeFi, Governance, NFT, Prompts, Audits, Templates)

---

## Command Implementation Details

### Command Registration

All commands are registered in `hyperkit-agent/cli/main.py`:

```python
cli.add_command(generate_group, name='generate')
cli.add_command(deploy_group, name='deploy')
cli.add_command(audit_group, name='audit')
cli.add_command(batch_audit_group, name='batch-audit')
cli.add_command(verify_group, name='verify')
cli.add_command(monitor_group, name='monitor')
cli.add_command(config_group, name='config')
cli.add_command(workflow_group, name='workflow')
cli.add_command(docs_group, name='docs')
cli.add_command(doctor_command, name='doctor')
```

### Command Structure

Each command group follows this pattern:

```python
@click.group()
def command_group():
    """Command group description"""
    pass

@command_group.command()
@click.option('--option', help='Option description')
def subcommand(option):
    """Subcommand description"""
    # Implementation
```

### Error Handling

All commands include:
- Input validation
- Error messages with suggestions
- Graceful fallbacks
- RAG template error handling (falls back to default behavior)

### AI Model Configuration

**Primary**: Gemini (gemini-2.5-flash-lite via Alith SDK adapter)  
**Secondary**: OpenAI (via Alith SDK) if Gemini unavailable

Configured via `config llm` command.

---

## Examples & Usage Patterns

### Full Contract Lifecycle

```bash
# 1. Generate contract
hyperagent generate contract --type ERC20 --name MyToken

# 2. Audit contract
hyperagent audit contract --contract MyToken.sol

# 3. Deploy contract
hyperagent deploy contract --contract MyToken.sol

# 4. Verify contract
hyperagent verify contract --address <DEPLOYED_ADDRESS> --network hyperion
```

### Workflow Approach (Recommended)

```bash
# Single command for full lifecycle
hyperagent workflow run "create ERC20 token named MyToken" --network hyperion
```

### Batch Operations

```bash
# Batch audit multiple contracts
hyperagent batch-audit contracts -f contracts/*.sol --format all -n "Production Audit"
```

### RAG Template Testing

```bash
# Test RAG connections
hyperagent test-rag

# List available templates
hyperagent workflow list
```

### Configuration Management

```bash
# Set LLM provider
hyperagent config llm --provider gemini

# Check configuration
hyperagent config list

# Run preflight checks
hyperagent doctor
```

---

## Network Support

**Supported Networks**:
- `hyperion` (default) - Hyperion testnet (exclusive deployment target)

**Deprecated**: Other networks are no longer supported. All deployment commands default to Hyperion.

---

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Configuration error
- `3` - Network connection error
- `4` - Contract deployment error

---

## Additional Resources

- **Main Documentation**: `hyperkit-agent/docs/README.md`
- **API Reference**: `hyperkit-agent/docs/API_REFERENCE.md`
- **Contributor Guide**: `CONTRIBUTING.md`
- **Status Assessment**: `hyperkit-agent/docs/HONEST_STATUS.md`
- **RAG Templates**: `hyperkit-agent/docs/RAG_TEMPLATES/cid-registry.json`

---

**Last Updated**: 2025-01-25  
**Maintained By**: HyperAgent Development Team
