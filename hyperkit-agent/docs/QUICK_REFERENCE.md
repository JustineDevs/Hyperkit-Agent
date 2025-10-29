<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: 1.4.6  
**Last Verified**: 2025-10-28  
**Commit**: `d5465090`  
**Branch**: `main`  
<!-- AUDIT_BADGE_END -->

# HyperKit Agent Quick Reference

One-page command reference for common operations.

---

## Installation

```bash
# Clone repository
git clone https://github.com/YOUR_REPO/Hyperkit-Agent.git
cd Hyperkit-Agent/hyperkit-agent

# Install dependencies
pip install -r requirements.txt

# Optional: Install IPFS features
pip install -r requirements.txt
```

---

## Contract Deployment

```bash
# Auto-detect constructor args
hyperagent deploy contract MyToken.sol

# Provide args explicitly
hyperagent deploy contract MyToken.sol --args '["0x742d35Cc...", 1000000]'

# Use JSON file
hyperagent deploy contract MyToken.sol --file args.json

# Deploy to specific network
hyperagent deploy contract MyToken.sol --network hyperion-testnet
```

---

## Contract Auditing

```bash
# Audit single contract
hyperagent audit contract MyToken.sol

# Batch audit directory
hyperagent batch-audit directory contracts/ --format html --format pdf

# Batch audit specific files
hyperagent batch-audit files contract1.sol contract2.sol --output ./reports

# Export formats: json, html, markdown, csv, pdf, excel
```

---

## Template System

```bash
# List templates
hyperagent template list

# Show template details
hyperagent template show ERC20

# Generate from template
hyperagent template generate ERC20 MyToken.sol \
  -v token_name=MyToken \
  -v token_symbol=MTK \
  -v initial_supply=1000000

# Use variables file
hyperagent template generate ERC20 MyToken.sol --vars-file vars.json

# Create custom template
hyperagent template create MyTemplate template.sol -d "Description" -c tokens
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_deployer.py -v

# Run with coverage
pytest tests/ --cov=core --cov=services

# Run specific test
pytest tests/test_deployer.py::test_deploy_success -v
```

---

## Code Quality

```bash
# Format code
black core/ services/

# Check formatting
black --check core/ services/

# Lint code
flake8 core/ services/

# Sort imports
isort core/ services/

# Security scan
bandit -r core/ services/
```

---

## Common Error Fixes

```bash
# Module not found
pip install -r requirements.txt

# Foundry not found
curl -L https://foundry.paradigm.xyz | bash; foundryup

# Constructor validation failed
# Use --args or --file

# CI/CD fails
# Check .github/workflows/ci-cd.yml
# Run tests locally first: pytest tests/ -v
```

---

## Environment Variables

```bash
# Copy example
cp env.example .env

# Required variables
OPENAI_API_KEY=your_key
GOOGLE_API_KEY=your_key
ANTHROPIC_API_KEY=your_key

# Optional for IPFS
PINATA_API_KEY=your_key
PINATA_SECRET_KEY=your_secret

# Network RPCs
HYPERION_RPC_URL=https://hyperion-testnet.metisdevops.link
```

---

## Git Workflow

```bash
# Update to latest
git pull origin main

# Create feature branch
git checkout -b feature/my-feature

# Commit changes
git add .
git commit -m "feat: description"

# Push and create PR
git push origin feature/my-feature
```

---

## Troubleshooting

| Issue | Quick Fix |
|-------|-----------|
| Can't import module | `pip install -r requirements.txt` |
| Foundry not found | `curl -L https://foundry.paradigm.xyz \| bash` |
| Constructor error | Use `--file args.json` |
| CI/CD fails | Run `pytest tests/ -v` locally |
| Mock mode detected | Remove `MOCK_MODE = True` |

---

**Full Documentation**: [docs/TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md)  
**Video Tutorials**: (Coming soon)  
**Support**: support@hyperkit.ai

