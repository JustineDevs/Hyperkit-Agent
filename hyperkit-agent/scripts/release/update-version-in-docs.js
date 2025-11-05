#!/usr/bin/env node
/**
 * Update Version in All Documentation
 * 
 * Syncs version number across all documentation files:
 * - README.md
 * - CHANGELOG.md
 * - All markdown files with version references
 * - Documentation headers and badges
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '../..');
const VERSION_FILE = path.join(ROOT_DIR, 'VERSION');

function getCurrentVersion() {
  try {
    if (fs.existsSync(VERSION_FILE)) {
      return fs.readFileSync(VERSION_FILE, 'utf8').trim();
    }
    const pkg = JSON.parse(fs.readFileSync(path.join(ROOT_DIR, 'package.json'), 'utf8'));
    return pkg.version;
  } catch (err) {
    console.error('❌ Could not read current version');
    process.exit(1);
  }
}

function findMarkdownFiles(dir, files = []) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    
    // Skip certain directories
    if (entry.isDirectory()) {
      if (['node_modules', '.git', '__pycache__', '.pytest_cache', 'dist', 'build'].includes(entry.name)) {
        continue;
      }
      findMarkdownFiles(fullPath, files);
    } else if (entry.isFile() && entry.name.endsWith('.md')) {
      files.push(fullPath);
    }
  }
  
  return files;
}

function updateVersionInFile(filePath, version) {
  let content = fs.readFileSync(filePath, 'utf8');
  let updated = false;
  
  // Pattern 1: Version badges [![Version](...vX.Y.Z...)]
  const badgePattern = /\[!\[Version\]\([^)]*v\d+\.\d+\.\d+[^)]*\)\]/g;
  if (badgePattern.test(content)) {
    content = content.replace(
      /v\d+\.\d+\.\d+/g,
      `v${version}`
    );
    updated = true;
  }
  
  // Pattern 2: Version: X.Y.Z or Version X.Y.Z
  const versionPattern = /(Version|version):\s*\d+\.\d+\.\d+/g;
  if (versionPattern.test(content)) {
    content = content.replace(
      /(Version|version):\s*\d+\.\d+\.\d+/g,
      `$1: ${version}`
    );
    updated = true;
  }
  
  // Pattern 3: vX.Y.Z in text
  const textVersionPattern = /\bv\d+\.\d+\.\d+\b/g;
  if (textVersionPattern.test(content)) {
    content = content.replace(
      /\bv\d+\.\d+\.\d+\b/g,
      `v${version}`
    );
    updated = true;
  }
  
  // Pattern 4: HyperKit Agent vX.Y.Z
  const agentVersionPattern = /HyperKit Agent v\d+\.\d+\.\d+/gi;
  if (agentVersionPattern.test(content)) {
    content = content.replace(
      /HyperKit Agent v\d+\.\d+\.\d+/gi,
      `HyperKit Agent v${version}`
    );
    updated = true;
  }
  
  if (updated) {
    fs.writeFileSync(filePath, content, 'utf8');
    return true;
  }
  
  return false;
}

function gitAdd(filePath) {
  try {
    const relativePath = path.relative(ROOT_DIR, filePath);
    execSync(`git add "${relativePath}"`, {
      cwd: ROOT_DIR,
      stdio: 'pipe'
    });
    return true;
  } catch (err) {
    return false;
  }
}

function gitCommit(files, message) {
  try {
    for (const file of files) {
      gitAdd(file);
    }
    execSync(`git commit -m "${message}"`, {
      cwd: ROOT_DIR,
      stdio: 'pipe'
    });
    return true;
  } catch (err) {
    if (err.message.includes('nothing to commit')) {
      return false;
    }
    return false;
  }
}

function main() {
  const autoCommit = !process.argv.includes('--no-commit');
  
  console.log(`\n📚 Updating version in all documentation files\n`);
  
  const version = getCurrentVersion();
  console.log(`Current version: ${version}\n`);
  
  // Find all markdown files
  const mdFiles = findMarkdownFiles(ROOT_DIR);
  console.log(`Found ${mdFiles.length} markdown files to check\n`);
  
  const updatedFiles = [];
  
  for (const filePath of mdFiles) {
    // Skip certain files
    const relativePath = path.relative(ROOT_DIR, filePath);
    if (relativePath.includes('node_modules') || relativePath.includes('.git')) {
      continue;
    }
    
    if (updateVersionInFile(filePath, version)) {
      updatedFiles.push(filePath);
      console.log(`✅ Updated: ${relativePath}`);
    }
  }
  
  if (updatedFiles.length === 0) {
    console.log(`ℹ️  No documentation files needed version updates`);
    return;
  }
  
  console.log(`\n✅ Updated ${updatedFiles.length} documentation file(s)`);
  
  if (autoCommit) {
    if (gitCommit(updatedFiles, `docs: update version references to ${version}`)) {
      console.log(`\n✅ Committed version updates`);
    } else {
      console.log(`\n⚠️  No changes to commit`);
    }
  } else {
    console.log(`\n📝 Next steps:`);
    console.log(`   1. Review changes: git diff`);
    console.log(`   2. Commit: git add ${updatedFiles.map(f => path.relative(ROOT_DIR, f)).join(' ')}`);
    console.log(`   3. Commit: git commit -m "docs: update version references to ${version}"`);
  }
  
  console.log();
}

if (require.main === module) {
  main();
}

module.exports = { getCurrentVersion, updateVersionInFile };

