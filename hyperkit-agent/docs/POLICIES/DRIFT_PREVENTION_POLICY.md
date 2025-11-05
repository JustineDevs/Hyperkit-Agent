# Drift Prevention Policy

<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: 1.4.7  
**Last Verified**: 2025-11-06  
**Commit**: `2c34f8c`  
**Branch**: `main`  
<!-- AUDIT_BADGE_END -->

## Policy Overview

This policy ensures that documentation remains synchronized with code changes, preventing the accumulation of outdated guides and references.

## Core Principles

### 1. **Zero-Excuse Culture**
- Every PR that changes CLI commands or workflows MUST include documentation updates
- No exceptions for "small changes" or "internal refactoring"
- Documentation debt is treated as a blocking issue for releases

### 2. **Mandatory Documentation Review**
- All PRs must include a documentation reviewer
- Documentation changes must be reviewed by someone familiar with the user-facing impact
- Technical writers or senior developers must approve documentation changes

### 3. **Automated Enforcement**
- CI/CD pipeline automatically checks for documentation updates
- PRs are blocked if CLI changes don't include documentation updates
- Automated drift detection runs on every PR

## Enforcement Rules

### **Rule 1: CLI Changes Require Documentation Updates**
If any of these files are modified:
- `hyperkit-agent/cli/**`
- `hyperkit-agent/services/**`
- `hyperkit-agent/core/**`
- `hyperkit-agent/scripts/**`

Then at least one of these must also be modified:
- `README.md`
- `docs/CLI_COMMANDS_REFERENCE.md`
- `docs/API_REFERENCE.md`
- `docs/TROUBLESHOOTING_GUIDE.md`
- Relevant feature documentation in `docs/`

### **Rule 2: New Features Require Complete Documentation**
New features must include:
- User-facing documentation
- API documentation (if applicable)
- Troubleshooting section
- Examples and usage patterns
- Integration guides (if applicable)

### **Rule 3: Breaking Changes Require Migration Guides**
Breaking changes must include:
- Clear migration instructions
- Backward compatibility notes
- Deprecation warnings
- Timeline for removal

## Automated Checks

### **GitHub Actions Workflow**
The `.github/workflows/drift-prevention-policy.yml` workflow:

1. **Detects CLI Changes**: Scans for modifications to CLI/core files
2. **Checks Documentation Updates**: Verifies documentation was updated
3. **Runs Drift Audit**: Executes automated documentation drift detection
4. **Blocks Non-Compliant PRs**: Prevents merge if policy is violated
5. **Comments on PRs**: Provides feedback on policy compliance

### **Drift Detection**
The automated drift detection checks for:
- References to deprecated CLI commands
- Future-tense language in documentation
- Stale TODO/FIXME comments
- Outdated script references
- Missing implementation status

## Documentation Standards

### **Required Elements**
Every documentation file must include:
- Clear purpose and scope
- Prerequisites and setup instructions
- Step-by-step usage examples
- Troubleshooting section
- Related documentation links

### **Audit Badges**
All technical documentation includes audit badges:
```markdown
<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: 1.4.7  
**Last Verified**: 2025-11-06  
**Commit**: `2c34f8c`  
**Branch**: `main`  
<!-- AUDIT_BADGE_END -->
```

### **Implementation Status**
Documentation must clearly indicate:
- ✅ **Implemented**: Feature is fully functional
- ⚠️ **Partially Implemented**: Feature works with limitations
- ❌ **Not Implemented**: Feature is documented but not functional
- 🔧 **Stub Process**: Process is documented but not CLI-integrated

## Review Process

### **Documentation Review Checklist**
Reviewers must verify:
- [ ] Documentation matches actual implementation
- [ ] Examples are tested and working
- [ ] All CLI commands are documented
- [ ] Troubleshooting covers common issues
- [ ] Links are valid and up-to-date
- [ ] Implementation status is accurate

### **Reviewer Requirements**
- Must be familiar with the feature being documented
- Must test all examples and commands
- Must verify implementation status
- Must check for consistency with other documentation

## Escalation Procedures

### **Policy Violations**
1. **First Violation**: Warning comment on PR
2. **Repeated Violations**: Block PR merge
3. **Persistent Violations**: Escalate to team lead

### **Documentation Debt**
1. **Minor Debt**: Track in project backlog
2. **Major Debt**: Block release until resolved
3. **Critical Debt**: Emergency documentation sprint

## Monitoring and Metrics

### **Key Metrics**
- Documentation coverage percentage
- Time between code change and doc update
- Number of policy violations per sprint
- Documentation debt backlog size

### **Reporting**
- Weekly documentation status report
- Monthly drift prevention metrics
- Quarterly documentation debt assessment

## Exceptions

### **Emergency Fixes**
Emergency fixes may bypass documentation requirements if:
- Security vulnerability requires immediate fix
- Critical bug affects production systems
- Documentation update is scheduled within 24 hours

### **Experimental Features**
Experimental features may have minimal documentation if:
- Clearly marked as experimental
- Limited to internal use only
- Documentation planned for next release

## Training and Onboarding

### **New Team Members**
- Must complete documentation standards training
- Must review drift prevention policy
- Must understand audit badge system
- Must practice documentation review process

### **Ongoing Training**
- Monthly documentation best practices sessions
- Quarterly drift prevention policy reviews
- Annual documentation standards updates

## Tools and Automation

### **Required Tools**
- GitHub Actions for automated checks
- Documentation drift audit script
- Audit badge system
- Version synchronization system

### **Optional Tools**
- Documentation generation tools
- Link checking automation
- Spell checking integration
- Style guide enforcement

## Success Criteria

### **Short-term Goals (1-3 months)**
- 100% policy compliance rate
- Zero documentation drift violations
- Complete audit badge coverage
- Automated enforcement working

### **Long-term Goals (6-12 months)**
- Documentation debt reduced to zero
- Proactive documentation updates
- Self-service documentation tools
- Community contribution guidelines

## Contact and Support

### **Policy Questions**
- **Primary Contact**: Documentation Team Lead
- **Escalation**: Engineering Manager
- **Policy Updates**: Technical Writing Team

### **Technical Issues**
- **CI/CD Issues**: DevOps Team
- **Script Problems**: Automation Team
- **Tool Issues**: Platform Team

---

**Policy Version**: 1.0  
**Last Updated**: 2025-10-28  
**Next Review**: 2025-11-28  
**Approved By**: Engineering Leadership  

---

*This policy is enforced automatically and applies to all contributors. Questions or concerns should be raised through the appropriate channels.*
