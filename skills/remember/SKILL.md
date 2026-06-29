---
name: remember
description: Store a fact in mem0 verbatim, tagged with a type. Use when the user says remember this, save this, note that, or states a decision, preference, convention, or gotcha worth keeping across sessions.
---

# Remember

Save a stated fact straight into mem0. The user already phrased it, so store it verbatim — don't let the server re-extract it.

Invoked as `remember <text>`. If no text came with the call, ask what to store and stop.

Tag it with a `type` inferred from the wording:

- `decision` — "we decided", "always", "never"
- `anti_pattern` — "doesn't work", "don't use X because"
- `user_preference` — "I prefer", "use X over Y"
- `convention` — naming, layout, "the rule is"
- `environmental` — setup, tooling, hosts, config
- `task_learning` — everything else worth recalling

Call `add_memory` with `text` set to the user's words, `infer=false`, and `metadata={"type": <type>, "source": "remember"}`. Leave scope to the server default.

The write is synchronous: read the id from the first result and confirm in one line —

```
Remembered (<type>): "<first 80 chars>" — <id>
```

If the result comes back empty, the server rejected it as a duplicate of something already stored; say so instead of inventing an id.
