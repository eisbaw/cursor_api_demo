---
id: TASK-160
title: Document all hook input/output schemas
status: To Do
assignee: []
created_date: '2026-01-28 06:34'
labels:
  - reverse-engineering
  - hooks
  - schemas
dependencies:
  - TASK-96
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-96-shell-validators.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Each hook type receives different input parameters and validates different response schemas. Need to document the complete input/output schemas for all 12 hook types:

**Hook Types**:
- beforeShellExecution / afterShellExecution
- beforeMCPExecution / afterMCPExecution
- beforeReadFile / afterFileEdit
- beforeTabFileRead / afterTabFileEdit
- beforeSubmitPrompt
- stop
- afterAgentResponse / afterAgentThought

This will help understand what data is available to hook scripts and what responses they can return.
<!-- SECTION:DESCRIPTION:END -->
