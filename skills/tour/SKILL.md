---
name: tour
description: Browse everything stored in mem0, grouped by type, with full text. Use for a broad review of what the project knows, onboarding to existing memory, or auditing before a cleanup.
---

# Tour

Unlike `peek`, this shows full memories, not one-liners.

Pull the set with `get_memories` (`limit` 100). If the user passed a query, run `search_memories` instead so the tour is scoped to that topic.

Group by `metadata.type`. Within each group, print the full memory text and its short id. Order groups so the load-bearing ones come first — `decision`, `convention`, `anti_pattern` — then the rest, then anything untyped under "other".

```
## decision (4)
- All deploys go through the GitHub Actions pipeline, never manual SSH. [mem0:a3f8b2c1]
...

## convention (2)
...
```

Close with a one-line total. If the store is empty, say so and point at `remember`.
