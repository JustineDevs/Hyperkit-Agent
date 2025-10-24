#!/bin/bash

# HyperKit AI Agent - Installation Script
# Automated setup for smart contract generation, auditing, and deployment

set -e

echo "🚀 HyperKit AI Agent - Installation Script"
echo "=========================================="

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python $python_version detected (>= $required_version required)"
else
    echo "❌ Python $required_version or higher required. Found: $python_version"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p artifacts/contracts/{tokens,gaming,defi,nft,governance,bridge,launchpad,other}/generated
mkdir -p artifacts/audits
mkdir -p artifacts/deployments
mkdir -p artifacts/verification
mkdir -p contracts/generated
mkdir -p contracts/deployed
mkdir -p logs
mkdir -p cache

echo "✅ Directory structure created"

# Copy environment file
echo "⚙️  Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp env.example .env
    echo "✅ Environment file created (.env)"
    echo "⚠️  Please edit .env file with your API keys"
else
    echo "✅ Environment file already exists"
fi

# Install Foundry (for Solidity compilation)
echo "🔨 Installing Foundry (Solidity compiler)..."
if ! command -v forge &> /dev/null; then
    curl -L https://foundry.paradigm.xyz | bash
    source ~/.bashrc
    foundryup
    echo "✅ Foundry installed"
else
    echo "✅ Foundry already installed"
fi

# Install pre-commit hooks (optional)
echo "🪝 Setting up pre-commit hooks..."
if command -v pre-commit &> /dev/null; then
    pre-commit install
    echo "✅ Pre-commit hooks installed"
else
    echo "⚠️  Pre-commit not available (optional)"
fi

# Test installation
echo "🧪 Testing installation..."
python3 -c "
try:
    from core.agent.main import HyperKitAgent
    from services.generation.contract_namer import ContractNamer
    from core.config.paths import PathManager
    print('✅ Core modules imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

# Final setup
echo "🎉 Installation completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Test the installation: hyperagent status"
echo "4. Generate your first contract: hyperagent generate 'Create an ERC20 token'"
echo ""
echo "🔗 Useful commands:"
echo "  hyperagent status          - Check system status"
echo "  hyperagent generate        - Generate smart contracts"
echo "  hyperagent audit           - Audit contracts"
echo "  hyperagent deploy          - Deploy contracts"
echo "  hyperagent workflow        - Complete workflow"
echo ""
echo "📚 Documentation: https://docs.hyperkit.ai"
echo "🐛 Issues: https://github.com/hyperkit-ai/hyperkit-agent/issues"
