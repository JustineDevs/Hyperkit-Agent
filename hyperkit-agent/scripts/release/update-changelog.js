#!/usr/bin/env node
/**
 * Update CHANGELOG.md
 * 
 * Automatically updates CHANGELOG.md with a new version entry
 * based on git commits since last release.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '../..');
const CHANGELOG_PATH = path.join(ROOT_DIR, 'CHANGELOG.md');
const { getCurrentVersion } = require('./update-version-all.js');

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

function getGitCommitsSinceLastTag() {
  try {
    const lastTag = execSync('git describe --tags --abbrev=0 2>/dev/null || echo ""', {
      encoding: 'utf8',
      cwd: ROOT_DIR
    }).trim();
    
    if (lastTag) {
      const commits = execSync(`git log ${lastTag}..HEAD --pretty=format:"- %s"`, {
        encoding: 'utf8',
        cwd: ROOT_DIR
      }).trim().split('\n').filter(line => line.trim());
      return commits;
    } else {
      // No tags, get last 20 commits
      const commits = execSync('git log -20 --pretty=format:"- %s"', {
        encoding: 'utf8',
        cwd: ROOT_DIR
      }).trim().split('\n').filter(line => line.trim());
      return commits;
    }
  } catch (err) {
    console.warn('⚠️  Could not get git commits, using placeholder');
    return ['- Update changelog manually'];
  }
}

function categorizeCommits(commits) {
  const categories = {
    features: [],
    fixes: [],
    docs: [],
    refactor: [],
    chore: [],
    breaking: []
  };
  
  for (const commit of commits) {
    const lower = commit.toLowerCase();
    
    if (lower.includes('breaking') || lower.includes('!:')) {
      categories.breaking.push(commit);
    } else if (lower.includes('feat') || lower.includes('add') || lower.includes('new')) {
      categories.features.push(commit);
    } else if (lower.includes('fix') || lower.includes('bug')) {
      categories.fixes.push(commit);
    } else if (lower.includes('doc') || lower.includes('readme')) {
      categories.docs.push(commit);
    } else if (lower.includes('refactor') || lower.includes('refactor')) {
      categories.refactor.push(commit);
    } else {
      categories.chore.push(commit);
    }
  }
  
  return categories;
}

function formatChangelogEntry(version, date, categories) {
  let entry = `## [${version}] - ${date}\n\n`;
  
  let hasContent = false;
  
  if (categories.breaking.length > 0) {
    entry += `### 🔥 Breaking Changes\n\n`;
    for (const item of categories.breaking) {
      entry += `${item}\n`;
    }
    entry += '\n';
    hasContent = true;
  }
  
  if (categories.features.length > 0) {
    entry += `### ✨ Added\n\n`;
    for (const item of categories.features) {
      entry += `${item}\n`;
    }
    entry += '\n';
    hasContent = true;
  }
  
  if (categories.fixes.length > 0) {
    entry += `### 🐛 Fixed\n\n`;
    for (const item of categories.fixes) {
      entry += `${item}\n`;
    }
    entry += '\n';
    hasContent = true;
  }
  
  if (categories.refactor.length > 0) {
    entry += `### ♻️ Refactored\n\n`;
    for (const item of categories.refactor) {
      entry += `${item}\n`;
    }
    entry += '\n';
    hasContent = true;
  }
  
  if (categories.docs.length > 0) {
    entry += `### 📚 Documentation\n\n`;
    for (const item of categories.docs) {
      entry += `${item}\n`;
    }
    entry += '\n';
    hasContent = true;
  }
  
  if (categories.chore.length > 0) {
    entry += `### 🔧 Chore\n\n`;
    for (const item of categories.chore.slice(0, 10)) { // Limit to 10
      entry += `${item}\n`;
    }
    if (categories.chore.length > 10) {
      entry += `\n_...and ${categories.chore.length - 10} more_\n`;
    }
    entry += '\n';
    hasContent = true;
  }
  
  if (!hasContent) {
    entry += `### Changes\n\n- Version bump to ${version}\n\n`;
  }
  
  return entry;
}

function updateChangelog(newVersion, autoCommit = false) {
  const date = new Date().toISOString().split('T')[0];
  const commits = getGitCommitsSinceLastTag();
  const categories = categorizeCommits(commits);
  const newEntry = formatChangelogEntry(newVersion, date, categories);
  
  let changelog = '';
  const wasNew = !fs.existsSync(CHANGELOG_PATH);
  
  if (fs.existsSync(CHANGELOG_PATH)) {
    changelog = fs.readFileSync(CHANGELOG_PATH, 'utf8');
    
    // Check if entry already exists
    const versionRegex = new RegExp(`^## \\[${newVersion}\\]`, 'm');
    if (versionRegex.test(changelog)) {
      console.log(`⚠️  Version ${newVersion} already exists in CHANGELOG.md`);
      console.log(`   Review and update manually if needed`);
      return false;
    }
  } else {
    // Create new changelog
    changelog = `# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n`;
  }
  
  // Insert new entry after the header
  const headerEnd = changelog.indexOf('\n\n## [');
  if (headerEnd > 0) {
    changelog = changelog.slice(0, headerEnd) + '\n\n' + newEntry + changelog.slice(headerEnd + 2);
  } else {
    changelog = changelog + '\n' + newEntry;
  }
  
  fs.writeFileSync(CHANGELOG_PATH, changelog);
  console.log(`✅ ${wasNew ? 'Created' : 'Updated'} ${path.relative(ROOT_DIR, CHANGELOG_PATH)}`);
  console.log(`   Added version ${newVersion} entry with ${commits.length} commits`);
  
  if (autoCommit) {
    gitAdd(CHANGELOG_PATH);
    gitCommit([CHANGELOG_PATH], `chore: update CHANGELOG.md for version ${newVersion}`);
    console.log(`   💾 Committed: CHANGELOG.md`);
  }
  
  return true;
}

function main() {
  const versionArg = process.argv[2];
  const autoCommit = !process.argv.includes('--no-commit');
  
  let version;
  if (versionArg) {
    version = versionArg;
  } else {
    version = getCurrentVersion();
  }
  
  console.log(`\n📝 Updating CHANGELOG.md for version ${version}\n`);
  
  if (autoCommit) {
    console.log(`📝 Auto-commit: ENABLED (use --no-commit to disable)\n`);
  } else {
    console.log(`📝 Auto-commit: DISABLED\n`);
  }
  
  if (updateChangelog(version, autoCommit)) {
    console.log(`\n✅ CHANGELOG update complete`);
    
    if (!autoCommit) {
      console.log(`\n📝 Next steps:`);
      console.log(`   1. Review changes: git diff CHANGELOG.md`);
      console.log(`   2. Commit: git add CHANGELOG.md && git commit -m "chore: update CHANGELOG.md for version ${version}"`);
    }
  }
  
  console.log();
}

if (require.main === module) {
  main();
}

module.exports = { updateChangelog };

