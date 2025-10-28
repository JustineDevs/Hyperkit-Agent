#!/bin/bash
# Archive Old Scripts
# Archives or deletes scripts not updated/accessed in 2 months

set -e

echo "Archive Old Scripts"
echo "=================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
ARCHIVE_DIR="../../ARCHIVE/old_scripts"
DAYS_OLD=60  # 2 months
SCRIPT_DIR="../.."

# Create archive directory
mkdir -p "$ARCHIVE_DIR"

# Find old scripts
echo "Finding scripts not updated in $DAYS_OLD days..."
echo ""

OLD_SCRIPTS=()

# Find Python scripts
while IFS= read -r script; do
    if [ -f "$script" ]; then
        # Check if file hasn't been modified in DAYS_OLD days
        if find "$script" -mtime +$DAYS_OLD | grep -q .; then
            OLD_SCRIPTS+=("$script")
        fi
    fi
done < <(find "$SCRIPT_DIR" -name "*.py" -type f)

# Find shell scripts
while IFS= read -r script; do
    if [ -f "$script" ]; then
        if find "$script" -mtime +$DAYS_OLD | grep -q .; then
            OLD_SCRIPTS+=("$script")
        fi
    fi
done < <(find "$SCRIPT_DIR" -name "*.sh" -type f)

# Display old scripts
if [ ${#OLD_SCRIPTS[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ No old scripts found (all updated within $DAYS_OLD days)${NC}"
    exit 0
fi

echo -e "${YELLOW}Found ${#OLD_SCRIPTS[@]} old scripts:${NC}"
for script in "${OLD_SCRIPTS[@]}"; do
    file_age=$(stat -f "%Sm" -t "%Y-%m-%d" "$script" 2>/dev/null || stat -c "%y" "$script" | cut -d' ' -f1)
    echo "  - $script (last modified: $file_age)"
done

echo ""
echo -e "${YELLOW}Options:${NC}"
echo "1. Archive to $ARCHIVE_DIR"
echo "2. Delete permanently"
echo "3. Skip"
echo ""
read -p "Choose option [1/2/3]: " choice

case $choice in
    1)
        echo ""
        echo "Archiving old scripts..."
        for script in "${OLD_SCRIPTS[@]}"; do
            relative_path="${script#$SCRIPT_DIR/}"
            target_dir="$ARCHIVE_DIR/$(dirname "$relative_path")"
            mkdir -p "$target_dir"
            
            # Copy to archive
            cp "$script" "$ARCHIVE_DIR/$relative_path"
            
            # Remove original
            rm "$script"
            
            echo -e "${GREEN}✓ Archived: $script${NC}"
        done
        echo ""
        echo -e "${GREEN}✓ All old scripts archived to $ARCHIVE_DIR${NC}"
        ;;
    2)
        echo ""
        read -p "Are you sure you want to DELETE these scripts? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            for script in "${OLD_SCRIPTS[@]}"; do
                rm "$script"
                echo -e "${RED}✗ Deleted: $script${NC}"
            done
            echo ""
            echo -e "${RED}All old scripts deleted${NC}"
        else
            echo "Deletion cancelled"
        fi
        ;;
    3)
        echo "Skipping..."
        exit 0
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

echo ""
echo "Archive process complete!"
