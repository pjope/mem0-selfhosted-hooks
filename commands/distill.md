---
description: Distil raw verbatim session captures into durable facts using the local LLM
---

Run the mem0 distillation post-processor and report the result:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/distill.py"
```

Summarize how many raw captures became how many facts. If a batch failed or the endpoint was unreachable, point at the likely cause: `DISTILL_OLLAMA_URL` unset/unreachable, the model not pulled in Ollama, or `MEM0_MCP_URL` unset.
