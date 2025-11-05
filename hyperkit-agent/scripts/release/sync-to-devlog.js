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
    console.log('[ERROR] Working tree has uncommitted changes');
    console.log('   Please commit or stash changes before syncing to devlog');
    originalBranch = null; // Clear tracking
    return false;
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
    
    // Restore stash if there was one
    try {
      execSync('git stash pop', { cwd: ROOT_DIR, stdio: 'pipe' });
    } catch {
      // No stash to restore
    }
    
    console.log(`\n✅ Successfully synced ${docFiles.length} files to devlog branch`);
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

