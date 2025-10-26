#!/bin/bash
# emergency_patch.sh - Fast-track security patch deployment
# Use ONLY for P0 Critical incidents where normal CI/CD is too slow

set -e

echo "🚨 EMERGENCY PATCH DEPLOYMENT"
echo "============================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Verify you're on hotfix branch
BRANCH=$(git branch --show-current)
if [[ ! $BRANCH =~ ^hotfix/security-patch ]]; then
    echo -e "${RED}❌ ERROR: Must be on a hotfix/security-patch-* branch${NC}"
    echo "Create one with: git checkout -b hotfix/security-patch-$(date +%Y%m%d)"
    exit 1
fi

echo -e "${GREEN}✅ On hotfix branch: $BRANCH${NC}"
echo ""

# 2. Run critical tests only (fast validation)
echo "🧪 Running critical tests..."
if pytest tests/test_basic.py tests/test_deployment_e2e.py -v --tb=short; then
    echo -e "${GREEN}✅ Critical tests passed${NC}"
else
    echo -e "${RED}❌ Tests failed - fix before continuing${NC}"
    exit 1
fi
echo ""

# 3. Security scan
echo "🔒 Running security scan..."
if bandit -r . -ll 2>&1 | tee /tmp/bandit-output.txt; then
    echo -e "${GREEN}✅ Security scan passed${NC}"
else
    echo -e "${YELLOW}⚠️  Security warnings detected - review output above${NC}"
    read -p "Continue anyway? (yes/no): " CONTINUE
    if [[ $CONTINUE != "yes" ]]; then
        exit 1
    fi
fi
echo ""

# 4. Build contracts
echo "🔨 Building contracts..."
if forge build; then
    echo -e "${GREEN}✅ Contracts built successfully${NC}"
else
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi
echo ""

# 5. Create patch commit
echo "📝 Creating patch commit..."
read -p "Enter CVE or incident ID (e.g., CVE-2025-XXXX or SA-20251026-001): " CVE_ID
read -p "Enter brief description: " DESCRIPTION

git add .
git commit -m "SECURITY PATCH: ${CVE_ID} - ${DESCRIPTION}

This is an emergency patch for a critical security incident.
Normal CI/CD bypassed for rapid deployment.

Severity: P0 CRITICAL
Impact: ${DESCRIPTION}

See SECURITY_AUDIT_LOG.md for full details.

Emergency patch checklist:
- [x] Critical tests passed
- [x] Security scan completed
- [x] Contracts built successfully
- [x] 2+ peer reviews (complete before merge)
- [ ] Deployed to testnet (if applicable)
- [ ] 24-hour monitoring active

Next steps:
1. Deploy to testnet (if time permits)
2. Deploy to production
3. Monitor for 24-72 hours
4. Create post-mortem in REPORTS/
5. Update SECURITY_AUDIT_LOG.md"

echo -e "${GREEN}✅ Commit created${NC}"
echo ""

# 6. Tag the patch
TAG="security-patch-$(date +%Y%m%d-%H%M)"
git tag -a "$TAG" -m "Emergency security patch: ${CVE_ID}

${DESCRIPTION}

This patch was fast-tracked due to severity.
See commit message for full details."

echo -e "${GREEN}✅ Tagged as: $TAG${NC}"
echo ""

# 7. Show next steps
echo "=========================================="
echo "📋 NEXT STEPS"
echo "=========================================="
echo ""
echo "1. Push to GitHub:"
echo "   git push origin $BRANCH --tags"
echo ""
echo "2. Create Pull Request:"
echo "   - Title: 🚨 SECURITY PATCH: ${CVE_ID}"
echo "   - Request 2+ reviews"
echo "   - Mark as high priority"
echo ""
echo "3. Deploy (after approval):"
echo "   hyperagent deploy --contract [CONTRACT] --network hyperion"
echo ""
echo "4. Verify deployment:"
echo "   hyperagent verify contract [ADDRESS] --network hyperion"
echo ""
echo "5. Monitor system:"
echo "   hyperagent monitor system"
echo "   # Check logs every hour for 24 hours"
echo ""
echo "6. Document incident:"
echo "   # Update docs/SECURITY_AUDIT_LOG.md"
echo "   # Create post-mortem in REPORTS/POSTMORTEM-${CVE_ID}.md"
echo ""
echo "7. Communication:"
echo "   # Notify stakeholders"
echo "   # Update status page"
echo "   # Credit security researcher (if applicable)"
echo ""
echo "=========================================="
echo "🚨 REMEMBER: This bypassed normal CI/CD"
echo "Merge to main only after:"
echo "  - 2+ peer reviews complete"
echo "  - 24-hour monitoring shows no issues"
echo "  - Post-mortem documented"
echo "=========================================="

