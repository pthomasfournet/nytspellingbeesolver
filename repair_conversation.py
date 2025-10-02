#!/usr/bin/env python3
"""
Automated repair script for Anthropic API conversation errors.
Fixes missing tool_result blocks by inserting proper user messages.
"""

import json
import sys
import os


def repair_jsonl_conversation(input_file, output_file=None):
    """
    Repair a JSONL conversation file by adding missing tool_result blocks.

    Args:
        input_file: Path to the input JSONL file
        output_file: Path to save repaired file (defaults to input_file.fixed.jsonl)
    """
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}.fixed{ext}"

    print(f"\n🔧 Repairing: {input_file}")
    print(f"📝 Output: {output_file}\n")

    entries = []
    messages = []
    message_to_entry = {}  # Map message to original entry for context

    try:
        with open(input_file, 'r') as f:
            for idx, line in enumerate(f):
                if line.strip():
                    entry = json.loads(line)
                    entries.append(entry)
                    if 'message' in entry:
                        msg_idx = len(messages)
                        messages.append(entry['message'])
                        message_to_entry[msg_idx] = idx
    except FileNotFoundError:
        print(f"❌ Error: File not found: {input_file}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in file: {e}")
        return False

    if not messages:
        print("⚠️  No messages found in file")
        return False

    print(f"✓ Loaded {len(messages)} messages from {len(entries)} entries\n")

    repairs_made = 0
    insertions = []  # List of (entry_index, new_entry) to insert

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
        needs_repair = False
        missing_ids = []

        if i + 1 >= len(messages):
            needs_repair = True
            missing_ids = tool_use_ids
        else:
            next_msg = messages[i + 1]

            if next_msg.get('role') != 'user':
                needs_repair = True
                missing_ids = tool_use_ids
            else:
                # Check for tool_results
                next_content = next_msg.get('content', [])
                if isinstance(next_content, str):
                    next_content = []

                result_ids = []
                for block in next_content:
                    if isinstance(block, dict) and block.get('type') == 'tool_result':
                        result_ids.append(block.get('tool_use_id'))

                missing_ids = list(set(tool_use_ids) - set(result_ids))
                if missing_ids:
                    needs_repair = True

        if needs_repair:
            print(f"🔨 Repairing message {i}: Adding tool_result blocks for {missing_ids}")

            # Create tool_result blocks
            tool_results = []
            for tool_id in missing_ids:
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": "[PLACEHOLDER: Replace with actual tool output]"
                })

            # Create new user message entry
            entry_idx = message_to_entry[i]
            original_entry = entries[entry_idx]

            new_entry = {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": tool_results
                },
                "parentUuid": original_entry.get("uuid", ""),
                "uuid": f"repair_{i}_{tool_use_ids[0]}",
                "timestamp": original_entry.get("timestamp", ""),
                "sessionId": original_entry.get("sessionId", ""),
                "cwd": original_entry.get("cwd", ""),
                "version": original_entry.get("version", ""),
                "isSidechain": False,
                "userType": "repair"
            }

            # Schedule insertion after this entry
            insertions.append((entry_idx + 1, new_entry))
            repairs_made += 1

    if repairs_made == 0:
        print("✅ No repairs needed! Conversation structure is already valid.\n")
        return True

    # Apply insertions (in reverse order to maintain indices)
    insertions.sort(reverse=True)
    for insert_idx, new_entry in insertions:
        entries.insert(insert_idx, new_entry)

    # Write repaired file
    try:
        with open(output_file, 'w') as f:
            for entry in entries:
                f.write(json.dumps(entry) + '\n')
        print(f"\n✅ Successfully repaired {repairs_made} issues")
        print(f"📁 Saved to: {output_file}")
        print(f"\n⚠️  IMPORTANT: Replace [PLACEHOLDER] entries with actual tool outputs!\n")
        return True
    except IOError as e:
        print(f"❌ Error writing output file: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python repair_conversation.py input.jsonl [output.jsonl]")
        print()
        print("If output file is not specified, creates input.fixed.jsonl")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    success = repair_jsonl_conversation(input_file, output_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
