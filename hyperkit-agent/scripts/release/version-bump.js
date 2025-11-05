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

function main() {
  const type = process.argv[2];
  
  if (!type || !['patch', 'minor', 'major'].includes(type)) {
    console.error('❌ Usage: node version-bump.js [patch|minor|major]');
    process.exit(1);
  }
  
  const autoCommit = !process.argv.includes('--no-commit');
  
  console.log(`\n📦 Bumping ${type} version\n`);
  
  const currentVersion = getCurrentVersion();
  console.log(`Current version: ${currentVersion}`);
  
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
    // Update changelog
    console.log('\n📝 Updating CHANGELOG.md...');
    execSync('node hyperkit-agent/scripts/release/update-changelog.js', {
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
  console.log(`\n💡 Tip: Run 'npm run hygiene' to sync documentation to devlog branch`);
  console.log();
}

if (require.main === module) {
  main();
}

module.exports = { getCurrentVersion, bumpVersion };

