---
id: TASK-25
title: Extract protobuf schema for agent.v1 messages
status: Done
assignee: []
created_date: '2026-01-27 14:09'
updated_date: '2026-01-28 07:09'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Completed comprehensive analysis of the agent.v1 protobuf schema from Cursor IDE 2.3.41 beautified source code.

### Key Findings

**Scope:**
- ~300+ message types across 50+ proto source files
- 16 enum types for state and type definitions
- 6 gRPC services for agent communication

**Services Documented:**
1. `AgentService` - Main agent communication (Run, RunSSE, RunPoll, NameAgent, GetUsableModels, etc.)
2. `ExecService` - Tool execution protocol
3. `ControlService` - File operations and artifact management
4. `PrivateWorkerBridgeExternalService` - Worker bridge with Frame protocol
5. `LifecycleService` - Instance management
6. `PtyHostService` - PTY management

**Core Message Hierarchies:**
- `AgentClientMessage` / `AgentServerMessage` - Top-level bidirectional streaming
- `ExecServerMessage` / `ExecClientMessage` - Tool execution request/response
- `ToolCall` - 34 tool types including shell, edit, grep, glob, read, mcp, web search, etc.
- `InteractionUpdate` - 17 streaming update types for real-time UI updates
- `ConversationState` / `ConversationStateStructure` - Full conversation persistence

**Enums Extracted:**
- AgentMode (AGENT, ASK, PLAN, DEBUG, TRIAGE)
- SandboxPolicy.Type (INSECURE_NONE, WORKSPACE_READWRITE, WORKSPACE_READONLY)
- DiagnosticSeverity, TodoStatus, MouseButton, ScrollDirection, etc.

### Output
Analysis written to: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-25-agent-v1-protobuf.md`

### Follow-up Tasks Created
- TASK-256: Extract computer_use.proto automation messages
- TASK-257: Document MCP integration
- TASK-258: Analyze Frame-based worker bridge protocol
- TASK-259: Extract ControlService file/artifact protocol
<!-- SECTION:FINAL_SUMMARY:END -->
