#!/usr/bin/env node
/**
 * Solidity post-gen sanitizer & QA tool for Hyperkit-Agent
 * - Fixes known bad patterns (LLM/codegen errors)
 * - Reports potential issues for manual/automated attention
 *
 * Usage:
 * node scripts/ci/sanitize_solidity_postgen.js contracts/
 */

const fs = require('fs');
const path = require('path');

function sanitizeSolidityCode(code) {
  let original = code;

  // 1. Replace 'implements' with 'is' for contract inheritance/interfaces
  // Solidity does NOT support 'implements' - it's a Java/TypeScript pattern
  code = code.replace(/contract\s+([A-Za-z0-9_]+)\s+implements\s+/g, "contract $1 is ");

  // 2. Remove/replace deprecated Counters.sol usage (OZ v5+)
  code = code.replace(
    /import\s+['"]@openzeppelin\/contracts\/utils\/Counters\.sol['"];\s*/g,
    ""
  );
  code = code.replace(/using Counters\s+for\s+Counters\.Counter;\s*/g, "");
  code = code.replace(/Counters\.Counter\s+([a-zA-Z0-9_]+);/g, "uint256 $1;");
  code = code.replace(/(\w+)\.current\(\)/g, "$1");
  code = code.replace(/(\w+)\.increment\(\)/g, "$1++");

  // 3. Fix pragma version if needed (ensure ^0.8.20 minimum for OZ v5)
  code = code.replace(
    /pragma solidity\s+\^?0\.8\.\d+;/g,
    "pragma solidity ^0.8.20;"
  );

  // 4. Optionally: Remove/remap other known unsafe patterns (customize here!)
  // Add more as you see repeated failures (e.g., double semicolons, etc.)

  if (original !== code) {
    // Optionally log what was changed
    console.log("✔️  Solidity sanitizer: applied standard fixes");
  }
  return code;
}

// Recursively sanitize all .sol files in a directory tree
function sanitizeAllSolidityFiles(dirname) {
  const files = fs.readdirSync(dirname, { withFileTypes: true });
  let fixes = 0;

  for (const file of files) {
    if (file.isDirectory()) {
      fixes += sanitizeAllSolidityFiles(path.join(dirname, file.name));
    } else if (path.extname(file.name) === '.sol') {
      const filePath = path.join(dirname, file.name);
      let code = fs.readFileSync(filePath, 'utf8');
      const fixed = sanitizeSolidityCode(code);
      if (fixed !== code) {
        fs.writeFileSync(filePath, fixed, 'utf8');
        console.log(`✔️  Sanitized ${filePath}`);
        fixes++;
      }
    }
  }
  return fixes;
}

const targetDir = process.argv[2] || "contracts";
if (!fs.existsSync(targetDir)) {
  console.error(`❌ Error: Directory '${targetDir}' not found`);
  process.exit(1);
}

const fixCount = sanitizeAllSolidityFiles(targetDir);
console.log(`✅ Solidity post-gen sanitization complete (${fixCount} file(s) fixed).`);
process.exit(fixCount > 0 ? 0 : 0); // Always exit 0, fixes are logged
