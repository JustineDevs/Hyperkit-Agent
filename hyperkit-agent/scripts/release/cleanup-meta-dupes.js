#!/usr/bin/env node
/**
 * Cleanup Duplicate Meta Files
 * 
 * Removes duplicate project-level meta files that should only exist in root:
 * - hyperkit-agent/VERSION (should be root/VERSION only)
 * - hyperkit-agent/CHANGELOG.md (should be root/CHANGELOG.md only)
 * - hyperkit-agent/SECURITY.md (should be root/SECURITY.md only)
 * 
 * This script enforces the "single source of truth" policy for project meta files.
 * 
 * Usage:
 *   node cleanup-meta-dupes.js [--dry-run] [--verbose]
 */

const fs = require('fs');
const path = require('path');

// ROOT_DIR is the repository root (HyperAgent/)
// This script is in hyperkit-agent/scripts/release/, so go up 3 levels
const ROOT_DIR = path.resolve(__dirname, '../../..');

// Files that should ONLY exist in root (not in hyperkit-agent/)
const DUPLICATE_META_FILES = [
  'hyperkit-agent/VERSION',
  'hyperkit-agent/CHANGELOG.md',
  'hyperkit-agent/SECURITY.md',
  'hyperkit-agent/LICENSE.md',
  'hyperkit-agent/CODE_OF_CONDUCT.md',
  'hyperkit-agent/CONTRIBUTING.md',
];

// Files that are ALLOWED to exist in hyperkit-agent/ (package-specific)
const ALLOWED_PACKAGE_FILES = [
  'hyperkit-agent/README.md',  // Package-specific README is OK
  'hyperkit-agent/TODO.md',    // TODO is not a meta file
  'hyperkit-agent/package.json', // Package-specific package.json (if needed)
];

function cleanupDuplicates(dryRun = false, verbose = false) {
  const removed = [];
  const errors = [];
  
  console.log('🔍 Checking for duplicate meta files...\n');
  
  for (const filePath of DUPLICATE_META_FILES) {
    const fullPath = path.join(ROOT_DIR, filePath);
    
    if (fs.existsSync(fullPath)) {
      if (dryRun) {
        console.log(`⚠️  [DRY RUN] Would remove: ${filePath}`);
        removed.push(filePath);
      } else {
        try {
          // Check if root version exists
          const rootFile = filePath.replace('hyperkit-agent/', '');
          const rootPath = path.join(ROOT_DIR, rootFile);
          
          if (!fs.existsSync(rootPath)) {
            console.warn(`⚠️  WARNING: Root ${rootFile} does not exist, but duplicate found at ${filePath}`);
            console.warn(`   Keeping duplicate for now (root file missing)`);
            continue;
          }
          
          // Read both files to compare (optional, for verbose output)
          if (verbose) {
            const duplicateContent = fs.readFileSync(fullPath, 'utf8');
            const rootContent = fs.readFileSync(rootPath, 'utf8');
            
            if (duplicateContent.trim() !== rootContent.trim()) {
              console.warn(`⚠️  Content differs between ${filePath} and ${rootFile}`);
              console.warn(`   Root version will be preserved`);
            }
          }
          
          // Remove duplicate
          fs.unlinkSync(fullPath);
          removed.push(filePath);
          console.log(`✅ Removed: ${filePath}`);
        } catch (err) {
          errors.push({ file: filePath, error: err.message });
          console.error(`❌ Failed to remove ${filePath}: ${err.message}`);
        }
      }
    }
  }
  
  // Summary
  console.log('\n' + '='.repeat(60));
  if (dryRun) {
    if (removed.length > 0) {
      console.log(`⚠️  [DRY RUN] Would remove ${removed.length} duplicate file(s):`);
      removed.forEach(f => console.log(`   - ${f}`));
      console.log('\n   Run without --dry-run to actually remove them.');
    } else {
      console.log('✅ No duplicate meta files detected.');
    }
  } else {
    if (removed.length > 0) {
      console.log(`✅ Cleanup complete: Removed ${removed.length} duplicate file(s):`);
      removed.forEach(f => console.log(`   - ${f}`));
    } else {
      console.log('✅ No duplicate meta files found. Repository is clean.');
    }
    
    if (errors.length > 0) {
      console.log(`\n⚠️  ${errors.length} error(s) occurred:`);
      errors.forEach(e => console.log(`   - ${e.file}: ${e.error}`));
    }
  }
  
  console.log('='.repeat(60));
  
  // Exit code
  if (errors.length > 0) {
    process.exit(1);
  } else if (dryRun && removed.length > 0) {
    process.exit(0); // Dry-run with findings is OK (just informational)
  } else {
    process.exit(0);
  }
}

function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes('--dry-run') || args.includes('-d');
  const verbose = args.includes('--verbose') || args.includes('-v');
  
  console.log('🧹 Duplicate Meta File Cleanup');
  console.log('='.repeat(60));
  console.log(`Repository root: ${ROOT_DIR}`);
  console.log(`Mode: ${dryRun ? 'DRY RUN (no changes)' : 'LIVE (will remove duplicates)'}`);
  console.log();
  
  cleanupDuplicates(dryRun, verbose);
}

if (require.main === module) {
  main();
}

module.exports = { cleanupDuplicates, DUPLICATE_META_FILES };

