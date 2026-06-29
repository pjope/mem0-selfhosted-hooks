"""Endpoint connectivity check, run via /mem0-ping."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_client import EXIT_FAILURE, EXIT_OK, Mem0Client, Mem0Config  # noqa: E402

SAMPLE_LIMIT = 1


def main() -> int:
    config = Mem0Config()
    if not config.enabled:
        print("MEM0_MCP_URL is not set — configure the endpoint first.")
        return EXIT_FAILURE

    print(f"Endpoint : {config.url}")
    print(f"User ID  : {config.user_id}")
    print(f"Token    : {'set' if config.token else 'none'}")
    try:
        client = Mem0Client(config)
        client.connect()
        results = client.search_memories("connectivity test", limit=SAMPLE_LIMIT)
        print("Handshake: ok")
        print(f"Search   : ok ({len(results)} sample result(s))")
        return EXIT_OK
    except Exception as error:
        print(f"Failed   : {error}")
        return EXIT_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
