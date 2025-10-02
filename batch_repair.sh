#!/bin/bash
# Batch repair all conversation files in Claude Code project directory

CONV_DIR="/home/tom/.claude/projects/-home-tom-spelling-bee-solver-project"
SCRIPT_DIR="/home/tom/spelling_bee_solver_project"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Anthropic API Conversation Batch Repair Tool            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Find all .jsonl files
FILES=($(find "$CONV_DIR" -name "*.jsonl" -not -name "*.fixed.jsonl" 2>/dev/null))

if [ ${#FILES[@]} -eq 0 ]; then
    echo "❌ No conversation files found in $CONV_DIR"
    exit 1
fi

echo "📂 Found ${#FILES[@]} conversation file(s)"
echo ""

# Analyze each file
for file in "${FILES[@]}"; do
    filename=$(basename "$file")
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📄 Analyzing: $filename"
    echo ""

    # Run diagnostic
    python3 "$SCRIPT_DIR/fix_conversation.py" "$file"

    echo ""
    read -p "🔧 Do you want to repair this file? (y/N): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3 "$SCRIPT_DIR/repair_conversation.py" "$file"

        # Validate repaired file
        fixed_file="${file%.jsonl}.fixed.jsonl"
        if [ -f "$fixed_file" ]; then
            echo ""
            python3 "$SCRIPT_DIR/validate_conversation.py" "$fixed_file"
        fi
    else
        echo "⏭️  Skipping repair"
    fi

    echo ""
done

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Batch repair complete!                                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
