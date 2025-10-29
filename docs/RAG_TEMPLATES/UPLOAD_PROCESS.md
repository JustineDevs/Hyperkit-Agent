<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: 1.5.4  
**Last Verified**: 2025-10-28  
**Commit**: `d5465090`  
**Branch**: `main`  
<!-- AUDIT_BADGE_END -->

# RAG Template Upload Process - Standard Operating Procedure

**Purpose**: Standardized process for uploading RAG templates to IPFS  
**Goal**: Zero asset sprawl, clear CID tracking, repeatable process  
**Version**: 1.0  
**Last Updated**: 2025-10-28

---

## 📋 Pre-Upload Checklist

Before uploading any template, ensure:

- [ ] Template is production-ready (no TODOs, no placeholders)
- [ ] Template has clear, descriptive function-based name
- [ ] Template is entered in `cid-registry.json`
- [ ] Template description is clear and concise
- [ ] No duplicate templates exist
- [ ] Category is correctly assigned

---

## 🚀 Upload Process

### Step 1: Prepare Template File

**Convert markdown to IPFS-ready format:**

```bash
# From markdown
cat docs/RAG_TEMPLATES/Contracts/ERC20-Template.md \
  > temp-uploads/erc20-template.txt

# Add metadata wrapper (optional but recommended)
cat > temp-uploads/erc20-template.json <<EOF
{
  "name": "erc20-template",
  "description": "Standard ERC20 fungible token contract template",
  "category": "contracts",
  "content": "$(cat docs/RAG_TEMPLATES/Contracts/ERC20-Template.md | jq -Rs .)"
}
EOF
```

### Step 2: Upload to Pinata

**Option A: Using Pinata API (Recommended)**
```bash
curl -X POST https://api.pinata.cloud/pinning/pinFileToIPFS \
  -H "Authorization: Bearer $PINATA_JWT" \
  -H "Content-Type: multipart/form-data" \
  -F file=@temp-uploads/erc20-template.txt
```

**Option B: Using our IPFS script**
```bash
python hyperkit-agent/scripts/setup_rag_vectors.py \
  --upload-template erc20-template.txt \
  --category contracts
```

### Step 3: Record CID

**Update cid-registry.json:**
```json
"erc20-template": {
  "description": "Standard ERC20 fungible token contract template",
  "filename": "ERC20-Template.md",
  "category": "contracts",
  "cid": "QmXXXXXXXXXXXXXXXXXXXXX",  // ← PASTE CID HERE
  "uploaded": true,
  "upload_date": "2025-10-28",
  "uploaded_by": "your-username"
}
```

### Step 4: Update README

**Update docs/RAG_TEMPLATES/README.md:**

Change status table:
```markdown
| erc20-template | ✅ Uploaded | QmXXX... | Verified working |
```

### Step 5: Validate

**Run validation script:**
```bash
hyperagent validate_rag_templates

# Expected output:
# ✅ All templates uploaded
# ✅ All CIDs valid
# ✅ No orphaned files
# ✅ Registry in sync
```

---

## 🔍 Verification

After upload, verify:

1. **CID is accessible:**
   ```bash
   curl https://ipfs.io/ipfs/QmXXXXXXXXXXXXXXXXXXXXX
   ```

2. **AI agent can fetch:**
   ```python
   from services.rag.template_fetcher import fetch_template
   template = fetch_template("erc20-template")
   assert template is not None
   ```

3. **Registry is updated:**
   ```bash
   cat docs/RAG_TEMPLATES/cid-registry.json | jq '.templates."erc20-template".uploaded'
   # Should return: true
   ```

---

## ❌ Common Mistakes to Avoid

**Don't:**
- ❌ Upload without updating registry
- ❌ Use random/timestamped names
- ❌ Bulk pack templates (one file = one CID)
- ❌ Upload duplicates
- ❌ Leave TODOs or placeholders
- ❌ Forget to update README

**Do:**
- ✅ Upload one at a time
- ✅ Update registry immediately
- ✅ Use descriptive function-based names
- ✅ Test CID access after upload
- ✅ Document any issues
- ✅ Update status table

---

## 📊 Progress Tracking

Track upload progress in `cid-registry.json`:

```json
{
  "upload_status": {
    "total_templates": 8,
    "uploaded": 0,
    "pending": 8,
    "last_upload": null,
    "next_review": "2025-11-01"
  }
}
```

---

## 🔄 Maintenance Schedule

- **Weekly**: Check for orphaned uploads
- **Monthly**: Review CID accessibility
- **Quarterly**: Audit registry for drift
- **Annually**: Full template library review

---

## 🎯 Success Criteria

Upload is successful when:

✅ Template file uploaded to IPFS  
✅ CID recorded in registry  
✅ Registry validated (no errors)  
✅ README status updated  
✅ CID is publicly accessible  
✅ AI agent can fetch template  
✅ Documentation complete  

---

**Last Updated**: 2025-10-28  
**Owner**: HyperAgent Core Team  
**Contact**: See CONTRIBUTING.md

