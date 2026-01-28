---
id: TASK-226
title: Investigate hunk undo/redo integration with editor history
status: To Do
assignee: []
created_date: '2026-01-28 06:55'
labels:
  - reverse-engineering
  - undo-redo
  - editor-history
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-63-hunk-widget.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyze how hunk accept/reject operations integrate with VS Code's undo/redo stack.

Discovered in TASK-63: The session class (`wbu`) has `undoChangesUntil` method that manipulates version history. Key questions:
- How are individual hunk operations tracked in undo history?
- Can users undo an accepted hunk?
- How does `_mirrorChanges` maintain consistency between models?

References:
- Line 979830: `async undoChangesUntil(requestId)` in wbu class
- Line 979924: `_mirrorChanges(event)` in JEo class
- Uses `getAlternativeVersionId()` for version tracking
<!-- SECTION:DESCRIPTION:END -->
