# Anthropic API Conversation Repair Tools

This directory contains tools to diagnose and repair Anthropic API conversation errors related to missing `tool_result` blocks.

## Error Context

The Anthropic Messages API requires a **strict alternating pattern** between tool usage and tool results:

```
assistant (with tool_use) → user (with tool_result) → assistant → ...
```

When this pattern is broken, you'll see errors like:
```
API Error: 400 {"type":"error","error":{"type":"invalid_request_error",
"message":"messages.4: `tool_use` ids were found without `tool_result` blocks..."}}
```

## Tools Created

### 1. `fix_conversation.py` - Diagnostic Script

Analyzes conversation files and identifies missing `tool_result` blocks.

**Usage:**
```bash
# Analyze error message
python3 fix_conversation.py "messages.4: tool_use ids were found..."

# Analyze conversation file
python3 fix_conversation.py path/to/conversation.jsonl
```

### 2. `repair_conversation.py` - Automated Repair

Automatically fixes conversation structure by inserting proper user messages with `tool_result` placeholders.

**Usage:**
```bash
# Repair with default output name (adds .fixed to filename)
python3 repair_conversation.py input.jsonl

# Repair with custom output name
python3 repair_conversation.py input.jsonl output.jsonl
```

### 3. `validate_conversation.py` - Validation Module

Validates that conversation structure is correct.

**Usage:**
```bash
python3 validate_conversation.py conversation.jsonl
```

## Repair Results

### Files Analyzed

| File | Messages | Issues Found | Status |
|------|----------|--------------|--------|
| 480f27ac-8242-4b4b-aabf-80de31ad96e1.jsonl | 161 | 52 | ✅ Repaired |
| b0347cc9-8d67-449a-96a1-3efa3b45aa29.jsonl | 19 | 4 | ✅ Repaired |
| cf9dd296-04cd-41cd-b67b-2d5d82803999.jsonl | 2 | 0 | ✅ Valid |

### Repaired Files

The repaired conversation files are saved with `.fixed.jsonl` extension:

- `/home/tom/.claude/projects/-home-tom-spelling-bee-solver-project/480f27ac-8242-4b4b-aabf-80de31ad96e1.fixed.jsonl`
  - **161 messages** → **213 messages** (52 repairs)
  - ✅ Validated and ready to use

- `/home/tom/.claude/projects/-home-tom-spelling-bee-solver-project/b0347cc9-8d67-449a-96a1-3efa3b45aa29.fixed.jsonl`
  - **19 messages** → **23 messages** (4 repairs)
  - ✅ Validated and ready to use

## Important Notes

### ⚠️ Placeholders

The repair script inserts placeholder tool results:
```json
{
  "type": "tool_result",
  "tool_use_id": "toolu_XXX",
  "content": "[PLACEHOLDER: Replace with actual tool output]"
}
```

**These placeholders should be replaced with actual tool outputs if you want to continue the conversation meaningfully.**

However, for structural validation and avoiding API errors, the placeholders are sufficient.

### Next Steps

1. **Use the fixed files** - The `.fixed.jsonl` files are now structurally valid
2. **Replace placeholders** (optional) - If you need actual tool results for continuation
3. **Backup originals** - The original files remain untouched

## How It Works

### The Three Rules

1. **Every `tool_use` block MUST be followed by a corresponding `tool_result` block**
2. **Tool results MUST be in a `user` role message**
3. **The `tool_use_id` in the result MUST exactly match the `id` from the tool_use block**

### Repair Process

1. **Scan** - Identify all messages with `tool_use` blocks
2. **Check** - Verify each has a corresponding `tool_result` in the next user message
3. **Repair** - Insert missing user messages with `tool_result` blocks
4. **Validate** - Confirm structure is now correct

## Reference

Based on the comprehensive guide at:
`/home/tom/Downloads/ANTHROPIC_API_FIX_GUIDE.md`

## Summary

✅ **All conversation files analyzed**
✅ **2 files repaired successfully**
✅ **All repairs validated**
✅ **Ready to use**

The spelling bee solver project conversations are now structurally sound and won't trigger API errors related to missing tool results.
