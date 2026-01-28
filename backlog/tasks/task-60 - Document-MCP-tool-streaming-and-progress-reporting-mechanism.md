---
id: TASK-60
title: Document MCP tool streaming and progress reporting mechanism
status: Done
assignee: []
created_date: '2026-01-27 14:49'
updated_date: '2026-01-28 07:09'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigated MCP tool streaming and progress reporting mechanism in Cursor IDE 2.3.41. Key finding: MCP tools do NOT support true streaming - they use synchronous request-response with progress notifications as a workaround. Documented progress cache system, elicitation mechanism for user interaction, and human review workflow.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

**Key Finding**: MCP tools do NOT support true streaming despite protobuf stream type definitions. Tool execution is synchronous with `streamedCall()` and `finishStream()` methods throwing explicit errors.

### Documented Systems:
1. **Progress Notification Mechanism**: Uses `mcp.progressNotification` command with progressToken (toolCallId) as key
2. **Elicitation System**: Allows user interaction during tool execution via `mcp.elicitationRequest` command
3. **Human Review Workflow**: MCPToolReviewModel with RUN/SKIP/REJECT/ALLOWLIST options
4. **Two Tool APIs**: Legacy `vt.MCP` and newer `vt.CALL_MCP_TOOL` with explicit server targeting
5. **Recovery Mechanism**: Automatic retry with client recreation for transient failures

### Output:
- Analysis file: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-60-mcp-streaming.md`
<!-- SECTION:FINAL_SUMMARY:END -->
