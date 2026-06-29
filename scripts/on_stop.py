"""Stop hook: save the tail of the transcript to mem0.

Exits 0 on any failure so a memory outage never blocks shutdown; skips
re-entrant stop events to avoid a save loop.
"""

from __future__ import annotations

import json
import os
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_client import EXIT_OK, Mem0Client, Mem0Config  # noqa: E402

MAX_MESSAGES = 6
MAX_CHARS_PER_MESSAGE = 4000
RELEVANT_ROLES = ("user", "assistant")


def _text_from_content(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return "\n".join(parts)
    return ""


def _read_transcript(path: str) -> list[dict]:
    messages: deque = deque(maxlen=MAX_MESSAGES)
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                continue
            message = entry.get("message") or {}
            role = message.get("role") or entry.get("type")
            if role not in RELEVANT_ROLES:
                continue
            text = _text_from_content(message.get("content")).strip()
            if text:
                messages.append({"role": role, "content": text[:MAX_CHARS_PER_MESSAGE]})
    return list(messages)


def _read_payload() -> dict:
    raw = "" if sys.stdin.isatty() else sys.stdin.read()
    try:
        return json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {}


def main() -> None:
    payload = _read_payload()
    if payload.get("stop_hook_active"):
        sys.exit(EXIT_OK)

    transcript = payload.get("transcript_path")
    if not transcript or not os.path.isfile(transcript):
        sys.exit(EXIT_OK)

    config = Mem0Config()
    if not config.enabled:
        sys.exit(EXIT_OK)

    try:
        messages = _read_transcript(transcript)
        if not messages:
            sys.exit(EXIT_OK)
        transcript_text = "\n\n".join(
            f"{message['role']}: {message['content']}" for message in messages
        )
        client = Mem0Client(config)
        client.connect()
        client.add_memory(text=transcript_text, messages=messages)
    except Exception:
        sys.exit(EXIT_OK)


if __name__ == "__main__":
    main()
