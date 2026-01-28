---
id: TASK-148
title: Analyze approval dialog UI components
status: To Do
assignee: []
created_date: '2026-01-28 00:12'
labels:
  - reverse-engineering
  - cursor-2.3.41
  - ui-analysis
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-112-tool-approval.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate the React/UI components that render the tool approval dialogs. The review models (TerminalToolReviewModel, MCPToolReviewModel, EditFileReviewModel) manage state but the actual UI rendering is in the composer views. Need to trace composerViewsService.triggerScrollToBottom and find the dialog components.
<!-- SECTION:DESCRIPTION:END -->
