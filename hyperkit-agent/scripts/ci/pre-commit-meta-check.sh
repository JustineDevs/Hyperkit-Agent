#!/bin/bash
# Pre-commit hook: Check for duplicate meta files
# 
# This hook prevents accidental addition of duplicate meta files.
# Install via: ln -s ../../scripts/ci/pre-commit-meta-check.sh .git/hooks/pre-commit
#
# Or use Husky: npm install --save-dev husky && npx husky install

set -e

# Get repository root
REPO_ROOT=$(git rev-parse --show-toplevel)

# Files that should NOT be in hyperkit-agent/
DUPLICATE_META_FILES=(
  "hyperkit-agent/VERSION"
  "hyperkit-agent/CHANGELOG.md"
  "hyperkit-agent/SECURITY.md"
  "hyperkit-agent/LICENSE.md"
  "hyperkit-agent/CODE_OF_CONDUCT.md"
  "hyperkit-agent/CONTRIBUTING.md"
)

# Check staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACMR)

FOUND_DUPES=0

for file in "${DUPLICATE_META_FILES[@]}"; do
  if echo "$STAGED_FILES" | grep -q "^$file"; then
    echo "❌ ERROR: Attempting to commit duplicate meta file: $file"
    echo "   Project-level meta files must exist ONLY in root directory."
    echo "   See CONTRIBUTING.md for 'Single Source of Truth Policy'"
    echo ""
    echo "   To fix:"
    echo "   1. Remove this file: git rm --cached $file"
    echo "   2. Or run cleanup: npm run version:cleanup-dupes"
    FOUND_DUPES=1
  fi
done

if [ $FOUND_DUPES -eq 1 ]; then
  echo ""
  echo "💡 Tip: Run 'npm run version:cleanup-dupes' to automatically remove duplicates"
  exit 1
fi

exit 0

