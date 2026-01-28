---
id: TASK-301.2
title: Parse ClientSideToolV2Call from streaming response
status: Done
assignee: []
created_date: '2026-01-28 10:05'
updated_date: '2026-01-28 10:20'
labels:
  - implementation
  - protobuf
  - parsing
dependencies:
  - TASK-301.1
references:
  - reveng_2.3.41/analysis/TASK-52-toolcall-schema.md
  - reveng_2.3.41/analysis/TASK-126-toolv2-params.md
parent_task_id: TASK-301
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement parsing of tool calls from server response:
- Detect magic byte 0x00/0x01 for compression
- Parse StreamUnifiedChatResponseWithTools
- Extract ClientSideToolV2Call messages (tool enum, params, tool_call_id)
- Handle partial_tool_call for streaming args
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Tool call detection from response chunks
- [ ] #2 Tool params extracted (readFileParams, listDirParams, etc.)
- [ ] #3 tool_call_id captured for result matching
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Tool calls detected via toolu_bdrk_* pattern matching
<!-- SECTION:NOTES:END -->
