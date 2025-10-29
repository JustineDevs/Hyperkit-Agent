#!/usr/bin/env node
/**
 * Update Documentation
 * 
 * Updates documentation files with latest version, dates, and commit info.
 * Ensures all doc references are current and accurate.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '../..');
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

function getGitInfo() {
  try {
    const commit = execSync('git rev-parse --short HEAD', {
      encoding: 'utf8',
      cwd: ROOT_DIR
    }).trim();
    
    const date = execSync('git log -1 --format=%cd --date=short', {
      encoding: 'utf8',
      cwd: ROOT_DIR
    }).trim();
    
    return { commit, date };
  } catch (err) {
    return { commit: 'unknown', date: new Date().toISOString().split('T')[0] };
  }
}

function updateDocBadges(filePath, autoCommit = false) {
  if (!fs.existsSync(filePath)) {
    return false;
  }
  
  const { commit, date } = getGitInfo();
  const version = getCurrentVersion();
  let content = fs.readFileSync(filePath, 'utf8');
  let updated = false;
  
  // Create new badge content
  const newBadge = `<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: ${version}  
**Last Verified**: ${date}  
**Commit**: \`${commit}\`  
**Branch**: \`main\`  
<!-- AUDIT_BADGE_END -->`;
  
  // Check if badge already exists
  const badgeRegex = /<!-- AUDIT_BADGE_START -->[\s\S]*?<!-- AUDIT_BADGE_END -->/g;
  
  if (badgeRegex.test(content)) {
    // Update existing badge
    content = content.replace(badgeRegex, newBadge);
    updated = true;
  } else {
    // Add badge at the beginning of the file (after frontmatter if exists)
    // Check for YAML frontmatter
    const frontmatterRegex = /^---\n[\s\S]*?\n---\n/;
    if (frontmatterRegex.test(content)) {
      // Insert after frontmatter
      content = content.replace(frontmatterRegex, (match) => match + '\n' + newBadge + '\n\n');
      updated = true;
    } else {
      // Insert at the beginning
      content = newBadge + '\n\n' + content;
      updated = true;
    }
  }
  
  // Update version references in content (but not in badges)
  // Only update standalone version strings, not those in badges
  const versionRegex = /(version[:\s]+["']?)([\d.]+)(["']?)/gi;
  const lines = content.split('\n');
  let needsVersionUpdate = false;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    // Skip badge lines
    if (line.includes('AUDIT_BADGE') || line.includes('**Version**')) {
      continue;
    }
    
    if (versionRegex.test(line)) {
      const updatedLine = line.replace(/(version[:\s]+["']?)([\d.]+)(["']?)/gi, (match, prefix, oldVersion, suffix) => {
        if (oldVersion.match(/^\d+\.\d+\.\d+$/)) {
          needsVersionUpdate = true;
          return prefix + version + suffix;
        }
        return match;
      });
      if (updatedLine !== line) {
        lines[i] = updatedLine;
        updated = true;
      }
    }
  }
  
  if (needsVersionUpdate) {
    content = lines.join('\n');
  }
  
  if (updated) {
    fs.writeFileSync(filePath, content, 'utf8');
    
    if (autoCommit) {
      gitAdd(filePath);
      const relativePath = path.relative(ROOT_DIR, filePath);
      gitCommit([filePath], `docs: update audit badge in ${relativePath}`);
    }
    
    return true;
  }
  
  return false;
}

// Specific documentation files that need audit badge updates
const TARGET_DOC_FILES = [
  // EXECUTION docs
  'docs/EXECUTION/CRITICAL_FIXES_APPLIED.md',
  'docs/EXECUTION/DEMO_SCRIPT.md',
  'docs/EXECUTION/DISASTER_RECOVERY.md',
  'docs/EXECUTION/GENERATED_FILES.md',
  'docs/EXECUTION/KNOWN_ISSUES.md',
  'docs/EXECUTION/KNOWN_LIMITATIONS.md',
  'docs/EXECUTION/MYTHRIL_WINDOWS_INSTALLATION.md',
  'docs/EXECUTION/workflow-command.md',
  'docs/EXECUTION/PRE_DEMO_CHECKLIST.md',
  'docs/EXECUTION/README.md',
  
  // GUIDE docs
  'docs/GUIDE/CHANGES_SUMMARY.md',
  'docs/GUIDE/CONFIGURATION_GUIDE.md',
  'docs/GUIDE/MIGRATION_GUIDE.md',
  'docs/GUIDE/QUICK_START.md',
  'docs/GUIDE/PINATA_SETUP_GUIDE.md',
  'docs/GUIDE/IPFS_RAG_GUIDE.md',
  
  // INTEGRATION docs
  'docs/INTEGRATION/ALITH_INTEGRATION_PROGRESS.md',
  'docs/INTEGRATION/ALITH_SDK_INTEGRATION_ROADMAP.md',
  'docs/INTEGRATION/WALLET_SECURITY_EXTENSIONS.md',
  'docs/INTEGRATION/SAMPLE_INTEGRATION_SCRIPTS.md',
  
  // POLICIES docs
  'docs/POLICIES/DRIFT_PREVENTION_POLICY.md',
  
  // TEAM docs
  'docs/TEAM/ARCHITECTURE_DIAGRAMS.md',
  'docs/TEAM/CPOO_DELIVERY_SUMMARY.md',
  'docs/TEAM/CPOO_INTEGRATION_GUIDE.md',
  'docs/TEAM/DEVELOPER_GUIDE.md',
  'docs/TEAM/ENVIRONMENT_SETUP.md',
  'docs/TEAM/FOUNDRY_INTEGRATION_REPORT.md',
  'docs/TEAM/INTEGRATION_REPORT.md',
  'docs/TEAM/ISSUE_ASSESSMENT_AND_FIXES.md',
  'docs/TEAM/TEAM_COORDINATION_GUIDE.md',
  'docs/TEAM/LAZAI_REGISTRATION_REQUEST.md',
  'docs/TEAM/README.md',
  'docs/TEAM/TECHNICAL_DOCUMENTATION.md',
  'docs/TEAM/WORKFLOW_BEHAVIOR_REPORT.md'
];

function processDocsDirectory(autoCommit = false) {
  let updatedCount = 0;
  const updatedFiles = [];
  
  // Process each target file specifically
  for (const relativePath of TARGET_DOC_FILES) {
    const filePath = path.join(ROOT_DIR, relativePath);
    
    if (!fs.existsSync(filePath)) {
      console.log(`⚠️  File not found: ${relativePath}`);
      continue;
    }
    
    if (updateDocBadges(filePath, autoCommit)) {
      updatedCount++;
      updatedFiles.push(filePath);
      console.log(`✅ Updated ${relativePath}${autoCommit ? ' (committed)' : ''}`);
    }
  }
  
  return { count: updatedCount, files: updatedFiles };
}

function updateRootReadme(autoCommit = false) {
  const readmePath = path.join(ROOT_DIR, 'README.md');
  if (!fs.existsSync(readmePath)) {
    return false;
  }
  
  return updateDocBadges(readmePath, autoCommit);
}

function main() {
  const autoCommit = !process.argv.includes('--no-commit');
  
  console.log(`\n📚 Updating documentation files\n`);
  console.log(`   Target files: ${TARGET_DOC_FILES.length} documentation files\n`);
  
  if (autoCommit) {
    console.log(`📝 Auto-commit: ENABLED (use --no-commit to disable)\n`);
  } else {
    console.log(`📝 Auto-commit: DISABLED\n`);
  }
  
  let total = 0;
  let readmeUpdated = false;
  const allUpdatedFiles = [];
  
  // Update root README
  if (updateRootReadme(autoCommit)) {
    console.log(`✅ Updated README.md${autoCommit ? ' (committed)' : ''}`);
    readmeUpdated = true;
    total++;
    allUpdatedFiles.push(path.join(ROOT_DIR, 'README.md'));
  }
  
  // Update all target documentation files (add/update audit badges)
  const { count: docsCount, files: docFiles } = processDocsDirectory(autoCommit);
  total += docsCount;
  allUpdatedFiles.push(...docFiles);
  
  if (total === 0) {
    console.log(`ℹ️  No documentation files needed updates`);
  } else {
    console.log(`\n✅ Updated ${total} documentation file(s)`);
    console.log(`   - Root README: ${readmeUpdated ? 1 : 0}`);
    console.log(`   - Target docs: ${docsCount}/${TARGET_DOC_FILES.length}`);
    
    if (autoCommit && allUpdatedFiles.length > 0) {
      console.log(`\n📝 All files have been committed individually`);
      console.log(`   Use 'git log --oneline -${total}' to see commits`);
    } else if (!autoCommit) {
      console.log(`\n📝 Next steps:`);
      console.log(`   1. Review changes: git diff`);
      console.log(`   2. Commit: git add docs/ README.md && git commit -m "docs: update audit badges"`);
    }
  }
  
  console.log();
}

if (require.main === module) {
  main();
}

module.exports = { 
  updateDocBadges, 
  processDocsDirectory,
  TARGET_DOC_FILES 
};

