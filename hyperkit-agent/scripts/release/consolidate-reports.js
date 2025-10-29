#!/usr/bin/env node
/**
 * Consolidate Reports
 * 
 * Organizes and consolidates reports in REPORTS/ directory.
 * This script ensures reports are properly organized before production release.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '../..');
const REPORTS_DIR = path.join(ROOT_DIR, 'REPORTS');

// Git operations helper
function gitAdd(filePath) {
  try {
    const relativePath = path.relative(ROOT_DIR, filePath);
    execSync(`git add "${relativePath}"`, {
      cwd: ROOT_DIR,
      stdio: 'pipe'
    });
    return true;
  } catch (err) {
    console.warn(`⚠️  Could not git add ${filePath}: ${err.message}`);
    return false;
  }
}

function gitCommit(files, message) {
  try {
    // If files array is provided, add each file
    if (Array.isArray(files) && files.length > 0) {
      for (const filePath of files) {
        gitAdd(filePath);
      }
    }
    
    // Commit with message
    execSync(`git commit -m "${message}"`, {
      cwd: ROOT_DIR,
      stdio: 'pipe'
    });
    return true;
  } catch (err) {
    // If commit fails (e.g., no changes), that's okay
    if (err.message.includes('nothing to commit')) {
      return false;
    }
    console.warn(`⚠️  Could not commit: ${err.message}`);
    return false;
  }
}

// Check if consolidation script exists (Python version)
// Note: merge.py is the unified script that replaces consolidate_reports.py, consolidate_archive.py, and delete_obsolete_files.py
function runConsolidationScript() {
  // Try merge.py first (unified script)
  const mergeScript = path.join(ROOT_DIR, 'scripts', 'reports', 'merge.py');
  // Prefer merge.py (unified), fallback to consolidate_reports.py
  const scriptToUse = fs.existsSync(mergeScript) ? mergeScript : consolidateScript;
  
  if (fs.existsSync(scriptToUse)) {
    const scriptName = path.basename(scriptToUse);
    console.log(`📊 Running Python script: ${scriptName}\n`);
    try {
      const { execSync } = require('child_process');
      execSync(`python "${scriptToUse}"`, {
        cwd: ROOT_DIR,
        stdio: 'inherit',
        env: {
          ...process.env,
          REPORTS_DIR: REPORTS_DIR  // Pass REPORTS directory as env var
        }
      });
      console.log('\n✅ Reports consolidated successfully');
      return true;
    } catch (err) {
      console.error('\n❌ Error running consolidation script');
      console.error(`   Exit code: ${err.status || 'unknown'}`);
      if (err.message) {
        console.error(`   Error: ${err.message}`);
      }
      return false;
    }
  } else {
    console.log('ℹ️  Consolidation script not found, skipping');
    console.log(`   Expected at: ${consolidateScript}`);
    console.log('   Reports should already be consolidated');
    return true;
  }
}

function verifyConsolidatedFiles(autoCommit = false) {
  const expectedFiles = [
    'ACCOMPLISHED/ACCOMPLISHED.md',
    'AUDIT/AUDIT.md',
    'COMPLIANCE/COMPLIANCE.md',
    'INFRASTRUCTURE/INFRASTRUCTURE.md',
    'IPFS_RAG/IPFS.md',
    'QUALITY/QUALITY.md',
    'STATUS/STATUS.md',
    'TODO/TODO_TRACKER.md',
    'integration/INTEGRATION.md',
    'api-audits/API_AUDITS.md',
    'archive/FIXES_ARCHIVE.md',
    'security/SECURITY.md'
  ];
  
  console.log('\n🔍 Verifying consolidated files...\n');
  
  let allPresent = true;
  const existingFiles = [];
  
  for (const file of expectedFiles) {
    const filePath = path.join(REPORTS_DIR, file);
    if (fs.existsSync(filePath)) {
      const stats = fs.statSync(filePath);
      const sizeKB = (stats.size / 1024).toFixed(1);
      console.log(`  ✅ ${file} (${sizeKB} KB)`);
      existingFiles.push(filePath);
    } else {
      console.log(`  ⚠️  ${file} - MISSING`);
      allPresent = false;
    }
  }
  
  if (!allPresent) {
    console.log('\n⚠️  Some consolidated files are missing. Run consolidation script first.');
    return { success: false, files: [] };
  }
  
  console.log('\n✅ All consolidated files present');
  
  // Commit consolidated files if auto-commit enabled
  if (autoCommit && existingFiles.length > 0) {
    // Check if any files were modified
    try {
      const status = execSync('git status --porcelain', {
        cwd: ROOT_DIR,
        encoding: 'utf8'
      }).trim();
      
      const modifiedFiles = existingFiles.filter(filePath => {
        const relativePath = path.relative(ROOT_DIR, filePath);
        return status.includes(relativePath);
      });
      
      if (modifiedFiles.length > 0) {
        gitCommit(modifiedFiles, 'docs: update consolidated reports');
        console.log(`   💾 Committed ${modifiedFiles.length} report file(s)`);
      }
    } catch (err) {
      // Ignore git errors
    }
  }
  
  return { success: true, files: existingFiles };
}

function main() {
  const autoCommit = !process.argv.includes('--no-commit');
  
  console.log('\n📊 Consolidating and organizing reports\n');
  
  if (autoCommit) {
    console.log(`📝 Auto-commit: ENABLED (use --no-commit to disable)\n`);
  } else {
    console.log(`📝 Auto-commit: DISABLED\n`);
  }
  
  if (!fs.existsSync(REPORTS_DIR)) {
    console.log(`⚠️  REPORTS directory not found: ${REPORTS_DIR}`);
    process.exit(1);
  }
  
  const consolidated = runConsolidationScript();
  if (!consolidated) {
    process.exit(1);
  }
  
  const { success: verified, files: reportFiles } = verifyConsolidatedFiles(autoCommit);
  if (!verified) {
    process.exit(1);
  }
  
  console.log('\n✅ Reports organization complete');
  
  if (!autoCommit && reportFiles.length > 0) {
    console.log(`\n📝 Next steps:`);
    console.log(`   1. Review changes: git diff REPORTS/`);
    console.log(`   2. Commit: git add REPORTS/ && git commit -m "docs: consolidate reports"`);
  }
  
  console.log();
}

if (require.main === module) {
  main();
}

module.exports = { runConsolidationScript, verifyConsolidatedFiles };

