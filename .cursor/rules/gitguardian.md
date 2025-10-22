# Cursor IDE Rules - GitGuardian Security Best Practices

## Security Foundation: Secrets Management & API Security

This configuration enforces cybersecurity best practices based on GitGuardian's security standards for secrets detection, API security, and secure development workflows.

---

## 🔐 Core Security Principles

### 1. NEVER Store Secrets in Code
- **DO NOT** hardcode API keys, passwords, tokens, certificates, database credentials, or any sensitive data directly in source code
- **DO NOT** commit unencrypted secrets to Git repositories (public or private)
- **DO NOT** store secrets in configuration files that are tracked by version control
- **DO NOT** include secrets in code comments, documentation, or commit messages

### 2. Use Environment Variables & Secrets Management
- **DO** use environment variables to store sensitive configuration
- **DO** use secrets management tools (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault, Google Secret Manager)
- **DO** load secrets at runtime from secure stores
- **DO** use `.env` files for local development (ensure they are gitignored)
- **DO** encrypt secrets when storing them in repositories (use tools like git-secret or SOPS)

### 3. Git Security Practices
- **DO** add sensitive files to `.gitignore` BEFORE the first commit
- **DO** use specific file paths in `git add` commands instead of `git add *` or `git add .`
- **DO** regularly review `git status` before committing
- **DO** clear Git cache after adding files to `.gitignore`: `git rm . -r --cached`
- **DO NOT** assume private repositories are safe for storing secrets

---

## 📋 .gitignore Requirements

### Must Always Include:
```gitignore
# Environment variables and secrets
.env
.env.*
.env.local
.env.development
.env.production
.env.staging
secrets.yml
config/secrets.yml

# API keys and credentials
**/secrets/
**/credentials/
*.pem
*.key
*.p12
*.pfx
*.cer
*.crt
id_rsa*
*.ppk

# Cloud provider credentials
.aws/credentials
.gcp/credentials.json
.azure/credentials

# Database files
*.db
*.sqlite
*.sqlite3

# Configuration with potential secrets
config.local.js
config.local.json
settings.local.py
appsettings.Development.json

# IDE and editor files with potential secrets
.vscode/settings.json
.idea/
*.swp
*.swo

# Logs (may contain sensitive data)
*.log
logs/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build artifacts
dist/
build/
target/
out/

# Package manager
node_modules/
vendor/
```

---

## ✅ DO: Secure Development Practices

### Code & Configuration
- **DO** use tokenization to replace sensitive information with secure tokens
- **DO** implement Role-Based Access Control (RBAC) for secrets access
- **DO** apply the Principle of Least Privilege (PoLP) - grant minimum necessary permissions
- **DO** use short-lived secrets and tokens when possible
- **DO** whitelist IP addresses for API access where appropriate
- **DO** default to minimal permission scope for APIs

### Version Control
- **DO** implement pre-commit hooks to scan for secrets before commits
- **DO** run secrets scanning in CI/CD pipelines as a final defense
- **DO** use GitHub/GitLab security features for automated secret detection
- **DO** review code changes before merging, using security checklists
- **DO** audit Git history regularly for previously committed secrets

### Secret Rotation & Management
- **DO** rotate secrets immediately when exposure is suspected
- **DO** automate secret rotation at defined intervals
- **DO** invalidate old secrets after rotation
- **DO** maintain audit logs of secret access (who accessed which secret and when)
- **DO** track secret lifecycle in a centralized inventory

### Monitoring & Detection
- **DO** enable real-time alerting for secret detection (Slack, Discord, JIRA, webhooks)
- **DO** use automated scanning tools (GitGuardian, TruffleHog, Gitleaks, detect-secrets)
- **DO** scan multiple locations: code, commit history, comments, logs, documentation
- **DO** verify validity of detected secrets with non-intrusive API calls
- **DO** implement GitGuardian Honeytoken or similar decoy secrets to detect unauthorized access

---

## ❌ DO NOT: Security Anti-Patterns

### Dangerous Practices
- **DO NOT** use `git add *` or `git add .` blindly - always review what you're staging
- **DO NOT** share secrets via unencrypted messaging (Slack, Discord, email)
- **DO NOT** store secrets in plaintext in databases or file systems
- **DO NOT** rely solely on code reviews to discover secrets
- **DO NOT** commit debugging code that contains test credentials to production branches
- **DO NOT** expose secrets in log outputs or error messages
- **DO NOT** include secrets in API responses or client-side code
- **DO NOT** disable or bypass security checks without documented approval

### Configuration Mistakes
- **DO NOT** commit `.env` files to version control
- **DO NOT** put production secrets in staging or development environments
- **DO NOT** hardcode database connection strings with credentials
- **DO NOT** store encryption keys alongside encrypted data
- **DO NOT** use default or example secrets in production

---

## 🧪 Special Rule: Test Data & Development Secrets

### For Test/Mock Data ONLY:
When the exposed information is **explicitly test data, mock credentials, or example values**:

- **DO NOT** trigger removal or updates if the file clearly indicates test/demo purposes
- **ALLOWED** patterns for test files:
  - Files in `test/`, `tests/`, `__tests__/`, `spec/` directories
  - Files named `*.test.*`, `*.spec.*`, `*.mock.*`, `*.example.*`
  - Files with clear comments indicating test/demo data: `# TEST DATA ONLY`, `// MOCK CREDENTIALS`
  - Configuration templates: `.env.example`, `secrets.yml.template`, `config.example.json`
  - README examples with placeholder values like `YOUR_API_KEY_HERE`, `REPLACE_ME`, `EXAMPLE_VALUE`

- **STILL ENFORCE** security checks on:
  - Any file without explicit test/mock indicators
  - Production configuration files (even in test directories)
  - Files in `src/`, `lib/`, `app/`, `config/` (unless explicitly marked as examples)
  - Any credential that appears to be valid/real (not obviously fake)

### Validation Criteria for Test Data:
```javascript
// ✅ ALLOWED - Clearly test data
const MOCK_API_KEY = "test_1234567890_mock_key";
const TEST_PASSWORD = "password123"; // For testing only

// ✅ ALLOWED - Template/Example
API_KEY=your_api_key_here  // .env.example file

// ❌ NOT ALLOWED - Looks real, trigger security check
const API_KEY = "sk_live_51HyP3jK..."; // Real Stripe key pattern

// ❌ NOT ALLOWED - No test indicator
const PASSWORD = "MySecretPassword123";
```

---

## 🔍 Automated Detection Integration

### Pre-Commit Hook Setup
Install and configure secrets scanning before commits:

```bash
# Using GitGuardian ggshield
pip install ggshield
ggshield install -m local

# Using detect-secrets
pip install detect-secrets
detect-secrets scan > .secrets.baseline
```

### Required Pre-Commit Configuration (`.pre-commit-config.yaml`):
```yaml
repos:
  - repo: local
    hooks:
      - id: detect-secrets
        name: Detect Secrets
        entry: detect-secrets-hook
        language: python
        args: ['--baseline', '.secrets.baseline']
      
      - id: gitguardian
        name: GitGuardian Scan
        entry: ggshield secret scan pre-commit
        language: system
        pass_filenames: false
```

### CI/CD Integration (GitHub Actions example):
```yaml
name: Security Scan
on: [push, pull_request]

jobs:
  secret-detection:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: GitGuardian Scan
        uses: GitGuardian/gg-shield-action@master
        env:
          GITGUARDIAN_API_KEY: ${{ secrets.GITGUARDIAN_API_KEY }}
```

---

## 🚨 Incident Response: If Secrets Are Exposed

### Immediate Actions:
1. **REVOKE** the exposed secret immediately (even if unsure of compromise)
2. **ROTATE** to a new secret value to invalidate the old one
3. **REMOVE** the secret from Git history using `git filter-branch` or BFG Repo-Cleaner
4. **AUDIT** access logs to check for unauthorized usage
5. **NOTIFY** security team and stakeholders
6. **DOCUMENT** the incident for future prevention

### Removal from Git History:
```bash
# Using BFG Repo-Cleaner (recommended)
bfg --replace-text passwords.txt repo.git

# Using git filter-branch (if BFG not available)
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch path/to/secret/file' \
  --prune-empty --tag-name-filter cat -- --all
```

---

## 📊 Security Checklist for Code Review

Before approving any pull request:

- [ ] No hardcoded API keys, passwords, tokens, or credentials
- [ ] All sensitive configuration uses environment variables
- [ ] `.gitignore` includes all necessary secret file patterns
- [ ] No secrets in comments, documentation, or commit messages
- [ ] Pre-commit hooks passed without being bypassed
- [ ] CI/CD security scans completed successfully
- [ ] No new `.env` files committed (only `.env.example` allowed)
- [ ] Database connection strings don't contain credentials
- [ ] API calls use properly secured authentication
- [ ] Logging doesn't expose sensitive information

---

## 🎯 Context-Aware Rules

### When Editing Specific File Types:

**JavaScript/TypeScript:**
- Never use `process.env.API_KEY` directly in client-side code
- Always validate environment variables are loaded server-side
- Use proxy endpoints to hide API keys from frontend

**Python:**
- Use `python-dotenv` for environment variable management
- Never commit `settings.py` with production credentials
- Use `settings.local.py` for local overrides (gitignored)

**Java:**
- Never hardcode credentials in `application.properties` or `application.yml`
- Use `application-local.properties` for development (gitignored)
- Implement Spring Cloud Config or similar for secret management

**Docker:**
- Use Docker secrets or environment variables, never hardcode in Dockerfile
- Don't commit `.env` files used by docker-compose
- Use build arguments only for non-sensitive data

**Infrastructure as Code (Terraform, CloudFormation):**
- Never commit state files containing secrets
- Use variable files (`.tfvars`) that are gitignored
- Use secrets managers for sensitive outputs

---

## 🔄 Continuous Improvement

- **Regularly update** this rules file as new threats emerge
- **Train team members** on secrets management best practices
- **Audit security posture** quarterly with comprehensive repository scans
- **Review and improve** incident response procedures based on learnings
- **Stay informed** about new GitGuardian features and security updates

---

## 📚 Additional Resources

- [GitGuardian Secrets Security Guide](https://www.gitguardian.com/secrets-management-guide)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [GitGuardian API Security Best Practices](https://blog.gitguardian.com/secrets-api-management/)
- [GitGuardian ggshield CLI Documentation](https://docs.gitguardian.com/ggshield-docs/)

---

## 💡 Quick Reference Commands

```bash
# Scan for secrets before commit
ggshield secret scan pre-commit

# Scan specific files
ggshield secret scan path/to/file

# Scan entire repository history
ggshield secret scan repo .

# Create secrets baseline
detect-secrets scan > .secrets.baseline

# Audit secrets baseline
detect-secrets audit .secrets.baseline

# Clear git cache
git rm . -r --cached

# Check what will be committed
git status
git diff --staged
```

---

**Remember:** A single leaked credential can lead to catastrophic security incidents. When in doubt, treat it as a secret and protect it accordingly. Security is not optional—it's a requirement.