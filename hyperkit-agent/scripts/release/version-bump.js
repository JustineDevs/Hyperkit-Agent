#!/usr/bin/env node
/**
 * Version Bump Script
 * 
 * Handles semantic versioning (patch/minor/major) and updates:
 * - VERSION file (root)
 * - package.json version
 * - pyproject.toml version
 * 
 * Automatically calls update-changelog.js and sync-to-devlog.js after bump.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// ROOT_DIR is the repository root (HyperAgent/)
// This script is in hyperkit-agent/scripts/release/, so go up 3 levels
const ROOT_DIR = path.resolve(__dirname, '../../..');
const VERSION_FILE = path.join(ROOT_DIR, 'VERSION');
const PACKAGE_JSON = path.join(ROOT_DIR, 'package.json');
const PYPROJECT_TOML = path.join(ROOT_DIR, 'hyperkit-agent/pyproject.toml');

function getCurrentVersion() {
  try {
    if (fs.existsSync(VERSION_FILE)) {
      return fs.readFileSync(VERSION_FILE, 'utf8').trim();
    }
    // Fallback to package.json
    const pkg = JSON.parse(fs.readFileSync(PACKAGE_JSON, 'utf8'));
    return pkg.version;
  } catch (err) {
    console.error('❌ Could not read current version');
    process.exit(1);
  }
}

function bumpVersion(currentVersion, type) {
  const [major, minor, patch] = currentVersion.split('.').map(Number);
  
  switch (type) {
    case 'major':
      return `${major + 1}.0.0`;
    case 'minor':
      return `${major}.${minor + 1}.0`;
    case 'patch':
      return `${major}.${minor}.${patch + 1}`;
    default:
      throw new Error(`Invalid version type: ${type}. Use patch, minor, or major`);
  }
}

function updateVersionFile(newVersion) {
  fs.writeFileSync(VERSION_FILE, newVersion + '\n', 'utf8');
  console.log(`✅ Updated VERSION: ${newVersion}`);
}

function updatePackageJson(newVersion) {
  const pkg = JSON.parse(fs.readFileSync(PACKAGE_JSON, 'utf8'));
  pkg.version = newVersion;
  fs.writeFileSync(PACKAGE_JSON, JSON.stringify(pkg, null, 2) + '\n', 'utf8');
  console.log(`✅ Updated package.json: ${newVersion}`);
}

function updatePyprojectToml(newVersion) {
  if (!fs.existsSync(PYPROJECT_TOML)) {
    console.warn('⚠️  pyproject.toml not found, skipping');
    return;
  }
  
  let content = fs.readFileSync(PYPROJECT_TOML, 'utf8');
  // Match version = "x.y.z" or version = 'x.y.z'
  content = content.replace(
    /version\s*=\s*["']\d+\.\d+\.\d+["']/,
    `version = "${newVersion}"`
  );
  fs.writeFileSync(PYPROJECT_TOML, content, 'utf8');
  console.log(`✅ Updated pyproject.toml: ${newVersion}`);
}

function gitCommit(files, message) {
  try {
    for (const file of files) {
      execSync(`git add "${file}"`, { cwd: ROOT_DIR, stdio: 'pipe' });
    }
    execSync(`git commit -m "${message}"`, { cwd: ROOT_DIR, stdio: 'pipe' });
    return true;
  } catch (err) {
    if (err.message.includes('nothing to commit')) {
      return false;
    }
    console.warn(`⚠️  Could not commit: ${err.message}`);
    return false;
  }
}

function getRemoteVersion(branch = 'origin/main') {
  /**
   * Fetch version from remote repository.
   * Returns null if remote is not available or fetch fails.
   */
  try {
    // Try to fetch remote version from VERSION file
    try {
      // Fetch latest from remote (without merging)
      execSync('git fetch origin main --quiet', { 
        cwd: ROOT_DIR, 
        stdio: 'pipe',
        timeout: 10000  // 10 second timeout
      });
    } catch (fetchErr) {
      // Remote might not be available, that's OK for local-only workflows
      return null;
    }
    
    // Try to get version from remote branch
    try {
      const remoteVersion = execSync(`git show ${branch}:VERSION`, {
        cwd: ROOT_DIR,
        encoding: 'utf8',
        stdio: 'pipe',
        timeout: 5000
      }).trim();
      
      if (remoteVersion && /^\d+\.\d+\.\d+$/.test(remoteVersion)) {
        return remoteVersion;
      }
    } catch (err) {
      // Try package.json as fallback
      try {
        const remotePackageJson = execSync(`git show ${branch}:package.json`, {
          cwd: ROOT_DIR,
          encoding: 'utf8',
          stdio: 'pipe',
          timeout: 5000
        });
        const pkg = JSON.parse(remotePackageJson);
        if (pkg.version && /^\d+\.\d+\.\d+$/.test(pkg.version)) {
          return pkg.version;
        }
      } catch (err2) {
        // Remote branch might not exist or file doesn't exist
        return null;
      }
    }
    
    return null;
  } catch (err) {
    // Remote not available or network error - that's OK for local-only workflows
    return null;
  }
}

function compareVersions(v1, v2) {
  /**
   * Compare two semantic versions.
   * Returns: 1 if v1 > v2, -1 if v1 < v2, 0 if equal
   */
  const [m1, n1, p1] = v1.split('.').map(Number);
  const [m2, n2, p2] = v2.split('.').map(Number);
  
  if (m1 !== m2) return m1 > m2 ? 1 : -1;
  if (n1 !== n2) return n1 > n2 ? 1 : -1;
  if (p1 !== p2) return p1 > p2 ? 1 : -1;
  return 0;
}

function calculateVersionGap(localVersion, remoteVersion) {
  /**
   * Calculate the gap between local and remote versions.
   * Returns: { major: 0, minor: 0, patch: 0, total: 0 }
   */
  const [lm, ln, lp] = localVersion.split('.').map(Number);
  const [rm, rn, rp] = remoteVersion.split('.').map(Number);
  
  return {
    major: lm - rm,
    minor: ln - rn,
    patch: lp - rp,
    total: (lm * 10000) + (ln * 100) + lp - ((rm * 10000) + (rn * 100) + rp)
  };
}

function checkUncommittedFiles() {
  /**
   * Check for uncommitted files: untracked, modified, and staged.
   * Returns: { untracked: [], modified: [], staged: [] }
   */
  try {
    const statusOutput = execSync('git status --porcelain', {
      cwd: ROOT_DIR,
      encoding: 'utf8',
      stdio: 'pipe'
    }).trim();
    
    if (!statusOutput) {
      return { untracked: [], modified: [], staged: [] };
    }
    
    const untracked = [];
    const modified = [];
    const staged = [];
    
    const lines = statusOutput.split('\n');
    for (const line of lines) {
      if (!line.trim()) continue;
      
      const status = line.substring(0, 2);
      const filename = line.substring(3).trim();
      
      // Skip lib/ submodule changes
      if (filename.includes('/lib/') || filename.includes('\\lib\\')) {
        continue;
      }
      
      // Categorize files
      if (status === '??') {
        // Untracked file
        untracked.push(filename);
      } else if (status[1] === 'M' || status[1] === 'D') {
        // Modified or deleted in working tree
        modified.push(filename);
      } else if (status[0] === 'M' || status[0] === 'A' || status[0] === 'D' || status[0] === 'R') {
        // Staged changes
        staged.push(filename);
      }
    }
    
    return { untracked, modified, staged };
  } catch (err) {
    // If git command fails, assume no uncommitted files
    return { untracked: [], modified: [], staged: [] };
  }
}

function stageAllModifiedFiles() {
  /**
   * Stage all modified, deleted, and untracked files.
   * Returns: number of files staged
   */
  try {
    const statusOutput = execSync('git status --porcelain', {
      cwd: ROOT_DIR,
      encoding: 'utf8',
      stdio: 'pipe'
    }).trim();
    
    if (!statusOutput) {
      return 0;
    }
    
    // Get already staged files
    let alreadyStaged = new Set();
    try {
      const stagedOutput = execSync('git diff --cached --name-only', {
        cwd: ROOT_DIR,
        encoding: 'utf8',
        stdio: 'pipe'
      }).trim();
      if (stagedOutput) {
        alreadyStaged = new Set(stagedOutput.split('\n'));
      }
    } catch (err) {
      // No staged files
    }
    
    let stagedCount = 0;
    const lines = statusOutput.split('\n');
    
    for (const line of lines) {
      if (!line.trim()) continue;
      
      const status = line.substring(0, 2);
      const filename = line.substring(3).trim();
      
      // Skip lib/ submodule changes
      if (filename.includes('/lib/') || filename.includes('\\lib\\')) {
        continue;
      }
      
      // Skip if already staged
      if (alreadyStaged.has(filename)) {
        continue;
      }
      
      // Stage if file is modified (M), deleted (D), or untracked (?)
      if (status[1] === 'M' || status[1] === 'D' || status[1] === '?') {
        try {
          execSync(`git add "${filename}"`, {
            cwd: ROOT_DIR,
            stdio: 'pipe'
          });
          stagedCount++;
        } catch (err) {
          // Skip files that can't be staged
        }
      }
    }
    
    return stagedCount;
  } catch (err) {
    return 0;
  }
}

function validateVersionGap(localVersion, remoteVersion, bumpType) {
  /**
   * Validate that the version gap is reasonable.
   * Returns: { valid: boolean, warning: string | null }
   */
  if (!remoteVersion) {
    // No remote version available - allow local bump
    return { valid: true, warning: null };
  }
  
  const comparison = compareVersions(localVersion, remoteVersion);
  
  if (comparison < 0) {
    // Local is behind remote - this is a problem
    return {
      valid: false,
      warning: `⚠️  LOCAL VERSION BEHIND REMOTE!\n` +
               `   Local:  ${localVersion}\n` +
               `   Remote: ${remoteVersion}\n` +
               `   \n` +
               `   You need to pull latest changes first:\n` +
               `   git pull origin main\n` +
               `   \n` +
               `   Then re-run the version bump.`
    };
  }
  
  if (comparison === 0) {
    // Versions are equal - normal bump scenario
    return { valid: true, warning: null };
  }
  
  // Local is ahead of remote - calculate gap
  const gap = calculateVersionGap(localVersion, remoteVersion);
  
  // Check if gap is too large for the bump type
  const maxAllowedGap = {
    patch: 10,  // Allow up to 10 patch versions ahead
    minor: 5,   // Allow up to 5 minor versions ahead
    major: 2    // Allow up to 2 major versions ahead
  };
  
  const maxGap = maxAllowedGap[bumpType] || 10;
  
  if (gap.total > maxGap) {
    return {
      valid: true,  // Allow but warn
      warning: `⚠️  VERSION GAP DETECTED\n` +
               `   Local:  ${localVersion}\n` +
               `   Remote: ${remoteVersion}\n` +
               `   Gap:    ${gap.major > 0 ? gap.major + ' major' : ''} ${gap.minor > 0 ? gap.minor + ' minor' : ''} ${gap.patch > 0 ? gap.patch + ' patch' : ''}\n` +
               `   \n` +
               `   This is a significant gap. Consider pushing your changes:\n` +
               `   git push origin main\n` +
               `   \n` +
               `   Or if you're working locally, this is OK.`
    };
  }
  
  return { valid: true, warning: null };
}

function main() {
  const type = process.argv[2];
  
  if (!type || !['patch', 'minor', 'major'].includes(type)) {
    console.error('❌ Usage: node version-bump.js [patch|minor|major]');
    process.exit(1);
  }
  
  const autoCommit = !process.argv.includes('--no-commit');
  const skipRemoteCheck = process.argv.includes('--skip-remote-check');
  const skipUncommittedCheck = process.argv.includes('--skip-uncommitted-check');
  
  console.log(`\n📦 Bumping ${type} version\n`);
  
  // Check for uncommitted files before version bump
  if (!skipUncommittedCheck) {
    console.log('🔍 Checking for uncommitted files...');
    const { untracked, modified, staged } = checkUncommittedFiles();
    const hasUncommitted = untracked.length > 0 || modified.length > 0;
    
    if (hasUncommitted) {
      console.log('\n⚠️  Uncommitted files detected before version bump:');
      
      if (untracked.length > 0) {
        console.log(`   Untracked files (${untracked.length}):`);
        for (const f of untracked.slice(0, 5)) {
          console.log(`     + ${f}`);
        }
        if (untracked.length > 5) {
          console.log(`     ... and ${untracked.length - 5} more`);
        }
      }
      
      if (modified.length > 0) {
        console.log(`   Modified files (${modified.length}):`);
        for (const f of modified.slice(0, 5)) {
          console.log(`     M ${f}`);
        }
        if (modified.length > 5) {
          console.log(`     ... and ${modified.length - 5} more`);
        }
      }
      
      console.log('\n   Auto-staging uncommitted files...');
      const autoStaged = stageAllModifiedFiles();
      if (autoStaged > 0) {
        console.log(`   ✅ Auto-staged ${autoStaged} file(s)`);
        console.log('   These files will be committed with the version bump\n');
      } else {
        console.log('   [INFO] No files were staged (may already be staged)\n');
      }
    } else {
      console.log('   ✅ Working tree is clean\n');
    }
  } else {
    console.log('ℹ️  Skipping uncommitted files check (--skip-uncommitted-check)\n');
  }
  
  // Get current local version
  const currentVersion = getCurrentVersion();
  console.log(`Current local version: ${currentVersion}`);
  
  // Check remote version (if available)
  if (!skipRemoteCheck) {
    console.log(`\n🔍 Checking remote version...`);
    const remoteVersion = getRemoteVersion();
    
    if (remoteVersion) {
      console.log(`Remote version: ${remoteVersion}`);
      
      // Validate version gap
      const validation = validateVersionGap(currentVersion, remoteVersion, type);
      
      if (!validation.valid) {
        console.error(`\n${validation.warning}`);
        process.exit(1);
      }
      
      if (validation.warning) {
        console.warn(`\n${validation.warning}\n`);
      }
      
      // Show comparison
      const comparison = compareVersions(currentVersion, remoteVersion);
      if (comparison > 0) {
        console.log(`ℹ️  Local is ${comparison > 0 ? 'ahead' : 'behind'} of remote (this is OK for local development)`);
      } else if (comparison === 0) {
        console.log(`✅ Local and remote versions match`);
      }
    } else {
      console.log(`ℹ️  Remote version not available (working locally or no remote configured)`);
      console.log(`   Local version will be used for bumping`);
    }
  } else {
    console.log(`ℹ️  Skipping remote version check (--skip-remote-check)`);
  }
  
  console.log(`\n📈 Calculating new version...`);
  const newVersion = bumpVersion(currentVersion, type);
  console.log(`New version: ${newVersion}\n`);
  
  // Update all version files
  updateVersionFile(newVersion);
  updatePackageJson(newVersion);
  updatePyprojectToml(newVersion);
  
  // Commit changes (including all staged files from auto-staging)
  if (autoCommit) {
    // First, stage version files explicitly
    const files = [VERSION_FILE, PACKAGE_JSON];
    if (fs.existsSync(PYPROJECT_TOML)) {
      files.push(PYPROJECT_TOML);
    }
    
    // Stage all other modified files (from auto-staging)
    const additionalStaged = stageAllModifiedFiles();
    
    // Commit all staged files
    const commitMessage = `chore: version bump to ${newVersion} [auto-commit]\n\n` +
                         `Bumped ${type} version: ${currentVersion} → ${newVersion}\n` +
                         (additionalStaged > 0 ? `Auto-committed ${additionalStaged} additional file(s) from workflow.\n` : '') +
                         `\nGenerated: ${new Date().toISOString()}`;
    
    if (gitCommit(files, commitMessage)) {
      console.log(`\n✅ Committed version bump: ${newVersion}`);
      if (additionalStaged > 0) {
        console.log(`   Also committed ${additionalStaged} additional file(s) from workflow`);
      }
    } else {
      // Try to commit just the version files if the combined commit failed
      if (gitCommit(files, `chore: bump version to ${newVersion}`)) {
        console.log(`\n✅ Committed version bump: ${newVersion}`);
        // Try to commit remaining files
        const remainingStaged = stageAllModifiedFiles();
        if (remainingStaged > 0) {
          const remainingCommitMessage = `chore: auto-commit workflow files after version bump\n\n` +
                                       `Auto-committed ${remainingStaged} file(s) after version bump.\n` +
                                       `Generated: ${new Date().toISOString()}`;
          try {
            execSync(`git commit -m "${remainingCommitMessage}"`, {
              cwd: ROOT_DIR,
              stdio: 'pipe'
            });
            console.log(`   ✅ Also committed ${remainingStaged} workflow file(s)`);
          } catch (err) {
            console.log(`   ⚠️  Could not commit remaining files: ${err.message}`);
          }
        }
      } else {
        console.log(`\n⚠️  No changes to commit`);
      }
    }
  } else {
    console.log(`\n📝 Next steps:`);
    console.log(`   1. Review changes: git diff`);
    console.log(`   2. Stage all files: git add .`);
    console.log(`   3. Commit: git commit -m "chore: bump version to ${newVersion}"`);
  }
  
  // Run post-bump scripts
  console.log(`\n🔄 Running post-bump scripts...\n`);
  
  try {
    // Cleanup duplicate meta files (enforce single source of truth)
    console.log('🧹 Cleaning up duplicate meta files...');
    execSync('node hyperkit-agent/scripts/release/cleanup-meta-dupes.js', {
      cwd: ROOT_DIR,
      stdio: 'inherit'
    });
  } catch (err) {
    console.warn('⚠️  Failed to cleanup duplicates:', err.message);
  }
  
  try {
    // Update changelog (pass new version explicitly)
    console.log('\n📝 Updating CHANGELOG.md...');
    execSync(`node hyperkit-agent/scripts/release/update-changelog.js ${newVersion}`, {
      cwd: ROOT_DIR,
      stdio: 'inherit'
    });
  } catch (err) {
    console.warn('⚠️  Failed to update changelog:', err.message);
  }
  
  try {
    // Update docs
    console.log('\n📚 Updating documentation...');
    execSync('node hyperkit-agent/scripts/release/update-docs.js', {
      cwd: ROOT_DIR,
      stdio: 'inherit'
    });
  } catch (err) {
    console.warn('⚠️  Failed to update docs:', err.message);
  }
  
  try {
    // Sync to devlog
    console.log('\n🔄 Syncing to devlog branch...');
    execSync('node hyperkit-agent/scripts/release/sync-to-devlog.js', {
      cwd: ROOT_DIR,
      stdio: 'inherit'
    });
  } catch (err) {
    console.warn('⚠️  Failed to sync to devlog:', err.message);
  }
  
  console.log(`\n✅ Version bump complete: ${currentVersion} → ${newVersion}`);
  
  // Final check for uncommitted files
  if (!skipUncommittedCheck) {
    console.log('\n🔍 Final check for uncommitted files...');
    const finalCheck = checkUncommittedFiles();
    const hasFinalUncommitted = finalCheck.untracked.length > 0 || finalCheck.modified.length > 0;
    
    if (hasFinalUncommitted) {
      console.log('⚠️  Uncommitted files detected after version bump:');
      if (finalCheck.untracked.length > 0) {
        console.log(`   Untracked: ${finalCheck.untracked.length} file(s)`);
      }
      if (finalCheck.modified.length > 0) {
        console.log(`   Modified: ${finalCheck.modified.length} file(s)`);
      }
      
      // Try to auto-stage and commit remaining files
      console.log('\n   Attempting to auto-commit remaining files...');
      const remainingStaged = stageAllModifiedFiles();
      if (remainingStaged > 0) {
        try {
          const remainingCommitMessage = `chore: auto-commit remaining files after version bump\n\n` +
                                       `Auto-committed ${remainingStaged} remaining file(s) after version bump.\n` +
                                       `Generated: ${new Date().toISOString()}`;
          execSync(`git commit -m "${remainingCommitMessage}"`, {
            cwd: ROOT_DIR,
            stdio: 'pipe'
          });
          console.log(`   ✅ Committed ${remainingStaged} remaining file(s)`);
        } catch (err) {
          console.log(`   ⚠️  Could not commit remaining files: ${err.message}`);
          console.log('   Please review and commit manually:');
          console.log('     git status');
          console.log('     git add <files>');
          console.log('     git commit -m "your message"');
        }
      }
    } else {
      console.log('   ✅ Working tree is clean - all files committed');
    }
  }
  
  // Remind about local vs remote version persistence
  if (!skipRemoteCheck) {
    const remoteVersion = getRemoteVersion();
    if (remoteVersion) {
      const newVsRemote = compareVersions(newVersion, remoteVersion);
      if (newVsRemote > 0) {
        console.log(`\n💡 Local version (${newVersion}) is ahead of remote (${remoteVersion})`);
        console.log(`   ✅ This version will persist in your local commits`);
        console.log(`   📤 To sync to remote: git push origin main`);
        console.log(`   🔄 Or continue working locally - version stays bumped until you push`);
      } else if (newVsRemote === 0) {
        console.log(`\n💡 Local and remote versions are now aligned`);
        console.log(`   📤 Push to sync: git push origin main`);
      }
    } else {
      console.log(`\n💡 Version bumped locally (${newVersion})`);
      console.log(`   ✅ This version will persist in your local commits`);
      console.log(`   📤 When ready, push to remote: git push origin main`);
    }
  } else {
    console.log(`\n💡 Version bumped locally (${newVersion})`);
    console.log(`   ✅ This version will persist in your local commits`);
  }
  
  console.log(`\n💡 Tip: Run 'npm run hygiene' to sync documentation to devlog branch`);
  console.log();
}

if (require.main === module) {
  main();
}

module.exports = { 
  getCurrentVersion, 
  bumpVersion, 
  getRemoteVersion,
  compareVersions,
  calculateVersionGap,
  validateVersionGap,
  checkUncommittedFiles,
  stageAllModifiedFiles
};

