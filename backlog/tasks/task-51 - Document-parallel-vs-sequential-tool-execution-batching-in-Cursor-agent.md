---
id: TASK-51
title: Document parallel vs sequential tool execution batching in Cursor agent
status: Done
assignee: []
created_date: '2026-01-27 14:48'
updated_date: '2026-01-27 22:34'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Documented the parallel vs sequential tool execution batching algorithm in Cursor agent version 2.3.41.

## Key Findings

### Parallel-Eligible Tools (12 tools)
These tools can execute concurrently in batches:
- READ_FILE_V2, LIST_DIR_V2, FILE_SEARCH, GLOB_FILE_SEARCH
- SEMANTIC_SEARCH_FULL, READ_SEMSEARCH_FILES, SEARCH_SYMBOLS
- RIPGREP_SEARCH, RIPGREP_RAW_SEARCH (limited to 5 concurrent)
- READ_LINTS, DEEP_SEARCH, TASK

### Sequential-Only Tools
- All file modification tools (EDIT_FILE, EDIT_FILE_V2, DELETE_FILE)
- Terminal commands (RUN_TERMINAL_COMMAND_V2)
- MCP tools (no streaming support)
- Streaming tools (WEB_SEARCH, etc.)

### Batching Algorithm
1. Tool calls arrive via `toolWrappedStream`
2. Parallel-eligible tools are added to a Promise array (`g`)
3. Sequential tools flush the batch first via `ee()`
4. Per-tool-type concurrency limits via `waitForToolSlot()`
5. Batch completes when all promises settle via `Promise.allSettled(g)`

### Concurrency Control
- RIPGREP tools limited to 5 concurrent
- Most other tools have unlimited concurrency
- TTL-based cleanup (10s default) for stale tool slots

## Deliverables
- Created `/reveng_2.3.41/analysis/TASK-51-tool-batching.md`
- Created 3 follow-up tasks for deeper investigation:
  - TASK-81: Server-side batching decisions
  - TASK-82: Timeout/retry behavior
  - TASK-83: persist_idempotent_stream_state flag
<!-- SECTION:FINAL_SUMMARY:END -->
