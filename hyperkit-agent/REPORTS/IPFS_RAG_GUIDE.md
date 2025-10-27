# 🌐 IPFS RAG Integration Guide

## Overview

HyperKit Agent now supports **decentralized IPFS-based vector storage** for RAG (Retrieval-Augmented Generation). This implementation allows you to:

- ✅ Store vector databases on IPFS (content-addressed, immutable)
- ✅ Share vector stores across developers, CI/CD, and production
- ✅ Fetch the latest vector store by CID without local rebuilds
- ✅ Keep repositories lightweight (no large binary files in git)
- ✅ Enable censorship-resistant, truly portable AI knowledge infrastructure

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd hyperkit-agent
pip install ipfshttpclient chromadb
```

### 2. Generate Initial Vector Store (Local)

```bash
python scripts/setup_rag_vectors.py
```

This creates a local ChromaDB vector store at `data/vector_store/`.

### 3. Upload to IPFS

```bash
python scripts/setup_rag_vectors.py --upload-ipfs
```

**Output:**
```
✓ Uploaded to IPFS with CID: QmXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  Access at: https://ipfs.io/ipfs/QmXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  Save this CID to fetch later: QmXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Save the CID** - you'll need it to fetch the vector store later!

### 4. Fetch from IPFS (New Developer/CI/CD)

```bash
python scripts/setup_rag_vectors.py --fetch-cid QmXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

This downloads the vector store from IPFS and extracts it locally.

### 5. List Registered CIDs

```bash
python scripts/setup_rag_vectors.py --list-cids
```

Shows all CIDs you've uploaded or fetched, with timestamps.

---

## 📋 Complete Workflow Example

### Scenario: New Team Member Joining

**Without IPFS (Old Way):**
```bash
# 1. Clone repo (gets huge with vectors)
git clone https://github.com/YourOrg/HyperKit-Agent
cd HyperKit-Agent

# 2. Run setup (takes 10-30 minutes to generate vectors)
python scripts/setup_rag_vectors.py

# 3. Hope it works on their machine
```

**With IPFS (New Way):**
```bash
# 1. Clone repo (lightweight, no vectors)
git clone https://github.com/YourOrg/HyperKit-Agent
cd HyperKit-Agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Fetch pre-built vectors from IPFS (< 1 minute)
python scripts/setup_rag_vectors.py --fetch-cid QmXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 4. Ready to go!
```

---

## 🏗️ Architecture

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    IPFS RAG Architecture                     │
└─────────────────────────────────────────────────────────────┘

Developer A (Building)                Developer B (Fetching)
     │                                       │
     ├─ Generate vectors ─┐                │
     │  locally           │                │
     │                    │                │
     └─ Upload to IPFS ───┼──────── CID ───┘
                          │
                     ┌────▼────┐
                     │  IPFS   │
                     │   CID   │
                     └─────────┘
                          │
        All developers fetch by same CID
```

### Key Components

1. **Local ChromaDB**: Generates and caches vectors locally
2. **CID Registry**: Tracks uploaded/fetched CIDs (`data/vector_store/cid_registry.json`)
3. **IPFS Upload**: Compresses vector store and uploads to IPFS
4. **IPFS Fetch**: Downloads by CID and extracts locally

---

## 📦 IPFS Storage Strategy

### What Gets Uploaded

The entire `data/vector_store/` directory including:
- ChromaDB database files
- Collection metadata
- Vector embeddings
- Index files

**Typical Size**: 50-500MB (compressed)

### CID Registry

Stored at: `data/vector_store/cid_registry.json`

```json
{
  "latest_cid": "QmXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "versions": [
    {
      "cid": "QmXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      "timestamp": 1706697600,
      "uploaded": true
    },
    {
      "cid": "QmYyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy",
      "timestamp": 1706697645,
      "fetched": true
    }
  ]
}
```

---

## 🔧 Advanced Configuration

### Option 1: Local IPFS Node

**Best for development and frequent updates**

```bash
# Install IPFS
ipfs init
ipfs daemon

# Now upload/fetch uses local node (faster)
python scripts/setup_rag_vectors.py --upload-ipfs
```

**Benefits:**
- Faster uploads/downloads
- No rate limits
- Full IPFS functionality
- Can pin your own data

### Option 2: IPFS Gateway (Pinata)

**Best for production and CI/CD**

```bash
# Set environment variables
export PINATA_API_KEY="your_key"
export PINATA_API_SECRET="your_secret"

# Upload uses Pinata (reliable pinning)
python scripts/setup_rag_vectors.py --upload-ipfs
```

**Benefits:**
- Reliable pinning service
- No local IPFS node needed
- CDN-backed gateways
- Professional SLA

### Option 3: Public Gateways Only

**Simplest setup (no credentials)**

```bash
# Just use public IPFS gateways
python scripts/setup_rag_vectors.py --upload-ipfs  # Mock CID
python scripts/setup_rag_vectors.py --fetch-cid Qm...  # Downloads from gateways
```

**Benefits:**
- No setup required
- Works everywhere
- No API keys

**Limitations:**
- Slower downloads
- No guaranteed pinning
- Dependent on gateway availability

---

## 🎯 Best Practices

### 1. Version Management

**Always version your vector stores:**

```bash
# After updating vectors
git commit -am "Update vector store"
CID=$(python scripts/setup_rag_vectors.py --upload-ipfs)
echo "LATEST_VECTOR_STORE_CID=$CID" >> .env
git commit -am "Update vector store CID"
```

### 2. CI/CD Integration

**Update `.github/workflows/ci-cd.yml`:**

```yaml
- name: Fetch Vector Store from IPFS
  run: |
    python scripts/setup_rag_vectors.py --fetch-cid ${{ secrets.VECTOR_STORE_CID }}

- name: Run Tests with RAG
  run: |
    python -m pytest tests/
```

### 3. Backup Strategy

**Pin your important CIDs:**

```bash
# Via Pinata dashboard or API
# Or use ipfs pin add <CID>
```

### 4. Automate Sync

**Create `scripts/sync_vectors.sh`:**

```bash
#!/bin/bash
LATEST_CID=$(cat .env | grep VECTOR_STORE_CID | cut -d= -f2)
python scripts/setup_rag_vectors.py --fetch-cid $LATEST_CID
```

---

## 🐛 Troubleshooting

### Problem: "Failed to upload to IPFS"

**Solutions:**
1. Check if IPFS daemon is running: `ipfs daemon`
2. Verify Pinata credentials: `echo $PINATA_API_KEY`
3. Check network connectivity: `ping ipfs.io`

### Problem: "Failed to fetch from all gateways"

**Solutions:**
1. Try direct IPFS node: `ipfs daemon`
2. Wait a few minutes (gateways cache)
3. Use different gateway: `https://gateway.pinata.cloud/ipfs/` vs `https://ipfs.io/ipfs/`

### Problem: "ChromaDB not initialized"

**Solution:**
```bash
python scripts/setup_rag_vectors.py  # Create local store first
```

### Problem: Large upload times

**Solutions:**
1. Use local IPFS node instead of gateway
2. Compress before upload (automatically done)
3. Use Pinata (has CDN)

---

## 📊 Performance Benchmarks

### Upload Time (First Time)

- **Local IPFS Node**: ~30 seconds per 100MB
- **Pinata API**: ~1-2 minutes per 100MB
- **Public Gateway**: N/A (not recommended)

### Download Time

- **Local IPFS Node**: ~10 seconds per 100MB
- **Pinata Gateway**: ~30-60 seconds per 100MB
- **Public Gateway**: ~1-3 minutes per 100MB

### Size Comparison

- **Raw ChromaDB**: ~200MB
- **Compressed (tar.gz)**: ~50MB
- **Git Repo (without IPFS)**: +200MB per commit
- **Git Repo (with IPFS)**: +1KB per CID

---

## 🎓 Examples

### Example 1: Fresh Install

```bash
# Clone the repo
git clone https://github.com/YourOrg/HyperKit-Agent
cd HyperKit-Agent

# Install dependencies
pip install -r requirements.txt

# Fetch latest vector store
python scripts/setup_rag_vectors.py --fetch-cid QmABC123...

# Verify
python scripts/setup_rag_vectors.py --list-cids

# Ready to use!
hyperagent workflow run "Create ERC20 token"
```

### Example 2: Update Vector Store

```bash
# Modify knowledge base
echo "New documentation..." >> docs/new_feature.md

# Regenerate vectors
python scripts/setup_rag_vectors.py

# Upload to IPFS
python scripts/setup_rag_vectors.py --upload-ipfs
# Save the new CID!

# Update CI/CD with new CID
# Update secrets.VECTOR_STORE_CID in GitHub Actions
```

### Example 3: Multiple Environments

```bash
# Production environment
export VECTOR_STORE_CID="QmPROD..."
python scripts/setup_rag_vectors.py --fetch-cid $VECTOR_STORE_CID

# Staging environment
export VECTOR_STORE_CID="QmSTAGE..."
python scripts/setup_rag_vectors.py --fetch-cid $VECTOR_STORE_CID

# Development environment
python scripts/setup_rag_vectors.py  # Build locally
```

---

## 🔐 Security Considerations

### Privacy

- **Public IPFS**: All data is publicly accessible
- **Encryption**: Encrypt sensitive data before upload
- **Private IPFS**: Use private IPFS network for sensitive data

### Access Control

- **Public**: Anyone with CID can fetch
- **Private**: Use IPFS private network
- **Encryption**: Encrypt before upload

### Best Practices

1. ✅ Store only non-sensitive knowledge in public IPFS
2. ✅ Encrypt sensitive data before upload
3. ✅ Use Pinata with IPFS for reliability
4. ✅ Pin important CIDs to prevent garbage collection
5. ✅ Monitor vector store size and performance

---

## 🎉 Benefits Summary

### For Developers
- ⚡ Fast onboarding (fetch vs rebuild)
- 🔄 Easy updates (push new CID)
- 💾 No large files in git
- 🚀 CI/CD friendly

### For DevOps
- 📦 Version-controlled vector stores
- 🌐 Decentralized infrastructure
- 💰 Reduced storage costs
- 🔒 Immutable audit trails

### For Organizations
- 🌍 Global access (any IPFS node)
- 🛡️ Censorship resistance
- 📈 Scalable knowledge sharing
- 🔗 Web3-native architecture

---

## 📚 Additional Resources

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [IPFS Documentation](https://docs.ipfs.io/)
- [Pinata Setup Guide](../docs/EXECUTION/PINATA_SETUP_GUIDE.md)
- [HyperKit Agent RAG System](../docs/OBSIDIAN_RAG_SETUP_GUIDE.md)

---

## 🙋 Support

If you encounter issues:

1. Check [Troubleshooting](#-troubleshooting) section
2. Review [ChromaDB logs](data/vector_store/)
3. Check [IPFS CID registry](data/vector_store/cid_registry.json)
4. Open an issue on GitHub

---

**Last Updated**: 2025-01-25  
**Version**: 1.2.0  
**Author**: HyperKit Development Team
