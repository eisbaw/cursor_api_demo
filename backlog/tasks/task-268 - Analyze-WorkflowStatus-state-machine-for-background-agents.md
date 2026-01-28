---
id: TASK-268
title: Analyze WorkflowStatus state machine for background agents
status: To Do
assignee: []
created_date: '2026-01-28 07:15'
labels:
  - reverse-engineering
  - protobuf
  - background-agent
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js:343441
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-38-conversation-state.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate the WorkflowStatus enum and state transitions used by background agent conversations. The CloudAgentStorageService uses workflowStatus to track conversation lifecycle (ARCHIVED, ERROR, EXPIRED, RUNNING, etc.). Document:
- All possible status values
- State transition rules
- How status affects streaming behavior
- Recovery mechanisms for error states
<!-- SECTION:DESCRIPTION:END -->
