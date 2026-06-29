---
name: peek
description: Quick compact search of mem0, or a direct lookup by memory id. Use to check whether something was already recorded, resolve a [mem0:<id>] citation, or glance at what's stored without the full tour.
---

# Peek

A fast lookup with one-line results.

If the argument looks like a memory id — a bare UUID, an 8-char hex prefix, or a `[mem0:<hex>]` citation — pull it directly with `get_memory` and show that one. Otherwise treat it as a search.

For a search, call `search_memories` with the query, `rerank=true`, and a small `limit` (10). Print each hit as:

```
<n>. [<type>] <memory, ~80 chars> (<created date>) [mem0:<short id>]
```

`<type>` comes from `metadata.type` when present, else drop the bracket. Sort by score as returned; don't re-rank by hand.

Nothing found → one line: `No memories for "<query>".` Don't pad it.
