"""MCP streamable-HTTP client for the mem0 tools, stdlib only.

Two transport quirks are worth knowing up front: responses come back as SSE or
plain JSON depending on the gateway, and this mem0 build rejects add_memory
unless a ``text`` argument is present even when ``messages`` is supplied.
"""

from __future__ import annotations

import json
import os
import urllib.request

PROTOCOL_VERSION = "2025-06-18"
DEFAULT_TOOL_PREFIX = "mem0__"
DEFAULT_USER_ID = "default"
DEFAULT_SEARCH_LIMIT = 10
DEFAULT_TIMEOUT_SECONDS = 15
CLIENT_NAME = "mem0-selfhosted-hooks"
CLIENT_VERSION = "0.1.0"
SESSION_ID_HEADER = "Mcp-Session-Id"
SSE_DATA_PREFIX = "data:"

SEARCH_TOOL = "search_memories"
ADD_TOOL = "add_memory"
RESULTS_KEY = "results"

EXIT_OK = 0
EXIT_FAILURE = 1


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "").strip())
    except (TypeError, ValueError):
        return default


class Mem0Config:
    def __init__(self) -> None:
        self.url = os.environ.get("MEM0_MCP_URL", "").strip()
        self.token = (
            os.environ.get("MEM0_MCP_TOKEN")
            or os.environ.get("METAMCP_API_KEY")
            or ""
        ).strip()
        self.user_id = (
            os.environ.get("MEM0_USER_ID", DEFAULT_USER_ID).strip() or DEFAULT_USER_ID
        )
        self.tool_prefix = os.environ.get("MEM0_TOOL_PREFIX", DEFAULT_TOOL_PREFIX)
        self.search_limit = _int_env("MEM0_SEARCH_LIMIT", DEFAULT_SEARCH_LIMIT)
        self.timeout = _int_env("MEM0_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)

    @property
    def enabled(self) -> bool:
        return bool(self.url)


class Mem0Client:
    def __init__(self, config: Mem0Config) -> None:
        self.config = config
        self._session_id: str | None = None
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _post(self, payload: dict) -> str:
        request = urllib.request.Request(
            self.config.url, data=json.dumps(payload).encode(), method="POST"
        )
        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "application/json, text/event-stream")
        if self.config.token:
            request.add_header("Authorization", "Bearer " + self.config.token)
        if self._session_id:
            request.add_header(SESSION_ID_HEADER, self._session_id)
        with urllib.request.urlopen(request, timeout=self.config.timeout) as response:
            session_id = response.headers.get(SESSION_ID_HEADER)
            if session_id:
                self._session_id = session_id
            return response.read().decode()

    @staticmethod
    def _parse(body: str) -> dict:
        for line in body.splitlines():
            line = line.strip()
            if line.startswith(SSE_DATA_PREFIX):  # SSE frame; bare JSON falls through
                return json.loads(line[len(SSE_DATA_PREFIX):].strip())
        return json.loads(body)

    @staticmethod
    def _unwrap(result: dict):
        # mem0 tools wrap their payload as a JSON string in content[0].text
        content = result.get("content") if isinstance(result, dict) else None
        if isinstance(content, list) and content:
            text = content[0].get("text", "")
            try:
                return json.loads(text)
            except (json.JSONDecodeError, TypeError):
                return {"text": text}
        return result

    def connect(self) -> None:
        body = self._post({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": CLIENT_NAME, "version": CLIENT_VERSION},
            },
        })
        self._parse(body)
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    def call_tool(self, name: str, arguments: dict):
        body = self._post({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {"name": self.config.tool_prefix + name, "arguments": arguments},
        })
        envelope = self._parse(body)
        if "error" in envelope:
            raise RuntimeError(envelope["error"])
        return self._unwrap(envelope.get("result", {}))

    def search_memories(self, query: str, limit: int | None = None) -> list:
        data = self.call_tool(SEARCH_TOOL, {
            "query": query,
            "user_id": self.config.user_id,
            "limit": limit or self.config.search_limit,
        })
        return data.get(RESULTS_KEY, []) if isinstance(data, dict) else []

    def add_memory(self, text: str, messages: list | None = None):
        # This server requires ``text`` even when ``messages`` is supplied;
        # send both so structured roles are available where supported.
        arguments: dict = {"user_id": self.config.user_id, "text": text}
        if messages:
            arguments["messages"] = messages
        return self.call_tool(ADD_TOOL, arguments)
