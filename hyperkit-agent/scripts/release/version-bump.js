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
  
  console.log(`\n📦 Bumping ${type} version\n`);
  
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
  
  // Commit changes
  if (autoCommit) {
    const files = [VERSION_FILE, PACKAGE_JSON];
    if (fs.existsSync(PYPROJECT_TOML)) {
      files.push(PYPROJECT_TOML);
    }
    
    if (gitCommit(files, `chore: bump version to ${newVersion}`)) {
      console.log(`\n✅ Committed version bump: ${newVersion}`);
    } else {
      console.log(`\n⚠️  No changes to commit`);
    }
  } else {
    console.log(`\n📝 Next steps:`);
    console.log(`   1. Review changes: git diff`);
    console.log(`   2. Commit: git add VERSION package.json hyperkit-agent/pyproject.toml`);
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
  validateVersionGap
};

