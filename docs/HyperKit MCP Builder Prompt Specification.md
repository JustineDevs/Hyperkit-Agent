# HyperAgent MCP Builder Prompt Specification - COMPLETED

**Project Status**: ✅ **PRODUCTION READY - MISSION ACCOMPLISHED**  
**Timeline**: October 21-27, 2025 (6 days)  
**Achievement**: 🏆 **100% TODO COMPLETION - ALL DELIVERABLES READY**

***

## Overview

This document specifies the prompt and tool definitions for the **HyperAgent Model Context Protocol (MCP) Builder**—empowering generative, auditable, and deployment-ready dApps and smart contracts. It is designed for integration with MCP-enabled orchestration servers, AI development platforms, and CLI workflows, following a modular, highly extensible pattern.

**Status**: All MCP specifications implemented and production-ready.

***

## Prompt Catalog

### 1. **hyperkit-generate-contract**

- **Description**: Generate a secure Solidity smart contract based on user requirements and best practices.
- **Arguments**:
    - `requirements` (string, required): High-level description of contract behavior and features.
    - `template` (string, optional): Name of desired contract template (e.g., “ERC20”, “vault”, “custom”).
    - `audit_level` (string, optional): `"basic"`, `"strict"`, or `"enterprise"`.
- **Example User Input**:
“Create an ERC20 token contract with mint, burn, pausable, and upgradeable features.”

***

### 2. **hyperkit-audit-contract**

- **Description**: Analyze any EVM smart contract by source, address, or explorer link for vulnerabilities and compliance issues.
- **Arguments**:
    - `contract_source` (string, required): Solidity/bytecode or explorer URL.
    - `network` (string, optional): Network for on-chain analysis (e.g., “mainnet”, “hyperion”, “metis”).
    - `findings_format` (string, optional): `"summary"`, `"detailed"`, `"remediation"`.
- **Example User Input**:
`contract_source: "0xabc123..."` or
`contract_source: "https://metiscan.io/address/0xabc123..."`

***

### 3. **hyperkit-scaffold-dapp**

- **Description**: Scaffold a full-stack dApp (frontend, backend, contracts) from specification.
- **Arguments**:
    - `project_name` (string, required): Human-readable project/dApp name.
    - `features` (array of string, required): e.g., `[swap, staking, governance]`
    - `frontend_stack` (string, optional): Next.js, React, Tailwind.
    - `backend_stack` (string, optional): Node.js, Express, Python, FastAPI.
    - `blockchain_network` (string, optional): Target chains (“hyperion”, “polygon”, etc.)
- **Example User Input**:
Frontend: Next.js, Backend: Node.js/Express, Features: swap, staking, multi-chain support.

***

### 4. **hyperkit-deploy-contract**

- **Description**: Deploy a verified smart contract on a selected EVM-compatible network.
- **Arguments**:
    - `source_code` (string, required): Solidity code to deploy.
    - `network` (string, required): Deployment target (“hyperion”, “metis”, “polygon”).
    - `private_key` (dotenv reference, required): Loaded from server config only, never inline.
- **Example User Input**:
`source_code: [Solidity file contents], network: "hyperion"`

***

### 5. **hyperkit-audit-log-onchain**

- **Description**: Log audit summary and findings onchain in the HyperKit audit registry.
- **Arguments**:
    - `audit_report` (object, required): Output of `hyperkit-audit-contract`.
    - `contract_address` (string, required): Target contract address.
    - `network` (string, required): Registry chain.
- **Example User Input**:
`"audit_report": {summary: ..., findings: ...}, "contract_address": "0x...", "network": "hyperion"`

***

## Response Schema (Example)

Responses follow the standardized MCP message contract:

```json
{
  "messages": [
    {
      "role": "user",
      "content": {
        "type": "text",
        "text": "Operation description & result details..."
      }
    },
    {
      "role": "system",
      "content": {
        "type": "json",
        "data": {
          "filename": "contracts/Token.sol",
          "summary": "...",
          "risks": ["reentrancy", "unchecked-call"],
          "transaction_hash": "0xdeadbeef...",
          "deployment_url": "https://hyperion-explorer.io/tx/0xdeadbeef..."
        }
      }
    }
  ],
  "isError": false
}
```

Sensitive fields (such as `private_key`) must reference the environment and never appear directly in messages.

***

## Secure Handling of Sensitive Data

**Guidelines:**

- Always reference secrets through dotenv (`os.getenv("PRIVATE_KEY")`), vault, or secure runtime config.
- Input schemas should not allow sensitive values via user or prompt input.

**Best practice:**

```python
import os
PRIVATE_KEY = os.getenv("PRIVATE_KEY")  # Do not hardcode!
```


***

## Example MCP Prompt Definitions (Python SDK)

```python
from mcp.server import Server
import mcp.types as types

PROMPTS = [
    types.Prompt(
        name="hyperkit-generate-contract",
        description="Generate a secure Solidity smart contract...",
        arguments=[
            types.PromptArgument(name="requirements", description="Contract requirements", required=True),
            types.PromptArgument(name="template", required=False),
            types.PromptArgument(name="audit_level", required=False)
        ]
    ),
    # ... repeat for all prompts above
]

app = Server("hyperkit-mcp-builder")

@app.list_prompts()
async def list_prompts():
    return PROMPTS

@app.get_prompt()
async def get_prompt(name, arguments):
    # Dynamic invocation logic for each prompt
    pass
```


***

## Testing

- **Unit tests:** For each handler and format.
- **Workflow tests:** End-to-end dApp generation, audit, deployment, and logging.
- **Security review:** Ensure dotenv-only usage for all secrets.

***

## Change Management

- Prompt additions/updates should be tracked in a `CHANGELOG.md`.
- All .env references should be documented in `README.md` and `.env.example`.

***

This HyperKit MCP Builder Prompt format is fully aligned with industry-standard MCP builder implementations and can be integrated in Node.js, Python, or any supported backend. Adjust argument lists, permission scopes, and examples to align with your team’s specific security and business rules.
<span style="display:none">[^1][^2][^3][^4][^5][^6][^7][^8]</span>

<div align="center">⁂</div>

[^1]: https://modelcontextprotocol.io/docs/develop/build-server

[^2]: https://modelcontextprotocol.io/specification/2025-06-18/server/prompts

[^3]: https://www.youtube.com/watch?v=ZoZxQwp1PiM

[^4]: https://platform.openai.com/docs/mcp

[^5]: https://modelcontextprotocol.info/docs/concepts/prompts/

[^6]: https://composio.dev/blog/how-to-effectively-use-prompts-resources-and-tools-in-mcp

[^7]: https://www.builder.io/blog/mcp-server

[^8]: https://towardsdatascience.com/model-context-protocol-mcp-tutorial-build-your-first-mcp-server-in-6-steps/

