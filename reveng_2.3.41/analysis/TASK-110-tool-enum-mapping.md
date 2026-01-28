# TASK-110: BuiltinTool and ClientSideToolV2 Enum Mapping

## Overview

Cursor implements two distinct tool enum systems in `aiserver.v1`:
- **BuiltinTool** (`$Me`): Legacy/server-side tool enum with 20 tools
- **ClientSideToolV2** (`vt`): Modern client-side tool enum with 44 tools

These are defined in `out-build/proto/aiserver/v1/tools_pb.js` (beautified line ~104360).

## ClientSideToolV2 Enum (Modern System)

| ID | Enum Name | Short Name | Category |
|----|-----------|------------|----------|
| 0 | CLIENT_SIDE_TOOL_V2_UNSPECIFIED | UNSPECIFIED | - |
| 1 | CLIENT_SIDE_TOOL_V2_READ_SEMSEARCH_FILES | READ_SEMSEARCH_FILES | Search |
| 3 | CLIENT_SIDE_TOOL_V2_RIPGREP_SEARCH | RIPGREP_SEARCH | Search |
| 5 | CLIENT_SIDE_TOOL_V2_READ_FILE | READ_FILE | File |
| 6 | CLIENT_SIDE_TOOL_V2_LIST_DIR | LIST_DIR | File |
| 7 | CLIENT_SIDE_TOOL_V2_EDIT_FILE | EDIT_FILE | File |
| 8 | CLIENT_SIDE_TOOL_V2_FILE_SEARCH | FILE_SEARCH | Search |
| 9 | CLIENT_SIDE_TOOL_V2_SEMANTIC_SEARCH_FULL | SEMANTIC_SEARCH_FULL | Search |
| 11 | CLIENT_SIDE_TOOL_V2_DELETE_FILE | DELETE_FILE | File |
| 12 | CLIENT_SIDE_TOOL_V2_REAPPLY | REAPPLY | Edit |
| 15 | CLIENT_SIDE_TOOL_V2_RUN_TERMINAL_COMMAND_V2 | RUN_TERMINAL_COMMAND_V2 | Terminal |
| 16 | CLIENT_SIDE_TOOL_V2_FETCH_RULES | FETCH_RULES | Context |
| 18 | CLIENT_SIDE_TOOL_V2_WEB_SEARCH | WEB_SEARCH | External |
| 19 | CLIENT_SIDE_TOOL_V2_MCP | MCP | MCP |
| 23 | CLIENT_SIDE_TOOL_V2_SEARCH_SYMBOLS | SEARCH_SYMBOLS | Search |
| 24 | CLIENT_SIDE_TOOL_V2_BACKGROUND_COMPOSER_FOLLOWUP | BACKGROUND_COMPOSER_FOLLOWUP | Agent |
| 25 | CLIENT_SIDE_TOOL_V2_KNOWLEDGE_BASE | KNOWLEDGE_BASE | Context |
| 26 | CLIENT_SIDE_TOOL_V2_FETCH_PULL_REQUEST | FETCH_PULL_REQUEST | Git |
| 27 | CLIENT_SIDE_TOOL_V2_DEEP_SEARCH | DEEP_SEARCH | Search |
| 28 | CLIENT_SIDE_TOOL_V2_CREATE_DIAGRAM | CREATE_DIAGRAM | Output |
| 29 | CLIENT_SIDE_TOOL_V2_FIX_LINTS | FIX_LINTS | Lint |
| 30 | CLIENT_SIDE_TOOL_V2_READ_LINTS | READ_LINTS | Lint |
| 31 | CLIENT_SIDE_TOOL_V2_GO_TO_DEFINITION | GO_TO_DEFINITION | Navigation |
| 32 | CLIENT_SIDE_TOOL_V2_TASK | TASK | Task |
| 33 | CLIENT_SIDE_TOOL_V2_AWAIT_TASK | AWAIT_TASK | Task |
| 34 | CLIENT_SIDE_TOOL_V2_TODO_READ | TODO_READ | Task |
| 35 | CLIENT_SIDE_TOOL_V2_TODO_WRITE | TODO_WRITE | Task |
| 38 | CLIENT_SIDE_TOOL_V2_EDIT_FILE_V2 | EDIT_FILE_V2 | File |
| 39 | CLIENT_SIDE_TOOL_V2_LIST_DIR_V2 | LIST_DIR_V2 | File |
| 40 | CLIENT_SIDE_TOOL_V2_READ_FILE_V2 | READ_FILE_V2 | File |
| 41 | CLIENT_SIDE_TOOL_V2_RIPGREP_RAW_SEARCH | RIPGREP_RAW_SEARCH | Search |
| 42 | CLIENT_SIDE_TOOL_V2_GLOB_FILE_SEARCH | GLOB_FILE_SEARCH | Search |
| 43 | CLIENT_SIDE_TOOL_V2_CREATE_PLAN | CREATE_PLAN | Planning |
| 44 | CLIENT_SIDE_TOOL_V2_LIST_MCP_RESOURCES | LIST_MCP_RESOURCES | MCP |
| 45 | CLIENT_SIDE_TOOL_V2_READ_MCP_RESOURCE | READ_MCP_RESOURCE | MCP |
| 46 | CLIENT_SIDE_TOOL_V2_READ_PROJECT | READ_PROJECT | Project |
| 47 | CLIENT_SIDE_TOOL_V2_UPDATE_PROJECT | UPDATE_PROJECT | Project |
| 48 | CLIENT_SIDE_TOOL_V2_TASK_V2 | TASK_V2 | Task |
| 49 | CLIENT_SIDE_TOOL_V2_CALL_MCP_TOOL | CALL_MCP_TOOL | MCP |
| 50 | CLIENT_SIDE_TOOL_V2_APPLY_AGENT_DIFF | APPLY_AGENT_DIFF | Agent |
| 51 | CLIENT_SIDE_TOOL_V2_ASK_QUESTION | ASK_QUESTION | User |
| 52 | CLIENT_SIDE_TOOL_V2_SWITCH_MODE | SWITCH_MODE | Mode |
| 53 | CLIENT_SIDE_TOOL_V2_GENERATE_IMAGE | GENERATE_IMAGE | Output |
| 54 | CLIENT_SIDE_TOOL_V2_COMPUTER_USE | COMPUTER_USE | External |
| 55 | CLIENT_SIDE_TOOL_V2_WRITE_SHELL_STDIN | WRITE_SHELL_STDIN | Terminal |

**Note**: IDs 2, 4, 10, 13, 14, 17, 20-22, 36-37 are not assigned (gaps in numbering).

## BuiltinTool Enum (Legacy System)

| ID | Enum Name | Short Name | Category |
|----|-----------|------------|----------|
| 0 | BUILTIN_TOOL_UNSPECIFIED | UNSPECIFIED | - |
| 1 | BUILTIN_TOOL_SEARCH | SEARCH | Search |
| 2 | BUILTIN_TOOL_READ_CHUNK | READ_CHUNK | File |
| 3 | BUILTIN_TOOL_GOTODEF | GOTODEF | Navigation |
| 4 | BUILTIN_TOOL_EDIT | EDIT | Edit |
| 5 | BUILTIN_TOOL_UNDO_EDIT | UNDO_EDIT | Edit |
| 6 | BUILTIN_TOOL_END | END | Control |
| 7 | BUILTIN_TOOL_NEW_FILE | NEW_FILE | File |
| 8 | BUILTIN_TOOL_ADD_TEST | ADD_TEST | Test |
| 9 | BUILTIN_TOOL_RUN_TEST | RUN_TEST | Test |
| 10 | BUILTIN_TOOL_DELETE_TEST | DELETE_TEST | Test |
| 11 | BUILTIN_TOOL_SAVE_FILE | SAVE_FILE | File |
| 12 | BUILTIN_TOOL_GET_TESTS | GET_TESTS | Test |
| 13 | BUILTIN_TOOL_GET_SYMBOLS | GET_SYMBOLS | Search |
| 14 | BUILTIN_TOOL_SEMANTIC_SEARCH | SEMANTIC_SEARCH | Search |
| 15 | BUILTIN_TOOL_GET_PROJECT_STRUCTURE | GET_PROJECT_STRUCTURE | Context |
| 16 | BUILTIN_TOOL_CREATE_RM_FILES | CREATE_RM_FILES | File |
| 17 | BUILTIN_TOOL_RUN_TERMINAL_COMMANDS | RUN_TERMINAL_COMMANDS | Terminal |
| 18 | BUILTIN_TOOL_NEW_EDIT | NEW_EDIT | Edit |
| 19 | BUILTIN_TOOL_READ_WITH_LINTER | READ_WITH_LINTER | Lint |

## Functional Mapping Between Systems

### Conceptually Similar Tools

| BuiltinTool | ClientSideToolV2 | Notes |
|-------------|------------------|-------|
| SEARCH (1) | RIPGREP_SEARCH (3) | Different search implementations |
| READ_CHUNK (2) | READ_FILE (5), READ_FILE_V2 (40) | V2 has two versions |
| GOTODEF (3) | GO_TO_DEFINITION (31) | Same functionality |
| EDIT (4) | EDIT_FILE (7), EDIT_FILE_V2 (38) | V2 has evolved versions |
| NEW_FILE (7) | (no direct equivalent) | V2 uses EDIT_FILE for creation |
| GET_SYMBOLS (13) | SEARCH_SYMBOLS (23) | Symbol search |
| SEMANTIC_SEARCH (14) | SEMANTIC_SEARCH_FULL (9) | Semantic search |
| RUN_TERMINAL_COMMANDS (17) | RUN_TERMINAL_COMMAND_V2 (15) | Terminal execution |
| READ_WITH_LINTER (19) | READ_LINTS (30) | Lint reading |

### Tools Only in ClientSideToolV2 (New Features)

| Tool | ID | Purpose |
|------|-----|---------|
| READ_SEMSEARCH_FILES | 1 | Semantic search file retrieval |
| LIST_DIR / LIST_DIR_V2 | 6, 39 | Directory listing |
| DELETE_FILE | 11 | File deletion |
| REAPPLY | 12 | Re-apply edits |
| FETCH_RULES | 16 | Rules/settings context |
| WEB_SEARCH | 18 | Web search integration |
| MCP | 19 | Model Context Protocol |
| BACKGROUND_COMPOSER_FOLLOWUP | 24 | Background agent |
| KNOWLEDGE_BASE | 25 | Knowledge base queries |
| FETCH_PULL_REQUEST | 26 | Git PR fetching |
| DEEP_SEARCH | 27 | Deep semantic search |
| CREATE_DIAGRAM | 28 | Diagram generation |
| FIX_LINTS | 29 | Auto-fix lint issues |
| TASK / TASK_V2 | 32, 48 | Sub-task spawning |
| AWAIT_TASK | 33 | Task synchronization |
| TODO_READ / TODO_WRITE | 34, 35 | Todo list management |
| GLOB_FILE_SEARCH | 42 | Glob pattern search |
| CREATE_PLAN | 43 | Planning tool |
| LIST_MCP_RESOURCES | 44 | MCP resource listing |
| READ_MCP_RESOURCE | 45 | MCP resource reading |
| READ_PROJECT / UPDATE_PROJECT | 46, 47 | Project config |
| CALL_MCP_TOOL | 49 | MCP tool invocation |
| APPLY_AGENT_DIFF | 50 | Agent diff application |
| ASK_QUESTION | 51 | User interaction |
| SWITCH_MODE | 52 | Mode switching |
| GENERATE_IMAGE | 53 | Image generation |
| COMPUTER_USE | 54 | Computer use automation |
| WRITE_SHELL_STDIN | 55 | Shell stdin writing |
| RIPGREP_RAW_SEARCH | 41 | Raw ripgrep access |

### Tools Only in BuiltinTool (Legacy/Deprecated)

| Tool | ID | Purpose |
|------|-----|---------|
| UNDO_EDIT | 5 | Undo edits |
| END | 6 | End signal |
| ADD_TEST | 8 | Add test case |
| RUN_TEST | 9 | Run test case |
| DELETE_TEST | 10 | Delete test case |
| SAVE_FILE | 11 | Save file explicitly |
| GET_TESTS | 12 | Get test cases |
| GET_PROJECT_STRUCTURE | 15 | Project structure |
| CREATE_RM_FILES | 16 | Create/remove files |
| NEW_EDIT | 18 | New edit pattern |

## Message Structures

### ClientSideToolV2Call (line ~104959)

```protobuf
message ClientSideToolV2Call {
  ClientSideToolV2 tool = 1;
  oneof params { ... }  // Tool-specific params
  string tool_call_id = 3;
  optional double timeout_ms = 6;
  string name = 9;
  bool is_streaming = 14;
  bool is_last_message = 15;
  bool internal = 51;
  string raw_args = 10;
  optional uint32 tool_index = 48;
  optional string model_call_id = 49;
}
```

### BuiltinToolCall (line ~109564)

```protobuf
message BuiltinToolCall {
  BuiltinTool tool = 1;
  oneof params { ... }  // Tool-specific params
  optional string tool_call_id = 22;
}
```

## Key Observations

1. **No Direct Mapping Code Found**: The codebase does not contain explicit mapping functions between BuiltinTool and ClientSideToolV2. They appear to be separate systems.

2. **ClientSideToolV2 is More Comprehensive**: The V2 system has 44 tools vs 20 in the legacy system, including:
   - MCP integration (tools 19, 44, 45, 49)
   - Task/agent management (tools 24, 32, 33, 48, 50)
   - Todo management (tools 34, 35)
   - Advanced search (tools 27, 41, 42)
   - New output types (tools 28, 53)
   - Computer use automation (tool 54)

3. **Version Evolution**: Several tools have V2 versions:
   - EDIT_FILE -> EDIT_FILE_V2 (7 -> 38)
   - LIST_DIR -> LIST_DIR_V2 (6 -> 39)
   - READ_FILE -> READ_FILE_V2 (5 -> 40)
   - TASK -> TASK_V2 (32 -> 48)

4. **ID Gap Analysis**: ClientSideToolV2 has gaps (2, 4, 10, 13, 14, 17, 20-22, 36-37) suggesting deprecated or reserved tools.

5. **BuiltinTool Legacy Features**: Contains test-related tools (ADD_TEST, RUN_TEST, DELETE_TEST, GET_TESTS) not present in V2, suggesting this feature may have been removed or refactored.

## Source References

- Enum definitions: `workbench.desktop.main.js` lines 104365-104574
- ClientSideToolV2Call message: lines 104950-105286
- BuiltinToolCall message: lines 109554-109723
- ClientSideToolV2Result message: lines 105287-105350+
- BuiltinToolResult message: lines 109724-109800+

## Tool Parameter/Result Name Mapping (eoe)

The `eoe` object (line 480036-480204) maps each ClientSideToolV2 tool to its protobuf param/result field names:

| Tool | paramName | returnName |
|------|-----------|------------|
| READ_SEMSEARCH_FILES | readSemsearchFilesParams | readSemsearchFilesResult |
| RIPGREP_SEARCH | ripgrepSearchParams | ripgrepSearchResult |
| RIPGREP_RAW_SEARCH | ripgrepRawSearchParams | ripgrepRawSearchResult |
| RUN_TERMINAL_COMMAND_V2 | runTerminalCommandV2Params | runTerminalCommandV2Result |
| READ_FILE | readFileParams | readFileResult |
| LIST_DIR | listDirParams | listDirResult |
| EDIT_FILE | editFileParams | editFileResult |
| FILE_SEARCH | fileSearchParams | fileSearchResult |
| SEMANTIC_SEARCH_FULL | semanticSearchFullParams | semanticSearchFullResult |
| DELETE_FILE | deleteFileParams | deleteFileResult |
| REAPPLY | reapplyParams | reapplyResult |
| FETCH_RULES | fetchRulesParams | fetchRulesResult |
| WEB_SEARCH | webSearchParams | webSearchResult |
| MCP | mcpParams | mcpResult |
| SEARCH_SYMBOLS | searchSymbolsParams | searchSymbolsResult |
| BACKGROUND_COMPOSER_FOLLOWUP | backgroundComposerFollowupParams | backgroundComposerFollowupResult |
| KNOWLEDGE_BASE | knowledgeBaseParams | knowledgeBaseResult |
| FETCH_PULL_REQUEST | fetchPullRequestParams | fetchPullRequestResult |
| DEEP_SEARCH | deepSearchParams | deepSearchResult |
| CREATE_DIAGRAM | createDiagramParams | createDiagramResult |
| FIX_LINTS | fixLintsParams | fixLintsResult |
| READ_LINTS | readLintsParams | readLintsResult |
| GO_TO_DEFINITION | gotodefParams | gotodefResult |
| TASK | taskParams | taskResult |
| AWAIT_TASK | awaitTaskParams | awaitTaskResult |
| TODO_READ | todoReadParams | todoReadResult |
| TODO_WRITE | todoWriteParams | todoWriteResult |
| EDIT_FILE_V2 | editFileV2Params | editFileV2Result |
| LIST_DIR_V2 | listDirV2Params | listDirV2Result |
| READ_FILE_V2 | readFileV2Params | readFileV2Result |
| GLOB_FILE_SEARCH | globFileSearchParams | globFileSearchResult |
| LIST_MCP_RESOURCES | listMcpResourcesParams | listMcpResourcesResult |
| READ_MCP_RESOURCE | readMcpResourceParams | readMcpResourceResult |
| CALL_MCP_TOOL | callMcpToolParams | callMcpToolResult |
| APPLY_AGENT_DIFF | applyAgentDiffParams | applyAgentDiffResult |
| CREATE_PLAN | createPlanParams | createPlanResult |
| READ_PROJECT | readProjectParams | readProjectResult |
| UPDATE_PROJECT | updateProjectParams | updateProjectResult |
| TASK_V2 | taskV2Params | taskV2Result |
| ASK_QUESTION | askQuestionParams | askQuestionResult |
| SWITCH_MODE | switchModeParams | switchModeResult |
| GENERATE_IMAGE | generateImageArgs | generateImageResult |

## String-Based Tool Names

Tool names are also represented as strings in certain contexts (line 696199-696211):

```javascript
{
    codebase_search: "Codebase search",
    run_terminal_cmd: "Run terminal command",
    list_dir: "List directory",
    grep_search: "Grep search",
    edit_file: "Edit file",
    read_file: "Read file",
    file_search: "File search",
    delete_file: "Delete file",
    reapply: "Reapply",
    fetch_rules: "Fetch rules",
    web_search: "Web search",
    mcp: "MCP"
}
```

String names are used in `ClientSideToolV2Call.name` field and for tool call display in the UI.

## Tool UI Categories (kqe)

Tools are organized into UI categories (line 215345-215383):

### Search Category
- READ_SEMSEARCH_FILES (label: "Codebase")
- WEB_SEARCH (label: "Web")
- RIPGREP_RAW_SEARCH (label: "Grep Search")
- FILE_SEARCH (label: "Search files")

### Edit Category
- EDIT_FILE (label: "Edit & Reapply")
- DELETE_FILE (label: "Delete file")

### Run Category
- RUN_TERMINAL_COMMAND_V2 (label: "Terminal")

## Tool Approval Configuration

Tools requiring user approval (line 215319-215344):

| Tool | Accept Label | Reject Label | Wait Text |
|------|--------------|--------------|-----------|
| RUN_TERMINAL_COMMAND_V2 | "Run" | "Stop" | "Waiting for approval" |
| EDIT_FILE | "Keep" | "Undo" | "" |
| BACKGROUND_COMPOSER_FOLLOWUP | "Send to background composer" | "Skip" | "Waiting for approval" |
| WEB_SEARCH | "Continue" | "Cancel" | "Waiting for approval" |
| SWITCH_MODE | "Switch" | "Skip" | "Waiting for approval" |

## Background-Capable Tools

Tools that can run without blocking the UI (line 450892, `sMc` set):
- FETCH_PULL_REQUEST
- GO_TO_DEFINITION
- BACKGROUND_COMPOSER_FOLLOWUP
- SEARCH_SYMBOLS
- READ_FILE
- LIST_DIR
- CREATE_DIAGRAM
- RIPGREP_SEARCH

## Tools That Can Be Grouped/Collapsed in UI

For UI display, these tools can be grouped together (line 720732):
- Search tools: WEB_SEARCH, LIST_DIR, LIST_DIR_V2, RIPGREP_SEARCH, RIPGREP_RAW_SEARCH, SEMANTIC_SEARCH_FULL, FILE_SEARCH, GLOB_FILE_SEARCH, READ_SEMSEARCH_FILES, SEARCH_SYMBOLS, GO_TO_DEFINITION
- Read tools (when groupReads enabled): READ_FILE, READ_FILE_V2

## V1/V2 Tool Version Handling

Code frequently checks for both versions (pattern found throughout codebase):

```javascript
// Example patterns:
if (t.bubbleTool === vt.EDIT_FILE || t.bubbleTool === vt.EDIT_FILE_V2)
if (i.bubbleData?.tool === vt.READ_FILE || i.bubbleData?.tool === vt.READ_FILE_V2)
if (t === vt.LIST_DIR || t === vt.LIST_DIR_V2)
```

This indicates both V1 and V2 versions are actively used with V1 tools still in production.

## StreamedBackToolCall Messages

Two versions exist for streaming tool calls:

### StreamedBackToolCall (line 105800-105900)
- Uses ClientSideToolV2 enum (not BuiltinTool)
- Contains stream-specific param messages (e.g., `readSemsearchFilesStream`)

### StreamedBackToolCallV2 (line 106120-106200)
- Also uses ClientSideToolV2 enum
- Contains params messages (e.g., `readSemsearchFilesParams`)

Both use the modern ClientSideToolV2 system, not the legacy BuiltinTool.

## Related Files

- `out-build/proto/aiserver/v1/tools_pb.js` - Main tool definitions
- Uses protobuf-es runtime (`v.util.setEnumType`)
