# Fixing Foundry Nightly Build on Windows

**Issue**: You have a nightly build of Foundry installed, which is unstable for production and will be refused when `HYPERAGENT_STRICT_FORGE=1`.

## Current Situation

After removing the duplicate binary from `~/.foundry/bin/forge`, you still have:
- **Location**: `C:\Program Files\foundry\forge.EXE`
- **Version**: `1.4.3-nightly` ❌
- **Problem**: This is a nightly build, not stable

## Solution: Replace with Stable Version

### Option 1: Manual Download (Recommended for Windows)

1. **Download Stable Foundry**:
   - Go to: https://github.com/foundry-rs/foundry/releases
   - Look for the latest **stable** release (NOT "nightly" or "pre-release")
   - Download the Windows binary/archive
   - Example: Look for `foundry_nightly_YYYY-MM-DD_windows_amd64.tar.gz` from a stable release

2. **Replace the Binary**:
   ```bash
   # Backup current binary (optional)
   cp "/c/Program Files/foundry/forge.EXE" "/c/Program Files/foundry/forge.EXE.backup"
   
   # Extract and replace with stable version
   # (Follow extraction instructions from the release)
   
   # Verify new version
   forge --version
   # Should show: forge Version: 1.4.8 (or stable version, NOT nightly)
   ```

3. **Update Environment Variable**:
   ```bash
   export HYPERAGENT_FORGE_VERSION="forge 1.3.0"
   # Or match whatever stable version you installed
   ```

4. **Verify**:
   ```bash
   hyperagent config foundry-check
   # Should show: Is Nightly Build: No ✅
   ```

### Option 2: Use Foundryup (If Available)

On Windows, foundryup may not work directly, but you can try:

```bash
# This might work if foundryup is properly configured for Windows
foundryup

# Or specify version
foundryup --version 1.3.0
```

**Note**: Foundryup on Windows is less reliable than Linux/Mac. Manual download is usually more reliable.

### Option 3: Clean Install

If manual replacement doesn't work:

1. **Remove entire Foundry installation**:
   ```bash
   rm -rf "/c/Program Files/foundry"
   ```

2. **Download and extract stable Foundry**:
   - Download from GitHub releases
   - Extract to `C:\Program Files\Foundry\`
   - Ensure `forge.exe`, `cast.exe`, `anvil.exe` are in the `bin/` subdirectory or root

3. **Add to PATH** (if not already):
   - Add `C:\Program Files\Foundry\bin` to your system PATH
   - Or use the full path: `C:\Program Files\Foundry\forge.exe`

4. **Verify**:
   ```bash
   forge --version
   hyperagent config foundry-check
   ```

## Verification Steps

After fixing, verify everything works:

```bash
# 1. Check forge version (should NOT say "nightly")
forge --version

# 2. Run diagnostic
hyperagent config foundry-check

# Expected output:
# - Is Nightly Build: No ✅
# - Would Refuse Deploy: No ✅ (if strict mode is off, or Yes if strict mode is on but version is correct)

# 3. Test workflow (optional)
hyperagent workflow run "create simple ERC20 token" --test-only
```

## Troubleshooting

### Issue: Still shows nightly after replacement

**Check**:
- Which binary is being used: `which forge`
- All forge locations: `which -a forge`
- If PATH has multiple entries, remove duplicates

**Fix**:
```bash
# Check PATH order
echo $PATH

# Ensure the stable version comes first
# Move stable version to a directory that's earlier in PATH
```

### Issue: Permission denied when replacing

**Fix**:
- Run terminal as Administrator on Windows
- Or move to a user-writable location like `C:\Users\<YourUser>\foundry\`

### Issue: Foundryup doesn't work on Windows

**Solution**: Use manual download from GitHub releases. Foundryup is primarily designed for Unix-like systems.

## Environment Variables

After installing stable version, set:

```bash
# Match your stable version (e.g., 1.3.0)
export HYPERAGENT_FORGE_VERSION="forge 1.3.0"

# Optional: Enable strict mode (recommended for production)
export HYPERAGENT_STRICT_FORGE=1

# Add to ~/.bashrc or ~/.profile to persist
echo 'export HYPERAGENT_FORGE_VERSION="forge 1.3.0"' >> ~/.bashrc
echo 'export HYPERAGENT_STRICT_FORGE=1' >> ~/.bashrc
```

## Summary

Your current issue: The binary at `C:\Program Files\foundry\forge.EXE` is still nightly.

**Quick fix**:
1. Download stable from https://github.com/foundry-rs/foundry/releases
2. Replace `C:\Program Files\foundry\forge.EXE` with stable version
3. Verify: `forge --version` (should NOT say "nightly")
4. Run: `hyperagent config foundry-check` to confirm

Once fixed, your workflow commands will work properly, and with strict mode enabled, you'll be protected from accidentally using nightly builds.

