---
name: import
description: Load memories into mem0 from an export file or a Claude Code MEMORY.md. Use to restore a backup, migrate from another machine, or seed a fresh store from existing notes.
---

# Import

Two sources, both writing through `add_memory` with `infer=false` so entries land verbatim.

**An export file** (the format the `export` skill writes): split it on the `---` front-matter blocks. For each, store the body text and carry its `type` into `metadata={"type": <type>, "source": "import"}`. Skip blocks whose body is empty.

**A `MEMORY.md`** (Claude Code's native notes): take each bullet as one memory, store it with `metadata={"type": "task_learning", "source": "import"}`.

Before a large import, say how many entries you're about to write and let the user stop you. Afterwards report the count that actually stored versus attempted — the server drops entries it considers duplicates, so the two can differ, and that's fine to state plainly.

This skill does not import other tools' config files; point the user at those tools' own exporters if they ask.
