# IPFS Pinata System Documentation

## Overview

The HyperKit Agent IPFS Pinata system provides dual-scope artifact management with separate namespaces for Team (official) and Community (user-generated) artifacts.

## Architecture

### Dual-Scope System

- **Team Scope**: Official, production-vetted artifacts
  - Managed by HyperKit team
  - Requires team API keys
  - Stored in `cid-registry-team.json`
  - High trust, canonical contracts

- **Community Scope**: User-generated, experimental artifacts
  - Managed by community users
  - Can use separate API keys or shared keys
  - Stored in `cid-registry-community.json`
  - Quality-scored and moderated

### CID Registry System

Each scope maintains a separate CID registry:

```json
{
  "artifact-id": {
    "cid": "Qm...",
    "scope": "team|community",
    "artifact_type": "contract|prompt|workflow|metadata",
    "content_hash": "sha256...",
    "timestamp": "2025-01-25T10:00:00Z",
    "workflow_signature": "workflow-id-timestamp",
    "metadata": {...},
    "ipfs_url": "ipfs://Qm...",
    "gateway_url": "https://gateway.pinata.cloud/ipfs/Qm..."
  }
}
```

## Upload Classification Policy

### Team Uploads

**Criteria:**
- Official HyperKit templates and contracts
- Production-vetted and audited
- Used as canonical examples
- High quality and security standards

**Process:**
1. Upload via `--upload-scope team` flag
2. Requires `PINATA_TEAM_API_KEY` and `PINATA_TEAM_SECRET_KEY`
3. Automatically registered in team registry
4. Available in RAG queries with `official-only` scope

### Community Uploads

**Criteria:**
- User-generated contracts and artifacts
- Experimental or custom implementations
- Quality-scored and moderated
- Can be flagged/reviewed

**Process:**
1. Upload via `--upload-scope community` flag
2. Requires `PINATA_COMMUNITY_API_KEY` (or shared team keys)
3. Scanned for malicious patterns
4. Quality scored automatically
5. Registered in community registry
6. Available in RAG queries with `opt-in-community` scope

## Provenance Tracking

Each artifact includes:

- **Content Hash**: SHA-256 hash for integrity verification
- **Workflow Signature**: Links artifact to workflow run
- **Timestamp**: Upload time for freshness tracking
- **Metadata**: Type, tags, description, key-value pairs

## Usage Guidelines

### For Team Members

1. **Upload Official Artifacts:**
   ```bash
   hyperagent workflow run "Create ERC20 token" --upload-scope team
   ```

2. **Use Official-Only RAG:**
   ```bash
   hyperagent workflow run "Create contract" --rag-scope official-only
   ```

### For Community Users

1. **Upload Community Artifacts:**
   ```bash
   hyperagent workflow run "Create custom token" --upload-scope community
   ```

2. **Enable Community RAG (Opt-In):**
   ```bash
   hyperagent workflow run "Create contract" --rag-scope opt-in-community
   ```

3. **Quality Thresholds:**
   - Community artifacts require quality score >= 0.5
   - Lower quality artifacts are filtered out
   - Flagged content is sandboxed

## Contribution Process

### Contributing to Team Scope

1. Submit PR with artifact
2. Security audit required
3. Team review and approval
4. Upload to team scope
5. Added to canonical registry

### Contributing to Community Scope

1. Upload via CLI with `--upload-scope community`
2. Automatic quality scanning
3. Community moderation review
4. Upvotes/flags determine visibility
5. Quality scoring affects RAG priority

## Security & Moderation

### Content Scanning

- Automated malicious pattern detection
- Suspicious code identification
- Quality scoring
- Risk assessment

### Flagging System

- Users can flag inappropriate content
- Admin review workflow
- Automated purging for malicious content
- Reputation tracking

### Sandboxing

- Flagged content isolated from RAG queries
- Quality threshold filtering
- Reputation-based access

## RAG Fetch Logic

### Official-Only Mode (Default)

- Only Team artifacts included
- High trust, canonical contracts
- No Community content

### Opt-In-Community Mode

- Team artifacts prioritized
- Community artifacts filtered by quality (>= 0.5)
- Quality scoring determines ranking
- Flagged content excluded

### Prioritization

1. **Scope Priority**: Team > Legacy > Community
2. **Relevance Score**: Query matching
3. **Quality Score**: Compilation success, audit results, usage

## Analytics & Moderation

### Metrics Tracked

- Upload frequency
- Usage statistics
- Quality scores
- Reputation scores
- Flag counts

### Quality Factors

- Compilation success
- Audit severity
- Usage frequency
- Upvotes/flags
- Age (older = more trusted)

## Configuration

### Environment Variables

```bash
# Team Scope (Required for official uploads)
PINATA_TEAM_API_KEY=your_team_key
PINATA_TEAM_SECRET_KEY=your_team_secret

# Community Scope (Optional, defaults to team keys)
PINATA_COMMUNITY_API_KEY=your_community_key
PINATA_COMMUNITY_SECRET_KEY=your_community_secret

# Legacy Support
PINATA_API_KEY=your_key
PINATA_SECRET_KEY=your_secret
```

### Registry Locations

- Team Registry: `data/ipfs_registries/cid-registry-team.json`
- Community Registry: `data/ipfs_registries/cid-registry-community.json`
- Analytics Data: `data/analytics/community_analytics.json`
- Moderation Data: `data/moderation/flagged_content.json`

## Best Practices

1. **Team Uploads**: Use for canonical, production-ready contracts
2. **Community Uploads**: Use for experimental or custom implementations
3. **RAG Scope**: Default to `official-only` for production, `opt-in-community` for exploration
4. **Quality**: Upload well-tested, documented artifacts
5. **Security**: Review Community artifacts before production use

## Troubleshooting

### Upload Failures

- Check API keys are correctly configured
- Verify network connectivity
- Check Pinata account limits

### RAG Not Finding Artifacts

- Verify registry files exist
- Check scope settings (official-only vs opt-in-community)
- Ensure quality scores meet thresholds

### Quality Issues

- Run security audits before upload
- Ensure compilation succeeds
- Add proper documentation

