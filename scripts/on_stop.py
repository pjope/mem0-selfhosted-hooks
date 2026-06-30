"""Stop hook: save the turn that just completed to mem0, verbatim and chunked.

Stores with infer=False — this deployment's extraction LLM is unreliable, so the
hook captures the raw turn (the user prompt plus all assistant text of that turn)
rather than relying on mem0 to distil facts. Tool calls/results are excluded.
The text is split into embed-sized chunks so every chunk is fully indexed, since
the embedder only vectorises its first ~2048 tokens. Exits 0 on any failure and
skips re-entrant stop events.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_client import EXIT_OK, SESSION_SOURCE, Mem0Client, Mem0Config  # noqa: E402

MAX_TURN_CHARS = 60000
CHUNK_CHARS = 6000
USER_ROLE = "user"
ASSISTANT_ROLE = "assistant"


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


def _latest_turn(path: str) -> str:
    user_text = ""
    assistant_parts: list[str] = []
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
            text = _text_from_content(message.get("content")).strip()
            if role == USER_ROLE and text:
                user_text = text
                assistant_parts = []
            elif role == ASSISTANT_ROLE and text:
                assistant_parts.append(text)

    parts = []
    if user_text:
        parts.append(f"User: {user_text}")
    if assistant_parts:
        parts.append("Assistant: " + "\n\n".join(assistant_parts))
    return "\n\n".join(parts)[:MAX_TURN_CHARS]


def _chunks(text: str) -> list[str]:
    return [text[i:i + CHUNK_CHARS] for i in range(0, len(text), CHUNK_CHARS)]


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
        turn = _latest_turn(transcript)
        if not turn:
            sys.exit(EXIT_OK)
        chunks = _chunks(turn)
        client = Mem0Client(config)
        client.connect()
        for index, chunk in enumerate(chunks):
            client.add_memory(
                text=chunk,
                infer=False,
                metadata={"source": SESSION_SOURCE, "part": index, "parts": len(chunks)},
            )
    except Exception:
        sys.exit(EXIT_OK)


if __name__ == "__main__":
    main()
