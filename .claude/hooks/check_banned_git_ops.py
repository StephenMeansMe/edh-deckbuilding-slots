#!/usr/bin/env python3
"""PreToolUse hook: block banned git operations before they run."""

import json
import re
import sys

data = json.load(sys.stdin)
cmd = data.get("tool_input", {}).get("command", "")

# Strip heredoc bodies so "git stash" in commit message text doesn't trigger.
scanned = re.sub(
    r"<<['\"]?\w+['\"]?.*?^\w+",
    "",
    cmd,
    flags=re.DOTALL | re.MULTILINE,
)

# "git stash" at a command boundary (start, after ; & | newline or open-paren).
# Exclude "git config" lines (used to set the blocking alias itself).
stash_invocation = re.search(
    r"(?:^|[;&|(\n])\s*git\s+stash",
    scanned,
    re.MULTILINE,
)

if stash_invocation and "git config" not in scanned:
    print("BLOCKED: git stash is prohibited in this project.")
    print("To inspect committed state without stashing:")
    print("  git show HEAD:<file> | uv run ruff check -")
    print("  git diff HEAD -- <file>")
    print("See CLAUDE.md: Forbidden git operations.")
    sys.exit(2)
