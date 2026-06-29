"""SessionStart hook: recall project memories into additionalContext.

Exits 0 on any failure — a memory outage must never block a session start.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_client import EXIT_OK, Mem0Client, Mem0Config  # noqa: E402

MAX_MEMORIES = 12
GIT_TIMEOUT_SECONDS = 3
HOOK_EVENT = "SessionStart"
CONTEXT_HEADER = "# mem0 Cross-Session Memory"


def _git(cwd: str, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", cwd, *args],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return ""


def _read_payload() -> dict:
    raw = "" if sys.stdin.isatty() else sys.stdin.read()
    try:
        return json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {}


def _collect(client: Mem0Client, queries: list[str]) -> list[str]:
    seen: set = set()
    lines: list[str] = []
    for query in queries:
        for memory in client.search_memories(query):
            identifier = memory.get("id")
            if identifier in seen:
                continue
            seen.add(identifier)
            text = (memory.get("memory") or "").strip()
            if text:
                lines.append(text)
            if len(lines) >= MAX_MEMORIES:
                return lines
    return lines


def main() -> None:
    payload = _read_payload()
    cwd = payload.get("cwd") or os.getcwd()
    project = Path(cwd).name
    branch = _git(cwd, "rev-parse", "--abbrev-ref", "HEAD")

    config = Mem0Config()
    if not config.enabled:
        sys.exit(EXIT_OK)

    try:
        client = Mem0Client(config)
        client.connect()
        lines = _collect(client, [
            f"{project} architecture conventions decisions",
            f"recent session summary {project}",
        ])
    except Exception:
        sys.exit(EXIT_OK)

    if not lines:
        sys.exit(EXIT_OK)

    scope = f"project `{project}`" + (f", branch `{branch}`" if branch else "")
    body = "\n".join(f"- {line}" for line in lines)
    context = f"{CONTEXT_HEADER}\n_Recalled from self-hosted mem0 for {scope}._\n\n{body}"
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT,
            "additionalContext": context,
        }
    }))
    sys.exit(EXIT_OK)


if __name__ == "__main__":
    main()
