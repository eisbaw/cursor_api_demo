---
id: TASK-125
title: >-
  Investigate BuiltinTool test-related tools (ADD_TEST, RUN_TEST, DELETE_TEST,
  GET_TESTS) - why removed from ClientSideToolV2?
status: Done
assignee: []
created_date: '2026-01-28 00:09'
updated_date: '2026-01-28 06:55'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate why test-related tools (ADD_TEST, RUN_TEST, DELETE_TEST, GET_TESTS) exist in BuiltinTool enum but are absent from ClientSideToolV2.

Key findings:
- These tools represent legacy server-orchestrated test management
- They have been superseded by general-purpose ClientSideToolV2 tools
- ADD_TEST/DELETE_TEST replaced by EDIT_FILE_V2
- RUN_TEST replaced by RUN_TERMINAL_COMMAND_V2
- GET_TESTS replaced by READ_FILE_V2 + SEARCH_SYMBOLS
- Protobuf messages exist for backwards compatibility but no client handlers implemented
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Documented all test tool enum values and their IDs
- [x] #2 Analyzed AddTestParams, RunTestParams, DeleteTestParams, GetTestsParams schemas
- [x] #3 Analyzed AddTestResult, RunTestResult, DeleteTestResult, GetTestsResult schemas
- [x] #4 Compared BuiltinTool vs ClientSideToolV2 architectures
- [x] #5 Identified why test tools were not migrated to ClientSideToolV2
- [x] #6 Documented modern equivalents for each test tool capability
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Investigated the test-related tools in BuiltinTool enum and their absence from ClientSideToolV2.

### Key Findings

1. **Legacy Architecture**: Test tools (IDs 8-10, 12) represent an older server-orchestrated test management system

2. **Superseded by General Tools**:
   - ADD_TEST -> EDIT_FILE_V2 (tests added via file editing)
   - RUN_TEST -> RUN_TERMINAL_COMMAND_V2 (tests run via terminal)
   - DELETE_TEST -> EDIT_FILE_V2 (tests deleted via file editing)
   - GET_TESTS -> READ_FILE_V2 + SEARCH_SYMBOLS (tests discovered via reading/symbols)

3. **Protobuf Messages Present but Dormant**:
   - AddTestParams, RunTestParams, DeleteTestParams, GetTestsParams defined
   - AddTestResult, RunTestResult, DeleteTestResult, GetTestsResult defined
   - No client-side handlers implemented for these messages

4. **Modern Approach Benefits**:
   - Reduced client complexity
   - Framework-agnostic (works with any test framework)
   - Agent has more flexibility
   - Smaller security attack surface

### Analysis Written To
`/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-125-builtin-test-tools.md`
<!-- SECTION:FINAL_SUMMARY:END -->
