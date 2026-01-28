---
id: TASK-81
title: Analyze server-side tool batching decisions
status: Done
assignee: []
created_date: '2026-01-27 22:34'
updated_date: '2026-01-28 06:36'
labels:
  - reverse-engineering
  - server-protocol
  - tool-batching
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate how the Cursor server decides when to emit tool calls in parallel vs sequential. The client-side batching (TASK-51) shows which tools CAN run in parallel, but we need to understand the server-side logic that determines WHEN to batch them.

Key questions:
- Does the server send multiple tool calls simultaneously?
- Is there a protocol for signaling batch boundaries?
- How does the model's output affect batching decisions?
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Investigated how Cursor handles server-side vs client-side tool batching decisions.

### Key Finding
**The server does NOT make batching decisions.** It simply streams tool calls sequentially as the model generates them. The CLIENT (`ToolV2Service`) decides whether to execute tools in parallel based on:

1. **Hardcoded parallel-eligible set**: 12 tools (READ_FILE_V2, LIST_DIR_V2, FILE_SEARCH, SEMANTIC_SEARCH_FULL, etc.) can run in parallel
2. **Tool type classification**: Write/streaming tools are always sequential
3. **Per-type concurrency limits**: Ripgrep limited to 5 concurrent, others unlimited

### Protocol Details
- `StreamUnifiedChatResponseWithTools` sends one tool at a time via `client_side_tool_v2_call`
- `modelCallId` groups tools from same model inference but doesn't affect batching
- `parallel_tool_calls_complete` field exists but is for telemetry, not control flow
- `PARALLEL_TOOL_CALL_START/END` event types are for analytics reporting

### Batch Lifecycle
1. Tool arrives in stream
2. Client checks if tool type is in parallel-eligible set
3. If parallel: queue with other parallel tools, wait for slot
4. If sequential or streaming: flush pending batch, execute synchronously
5. Batch completes when all queued tools finish OR non-parallel tool arrives

Written to: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-81-tool-batching.md`
<!-- SECTION:FINAL_SUMMARY:END -->
