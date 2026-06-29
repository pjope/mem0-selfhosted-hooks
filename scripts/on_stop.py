"""Stop hook: save the exchange that just completed to mem0, verbatim.

Stores with infer=False — this deployment's extraction LLM is unreliable, so the
hook captures the raw last user/assistant exchange rather than relying on mem0 to
distil facts. Only the latest exchange is taken (not a sliding window) so each
turn is recorded once without overlap. Exits 0 on any failure and skips
re-entrant stop events.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_client import EXIT_OK, SESSION_SOURCE, Mem0Client, Mem0Config  # noqa: E402

MAX_CHARS_PER_ROLE = 4000
RELEVANT_ROLES = ("user", "assistant")
ROLE_LABELS = {"user": "User", "assistant": "Assistant"}


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


def _latest_exchange(path: str) -> dict:
    latest = {role: "" for role in RELEVANT_ROLES}
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
                latest[role] = text[:MAX_CHARS_PER_ROLE]
    return latest


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
        exchange = _latest_exchange(transcript)
        parts = [f"{ROLE_LABELS[role]}: {exchange[role]}" for role in RELEVANT_ROLES if exchange[role]]
        if not parts:
            sys.exit(EXIT_OK)
        client = Mem0Client(config)
        client.connect()
        client.add_memory(text="\n\n".join(parts), infer=False, metadata={"source": SESSION_SOURCE})
    except Exception:
        sys.exit(EXIT_OK)


if __name__ == "__main__":
    main()
