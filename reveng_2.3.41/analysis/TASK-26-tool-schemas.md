# TASK-26: Deep Dive into Tool Parameter and Result Schemas

**Source:** `reveng_2.3.41/beautified/workbench.desktop.main.js`
**Analysis Date:** 2026-01-27
**Related:** TASK-7-protobuf-schemas.md

## Overview

This document provides detailed schemas for the ClientSideToolV2 tool system used in Cursor's agentic operations. Each tool has three message types:
- **Params**: Input parameters sent to the tool
- **Result**: Output returned when the tool completes
- **Stream**: Data streamed during execution (for progressive UI updates)

### Scalar Type Reference

The `T` field in scalar types corresponds to protobuf scalar type numbers:
- `T: 1` = double
- `T: 3` = int64
- `T: 5` = int32
- `T: 8` = bool
- `T: 9` = string
- `T: 12` = bytes
- `T: 13` = uint32

---

## Core Tool Call and Result Structures

### ClientSideToolV2Call (aiserver.v1.ClientSideToolV2Call)
**Location:** Line ~104959

The wrapper message for all tool invocations:

```protobuf
message ClientSideToolV2Call {
  ClientSideToolV2 tool = 1;                    // enum: which tool
  string tool_call_id = 3;                      // unique call identifier
  optional double timeout_ms = 6;               // tool timeout
  string name = 9;                              // tool name string
  bool is_streaming = 14;                       // streaming in progress
  bool is_last_message = 15;                    // final streaming chunk
  bool internal = 51;                           // internal/system tool call
  string raw_args = 10;                         // raw JSON arguments
  optional uint32 tool_index = 48;              // index in parallel calls
  optional string model_call_id = 49;           // associated model call

  // Params oneof - exactly one will be set based on tool enum
  oneof params {
    ReadSemsearchFilesParams read_semsearch_files_params = 2;
    RipgrepSearchParams ripgrep_search_params = 5;
    ReadFileParams read_file_params = 8;
    ListDirParams list_dir_params = 12;
    EditFileParams edit_file_params = 13;
    ToolCallFileSearchParams file_search_params = 16;
    SemanticSearchFullParams semantic_search_full_params = 17;
    DeleteFileParams delete_file_params = 19;
    ReapplyParams reapply_params = 20;
    RunTerminalCommandV2Params run_terminal_command_v2_params = 23;
    FetchRulesParams fetch_rules_params = 24;
    WebSearchParams web_search_params = 26;
    MCPParams mcp_params = 27;
    SearchSymbolsParams search_symbols_params = 31;
    GotodefParams gotodef_params = 41;
    BackgroundComposerFollowupParams background_composer_followup_params = 32;
    KnowledgeBaseParams knowledge_base_params = 33;
    FetchPullRequestParams fetch_pull_request_params = 34;
    DeepSearchParams deep_search_params = 35;
    CreateDiagramParams create_diagram_params = 36;
    FixLintsParams fix_lints_params = 37;
    ReadLintsParams read_lints_params = 38;
    TaskParams task_params = 42;
    AwaitTaskParams await_task_params = 43;
    TodoReadParams todo_read_params = 44;
    TodoWriteParams todo_write_params = 45;
    EditFileV2Params edit_file_v2_params = 50;
    ListDirV2Params list_dir_v2_params = 52;
    ReadFileV2Params read_file_v2_params = 53;
    RipgrepRawSearchParams ripgrep_raw_search_params = 54;
    GlobFileSearchParams glob_file_search_params = 55;
    CreatePlanParams create_plan_params = 56;
    ListMcpResourcesParams list_mcp_resources_params = 57;
    ReadMcpResourceParams read_mcp_resource_params = 58;
    ReadProjectParams read_project_params = 59;
    UpdateProjectParams update_project_params = 60;
    TaskV2Params task_v2_params = 61;
    CallMcpToolParams call_mcp_tool_params = 62;
    ApplyAgentDiffParams apply_agent_diff_params = 63;
    AskQuestionParams ask_question_params = 64;
    SwitchModeParams switch_mode_params = 65;
    ComputerUseParams computer_use_params = 66;
    WriteShellStdinParams write_shell_stdin_params = 67;
  }
}
```

### ClientSideToolV2Result (aiserver.v1.ClientSideToolV2Result)
**Location:** Line ~105297

The wrapper message for all tool results:

```protobuf
message ClientSideToolV2Result {
  ClientSideToolV2 tool = 1;                    // enum: which tool
  string tool_call_id = 35;                     // matches the call
  optional ToolResultError error = 8;           // error if failed
  optional string model_call_id = 48;           // associated model call
  optional uint32 tool_index = 49;              // index in parallel calls
  optional ToolResultAttachments attachments = 50;  // additional data

  // Result oneof - exactly one will be set
  oneof result {
    ReadSemsearchFilesResult read_semsearch_files_result = 2;
    RipgrepSearchResult ripgrep_search_result = 4;
    ReadFileResult read_file_result = 6;
    ListDirResult list_dir_result = 9;
    EditFileResult edit_file_result = 10;
    ToolCallFileSearchResult file_search_result = 11;
    SemanticSearchFullResult semantic_search_full_result = 18;
    DeleteFileResult delete_file_result = 20;
    ReapplyResult reapply_result = 21;
    RunTerminalCommandV2Result run_terminal_command_v2_result = 24;
    FetchRulesResult fetch_rules_result = 25;
    WebSearchResult web_search_result = 27;
    MCPResult mcp_result = 28;
    SearchSymbolsResult search_symbols_result = 32;
    BackgroundComposerFollowupResult background_composer_followup_result = 33;
    KnowledgeBaseResult knowledge_base_result = 34;
    FetchPullRequestResult fetch_pull_request_result = 36;
    DeepSearchResult deep_search_result = 37;
    CreateDiagramResult create_diagram_result = 38;
    FixLintsResult fix_lints_result = 39;
    ReadLintsResult read_lints_result = 40;
    GotodefResult gotodef_result = 41;
    TaskResult task_result = 42;
    AwaitTaskResult await_task_result = 43;
    TodoReadResult todo_read_result = 44;
    TodoWriteResult todo_write_result = 45;
    EditFileV2Result edit_file_v2_result = 51;
    ListDirV2Result list_dir_v2_result = 52;
    ReadFileV2Result read_file_v2_result = 53;
    RipgrepRawSearchResult ripgrep_raw_search_result = 54;
    GlobFileSearchResult glob_file_search_result = 55;
    CreatePlanResult create_plan_result = 56;
    ListMcpResourcesResult list_mcp_resources_result = 57;
    ReadMcpResourceResult read_mcp_resource_result = 58;
    ReadProjectResult read_project_result = 59;
    UpdateProjectResult update_project_result = 60;
    TaskV2Result task_v2_result = 61;
    CallMcpToolResult call_mcp_tool_result = 62;
    ApplyAgentDiffResult apply_agent_diff_result = 63;
    AskQuestionResult ask_question_result = 64;
    SwitchModeResult switch_mode_result = 65;
    ComputerUseResult computer_use_result = 66;
    GenerateImageResult generate_image_result = 67;
    WriteShellStdinResult write_shell_stdin_result = 68;
  }
}
```

---

## Error Handling Schema

### ToolResultError (aiserver.v1.ToolResultError)
**Location:** Line ~104834

```protobuf
message ToolResultError {
  string client_visible_error_message = 1;       // Shown to user
  string model_visible_error_message = 2;        // Sent to LLM for context
  optional string actual_error_message_only_send_from_client_to_server_never_the_other_way_around_because_that_may_be_a_security_risk = 3;

  oneof error_details {
    EditFileError edit_file_error_details = 5;
    SearchReplaceError search_replace_error_details = 6;
  }

  message EditFileError {
    int32 num_lines_in_file_before_edit = 1;     // Context for retry
  }

  message SearchReplaceError {
    int32 num_lines_in_file_before_edit = 1;     // Context for retry
  }
}
```

### ToolResultAttachments (aiserver.v1.ToolResultAttachments)
**Location:** Line ~105642

```protobuf
message ToolResultAttachments {
  repeated TodoItem original_todos = 1;
  repeated TodoItem updated_todos = 2;
  repeated NudgeMessage nudge_messages = 3;
  bool should_show_todo_write_reminder = 4;
  TodoReminderType todo_reminder_type = 5;
  optional DiscoveryBudgetReminder discovery_budget_reminder = 6;
}
```

---

## File Operations

### ReadFileParams (aiserver.v1.ReadFileParams)
**Location:** Line ~107575

```protobuf
message ReadFileParams {
  string relative_workspace_path = 1;           // File path relative to workspace
  bool read_entire_file = 2;                    // Read all content
  optional int32 start_line_one_indexed = 3;    // Start line (1-indexed)
  optional int32 end_line_one_indexed_inclusive = 4;  // End line (inclusive)
  bool file_is_allowed_to_be_read_entirely = 5; // Permission flag
  optional int32 max_lines = 6;                 // Limit lines returned
  optional int32 max_chars = 7;                 // Limit characters
  optional int32 min_lines = 8;                 // Minimum lines to return
}
```

### ReadFileResult (aiserver.v1.ReadFileResult)
**Location:** Line ~107645

```protobuf
message ReadFileResult {
  string contents = 1;                          // File content
  bool did_downgrade_to_line_range = 2;         // Fell back to range
  bool did_shorten_line_range = 3;              // Range was truncated
  bool did_set_default_line_range = 4;          // Used default range
  optional string full_file_contents = 5;       // Complete file (if requested)
  optional string outline = 6;                  // Symbol outline
  optional int32 start_line_one_indexed = 7;    // Actual start line
  optional int32 end_line_one_indexed_inclusive = 8;  // Actual end line
  string relative_workspace_path = 9;           // Confirmed path
  bool did_shorten_char_range = 10;             // Chars were truncated
  optional bool read_full_file = 11;            // Entire file was read
  optional int32 total_lines = 12;              // Total lines in file
  repeated CursorRule matching_cursor_rules = 13;  // Applicable rules
  optional FileGitContext file_git_context = 14;   // Git info
}
```

### ReadFileV2Params (aiserver.v1.ReadFileV2Params)
**Location:** Line ~116166

The V2 API uses character-based offsets rather than line-based:

```protobuf
message ReadFileV2Params {
  string target_file = 1;                       // File path
  optional int32 offset = 2;                    // Line offset (0-indexed)
  optional int32 limit = 3;                     // Number of lines
  int32 chars_limit = 4;                        // Character limit
  string effective_uri = 5;                     // Resolved URI
}
```

### ReadFileV2Result (aiserver.v1.ReadFileV2Result)
**Location:** Line ~116218

```protobuf
message ReadFileV2Result {
  optional string contents = 1;                 // File content
  int32 num_characters_in_requested_range = 2;  // Chars in range
  optional bool offset_is_bigger_than_number_of_lines_in_file = 3;
  optional int32 total_lines_in_file = 4;       // Total file lines
  repeated CursorRule matching_cursor_rules = 5;
  repeated Image images = 6;                    // Images (for PDFs, etc.)
}
```

### EditFileParams (aiserver.v1.EditFileParams)
**Location:** Line ~106727

Legacy edit API using full file content or search/replace:

```protobuf
message EditFileParams {
  string relative_workspace_path = 1;           // Target file
  string language = 2;                          // File language ID
  bool blocking = 4;                            // Wait for completion
  string contents = 3;                          // New file content
  optional string instructions = 5;             // Edit instructions
  optional bool should_edit_file_fail_for_large_files = 12;
  optional string old_string = 6;               // Search string
  optional string new_string = 7;               // Replace string
  optional bool allow_multiple_matches = 8;     // Replace all occurrences
  optional bool use_whitespace_insensitive_fallback = 10;
  optional bool use_did_you_mean_fuzzy_match = 11;
  optional bool gracefully_handle_recoverable_errors = 16;
  repeated LineRange line_ranges = 9;           // Restrict to ranges
  optional int32 notebook_cell_idx = 13;        // Jupyter cell index
  optional bool is_new_cell = 14;               // Creating new cell
  optional string cell_language = 15;           // Cell language
  optional string edit_category = 17;           // Edit category
  optional bool should_eagerly_process_lints = 18;
}
```

### EditFileResult (aiserver.v1.EditFileResult)
**Location:** Line ~106856

```protobuf
message EditFileResult {
  optional FileDiff diff = 1;                   // Generated diff
  bool is_applied = 2;                          // Edit was applied
  bool apply_failed = 3;                        // Application failed
  repeated LinterError linter_errors = 4;       // New lint errors
  optional bool rejected = 5;                   // User rejected
  optional int32 num_matches = 6;               // Search matches found
  optional bool whitespace_insensitive_fallback_found_match = 7;
  optional bool no_match_found_in_line_ranges = 8;
  optional RecoverableError recoverable_error = 11;
  optional int32 num_lines_in_file = 9;         // File size
  optional bool is_subagent_edit = 10;          // From subagent
  optional bool diff_became_no_op_due_to_on_save_fixes = 12;
  optional EditFileHumanReview human_review = 13;
  optional HumanFeedback human_feedback = 14;
  optional bool should_eagerly_process_lints = 15;
  optional HumanReview human_review_v2 = 16;    // Review result
  optional bool were_all_new_linter_errors_resolved_by_this_edit = 17;
}
```

### EditFileV2Params (aiserver.v1.EditFileV2Params)
**Location:** Line ~106450

V2 edit API with streaming support:

```protobuf
message EditFileV2Params {
  string relative_workspace_path = 1;           // Target file
  optional string contents_after_edit = 2;      // Final content
  optional bool waiting_for_file_contents = 3;  // Still streaming
  bool should_send_back_linter_errors = 6;      // Return lint errors
  optional FileDiff diff = 7;                   // Precomputed diff
  string result_for_model = 8;                  // Result for LLM context
  optional string streaming_content = 9;        // Partial content
  optional bool no_codeblock = 10;              // Plain text edit
  optional bool cloud_agent_edit = 11;          // From cloud agent

  oneof streaming_edit {
    StreamingEditText text = 4;
    StreamingEditCode code = 5;
  }

  message StreamingEditText {
    string text = 1;
  }

  message StreamingEditCode {
    string code = 1;
  }
}
```

### EditFileV2Result (aiserver.v1.EditFileV2Result)
**Location:** Line ~106598

```protobuf
message EditFileV2Result {
  optional string contents_before_edit = 1;     // Original content
  optional string eol_sequence = 9;             // Line ending style
  optional string detected_language = 11;       // File language
  bool file_was_created = 2;                    // New file created
  optional FileDiff diff = 3;                   // Applied diff
  optional bool rejected = 4;                   // User rejected
  repeated LinterError linter_errors = 5;       // New lint errors
  bool sent_back_linter_errors = 6;             // Lints returned
  bool should_auto_fix_lints = 8;               // Auto-fix available
  optional HumanReview human_review_v2 = 7;     // Review result
  string result_for_model = 10;                 // Result for LLM
  optional string contents_after_edit = 12;     // Final content
  optional string before_content_id = 13;       // Content versioning
  string after_content_id = 14;                 // Content versioning
}
```

### DeleteFileParams (aiserver.v1.DeleteFileParams)
**Location:** Line ~109462

```protobuf
message DeleteFileParams {
  string relative_workspace_path = 1;           // File to delete
}
```

### DeleteFileResult (aiserver.v1.DeleteFileResult)
**Location:** Line ~109492

```protobuf
message DeleteFileResult {
  bool rejected = 1;                            // User rejected
  bool file_non_existent = 2;                   // File not found
  bool file_deleted_successfully = 3;           // Success
}
```

---

## Directory Operations

### ListDirParams (aiserver.v1.ListDirParams)
**Location:** Line ~107425

```protobuf
message ListDirParams {
  string directory_path = 1;                    // Directory to list
}
```

### ListDirResult (aiserver.v1.ListDirResult)
**Location:** Line ~107455

```protobuf
message ListDirResult {
  repeated File files = 1;                      // Directory contents
  string directory_relative_workspace_path = 2; // Confirmed path

  message File {
    string name = 1;                            // Filename
    bool is_directory = 2;                      // Is subdirectory
    optional int64 size = 3;                    // File size bytes
    optional Timestamp last_modified = 4;       // Modification time
    optional int32 num_children = 5;            // Child count (dirs)
    optional int32 num_lines = 6;               // Line count (files)
  }
}
```

### ListDirV2Params (aiserver.v1.ListDirV2Params)
**Location:** Line ~115972

V2 API with tree structure support:

```protobuf
message ListDirV2Params {
  string target_directory = 1;                  // Directory to list
  optional int32 depth = 2;                     // Max recursion depth
}
```

### ListDirV2Result (aiserver.v1.ListDirV2Result)
**Location:** Line ~116014

```protobuf
message ListDirV2Result {
  repeated DirectoryTreeNode children = 1;      // Tree structure

  message DirectoryTreeNode {
    string name = 1;                            // Entry name
    repeated DirectoryTreeNode children = 2;    // Subdirectories
    optional File file_info = 3;                // File details

    message File {
      int64 size = 1;                           // File size bytes
    }
  }
}
```

### GlobFileSearchParams (aiserver.v1.GlobFileSearchParams)
**Location:** Line ~116309

```protobuf
message GlobFileSearchParams {
  string target_directory = 1;                  // Base directory
  string glob_pattern = 2;                      // Glob pattern (e.g., "**/*.ts")
}
```

### GlobFileSearchResult (aiserver.v1.GlobFileSearchResult)
**Location:** Line ~116344

```protobuf
message GlobFileSearchResult {
  repeated Directory directories = 1;           // Matching results

  message File {
    string rel_path = 1;                        // Relative path
  }

  message Directory {
    string abs_path = 1;                        // Absolute directory path
    repeated File files = 2;                    // Matching files
    int32 total_files = 3;                      // Total matches
    bool ripgrep_truncated = 4;                 // Results truncated
  }
}
```

---

## Terminal Command Execution

### RunTerminalCommandV2Params (aiserver.v1.RunTerminalCommandV2Params)
**Location:** Line ~112394

```protobuf
message RunTerminalCommandV2Params {
  string command = 1;                           // Command to run
  optional string cwd = 2;                      // Working directory
  optional bool new_session = 3;                // Create new terminal
  optional ExecutionOptions options = 4;        // Execution settings
  bool is_background = 5;                       // Run in background
  bool require_user_approval = 6;               // Need confirmation
  optional ShellCommandParsingResult parsing_result = 7;  // Pre-parsed
  optional int32 idle_timeout_seconds = 8;      // Idle timeout
  optional SandboxPolicy requested_sandbox_policy = 9;    // Sandbox settings
  optional int64 file_output_threshold_bytes = 10;        // Output limit

  message ExecutionOptions {
    optional int32 timeout = 1;                 // Overall timeout
    optional bool skip_ai_check = 2;            // Skip AI completion check
    optional int32 command_run_timeout_ms = 3;  // Command timeout
    optional int32 command_change_check_interval_ms = 4;
    optional int32 ai_finish_check_max_attempts = 5;
    optional int32 ai_finish_check_interval_ms = 6;
    optional int32 delayer_interval_ms = 7;
    optional bool ai_check_for_hangs = 8;       // Detect hung processes
  }
}
```

### RunTerminalCommandV2Result (aiserver.v1.RunTerminalCommandV2Result)
**Location:** Line ~112589

```protobuf
message RunTerminalCommandV2Result {
  string output = 1;                            // Command output
  int32 exit_code = 2;                          // Exit code
  optional bool rejected = 3;                   // User rejected
  bool popped_out_into_background = 4;          // Moved to background
  bool is_running_in_background = 5;            // Still running
  bool not_interrupted = 6;                     // Completed normally
  string resulting_working_directory = 7;       // Final cwd
  bool did_user_change = 8;                     // User modified
  RunTerminalCommandEndedReason ended_reason = 9;  // How it ended
  optional int32 exit_code_v2 = 10;             // Detailed exit code
  optional string updated_command = 11;         // Modified command
  string output_raw = 12;                       // Raw output
  optional HumanReview human_review_v2 = 13;    // Review result
  optional SandboxPolicy effective_sandbox_policy = 14;  // Applied policy
  optional int32 terminal_instance_id = 15;     // Terminal ID
  optional OutputLocation output_location = 16; // Large output file
  optional string terminal_instance_path = 17;  // Terminal path
  optional uint32 background_shell_id = 18;     // Background shell ID
}
```

### RunTerminalCommandEndedReason (aiserver.v1.RunTerminalCommandEndedReason)
**Location:** Line ~104576

```protobuf
enum RunTerminalCommandEndedReason {
  UNSPECIFIED = 0;
  EXECUTION_COMPLETED = 1;                      // Normal completion
  EXECUTION_ABORTED = 2;                        // User aborted
  EXECUTION_FAILED = 3;                         // Command failed
  ERROR_OCCURRED_CHECKING_REASON = 4;           // Check error
  IDLE_TIMEOUT = 5;                             // Timed out idle
}
```

### OutputLocation (aiserver.v1.OutputLocation)
**Location:** Line ~112549

For large outputs that are written to files:

```protobuf
message OutputLocation {
  string file_path = 1;                         // Path to output file
  int64 size_bytes = 2;                         // File size
  int64 line_count = 3;                         // Number of lines
}
```

---

## Search Operations

### SearchSymbolsParams (aiserver.v1.SearchSymbolsParams)
**Location:** Line ~113404

```protobuf
message SearchSymbolsParams {
  string query = 1;                             // Search query
}
```

### SearchSymbolsResult (aiserver.v1.SearchSymbolsResult)
**Location:** Line ~113434

```protobuf
message SearchSymbolsResult {
  repeated SymbolMatch matches = 1;             // Matching symbols
  optional bool rejected = 2;                   // User rejected

  message SymbolMatch {
    string name = 1;                            // Symbol name
    string uri = 2;                             // File URI
    optional Range range = 3;                   // Symbol location
    string secondary_text = 4;                  // Additional info
    repeated MatchRange label_matches = 5;      // Name match ranges
    repeated MatchRange description_matches = 6; // Desc match ranges
    double score = 7;                           // Relevance score
  }
}
```

### SemanticSearchFullParams (aiserver.v1.SemanticSearchFullParams)
**Location:** Line ~109289

```protobuf
message SemanticSearchFullParams {
  optional RepositoryInfo repository_info = 1;  // Repo context
  string query = 2;                             // Search query
  optional string include_pattern = 3;          // Include glob
  optional string exclude_pattern = 4;          // Exclude glob
  int32 top_k = 5;                              // Number of results
  repeated PullRequestReference pr_references = 6;  // PR context
  optional bool pr_search_on = 7;               // Enable PR search
  optional string explanation = 8;              // Search explanation
  repeated CodeResult code_results = 9;         // Existing results
}
```

### SemanticSearchFullResult (aiserver.v1.SemanticSearchFullResult)
**Location:** Line ~109365

```protobuf
message SemanticSearchFullResult {
  repeated CodeResult code_results = 1;         // Code matches
  repeated FileInfo all_files = 2;              // All matched files
  repeated MissingFile missing_files = 3;       // Files not found
  repeated Knowledge knowledge_results = 4;     // Knowledge base
  repeated ToolPullRequestResult pr_results = 5; // PR results
  optional string git_remote_url = 6;           // Repo URL
  optional bool pr_hydration_timed_out = 7;     // PR fetch timeout
}
```

### RipgrepRawSearchParams (aiserver.v1.RipgrepRawSearchParams)
**Location:** Line ~114934

```protobuf
message RipgrepRawSearchParams {
  string pattern = 1;                           // Search pattern (regex)
  optional string path = 2;                     // Search path
  repeated string ignore_globs = 3;             // Exclude patterns
  optional bool case_sensitive = 4;             // Case sensitivity
  optional int32 max_results = 5;               // Result limit
}
```

---

## Web and External Tools

### WebSearchParams (aiserver.v1.WebSearchParams)
**Location:** Line ~112797

```protobuf
message WebSearchParams {
  string search_term = 1;                       // Search query
}
```

### WebSearchResult (aiserver.v1.WebSearchResult)
**Location:** Line ~112827

```protobuf
message WebSearchResult {
  repeated WebReference references = 1;         // Search results
  optional bool is_final = 2;                   // Final results
  optional bool rejected = 3;                   // User rejected

  message WebReference {
    string title = 1;                           // Page title
    string url = 2;                             // Page URL
    string chunk = 3;                           // Content excerpt
  }
}
```

---

## MCP (Model Context Protocol) Tools

### MCPParams (aiserver.v1.MCPParams)
**Location:** Line ~112940

```protobuf
message MCPParams {
  repeated Tool tools = 1;                      // Available tools
  optional int64 file_output_threshold_bytes = 2;

  message Tool {
    string name = 1;                            // Tool name
    string description = 2;                     // Tool description
    string parameters = 3;                      // JSON schema
    string server_name = 4;                     // MCP server name
  }
}
```

### MCPResult (aiserver.v1.MCPResult)
**Location:** Line ~113022

```protobuf
message MCPResult {
  string selected_tool = 1;                     // Tool that was called
  string result = 2;                            // Tool output
}
```

---

## Task and Subagent Tools

### TaskParams (aiserver.v1.TaskParams)
**Location:** Line ~114612

```protobuf
message TaskParams {
  string task_description = 1;                  // Task description
  string task_title = 4;                        // Task title
  optional bool async = 2;                      // Run asynchronously
  repeated string allowed_write_directories = 3; // Write permissions
  optional string model_override = 5;           // Custom model
  optional bool max_mode_override = 6;          // Max mode
  optional bool default_expanded_while_running = 7;
}
```

### TaskResult (aiserver.v1.TaskResult)
**Location:** Line ~114679

```protobuf
message TaskResult {
  oneof result {
    CompletedTaskResult completed_task_result = 1;
    AsyncTaskResult async_task_result = 2;
  }

  message CompletedTaskResult {
    string summary = 1;                         // Task summary
    repeated FileResult file_results = 2;       // File changes
    bool user_aborted = 3;                      // User cancelled
    bool subagent_errored = 4;                  // Subagent failed
  }

  message AsyncTaskResult {
    string task_id = 1;                         // Background task ID
    bool user_aborted = 2;                      // User cancelled
    bool subagent_errored = 3;                  // Subagent failed
  }
}
```

### TaskV2Params (aiserver.v1.TaskV2Params)
**Location:** Line ~114827

```protobuf
message TaskV2Params {
  string description = 1;                       // Task description
  string prompt = 2;                            // Full prompt
  string subagent_type = 3;                     // Subagent type
  optional string model = 4;                    // Model to use
}
```

### TaskV2Result (aiserver.v1.TaskV2Result)
**Location:** Line ~114873

```protobuf
message TaskV2Result {
  optional string agent_id = 1;                 // Created agent ID
  bool is_background = 2;                       // Running in background
}
```

---

## Todo List Tools

### TodoReadParams (aiserver.v1.TodoReadParams)
**Location:** Line ~115721

```protobuf
message TodoReadParams {
  bool read = 1;                                // Trigger read
}
```

### TodoReadResult (aiserver.v1.TodoReadResult)
**Location:** Line ~115797

```protobuf
message TodoReadResult {
  repeated TodoItem todos = 1;                  // Current todos
}
```

### TodoWriteParams (aiserver.v1.TodoWriteParams)
**Location:** Line ~115853

```protobuf
message TodoWriteParams {
  repeated TodoItem todos = 1;                  // Todos to write
  bool merge = 2;                               // Merge with existing
}
```

### TodoWriteResult (aiserver.v1.TodoWriteResult)
**Location:** Line ~115889

```protobuf
message TodoWriteResult {
  bool success = 1;                             // Write succeeded
  repeated string ready_task_ids = 2;           // Ready tasks
  bool needs_in_progress_todos = 3;             // Needs active todo
  repeated TodoItem final_todos = 4;            // Resulting todos
  repeated TodoItem initial_todos = 5;          // Before todos
  bool was_merge = 6;                           // Merge was used
}
```

### TodoItem (aiserver.v1.TodoItem)
**Location:** Line ~115751

```protobuf
message TodoItem {
  string content = 1;                           // Todo text
  string status = 2;                            // "pending"|"in_progress"|"completed"
  string id = 3;                                // Unique ID
  repeated string dependencies = 4;             // Dependent task IDs
}
```

---

## Computer Use Tool

### ComputerUseParams (aiserver.v1.ComputerUseParams)
**Location:** Line ~117402

```protobuf
message ComputerUseParams {
  repeated ComputerAction actions = 1;          // Actions to perform
}
```

### ComputerUseResult (aiserver.v1.ComputerUseResult)
**Location:** Line ~117435

```protobuf
message ComputerUseResult {
  oneof result {
    ComputerUseSuccess success = 1;             // Success response
    ComputerUseError error = 2;                 // Error response
  }
}
```

---

## Human Review Message

### HumanReview (aiserver.v1.HumanReview)
**Location:** Line ~107223

Used in results to capture user feedback on tool operations:

```protobuf
message HumanReview {
  string selected_option = 1;                   // User selection
  string feedback_text = 2;                     // User feedback
  bool submit_feedback_as_new_message = 3;      // Add to conversation
  string bubble_id = 4;                         // UI element ID
}
```

---

## ClientSideToolV2 Enum Reference

**Location:** Line ~104365

Complete list of all 55+ tools:

| Value | Name | Description |
|-------|------|-------------|
| 0 | UNSPECIFIED | Default/unknown |
| 1 | READ_SEMSEARCH_FILES | Read semantically searched files |
| 3 | RIPGREP_SEARCH | Regex search with ripgrep |
| 5 | READ_FILE | Read file contents |
| 6 | LIST_DIR | List directory contents |
| 7 | EDIT_FILE | Edit file (legacy) |
| 8 | FILE_SEARCH | Fuzzy file name search |
| 9 | SEMANTIC_SEARCH_FULL | Full semantic search |
| 11 | DELETE_FILE | Delete file |
| 12 | REAPPLY | Reapply previous edit |
| 15 | RUN_TERMINAL_COMMAND_V2 | Execute terminal command |
| 16 | FETCH_RULES | Fetch cursor rules |
| 18 | WEB_SEARCH | Search the web |
| 19 | MCP | Call MCP tool (legacy) |
| 23 | SEARCH_SYMBOLS | Search code symbols |
| 24 | BACKGROUND_COMPOSER_FOLLOWUP | Followup with background agent |
| 25 | KNOWLEDGE_BASE | Query knowledge base |
| 26 | FETCH_PULL_REQUEST | Fetch PR information |
| 27 | DEEP_SEARCH | Deep codebase search |
| 28 | CREATE_DIAGRAM | Create Mermaid diagram |
| 29 | FIX_LINTS | Auto-fix lint errors |
| 30 | READ_LINTS | Read lint errors |
| 31 | GO_TO_DEFINITION | Go to symbol definition |
| 32 | TASK | Create subagent task |
| 33 | AWAIT_TASK | Wait for task completion |
| 34 | TODO_READ | Read todo list |
| 35 | TODO_WRITE | Write todo list |
| 38 | EDIT_FILE_V2 | Edit file (new) |
| 39 | LIST_DIR_V2 | List directory (tree) |
| 40 | READ_FILE_V2 | Read file (new) |
| 41 | RIPGREP_RAW_SEARCH | Raw ripgrep search |
| 42 | GLOB_FILE_SEARCH | Glob pattern file search |
| 43 | CREATE_PLAN | Create execution plan |
| 44 | LIST_MCP_RESOURCES | List MCP resources |
| 45 | READ_MCP_RESOURCE | Read MCP resource |
| 46 | READ_PROJECT | Read project info |
| 47 | UPDATE_PROJECT | Update project info |
| 48 | TASK_V2 | Create task (new) |
| 49 | CALL_MCP_TOOL | Call MCP tool (new) |
| 50 | APPLY_AGENT_DIFF | Apply agent-generated diff |
| 51 | ASK_QUESTION | Ask user a question |
| 52 | SWITCH_MODE | Switch agent mode |
| 53 | GENERATE_IMAGE | Generate image |
| 54 | COMPUTER_USE | Computer automation |
| 55 | WRITE_SHELL_STDIN | Write to shell stdin |

---

## Key Findings

1. **Tool Versioning**: Many tools have V2 versions (ReadFile, EditFile, ListDir, Task) indicating API evolution.

2. **Error Handling**: ToolResultError provides both user-visible and model-visible error messages, allowing the LLM to understand errors without exposing sensitive information to users.

3. **Human Review**: Most write operations (edit, delete, terminal) support HumanReview for user confirmation flows.

4. **Streaming Support**: Each tool has a Stream message type for progressive UI updates during execution.

5. **Background Execution**: Terminal commands and tasks support background execution with async result retrieval.

6. **Sandboxing**: Terminal command execution supports sandbox policies for security.

7. **Content Versioning**: EditFileV2 includes content IDs for tracking file versions during edits.

8. **Todo System**: Full todo management with dependencies for task tracking across agent operations.

---

## Future Investigation Needed

- **TASK-26a**: ComputerAction message structure for computer use tool
- **TASK-26b**: SandboxPolicy schema and enforcement
- **TASK-26c**: FileDiff message structure and diff format
- **TASK-26d**: Plan creation and management schemas (CreatePlan)
- **TASK-26e**: MCP resource schemas (ListMcpResources, ReadMcpResource)
