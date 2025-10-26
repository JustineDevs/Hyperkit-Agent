#!/bin/bash
# 30-Minute New Developer Onboarding Test
# This script simulates a new developer following ONLY the README
# to set up, deploy, and verify a contract on testnet.
#
# Usage: ./test_new_developer_onboarding.sh
#
# Expected: Complete in under 30 minutes with no prior knowledge

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Timer
START_TIME=$(date +%s)

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 HyperAgent - New Developer Onboarding Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "This test simulates a new developer following ONLY the README"
echo "to set up and deploy a contract to testnet in under 30 minutes."
echo ""

# Track failures
FAILURES=()

# Function to log time elapsed
elapsed_time() {
    CURRENT=$(date +%s)
    ELAPSED=$((CURRENT - START_TIME))
    echo -e "${BLUE}[$(date +%H:%M:%S)] Elapsed: ${ELAPSED}s${NC}"
}

# Function to check command success
check_step() {
    local step_name=$1
    local command=$2
    
    echo -e "\n${YELLOW}📋 Step: ${step_name}${NC}"
    elapsed_time
    
    if eval "$command"; then
        echo -e "${GREEN}✅ ${step_name} - PASSED${NC}"
        return 0
    else
        echo -e "${RED}❌ ${step_name} - FAILED${NC}"
        FAILURES+=("$step_name")
        return 1
    fi
}

# Function to check file exists
check_file_exists() {
    local file=$1
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ Found: $file${NC}"
        return 0
    else
        echo -e "${RED}❌ Missing: $file${NC}"
        FAILURES+=("Missing file: $file")
        return 1
    fi
}

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Phase 1: Environment Prerequisites${NC}"
echo -e "${YELLOW}========================================${NC}"

# Check Python version
check_step "Python 3.10+ installed" "python --version | grep -E 'Python 3\.(1[0-9]|[2-9][0-9])'"

# Check Node.js version
check_step "Node.js 18+ installed" "node --version | grep -E 'v(1[8-9]|[2-9][0-9])'"

# Check Git
check_step "Git installed" "git --version"

# Check Foundry
check_step "Foundry installed" "forge --version"

echo -e "\n${YELLOW}========================================${NC}"
echo -e "${YELLOW}Phase 2: Project Setup${NC}"
echo -e "${YELLOW}========================================${NC}"

# Check we're in the right directory
check_file_exists "README.md"
check_file_exists "pyproject.toml"
check_file_exists "foundry.toml"

# Install Python dependencies
check_step "Install Python dependencies" "pip install -e . --quiet"

# Install Foundry dependencies (OpenZeppelin)
check_step "Install OpenZeppelin contracts" "forge install OpenZeppelin/openzeppelin-contracts --no-commit || true"

# Verify OpenZeppelin installation
check_file_exists "lib/openzeppelin-contracts/package.json"

# Build Foundry contracts
check_step "Build Foundry contracts" "forge build"

# Verify build output
check_file_exists "out/GamingToken.sol/GameToken.json"

echo -e "\n${YELLOW}========================================${NC}"
echo -e "${YELLOW}Phase 3: Environment Configuration${NC}"
echo -e "${YELLOW}========================================${NC}"

# Check .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from env.example...${NC}"
    cp env.example .env
    echo -e "${RED}❌ Please configure .env with your API keys and private key!${NC}"
    echo -e "${RED}   Required: GOOGLE_API_KEY, DEFAULT_PRIVATE_KEY, HYPERION_RPC_URL${NC}"
    FAILURES+=("Environment not configured - .env needs API keys")
else
    echo -e "${GREEN}✅ .env file exists${NC}"
    
    # Check critical environment variables (without exposing values)
    if grep -q "YOUR_.*_HERE" .env; then
        echo -e "${RED}❌ .env contains placeholder values - needs configuration${NC}"
        FAILURES+=("Environment variables not configured")
    else
        echo -e "${GREEN}✅ .env appears configured${NC}"
    fi
fi

echo -e "\n${YELLOW}========================================${NC}"
echo -e "${YELLOW}Phase 4: CLI Verification${NC}"
echo -e "${YELLOW}========================================${NC}"

# Test CLI is installed
check_step "HyperAgent CLI installed" "hyperagent --help"

# Test version command
check_step "Version command works" "hyperagent version"

# Test monitor command
check_step "System health check works" "hyperagent monitor system"

# Test limitations command
check_step "Limitations command works" "hyperagent limitations"

echo -e "\n${YELLOW}========================================${NC}"
echo -e "${YELLOW}Phase 5: Unit Tests${NC}"
echo -e "${YELLOW}========================================${NC}"

# Run pytest
check_step "Unit tests pass" "pytest tests/test_basic.py -v --tb=short"

# Run deployment E2E tests (non-integration)
check_step "Deployment E2E tests pass" "pytest tests/test_deployment_e2e.py -v -k 'not integration' --tb=short"

echo -e "\n${YELLOW}========================================${NC}"
echo -e "${YELLOW}Phase 6: Workflow Test (Dry Run)${NC}"
echo -e "${YELLOW}========================================${NC}"

# Test workflow help
check_step "Workflow help command" "hyperagent workflow --help"

# NOTE: We cannot test actual deployment without valid testnet credentials
# This would be done manually by the new developer

echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}📊 Onboarding Test Results${NC}"
echo -e "${BLUE}========================================${NC}"

# Calculate elapsed time
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))
MINUTES=$((TOTAL_TIME / 60))
SECONDS=$((TOTAL_TIME % 60))

echo ""
echo -e "${BLUE}⏱️  Total Time: ${MINUTES}m ${SECONDS}s${NC}"
echo ""

# Check if we met the 30-minute target
if [ $TOTAL_TIME -gt 1800 ]; then
    echo -e "${RED}❌ FAILED: Setup took longer than 30 minutes${NC}"
    FAILURES+=("Setup time exceeded 30 minutes")
else
    echo -e "${GREEN}✅ PASSED: Setup completed within 30 minutes${NC}"
fi

# Summary
if [ ${#FAILURES[@]} -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}🎉 ALL CHECKS PASSED!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "A new developer can successfully:"
    echo "  ✅ Set up the development environment"
    echo "  ✅ Install all dependencies"
    echo "  ✅ Build contracts with Foundry"
    echo "  ✅ Run the CLI commands"
    echo "  ✅ Execute tests"
    echo "  ✅ Complete setup in under 30 minutes"
    echo ""
    echo "Next steps for the developer:"
    echo "  1. Configure .env with real API keys and testnet private key"
    echo "  2. Run: hyperagent workflow run \"Create ERC20 token\" --network hyperion"
    echo "  3. Verify deployment on Hyperion explorer"
    echo ""
    exit 0
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}❌ ${#FAILURES[@]} CHECKS FAILED${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "Failed steps:"
    for failure in "${FAILURES[@]}"; do
        echo -e "${RED}  ❌ $failure${NC}"
    done
    echo ""
    echo "README gaps to fix:"
    echo "  - Document missing prerequisites"
    echo "  - Add troubleshooting section"
    echo "  - Clarify setup steps that failed"
    echo "  - Add screenshots/examples"
    echo ""
    exit 1
fi

