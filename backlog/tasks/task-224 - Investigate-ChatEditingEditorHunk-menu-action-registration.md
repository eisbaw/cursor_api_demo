---
id: TASK-224
title: Investigate ChatEditingEditorHunk menu action registration
status: To Do
assignee: []
created_date: '2026-01-28 06:55'
labels:
  - reverse-engineering
  - menu-actions
  - hunk-ui
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-63-hunk-widget.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate how the `Me.ChatEditingEditorHunk` menu items are registered and what actions are available.

Discovered in TASK-63: The $wt hunk widget creates a toolbar using this menu ID. Understanding the action registration would reveal:
- What keyboard shortcuts are available for hunk operations
- How the accept/reject/toggle actions are contributed
- Whether there are additional undocumented actions

References:
- Line 1000603: `o.createInstance(tD, this._domNode, Me.ChatEditingEditorHunk, {...})`
- Line 22051: `this.ChatEditingEditorHunk = new Xo("ChatEditingEditorHunk")`
<!-- SECTION:DESCRIPTION:END -->
