# RAG Templates - IPFS Integration

**Status**: Prepared for IPFS upload  
**Purpose**: AI agent template library for HyperAgent RAG system  
**Upload Tool**: Pinata IPFS  
**Last Updated**: 2025-10-28

---

## 📋 Template Inventory

### 🎯 Contracts (2 templates)
- **erc20-template** - Standard ERC20 fungible token contract
- **erc721-template** - Standard ERC721 NFT contract

### 🔧 Templates (1 template)
- **hardhat-deploy** - Hardhat deployment script template with env config

### 🔍 Audits (2 templates)
- **gas-optimization-audit** - Gas optimization audit checklist
- **security-checklist** - Security best-practices audit template

### 💬 Prompts (3 templates)
- **contract-generation-prompt** - General contract creation prompts
- **generation-style-prompt** - Style/feature control prompts
- **security-prompts** - Security-focused generation prompts

---

## 🚀 Upload Instructions

### Prerequisites
1. Pinata account (https://www.pinata.cloud/)
2. PINATA_API_KEY and PINATA_SECRET_KEY in `.env`
3. Python with `ipfshttpclient` or Pinata API

### Upload Process

**Step 1**: Convert markdown files to IPFS-ready format
```bash
# Each template should be uploaded with descriptive function-based name
# Example: ERC20-Template.md → erc20-template.txt
```

**Step 2**: Upload to IPFS Pinata
```bash
# Using our existing IPFS upload script
python hyperkit-agent/scripts/setup_rag_vectors.py --upload-ipfs templates/
```

**Step 3**: Update CID registry
```json
"erc20-template": {
  "cid": "QmXXXXXXXXXXXXXXXXXXXXX",
  "uploaded": true,
  "upload_date": "2025-10-28"
}
```

---

## 📝 Naming Principles

✅ **DO**:
- Use function-based descriptive names: `erc20-template`, `hardhat-deploy`
- Keep consistency across filename and CID registry key
- One CID per template file

❌ **DON'T**:
- Use random/timestamped names: `template_1234567.txt`
- Bulk pack templates (each gets unique CID)
- Reuse filenames for different template types

---

## 🔍 CID Registry

See `cid-registry.json` for complete mapping:
- Template name → IPFS CID
- Category grouping
- Upload status
- File locations

**Usage**:
```python
# In AI agent RAG system
registry = load_cid_registry("docs/RAG_TEMPLATES/cid-registry.json")
cid = registry.templates["erc20-template"]["cid"]
template = fetch_from_ipfs(cid)
```

---

## 📊 Current Status

| Template | Status | CID | Notes |
|----------|--------|-----|-------|
| erc20-template | ✅ Uploaded | QmYWkBLnCwUHtA4vgsFM4ePrCG9xpo2taHRsvEbbyz2JYs | Verified working |
| erc721-template | ✅ Uploaded | QmQSsEKKG6JyMhM523ZPeMPDYCyiFxTVKTFqZerjABdTA4 | Verified working |
| hardhat-deploy | ✅ Uploaded | QmXwNxjvkw9aLZARfvM1bPThKMuP9eqmzD4cevtswKsvvh | Verified working |
| gas-optimization-audit | ✅ Uploaded | QmZ3QGB43iF9ntopnbpnPG5pnWxL3DcD2nnQBWU4ECiTY4 | Verified working |
| security-checklist | ✅ Uploaded | QmRv9N296TqgyJJUSdov5d9jk9jWQHQf8eMKJXfpPmkjAS | Verified working |
| contract-generation-prompt | ✅ Uploaded | QmSC6QjuDrhNfpX9vA7P37wC4qXrMf8wYSscf2fLXugU5F | Verified working |
| generation-style-prompt | ✅ Uploaded | QmeyKuYQoYUToTetEV5ti2t3nBJD5v8TrezXUdP1hbmoUs | Verified working |
| security-prompts | ✅ Uploaded | QmYS2tXdBNFj3Pie6RUi5WKFPzGgL173M1wrhQhwsmbmAV | Verified working |

---

## 🔄 Maintenance Process

**When adding new template**:
1. Add entry to `cid-registry.json`
2. Upload to IPFS Pinata (one file per CID)
3. Update CID in registry
4. Run validation: `validate_rag_templates.py`
5. Update this README with new status

**Zero asset sprawl policy**:
- Every template must have clear description
- Every CID must be in registry
- Every upload date must be tracked
- No orphaned assets in IPFS

---

## 🎯 Next Steps

1. ✅ **DONE**: Analyzed all templates
2. ✅ **DONE**: Created CID registry
3. ✅ **DONE**: Created README with upload instructions
4. ⚠️ **PENDING**: Upload to Pinata (requires API keys)
5. ⚠️ **PENDING**: Update CIDs in registry
6. ⚠️ **PENDING**: Test AI agent fetching by CID

---

**Last Updated**: 2025-10-28  
**Maintained By**: HyperAgent Core Team  
**IPFS Integration**: Production-ready (`setup_rag_vectors.py`)

