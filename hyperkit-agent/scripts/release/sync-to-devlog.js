#!/usr/bin/env node
/**
 * Sync Documentation to Devlog Branch
 * 
 * Moves all documentation files (.md, .json in docs/REPORTS) to devlog branch
 * while keeping only code and essential docs in main branch.
 * 
 * This script is called automatically during version bumps to maintain
 * branch separation.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const readline = require('readline');

const ROOT_DIR = path.resolve(__dirname, '../..');
const WHITELIST_FILE = path.join(ROOT_DIR, 'hyperkit-agent/scripts/ci/essential_docs_whitelist.json');

function loadWhitelist() {
  if (!fs.existsSync(WHITELIST_FILE)) {
    console.warn(`[WARNING] Whitelist file not found: ${WHITELIST_FILE}`);
    return {
      files: [],
      directories_keep_in_main: [],
      directories_move_to_devlog: []
    };
  }
  
  return JSON.parse(fs.readFileSync(WHITELIST_FILE, 'utf8'));
}

function getCurrentBranch() {
  try {
    return execSync('git rev-parse --abbrev-ref HEAD', {
      cwd: ROOT_DIR,
      encoding: 'utf8'
    }).trim();
  } catch (err) {
    console.error(`[ERROR] Error getting current branch: ${err.message}`);
    process.exit(1);
  }
}

function isCleanWorkingTree() {
  try {
    execSync('git diff --quiet HEAD', { cwd: ROOT_DIR, stdio: 'pipe' });
    return true;
  } catch {
    return false;
  }
}

function getAllFiles(dir, fileList = []) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    
    // Skip git and ignored dirs
    if (entry.isDirectory()) {
      if (['.git', 'node_modules', '__pycache__', '.pytest_cache', '.venv', 'venv'].includes(entry.name)) {
        continue;
      }
      getAllFiles(fullPath, fileList);
    } else {
      fileList.push(fullPath);
    }
  }
  
  return fileList;
}

function getDocFilesToSync(repoRoot, whitelist) {
  const docExtensions = ['.md', '.json'];
  const docFiles = [];
  
  // Directories that should be moved to devlog
  const devlogDirs = whitelist.directories_move_to_devlog || [];
  
  // Essential files that stay in main
  const essentialFiles = new Set(whitelist.files || []);
  
  const allFiles = getAllFiles(repoRoot);
  
  for (const filePath of allFiles) {
    const relPath = path.relative(repoRoot, filePath);
    const ext = path.extname(filePath);
    
    // Skip if in essential files whitelist
    if (essentialFiles.has(relPath)) {
      continue;
    }
    
    // Check if file is in a devlog directory
    const shouldMoveDir = devlogDirs.some(dir => 
      relPath.startsWith(dir) || relPath === dir
    );
    
    if (shouldMoveDir && docExtensions.includes(ext)) {
      docFiles.push(relPath);
    }
  }
  
  return docFiles;
}

function askQuestion(question) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });
  
  return new Promise(resolve => {
    rl.question(question, answer => {
      rl.close();
      resolve(answer);
    });
  });
}

// Track original branch for cleanup
let originalBranch = null;

// Cleanup function for signal handlers
function cleanupOnExit() {
  if (originalBranch) {
    const current = getCurrentBranch();
    if (current !== originalBranch) {
      try {
        console.log(`\n[CLEANUP] Restoring original branch: ${originalBranch}`);
        execSync(`git checkout ${originalBranch}`, {
          cwd: ROOT_DIR,
          stdio: 'pipe'
        });
      } catch (err) {
        console.error(`[ERROR] Failed to restore branch: ${err.message}`);
        console.error(`[MANUAL] Run: git checkout ${originalBranch}`);
      }
    }
  }
}

// Register cleanup handlers
process.on('SIGINT', () => {
  console.log('\n\n[INTERRUPT] Sync interrupted by user');
  cleanupOnExit();
  process.exit(130);
});

process.on('SIGTERM', () => {
  console.log('\n\n[TERMINATE] Sync terminated');
  cleanupOnExit();
  process.exit(143);
});

process.on('exit', cleanupOnExit);

async function syncToDevlog(dryRun = false) {
  // Store original branch for cleanup
  originalBranch = getCurrentBranch();
  const currentBranch = originalBranch;
  
  if (currentBranch !== 'main') {
    console.log(`[WARNING] Not on main branch (current: ${currentBranch})`);
    console.log('   This script should typically run from main branch');
    const response = await askQuestion('   Continue anyway? (y/N): ');
    if (response.toLowerCase() !== 'y') {
      originalBranch = null; // Clear tracking
      return false;
    }
  }
  
  // Check for uncommitted changes
  if (!isCleanWorkingTree() && !dryRun) {
    console.log('\n❌ [ERROR] Working tree has uncommitted changes');
    console.log('   Sync-to-devlog requires a clean working tree for safety.');
    console.log('   Branch switching and merging with uncommitted changes can cause data loss.\n');
    
    // Show what files have changes
    try {
      const statusOutput = execSync('git status --short', {
        cwd: ROOT_DIR,
        encoding: 'utf8'
      }).trim();
      
      if (statusOutput) {
        const lines = statusOutput.split('\n').slice(0, 10);
        console.log('   Uncommitted changes detected:');
        lines.forEach(line => {
          console.log(`     ${line}`);
        });
        if (statusOutput.split('\n').length > 10) {
          console.log(`     ... and ${statusOutput.split('\n').length - 10} more files`);
        }
        console.log('');
      }
    } catch (err) {
      // Ignore errors getting status
    }
    
    console.log('   📋 Next steps:');
    console.log('   1. Review changes: git status');
    console.log('   2. Commit changes: git add . && git commit -m "your message"');
    console.log('      OR stash changes: git stash');
    console.log('   3. Re-run: npm run hygiene (or npm run version:patch)');
    console.log('');
    console.log('   ⚠️  Never bypass this check - it protects your repository integrity!\n');
    
    originalBranch = null; // Clear tracking
    process.exit(1);
  }
  
  // Load whitelist
  const whitelist = loadWhitelist();
  
  // Get files to sync
  const docFiles = getDocFilesToSync(ROOT_DIR, whitelist);
  
  if (docFiles.length === 0) {
    console.log('[INFO] No documentation files found to sync');
    return true;
  }
  
  if (dryRun) {
    console.log(`[DRY RUN] Would sync ${docFiles.length} files to devlog branch`);
    console.log('\nFiles that would be synced:');
    for (let i = 0; i < Math.min(20, docFiles.length); i++) {
      console.log(`  ${docFiles[i]}`);
    }
    if (docFiles.length > 20) {
      console.log(`  ... and ${docFiles.length - 20} more`);
    }
    return true;
  }
  
  console.log(`[SYNC] Syncing ${docFiles.length} documentation files to devlog branch...`);
  
  try {
    // Stash any uncommitted changes (should be clean, but safety check)
    execSync('git stash', { cwd: ROOT_DIR, stdio: 'pipe' });
    
    // Check if devlog branch exists
    let devlogExists = false;
    try {
      execSync('git show-ref --verify --quiet refs/heads/devlog', {
        cwd: ROOT_DIR,
        stdio: 'pipe'
      });
      devlogExists = true;
    } catch {
      devlogExists = false;
    }
    
    if (!devlogExists) {
      // Create devlog branch from main
      console.log('[CREATE] Creating devlog branch...');
      execSync('git checkout -b devlog', { cwd: ROOT_DIR, stdio: 'inherit' });
      execSync(`git checkout ${currentBranch}`, { cwd: ROOT_DIR, stdio: 'inherit' });
    } else {
      // Checkout devlog
      console.log('[CHECKOUT] Checking out devlog branch...');
      execSync('git checkout devlog', { cwd: ROOT_DIR, stdio: 'inherit' });
      
      // Merge latest from main to get code updates
      console.log('[MERGE] Merging latest from main...');
      execSync(`git merge ${currentBranch} --no-edit --no-ff`, {
        cwd: ROOT_DIR,
        stdio: 'inherit'
      });
    }
    
    // Ensure all doc files are present in devlog
    console.log('[FILES] Ensuring documentation files are present...');
    for (const docFile of docFiles) {
      const filePath = path.join(ROOT_DIR, docFile);
      if (fs.existsSync(filePath)) {
        // File exists, ensure it's tracked
        execSync(`git add "${docFile}"`, { cwd: ROOT_DIR, stdio: 'pipe' });
      } else {
        // File might have been deleted, check if it exists in main
        try {
          execSync(`git checkout ${currentBranch} -- "${docFile}"`, {
            cwd: ROOT_DIR,
            stdio: 'pipe'
          });
          if (fs.existsSync(filePath)) {
            execSync(`git add "${docFile}"`, { cwd: ROOT_DIR, stdio: 'pipe' });
          }
        } catch {
          // File doesn't exist in main either, skip
        }
      }
    }
    
    // Commit changes to devlog
    try {
      execSync('git diff --cached --quiet', { cwd: ROOT_DIR, stdio: 'pipe' });
      // No changes to commit
      console.log('[INFO] No new documentation changes to commit on devlog');
    } catch {
      // Has changes
      const commitMessage = `chore(devlog): sync documentation from ${currentBranch}

Synced ${docFiles.length} documentation files from main branch.
Generated: ${new Date().toISOString()}`;
      execSync(`git commit -m "${commitMessage}"`, {
        cwd: ROOT_DIR,
        stdio: 'inherit'
      });
      console.log('[OK] Committed documentation changes to devlog');
    }
    
    // Return to original branch
    execSync(`git checkout ${currentBranch}`, { cwd: ROOT_DIR, stdio: 'inherit' });
    
    // Verify we're back on original branch
    const finalBranch = getCurrentBranch();
    if (finalBranch !== currentBranch) {
      console.error(`[ERROR] Branch mismatch! Expected ${currentBranch}, got ${finalBranch}`);
      console.error(`[MANUAL] Run: git checkout ${currentBranch}`);
    } else {
      console.log(`[OK] Returned to original branch: ${currentBranch}`);
    }
    
    // CRITICAL: Remove synced files from main branch to keep it minimal
    // This ensures main only has essential docs, and devlog has full docs
    if (currentBranch === 'main' && docFiles.length > 0 && !dryRun) {
      console.log('\n[REMOVE] Removing documentation files from main branch...');
      console.log('         (Keeping essential files only - see essential_docs_whitelist.json)');
      
      // Get list of files that should be removed from main
      // (files that were synced to devlog and are not in essential whitelist)
      const essentialFiles = whitelist.files || [];
      const essentialDirs = whitelist.directories_keep_in_main || [];
      
      const filesToRemove = docFiles.filter(docFile => {
        // Skip if file is in essential list
        if (essentialFiles.includes(docFile)) {
          return false;
        }
        
        // Skip if file is in essential directory
        const inEssentialDir = essentialDirs.some(dir => {
          const normalizedDir = dir.replace(/\/$/, '');
          return docFile.startsWith(normalizedDir + '/') || docFile === normalizedDir;
        });
        if (inEssentialDir) {
          return false;
        }
        
        // File should be removed from main (it's now exclusively in devlog)
        return true;
      });
      
      if (filesToRemove.length > 0) {
        console.log(`  Found ${filesToRemove.length} files to remove from main`);
        
        // Remove files from main
        let removedCount = 0;
        for (const fileToRemove of filesToRemove) {
          const filePath = path.join(ROOT_DIR, fileToRemove);
          if (fs.existsSync(filePath)) {
            try {
              // Try git rm first (for tracked files)
              execSync(`git rm "${fileToRemove}"`, { 
                cwd: ROOT_DIR, 
                stdio: 'pipe' 
              });
              removedCount++;
              console.log(`  [REMOVED] ${fileToRemove}`);
            } catch (err) {
              // File might not be tracked, try regular delete
              try {
                fs.unlinkSync(filePath);
                removedCount++;
                console.log(`  [DELETED] ${fileToRemove} (was untracked)`);
              } catch (deleteErr) {
                console.warn(`  [WARN] Could not remove ${fileToRemove}: ${deleteErr.message}`);
              }
            }
          }
        }
        
        // Commit removal with matching message pattern (avoids triggering version bump)
        // Check if there are staged changes (git rm) or unstaged changes (deleted files)
        let hasStagedChanges = false;
        let hasUnstagedChanges = false;
        
        try {
          execSync('git diff --cached --quiet', { cwd: ROOT_DIR, stdio: 'pipe' });
        } catch {
          hasStagedChanges = true;
        }
        
        try {
          execSync('git diff --quiet', { cwd: ROOT_DIR, stdio: 'pipe' });
        } catch {
          hasUnstagedChanges = true;
        }
        
        if (hasStagedChanges || hasUnstagedChanges) {
          // Stage any unstaged deletions
          if (hasUnstagedChanges) {
            try {
              execSync('git add -u', { cwd: ROOT_DIR, stdio: 'pipe' });
            } catch (err) {
              console.warn(`[WARN] Could not stage deletions: ${err.message}`);
            }
          }
          
          // Commit removal with matching message pattern (avoids triggering version bump)
          const removeCommitMessage = `chore(main): remove docs moved to devlog

Removed ${removedCount} documentation files from main branch.
These files are now exclusively in devlog branch.
Generated: ${new Date().toISOString()}`;
          
          execSync(`git commit -m "${removeCommitMessage}"`, {
            cwd: ROOT_DIR,
            stdio: 'inherit'
          });
          console.log(`[OK] Committed removal of ${removedCount} files from main`);
        } else {
          console.log('[INFO] No files staged for removal (already removed or essential)');
        }
      } else {
        console.log('[INFO] No files to remove from main (all are essential)');
      }
    } else if (dryRun && currentBranch === 'main' && docFiles.length > 0) {
      console.log('\n[DRY RUN] Would remove documentation files from main branch');
      console.log('          (Files synced to devlog that are not essential)');
    }
    
    // Restore stash if there was one
    try {
      execSync('git stash pop', { cwd: ROOT_DIR, stdio: 'pipe' });
    } catch {
      // No stash to restore
    }
    
    console.log(`\n✅ Successfully synced ${docFiles.length} files to devlog branch`);
    if (currentBranch === 'main' && !dryRun) {
      console.log(`✅ Removed non-essential docs from main branch (keeps main minimal)`);
    }
    originalBranch = null; // Clear tracking after success
    return true;
    
  } catch (err) {
    console.error(`\n❌ Error during sync: ${err.message}`);
    // Try to return to original branch
    cleanupOnExit();
    return false;
  }
}

async function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes('--dry-run');
  
  const success = await syncToDevlog(dryRun);
  process.exit(success ? 0 : 1);
}

if (require.main === module) {
  main();
}

module.exports = { syncToDevlog, loadWhitelist, getDocFilesToSync };

