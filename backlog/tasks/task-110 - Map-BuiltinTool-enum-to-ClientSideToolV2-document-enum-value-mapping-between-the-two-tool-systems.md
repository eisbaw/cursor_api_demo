---
id: TASK-110
title: >-
  Map BuiltinTool enum to ClientSideToolV2 - document enum value mapping between
  the two tool systems
status: Done
assignee: []
created_date: '2026-01-27 22:36'
updated_date: '2026-01-28 07:23'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate and document the mapping between BuiltinTool and ClientSideToolV2 enum systems in Cursor IDE 2.3.41.

Key findings:
- Two distinct tool systems that are NOT directly mapped to each other
- BuiltinTool: Legacy system with 20 tools (including test-related tools)
- ClientSideToolV2: Modern system with 44+ tools (including MCP, tasks, computer use)
- Multiple V1/V2 tool pairs (EDIT_FILE, READ_FILE, LIST_DIR, TASK)
- Tool param/result name mapping (eoe object)
- UI categories, approval requirements, and grouping behavior documented
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 BuiltinTool enum values documented with IDs 0-19
- [x] #2 ClientSideToolV2 enum values documented with IDs 0-55 (gaps noted)
- [x] #3 Functional mapping between similar tools documented
- [x] #4 V1/V2 tool version pairs identified
- [x] #5 Tool param/result name mapping (eoe) documented
- [x] #6 String-based tool names documented
- [x] #7 UI categories and tool grouping documented
- [x] #8 Tool approval requirements documented
- [x] #9 Background-capable tools identified
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Documented the two tool enum systems in Cursor IDE 2.3.41:

### BuiltinTool (Legacy)
- 20 tools (IDs 0-19)
- Contains test-related tools (ADD_TEST, RUN_TEST, DELETE_TEST, GET_TESTS)
- Used in `BuiltinToolCall` and `BuiltinToolResult` messages

### ClientSideToolV2 (Modern)
- 44+ tools with gaps in numbering (deprecated tools removed)
- Includes modern features: MCP, tasks, computer use, todo management
- Used in `ClientSideToolV2Call`, `ClientSideToolV2Result`, `StreamedBackToolCall` messages

### Key Findings
1. No direct 1:1 mapping exists between the two systems
2. ClientSideToolV2 is the primary system in active use
3. Multiple V1/V2 tool pairs exist with code checking both versions
4. Tool param/result names mapped via `eoe` object (line 480036)
5. String-based tool names used for UI display
6. UI categories: Search, Edit, Run
7. Approval requirements documented for 5 tools
8. Background-capable tools identified (8 tools)

Analysis file: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-110-tool-enum-mapping.md`
<!-- SECTION:FINAL_SUMMARY:END -->
