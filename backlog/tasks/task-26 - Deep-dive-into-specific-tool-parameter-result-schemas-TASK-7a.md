---
id: TASK-26
title: Deep dive into specific tool parameter/result schemas (TASK-7a)
status: Done
assignee: []
created_date: '2026-01-27 14:10'
updated_date: '2026-01-28 07:24'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Completed deep analysis of ClientSideToolV2 parameter and result schemas from Cursor IDE 2.3.41.

## Key Findings

1. **56 Tool Types Identified**: Complete enumeration of ClientSideToolV2 tools including core operations (READ_FILE, EDIT_FILE, LIST_DIR), agent features (TASK, TASK_V2, TODO_READ/WRITE), and specialized tools (COMPUTER_USE, SWITCH_MODE, GENERATE_IMAGE)

2. **Complete Schema Documentation**: Documented protobuf message structures for:
   - ClientSideToolV2Call with 11 base fields plus params oneof
   - ClientSideToolV2Result with 6 base fields plus result oneof
   - ToolResultError with security-aware error message handling
   - ToolResultAttachments with todo reminders and discovery budget

3. **Detailed Params/Results for Key Tools**:
   - ReadFileParams/Result with line range controls
   - EditFileParams/Result with search/replace, fuzzy matching, linter integration
   - EditFileV2Params with streaming edit support
   - RunTerminalCommandV2Params with sandbox policies and execution options
   - GlobFileSearchParams/Result for pattern-based file discovery
   - TodoWriteParams with merge and dependencies
   - CallMcpToolParams using google.protobuf.Struct for args

4. **Streaming Architecture**: Each tool has Params, Result, and Stream message types; StreamedBackToolCall enables progressive updates

5. **Security Considerations**: Error messages explicitly labeled for client/server directionality; sandbox policies for terminal commands

## Output

Analysis file: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-26-tool-param-schemas.md`

## Follow-up Tasks Created

- TASK-279: Tool streaming protocol framing
- TASK-280: Computer use action types
- TASK-281: Agent mode definitions
- TASK-282: Sandbox policy enforcement (high priority)
- TASK-283: Human review workflow
- TASK-284: MCP vs CALL_MCP_TOOL comparison
<!-- SECTION:FINAL_SUMMARY:END -->
