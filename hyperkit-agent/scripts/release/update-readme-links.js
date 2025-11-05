#!/usr/bin/env node
/**
 * Update README.md Links for Devlog Branch Strategy
 * 
 * Converts relative links pointing to documentation in devlog branch
 * to GitHub URLs, ensuring links work from main branch (code-only).
 * 
 * This script is automatically run during version bumps to maintain
 * link integrity across branches.
 */

const fs = require('fs');
const path = require('path');

const ROOT_DIR = path.resolve(__dirname, '../..');
const REPO_URL = 'https://github.com/JustineDevs/Hyperkit-Agent';

// Links that should point to devlog branch (convert to GitHub URLs)
const DEVLOG_LINK_PATTERNS = [
  /hyperkit-agent\/REPORTS\//,
  /hyperkit-agent\/docs\/TEAM\//,
  /hyperkit-agent\/docs\/EXECUTION\//,
  /hyperkit-agent\/docs\/INTEGRATION\//,
  /hyperkit-agent\/docs\/ROADMAP\.md/,
  /hyperkit-agent\/docs\/API_REFERENCE\.md/,
  /hyperkit-agent\/docs\/SECURITY_SETUP\.md/,
  /^docs\//,
  /^REPORTS\//,
];

// Links to keep relative (these files exist in main branch)
const KEEP_RELATIVE_PATTERNS = [
  /README\.md$/,
  /CHANGELOG\.md$/,
  /LICENSE\.md$/,
  /SECURITY\.md$/,
  /CONTRIBUTING\.md$/,
  /CODE_OF_CONDUCT\.md$/,
  /hyperkit-agent\/docs\/GUIDE\/QUICK_START\.md/,
  /hyperkit-agent\/docs\/GUIDE\/ENVIRONMENT_SETUP\.md/,
  /hyperkit-agent\/config\.yaml$/,
  /hyperkit-agent\/pyproject\.toml$/,
  /package\.json$/,
  /^VERSION$/,
];

// External URLs, anchors, and special patterns to skip
const SKIP_PATTERNS = [
  /^https?:\/\//,  // Already external URLs
  /^#/,            // Anchor links
  /^mailto:/,      // Email links
  /^ftp:\/\//,     // FTP links
];

function shouldConvertToGithubUrl(linkPath) {
  // Skip if already external URL or anchor
  for (const pattern of SKIP_PATTERNS) {
    if (pattern.test(linkPath)) {
      return false;
    }
  }
  
  // Check if it's in KEEP_RELATIVE list (exists in main)
  for (const pattern of KEEP_RELATIVE_PATTERNS) {
    if (pattern.test(linkPath)) {
      return false;
    }
  }
  
  // Check if it matches DEVLOG_LINKS patterns (should be in devlog)
  for (const pattern of DEVLOG_LINK_PATTERNS) {
    if (pattern.test(linkPath)) {
      return true;
    }
  }
  
  // Default: keep relative (might be code files or other assets)
  return false;
}

function convertToGithubUrl(linkPath) {
  // Remove leading ./ if present
  linkPath = linkPath.replace(/^\.\//, '');
  
  // Remove leading / if present
  linkPath = linkPath.replace(/^\//, '');
  
  // Convert to GitHub blob URL
  return `${REPO_URL}/blob/devlog/${linkPath}`;
}

function updateReadmeLinks(readmePath, dryRun = false) {
  if (!fs.existsSync(readmePath)) {
    console.error(`❌ README.md not found: ${readmePath}`);
    process.exit(1);
  }
  
  let content = fs.readFileSync(readmePath, 'utf8');
  const changes = [];
  
  // Pattern to match markdown links: [text](path) or [text](path "title")
  const linkPattern = /\[([^\]]+)\]\(([^)]+)\)/g;
  
  content = content.replace(linkPattern, (match, linkText, linkPath) => {
    // Remove title if present (e.g., "title" in [text](path "title"))
    if (linkPath.includes(' "')) {
      linkPath = linkPath.split(' "')[0];
    }
    
    // Skip if already a GitHub URL or external URL
    if (linkPath.startsWith('http')) {
      return match;
    }
    
    // Skip if it's an anchor link
    if (linkPath.startsWith('#')) {
      return match;
    }
    
    // Check if should convert
    if (shouldConvertToGithubUrl(linkPath)) {
      const newUrl = convertToGithubUrl(linkPath);
      changes.push([linkPath, newUrl]);
      return `[${linkText}](${newUrl})`;
    }
    
    return match;
  });
  
  return { content, changes };
}

function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes('--dry-run');
  const fileArg = args.find(arg => arg.startsWith('--file='));
  const readmePath = fileArg 
    ? path.resolve(ROOT_DIR, fileArg.split('=')[1])
    : path.join(ROOT_DIR, 'README.md');
  
  if (!fs.existsSync(readmePath)) {
    console.error(`❌ README.md not found: ${readmePath}`);
    process.exit(1);
  }
  
  const { content, changes } = updateReadmeLinks(readmePath, dryRun);
  
  if (changes.length > 0) {
    if (dryRun) {
      console.log(`[DRY RUN] Would update ${changes.length} links in ${path.relative(ROOT_DIR, readmePath)}`);
      console.log('\nChanges that would be made:');
      for (let i = 0; i < Math.min(20, changes.length); i++) {
        const [old, newUrl] = changes[i];
        console.log(`  ${old}`);
        console.log(`    -> ${newUrl}`);
      }
      if (changes.length > 20) {
        console.log(`\n  ... and ${changes.length - 20} more changes`);
      }
      console.log(`\n[INFO] Run without --dry-run to apply changes`);
    } else {
      fs.writeFileSync(readmePath, content, 'utf8');
      console.log(`[OK] Updated ${changes.length} links in ${path.relative(ROOT_DIR, readmePath)}`);
      console.log('\nSample changes:');
      for (let i = 0; i < Math.min(5, changes.length); i++) {
        const [old, newUrl] = changes[i];
        console.log(`  ${old} -> ${newUrl}`);
      }
      if (changes.length > 5) {
        console.log(`  ... and ${changes.length - 5} more`);
      }
    }
  } else {
    console.log(`[INFO] No links needed updating in ${path.relative(ROOT_DIR, readmePath)}`);
  }
}

if (require.main === module) {
  main();
}

module.exports = { updateReadmeLinks, shouldConvertToGithubUrl, convertToGithubUrl };

