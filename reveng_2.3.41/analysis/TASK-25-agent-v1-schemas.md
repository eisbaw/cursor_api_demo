# TASK-25: Agent.v1 Protobuf Message Schemas Analysis

**Source:** `reveng_2.3.41/beautified/workbench.desktop.main.js`
**Analysis Date:** 2026-01-27

## Overview

The Cursor IDE agent system (`agent.v1.*` namespace) provides the infrastructure for the agentic coding assistant. This namespace is **distinct from** `aiserver.v1` - while `aiserver.v1` handles communication with Cursor's AI servers, `agent.v1` handles the local agent execution, tool calls, and conversation state management.

### Key Differences from aiserver.v1

| Aspect | aiserver.v1 | agent.v1 |
|--------|-------------|----------|
| Purpose | Cloud AI server communication | Local agent execution |
| Streaming | Server streaming responses | Bidirectional exec messages |
| Tools | Tool definitions | Tool args/results |
| State | Chat request/response | ConversationState management |

### Scalar Type Reference

The `T` field in scalar types corresponds to protobuf scalar type numbers:
- `T: 3` = int64
- `T: 4` = uint64
- `T: 5` = int32
- `T: 8` = bool
- `T: 9` = string
- `T: 12` = bytes
- `T: 13` = uint32

---

## Services

### 1. AgentService (`agent.v1.AgentService`)

**Location:** Line ~555871

The primary agent service handling run requests and model operations.

```protobuf
service AgentService {
  // Main bidirectional streaming agent run
  rpc Run(stream AgentClientMessage) returns (stream AgentServerMessage);  // BiDiStreaming

  // Server-streaming SSE variant
  rpc RunSSE(aiserver.v1.BidiRequestId) returns (stream AgentServerMessage);  // ServerStreaming

  // Polling variant for environments without streaming
  rpc RunPoll(aiserver.v1.BidiPollRequest) returns (stream aiserver.v1.BidiPollResponse);  // ServerStreaming

  // Agent naming
  rpc NameAgent(NameAgentRequest) returns (NameAgentResponse);  // Unary

  // Model configuration
  rpc GetUsableModels(GetUsableModelsRequest) returns (GetUsableModelsResponse);  // Unary
  rpc GetDefaultModelForCli(GetDefaultModelForCliRequest) returns (GetDefaultModelForCliResponse);  // Unary
  rpc GetAllowedModelIntents(GetAllowedModelIntentsRequest) returns (GetAllowedModelIntentsResponse);  // Unary
}
```

**Note:** The SSE and Poll variants use `aiserver.v1.Bidi*` types for transport, wrapping agent messages.

### 2. ControlService (`agent.v1.ControlService`)

**Location:** Line ~807539

Low-level control operations for agent execution environment.

```protobuf
service ControlService {
  rpc Ping(PingRequest) returns (PingResponse);  // Unary
  rpc Exec(ExecRequest) returns (stream ExecResponse);  // ServerStreaming
  rpc ReadTextFile(ReadTextFileRequest) returns (ReadTextFileResponse);  // Unary
  rpc WriteTextFile(WriteTextFileRequest) returns (WriteTextFileResponse);  // Unary
  rpc ReadBinaryFile(ReadBinaryFileRequest) returns (ReadBinaryFileResponse);  // Unary
  rpc WriteBinaryFile(WriteBinaryFileRequest) returns (WriteBinaryFileResponse);  // Unary
  rpc GetDiff(GetDiffRequest) returns (DiffResult);  // Unary
  rpc GetWorkspaceChangesHash(GetWorkspaceChangesHashRequest) returns (GetWorkspaceChangesHashResponse);  // Unary
  rpc RefreshGithubAccessToken(RefreshGithubAccessTokenRequest) returns (RefreshGithubAccessTokenResponse);  // Unary
  rpc WarmRemoteAccessServer(WarmRemoteAccessServerRequest) returns (WarmRemoteAccessServerResponse);  // Unary
  rpc ListArtifacts(ListArtifactsRequest) returns (ListArtifactsResponse);  // Unary
  rpc UploadArtifacts(UploadArtifactsRequest) returns (UploadArtifactsResponse);  // Unary
  rpc GetMcpRefreshTokens(GetMcpRefreshTokensRequest) returns (GetMcpRefreshTokensResponse);  // Unary
}
```

### 3. ExecService (`agent.v1.ExecService`)

**Location:** Line ~807664

Dedicated execution service for tool operations.

```protobuf
service ExecService {
  rpc Exec(ExecServerMessage) returns (stream ExecStreamElement);  // ServerStreaming
}

message ExecStreamElement {
  oneof element {
    ExecClientMessage exec_client_message = 1;
    ExecClientControlMessage exec_client_control_message = 2;
  }
}
```

### 4. LifecycleService (`agent.v1.LifecycleService`)

**Location:** Line ~807781

Instance lifecycle management.

```protobuf
service LifecycleService {
  rpc ResetInstance(Empty) returns (Empty);  // Unary
  rpc RenewInstance(Empty) returns (Empty);  // Unary
}
```

### 5. PrivateWorkerBridgeExternalService (`agent.v1.PrivateWorkerBridgeExternalService`)

**Location:** Line ~807770

Bridge service for external worker communication.

```protobuf
service PrivateWorkerBridgeExternalService {
  rpc Connect(stream BridgeMessage) returns (stream BridgeMessage);  // BiDiStreaming
}
```

---

## Core Message Types

### AgentClientMessage (`agent.v1.AgentClientMessage`)

**Location:** Line ~142712

Client-to-server bidirectional streaming message.

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

### AgentServerMessage (`agent.v1.AgentServerMessage`)

**Location:** Line ~142781

Server-to-client bidirectional streaming message.

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

### AgentRunRequest (`agent.v1.AgentRunRequest`)

**Location:** Line ~141423

Initial request to start an agent run.

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

---

## Conversation State

### ConversationStateStructure (`agent.v1.ConversationStateStructure`)

**Location:** Line ~141053

The complete conversation state, persisted across turns.

```protobuf
message ConversationStateStructure {
  repeated bytes turns_old = 2;  // Legacy turns
  repeated bytes root_prompt_messages_json = 1;
  repeated bytes turns = 8;  // Current turns (binary encoded)
  repeated bytes todos = 3;
  repeated string pending_tool_calls = 4;
  ConversationTokenDetails token_details = 5;
  optional bytes summary = 6;
  optional bytes plan = 7;
  repeated string previous_workspace_uris = 12;
  map<string, FileStateStructure> file_states = 9;
  map<string, bytes> file_states_v2 = 18;
  repeated ConversationSummaryArchive summary_archives = 11;
  repeated StepTiming turn_timings = 15;
  map<string, SubagentPersistedState> subagent_states = 19;
  int32 self_summary_count = 20;
  repeated string read_paths = 21;
}
```

### ConversationAction (`agent.v1.ConversationAction`)

**Location:** Line ~139804

User actions that drive the conversation.

```protobuf
message ConversationAction {
  oneof action {
    UserMessageAction user_message_action = 1;
    ResumeAction resume_action = 2;
    CancelAction cancel_action = 3;
    SummarizeAction summarize_action = 4;
    ShellCommandAction shell_command_action = 5;
    StartPlanAction start_plan_action = 6;
    ExecutePlanAction execute_plan_action = 7;
    AsyncAskQuestionCompletionAction async_ask_question_completion_action = 8;
    BackgroundSubagentCompletionAction background_subagent_completion_action = 9;
  }
}
```

### UserMessageAction (`agent.v1.UserMessageAction`)

**Location:** Line ~139883

```protobuf
message UserMessageAction {
  UserMessage user_message = 1;
  RequestContext request_context = 2;
  optional bool send_to_interaction_listener = 3;
}
```

---

## Interaction Updates (Streaming)

### InteractionUpdate (`agent.v1.InteractionUpdate`)

**Location:** Line ~142049

The main streaming update type sent during agent execution.

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

### InteractionQuery (`agent.v1.InteractionQuery`)

**Location:** Line ~142178

Server-initiated queries requiring client response.

```protobuf
message InteractionQuery {
  uint32 id = 1;
  oneof query {
    WebSearchRequestQuery web_search_request_query = 2;
    ExaSearchRequestQuery exa_search_request_query = 3;
    ExaFetchRequestQuery exa_fetch_request_query = 4;
    SwitchModeRequestQuery switch_mode_request_query = 5;
    AskQuestionInteractionQuery ask_question_interaction_query = 6;
    CreatePlanRequestQuery create_plan_request_query = 7;
  }
}
```

---

## Tool Execution

### ExecServerMessage (`agent.v1.ExecServerMessage`)

**Location:** Line ~132415

Server-to-client execution requests.

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

### ExecClientMessage (`agent.v1.ExecClientMessage`)

**Location:** Line ~132572

Client-to-server execution results.

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
    FetchResult fetch_result = 20;
    RecordScreenResult record_screen_result = 21;
    ComputerUseResult computer_use_result = 22;
    WriteShellStdinResult write_shell_stdin_result = 23;
    BackgroundSubagentSpawnResult background_subagent_spawn_result = 24;
    BackgroundSubagentAbortResult background_subagent_abort_result = 26;
  }
}
```

---

## Tool Types

### ToolCall (`agent.v1.ToolCall`)

**Location:** Line ~139348

The main tool call union type containing all available tools.

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

---

## Shell Execution

### ShellArgs (`agent.v1.ShellArgs`)

**Location:** Line ~94412

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

### ShellResult (`agent.v1.ShellResult`)

**Location:** Line ~94502

```protobuf
message ShellResult {
  oneof result {
    ShellSuccess success = 1;
    ShellFailure failure = 2;
    ShellTimeout timeout = 3;
    ShellRejected rejected = 4;
    ShellPermissionDenied permission_denied = 5;
    ShellSpawnError spawn_error = 6;
    ShellPartialResult partial_result = 7;
  }
}
```

### ShellSuccess (`agent.v1.ShellSuccess`)

**Location:** Line ~94827

```protobuf
message ShellSuccess {
  int32 exit_code = 1;
  string stdout = 2;
  string stderr = 3;
  optional OutputLocation stdout_output_location = 4;
  optional OutputLocation stderr_output_location = 5;
  optional bool interrupted = 6;
  optional string interrupted_reason = 7;
}
```

### SandboxPolicy (`agent.v1.SandboxPolicy`)

**Location:** Line ~94193

```protobuf
message SandboxPolicy {
  Type type = 1;
  optional bool network_access = 2;
  repeated string additional_readwrite_paths = 3;
  repeated string additional_readonly_paths = 4;
  optional string debug_output_dir = 5;
  optional bool block_git_writes = 6;
  optional bool disable_tmp_write = 7;

  enum Type {
    TYPE_UNSPECIFIED = 0;
    TYPE_INSECURE_NONE = 1;
    TYPE_WORKSPACE_READWRITE = 2;
    TYPE_WORKSPACE_READONLY = 3;
  }
}
```

---

## Computer Use (Anthropic Claude Computer Use)

### ComputerUseArgs (`agent.v1.ComputerUseArgs`)

**Location:** Line ~103389

```protobuf
message ComputerUseArgs {
  string tool_call_id = 1;
  repeated ComputerUseAction actions = 2;
}
```

### ComputerUseAction (`agent.v1.ComputerUseAction`)

**Location:** Line ~103427

```protobuf
message ComputerUseAction {
  oneof action {
    MouseMoveAction mouse_move = 1;
    ClickAction click = 2;
    MouseDownAction mouse_down = 3;
    MouseUpAction mouse_up = 4;
    DragAction drag = 5;
    ScrollAction scroll = 6;
    TypeAction type = 7;
    KeyAction key = 8;
    WaitAction wait = 9;
    ScreenshotAction screenshot = 10;
    CursorPositionAction cursor_position = 11;
  }
}
```

### ComputerUseResult (`agent.v1.ComputerUseResult`)

**Location:** Line ~103886

```protobuf
message ComputerUseResult {
  oneof result {
    ComputerUseSuccess success = 1;
    ComputerUseError error = 2;
  }
}

message ComputerUseSuccess {
  optional bytes screenshot = 1;
  optional Coordinate cursor_position = 2;
  optional string screenshot_blob_id = 3;
}
```

---

## File Operations

### ReadArgs/ReadResult (`agent.v1.Read*`)

**Location:** Line ~130260

```protobuf
message ReadArgs {
  string path = 1;
  optional int32 start_line = 2;
  optional int32 end_line = 3;
}

message ReadResult {
  oneof result {
    ReadSuccess success = 1;
    ReadFileNotFound file_not_found = 2;
    ReadPermissionDenied permission_denied = 3;
    ReadInvalidFile invalid_file = 4;
    ReadError error = 5;
    ReadRejected rejected = 6;
  }
}

message ReadSuccess {
  string content = 1;
  int32 line_count = 2;
  int32 start_line = 3;
  int32 end_line = 4;
  optional bool is_truncated = 5;
}
```

### WriteArgs/WriteResult (`agent.v1.Write*`)

**Location:** Line ~129009

```protobuf
message WriteArgs {
  string path = 1;
  string content = 2;
  optional bool create_directories = 3;
}

message WriteResult {
  oneof result {
    WriteSuccess success = 1;
    WritePermissionDenied permission_denied = 2;
    WriteNoSpace no_space = 3;
    WriteError error = 4;
    WriteRejected rejected = 5;
  }
}
```

### EditArgs/EditResult (`agent.v1.Edit*`)

**Location:** Line ~133857

```protobuf
message EditArgs {
  string path = 1;
  string old_text = 2;
  string new_text = 3;
}

message EditResult {
  oneof result {
    EditSuccess success = 1;
    EditFileNotFound file_not_found = 2;
    EditReadPermissionDenied read_permission_denied = 3;
    EditWritePermissionDenied write_permission_denied = 4;
    EditError error = 5;
    EditRejected rejected = 6;
  }
}
```

---

## Search and Navigation

### GrepArgs (`agent.v1.GrepArgs`)

**Location:** Line ~129678

```protobuf
message GrepArgs {
  string pattern = 1;
  optional string path = 2;
  optional string include_glob = 3;
  optional string exclude_glob = 4;
  optional bool case_insensitive = 5;
  optional bool whole_word = 6;
  optional bool regex = 7;
  optional int32 max_results = 8;
  optional int32 context_lines = 9;
  // ... additional options
}
```

### LsArgs (`agent.v1.LsArgs`)

**Location:** Line ~102883

```protobuf
message LsArgs {
  string path = 1;
  optional int32 max_depth = 2;
  optional int32 max_entries = 3;
  optional string include_glob = 4;
  optional bool include_hidden = 5;
}

message LsResult {
  oneof result {
    LsSuccess success = 1;
    LsError error = 2;
    LsRejected rejected = 3;
    LsTimeout timeout = 4;
  }
}

message LsSuccess {
  LsDirectoryTreeNode root = 1;
}

message LsDirectoryTreeNode {
  string name = 1;
  bool is_directory = 2;
  repeated LsDirectoryTreeNode children = 3;
  optional File file = 4;
}
```

---

## Enumerations

### ShellAbortReason

**Location:** Line ~94273

```protobuf
enum ShellAbortReason {
  SHELL_ABORT_REASON_UNSPECIFIED = 0;
  SHELL_ABORT_REASON_USER_ABORT = 1;
  SHELL_ABORT_REASON_TIMEOUT = 2;
}
```

### MouseButton

**Location:** Line ~103311

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

**Location:** Line ~103331

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

**Location:** Line ~118788

```protobuf
enum PackageType {
  PACKAGE_TYPE_UNSPECIFIED = 0;
  PACKAGE_TYPE_CURSOR_RULE = 1;
  PACKAGE_TYPE_CURSOR_PACKAGE = 2;
}
```

### CursorRuleSource

**Location:** Line ~118913

```protobuf
enum CursorRuleSource {
  CURSOR_RULE_SOURCE_UNSPECIFIED = 0;
  CURSOR_RULE_SOURCE_GLOBAL = 1;
  CURSOR_RULE_SOURCE_WORKSPACE = 2;
}
```

### CustomSubagentPermissionMode

**Location:** Line ~119485

```protobuf
enum CustomSubagentPermissionMode {
  CUSTOM_SUBAGENT_PERMISSION_MODE_UNSPECIFIED = 0;
  CUSTOM_SUBAGENT_PERMISSION_MODE_ALL = 1;
  CUSTOM_SUBAGENT_PERMISSION_MODE_NONE = 2;
}
```

---

## Context Types

### RequestContext (`agent.v1.RequestContext`)

**Location:** Line ~120206

```protobuf
message RequestContext {
  RequestContextEnv env = 1;
  optional DebugModeConfig debug_mode_config = 2;
  repeated GitRepoInfo git_repos = 3;
  repeated ImageProto images = 4;
  repeated RepositoryIndexingInfo repository_indexing_info = 5;
  repeated McpTools mcp_tools = 6;
  repeated McpDescriptor mcp_descriptors = 7;
  repeated CursorRule cursor_rules = 8;
  repeated CustomSubagent custom_subagents = 9;
  repeated SkillDescriptor skill_descriptors = 10;
  // ... additional context fields
}
```

### SelectedContext (`agent.v1.SelectedContext`)

**Location:** Line ~138514

User-selected context for the conversation.

```protobuf
message SelectedContext {
  oneof context {
    SelectedFile file = 1;
    SelectedCodeSelection code_selection = 2;
    SelectedTerminal terminal = 3;
    SelectedTerminalSelection terminal_selection = 4;
    SelectedFolder folder = 5;
    SelectedExternalLink external_link = 6;
    SelectedCursorRule cursor_rule = 7;
    SelectedGitDiff git_diff = 8;
    SelectedGitDiffFromBranchToMain git_diff_from_branch_to_main = 9;
    SelectedGitCommit git_commit = 10;
    SelectedPullRequest pull_request = 11;
    SelectedGitPRDiffSelection git_pr_diff_selection = 12;
    SelectedCursorCommand cursor_command = 13;
    SelectedDocumentation documentation = 14;
    SelectedPastChat past_chat = 15;
    SelectedConsoleLog console_log = 16;
    SelectedUIElement ui_element = 17;
    SelectedImage image = 18;
    ExtraContextEntry extra_context = 19;
  }
}
```

---

## MCP Integration

### McpTools (`agent.v1.McpTools`)

**Location:** Line ~119289

```protobuf
message McpTools {
  repeated McpToolDefinition tools = 1;
}

message McpToolDefinition {
  string name = 1;
  string description = 2;
  string input_schema_json = 3;
}
```

### McpDescriptor (`agent.v1.McpDescriptor`)

**Location:** Line ~119355

```protobuf
message McpDescriptor {
  string name = 1;
  string description = 2;
  repeated McpToolDescriptor tools = 3;
  optional string instructions = 4;
}
```

---

## Complete Type Inventory

Total unique types discovered: **350+**

### Categories

| Category | Count | Examples |
|----------|-------|----------|
| Service Messages | 12 | AgentClientMessage, AgentServerMessage |
| Tool Args/Results | 80+ | ShellArgs, ShellResult, ReadArgs, etc. |
| Streaming Updates | 17 | TextDeltaUpdate, ToolCallStartedUpdate |
| Conversation State | 15 | ConversationStateStructure, ConversationTurn |
| Context Types | 25+ | SelectedFile, SelectedTerminal |
| Computer Use | 15 | ComputerUseAction, ClickAction, etc. |
| MCP | 12 | McpTools, McpDescriptor |
| Subagent | 10 | SubagentType, BackgroundSubagentSpawnArgs |

---

## Key Findings

1. **Bidirectional Streaming Architecture**: The agent uses BiDi streaming for real-time communication between client and server, with SSE and polling fallbacks.

2. **Exec Message Pattern**: Tool execution follows a request/response pattern through `ExecServerMessage` and `ExecClientMessage` with unique IDs for correlation.

3. **Rich Tool System**: 34+ distinct tool types with comprehensive args/result unions and error handling.

4. **Computer Use Integration**: Full support for Anthropic's computer use protocol with mouse, keyboard, and screen actions.

5. **Sandbox Support**: Shell execution includes sandbox policies for security (readonly, readwrite, none).

6. **State Persistence**: ConversationStateStructure enables resumable conversations with file states, todos, and subagent states.

7. **MCP Support**: First-class support for Model Context Protocol tools and resources.

---

## Recommended Follow-up Tasks

1. **TASK-25a**: Document PTY service schemas for terminal management
2. **TASK-25b**: Deep dive into SubagentPersistedState and background subagent patterns
3. **TASK-25c**: Analyze KV storage patterns (KvClientMessage/KvServerMessage)
4. **TASK-25d**: Document artifact upload/download schemas

---

## References

- Previous analysis: `TASK-7-protobuf-schemas.md` (aiserver.v1)
- Source: Line references are from `beautified/workbench.desktop.main.js`
