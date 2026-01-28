---
id: TASK-201
title: Investigate subagent state garbage collection and cleanup
status: To Do
assignee: []
created_date: '2026-01-28 06:49'
labels:
  - subagent
  - cleanup
  - lifecycle
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-89-subagent-state.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyze how Cursor handles cleanup of subagent states when parent conversations end or are deleted. The analysis in TASK-89 revealed that subagent states are stored in a map within ConversationStateStructure, but the cleanup mechanism is not clear.

Key questions:
- When are subagent states removed from the map?
- Are orphaned subagent states cleaned up automatically?
- What happens to transcript and status files when subagents are cleaned up?
- Is there a TTL or LRU mechanism for subagent states?
<!-- SECTION:DESCRIPTION:END -->
