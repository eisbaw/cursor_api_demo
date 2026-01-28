# TASK-52: ToolCall Protobuf Schema Analysis

**Source:** `reveng_2.3.41/beautified/workbench.desktop.main.js`
**Analysis Date:** 2026-01-27
**Previous:** TASK-26-tool-schemas.md (ClientSideToolV2 focus)

## Overview

This document provides a comprehensive analysis of the ToolCall protobuf schema, covering:
1. The two-tier tool architecture (agent.v1 vs aiserver.v1)
2. Complete tool type catalog for both packages
3. Streaming and delta patterns
4. Tool call lifecycle and execution flow

---

## Architecture: Two-Tier Tool System

Cursor uses two distinct protobuf packages for tool calling:

### 1. aiserver.v1 - Server-Side Tool Protocol

Used for communication between client and Cursor's AI server.

**Key Message Types:**
- `ClientSideToolV2Call` - Wrapper for all client-side tool invocations
- `ClientSideToolV2Result` - Wrapper for tool results
- `StreamedBackToolCall` - Streaming tool call from server
- `StreamedBackPartialToolCall` - Partial/incremental tool call data
- `StreamedBackToolCallV2` - V2 streaming protocol
- `ToolCall` - High-level wrapper (builtin or custom)
- `ToolResult` - High-level result wrapper
- `BuiltinToolCall` - Built-in tool invocation
- `BuiltinToolResult` - Built-in tool result
- `CustomToolCall` - Custom/MCP tool invocation
- `CustomToolResult` - Custom tool result

### 2. agent.v1 - Agent-Level Tool Execution

Used for internal agent operations and UI rendering.

**Key Message Types:**
- Various `*ToolCall` messages (ShellToolCall, EditToolCall, etc.)
- `*ToolArgs` messages for each tool
- `*ToolResult` messages with success/error oneofs
- `ToolCallDelta` - Streaming deltas for tool progress
- `TruncatedToolCall` - Context-limited tool representation

---

## High-Level ToolCall Wrappers

### aiserver.v1.ToolCall
**Location:** Line ~110037

The top-level wrapper that distinguishes between built-in and custom tools:

```protobuf
message ToolCall {
  oneof tool_call {
    BuiltinToolCall builtin_tool_call = 1;
    CustomToolCall custom_tool_call = 2;
  }
}
```

### aiserver.v1.ToolResult
**Location:** Line ~110076

```protobuf
message ToolResult {
  oneof tool_result {
    BuiltinToolResult builtin_tool_result = 1;
    CustomToolResult custom_tool_result = 2;
    ErrorToolResult error_tool_result = 3;
  }
}
```

### aiserver.v1.CustomToolCall
**Location:** Line ~111136

For MCP and user-defined tools:

```protobuf
message CustomToolCall {
  string tool_id = 1;     // Unique tool identifier
  string params = 2;      // JSON-encoded parameters
}
```

### aiserver.v1.CustomToolResult
**Location:** Line ~111196

```protobuf
message CustomToolResult {
  string tool_id = 1;     // Matching tool identifier
  string result = 2;      // JSON-encoded result
}
```

---

## BuiltinToolCall Structure

### aiserver.v1.BuiltinToolCall
**Location:** Line ~109554

Contains the BuiltinTool enum and params oneof:

```protobuf
message BuiltinToolCall {
  BuiltinTool tool = 1;                           // Tool type enum
  optional string tool_call_id = 22;              // Unique call ID

  oneof params {
    SearchParams search_params = 2;               // Code search
    ReadChunkParams read_chunk_params = 3;        // Read file chunk
    GotodefParams gotodef_params = 4;             // Go to definition
    EditParams edit_params = 5;                   // Edit file
    UndoEditParams undo_edit_params = 6;          // Undo edit
    EndParams end_params = 7;                     // End conversation
    NewFileParams new_file_params = 8;            // Create new file
    AddTestParams add_test_params = 9;            // Add test
    RunTestParams run_test_params = 10;           // Run test
    DeleteTestParams delete_test_params = 11;     // Delete test
    SaveFileParams save_file_params = 12;         // Save file
    GetTestsParams get_tests_params = 13;         // Get tests
    GetSymbolsParams get_symbols_params = 14;     // Get symbols
    SemanticSearchParams semantic_search_params = 15;  // Semantic search
    GetProjectStructureParams get_project_structure_params = 16;
    CreateRmFilesParams create_rm_files_params = 17;
    RunTerminalCommandsParams run_terminal_commands_params = 18;
    NewEditParams new_edit_params = 19;           // New edit API
    ReadWithLinterParams read_with_linter_params = 20;
    AddUiStepParams add_ui_step_params = 21;      // UI step
    ReadSemsearchFilesParams read_semsearch_files_params = 23;
    DeleteFileParams delete_file_params = 26;
  }
}
```

---

## Streaming Tool Call Types

### aiserver.v1.StreamedBackPartialToolCall
**Location:** Line ~105748

Sent when tool invocation begins, before full parameters:

```protobuf
message StreamedBackPartialToolCall {
  ClientSideToolV2 tool = 1;          // Tool enum
  string tool_call_id = 2;            // Unique ID
  string name = 3;                    // Tool name string
  optional uint32 tool_index = 4;     // Index in parallel calls
  optional string model_call_id = 5;  // Associated model call
}
```

### aiserver.v1.StreamedBackToolCall
**Location:** Line ~105800

Full tool call with streaming support:

```protobuf
message StreamedBackToolCall {
  ClientSideToolV2 tool = 1;          // Tool enum
  string tool_call_id = 2;            // Unique ID
  string name = 4;                    // Tool name
  string raw_args = 5;                // JSON arguments

  oneof params {
    ReadSemsearchFilesStream read_semsearch_files_stream = 3;
    RipgrepSearchStream ripgrep_search_stream = 5;
    ReadFileStream read_file_stream = 7;
    ListDirStream list_dir_stream = 12;
    EditFileStream edit_file_stream = 13;
    ToolCallFileSearchStream file_search_stream = 14;
    SemanticSearchFullStream semantic_search_full_stream = 19;
    DeleteFileStream delete_file_stream = 21;
    ReapplyStream reapply_stream = 22;
    RunTerminalCommandV2Stream run_terminal_command_v2_stream = 25;
    FetchRulesStream fetch_rules_stream = 26;
    WebSearchStream web_search_stream = 28;
    MCPStream mcp_stream = 29;
    SearchSymbolsStream search_symbols_stream = 33;
    GotodefStream gotodef_stream = 41;
    BackgroundComposerFollowupStream background_composer_followup_stream = 34;
    KnowledgeBaseStream knowledge_base_stream = 35;
    FetchPullRequestStream fetch_pull_request_stream = 36;
    DeepSearchStream deep_search_stream = 37;
    CreateDiagramStream create_diagram_stream = 38;
    // ... additional stream types
  }
}
```

### aiserver.v1.StreamedBackToolCallV2
**Location:** Line ~106119

Enhanced streaming with additional metadata.

---

## Complete agent.v1.ToolCall Catalog

### File Operations

| Tool Type | Args Message | Result Message | Description |
|-----------|--------------|----------------|-------------|
| ShellToolCall | QOt (shell args) | cIr (shell result) | Execute shell command |
| DeleteToolCall | O4t (delete args) | QPr (delete result) | Delete file |
| ReadToolCall | ReadToolArgs | ReadToolResult | Read file content |
| EditToolCall | kas (edit args) | cue (edit result) | Edit file |
| LsToolCall | ABt (ls args) | dlt (ls result) | List directory |
| GlobToolCall | GlobToolArgs | GlobToolResult | Glob pattern search |
| GrepToolCall | B4t (grep args) | Z7e (grep result) | Regex search |

### Search & Navigation

| Tool Type | Args Message | Result Message | Description |
|-----------|--------------|----------------|-------------|
| SemSearchToolCall | semsearch args | semsearch result | Semantic search |
| WebSearchToolCall | web search args | web search result | Web search |
| ExaSearchToolCall | ULr (exa args) | Zhl (exa result) | Exa AI search |
| ExaFetchToolCall | fetch args | fetch result | Exa URL fetch |
| FetchToolCall | gLr (fetch args) | pLr (fetch result) | General URL fetch |

### Code Analysis

| Tool Type | Args Message | Result Message | Description |
|-----------|--------------|----------------|-------------|
| ReadLintsToolCall | ReadLintsToolArgs | ReadLintsToolResult | Read lint errors |
| CreatePlanToolCall | plan args | plan result | Create execution plan |

### User Interaction

| Tool Type | Args Message | Result Message | Description |
|-----------|--------------|----------------|-------------|
| AskQuestionToolCall | AskQuestionArgs | AskQuestionResult | Ask user question |
| SwitchModeToolCall | switch args | switch result | Switch agent mode |

### MCP Integration

| Tool Type | Args Message | Result Message | Description |
|-----------|--------------|----------------|-------------|
| McpToolCall | mcp args | mcp result | Call MCP tool |
| ListMcpResourcesToolCall | list args | list result | List MCP resources |
| ReadMcpResourceToolCall | read args | read result | Read MCP resource |

### Task Management

| Tool Type | Args Message | Result Message | Description |
|-----------|--------------|----------------|-------------|
| TaskToolCall | task args | task result | Create subagent task |
| UpdateTodosToolCall | todos args | todos result | Update todo list |
| ReadTodosToolCall | read args | todos result | Read todo list |

### Advanced Tools

| Tool Type | Args Message | Result Message | Description |
|-----------|--------------|----------------|-------------|
| ComputerUseToolCall | PIr (computer args) | AIr (computer result) | Computer automation |
| GenerateImageToolCall | image args | image result | Generate image |
| RecordScreenToolCall | record args | record result | Screen recording |
| WriteShellStdinToolCall | stdin args | stdin result | Write to shell stdin |
| ReflectToolCall | ReflectArgs | ReflectResult | Agent reflection |
| SetupVmEnvironmentToolCall | vm args | vm result | Setup VM environment |
| ApplyAgentDiffToolCall | diff args | diff result | Apply agent diff |

---

## Detailed Tool Message Schemas

### agent.v1.ShellToolCall
**Location:** Line ~132719

```protobuf
message ShellToolCall {
  ShellArgs args = 1;              // Command to execute
  ShellResult result = 2;          // Execution result
}

message ShellToolCallDelta {
  oneof delta {
    ShellToolCallStdoutDelta stdout = 1;   // Stdout chunk
    ShellToolCallStderrDelta stderr = 2;   // Stderr chunk
  }
}

message ShellToolCallStdoutDelta {
  string content = 1;
}

message ShellToolCallStderrDelta {
  string content = 1;
}
```

### agent.v1.GlobToolCall
**Location:** Line ~133069

```protobuf
message GlobToolCall {
  GlobToolArgs args = 1;
  GlobToolResult result = 2;
}

message GlobToolArgs {
  optional string target_directory = 1;   // Base directory
  string glob_pattern = 2;                // Pattern (e.g., "**/*.ts")
}

message GlobToolResult {
  oneof result {
    GlobToolSuccess success = 1;
    GlobToolError error = 2;
  }
}

message GlobToolSuccess {
  string pattern = 1;           // Applied pattern
  string path = 2;              // Search path
  repeated string files = 3;    // Matching files
  int32 total_files = 4;        // Total matches
  bool client_truncated = 5;    // Client-side truncation
  bool ripgrep_truncated = 6;   // Ripgrep truncation
}

message GlobToolError {
  string error = 1;
}
```

### agent.v1.ReadToolCall
**Location:** Line ~133140

```protobuf
message ReadToolCall {
  ReadToolArgs args = 1;
  ReadToolResult result = 2;
}

message ReadToolArgs {
  string path = 1;              // File path
  optional int32 offset = 2;    // Line offset
  optional int32 limit = 3;     // Line limit
}

message ReadToolResult {
  oneof result {
    ReadToolSuccess success = 1;
    ReadToolError error = 2;
  }
}
```

### agent.v1.EditToolCall
**Location:** Line ~134189

```protobuf
message EditToolCall {
  EditArgs args = 1;            // Edit arguments
  EditResult result = 2;        // Edit result
}

message EditToolCallDelta {
  string stream_content_delta = 1;   // Streaming content
}
```

### agent.v1.ReadLintsToolCall
**Location:** Line ~134301

```protobuf
message ReadLintsToolCall {
  ReadLintsToolArgs args = 1;
  ReadLintsToolResult result = 2;
}

message ReadLintsToolArgs {
  repeated string paths = 1;           // Files to check
}

message ReadLintsToolResult {
  oneof result {
    ReadLintsToolSuccess success = 1;
    ReadLintsToolError error = 2;
  }
}

message ReadLintsToolSuccess {
  repeated FileDiagnostics file_diagnostics = 1;
  int32 total_files = 2;
  int32 total_diagnostics = 3;
}

message FileDiagnostics {
  string path = 1;
  repeated DiagnosticItem diagnostics = 2;
  int32 diagnostics_count = 3;
}

message DiagnosticItem {
  DiagnosticSeverity severity = 1;
  string message = 2;
  string source = 3;
  string code = 4;
  bool is_stale = 5;
}
```

### agent.v1.AskQuestionToolCall
**Location:** Line ~135556

```protobuf
message AskQuestionToolCall {
  AskQuestionArgs args = 1;
  AskQuestionResult result = 2;
}

message AskQuestionArgs {
  string title = 1;                           // Question title
  repeated Question questions = 2;            // Questions to ask
  bool run_async = 5;                         // Run asynchronously
  string async_original_tool_call_id = 6;     // Original call ID for async

  message Question {
    string id = 1;                   // Question identifier
    string prompt = 2;               // Question text
    repeated Option options = 3;     // Answer options
    bool allow_multiple = 4;         // Allow multiple selections
  }

  message Option {
    string id = 1;                   // Option identifier
    string label = 2;                // Display text
  }
}

message AskQuestionResult {
  oneof result {
    AskQuestionSuccess success = 1;
    AskQuestionError error = 2;
    AskQuestionAsync async = 3;      // Async response pending
  }
}

message AskQuestionSuccess {
  repeated Answer answers = 1;

  message Answer {
    string question_id = 1;
    repeated string selected_option_ids = 2;
  }
}
```

### agent.v1.ReflectToolCall
**Location:** Line ~137320

New reflection/reasoning tool:

```protobuf
message ReflectToolCall {
  ReflectArgs args = 1;
  ReflectResult result = 2;
}

message ReflectArgs {
  string unexpected_action_outcomes = 1;   // Analysis of unexpected results
  string relevant_instructions = 2;        // Relevant user instructions
  string scenario_analysis = 3;            // Current scenario analysis
  string critical_synthesis = 4;           // Critical thinking synthesis
  string next_steps = 5;                   // Planned next steps
  string tool_call_id = 6;                 // Associated tool call
}

message ReflectResult {
  oneof result {
    ReflectSuccess success = 1;
    ReflectError error = 2;
  }
}
```

### agent.v1.SetupVmEnvironmentToolCall
**Location:** Line ~137452

```protobuf
message SetupVmEnvironmentToolCall {
  SetupVmEnvironmentArgs args = 1;
  SetupVmEnvironmentResult result = 2;
}

message SetupVmEnvironmentArgs {
  string install_command = 2;      // Installation command
  string start_command = 3;        // Startup command
}

message SetupVmEnvironmentResult {
  oneof result {
    SetupVmEnvironmentSuccess success = 1;
  }
}
```

### agent.v1.ExaSearchToolCall
**Location:** Line ~136542

Exa AI-powered web search:

```protobuf
message ExaSearchToolCall {
  ExaSearchArgs args = 1;
  ExaSearchResult result = 2;
}

message ExaSearchReference {
  string title = 1;
  string url = 2;
  string text = 3;
  string published_date = 4;
}
```

---

## Tool Call Delta (Streaming Updates)

### agent.v1.ToolCallDelta
**Location:** Line ~139704

Streaming updates during tool execution:

```protobuf
message ToolCallDelta {
  oneof delta {
    ShellToolCallDelta shell_tool_call_delta = 1;    // Shell output
    TaskToolCallDelta task_tool_call_delta = 2;      // Task progress
    EditToolCallDelta edit_tool_call_delta = 3;      // Edit content
  }
}
```

---

## Truncated Tool Calls

### agent.v1.TruncatedToolCall
**Location:** Line ~139664

Used for context-limited representations:

```protobuf
message TruncatedToolCall {
  bytes original_step_blob_id = 1;     // Reference to full content
  TruncatedToolCallArgs args = 2;      // Placeholder args
  TruncatedToolCallResult result = 3;  // Truncated result
}

message TruncatedToolCallArgs {
  // Empty - arguments truncated
}

message TruncatedToolCallResult {
  oneof result {
    TruncatedToolCallSuccess success = 1;
    TruncatedToolCallError error = 2;
  }
}

message TruncatedToolCallError {
  string error = 1;                    // Error message preserved
}
```

---

## Conversation Step Integration

### agent.v1.ConversationStep
**Location:** Line ~139749

How tool calls fit in the conversation:

```protobuf
message ConversationStep {
  oneof message {
    AssistantMessage assistant_message = 1;    // Text response
    ToolCall tool_call = 2;                    // Tool invocation
    ThinkingMessage thinking_message = 3;      // Reasoning step
  }
}
```

---

## Key Findings

### 1. Dual Architecture Purpose

- **aiserver.v1**: Server communication, model tool calling, result aggregation
- **agent.v1**: Local execution, UI rendering, streaming updates

### 2. Consistent Tool Pattern

Every agent.v1 tool follows the pattern:
```protobuf
message XxxToolCall {
  XxxArgs args = 1;      // Input parameters
  XxxResult result = 2;  // Output result
}
```

Results consistently use a success/error oneof:
```protobuf
message XxxResult {
  oneof result {
    XxxSuccess success = 1;
    XxxError error = 2;
  }
}
```

### 3. Streaming Deltas for Long-Running Tools

Only certain tools have delta messages:
- ShellToolCallDelta (stdout/stderr streaming)
- TaskToolCallDelta (subagent progress)
- EditToolCallDelta (streaming content)

### 4. New Tools in This Version

Compared to earlier analysis, new tools discovered:
- **ReflectToolCall** - Agent self-reflection
- **SetupVmEnvironmentToolCall** - VM setup for cloud execution
- **ExaSearchToolCall** / **ExaFetchToolCall** - Exa AI integration
- **WriteShellStdinToolCall** - Shell stdin interaction
- **RecordScreenToolCall** - Screen recording capability

### 5. Truncation Strategy

TruncatedToolCall preserves:
- Reference to original blob
- Error messages (for context)
- Empty args placeholder

This allows context window management while maintaining error visibility.

---

## Protocol Flow

1. **Tool Request**: Server sends StreamedBackPartialToolCall (tool ID, name)
2. **Parameters**: Server sends StreamedBackToolCall with full params
3. **Execution**: Client executes tool, streams deltas if applicable
4. **Result**: Client sends ClientSideToolV2Result back
5. **Conversation**: Tool call stored as ConversationStep

---

## Related Documents

- TASK-26-tool-schemas.md - Detailed ClientSideToolV2 schemas
- TASK-7-protobuf-schemas.md - Overall protobuf architecture

---

## Follow-Up Investigations Needed

1. **TASK-52a**: ExaSearch and ExaFetch full parameter schemas
2. **TASK-52b**: RecordScreenToolCall capabilities and format
3. **TASK-52c**: ComputerUseToolCall action types (PIr/AIr)
4. **TASK-52d**: BuiltinTool enum values and mapping to ClientSideToolV2
5. **TASK-52e**: Tool execution approval flow analysis
