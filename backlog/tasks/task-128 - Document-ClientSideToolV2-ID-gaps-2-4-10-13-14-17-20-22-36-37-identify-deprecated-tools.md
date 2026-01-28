---
id: TASK-128
title: >-
  Document ClientSideToolV2 ID gaps (2, 4, 10, 13, 14, 17, 20-22, 36-37) -
  identify deprecated tools
status: Done
assignee: []
created_date: '2026-01-28 00:10'
updated_date: '2026-01-28 07:28'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyzed ClientSideToolV2 enum gaps in Cursor IDE 2.3.41 to identify deprecated/removed tools.

**Source:** reveng_2.3.41/beautified/workbench.desktop.main.js (line ~104365)

**Gaps Identified:** IDs 2, 4, 10, 13, 14, 17, 20-22, 36-37

**Key Finding:** ID 13 was RUN_TERMINAL_COMMAND v1, confirmed by `useLegacyTerminalTool` setting.

**Analysis written to:** reveng_2.3.41/analysis/TASK-128-tool-id-gaps.md
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary
Documented all 11 gaps in the ClientSideToolV2 enum with hypothesized deprecated tool names and evidence.

## Key Findings
1. **Gap ID 13 (RUN_TERMINAL_COMMAND v1)** - Very high confidence. The `useLegacyTerminalTool` setting at line 182286 and UI label "Legacy Terminal Tool" at line 904854 confirm terminal tool versioning.

2. **Gap ID 10 (SAVE_FILE)** - High confidence. BuiltinTool enum has SAVE_FILE=11, suggesting early explicit save functionality.

3. **Gaps 36-37 (RENAME_FILE, MOVE_FILE)** - Medium confidence. Position between TODO_WRITE and EDIT_FILE_V2 suggests file management tools.

4. **Gap ID 4 (CODEBASE_SEARCH)** - Medium confidence. SEMANTIC_SEARCH_CODEBASE exists in ToolType enum.

## Evidence Sources
- ClientSideToolV2 enum definition (line ~104365)
- BuiltinTool enum (line ~104513) - has no gaps, provides comparison
- useLegacyTerminalTool setting and related code
- ComposerCapabilityRequest.ToolType enum (line ~117965)

## Proto Field Analysis
ClientSideToolV2Call message field numbers differ from enum values (standard protobuf practice). Additional gaps in field numbers suggest more deprecated param types.
<!-- SECTION:FINAL_SUMMARY:END -->
