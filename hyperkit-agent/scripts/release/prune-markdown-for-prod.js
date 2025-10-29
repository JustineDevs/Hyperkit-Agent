#!/usr/bin/env node
/**
 * Prune Markdown for Production
 * 
 * Removes development-only, legacy, and non-production markdown files
 * before merging to master branch.
 * 
 * Production files to KEEP:
 * - README.md (root)
 * - CHANGELOG.md
 * - CONTRIBUTING.md
 * - SECURITY.md
 * - CODE_OF_CONDUCT.md
 * - LICENSE
 * - docs/* (essential guides only)
 * - REPORTS/ consolidated files (AUDIT.md, QUALITY.md, etc.)
 * 
 * Files to REMOVE for production:
 * - REPORTS/ACCOMPLISHED/*.md (except consolidated ACCOMPLISHED.md)
 * - REPORTS/TODO/*.md (except consolidated TODO_TRACKER.md)
 * - REPORTS/*/ 
 * - individual sharded files
 * - Any *_PROGRESS_*.md, *_MILESTONE_*.md
 * - Any dated reports that are superseded by consolidated files
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

function gitRm(filePath) {
  try {
    const relativePath = path.relative(ROOT_DIR, filePath);
    execSync(`git rm "${relativePath}"`, {
      cwd: ROOT_DIR,
      stdio: 'pipe'
    });
    return true;
  } catch (err) {
    // File might not be tracked, try regular delete
    try {
      fs.unlinkSync(filePath);
      return true;
    } catch (unlinkErr) {
      console.warn(`⚠️  Could not remove ${filePath}: ${err.message}`);
      return false;
    }
  }
}

// Patterns for files to REMOVE
const REMOVE_PATTERNS = [
  // Dated accomplishment files
  /ACCOMPLISHED\/.*_\d{4}-\d{2}-\d{2}\.md$/,
  /ACCOMPLISHED\/ALL_TODOS.*\.md$/,
  /ACCOMPLISHED\/AUDIT_COMPLETE.*\.md$/,
  /ACCOMPLISHED\/BRUTAL_REALITY.*\.md$/,
  /ACCOMPLISHED\/CLI_IMPLEMENTATION.*\.md$/,
  /ACCOMPLISHED\/COMPREHENSIVE.*\.md$/,
  /ACCOMPLISHED\/FINAL.*\.md$/,
  /ACCOMPLISHED\/IMPLEMENTATION.*\.md$/,
  /ACCOMPLISHED\/MISSION_ACCOMPLISHED.*\.md$/,
  /ACCOMPLISHED\/NEXT_STEPS.*\.md$/,
  /ACCOMPLISHED\/ORGANIZATION.*\.md$/,
  /ACCOMPLISHED\/PROJECT.*\.md$/,
  /ACCOMPLISHED\/REALITY_CHECK.*\.md$/,
  /ACCOMPLISHED\/REPORTS_ORGANIZATION.*\.md$/,
  /ACCOMPLISHED\/.*_COMPLETE.*\.md$/,
  /ACCOMPLISHED\/.*_PROGRESS.*\.md$/,
  
  // Progress/TODO individual files
  /TODO\/TODO_IMPLEMENTATION.*\.md$/,
  /TODO\/.*_PROGRESS.*\.md$/,
  
  // Status individual files (keep STATUS.md only)
  /STATUS\/.*_STATUS.*\.md$/,
  /STATUS\/.*_ASSESSMENT.*\.md$/,
  /STATUS\/.*_SUMMARY.*\.md$/,
  
  // Quality individual files (keep QUALITY.md only)
  /QUALITY\/.*_VALIDATION.*\.md$/,
  /QUALITY\/.*_REFERENCE.*\.md$/,
  /QUALITY\/.*_CRITERIA.*\.md$/,
  
  // Individual audit files (keep AUDIT.md only)
  /AUDIT\/.*_BADGE.*\.md$/,
  /AUDIT\/.*_REPORT.*\.md$/,
  
  // Individual IPFS files (keep IPFS.md only)
  /IPFS_RAG\/IPFS_RAG_.*\.md$/,
  
  // Individual compliance files (keep COMPLIANCE.md only)
  /COMPLIANCE\/.*_ASSESSMENT.*\.md$/,
  /COMPLIANCE\/.*_MITIGATION.*\.md$/,
  
  // Individual infrastructure files (keep INFRASTRUCTURE.md only)
  /INFRASTRUCTURE\/.*_PLAN.*\.md$/,
  /INFRASTRUCTURE\/.*_UPDATE.*\.md$/,
  /INFRASTRUCTURE\/.*_ACTION.*\.md$/,
  
  // Individual integration files (keep INTEGRATION.md only)
  /integration\/.*_AUDIT.*\.md$/,
  /integration\/.*_STATUS.*\.md$/,
  
  // Archive README files (keep FIXES_ARCHIVE.md only)
  /archive\/.*\/README\.md$/,
  
  // JSON data files with TODOs/issues (temporary data)
  /JSON_DATA\/.*TODO.*\.json$/,
  /JSON_DATA\/.*ISSUE.*\.json$/,
  /JSON_DATA\/.*INVENTORY.*\.json$/,
  
  // Consolidation scripts and temporary files
  /consolidate.*\.py$/,
  /delete_obsolete.*\.py$/,
  /CONSOLIDATION_COMPLETE\.md$/,
];

// Files to KEEP (these override REMOVE patterns)
const KEEP_FILES = [
  // Root files
  'README.md',
  'CHANGELOG.md',
  'CONTRIBUTING.md',
  'SECURITY.md',
  'CODE_OF_CONDUCT.md',
  'LICENSE',
  
  // Consolidated reports (keep these)
  'REPORTS/ACCOMPLISHED/ACCOMPLISHED.md',
  'REPORTS/AUDIT/AUDIT.md',
  'REPORTS/COMPLIANCE/COMPLIANCE.md',
  'REPORTS/INFRASTRUCTURE/INFRASTRUCTURE.md',
  'REPORTS/IPFS_RAG/IPFS.md',
  'REPORTS/QUALITY/QUALITY.md',
  'REPORTS/STATUS/STATUS.md',
  'REPORTS/TODO/TODO_TRACKER.md',
  'REPORTS/integration/INTEGRATION.md',
  'REPORTS/api-audits/API_AUDITS.md',
  'REPORTS/archive/FIXES_ARCHIVE.md',
  'REPORTS/security/SECURITY.md',
  
  // Category README files
  'REPORTS/README.md',
  'REPORTS/ACCOMPLISHED/README.md',
  'REPORTS/AUDIT/README.md',
  'REPORTS/COMPLIANCE/README.md',
  'REPORTS/IPFS_RAG/README.md',
  'REPORTS/security/README.md',
  
  // Essential docs
  'docs/README.md',
];

function shouldKeepFile(filePath) {
  const relativePath = path.relative(ROOT_DIR, filePath);
  
  // Check keep list first
  for (const keepPattern of KEEP_FILES) {
    if (relativePath.includes(keepPattern) || relativePath === keepPattern) {
      return true;
    }
  }
  
  // Check remove patterns
  for (const pattern of REMOVE_PATTERNS) {
    if (pattern.test(relativePath)) {
      return false;
    }
  }
  
  // Keep files in docs/ (essential guides)
  // Specifically keep all target documentation files that need audit badges
  const TARGET_DOC_FILES = [
    'docs/EXECUTION/', 'docs/GUIDE/', 'docs/INTEGRATION/', 
    'docs/POLICIES/', 'docs/TEAM/'
  ];
  
  if (relativePath.startsWith('docs/') && relativePath.endsWith('.md')) {
    // Check if it's in a target directory
    for (const targetDir of TARGET_DOC_FILES) {
      if (relativePath.startsWith(targetDir)) {
        return true; // Keep all files in target directories
      }
    }
    
    // Only remove if it's clearly a progress/milestone/doc
    const filename = path.basename(relativePath);
    if (filename.includes('_PROGRESS_') || filename.includes('_MILESTONE_') || filename.includes('_TODO_')) {
      return false;
    }
    return true;
  }
  
  // Default: keep unknown files (be conservative)
  return true;
}

function findFilesToRemove(dir = ROOT_DIR) {
  const toRemove = [];
  
  function walkDir(currentDir) {
    const files = fs.readdirSync(currentDir);
    
    for (const file of files) {
      const filePath = path.join(currentDir, file);
      
      try {
        const stats = fs.statSync(filePath);
        
        if (stats.isDirectory()) {
          // Skip node_modules, .git, etc.
          if (!['node_modules', '.git', '__pycache__', '.pytest_cache'].includes(file)) {
            walkDir(filePath);
          }
        } else if (file.endsWith('.md') || file.endsWith('.json')) {
          if (!shouldKeepFile(filePath)) {
            toRemove.push(filePath);
          }
        }
      } catch (err) {
        // Skip errors
      }
    }
  }
  
  walkDir(dir);
  return toRemove;
}

function main() {
  const dryRun = process.argv.includes('--dry-run') || process.argv.includes('-n');
  const autoCommit = !process.argv.includes('--no-commit');
  
  console.log('\n🧹 Pruning markdown files for production\n');
  
  if (dryRun) {
    console.log('🔍 DRY RUN MODE - No files will be deleted\n');
  } else {
    if (autoCommit) {
      console.log(`📝 Auto-commit: ENABLED (use --no-commit to disable)\n`);
    } else {
      console.log(`📝 Auto-commit: DISABLED\n`);
    }
  }
  
  const filesToRemove = findFilesToRemove();
  
  if (filesToRemove.length === 0) {
    console.log('✅ No files need to be removed');
    console.log('   Repository is already clean for production\n');
    return;
  }
  
  console.log(`📋 Found ${filesToRemove.length} file(s) to remove:\n`);
  
  const removedFiles = [];
  
  for (const file of filesToRemove) {
    const relativePath = path.relative(ROOT_DIR, file);
    console.log(`  ${dryRun ? '🔍 Would remove' : '🗑️  Removing'}: ${relativePath}`);
    
    if (!dryRun) {
      try {
        // Use git rm if tracked, otherwise regular delete
        if (gitRm(file)) {
          removedFiles.push(file);
        }
      } catch (err) {
        console.error(`  ❌ Error removing ${relativePath}: ${err.message}`);
      }
    }
  }
  
  console.log();
  
  if (dryRun) {
    console.log(`✅ Dry run complete. ${filesToRemove.length} file(s) would be removed.`);
    console.log(`   Run without --dry-run to actually remove files.\n`);
  } else {
    console.log(`✅ Removed ${filesToRemove.length} file(s)`);
    
    if (autoCommit && removedFiles.length > 0) {
      // Commit deletions
      gitCommit(removedFiles, `chore: prune ${removedFiles.length} development-only files for production`);
      console.log(`   💾 Committed: ${removedFiles.length} file(s) removed`);
    } else if (!autoCommit && removedFiles.length > 0) {
      console.log(`\n📝 Next steps:`);
      console.log(`   1. Review changes: git status`);
      console.log(`   2. Commit: git add -A && git commit -m "chore: prune development-only files for production"`);
    }
    
    console.log(`   Repository is now clean for production merge\n`);
  }
}

if (require.main === module) {
  main();
}

module.exports = { shouldKeepFile, findFilesToRemove };

