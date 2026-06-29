---
name: dream
description: Consolidate mem0 — merge duplicates, resolve contradictions, prune clearly-stale entries. Shows a diff and asks before changing anything unless run with --auto. Use when the store has grown noisy.
---

# Dream

A consolidation pass. It mutates memory, so the default is propose-then-confirm; `--auto` applies only the safe merges without asking.

Read the full set with `get_memories` (`limit` 200), then work out a plan in three buckets:

**Merge** — groups of near-duplicates. Pick the clearest wording (or compose one that covers the group), and plan to replace the group with it.

**Resolve** — contradictory pairs. The newer `created_at` usually wins, but if it's ambiguous, ask rather than guess.

**Prune** — only entries that are clearly dead: superseded by a merge, or pointing at a tool/path the repo no longer has. When unsure, keep it.

Show the plan as a diff before touching anything:

```
## dream
merge 3 → 1: "deploys via CI" (drops [mem0:a1],[mem0:b2],[mem0:c3])
resolve: keep [mem0:d4] (2026-06), drop [mem0:e5] (2026-01)
prune: [mem0:f6] — references the old Traefik route
```

On approval, apply each: a merge is `add_memory` of the kept text (`infer=false`, carry the type) followed by `delete_memory` on the originals; a resolve/prune is `delete_memory`. There's no rollback, so finish only after the writes succeed and report the net change.

`--auto` runs merges of obvious duplicates silently and leaves contradictions and prunes for a human.
