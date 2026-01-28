---
id: TASK-52
title: >-
  Analyze ToolCall protobuf schema - document all tool types, parameters, and
  result structures used by agent
status: Done
assignee: []
created_date: '2026-01-27 14:48'
updated_date: '2026-01-27 22:37'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Analyzed the ToolCall protobuf schema from Cursor's decompiled source code, documenting the two-tier tool system architecture.

## Key Findings

### Architecture
- **aiserver.v1 package**: Server-side tool protocol for communication with Cursor's AI server
- **agent.v1 package**: Agent-level tool execution for local operations and UI rendering

### Documented Structures

**High-Level Wrappers:**
- `ToolCall` / `ToolResult` - Top-level wrapper distinguishing builtin vs custom tools
- `BuiltinToolCall` / `BuiltinToolResult` - Built-in tool invocations
- `CustomToolCall` / `CustomToolResult` - MCP and user-defined tools
- `StreamedBackToolCall` / `StreamedBackPartialToolCall` - Streaming protocol

**agent.v1 Tools Cataloged:**
- File operations: ShellToolCall, DeleteToolCall, ReadToolCall, EditToolCall, LsToolCall, GlobToolCall, GrepToolCall
- Search: SemSearchToolCall, WebSearchToolCall, ExaSearchToolCall, ExaFetchToolCall, FetchToolCall
- Code analysis: ReadLintsToolCall, CreatePlanToolCall
- User interaction: AskQuestionToolCall, SwitchModeToolCall
- MCP: McpToolCall, ListMcpResourcesToolCall, ReadMcpResourceToolCall
- Task management: TaskToolCall, UpdateTodosToolCall, ReadTodosToolCall
- Advanced: ComputerUseToolCall, GenerateImageToolCall, RecordScreenToolCall, WriteShellStdinToolCall, ReflectToolCall, SetupVmEnvironmentToolCall

**Streaming Support:**
- ToolCallDelta for streaming updates during tool execution
- Shell, Task, and Edit tools support delta streaming

**Context Management:**
- TruncatedToolCall for context-limited representations

## Output
- Created: `reveng_2.3.41/analysis/TASK-52-toolcall-schema.md`

## Follow-up Tasks Created
- TASK-104: ExaSearch/ExaFetch schema analysis
- TASK-106: RecordScreenToolCall capabilities
- TASK-108: ComputerUseToolCall deep dive
- TASK-110: BuiltinTool to ClientSideToolV2 enum mapping
- TASK-112: Tool execution approval flow analysis
<!-- SECTION:FINAL_SUMMARY:END -->
