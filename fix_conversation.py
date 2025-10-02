#!/usr/bin/env python3
"""
Diagnostic script to analyze Anthropic API conversation errors.
Identifies missing tool_result blocks for tool_use IDs.
"""

import json
import sys
import re


def parse_error_message(error_msg):
    """Extract message index and tool IDs from error message."""
    # Example: "messages.4: `tool_use` ids were found without `tool_result` blocks..."
    match = re.search(r'messages\.(\d+):', error_msg)
    if not match:
        return None, []

    msg_index = int(match.group(1))

    # Extract tool IDs (toolu_XXXX format)
    tool_ids = re.findall(r'toolu_[A-Za-z0-9]+', error_msg)

    return msg_index, tool_ids


def analyze_jsonl_file(filepath):
    """Analyze a JSONL conversation file for missing tool_result blocks."""
    print(f"\n📂 Analyzing: {filepath}\n")

    messages = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    # Extract message if it exists
                    if 'message' in entry:
                        messages.append(entry['message'])
    except FileNotFoundError:
        print(f"❌ Error: File not found: {filepath}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in file: {e}")
        return

    if not messages:
        print("⚠️  No messages found in file")
        return

    print(f"✓ Loaded {len(messages)} messages\n")

    issues_found = False

    for i, msg in enumerate(messages):
        if msg.get('role') != 'assistant':
            continue

        # Find tool_use blocks
        content = msg.get('content', [])
        if isinstance(content, str):
            continue

        tool_use_ids = []
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'tool_use':
                tool_use_ids.append(block.get('id'))

        if not tool_use_ids:
            continue

        # Check next message
        if i + 1 >= len(messages):
            issues_found = True
            print(f"❌ Message {i}: Assistant used tools but no following message exists")
            print(f"   Missing tool_result blocks for: {tool_use_ids}\n")
            continue

        next_msg = messages[i + 1]

        if next_msg.get('role') != 'user':
            issues_found = True
            print(f"❌ Message {i}: Assistant used tools but next message is '{next_msg.get('role')}' instead of 'user'")
            print(f"   Missing tool_result blocks for: {tool_use_ids}\n")
            continue

        # Check for tool_results
        next_content = next_msg.get('content', [])
        if isinstance(next_content, str):
            next_content = []

        result_ids = []
        for block in next_content:
            if isinstance(block, dict) and block.get('type') == 'tool_result':
                result_ids.append(block.get('tool_use_id'))

        missing = set(tool_use_ids) - set(result_ids)
        if missing:
            issues_found = True
            print(f"❌ Message {i}: Tool uses {missing} have no corresponding tool_result blocks in message {i + 1}\n")

    if not issues_found:
        print("✅ No issues found! Conversation structure is valid.\n")
    else:
        print("=" * 60)
        print("SUMMARY: Issues detected in conversation structure")
        print("Run repair_conversation.py to automatically fix these issues")
        print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  1. Analyze error message:")
        print('     python fix_conversation.py "messages.4: tool_use ids..."')
        print()
        print("  2. Analyze conversation file:")
        print("     python fix_conversation.py conversation.jsonl")
        sys.exit(1)

    arg = sys.argv[1]

    # Check if it's an error message or file
    if arg.startswith("messages."):
        # It's an error message
        msg_index, tool_ids = parse_error_message(arg)
        if msg_index is None:
            print("❌ Could not parse error message")
            sys.exit(1)

        print(f"\n📊 Error Analysis:")
        print(f"   Message Index: {msg_index}")
        print(f"   Missing tool_result IDs: {tool_ids}")
        print(f"\n💡 Solution:")
        print(f"   Insert a user message after message {msg_index} with tool_result blocks for:")
        for tool_id in tool_ids:
            print(f"   - {tool_id}")
    else:
        # It's a file path
        analyze_jsonl_file(arg)


if __name__ == "__main__":
    main()
