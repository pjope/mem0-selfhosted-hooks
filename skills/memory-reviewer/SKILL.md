---
name: memory-reviewer
description: Read-only quality audit of stored mem0 memories — finds duplicates, contradictions, untyped entries, and likely-stale facts. Use when recall feels noisy or before running a consolidation.
---

# Memory reviewer

This only reports; it changes nothing. Fixing is `dream`'s job.

Read everything with `get_memories` (`limit` 200) and group by `metadata.type`. Then scan for:

- **Duplicates** — entries saying the same thing in different words (compare within and across groups).
- **Contradictions** — pairs that can't both be true (e.g. "deploy via CI" vs "deploy by hand").
- **Untyped** — memories with no `metadata.type`.
- **Stale** — facts tied to a tool/version/path that the current repo no longer matches. Flag as *suspected*, not certain; you can't always tell from the text alone.

Output counts first, then the specific pairs/ids worth a human's attention:

```
review: <total> memories — <dups> dup, <contra> contradiction, <untyped> untyped
- dup: [mem0:a1] / [mem0:b2] — both say deploys go through CI
- contradiction: [mem0:c3] vs [mem0:d4]
```

End by pointing at `dream` if there's anything to merge or prune.
