---
id: TASK-171
title: Analyze LLM tool ordering patterns and batching implications
status: To Do
assignee: []
created_date: '2026-01-28 06:36'
labels:
  - reverse-engineering
  - tool-batching
  - llm-behavior
dependencies:
  - TASK-81
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate how Cursor influences or observes the LLM's tool call ordering, and how this affects the client-side batching behavior.

Key questions:
- Does Cursor's system prompt encourage the model to emit read tools before write tools?
- How does `toolIndex` from the model correlate with actual execution order?
- Are there patterns in how models group related tool calls (e.g., multiple reads before an edit)?
- Does `modelCallId` grouping provide any optimization hints the client could use?

This emerged from TASK-81 analysis which showed the server doesn't make batching decisions - the model's output order is critical.
<!-- SECTION:DESCRIPTION:END -->
