# mem0-selfhosted-hooks

Session-boundary memory for Claude Code, pointed at your own
[mem0](https://github.com/mem0ai/mem0) instead of the mem0 cloud. It recalls
relevant memories when a session starts and saves the tail of the conversation
when it stops. No `m0-` key, no `api.mem0.ai` — the official mem0 plugin
hardcodes the cloud endpoint in its hook scripts and can't be repointed, which
is the whole reason this exists.

The hooks talk to mem0 over the MCP streamable-HTTP transport, so the endpoint
is just config. Point it at a mem0 server directly, or at a
[MetaMCP](https://github.com/metatool-ai/metamcp) gateway in front of one.

## Install

Needs Python 3.10+ on the machine running Claude Code (standard library only —
no `mem0ai` or `uv` on the client) and a reachable mem0 MCP streamable-HTTP
endpoint exposing `search_memories` and `add_memory`.

```
/plugin marketplace add pjope/mem0-selfhosted-hooks
/plugin install mem0-selfhosted-hooks@mem0-selfhosted-hooks
```

## Configure

The hooks read their config from the environment. The `env` block in
`~/.claude/settings.json` is injected into hook processes:

```json
{
  "env": {
    "MEM0_MCP_URL": "https://your-endpoint/mcp",
    "MEM0_MCP_TOKEN": "your-bearer-token",
    "MEM0_USER_ID": "your-user-id"
  }
}
```

| Variable | Default | Notes |
|----------|---------|-------|
| `MEM0_MCP_URL` | — | Required. Empty disables the hooks entirely. |
| `MEM0_MCP_TOKEN` | `METAMCP_API_KEY` | Bearer token, if the endpoint needs one. |
| `MEM0_USER_ID` | `default` | Memory scope. |
| `MEM0_TOOL_PREFIX` | `mem0__` | `mem0__` behind MetaMCP; `""` against a direct mem0 server. |
| `MEM0_SEARCH_LIMIT` | `10` | Results per search query. |
| `MEM0_TIMEOUT_SECONDS` | `15` | Per-request HTTP timeout. |

Run `/mem0-ping` to confirm the handshake and a read-only search work.

When mem0 sits behind a MetaMCP gateway, point `MEM0_MCP_URL` at the gateway
(`http://<host>:12008/metamcp/<namespace>/mcp`) and leave `MEM0_TOOL_PREFIX` at
`mem0__`. MetaMCP supplies the auth that the bare mem0 server lacks, so that's
the sane way to expose it on a LAN.

## What runs when

On **session start** the hook searches for memories about the current project and
branch and injects them as `additionalContext` — **facts-first**: raw verbatim
captures (`source: session`/`archived`) are filtered out so only distilled facts
and curated memories surface in auto-recall. On **stop** it stores the turn that
just finished **verbatim** (`infer=False`) — the user prompt plus all assistant
text of the turn (tool calls/results excluded), split into embed-sized chunks so
every chunk is fully indexed — tagged `source: session`.

Verbatim rather than distilled on purpose: mem0's inline fact-extraction depends
on the configured LLM producing strict JSON, which small local models do
unreliably. Capturing raw keeps writes fast and lossless; the distillation runs
later as a separate pass (see below).

Both hooks fail open: if the endpoint is unset or unreachable they print nothing
and exit 0. A memory outage should never be the thing that blocks your session.

## Distillation (post-processing)

`/<plugin>:distill` runs `scripts/distill.py`: it pulls the raw `source: session`
captures, has a local LLM distil them into durable facts **under a strict JSON
schema** (via Ollama's `format` parameter, so the model is grammar-constrained to
valid output — the enforcement mem0's inline path lacks), writes the facts back
tagged `source: distilled`, then **re-tags the consumed raw captures `source:
archived`** (kept and searchable, but skipped by future distill runs). It is
latency-tolerant, so it can use a heavier model than a hook could.

Run it on demand, or schedule it (e.g. end of day). Configure via env:

| Variable | Default | Purpose |
|----------|---------|---------|
| `DISTILL_OLLAMA_URL` | `http://localhost:11434` | Ollama endpoint for extraction. |
| `DISTILL_MODEL` | `gemma4:12b-ctx32k` | Extraction model (use a context-rich build). |

The graph store (`MEM0_ENABLE_GRAPH`) is a natural extension of this pass: entity
and relationship extraction belongs in the same latency-tolerant post-processing
step, not in the real-time hook.

## Skills

Beyond the automatic hooks, the plugin ships skills for working with memory by
hand. They call the mem0 tools directly (no scripts) and assume the same
single-user scope:

- `remember` / `forget` — store a fact verbatim / delete one with confirmation
- `peek` / `tour` — quick one-line search / full grouped browse
- `context-loader` — pull topic-relevant memories mid-session
- `export` / `import` — round-trip the store to a Markdown file
- `memory-reviewer` / `dream` — audit for duplicates and contradictions / consolidate them
- `health` — config + read/write/delete round-trip (deeper than `/mem0-ping`)

The project model from the cloud plugin (`app_id`, project listing/switching) is
intentionally absent — everything lives under one `MEM0_USER_ID`.

## License

MIT — see [LICENSE](LICENSE).
