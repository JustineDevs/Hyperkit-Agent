#!/bin/bash
# HyperKit-Agent Doctor: Production-Grade Preflight Script
# Implements hardened dependency validation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "============================================================"
echo "🔬 HyperKit-Agent Doctor: Environment Preflight"
echo "============================================================"

# Step 1: Check required tools
echo ""
echo "📋 Step 1: Checking Required Tools"

command -v forge >/dev/null || { echo "❌ forge not found. Install Foundry: foundryup"; exit 1; }
FORGE_VERSION=$(forge --version | head -n1)
echo "✅ forge: $FORGE_VERSION"

command -v python >/dev/null || command -v python3 >/dev/null || { echo "❌ python not found. Install Python>=3.8"; exit 1; }
PYTHON_VERSION=$(python --version 2>&1 || python3 --version 2>&1)
echo "✅ python: $PYTHON_VERSION"

command -v node >/dev/null || { echo "⚠️  node not found (optional for npm dependencies)"; }
if command -v node >/dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ node: $NODE_VERSION"
fi

command -v npm >/dev/null || { echo "⚠️  npm not found (optional for npm dependencies)"; }
if command -v npm >/dev/null; then
    NPM_VERSION=$(npm --version)
    echo "✅ npm: $NPM_VERSION"
fi

# Step 2: Check OpenZeppelin installation
echo ""
echo "📦 Step 2: Checking OpenZeppelin Installation"

OZ_DEST="lib/openzeppelin-contracts"
OZ_COUNTERS="$OZ_DEST/contracts/utils/Counters.sol"
OZ_ERC20="$OZ_DEST/contracts/token/ERC20/ERC20.sol"

if [ ! -d "$OZ_DEST" ] || [ ! -f "$OZ_ERC20" ]; then
    echo "❗ OpenZeppelin contracts missing. Auto-installing..."
    rm -rf "$OZ_DEST"
    
    # Try forge install first
    if forge install OpenZeppelin/openzeppelin-contracts 2>/dev/null; then
        echo "✅ OpenZeppelin installed via forge install"
    else
        echo "⚠️  forge install failed, trying direct git clone..."
        git clone --depth 1 https://github.com/OpenZeppelin/openzeppelin-contracts.git "$OZ_DEST"
        echo "✅ OpenZeppelin installed via direct clone"
    fi
    
    if [ ! -f "$OZ_ERC20" ]; then
        echo "❌ OpenZeppelin installation verification failed"
        exit 1
    fi
fi

# Check for Counters.sol (deprecated in OZ v5)
if [ ! -f "$OZ_COUNTERS" ]; then
    echo "⚠️  Counters.sol not found (deprecated in OpenZeppelin v5.x)"
    echo "💡 Contract generation will auto-remove Counters.sol usage"
    echo "✅ OpenZeppelin v5 compatible (Counters.sol auto-removed)"
else
    echo "✅ OpenZeppelin & Counters.sol present"
fi

# Step 3: Check Foundry configuration
echo ""
echo "⚙️  Step 3: Checking Foundry Configuration"

if [ ! -f "foundry.toml" ]; then
    echo "❌ foundry.toml not found"
    exit 1
fi

EXPECTED_SOLC="0.8.24"
SOLC_VERSION=$(grep -E 'solc\s*=' foundry.toml | head -n1 | sed -E 's/.*solc\s*=\s*["'\'']([^"'\'']+)["'\''].*/\1/' || echo "")

if [ -z "$SOLC_VERSION" ]; then
    SOLC_VERSION=$(grep -E 'solc_version\s*=' foundry.toml | head -n1 | sed -E 's/.*solc_version\s*=\s*["'\'']([^"'\'']+)["'\''].*/\1/' || echo "")
fi

if [ -z "$SOLC_VERSION" ]; then
    echo "⚠️  Could not detect solc version in foundry.toml"
elif [ "$SOLC_VERSION" != "$EXPECTED_SOLC" ]; then
    echo "⚠️  Solc version mismatch: found '$SOLC_VERSION', expected '$EXPECTED_SOLC'"
    echo "💡 Update foundry.toml: solc = \"$EXPECTED_SOLC\""
else
    echo "✅ Foundry config valid: solc = $SOLC_VERSION"
fi

# Step 4: Check git submodule issues
echo ""
echo "🔧 Step 4: Checking Git Submodule Configuration"

# Check root .gitmodules
if [ -f "../.gitmodules" ]; then
    if grep -q "hyperkit-agent/lib/openzeppelin-contracts" "../.gitmodules" 2>/dev/null; then
        echo "⚠️  Found broken submodule entry in root .gitmodules"
        echo "💡 Consider removing the entry or delete root .gitmodules"
    fi
fi

echo "✅ Git submodule configuration clean"

# Final summary
echo ""
echo "============================================================"
echo "✅ Preflight successful. All environment checks passed."
echo "============================================================"

