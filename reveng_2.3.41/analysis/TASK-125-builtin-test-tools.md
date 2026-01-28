# TASK-125: BuiltinTool Test-Related Tools Analysis

**Source:** `reveng_2.3.41/beautified/workbench.desktop.main.js`
**Analysis Date:** 2026-01-28
**Related:** TASK-110-tool-enum-mapping.md, TASK-52-toolcall-schema.md

## Overview

This analysis investigates the test-related tools in the BuiltinTool enum (ADD_TEST, RUN_TEST, DELETE_TEST, GET_TESTS) and why they are absent from ClientSideToolV2. The key finding is that these tools represent a legacy server-orchestrated test management system that has been superseded by more flexible client-side approaches.

---

## Test Tools in BuiltinTool Enum

### Enum Definitions (line ~104513)

| ID | Enum Name | Short Name |
|----|-----------|------------|
| 8 | BUILTIN_TOOL_ADD_TEST | ADD_TEST |
| 9 | BUILTIN_TOOL_RUN_TEST | RUN_TEST |
| 10 | BUILTIN_TOOL_DELETE_TEST | DELETE_TEST |
| 12 | BUILTIN_TOOL_GET_TESTS | GET_TESTS |

Note: ID 11 is SAVE_FILE, not a test tool. The test tools occupy IDs 8-10 and 12.

### BuiltinToolCall Message Structure (line ~109554)

The BuiltinToolCall message includes params fields for all test tools:

```protobuf
message BuiltinToolCall {
  BuiltinTool tool = 1;
  optional string tool_call_id = 22;

  oneof params {
    // ... other params ...
    AddTestParams add_test_params = 9;      // Field no: 9
    RunTestParams run_test_params = 10;     // Field no: 10
    DeleteTestParams delete_test_params = 11; // Field no: 11
    GetTestsParams get_tests_params = 13;   // Field no: 13
    // ... other params ...
  }
}
```

### BuiltinToolResult Message Structure (line ~109724)

```protobuf
message BuiltinToolResult {
  BuiltinTool tool = 1;

  oneof result {
    // ... other results ...
    AddTestResult add_test_result = 9;      // Field no: 9
    RunTestResult run_test_result = 10;     // Field no: 10
    DeleteTestResult delete_test_result = 11; // Field no: 11
    GetTestsResult get_tests_result = 13;   // Field no: 13
    // ... other results ...
  }
}
```

---

## Test Tool Parameter/Result Schemas

### AddTestParams (line ~111711)

```protobuf
message AddTestParams {
  string relative_workspace_path = 1;  // File path to add test
  string test_name = 2;                // Name of the test
  string test_code = 3;                // Test code content
}
```

### AddTestResult (line ~111751)

```protobuf
message AddTestResult {
  repeated Feedback feedback = 1;  // Lint/validation feedback
}

message Feedback {
  string message = 1;
  string severity = 2;            // Error, warning, etc.
  int32 start_line_number = 3;
  int32 end_line_number = 4;
  repeated RelatedInformation related_information = 5;
}

message RelatedInformation {
  string message = 1;
  int32 start_line_number = 2;
  int32 end_line_number = 3;
  string relative_workspace_path = 4;
}
```

### RunTestParams (line ~111878)

```protobuf
message RunTestParams {
  string relative_workspace_path = 1;  // File containing test
  optional string test_name = 2;       // Specific test to run (optional)
}
```

### RunTestResult (line ~111914)

```protobuf
message RunTestResult {
  string result = 1;  // Test execution output
}
```

### GetTestsParams (line ~111944)

```protobuf
message GetTestsParams {
  string relative_workspace_path = 1;  // File to get tests from
}
```

### GetTestsResult (line ~111974)

```protobuf
message GetTestsResult {
  repeated Test tests = 1;  // List of tests in file
}

message Test {
  string name = 1;            // Test name
  repeated string lines = 2;  // Test code lines
}
```

### DeleteTestParams (line ~112041)

```protobuf
message DeleteTestParams {
  string relative_workspace_path = 1;  // File containing test
  optional string test_name = 2;       // Specific test to delete
}
```

### DeleteTestResult (line ~112077)

```protobuf
message DeleteTestResult {
  // Empty - success is implicit
}
```

---

## Why Test Tools Are Missing from ClientSideToolV2

### 1. Architectural Evolution

**BuiltinTool** represents an older architecture where:
- The server orchestrated test operations
- Tools were tightly coupled to specific IDE functionality
- Test management was a first-class tool category

**ClientSideToolV2** represents a modern architecture where:
- The client has more autonomy
- Test execution is handled through terminal commands (RUN_TERMINAL_COMMAND_V2)
- File editing handles test creation (EDIT_FILE, EDIT_FILE_V2)
- Lint tools provide feedback (READ_LINTS, FIX_LINTS)

### 2. Superseded by Generic Tools

The test-specific tools have been functionally replaced:

| BuiltinTool | ClientSideToolV2 Equivalent | Notes |
|-------------|----------------------------|-------|
| ADD_TEST | EDIT_FILE_V2 (38) | Tests added via file editing |
| RUN_TEST | RUN_TERMINAL_COMMAND_V2 (15) | Tests run via terminal |
| DELETE_TEST | EDIT_FILE_V2 (38) | Tests deleted via file editing |
| GET_TESTS | READ_FILE_V2 (40), SEARCH_SYMBOLS (23) | Tests discovered via reading/symbols |

### 3. Feature Flag Evidence

The codebase contains a `useLegacyTerminalTool` flag (line ~182286):
```javascript
useLegacyTerminalTool: !1,  // false by default
```

This suggests a pattern of deprecating legacy tool implementations in favor of more modern equivalents.

### 4. No Client Handler for Test Tools

Analysis shows that while the protobuf messages exist for test tools in BuiltinToolCall/BuiltinToolResult, there are:
- No switch/case handlers for ADD_TEST, RUN_TEST, DELETE_TEST, GET_TESTS in client code
- No tool execution functions mapped to these enum values
- The messages exist only for server-side protocol compatibility

### 5. BuiltinTool vs ClientSideToolV2 Usage Pattern

**BuiltinTool** is used in:
- `BuiltinToolCall` / `BuiltinToolResult` messages
- Server-to-client protocol for legacy features
- Not actively dispatched in current client code

**ClientSideToolV2** is used in:
- `ClientSideToolV2Call` / `ClientSideToolV2Result` messages
- Active tool loop in composer service (line ~484595)
- Real-time tool execution with streaming support

---

## Evidence of Non-Usage

### No Dispatch Code Found

Searching for `$Me.ADD_TEST`, `$Me.RUN_TEST`, `$Me.DELETE_TEST`, `$Me.GET_TESTS` (the minified BuiltinTool enum variable) yields no results in tool dispatch code.

In contrast, ClientSideToolV2 values like `vt.READ_SEMSEARCH_FILES`, `vt.RIPGREP_SEARCH` are actively used in switch statements for tool execution.

### Message Structures Present but Dormant

The protobuf message structures are defined and can be parsed, but:
- No client-side implementation creates AddTestParams, RunTestParams, etc.
- No client-side implementation handles AddTestResult, RunTestResult, etc.
- The messages exist for backwards compatibility with server protocols

---

## Key Observations

### 1. Server-Side Protocol Artifacts

The test tools appear to be artifacts of an earlier version where:
- The Cursor server would orchestrate test operations
- The client would execute and return results
- Test management was a specialized capability

### 2. Modern Approach: General-Purpose Tools

The current approach uses:
- **File Operations**: Tests are just code - use EDIT_FILE_V2
- **Terminal Commands**: Test execution is just a command - use RUN_TERMINAL_COMMAND_V2
- **Symbol Search**: Test discovery is just symbol lookup - use SEARCH_SYMBOLS
- **Lint Reading**: Test feedback is just diagnostics - use READ_LINTS

### 3. Reduced Complexity

By removing specialized test tools, Cursor:
- Simplifies the client-side tool dispatcher
- Avoids maintaining test framework-specific logic
- Lets the AI use general tools for test operations
- Reduces the attack surface for security

### 4. Agent Autonomy

With ClientSideToolV2, the AI agent has more flexibility:
- Can use any test framework the user prefers
- Can adapt to project-specific test patterns
- Doesn't need specialized tool support per framework

---

## Related Protobuf Message References

### testNames Message (line ~118103)

There's a separate `testNames` message type that may be related to test discovery:

```protobuf
message TestNamesMessage {
  repeated string test_names = 1;  // List of test names
}
```

This appears in a different context (possibly test result reporting) rather than active tool execution.

---

## Recommendations for Further Investigation

1. **Server Protocol Analysis**: The BuiltinToolCall/BuiltinToolResult messages are used in server communication. Investigating the gRPC service definitions might reveal if test tools are still server-side features.

2. **Historical Version Comparison**: Comparing with earlier Cursor versions (pre-2.0) might show when test tools were actively used.

3. **Feature Gating**: There may be feature flags that re-enable test tools for specific enterprise configurations.

---

## Summary

The test-related tools (ADD_TEST, RUN_TEST, DELETE_TEST, GET_TESTS) in BuiltinTool represent a **legacy capability** that has been **superseded** by the more flexible ClientSideToolV2 architecture. Rather than having specialized test tools, modern Cursor:

1. Uses EDIT_FILE for test creation/modification/deletion
2. Uses RUN_TERMINAL_COMMAND for test execution
3. Uses SEARCH_SYMBOLS and READ_FILE for test discovery
4. Uses READ_LINTS for test feedback

The protobuf messages remain for backwards compatibility with server protocols, but the client-side tool execution code does not implement handlers for these tools.

---

## Source References

- BuiltinTool enum: lines 104513-104574
- BuiltinToolCall message: lines 109554-109723
- BuiltinToolResult message: lines 109724-109887
- AddTestParams: lines 111711-111750
- AddTestResult: lines 111751-111877
- RunTestParams: lines 111878-111913
- RunTestResult: lines 111914-111943
- GetTestsParams: lines 111944-111973
- GetTestsResult: lines 111974-112040
- DeleteTestParams: lines 112041-112076
- DeleteTestResult: lines 112077-112101
- ClientSideToolV2 enum: lines 104365-104512
- Tool dispatch loop: lines 484583-484600+
