# HyperKit Agent - Internal Documentation
> ⚠️ **NOT IMPLEMENTED BANNER**  
> This process references scripts or procedures that are not CLI-integrated.  
> These features are documented but not executable via `hyperagent` CLI.  
> See implementation status in `REPORTS/IMPLEMENTATION_STATUS.md`.



This directory contains all internal documentation for the HyperKit Agent project, organized by category.

## Documentation Structure

### 📁 TEAM/
Team processes, coding standards, and collaboration guides.

**Key Documents:**
- Developer onboarding guides
- Coding standards
- Team coordination
- Architecture documentation

→ [Browse TEAM Documentation](./TEAM/)

### 📁 EXECUTION/
Technical runbooks, deployment guides, and operational procedures.

**Key Documents:**
- Deployment guides
- Disaster recovery procedures
- Testing evidence
- Status reports

→ [Browse EXECUTION Documentation](./EXECUTION/)

### 📁 INTEGRATION/
External service integration guides and API specifications.

**Key Documents:**
- Alith SDK integration
- LAZAI platform integration
- Wallet security extensions
- Integration code samples

→ [Browse INTEGRATION Documentation](./INTEGRATION/)

### 📁 REFERENCE/
API references, CLI documentation, and technical specifications.

**Key Documents:**
- API endpoint documentation
- CLI command reference
- Configuration options
- Error codes

→ [Browse REFERENCE Documentation](./REFERENCE/)

## Quick Links

### For New Developers
1. [Developer Guide](./TEAM/DEVELOPER_GUIDE.md)
2. [Environment Setup](./TEAM/ENVIRONMENT_SETUP.md)
3. [Team Coordination](./TEAM/TEAM_COORDINATION_GUIDE.md)

### For Operations
1. [Disaster Recovery](./EXECUTION/DISASTER_RECOVERY.md)
2. [Pre-Demo Checklist](./EXECUTION/PRE_DEMO_CHECKLIST.md)
3. [Known Limitations](./EXECUTION/KNOWN_LIMITATIONS.md)

### For Integrators
1. [Alith SDK Integration](./INTEGRATION/ALITH_SDK_INTEGRATION_ROADMAP.md)
2. [LAZAI Integration](./INTEGRATION/LAZAI_INTEGRATION_GUIDE.md)
3. [API Reference](./REFERENCE/API_REFERENCE.md)

## Other Documentation Locations

### User-Facing Documentation
- **Root `/docs/`** - High-level project documentation (README, OVERVIEW, ROADMAP)

### Status Reports
- **`/hyperkit-agent/REPORTS/`** - Current status reports and assessments

### Historical Archive
- **`/ACCOMPLISHED/`** - Timestamped milestone reports and audits

## Contributing to Documentation

When adding new documentation:

1. Determine the correct category (TEAM, EXECUTION, INTEGRATION, REFERENCE)
2. Use the appropriate naming convention:
   - ALL_CAPS for milestones/assessments
   - Title_Case for guides
   - lowercase for scripts
3. Add an entry to the relevant subdirectory README
4. Update this index if adding a new major document

## Documentation Standards

- Use Markdown format
- Include last updated date
- Add cross-references where helpful
- Keep guides concise and actionable
- Include code examples where relevant

---

**Last Updated**: October 27, 2025  
**Version**: 1.4.6  
**Maintained By**: Documentation Team
