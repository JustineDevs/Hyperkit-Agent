#!/bin/bash
# Universal Dependency Install Script for HyperKit-Agent
# Aligned with ideal workflow best practices
# Run in your foundry repo root (hyperkit-agent/)

set -e  # Fail on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📦 HyperKit-Agent Dependency Installation"
echo "=========================================="

# Clean submodules if necessary (fixes broken git submodule issues)
echo "🧹 Cleaning old submodule references..."
rm -rf lib/openzeppelin-contracts
rm -rf .git/modules/lib/openzeppelin-contracts
rm -f .gitmodules

# Ensure lib directory exists
mkdir -p lib

# Install OpenZeppelin with Forge
echo "📥 Installing OpenZeppelin contracts..."
if forge install OpenZeppelin/openzeppelin-contracts; then
    echo "✅ OpenZeppelin installed successfully"
else
    echo "⚠️  Forge install failed, trying direct git clone..."
    # Fallback: direct git clone
    if [ -d "lib/openzeppelin-contracts" ]; then
        rm -rf lib/openzeppelin-contracts
    fi
    git clone https://github.com/OpenZeppelin/openzeppelin-contracts.git lib/openzeppelin-contracts
    echo "✅ OpenZeppelin installed via direct clone"
fi

# Verify installation
if [ -f "lib/openzeppelin-contracts/contracts/token/ERC20/ERC20.sol" ]; then
    echo "✅ Verified: OpenZeppelin contracts are installed"
else
    echo "❌ ERROR: OpenZeppelin installation verification failed"
    exit 1
fi

# Optional: Check for npm/python (only needed if contracts use them)
echo ""
echo "🔍 Checking optional tools..."

if command -v npm &> /dev/null; then
    echo "✅ npm found: $(npm --version)"
else
    echo "⚠️  npm not found (optional - only needed if contracts use npm/Node.js dependencies)"
fi

if command -v python3 &> /dev/null; then
    echo "✅ python3 found: $(python3 --version)"
elif command -v python &> /dev/null; then
    echo "✅ python found: $(python --version)"
else
    echo "⚠️  Python not found (optional - only needed for Python tooling)"
fi

echo ""
echo "✅ Dependency installation complete!"
echo ""
echo "Next steps:"
echo "  1. Verify: ls lib/openzeppelin-contracts/contracts/token/ERC20/ERC20.sol"
echo "  2. Test: forge build"
echo "  3. Run workflow: hyperagent workflow run \"create ERC20 token\""

