#!/usr/bin/env python3
"""
Validation module for Anthropic API conversations.
Ensures tool_use blocks have corresponding tool_result blocks.
"""

import json
import sys


def validate_tool_use_pattern(messages):
    """
    Validate that all tool_use blocks have corresponding tool_results.

    Args:
        messages: List of message dictionaries with 'role' and 'content'

    Returns:
        (is_valid, errors): Tuple of boolean and list of error messages

    Raises:
        ValueError: If conversation structure is invalid
    """
    errors = []

    for i, msg in enumerate(messages):
        if msg.get('role') != 'assistant':
            continue

        # Find tool_use blocks
        content = msg.get('content', [])
        if isinstance(content, str):
            continue

        tool_use_ids = [
            block['id']
            for block in content
            if isinstance(block, dict) and block.get('type') == 'tool_use'
        ]

        if not tool_use_ids:
            continue

        # Check next message
        if i + 1 >= len(messages):
            error = (
                f"Message {i}: Assistant used tools but no following message exists. "
                f"Tool IDs: {tool_use_ids}"
            )
            errors.append(error)
            continue

        next_msg = messages[i + 1]

        if next_msg.get('role') != 'user':
            error = (
                f"Message {i}: Assistant used tools but next message is "
                f"'{next_msg.get('role')}' instead of 'user'. Tool IDs: {tool_use_ids}"
            )
            errors.append(error)
            continue

        # Check for tool_results
        next_content = next_msg.get('content', [])
        if isinstance(next_content, str):
            next_content = []

        result_ids = [
            block['tool_use_id']
            for block in next_content
            if isinstance(block, dict) and block.get('type') == 'tool_result'
        ]

        missing = set(tool_use_ids) - set(result_ids)
        if missing:
            error = (
                f"Message {i}: Tool uses {missing} have no corresponding "
                f"tool_result blocks in message {i + 1}"
            )
            errors.append(error)

    return (len(errors) == 0, errors)


def validate_jsonl_file(filepath, raise_on_error=False):
    """
    Validate a JSONL conversation file.

    Args:
        filepath: Path to JSONL file
        raise_on_error: If True, raises ValueError on validation errors

    Returns:
        True if valid, False otherwise
    """
    print(f"\n🔍 Validating: {filepath}\n")

    messages = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    if 'message' in entry:
                        messages.append(entry['message'])
    except FileNotFoundError:
        print(f"❌ Error: File not found: {filepath}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in file: {e}")
        return False

    if not messages:
        print("⚠️  No messages found in file")
        return False

    print(f"✓ Loaded {len(messages)} messages\n")

    is_valid, errors = validate_tool_use_pattern(messages)

    if is_valid:
        print("✅ Conversation structure is VALID!")
        print("   All tool_use blocks have corresponding tool_result blocks.\n")
        return True
    else:
        print("❌ Conversation structure is INVALID!\n")
        print("Errors found:")
        for error in errors:
            print(f"  • {error}")
        print()

        if raise_on_error:
            raise ValueError("Invalid conversation structure")

        return False


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python validate_conversation.py conversation.jsonl")
        print()
        print("Validates that all tool_use blocks have corresponding tool_result blocks.")
        sys.exit(1)

    filepath = sys.argv[1]
    is_valid = validate_jsonl_file(filepath, raise_on_error=False)

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
