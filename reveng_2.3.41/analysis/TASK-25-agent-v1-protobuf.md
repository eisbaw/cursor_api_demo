# TASK-25: agent.v1 Protobuf Schema Analysis

**Source:** `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
**Analysis Date:** 2026-01-28
**Cursor Version:** 2.3.41

## Overview

The `agent.v1` package implements Cursor's AI agent communication protocol using Protocol Buffers. The schema defines:
- **~300+ message types** across 50+ proto source files
- **16 enum types** for various state and type definitions
- **6 gRPC services** for agent communication

## Protobuf Source Files

The following proto files are bundled in the source (paths from `out-build/proto/agent/v1/`):

| Proto File | Primary Purpose |
|------------|-----------------|
| `agent_pb.js` | Core agent messages (ToolCall, TaskArgs, ConversationStep, etc.) |
| `agent_service_pb.js` | AgentService messages (AgentClientMessage, AgentServerMessage) |
| `exec_pb.js` | Exec protocol (ExecServerMessage, ExecClientMessage) |
| `shell_exec_pb.js` | Shell execution (ShellArgs, ShellResult, ShellStream) |
| `sandbox_pb.js` | Sandbox policy definitions |
| `selected_context_pb.js` | Context selection (SelectedFile, SelectedImage, etc.) |
| `edit_tool_pb.js` | Edit tool protocol |
| `read_tool_pb.js` | Read tool protocol |
| `grep_tool_pb.js`, `grep_exec_pb.js` | Grep operations |
| `glob_tool_pb.js` | Glob operations |
| `ls_exec_pb.js`, `ls_tool_pb.js` | Directory listing |
| `write_exec_pb.js` | File write operations |
| `delete_exec_pb.js`, `delete_tool_pb.js` | File delete operations |
| `mcp_pb.js`, `mcp_exec_pb.js`, `mcp_tool_pb.js` | MCP integration |
| `web_search_tool_pb.js` | Web search functionality |
| `fetch_tool_pb.js`, `fetch_exec_pb.js` | URL fetch operations |
| `todo_tool_pb.js` | Todo list management |
| `computer_use_tool_pb.js` | Computer use/automation |
| `cursor_rules_pb.js` | Cursor rules configuration |
| `cursor_packages_pb.js` | Package definitions |
| `subagents_pb.js` | Sub-agent types |
| `diagnostics_exec_pb.js` | Diagnostics operations |
| `request_context_exec_pb.js` | Request context |
| `kv_pb.js` | Key-value blob storage |
| `background_shell_exec_pb.js` | Background shell execution |
| `background_subagent_exec_pb.js` | Background sub-agent execution |
| `record_screen_exec_pb.js`, `record_screen_tool_pb.js` | Screen recording |
| `create_plan_tool_pb.js` | Plan creation |
| `switch_mode_tool_pb.js` | Mode switching |
| `exa_search_tool_pb.js`, `exa_fetch_tool_pb.js` | Exa search integration |
| `ask_question_tool_pb.js` | User question prompts |
| `reflect_tool_pb.js` | Reflection tool |
| `setup_vm_environment_tool_pb.js` | VM environment setup |
| `semsearch_tool_pb.js` | Semantic search |
| `read_lints_tool_pb.js` | Linting operations |
| `mcp_resource_tool_pb.js` | MCP resource operations |
| `apply_agent_diff_tool_pb.js` | Diff application |
| `generate_image_tool_pb.js` | Image generation |
| `write_shell_stdin_tool_pb.js` | Shell stdin writing |
| `utils_pb.js` | Utility types (Range, Position, Error) |
| `repo_pb.js` | Repository info |

---

## Services

### 1. AgentService
**Full Name:** `agent.v1.AgentService`

| Method | Request Type | Response Type | Streaming |
|--------|--------------|---------------|-----------|
| `Run` | `AgentClientMessage` | `AgentServerMessage` | BiDiStreaming |
| `RunSSE` | (SSE request type) | `AgentServerMessage` | ServerStreaming |
| `RunPoll` | (Poll request type) | (Poll response type) | ServerStreaming |
| `NameAgent` | `NameAgentRequest` | `NameAgentResponse` | Unary |
| `GetUsableModels` | `GetUsableModelsRequest` | `GetUsableModelsResponse` | Unary |
| `GetDefaultModelForCli` | `GetDefaultModelForCliRequest` | `GetDefaultModelForCliResponse` | Unary |
| `GetAllowedModelIntents` | `GetAllowedModelIntentsRequest` | `GetAllowedModelIntentsResponse` | Unary |

### 2. ExecService
**Full Name:** `agent.v1.ExecService`

| Method | Request Type | Response Type | Streaming |
|--------|--------------|---------------|-----------|
| `Exec` | `ExecServerMessage` | `ExecStreamElement` | ServerStreaming |

### 3. ControlService
**Full Name:** `agent.v1.ControlService`

| Method | Request Type | Response Type | Streaming |
|--------|--------------|---------------|-----------|
| `Ping` | PingRequest | PingResponse | Unary |
| `Exec` | ExecRequest | ExecResponse | ServerStreaming |
| `ReadTextFile` | ReadTextFileRequest | ReadTextFileResponse | Unary |
| `WriteTextFile` | WriteTextFileRequest | WriteTextFileResponse | Unary |
| `ReadBinaryFile` | ReadBinaryFileRequest | ReadBinaryFileResponse | Unary |
| `WriteBinaryFile` | WriteBinaryFileRequest | WriteBinaryFileResponse | Unary |
| `GetDiff` | GetDiffRequest | GetDiffResponse | Unary |
| `GetWorkspaceChangesHash` | GetWorkspaceChangesHashRequest | GetWorkspaceChangesHashResponse | Unary |
| `RefreshGithubAccessToken` | RefreshGithubAccessTokenRequest | RefreshGithubAccessTokenResponse | Unary |
| `WarmRemoteAccessServer` | WarmRemoteAccessServerRequest | WarmRemoteAccessServerResponse | Unary |
| `ListArtifacts` | ListArtifactsRequest | ListArtifactsResponse | Unary |
| `UploadArtifacts` | UploadArtifactsRequest | UploadArtifactsResponse | Unary |
| `GetMcpRefreshTokens` | GetMcpRefreshTokensRequest | GetMcpRefreshTokensResponse | Unary |

### 4. PrivateWorkerBridgeExternalService
**Full Name:** `agent.v1.PrivateWorkerBridgeExternalService`

| Method | Request Type | Response Type | Streaming |
|--------|--------------|---------------|-----------|
| `Connect` | `Frame` | `Frame` | BiDiStreaming |

### 5. LifecycleService
**Full Name:** `agent.v1.LifecycleService`

| Method | Request Type | Response Type | Streaming |
|--------|--------------|---------------|-----------|
| `ResetInstance` | `Empty` | `Empty` | Unary |
| `RenewInstance` | `Empty` | `Empty` | Unary |

### 6. PtyHostService
**Full Name:** `agent.v1.PtyHostService`

PTY (pseudo-terminal) management service.

---

## Enum Definitions

### AgentMode
```protobuf
enum AgentMode {
  AGENT_MODE_UNSPECIFIED = 0;
  AGENT_MODE_AGENT = 1;
  AGENT_MODE_ASK = 2;
  AGENT_MODE_PLAN = 3;
  AGENT_MODE_DEBUG = 4;
  AGENT_MODE_TRIAGE = 5;
}
```

### SandboxPolicy.Type
```protobuf
enum SandboxPolicy.Type {
  TYPE_UNSPECIFIED = 0;
  TYPE_INSECURE_NONE = 1;
  TYPE_WORKSPACE_READWRITE = 2;
  TYPE_WORKSPACE_READONLY = 3;
}
```

### ShellAbortReason
```protobuf
enum ShellAbortReason {
  SHELL_ABORT_REASON_UNSPECIFIED = 0;
  SHELL_ABORT_REASON_USER_ABORT = 1;
  SHELL_ABORT_REASON_TIMEOUT = 2;
}
```

### AppliedAgentChange.ChangeType
```protobuf
enum AppliedAgentChange.ChangeType {
  CHANGE_TYPE_UNSPECIFIED = 0;
  CHANGE_TYPE_CREATED = 1;
  CHANGE_TYPE_MODIFIED = 2;
  CHANGE_TYPE_DELETED = 3;
}
```

### MouseButton
```protobuf
enum MouseButton {
  MOUSE_BUTTON_UNSPECIFIED = 0;
  MOUSE_BUTTON_LEFT = 1;
  MOUSE_BUTTON_RIGHT = 2;
  MOUSE_BUTTON_MIDDLE = 3;
  MOUSE_BUTTON_BACK = 4;
  MOUSE_BUTTON_FORWARD = 5;
}
```

### ScrollDirection
```protobuf
enum ScrollDirection {
  SCROLL_DIRECTION_UNSPECIFIED = 0;
  SCROLL_DIRECTION_UP = 1;
  SCROLL_DIRECTION_DOWN = 2;
  SCROLL_DIRECTION_LEFT = 3;
  SCROLL_DIRECTION_RIGHT = 4;
}
```

### PackageType
```protobuf
enum PackageType {
  PACKAGE_TYPE_UNSPECIFIED = 0;
  PACKAGE_TYPE_CURSOR_PROJECT = 1;
  PACKAGE_TYPE_CURSOR_PERSONAL = 2;
  PACKAGE_TYPE_CLAUDE_SKILL = 3;
  PACKAGE_TYPE_CLAUDE_PLUGIN = 4;
}
```

### CursorRuleSource
```protobuf
enum CursorRuleSource {
  CURSOR_RULE_SOURCE_UNSPECIFIED = 0;
  CURSOR_RULE_SOURCE_TEAM = 1;
  CURSOR_RULE_SOURCE_USER = 2;
}
```

### CustomSubagentPermissionMode
```protobuf
enum CustomSubagentPermissionMode {
  CUSTOM_SUBAGENT_PERMISSION_MODE_UNSPECIFIED = 0;
  CUSTOM_SUBAGENT_PERMISSION_MODE_DEFAULT = 1;
  CUSTOM_SUBAGENT_PERMISSION_MODE_READONLY = 2;
}
```

### DiagnosticSeverity
```protobuf
enum DiagnosticSeverity {
  DIAGNOSTIC_SEVERITY_UNSPECIFIED = 0;
  DIAGNOSTIC_SEVERITY_ERROR = 1;
  DIAGNOSTIC_SEVERITY_WARNING = 2;
  DIAGNOSTIC_SEVERITY_INFORMATION = 3;
  DIAGNOSTIC_SEVERITY_HINT = 4;
}
```

### RecordingMode
```protobuf
enum RecordingMode {
  RECORDING_MODE_UNSPECIFIED = 0;
  RECORDING_MODE_START_RECORDING = 1;
  RECORDING_MODE_SAVE_RECORDING = 2;
  RECORDING_MODE_DISCARD_RECORDING = 3;
}
```

### RequestedFilePathRejectedReason
```protobuf
enum RequestedFilePathRejectedReason {
  REQUESTED_FILE_PATH_REJECTED_REASON_UNSPECIFIED = 0;
  REQUESTED_FILE_PATH_REJECTED_REASON_SLASHES_NOT_ALLOWED = 1;
}
```

### TodoStatus
```protobuf
enum TodoStatus {
  TODO_STATUS_UNSPECIFIED = 0;
  TODO_STATUS_PENDING = 1;
  TODO_STATUS_IN_PROGRESS = 2;
  TODO_STATUS_COMPLETED = 3;
  TODO_STATUS_CANCELLED = 4;
}
```

### BackgroundSubagentCompletionStatus
```protobuf
enum BackgroundSubagentCompletionStatus {
  BACKGROUND_SUBAGENT_COMPLETION_STATUS_UNSPECIFIED = 0;
  BACKGROUND_SUBAGENT_COMPLETION_STATUS_COMPLETED = 1;
  BACKGROUND_SUBAGENT_COMPLETION_STATUS_FAILED = 2;
  BACKGROUND_SUBAGENT_COMPLETION_STATUS_ABORTED = 3;
}
```

### Frame.Kind
```protobuf
enum Frame.Kind {
  KIND_UNSPECIFIED = 0;
  KIND_REQUEST = 1;
  KIND_RESPONSE = 2;
  KIND_ERROR = 3;
}
```

### ArtifactUploadStatus / ArtifactUploadDispatchStatus
Additional artifact-related enums exist for upload tracking.

---

## Key Message Definitions

### Core Communication Messages

#### AgentClientMessage
Top-level client-to-server message wrapper.
```protobuf
message AgentClientMessage {
  oneof message {
    AgentRunRequest run_request = 1;
    ExecClientMessage exec_client_message = 2;
    ExecClientControlMessage exec_client_control_message = 5;
    KvClientMessage kv_client_message = 3;
    ConversationAction conversation_action = 4;
    InteractionResponse interaction_response = 6;
    ClientHeartbeat client_heartbeat = 7;
  }
}
```

#### AgentServerMessage
Top-level server-to-client message wrapper.
```protobuf
message AgentServerMessage {
  oneof message {
    InteractionUpdate interaction_update = 1;
    ExecServerMessage exec_server_message = 2;
    ExecServerControlMessage exec_server_control_message = 5;
    ConversationStateStructure conversation_checkpoint_update = 3;
    KvServerMessage kv_server_message = 4;
    InteractionQuery interaction_query = 7;
  }
}
```

#### AgentRunRequest
Initial request to start agent execution.
```protobuf
message AgentRunRequest {
  ConversationStateStructure conversation_state = 1;
  ConversationAction action = 2;
  ModelDetails model_details = 3;
  McpTools mcp_tools = 4;
  optional string conversation_id = 5;
  optional McpFileSystemOptions mcp_file_system_options = 6;
  optional SkillOptions skill_options = 7;
}
```

### Execution Protocol

#### ExecServerMessage
Server-initiated execution requests.
```protobuf
message ExecServerMessage {
  uint32 id = 1;
  string exec_id = 15;
  optional SpanContext span_context = 19;
  oneof message {
    ShellArgs shell_args = 2;
    WriteArgs write_args = 3;
    DeleteArgs delete_args = 4;
    GrepArgs grep_args = 5;
    ReadArgs read_args = 7;
    LsArgs ls_args = 8;
    DiagnosticsArgs diagnostics_args = 9;
    RequestContextArgs request_context_args = 10;
    McpArgs mcp_args = 11;
    ShellArgs shell_stream_args = 14;
    BackgroundShellSpawnArgs background_shell_spawn_args = 16;
    ListMcpResourcesExecArgs list_mcp_resources_exec_args = 17;
    ReadMcpResourceExecArgs read_mcp_resource_exec_args = 18;
    FetchArgs fetch_args = 20;
    RecordScreenArgs record_screen_args = 21;
    ComputerUseArgs computer_use_args = 22;
    WriteShellStdinArgs write_shell_stdin_args = 23;
    BackgroundSubagentSpawnArgs background_subagent_spawn_args = 24;
    BackgroundSubagentAbortArgs background_subagent_abort_args = 26;
  }
}
```

#### ExecClientMessage
Client responses to execution requests.
```protobuf
message ExecClientMessage {
  uint32 id = 1;
  string exec_id = 15;
  oneof message {
    ShellResult shell_result = 2;
    WriteResult write_result = 3;
    DeleteResult delete_result = 4;
    GrepResult grep_result = 5;
    ReadResult read_result = 7;
    LsResult ls_result = 8;
    DiagnosticsResult diagnostics_result = 9;
    RequestContextResult request_context_result = 10;
    McpResult mcp_result = 11;
    ShellStream shell_stream = 14;
    BackgroundShellSpawnResult background_shell_spawn_result = 16;
    ListMcpResourcesExecResult list_mcp_resources_exec_result = 17;
    ReadMcpResourceExecResult read_mcp_resource_exec_result = 18;
    // ... more result types
  }
}
```

### Shell Execution

#### ShellArgs
```protobuf
message ShellArgs {
  string command = 1;
  string working_directory = 2;
  int32 timeout = 3;
  string tool_call_id = 4;
  repeated string simple_commands = 5;
  bool has_input_redirect = 6;
  bool has_output_redirect = 7;
  ShellCommandParsingResult parsing_result = 8;
  optional SandboxPolicy requested_sandbox_policy = 9;
  optional uint64 file_output_threshold_bytes = 10;
  bool is_background = 11;
  bool skip_approval = 12;
}
```

#### ShellResult
```protobuf
message ShellResult {
  optional SandboxPolicy sandbox_policy = 101;
  optional bool is_background = 102;
  optional string terminals_folder = 103;
  oneof result {
    ShellSuccess success = 1;
    ShellFailure failure = 2;
    ShellTimeout timeout = 3;
    ShellRejected rejected = 4;
    ShellSpawnError spawn_error = 5;
    ShellPermissionDenied permission_denied = 7;
  }
}
```

#### ShellStream (for streaming output)
```protobuf
message ShellStream {
  oneof stream {
    ShellStreamStdout stdout = 1;
    ShellStreamStderr stderr = 2;
    ShellStreamExit exit = 3;
    ShellStreamStart start = 5;
  }
}
```

### Sandbox Policy

#### SandboxPolicy
```protobuf
message SandboxPolicy {
  SandboxPolicy.Type type = 1;
  optional bool network_access = 2;
  repeated string additional_readwrite_paths = 3;
  repeated string additional_readonly_paths = 4;
  optional string debug_output_dir = 5;
  optional bool block_git_writes = 6;
  optional bool disable_tmp_write = 7;
}
```

### Tool Call System

#### ToolCall
Large oneof containing all possible tool types.
```protobuf
message ToolCall {
  oneof tool {
    ShellToolCall shell_tool_call = 1;
    DeleteToolCall delete_tool_call = 3;
    GlobToolCall glob_tool_call = 4;
    GrepToolCall grep_tool_call = 5;
    ReadToolCall read_tool_call = 8;
    UpdateTodosToolCall update_todos_tool_call = 9;
    ReadTodosToolCall read_todos_tool_call = 10;
    EditToolCall edit_tool_call = 12;
    LsToolCall ls_tool_call = 13;
    ReadLintsToolCall read_lints_tool_call = 14;
    McpToolCall mcp_tool_call = 15;
    SemSearchToolCall sem_search_tool_call = 16;
    CreatePlanToolCall create_plan_tool_call = 17;
    WebSearchToolCall web_search_tool_call = 18;
    TaskToolCall task_tool_call = 19;
    ListMcpResourcesToolCall list_mcp_resources_tool_call = 20;
    ReadMcpResourceToolCall read_mcp_resource_tool_call = 21;
    ApplyAgentDiffToolCall apply_agent_diff_tool_call = 22;
    AskQuestionToolCall ask_question_tool_call = 23;
    FetchToolCall fetch_tool_call = 24;
    SwitchModeToolCall switch_mode_tool_call = 25;
    ExaSearchToolCall exa_search_tool_call = 26;
    ExaFetchToolCall exa_fetch_tool_call = 27;
    GenerateImageToolCall generate_image_tool_call = 28;
    RecordScreenToolCall record_screen_tool_call = 29;
    ComputerUseToolCall computer_use_tool_call = 30;
    WriteShellStdinToolCall write_shell_stdin_tool_call = 31;
    ReflectToolCall reflect_tool_call = 32;
    SetupVmEnvironmentToolCall setup_vm_environment_tool_call = 33;
    TruncatedToolCall truncated_tool_call = 34;
  }
}
```

### Interaction Updates (Streaming)

#### InteractionUpdate
Real-time updates during agent execution.
```protobuf
message InteractionUpdate {
  oneof message {
    TextDeltaUpdate text_delta = 1;
    PartialToolCallUpdate partial_tool_call = 7;
    ToolCallDeltaUpdate tool_call_delta = 15;
    ToolCallStartedUpdate tool_call_started = 2;
    ToolCallCompletedUpdate tool_call_completed = 3;
    ThinkingDeltaUpdate thinking_delta = 4;
    ThinkingCompletedUpdate thinking_completed = 5;
    UserMessageAppendedUpdate user_message_appended = 6;
    TokenDeltaUpdate token_delta = 8;
    SummaryUpdate summary = 9;
    SummaryStartedUpdate summary_started = 10;
    SummaryCompletedUpdate summary_completed = 11;
    ShellOutputDeltaUpdate shell_output_delta = 12;
    HeartbeatUpdate heartbeat = 13;
    TurnEndedUpdate turn_ended = 14;
    StepStartedUpdate step_started = 16;
    StepCompletedUpdate step_completed = 17;
  }
}
```

### Conversation State

#### ConversationState
```protobuf
message ConversationState {
  repeated string root_prompt_messages_json = 1;
  repeated ConversationTurn turns = 8;
  repeated TodoItem todos = 3;
  repeated string pending_tool_calls = 4;
  ConversationTokenDetails token_details = 5;
  optional ConversationSummary summary = 6;
  optional ConversationPlan plan = 7;
  optional ConversationSummaryArchive summary_archive = 9;
  map<string, FileState> file_states = 10;
  repeated ConversationSummaryArchive summary_archives = 11;
}
```

#### ConversationStateStructure
Extended version with additional fields.
```protobuf
message ConversationStateStructure {
  repeated bytes turns_old = 2;
  repeated bytes root_prompt_messages_json = 1;
  repeated bytes turns = 8;
  repeated bytes todos = 3;
  repeated string pending_tool_calls = 4;
  ConversationTokenDetails token_details = 5;
  optional bytes summary = 6;
  optional bytes plan = 7;
  repeated string previous_workspace_uris = 9;
  optional AgentMode mode = 10;
  optional bytes summary_archive = 11;
  map<string, bytes> file_states = 12;
  map<string, FileStateStructure> file_states_v2 = 14;
  repeated bytes summary_archives = 13;
  repeated StepTiming turn_timings = 15;
  map<string, SubagentPersistedState> subagent_states = 16;
  int32 self_summary_count = 17;
  repeated string read_paths = 18;
}
```

### Context Selection

#### SelectedContext
```protobuf
message SelectedContext {
  oneof context {
    SelectedImage selected_image = 1;
    SelectedFile selected_file = 2;
    SelectedCodeSelection selected_code_selection = 3;
    SelectedTerminal selected_terminal = 4;
    SelectedTerminalSelection selected_terminal_selection = 5;
    SelectedFolder selected_folder = 6;
    SelectedExternalLink selected_external_link = 7;
    SelectedCursorRule selected_cursor_rule = 8;
    SelectedGitDiff selected_git_diff = 9;
    SelectedGitDiffFromBranchToMain selected_git_diff_from_branch_to_main = 10;
    SelectedGitCommit selected_git_commit = 11;
    SelectedPullRequest selected_pull_request = 12;
    SelectedGitPRDiffSelection selected_git_pr_diff_selection = 13;
    SelectedCursorCommand selected_cursor_command = 14;
    SelectedDocumentation selected_documentation = 15;
    SelectedPastChat selected_past_chat = 16;
    SelectedConsoleLog selected_console_log = 17;
    SelectedUIElement selected_ui_element = 18;
  }
}
```

### Model Configuration

#### ModelDetails
```protobuf
message ModelDetails {
  // Fields include model configuration, credentials, etc.
  // References ApiKeyCredentials, AzureCredentials, BedrockCredentials
}
```

### MCP Integration

#### McpTools
```protobuf
message McpTools {
  repeated McpDescriptor descriptors = 1;
}
```

#### McpDescriptor
```protobuf
message McpDescriptor {
  string server_name = 1;
  repeated McpToolDescriptor tools = 2;
  McpInstructions instructions = 3;
}
```

---

## Scalar Type Reference

The code uses protobuf-es scalar type constants:
- `T: 5` = int32
- `T: 8` = bool
- `T: 9` = string
- `T: 12` = bytes
- `T: 13` = uint32
- `T: 4` = uint64

---

## Wire Protocol Notes

1. **BiDi Streaming**: The main `AgentService.Run` method uses bidirectional streaming, allowing interleaved requests/responses.

2. **Message IDs**: `ExecServerMessage` and `ExecClientMessage` use `id` (uint32) for request-response correlation.

3. **Exec ID**: An additional `exec_id` (string) field provides execution context tracking.

4. **Span Context**: OpenTelemetry-style tracing via `SpanContext` with trace_id, span_id.

5. **Oneof Pattern**: Extensively used for polymorphic message types (results, tool calls, updates).

---

## Investigation Paths Identified

1. **Frame protocol**: The `Frame` message with `KIND_REQUEST/RESPONSE/ERROR` suggests a lower-level RPC framing protocol worth investigating.

2. **Artifact Upload**: `ArtifactUploadStatus` and `ArtifactUploadDispatchStatus` enums suggest a file upload system.

3. **Computer Use**: Full automation protocol with mouse/keyboard actions (`MouseMoveAction`, `ClickAction`, `TypeAction`, etc.).

4. **Subagent System**: Background subagents with their own persisted state (`SubagentPersistedState`).

5. **Plan Execution**: `CreatePlanToolCall`, `StartPlanAction`, `ExecutePlanAction` suggest a planning system.

---

## Related Tasks to Create

Based on this analysis, the following investigation tasks are recommended:
- Extract computer_use.proto messages for automation protocol
- Document MCP (Model Context Protocol) integration details
- Analyze Frame-based low-level protocol for worker bridge
- Extract artifact upload/download protocol
