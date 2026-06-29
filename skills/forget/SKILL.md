---
name: forget
description: Delete memories from mem0 by search query or by id, always confirming first. Use to remove outdated decisions, wrong facts, or anything that shouldn't have been stored.
---

# Forget

Deletes are irreversible, so this skill never deletes without showing the user what's about to go.

**By id** (`forget <uuid>`): fetch it with `get_memory`, show the text, ask to confirm, then `delete_memory`.

**By query** (`forget <words>`): run `search_memories` (`limit` 10). Show the matches as a numbered list with their ids. Ask which to delete — a number, several, or "all of these". Never assume "all" from silence. Then `delete_memory` for each chosen id.

Report what actually went:

```
Deleted <n>: <short text of each>
```

If a `delete_memory` call fails, name the id that survived rather than reporting a clean sweep.
