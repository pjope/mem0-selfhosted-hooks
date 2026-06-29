"""Distil raw session captures into durable facts with a local LLM.

The Stop hook stores exchanges verbatim (``source: session``) because mem0's
inline extraction is unreliable. This runs the extraction as a batch step
instead: it pulls the raw captures and asks Ollama to distil them under a strict
JSON schema, so the model is grammar-constrained to valid structured output —
the enforcement mem0's tool-calling path lacked. Facts are written back tagged
``source: distilled`` and the consumed raw captures are deleted. Latency-tolerant
by design, so it can use a heavier model than a hook ever could.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_client import (  # noqa: E402
    DISTILLED_SOURCE,
    EXIT_FAILURE,
    EXIT_OK,
    SESSION_SOURCE,
    Mem0Client,
    Mem0Config,
)

DEFAULT_MODEL = "gemma4:12b-ctx32k"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
OLLAMA_TIMEOUT_SECONDS = 240
MEM0_WRITE_TIMEOUT_SECONDS = 90
MAX_INPUT_CHARS = 16000
DEFAULT_FACT_TYPE = "task_learning"
FACT_TYPES = [
    "decision", "convention", "anti_pattern",
    "user_preference", "environmental", "task_learning",
]

FACT_SCHEMA = {
    "type": "object",
    "properties": {
        "facts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "type": {"type": "string", "enum": FACT_TYPES},
                },
                "required": ["text", "type"],
            },
        }
    },
    "required": ["facts"],
}

SYSTEM_PROMPT = (
    "You distil a developer's working session into durable memory. From the "
    "exchanges, extract only facts worth recalling in a future session: "
    "decisions, conventions, anti-patterns or gotchas, user preferences, "
    "environment/config, and concrete task learnings. Ignore small talk, "
    "transient steps, and anything not durable. Write each fact as one clear "
    "declarative English sentence. If nothing is durable, return an empty list."
)


def _model() -> str:
    return os.environ.get("DISTILL_MODEL", DEFAULT_MODEL)


def _ollama_url() -> str:
    return os.environ.get("DISTILL_OLLAMA_URL", DEFAULT_OLLAMA_URL).rstrip("/")


def _extract(text: str) -> list[dict]:
    payload = {
        "model": _model(),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "format": FACT_SCHEMA,
        "stream": False,
        "options": {"temperature": 0},
    }
    request = urllib.request.Request(
        _ollama_url() + "/api/chat", data=json.dumps(payload).encode(), method="POST"
    )
    request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=OLLAMA_TIMEOUT_SECONDS) as response:
        body = json.loads(response.read().decode())
    content = body.get("message", {}).get("content", "")
    # the schema constrains gemma mostly, not perfectly: it can append trailing
    # text after the JSON, so decode the first value and ignore the rest.
    start = content.find("{")
    if start == -1:
        return []
    parsed, _ = json.JSONDecoder().raw_decode(content[start:])
    return parsed.get("facts", [])


def _batches(memories: list[dict]) -> list[list[dict]]:
    batches, current, size = [], [], 0
    for memory in memories:
        text = memory.get("memory") or ""
        if current and size + len(text) > MAX_INPUT_CHARS:
            batches.append(current)
            current, size = [], 0
        current.append(memory)
        size += len(text)
    if current:
        batches.append(current)
    return batches


def main() -> int:
    config = Mem0Config()
    if not config.enabled:
        print("MEM0_MCP_URL is not set.")
        return EXIT_FAILURE
    config.timeout = max(config.timeout, MEM0_WRITE_TIMEOUT_SECONDS)

    client = Mem0Client(config)
    client.connect()
    raw = [m for m in client.list_memories() if (m.get("metadata") or {}).get("source") == SESSION_SOURCE]
    if not raw:
        print("No raw session captures to distil.")
        return EXIT_OK

    print(f"Distilling {len(raw)} raw capture(s) with {_model()}…")
    facts_written, raw_removed = 0, 0
    for batch in _batches(raw):
        joined = "\n\n---\n\n".join(m.get("memory") or "" for m in batch)
        try:
            facts = _extract(joined)
        except Exception as error:
            print(f"  batch of {len(batch)} failed ({error}); leaving it for next run")
            continue
        for fact in facts:
            client.add_memory(
                text=fact["text"],
                infer=False,
                metadata={"type": fact.get("type", DEFAULT_FACT_TYPE), "source": DISTILLED_SOURCE},
            )
        facts_written += len(facts)
        for memory in batch:
            if memory.get("id"):
                client.delete_memory(memory["id"])
                raw_removed += 1

    print(f"Done: {raw_removed} raw capture(s) -> {facts_written} fact(s).")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
