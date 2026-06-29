---
name: export
description: Dump all mem0 memories to a portable Markdown file for backup or migration. Use before a cleanup, to archive, or to move memory between machines.
---

# Export

Read the whole set with `get_memories` (set `limit` high enough to cover everything — 500). For each memory write a block with a small YAML front-matter header carrying whatever the record has — `id`, `created_at`, `type` — followed by the memory text:

```markdown
---
id: a3f8b2c1-...
created_at: 2026-06-29T10:14:00Z
type: decision
---
All deploys go through the GitHub Actions pipeline, never manual SSH.
```

Write the file as `mem0-export-<cwd basename>-<YYYY-MM-DD>.md` in the working directory (get today's date from the shell). Fields the server didn't return just stay absent — don't invent them.

Finish with `Exported <n> memories to <filename>`. The format round-trips through the `import` skill.
