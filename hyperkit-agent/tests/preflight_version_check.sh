#!/bin/bash
# Preflight Version Check Script
# Aligned with ideal workflow best practices
# Validates Foundry and Solidity versions before workflow execution

set -e

SOLC_VERSION_EXPECTED="0.8.24"
FORGE_VERSION_EXPECTED="1.4"  # or exact version like "1.4.3"

echo "🔍 HyperKit-Agent Preflight Version Check"
echo "=========================================="

# Check Forge version
echo "Checking Foundry version..."
if ! command -v forge &> /dev/null; then
    echo "❌ ERROR: forge not found. Please install Foundry:"
    echo "   curl -L https://foundry.paradigm.xyz | bash"
    echo "   foundryup"
    exit 1
fi

FORGE_VERSION=$(forge --version | grep -oP 'forge \K[0-9]+\.[0-9]+\.[0-9]+' || forge --version | grep -oP 'Version: \K[0-9]+\.[0-9]+' || echo "unknown")
FORGE_MAJOR_MINOR=$(echo "$FORGE_VERSION" | cut -d. -f1-2)

echo "  Foundry version: $FORGE_VERSION"

# Check for nightly build (warn if in strict mode)
if echo "$FORGE_VERSION" | grep -qi "nightly"; then
    if [ "$HYPERAGENT_STRICT_FORGE" = "1" ] || [ "$HYPERAGENT_STRICT_FORGE" = "true" ]; then
        echo "❌ ERROR: Nightly build detected and strict mode enabled"
        echo "   Current: $FORGE_VERSION"
        echo "   Expected: stable version (e.g., 1.4.3)"
        echo "   Fix: Install stable version with: foundryup"
        exit 1
    else
        echo "⚠️  WARNING: Nightly build detected (may have unpredictable behavior)"
    fi
fi

# Check version matches expected
if [ "$FORGE_MAJOR_MINOR" != "$FORGE_VERSION_EXPECTED" ]; then
    if [ "$HYPERAGENT_STRICT_FORGE" = "1" ] || [ "$HYPERAGENT_STRICT_FORGE" = "true" ]; then
        echo "❌ ERROR: Foundry version mismatch"
        echo "   Current: $FORGE_VERSION"
        echo "   Expected: $FORGE_VERSION_EXPECTED.x"
        echo "   Fix: Install correct version with: foundryup --version ${FORGE_VERSION_EXPECTED}.x"
        exit 1
    else
        echo "⚠️  WARNING: Foundry version mismatch (may cause issues)"
        echo "   Current: $FORGE_VERSION"
        echo "   Expected: $FORGE_VERSION_EXPECTED.x"
    fi
fi

# Check Solidity compiler version (via forge)
echo ""
echo "Checking Solidity compiler version..."
if forge --version | grep -q "solc"; then
    SOLC_VERSION=$(forge --version | grep -oP 'solc \K[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")
    echo "  Solidity version: $SOLC_VERSION"
    
    if [ "$SOLC_VERSION" != "$SOLC_VERSION_EXPECTED" ]; then
        echo "⚠️  WARNING: Solidity version mismatch"
        echo "   Current: $SOLC_VERSION"
        echo "   Expected: $SOLC_VERSION_EXPECTED"
        echo "   Note: This is handled by foundry.toml, but ensure compatibility"
    fi
else
    echo "  Solidity version: (determined by foundry.toml)"
fi

# Check foundry.toml exists and has correct version
echo ""
echo "Checking foundry.toml configuration..."
if [ -f "foundry.toml" ]; then
    if grep -q "solc = \"$SOLC_VERSION_EXPECTED\"" foundry.toml || grep -q "solc_version = \"$SOLC_VERSION_EXPECTED\"" foundry.toml; then
        echo "✅ foundry.toml configured for Solidity $SOLC_VERSION_EXPECTED"
    else
        echo "⚠️  WARNING: foundry.toml may not specify Solidity $SOLC_VERSION_EXPECTED"
    fi
else
    echo "⚠️  WARNING: foundry.toml not found"
fi

# Check required tools
echo ""
echo "Checking required tools..."
REQUIRED_TOOLS=("forge" "python3" "python")
MISSING_TOOLS=()

for tool in "${REQUIRED_TOOLS[@]}"; do
    if command -v "$tool" &> /dev/null; then
        VERSION=$($tool --version 2>&1 | head -n1 || echo "installed")
        echo "✅ $tool: $VERSION"
    else
        echo "❌ $tool: not found"
        MISSING_TOOLS+=("$tool")
    fi
done

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    echo ""
    echo "❌ ERROR: Missing required tools: ${MISSING_TOOLS[*]}"
    echo "   Please install missing tools before running workflows"
    exit 1
fi

echo ""
echo "✅ Preflight checks passed!"
echo ""
echo "Environment summary:"
echo "  Foundry: $FORGE_VERSION"
echo "  Solidity: $SOLC_VERSION_EXPECTED (configured)"
echo "  Python: $(python3 --version 2>&1 || python --version 2>&1)"

