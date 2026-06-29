---
name: health
description: Diagnose the mem0 endpoint — config, connectivity, and a real read/write/delete round-trip. Use when recall or saving seems broken, searches come back empty, or after changing the endpoint config.
---

# Health

Goes one step past `/mem0-ping`: it proves a write actually lands and can be removed again.

First run the connectivity check, which covers config and the read path:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ping.py"
```

If that passes, prove the write path through the tools:

1. `add_memory` a throwaway line (`infer=false`, `metadata={"type":"task_learning","source":"health"}`) — clearly marked as a health probe.
2. Read the id back from the result.
3. `delete_memory` that id.

Report each stage as pass/fail. If the write succeeds but the delete fails, say so loudly — that leaves a stray probe memory behind and the user needs to know its id.

```
config     ok
handshake  ok
search     ok
write      ok
delete     ok
```

On any failure, name the likely cause: `MEM0_MCP_URL` unset, bad token, endpoint unreachable, or a tool error from the server.
