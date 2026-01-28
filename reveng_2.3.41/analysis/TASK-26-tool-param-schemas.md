# TASK-26: Deep Dive into Tool Parameter and Result Schemas

## Overview

This analysis documents the ClientSideToolV2 parameter and result schemas extracted from
Cursor IDE 2.3.41's beautified workbench.desktop.main.js source. These protobuf message
definitions are found in the `aiserver.v1` package and define the complete tool calling
interface between the Cursor client and AI server.

## Source Location

File: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
Package: `out-build/proto/aiserver/v1/tools_pb.js` (lines ~104362-117525)

---

## ClientSideToolV2 Enum (vt)

The tool enum defines 56 distinct tools (including UNSPECIFIED):

```javascript
// Line 104365
i[i.UNSPECIFIED = 0] = "UNSPECIFIED"
i[i.READ_SEMSEARCH_FILES = 1] = "READ_SEMSEARCH_FILES"
i[i.RIPGREP_SEARCH = 3] = "RIPGREP_SEARCH"
i[i.READ_FILE = 5] = "READ_FILE"
i[i.LIST_DIR = 6] = "LIST_DIR"
i[i.EDIT_FILE = 7] = "EDIT_FILE"
i[i.FILE_SEARCH = 8] = "FILE_SEARCH"
i[i.SEMANTIC_SEARCH_FULL = 9] = "SEMANTIC_SEARCH_FULL"
i[i.DELETE_FILE = 11] = "DELETE_FILE"
i[i.REAPPLY = 12] = "REAPPLY"
i[i.RUN_TERMINAL_COMMAND_V2 = 15] = "RUN_TERMINAL_COMMAND_V2"
i[i.FETCH_RULES = 16] = "FETCH_RULES"
i[i.WEB_SEARCH = 18] = "WEB_SEARCH"
i[i.MCP = 19] = "MCP"
i[i.SEARCH_SYMBOLS = 23] = "SEARCH_SYMBOLS"
i[i.BACKGROUND_COMPOSER_FOLLOWUP = 24] = "BACKGROUND_COMPOSER_FOLLOWUP"
i[i.KNOWLEDGE_BASE = 25] = "KNOWLEDGE_BASE"
i[i.FETCH_PULL_REQUEST = 26] = "FETCH_PULL_REQUEST"
i[i.DEEP_SEARCH = 27] = "DEEP_SEARCH"
i[i.CREATE_DIAGRAM = 28] = "CREATE_DIAGRAM"
i[i.FIX_LINTS = 29] = "FIX_LINTS"
i[i.READ_LINTS = 30] = "READ_LINTS"
i[i.GO_TO_DEFINITION = 31] = "GO_TO_DEFINITION"
i[i.TASK = 32] = "TASK"
i[i.AWAIT_TASK = 33] = "AWAIT_TASK"
i[i.TODO_READ = 34] = "TODO_READ"
i[i.TODO_WRITE = 35] = "TODO_WRITE"
i[i.EDIT_FILE_V2 = 38] = "EDIT_FILE_V2"
i[i.LIST_DIR_V2 = 39] = "LIST_DIR_V2"
i[i.READ_FILE_V2 = 40] = "READ_FILE_V2"
i[i.RIPGREP_RAW_SEARCH = 41] = "RIPGREP_RAW_SEARCH"
i[i.GLOB_FILE_SEARCH = 42] = "GLOB_FILE_SEARCH"
i[i.CREATE_PLAN = 43] = "CREATE_PLAN"
i[i.LIST_MCP_RESOURCES = 44] = "LIST_MCP_RESOURCES"
i[i.READ_MCP_RESOURCE = 45] = "READ_MCP_RESOURCE"
i[i.READ_PROJECT = 46] = "READ_PROJECT"
i[i.UPDATE_PROJECT = 47] = "UPDATE_PROJECT"
i[i.TASK_V2 = 48] = "TASK_V2"
i[i.CALL_MCP_TOOL = 49] = "CALL_MCP_TOOL"
i[i.APPLY_AGENT_DIFF = 50] = "APPLY_AGENT_DIFF"
i[i.ASK_QUESTION = 51] = "ASK_QUESTION"
i[i.SWITCH_MODE = 52] = "SWITCH_MODE"
i[i.GENERATE_IMAGE = 53] = "GENERATE_IMAGE"
i[i.COMPUTER_USE = 54] = "COMPUTER_USE"
i[i.WRITE_SHELL_STDIN = 55] = "WRITE_SHELL_STDIN"
```

**Note**: Numbers 2, 4, 10, 13, 14, 17, 20-22, 36-37 are not assigned (likely deprecated or reserved).

---

## ClientSideToolV2Call Message

**TypeName**: `aiserver.v1.ClientSideToolV2Call` (line 104959)

### Base Fields
| Field No | Name | Type | Required |
|----------|------|------|----------|
| 1 | tool | enum ClientSideToolV2 | Yes |
| 3 | tool_call_id | string | Yes |
| 6 | timeout_ms | double | No |
| 9 | name | string | Yes |
| 10 | raw_args | string | Yes |
| 14 | is_streaming | bool | Yes |
| 15 | is_last_message | bool | Yes |
| 48 | tool_index | uint32 | No |
| 49 | model_call_id | string | No |
| 51 | internal | bool | Yes |

### Params Oneof (Field Numbers 2, 5, 8, 12-13, 16-17, 19-20, 23-27, 31-38, 41-45, 50-67)
Each tool has a corresponding `*_params` field in the oneof. Example mappings:
- `read_file_params` (no: 8) -> ReadFileParams
- `edit_file_params` (no: 13) -> EditFileParams
- `run_terminal_command_v2_params` (no: 23) -> RunTerminalCommandV2Params
- `glob_file_search_params` (no: 55) -> GlobFileSearchParams

---

## ClientSideToolV2Result Message

**TypeName**: `aiserver.v1.ClientSideToolV2Result` (line 105297)

### Base Fields
| Field No | Name | Type | Required |
|----------|------|------|----------|
| 1 | tool | enum ClientSideToolV2 | Yes |
| 35 | tool_call_id | string | Yes |
| 8 | error | ToolResultError | No |
| 48 | model_call_id | string | No |
| 49 | tool_index | uint32 | No |
| 50 | attachments | ToolResultAttachments | No |

### Result Oneof (Field Numbers 2, 4, 6, 9-11, 18, 20-21, 24-25, 27-28, 32-45, 51-68)
Each tool has a corresponding `*_result` field in the oneof.

---

## Key Tool Parameter Schemas

### ReadFileParams (aiserver.v1.ReadFileParams)
**Line**: 107575

```protobuf
message ReadFileParams {
  string relative_workspace_path = 1;
  bool read_entire_file = 2;
  optional int32 start_line_one_indexed = 3;
  optional int32 end_line_one_indexed_inclusive = 4;
  bool file_is_allowed_to_be_read_entirely = 5;
  optional int32 max_lines = 6;
  optional int32 max_chars = 7;
  optional int32 min_lines = 8;
}
```

### ReadFileResult (aiserver.v1.ReadFileResult)
**Line**: 107645

```protobuf
message ReadFileResult {
  string contents = 1;
  bool did_downgrade_to_line_range = 2;
  bool did_shorten_line_range = 3;
  bool did_set_default_line_range = 4;
  optional string full_file_contents = 5;
  optional string outline = 6;
  optional int32 start_line_one_indexed = 7;
  optional int32 end_line_one_indexed_inclusive = 8;
  string relative_workspace_path = 9;
  bool did_shorten_char_range = 10;
  optional bool read_full_file = 11;
  optional int32 total_lines = 12;
  repeated CursorRule matching_cursor_rules = 13;
  FileGitContext file_git_context = 14;
}
```

### EditFileParams (aiserver.v1.EditFileParams)
**Line**: 106727

```protobuf
message EditFileParams {
  string relative_workspace_path = 1;
  string language = 2;
  string contents = 3;
  bool blocking = 4;
  optional string instructions = 5;
  optional string old_string = 6;
  optional string new_string = 7;
  optional bool allow_multiple_matches = 8;
  repeated LineRange line_ranges = 9;
  optional bool use_whitespace_insensitive_fallback = 10;
  optional bool use_did_you_mean_fuzzy_match = 11;
  optional bool should_edit_file_fail_for_large_files = 12;
  optional int32 notebook_cell_idx = 13;
  optional bool is_new_cell = 14;
  optional string cell_language = 15;
  optional bool gracefully_handle_recoverable_errors = 16;
  optional string edit_category = 17;
  optional bool should_eagerly_process_lints = 18;
}
```

### EditFileResult (aiserver.v1.EditFileResult)
**Line**: 106856

```protobuf
message EditFileResult {
  Diff diff = 1;
  bool is_applied = 2;
  bool apply_failed = 3;
  repeated LinterError linter_errors = 4;
  optional bool rejected = 5;
  optional int32 num_matches = 6;
  optional bool whitespace_insensitive_fallback_found_match = 7;
  // Additional fields for human review...
}
```

### EditFileV2Params (aiserver.v1.EditFileV2Params)
**Line**: 106450

```protobuf
message EditFileV2Params {
  string relative_workspace_path = 1;
  optional string contents_after_edit = 2;
  optional bool waiting_for_file_contents = 3;
  oneof streaming_edit {
    StreamingEditText text = 4;
    StreamingEditCode code = 5;
  }
  bool should_send_back_linter_errors = 6;
  optional Diff diff = 7;
  string result_for_model = 8;
  optional string streaming_content = 9;
  optional bool no_codeblock = 10;
  optional bool cloud_agent_edit = 11;
}
```

### RunTerminalCommandV2Params (aiserver.v1.RunTerminalCommandV2Params)
**Line**: 112394

```protobuf
message RunTerminalCommandV2Params {
  string command = 1;
  optional string cwd = 2;
  optional bool new_session = 3;
  optional ExecutionOptions options = 4;
  bool is_background = 5;
  bool require_user_approval = 6;
  optional ParsingResult parsing_result = 7;
  optional int32 idle_timeout_seconds = 8;
  optional SandboxPolicy requested_sandbox_policy = 9;
  optional int64 file_output_threshold_bytes = 10;
}

message ExecutionOptions {
  optional int32 timeout = 1;
  optional bool skip_ai_check = 2;
  optional int32 command_run_timeout_ms = 3;
  optional int32 command_change_check_interval_ms = 4;
  optional int32 ai_finish_check_max_attempts = 5;
  optional int32 ai_finish_check_interval_ms = 6;
  optional int32 delayer_interval_ms = 7;
  optional bool ai_check_for_hangs = 8;
}
```

### RunTerminalCommandV2Result (aiserver.v1.RunTerminalCommandV2Result)
**Line**: 112589

```protobuf
message RunTerminalCommandV2Result {
  string output = 1;
  int32 exit_code = 2;
  optional bool rejected = 3;
  bool popped_out_into_background = 4;
  bool is_running_in_background = 5;
  bool not_interrupted = 6;
  string resulting_working_directory = 7;
  bool did_user_change = 8;
  enum EndedReason ended_reason = 9;
  optional int32 exit_code_v2 = 10;
  optional string updated_command = 11;
  string output_raw = 12;
  optional HumanReviewV2 human_review_v2 = 13;
  optional SandboxPolicy effective_sandbox_policy = 14;
  optional int32 terminal_instance_id = 15;
  optional OutputLocation output_location = 16;
  optional string terminal_instance_path = 17;
  optional uint32 background_shell_id = 18;
}
```

### ListDirParams (aiserver.v1.ListDirParams)
**Line**: 107425

```protobuf
message ListDirParams {
  string directory_path = 1;
}
```

### ListDirResult (aiserver.v1.ListDirResult)
**Line**: 107455

```protobuf
message ListDirResult {
  repeated File files = 1;
  string directory_relative_workspace_path = 2;
}

message File {
  string name = 1;
  bool is_directory = 2;
  optional int64 size = 3;
  optional Timestamp last_modified = 4;
  optional int32 num_children = 5;
  optional int32 num_lines = 6;
}
```

### RipgrepSearchParams (aiserver.v1.RipgrepSearchParams)
**Line**: 107772

```protobuf
message RipgrepSearchParams {
  ITextQueryBuilderOptionsProto options = 1;
  IPatternInfoProto pattern_info = 2;
}

message IPatternInfoProto {
  string pattern = 1;
  optional bool is_reg_exp = 2;
  optional bool is_word_match = 3;
  optional string word_separators = 4;
  optional bool is_multiline = 5;
  optional bool is_unicode = 6;
  optional bool is_case_sensitive = 7;
  INotebookPatternInfoProto notebook_info = 8;
  optional bool pattern_was_escaped = 9;
}
```

### GlobFileSearchParams (aiserver.v1.GlobFileSearchParams)
**Line**: 116309

```protobuf
message GlobFileSearchParams {
  string target_directory = 1;
  string glob_pattern = 2;
}
```

### GlobFileSearchResult (aiserver.v1.GlobFileSearchResult)
**Line**: 116344

```protobuf
message GlobFileSearchResult {
  repeated Directory directories = 1;
}

message Directory {
  string abs_path = 1;
  repeated File files = 2;
  int32 total_files = 3;
  bool ripgrep_truncated = 4;
}

message File {
  string rel_path = 1;
}
```

### TaskParams (aiserver.v1.TaskParams)
**Line**: 114612

```protobuf
message TaskParams {
  string task_description = 1;
  optional bool async = 2;
  repeated string allowed_write_directories = 3;
  string task_title = 4;
  optional string model_override = 5;
  optional bool max_mode_override = 6;
  optional bool default_expanded_while_running = 7;
}
```

### TaskV2Params (aiserver.v1.TaskV2Params)
**Line**: 114827

```protobuf
message TaskV2Params {
  string description = ?;
  string prompt = ?;
  string subagent_type = ?;
}
```

### TodoWriteParams (aiserver.v1.TodoWriteParams)
**Line**: 115853

```protobuf
message TodoWriteParams {
  repeated TodoItem todos = 1;
  bool merge = 2;
}

message TodoItem {
  string content = 1;
  string status = 2;
  string id = 3;
  repeated string dependencies = 4;
}
```

### CallMcpToolParams (aiserver.v1.CallMcpToolParams)
**Line**: 113324

```protobuf
message CallMcpToolParams {
  string server = 1;
  string tool_name = 2;
  Struct tool_args = 3;  // google.protobuf.Struct
}
```

### AskQuestionParams (aiserver.v1.AskQuestionParams)
**Line**: 117062

```protobuf
message AskQuestionParams {
  string title = 1;
  repeated Question questions = 2;
  bool run_async = 3;
}

message Question {
  string id = 1;
  string prompt = 2;
  repeated Option options = 3;
  bool allow_multiple = 4;
}

message Option {
  string id = 1;
  string label = 2;
}
```

### SwitchModeParams (aiserver.v1.SwitchModeParams)
**Line**: 117286

```protobuf
message SwitchModeParams {
  string from_mode_id = 1;
  string to_mode_id = 2;
  optional string explanation = 3;
}
```

### ComputerUseParams (aiserver.v1.ComputerUseParams)
**Line**: 117402

```protobuf
message ComputerUseParams {
  repeated Action actions = 1;
}
```

---

## Error Handling Schema

### ToolResultError (aiserver.v1.ToolResultError)
**Line**: 104844

```protobuf
message ToolResultError {
  string client_visible_error_message = 1;
  string model_visible_error_message = 2;
  optional string actual_error_message_only_send_from_client_to_server_never_the_other_way_around_because_that_may_be_a_security_risk = 3;
  oneof error_details {
    EditFileError edit_file_error_details = 5;
    SearchReplaceError search_replace_error_details = 6;
  }
}

message EditFileError {
  int32 num_lines_in_file_before_edit = 1;
}

message SearchReplaceError {
  int32 num_lines_in_file_before_edit = 1;
}
```

---

## ToolResultAttachments (aiserver.v1.ToolResultAttachments)
**Line**: 105650

```protobuf
message ToolResultAttachments {
  repeated TodoItem original_todos = 1;
  repeated TodoItem updated_todos = 2;
  repeated NudgeMessage nudge_messages = 3;
  bool should_show_todo_write_reminder = 4;
  TodoReminderType todo_reminder_type = 5;
  optional DiscoveryBudgetReminder discovery_budget_reminder = 6;
}

enum TodoReminderType {
  TODO_REMINDER_TYPE_UNSPECIFIED = 0;
  TODO_REMINDER_TYPE_EVERY_10_TURNS = 1;
  TODO_REMINDER_TYPE_AFTER_EDIT = 2;
}

message DiscoveryBudgetReminder {
  int32 discovery_rounds_remaining = 1;
  optional string discovery_effort = 2;
}
```

---

## Tool Execution Flow

The tool execution flow is handled in a large switch statement (lines ~264991-265174):

```javascript
function N7l(i) {
    const e = i.tool,
        { params: t, result: n } = (() => {
            switch (e) {
                case vt.RUN_TERMINAL_COMMAND_V2:
                    return {
                        params: i.params ? jMe.fromJsonString(i.params) : void 0,
                        result: i.result ? f7.fromJsonString(i.result) : void 0
                    };
                case vt.READ_FILE:
                    return {
                        params: i.params ? $Bt.fromJsonString(i.params) : void 0,
                        result: i.result ? qBt.fromJsonString(i.result) : void 0
                    };
                // ... more cases
            }
        })()
}
```

Each tool maps to specific Params and Result class constructors for deserialization.

---

## Streaming Support

Many tools have corresponding `*Stream` message types for streaming partial results:
- `ReadFileStream` (line 107747)
- `EditFileStream` (line 107268)
- `EditFileV2Stream` (line 106702)
- `ListDirStream` (line 107550)
- `RunTerminalCommandV2Stream` (line 112713)
- `GlobFileSearchStream` (line 116451)
- `CallMcpToolStream` (line 116501)
- `ComputerUseStream` (line 117472)

The streaming messages typically contain the same params but are used for progressive updates.

---

## StreamedBackToolCall (aiserver.v1.StreamedBackToolCall)
**Line**: 105810

Used for streaming tool calls back from server to client with partial params:

```protobuf
message StreamedBackToolCall {
  ClientSideToolV2 tool = 1;
  string tool_call_id = 2;
  oneof params {
    // Stream versions of each tool's params
    ReadSemsearchFilesStream read_semsearch_files_stream = 3;
    RipgrepSearchStream ripgrep_search_stream = 5;
    ReadFileStream read_file_stream = 7;
    // ... etc
  }
  string name = ?;
  string raw_args = ?;
}
```

---

## Validation Logic

Tool validation occurs at multiple points:

1. **Service-level validation** (line 1129091):
```javascript
if (e.tool !== vt.RUN_TERMINAL_COMMAND_V2 || !e.params?.value)
    throw this.logService.error(`${s} Invalid tool call - tool=${e.tool}, hasParams=${!!e.params?.value}`),
          new Error("Invalid tool call for swRunTerminalCommand");
```

2. **Switch case handling** ensures only valid tool enum values are processed

3. **Protobuf deserialization** will fail for malformed params/results

---

## Key Observations

1. **Version Evolution**: Both v1 and v2 versions exist for several tools (READ_FILE/READ_FILE_V2, EDIT_FILE/EDIT_FILE_V2, LIST_DIR/LIST_DIR_V2), suggesting API evolution

2. **Streaming Architecture**: Each tool has three message types - Params, Result, and Stream - enabling progressive updates

3. **Security Awareness**: The error message field naming (`actual_error_message_only_send_from_client_to_server_never_the_other_way_around_because_that_may_be_a_security_risk`) shows security considerations

4. **Todo Integration**: The ToolResultAttachments includes todo-related fields, suggesting integrated task tracking

5. **Human Review**: Several result types include `HumanReviewV2` fields for approval workflows

6. **Sandbox Policies**: Terminal commands include sandbox policy fields for security enforcement

7. **MCP Integration**: First-class support for MCP tools with dedicated CALL_MCP_TOOL, LIST_MCP_RESOURCES, READ_MCP_RESOURCE tools

8. **Computer Use**: Tool 54 (COMPUTER_USE) indicates support for automated UI interactions

9. **Mode Switching**: SWITCH_MODE tool allows dynamic switching between agent modes

---

## Investigation Avenues for Follow-up

1. **Streaming Protocol Details**: How are stream messages framed and multiplexed?
2. **Human Review Flow**: Complete workflow for edit approval
3. **Sandbox Policy Enforcement**: How are requested vs effective policies computed?
4. **MCP Tool Execution**: How does CALL_MCP_TOOL differ from the older MCP tool?
5. **Computer Use Actions**: What action types are supported?
6. **Mode Definitions**: What modes exist and how are they defined?
7. **Todo Dependencies**: How are todo item dependencies resolved?

---

## Files Referenced

- Main source: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
- Proto package: `out-build/proto/aiserver/v1/tools_pb.js`
- Related: `out-build/proto/agent/v1/*_pb.js` for agent-specific schemas
