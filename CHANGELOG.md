# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

⚠️ **SOURCE OF TRUTH**: This file is the canonical changelog for the entire HyperAgent project.  
All version bumps, releases, and changes are documented here.

---

## [1.5.0] - 2025-10-28

### 🚀 Major System Refactor - Production Alignment

#### **Critical Changes**
- **AI Agent**: Alith SDK is now the ONLY AI agent (LazAI AI agent completely removed)
  - LazAI is network-only (blockchain RPC endpoint), NOT an AI service
  - Alith SDK uses OpenAI API key (not LazAI key)
  - HARD FAIL if Alith SDK not configured (NO fallback - Alith SDK ONLY)
  - Clear error messages distinguishing network vs AI agent functionality

- **RAG System**: IPFS Pinata is now the exclusive RAG backend
  - Obsidian RAG integration completely removed
  - MCP/Obsidian references marked as deprecated
  - All RAG operations use IPFS Pinata via CID registry
  - System fails hard if Pinata not configured (no mock fallbacks)

- **Configuration**: Comprehensive validation on startup
  - Config validation runs automatically on ConfigManager initialization
  - Critical config errors logged and optionally abort startup
  - Proper chain ID corrections (Hyperion: 133717, LazAI: 9001)
  - Deprecated config keys (MCP/Obsidian) trigger warnings

#### **Network Configuration - HYPERION-ONLY MODE**
- **CRITICAL**: Hyperion is now the EXCLUSIVE deployment target
  - `hyperion`: Chain ID 133717 (testnet) - ONLY supported network
  - LazAI and Metis networks REMOVED from all configs and code
  - Future network support documented in ROADMAP.md only (no code stubs)
  - All CLI commands hardcoded to Hyperion (--network flag hidden/deprecated)
  - Config validation FAILS HARD on non-Hyperion network configs

#### **Removed/Deprecated**
- **REMOVED**: All LazAI and Metis network configurations (Hyperion-only mode)
- **REMOVED**: All Docker/MCP containerization (Dockerfile.mcp, docker-compose.yml deleted)
- **REMOVED**: All LazAI AI agent code (LazAI is network-only, NOT an AI service)
- **REMOVED**: All fallback LLM code from agent (Alith SDK ONLY - hard fail if unavailable)
- **REMOVED**: Obsidian/MCP RAG integrations completely (IPFS Pinata exclusive)
- **REMOVED**: Mock storage/retrieval fallbacks (system fails hard instead)
- **DEPRECATED**: --network CLI flag (hidden, all commands use Hyperion)

#### **Documentation Updates**
- README.md: Updated with correct AI agent information (Alith SDK only)
- env.example: Clarified LazAI is network-only, Alith SDK requires OpenAI key
- config.yaml: Fixed chain IDs for Hyperion and LazAI networks
- requirements.txt: Updated comments about Alith SDK and deprecated MCP

#### **Breaking Changes**
⚠️ **Migration Required**:
- If using LazAI for AI: Switch to Alith SDK (requires OpenAI API key)
- If using Obsidian RAG: Migrate to IPFS Pinata (requires PINATA_API_KEY + PINATA_SECRET_KEY)
- Obsidian config keys in `.env` will trigger deprecation warnings

#### **Technical Improvements**
- Startup config validation prevents runtime errors
- Unified error handling across services
- Better error messages with actionable suggestions
- Network validation ensures only supported networks are used

---

## [4.3.1] - 2025-10-28

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-28
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v4.3.1

---
## [4.3.0] - 2025-10-27

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-27
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v4.3.0

---
## [4.2.0] - 2025-10-27

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-27
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v4.2.0

---
## [4.1.10] - 2025-10-27

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-27
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v4.1.10

---
## [4.1.9] - 2025-10-26

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-26
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v4.1.9

---
## [4.1.8] - 2025-10-26

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-26
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v4.1.8

---
## [4.1.7] - 2025-10-26

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-26
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v4.1.7

---
## [4.1.6] - 2025-10-26

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-26
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v4.1.6

---
## [4.1.5] - 2025-10-26

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-26
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v4.1.5

---
## [4.1.4] - 2025-10-26

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-26
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v4.1.4

---
## [4.1.3] - 2025-10-26

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-26
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v4.1.3

---
## [4.1.2] - 2025-10-26

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-26
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v4.1.2

---
## [4.1.1] - 2025-10-26

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-26
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v4.1.1

---
## [4.1.0] - 2025-10-25

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-25
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v4.1.0

---
## [4.0.0] - 2025-10-25

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-25
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v4.0.0

---
## [3.3.0] - 2025-10-25

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-25
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v3.3.0

---
## [3.2.0] - 2025-10-25

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-25
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v3.2.0

---
## [3.1.0] - 2025-10-25

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-25
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v3.1.0

---
## [3.0.5] - 2025-10-25

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-25
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v3.0.5

---
## [3.0.4] - 2025-10-25

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-25
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v3.0.4

---
## [3.0.3] - 2025-10-25

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-25
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v3.0.3

---
## [3.0.2] - 2025-10-25

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-25
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v3.0.2

---
## [3.0.1] - 2025-10-25

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-25
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v3.0.1

---
## [3.0.0] - 2025-10-24

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-24
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v3.0.0

---
## [2.0.6] - 2025-10-24

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-24
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v2.0.6

---
## [2.0.5] - 2025-10-24

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-24
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v2.0.5

---
## [2.0.4] - 2025-10-24

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-24
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v2.0.4

---
## [2.0.3] - 2025-10-24

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-24
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v2.0.3

---
## [2.0.2] - 2025-10-24

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-24
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v2.0.2

---
## [2.0.1] - 2025-10-24

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-24
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v2.0.1

---
## [2.0.0] - 2025-10-24

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-24
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v2.0.0

---
## [1.4.2] - 2025-10-24

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-24
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v1.4.2

---
## [1.4.1] - 2025-10-24

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-24
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v1.4.1

---
## [1.4.0] - 2025-10-24

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-24
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v1.4.0

---
## [1.3.6] - 2025-10-23

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-23
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v1.3.6

---
## [1.3.5] - 2025-10-22

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-22
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v1.3.5

---
## [1.3.4] - 2025-10-22

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-22
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v1.3.4

---
## [1.3.3] - 2025-10-22

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-22
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v1.3.3

---
## [1.3.2] - 2025-10-22

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-22
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v1.3.2

---
## [1.3.1] - 2025-10-22

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-22
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v1.3.1

---
## [1.3.0] - 2025-10-22

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-22
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v1.3.0

---
## [1.2.4] - 2025-10-22

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-22
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v1.2.4

---
## [1.2.3] - 2025-10-22

### 🚀 Automated Release
- **Version**: 1.5.1
- **Date**: 2025-10-22
- **Type**: Automated version bump

### 📋 Changes
- Updated version numbers across all tracked files
- Generated changeset entry
- Updated changelog files
- Created git commit and tag

### 🔧 Technical Details
- **Files Updated**: 4 version files
- **Changelog Updated**: 2 changelog files
- **Git Tag**: v1.2.3

---
## [Unreleased]

### Added
- Initial release of HyperKit AI Agent
- AI-powered smart contract generation with multi-provider support
- Comprehensive security auditing with Slither, Mythril, and custom patterns
- Multi-chain deployment support for Hyperion, Polygon, Arbitrum, and Ethereum
- RAG knowledge system with vector database integration
- Command-line interface with full functionality
- Python API for programmatic access
- Comprehensive test suite with unit tests
- Changesets integration for version management
- GitHub Actions CI/CD pipeline
- Security scanning and code quality enforcement

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- Automated vulnerability detection
- Gas optimization and estimation
- Security pattern validation
- Access control and authentication
- Secure private key management
