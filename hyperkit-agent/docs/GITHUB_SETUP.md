# GitHub Repository Setup Guide

**Purpose**: Configure GitHub repository settings for production readiness  
**Last Updated**: 2025-10-26

---

## 🔒 Branch Protection Rules

### Main Branch Protection

Navigate to: **Settings → Branches → Add rule**

**Branch name pattern**: `main`

**Required Settings**:
- ☑️ Require a pull request before merging
  - ☑️ Require approvals: **2**
  - ☑️ Dismiss stale pull request approvals when new commits are pushed
  - ☑️ Require review from Code Owners
- ☑️ Require status checks to pass before merging
  - ☑️ Require branches to be up to date before merging
  - Required status checks:
    - `test (3.10)`
    - `test (3.11)`
    - `test (3.12)`
    - `lint`
    - `security-scan`
- ☑️ Require conversation resolution before merging
- ☑️ Require signed commits
- ☑️ Require linear history
- ☑️ Do not allow bypassing the above settings

---

## 🎫 Issue Templates

Create `.github/ISSUE_TEMPLATE/` with:

### 1. Bug Report (`bug_report.md`)
Already created ✅

### 2. Feature Request (`feature_request.md`)
Already created ✅

### 3. Security Vulnerability (`security_report.md`)
```yaml
name: Security Vulnerability Report
description: Report a security issue (private)
labels: ["security", "critical"]
body:
  - type: markdown
    attributes:
      value: |
        ## 🔒 Security Vulnerability Report
        
        **⚠️ DO NOT file public issues for security vulnerabilities!**
        
        Please report security issues to: security@hyperkit.dev
        Or use GitHub Security Advisories (private)
        
        For bug bounty information, see SECURITY.md
```

---

## 🔐 Security Settings

### Dependabot

Enable in: **Settings → Security → Dependabot**

- ☑️ Dependabot alerts
- ☑️ Dependabot security updates
- ☑️ Dependabot version updates

**Configuration** (`.github/dependabot.yml`):
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/hyperkit-agent"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

### Secret Scanning

Enable in: **Settings → Security → Code security**

- ☑️ Secret scanning
- ☑️ Push protection

---

## 📋 Pull Request Template

Create `.github/pull_request_template.md`:

Already created ✅

---

## 🏷️ Labels

Create standard labels in: **Issues → Labels**

**Priority**:
- `P0: Critical` (red)
- `P1: High` (orange)
- `P2: Medium` (yellow)
- `P3: Low` (green)

**Type**:
- `bug` (red)
- `feature` (blue)
- `documentation` (light blue)
- `security` (dark red)
- `enhancement` (purple)

**Status**:
- `needs-review` (yellow)
- `in-progress` (blue)
- `blocked` (red)
- `wontfix` (grey)

---

## 🤖 GitHub Actions Secrets

Add in: **Settings → Secrets and variables → Actions**

**Required Secrets**:
```
HYPERION_RPC_URL
PRIVATE_KEY (for testnet deployments)
GOOGLE_API_KEY (optional, for AI features)
OPENAI_API_KEY (optional)
ANTHROPIC_API_KEY (optional)
```

---

## 👥 Team & Permissions

### Collaborators

Add in: **Settings → Collaborators**

**Roles**:
- **Admin**: Core maintainers (2+ people)
- **Write**: Active contributors
- **Triage**: Community moderators
- **Read**: All contributors

### Code Owners

Create `.github/CODEOWNERS`:
```
# Core team reviews all changes
* @core-team

# Security-critical files require security team
/hyperkit-agent/services/security/ @security-team
/hyperkit-agent/services/deployment/ @security-team
/hyperkit-agent/services/audit/ @security-team
docs/SECURITY_AUDIT_LOG.md @security-team
docs/EMERGENCY_RESPONSE.md @security-team

# CI/CD changes require DevOps approval
/.github/workflows/ @devops-team

# Smart contracts require audit team
/hyperkit-agent/artifacts/contracts/ @audit-team
/hyperkit-agent/artifacts/templates/ @audit-team
```

---

## 📊 Project Settings

### General

- ☑️ Wikis: Disabled (use docs/)
- ☑️ Issues: Enabled
- ☑️ Discussions: Enabled (for community)
- ☑️ Projects: Enabled
- ☑️ Preserve this repository: Enabled

### Merge Button

- ☑️ Allow squash merging: **Yes** (default)
- ☐ Allow merge commits: No
- ☐ Allow rebase merging: No
- ☑️ Automatically delete head branches: Yes

---

## 🎯 Milestones

Create milestones for tracking:

1. **v4.2.0 - Q1 2025**
   - External security audit
   - Public launch
   - Bug bounty activation

2. **v4.3.0 - Q2 2025**
   - Mainnet production deployment
   - Security certification
   - Ecosystem partnerships

---

## 📝 Repository Description

Update repository description:

```
🤖 HyperAgent - AI-powered smart contract development, auditing, and deployment platform for multi-chain Ethereum networks

#ai #blockchain #ethereum #smartcontracts #security #web3 #foundry #solidity
```

---

## 🌐 GitHub Pages (Optional)

Enable in: **Settings → Pages**

- **Source**: Deploy from a branch
- **Branch**: `gh-pages` or `docs/`
- **Custom domain**: docs.hyperkit.dev

---

## ✅ Setup Checklist

### Security
- [ ] Enable branch protection on `main`
- [ ] Require 2+ reviewers for PRs
- [ ] Enable Dependabot
- [ ] Enable secret scanning
- [ ] Add repository secrets

### Collaboration
- [ ] Add CODEOWNERS file
- [ ] Create issue templates
- [ ] Create PR template
- [ ] Set up labels
- [ ] Add collaborators with appropriate roles

### CI/CD
- [ ] Verify GitHub Actions workflows
- [ ] Set up required status checks
- [ ] Configure automated deployments
- [ ] Test CI/CD pipeline

### Documentation
- [ ] Update repository description
- [ ] Enable Discussions
- [ ] Create milestones
- [ ] Link to external docs (if applicable)

---

## 🚀 Quick Setup Script

```bash
#!/bin/bash
# Setup GitHub repository settings via GitHub CLI

# Branch protection
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["test (3.10)","test (3.11)","test (3.12)","lint","security-scan"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":2,"dismiss_stale_reviews":true}' \
  --field restrictions=null

# Enable Dependabot
gh api repos/:owner/:repo/vulnerability-alerts \
  --method PUT

gh api repos/:owner/:repo/automated-security-fixes \
  --method PUT

echo "✅ GitHub repository configured for production"
```

---

## 📍 Documentation Locations

- **Current Status**: `/hyperkit-agent/REPORTS/HONEST_STATUS_ASSESSMENT.md`
- **Action Plan**: `/hyperkit-agent/REPORTS/CRITICAL_FIXES_ACTION_PLAN.md`
- **Internal Docs**: `/hyperkit-agent/Docs/` - Team, execution, integration, reference
- **Historical Archive**: `/ACCOMPLISHED/` - Timestamped milestones

---

**Last Updated**: October 27, 2025  
**Version**: 4.3.0  
**Maintained By**: HyperKit DevOps Team  
**Location**: `/hyperkit-agent/docs/GITHUB_SETUP.md`

