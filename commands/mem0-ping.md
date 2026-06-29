---
description: Verify connectivity to the self-hosted mem0 endpoint used by the hooks
---

Run the mem0 connectivity check and report the result:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ping.py"
```

Summarize whether the handshake and search succeeded. If it failed, point at the likely cause: `MEM0_MCP_URL` unset, a wrong or missing token, or an unreachable endpoint.
