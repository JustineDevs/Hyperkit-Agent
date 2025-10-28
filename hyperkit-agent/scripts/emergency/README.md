# Emergency Scripts

Scripts for critical incident response and hotfix deployment.

## ⚠️ WARNING

**These scripts bypass normal CI/CD and should be used ONLY for P0 critical security incidents.**

## Scripts

| Script | Purpose | Arguments |
|--------|---------|-----------|
| `emergency_patch.sh` | Fast-track security patch deployment | - |
| `debug_deployment_error.py` | Debug deployment failures | `--error ERROR_ID` |

## Usage

### Emergency Security Patch
```bash
# Switch to hotfix branch
git checkout -b hotfix/security-patch-$(date +%Y%m%d)

# Run emergency patch script
bash emergency_patch.sh
```

### Debug Deployment Issues
```bash
python debug_deployment_error.py --error E123
```

## Requirements

### Emergency Patch
- Must be on `hotfix/security-patch-*` branch
- Requires CVE or incident ID
- Requires security approval
- Bypasses normal CI/CD

### Debug Script
- Requires error logs
- May need network access
- May generate debug artifacts

## Safety

- ⚠️ **Only use for P0 critical incidents**
- ⚠️ **Requires security team approval**
- ⚠️ **Bypasses normal safety checks**
- ⚠️ **Creates tags and commits automatically**
- ⚠️ **May deploy directly to production**

## Post-Incident

After using these scripts:
1. Document in `docs/SECURITY_AUDIT_LOG.md`
2. Create post-mortem in `REPORTS/`
3. Update incident tracking
4. Schedule retrospective

## Owner

HyperAgent Security Team
