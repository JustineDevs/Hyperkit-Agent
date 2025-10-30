<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: 1.5.7  
**Last Verified**: 2025-10-29  
**Commit**: `aac4687`  
**Branch**: `main`  
<!-- AUDIT_BADGE_END -->

# Generated Files Documentation

## Overview

The HyperKit AI Agent generates various files during its operation. This document describes where these files are stored and how to manage them.

## Generated File Locations

### 1. Smart Contracts

**Organized File Structure**: All generated files are now saved to organized artifact directories based on command type and category.

**Workflow Command**: Contracts saved to `artifacts/workflows/{category}/`
**Generate Command**: Contracts saved to `artifacts/generate/{category}/`
**Audit Command**: Reports saved to `artifacts/audit/`
**Deploy Command**: Deployment info saved to `artifacts/deploy/{category}/`
**Verify Command**: Verification results saved to `artifacts/verify/{category}/`

**Categories**: `tokens`, `defi`, `gaming`, `nft`, `governance`, `bridge`, `launchpad`, `other`

```bash
# Workflow command files (organized by category)
hyperkit-agent/artifacts/workflows/
├── tokens/
│   └── ERC20Token.sol
├── defi/
│   ├── StakingContract.sol
│   └── DEX.sol
├── gaming/
│   └── GamingToken.sol
├── nft/
│   └── NFTMarketplace.sol
├── governance/
│   └── DAO.sol
└── ...

# Generate command files
hyperkit-agent/artifacts/generate/
├── tokens/
│   └── MyToken.sol
├── defi/
│   └── StakingPool.sol
└── ...

# ALSO saved to foundry contracts/ for compilation
hyperkit-agent/contracts/
├── MultiSigWallet.sol  # From workflow
├── GamingToken.sol
└── ...
```

**File Naming**:
- Contract name extracted from generated code
- Automatically categorized based on contract content
- Saved to both organized location AND foundry directory for compilation

### 2. Audit Reports

**Default Location**: `./reports/`
**CLI Option**: `--report` parameter

```bash
# Generate audit report
python cli.py audit contract.sol --report ./reports/audit_report.json
```

**Report Types**:
- JSON format for machine processing
- Markdown format for human reading
- PDF format for official documentation

### 3. Deployment Artifacts

**Default Location**: `./deployments/`
**Network-specific subdirectories**

```bash
./deployments/
├── hyperion/
│   ├── contract_addresses.json
│   ├── deployment_logs.json
│   └── verification_results.json
└── andromeda/
    └── ...
```

### 4. Monitoring Data

**Default Location**: `./monitoring/`
**Real-time monitoring outputs**

```bash
./monitoring/
├── gas_analytics.json
├── transaction_logs.json
├── performance_metrics.json
└── alerts.json
```

### 5. RAG Knowledge Base

**Default Location**: `./data/`
**Knowledge base storage**

```bash
./data/
├── vectordb/          # Vector database (if using ChromaDB)
├── patterns/          # DeFi patterns cache
└── knowledge/         # Cached knowledge base
```

## File Management

### Automatic Cleanup

The agent includes automatic cleanup mechanisms:

```python
# Cleanup old generated files (older than 30 days)
python cli.py cleanup --older-than 30

# Cleanup specific file types
python cli.py cleanup --type contracts --older-than 7
```

### File Organization

**By Date**:
```bash
./contracts/2025-01-22/
├── ERC20Token_001.sol
├── StakingContract_002.sol
└── ...
```

**By Type**:
```bash
./generated/
├── contracts/
├── audits/
├── deployments/
└── monitoring/
```

**By Project**:
```bash
./projects/my-defi-project/
├── contracts/
├── audits/
├── deployments/
└── README.md
```

## Configuration

### Environment Variables

```bash
# Default output directories
CONTRACTS_OUTPUT_DIR=./contracts
AUDIT_REPORTS_DIR=./reports
DEPLOYMENTS_DIR=./deployments
MONITORING_DIR=./monitoring

# File retention settings
FILE_RETENTION_DAYS=30
AUTO_CLEANUP_ENABLED=true
```

### CLI Configuration

```bash
# Set default output directory
python cli.py config set --output-dir ./my-contracts/

# Set file retention policy
python cli.py config set --retention-days 60

# Enable auto-cleanup
python cli.py config set --auto-cleanup true
```

## Best Practices

### 1. File Naming

- Use descriptive names: `ERC20Token.sol` not `contract1.sol`
- Include version numbers: `StakingContract_v2.sol`
- Add timestamps for tracking: `VaultContract_20250122.sol`

### 2. Directory Structure

- Organize by project or date
- Use consistent naming conventions
- Keep related files together

### 3. Version Control

- Add generated files to `.gitignore` if not needed in repo
- Use separate branches for generated content
- Tag important versions

### 4. Backup Strategy

- Regular backups of important generated files
- Cloud storage for critical contracts
- Version control for audit reports

## Troubleshooting

### Common Issues

**1. Permission Errors**
```bash
# Fix directory permissions
chmod 755 ./contracts/
chmod 755 ./reports/
```

**2. Disk Space**
```bash
# Check disk usage
python cli.py status --disk-usage

# Cleanup old files
python cli.py cleanup --force
```

**3. File Conflicts**
```bash
# Use unique naming
python cli.py generate "ERC20 token" --output-dir ./contracts/ --unique-name

# Overwrite existing files
python cli.py generate "ERC20 token" --overwrite
```

## Integration with IDEs

### VS Code

Add to `.vscode/settings.json`:
```json
{
    "files.associations": {
        "*.sol": "solidity"
    },
    "solidity.defaultCompiler": "remote"
}
```

### IntelliJ IDEA

Configure Solidity plugin to recognize generated files in `./contracts/` directory.

## Monitoring Generated Files

### File Statistics

```bash
# Get file statistics
python cli.py stats --files

# Monitor file growth
python cli.py monitor --files --interval 60
```

### Automated Alerts

```bash
# Alert when disk usage > 80%
python cli.py monitor --disk-threshold 80

# Alert when file count > 1000
python cli.py monitor --file-count-threshold 1000
```

This documentation ensures proper management of all generated files in the HyperKit AI Agent system.
