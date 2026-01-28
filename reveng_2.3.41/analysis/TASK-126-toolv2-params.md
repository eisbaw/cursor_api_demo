# TASK-126: ClientSideToolV2Call Parameter Protobuf Mappings

## Overview

This document maps the ClientSideToolV2Call message structure to its corresponding parameter protobuf classes. The ClientSideToolV2Call message is defined in `aiserver.v1` namespace and uses a oneof pattern for tool-specific parameters.

## Source Location

- File: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
- Primary definition starts at line ~104950
- Duplicate definition at line ~314100 (separate code path using different minified identifiers)

## ClientSideToolV2 Enum (vt)

The tool type enum `aiserver.v1.ClientSideToolV2` defines 43 tool types (lines 104366-104500):

| Enum Value | Name | Proto Number |
|------------|------|--------------|
| UNSPECIFIED | CLIENT_SIDE_TOOL_V2_UNSPECIFIED | 0 |
| READ_SEMSEARCH_FILES | CLIENT_SIDE_TOOL_V2_READ_SEMSEARCH_FILES | 1 |
| RIPGREP_SEARCH | CLIENT_SIDE_TOOL_V2_RIPGREP_SEARCH | 3 |
| READ_FILE | CLIENT_SIDE_TOOL_V2_READ_FILE | 5 |
| LIST_DIR | CLIENT_SIDE_TOOL_V2_LIST_DIR | 6 |
| EDIT_FILE | CLIENT_SIDE_TOOL_V2_EDIT_FILE | 7 |
| FILE_SEARCH | CLIENT_SIDE_TOOL_V2_FILE_SEARCH | 8 |
| SEMANTIC_SEARCH_FULL | CLIENT_SIDE_TOOL_V2_SEMANTIC_SEARCH_FULL | 9 |
| DELETE_FILE | CLIENT_SIDE_TOOL_V2_DELETE_FILE | 11 |
| REAPPLY | CLIENT_SIDE_TOOL_V2_REAPPLY | 12 |
| RUN_TERMINAL_COMMAND_V2 | CLIENT_SIDE_TOOL_V2_RUN_TERMINAL_COMMAND_V2 | 15 |
| FETCH_RULES | CLIENT_SIDE_TOOL_V2_FETCH_RULES | 16 |
| WEB_SEARCH | CLIENT_SIDE_TOOL_V2_WEB_SEARCH | 18 |
| MCP | CLIENT_SIDE_TOOL_V2_MCP | 19 |
| SEARCH_SYMBOLS | CLIENT_SIDE_TOOL_V2_SEARCH_SYMBOLS | 23 |
| BACKGROUND_COMPOSER_FOLLOWUP | CLIENT_SIDE_TOOL_V2_BACKGROUND_COMPOSER_FOLLOWUP | 24 |
| KNOWLEDGE_BASE | CLIENT_SIDE_TOOL_V2_KNOWLEDGE_BASE | 25 |
| FETCH_PULL_REQUEST | CLIENT_SIDE_TOOL_V2_FETCH_PULL_REQUEST | 26 |
| DEEP_SEARCH | CLIENT_SIDE_TOOL_V2_DEEP_SEARCH | 27 |
| CREATE_DIAGRAM | CLIENT_SIDE_TOOL_V2_CREATE_DIAGRAM | 28 |
| FIX_LINTS | CLIENT_SIDE_TOOL_V2_FIX_LINTS | 29 |
| READ_LINTS | CLIENT_SIDE_TOOL_V2_READ_LINTS | 30 |
| GO_TO_DEFINITION | CLIENT_SIDE_TOOL_V2_GO_TO_DEFINITION | 31 |
| TASK | CLIENT_SIDE_TOOL_V2_TASK | 32 |
| AWAIT_TASK | CLIENT_SIDE_TOOL_V2_AWAIT_TASK | 33 |
| TODO_READ | CLIENT_SIDE_TOOL_V2_TODO_READ | 34 |
| TODO_WRITE | CLIENT_SIDE_TOOL_V2_TODO_WRITE | 35 |
| EDIT_FILE_V2 | CLIENT_SIDE_TOOL_V2_EDIT_FILE_V2 | 38 |
| LIST_DIR_V2 | CLIENT_SIDE_TOOL_V2_LIST_DIR_V2 | 39 |
| READ_FILE_V2 | CLIENT_SIDE_TOOL_V2_READ_FILE_V2 | 40 |
| RIPGREP_RAW_SEARCH | CLIENT_SIDE_TOOL_V2_RIPGREP_RAW_SEARCH | 41 |
| GLOB_FILE_SEARCH | CLIENT_SIDE_TOOL_V2_GLOB_FILE_SEARCH | 42 |
| CREATE_PLAN | CLIENT_SIDE_TOOL_V2_CREATE_PLAN | 43 |
| LIST_MCP_RESOURCES | CLIENT_SIDE_TOOL_V2_LIST_MCP_RESOURCES | 44 |
| READ_MCP_RESOURCE | CLIENT_SIDE_TOOL_V2_READ_MCP_RESOURCE | 45 |
| READ_PROJECT | CLIENT_SIDE_TOOL_V2_READ_PROJECT | 46 |
| UPDATE_PROJECT | CLIENT_SIDE_TOOL_V2_UPDATE_PROJECT | 47 |
| TASK_V2 | CLIENT_SIDE_TOOL_V2_TASK_V2 | 48 |
| CALL_MCP_TOOL | CLIENT_SIDE_TOOL_V2_CALL_MCP_TOOL | 49 |
| APPLY_AGENT_DIFF | CLIENT_SIDE_TOOL_V2_APPLY_AGENT_DIFF | 50 |
| ASK_QUESTION | CLIENT_SIDE_TOOL_V2_ASK_QUESTION | 51 |
| SWITCH_MODE | CLIENT_SIDE_TOOL_V2_SWITCH_MODE | 52 |
| GENERATE_IMAGE | CLIENT_SIDE_TOOL_V2_GENERATE_IMAGE | 53 |
| COMPUTER_USE | CLIENT_SIDE_TOOL_V2_COMPUTER_USE | 54 |
| WRITE_SHELL_STDIN | CLIENT_SIDE_TOOL_V2_WRITE_SHELL_STDIN | 55 |

## ClientSideToolV2Call Message Structure

The message has the following base fields plus a params oneof:

```protobuf
message ClientSideToolV2Call {
  // Base fields
  ClientSideToolV2 tool = 1;           // Enum type
  string tool_call_id = 3;             // Tool call identifier
  optional uint64 timeout_ms = 6;      // Optional timeout
  string name = 9;                     // Tool name
  bool is_streaming = 14;              // Streaming flag
  bool is_last_message = 15;           // Last message flag
  bool internal = 16;                  // Internal flag
  string raw_args = 10;                // Raw arguments string

  // Tool-specific params (oneof)
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

## Parameter Class Mappings

### Minified Class Name to Protobuf Type

| Minified Name | Protobuf Type | Line | Fields |
|---------------|---------------|------|--------|
| Slt | ReadSemsearchFilesParams | 108968 | repository_info, code_results, query, pr_references, pr_search_on |
| vlt | RipgrepSearchParams | 107764 | options, pattern_info |
| $Bt | ReadFileParams | 107567 | relative_workspace_path, read_entire_file, start_line_one_indexed, end_line_one_indexed_inclusive, file_is_allowed_to_be_read_entirely |
| HBt | ListDirParams | 107417 | directory_path |
| glt | EditFileParams | 106719 | relative_workspace_path, language, blocking, contents, instructions, line_ranges |
| WBt | ToolCallFileSearchParams | 107285 | query |
| _lt | SemanticSearchFullParams | 109281 | repository_info, query, include_pattern, top_k, pr_references, code_results |
| zMe | DeleteFileParams | 109454 | relative_workspace_path |
| NBt | ReapplyParams | 104594 | relative_workspace_path |
| jMe | RunTerminalCommandV2Params | 112386 | command, cwd, new_session, options, is_background, require_user_approval |
| FBt | FetchRulesParams | 104706 | rule_names (repeated) |
| M7e | WebSearchParams | 112789 | search_term |
| N7e | MCPParams | 112932 | tools (repeated), file_output_threshold_bytes |
| KBt | SearchSymbolsParams | 113396 | query |
| klt | GotodefParams | 111231 | relative_workspace_path, symbol, start_line, end_line |
| YBt | BackgroundComposerFollowupParams | - | (not fully traced) |
| XBt | KnowledgeBaseParams | - | (not fully traced) |
| QBt | FetchPullRequestParams | - | (not fully traced) |
| ZBt | DeepSearchParams | - | (not fully traced) |
| t4t | CreateDiagramParams | - | (not fully traced) |
| i4t | FixLintsParams | - | (not fully traced) |
| Rlt | ReadLintsParams | - | (not fully traced) |
| s4t | TaskParams | - | (task related) |
| a4t | AwaitTaskParams | - | (task related) |
| c4t | TodoReadParams | - | (todo related) |
| V7e | TodoWriteParams | 115845 | todos (repeated TodoItem), merge |
| Ope | EditFileV2Params | 106440 | relative_workspace_path, contents_after_edit, waiting_for_file_contents, streaming_edit (oneof: text, code), should_send_back_linter_errors, result_for_model |
| H7e | ListDirV2Params | - | (v2 list dir) |
| nNe | ReadFileV2Params | - | (v2 read file) |
| eNe | RipgrepRawSearchParams | - | (raw ripgrep) |
| Mlt | GlobFileSearchParams | - | (glob search) |
| q7e | CreatePlanParams | - | (plan creation) |
| xlt | ListMcpResourcesParams | - | (MCP resources) |
| Dlt | ReadMcpResourceParams | - | (MCP resource read) |
| f4t | ReadProjectParams | - | (project read) |
| g4t | UpdateProjectParams | - | (project update) |
| B7e | TaskV2Params | - | (task v2) |
| jBt | CallMcpToolParams | 113316 | server, tool_name, tool_args |
| mlt | ApplyAgentDiffParams | 104624 | agent_id |
| aue | AskQuestionParams | - | (ask question) |
| sNe | SwitchModeParams | - | (mode switch) |
| J7e | ComputerUseParams | 117394 | actions (repeated) |
| WMe | WriteShellStdinParams | - | (shell stdin) |

## Detailed Parameter Structures

### Slt - ReadSemsearchFilesParams (aiserver.v1.ReadSemsearchFilesParams)

```javascript
// Line 108968
constructor: { codeResults: [], query: "", prReferences: [] }
fields: [
  { no: 1, name: "repository_info", kind: "message", T: Hb },
  { no: 2, name: "code_results", kind: "message", T: eR, repeated: true },
  { no: 3, name: "query", kind: "scalar", T: 9 },  // string
  { no: 4, name: "pr_references", kind: "message", T: zos, repeated: true },
  { no: 5, name: "pr_search_on", kind: "scalar", T: 8, opt: true }  // bool
]
```

### vlt - RipgrepSearchParams (aiserver.v1.RipgrepSearchParams)

```javascript
// Line 107764
constructor: {}
fields: [
  { no: 1, name: "options", kind: "message", T: Pos },
  { no: 2, name: "pattern_info", kind: "message", T: Ros }
]
```

### $Bt - ReadFileParams (aiserver.v1.ReadFileParams)

```javascript
// Line 107567
constructor: { relativeWorkspacePath: "", readEntireFile: false, fileIsAllowedToBeReadEntirely: false }
fields: [
  { no: 1, name: "relative_workspace_path", kind: "scalar", T: 9 },  // string
  { no: 2, name: "read_entire_file", kind: "scalar", T: 8 },  // bool
  { no: 3, name: "start_line_one_indexed", kind: "scalar", T: 5, opt: true },  // int32
  { no: 4, name: "end_line_one_indexed_inclusive", kind: "scalar", T: 5, opt: true },  // int32
  { no: 5, name: "file_is_allowed_to_be_read_entirely", kind: "scalar", T: 8 }  // bool
]
```

### HBt - ListDirParams (aiserver.v1.ListDirParams)

```javascript
// Line 107417
constructor: { directoryPath: "" }
fields: [
  { no: 1, name: "directory_path", kind: "scalar", T: 9 }  // string
]
```

### glt - EditFileParams (aiserver.v1.EditFileParams)

```javascript
// Line 106719
constructor: { relativeWorkspacePath: "", language: "", blocking: false, contents: "", lineRanges: [] }
fields: [
  { no: 1, name: "relative_workspace_path", kind: "scalar", T: 9 },
  { no: 2, name: "language", kind: "scalar", T: 9 },
  { no: 4, name: "blocking", kind: "scalar", T: 8 },
  { no: 3, name: "contents", kind: "scalar", T: 9 },
  { no: 5, name: "instructions", kind: "scalar", T: 9, opt: true },
  { no: 6, name: "line_ranges", kind: "message", T: ..., repeated: true }
]
```

### WBt - ToolCallFileSearchParams (aiserver.v1.ToolCallFileSearchParams)

```javascript
// Line 107285
constructor: { query: "" }
fields: [
  { no: 1, name: "query", kind: "scalar", T: 9 }  // string
]
```

### _lt - SemanticSearchFullParams (aiserver.v1.SemanticSearchFullParams)

```javascript
// Line 109281
constructor: { query: "", topK: 0, prReferences: [], codeResults: [] }
fields: [
  { no: 1, name: "repository_info", kind: "message", T: Hb },
  { no: 2, name: "query", kind: "scalar", T: 9 },
  { no: 3, name: "include_pattern", kind: "scalar", T: 9, opt: true },
  { no: 4, name: "top_k", kind: "scalar", T: 5 },  // int32
  { no: 5, name: "pr_references", kind: "message", T: ..., repeated: true },
  { no: 6, name: "code_results", kind: "message", T: ..., repeated: true }
]
```

### zMe - DeleteFileParams (aiserver.v1.DeleteFileParams)

```javascript
// Line 109454
constructor: { relativeWorkspacePath: "" }
fields: [
  { no: 1, name: "relative_workspace_path", kind: "scalar", T: 9 }
]
```

### NBt - ReapplyParams (aiserver.v1.ReapplyParams)

```javascript
// Line 104594
constructor: { relativeWorkspacePath: "" }
fields: [
  { no: 1, name: "relative_workspace_path", kind: "scalar", T: 9 }
]
```

### jMe - RunTerminalCommandV2Params (aiserver.v1.RunTerminalCommandV2Params)

```javascript
// Line 112386
constructor: { command: "", isBackground: false, requireUserApproval: false }
fields: [
  { no: 1, name: "command", kind: "scalar", T: 9 },
  { no: 2, name: "cwd", kind: "scalar", T: 9, opt: true },
  { no: 3, name: "new_session", kind: "scalar", T: 8, opt: true },
  { no: 4, name: "options", kind: "message", T: Vos, opt: true },
  { no: 5, name: "is_background", kind: "scalar", T: 8 },
  { no: 6, name: "require_user_approval", kind: "scalar", T: 8 }
]
```

### FBt - FetchRulesParams (aiserver.v1.FetchRulesParams)

```javascript
// Line 104706
constructor: { ruleNames: [] }
fields: [
  { no: 1, name: "rule_names", kind: "scalar", T: 9, repeated: true }
]
```

### M7e - WebSearchParams (aiserver.v1.WebSearchParams)

```javascript
// Line 112789
constructor: { searchTerm: "" }
fields: [
  { no: 1, name: "search_term", kind: "scalar", T: 9 }
]
```

### N7e - MCPParams (aiserver.v1.MCPParams)

```javascript
// Line 112932
constructor: { tools: [] }
fields: [
  { no: 1, name: "tools", kind: "message", T: I1e, repeated: true },
  { no: 2, name: "file_output_threshold_bytes", kind: "scalar", T: 3, opt: true }
]
```

### KBt - SearchSymbolsParams (aiserver.v1.SearchSymbolsParams)

```javascript
// Line 113396
constructor: { query: "" }
fields: [
  { no: 1, name: "query", kind: "scalar", T: 9 }
]
```

### klt - GotodefParams (aiserver.v1.GotodefParams)

```javascript
// Line 111231
constructor: { relativeWorkspacePath: "", symbol: "", startLine: 0, endLine: 0 }
fields: [
  { no: 1, name: "relative_workspace_path", kind: "scalar", T: 9 },
  { no: 2, name: "symbol", kind: "scalar", T: 9 },
  { no: 3, name: "start_line", kind: "scalar", T: 5 },
  { no: 4, name: "end_line", kind: "scalar", T: 5 }
]
```

### V7e - TodoWriteParams (aiserver.v1.TodoWriteParams)

```javascript
// Line 115845
constructor: { todos: [], merge: false }
fields: [
  { no: 1, name: "todos", kind: "message", T: JR, repeated: true },  // TodoItem
  { no: 2, name: "merge", kind: "scalar", T: 8 }
]
```

### Ope - EditFileV2Params (aiserver.v1.EditFileV2Params)

```javascript
// Line 106440
constructor: {
  relativeWorkspacePath: "",
  streamingEdit: { case: void 0 },
  shouldSendBackLinterErrors: false,
  resultForModel: ""
}
fields: [
  { no: 1, name: "relative_workspace_path", kind: "scalar", T: 9 },
  { no: 2, name: "contents_after_edit", kind: "scalar", T: 9, opt: true },
  { no: 3, name: "waiting_for_file_contents", kind: "scalar", T: 8, opt: true },
  { no: 4, name: "text", kind: "message", T: HIr, oneof: "streaming_edit" },
  { no: 5, name: "code", kind: "message", T: $Ir, oneof: "streaming_edit" },
  { no: 6, name: "should_send_back_linter_errors", kind: "scalar", T: 8 },
  { no: 7, name: "result_for_model", kind: "scalar", T: 9 }
]
```

### jBt - CallMcpToolParams (aiserver.v1.CallMcpToolParams)

```javascript
// Line 113316
constructor: { server: "", toolName: "" }
fields: [
  { no: 1, name: "server", kind: "scalar", T: 9 },
  { no: 2, name: "tool_name", kind: "scalar", T: 9 },
  { no: 3, name: "tool_args", kind: "message", T: ZD }  // google.protobuf.Struct
]
```

### mlt - ApplyAgentDiffParams (aiserver.v1.ApplyAgentDiffParams)

```javascript
// Line 104624
constructor: { agentId: "" }
fields: [
  { no: 1, name: "agent_id", kind: "scalar", T: 9 }
]
```

### J7e - ComputerUseParams (aiserver.v1.ComputerUseParams)

```javascript
// Line 117394
constructor: { actions: [] }
fields: [
  { no: 1, name: "actions", kind: "message", T: LIr, repeated: true }
]
```

## Protobuf Scalar Types Reference

The `T` values in field definitions map to protobuf wire types:
- 1 = double
- 2 = float
- 3 = int64
- 4 = uint64
- 5 = int32
- 6 = fixed64
- 7 = fixed32
- 8 = bool
- 9 = string
- 10 = group (deprecated)
- 11 = message
- 12 = bytes
- 13 = uint32
- 14 = enum
- 15 = sfixed32
- 16 = sfixed64
- 17 = sint32
- 18 = sint64

## Alternative Module Definition (Line 314100+)

A second instance of ClientSideToolV2Call exists using different minified identifiers:

| Primary ID | Alternate ID | Protobuf Type |
|------------|--------------|---------------|
| Slt | Vys | ReadSemsearchFilesParams |
| vlt | EJr | RipgrepSearchParams |
| $Bt | kJr | ReadFileParams |
| HBt | _Jr | ListDirParams |
| glt | wJr | EditFileParams |
| WBt | SJr | ToolCallFileSearchParams |
| _lt | LJr | SemanticSearchFullParams |
| zMe | $ys | DeleteFileParams |
| NBt | gJr | ReapplyParams |
| jMe | BJr | RunTerminalCommandV2Params |
| FBt | vJr | FetchRulesParams |
| M7e | UJr | WebSearchParams |
| N7e | WJr | MCPParams |
| KBt | qJr | SearchSymbolsParams |

This duplication suggests the code exists in two separate compilation units or chunks.

## Export Map

The tool classes are exported in the module export block (lines 104101-104359):

```javascript
ClientSideToolV2Call: () => mJ,
ReadSemsearchFilesParams: () => Slt,
RipgrepSearchParams: () => vlt,
ReadFileParams: () => $Bt,
ListDirParams: () => HBt,
EditFileParams: () => glt,
// ... etc
```

## Usage Context

The ClientSideToolV2Call message is used in:
1. Tracing context creation: `r$d("ClientSideToolV2Call", Pe.tracingContext)` (line 484588)
2. Composer replay parsing: `[composer.replay] Failed to parse ClientSideToolV2Call` (line 488639)
3. Tool execution pipeline for agent-based workflows

## Key Insights

1. **Oneof Pattern**: The params field uses protobuf oneof, meaning only one parameter type is set per message
2. **Field Number Gaps**: Some field numbers are skipped (e.g., 4, 7, 10, 11, etc.), suggesting deprecated or reserved fields
3. **V2 Variants**: Several tools have V2 variants (EditFileV2, ListDirV2, ReadFileV2) with enhanced functionality
4. **MCP Integration**: Multiple MCP-related tools (MCPParams, CallMcpToolParams, ListMcpResourcesParams, ReadMcpResourceParams)
5. **Agent Features**: ApplyAgentDiffParams and related tools support agent-based workflows
6. **Computer Use**: ComputerUseParams suggests GUI automation capabilities

## Related Tasks

- TASK-110: Tool Enum Mapping (covers the enum values)
- TASK-127: Computer Use (covers J7e/ComputerUseParams in detail)
- TASK-26: Tool Schemas (general tool schema documentation)

---
*Generated by analysis of Cursor IDE 2.3.41 beautified source*
