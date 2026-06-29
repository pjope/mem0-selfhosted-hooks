---
name: context-loader
description: Pull relevant memories into context mid-session before working on something. Use when starting a new task, switching topics, or when the user asks what do we know about X.
---

# Context loader

The session-start hook already loads memory once at the top. This is the manual version for mid-session, when the topic shifts to something the startup recall didn't cover.

Take the current topic — from the user's phrasing or the files in play — and run two or three `search_memories` calls from different angles rather than one broad query: the topic itself, the topic plus "decision", the topic plus "gotcha"/"doesn't work". Use `rerank=true`.

Merge by id, keep the strongest handful, and surface them compactly:

```
Loaded <n> memories on "<topic>":
- [decision] ... [mem0:id]
- [anti_pattern] ... [mem0:id]
```

If nothing relevant comes back, stay silent — don't announce an empty load.
