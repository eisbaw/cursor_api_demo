# TASK-30: Shell Exec IPC Protocol Analysis

## Overview

The Cursor IDE implements a custom shell execution system that operates via IPC between the Main Thread and Extension Host. This is distinct from the standard VS Code terminal service and provides enhanced capabilities for AI-driven code execution including sandboxing, background execution, and streaming output.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Main Thread                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  MainThreadShellExec (TKe class)                                     │   │
│  │  - Registered via xp(eg.MainThreadShellExec)                         │   │
│  │  - Service ID: "shellExecService" ($Kt)                              │   │
│  │                                                                       │   │
│  │  Methods:                                                             │   │
│  │  - createSession(options?)                                            │   │
│  │  - execute(sessionId, command, options)                               │   │
│  │  - cancel(sessionId)                                                  │   │
│  │  - disposeSession(sessionId)                                          │   │
│  │  - getSessionHistory(sessionId)                                       │   │
│  │                                                                       │   │
│  │  Events from ExtHost:                                                 │   │
│  │  - $acceptEvent(handle, sessionId, event)                             │   │
│  │  - $updateShellExecCapabilities(capabilities)                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │  IPC (Proxy)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Extension Host                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ExtHostShellExec (qg.ExtHostShellExec)                              │   │
│  │                                                                       │   │
│  │  Methods (called by Main):                                            │   │
│  │  - $createSession(handle, options?)                                   │   │
│  │  - $execute(handle, sessionId, command, options)                      │   │
│  │  - $cancel(handle, sessionId)                                         │   │
│  │  - $disposeSession(handle, sessionId)                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Proxy Identifiers

Located around line 779355-779427:

```javascript
// Main Thread Identifiers (eg object)
MainThreadShellExec: Hc("MainThreadShellExec")

// Extension Host Identifiers (qg object)
ExtHostShellExec: Hc("ExtHostShellExec")
```

The `Hc()` function creates proxy identifiers for IPC communication between main and extension host.

## IPC Message Protocol

### Session Lifecycle

#### 1. Create Session
```
Main -> ExtHost: $createSession(handle: number, options?: SessionOptions)
Returns: sessionId: string
```

Session options include workspace context and remote authority configuration.

#### 2. Execute Command
```
Main -> ExtHost: $execute(handle: number, sessionId: string, command: string, options?: ExecuteOptions)
```

Execute options:
```typescript
interface ExecuteOptions {
    timeout?: number;
    sandboxPolicy?: {
        type: string;          // SandboxPolicy type name
        networkAccess?: boolean;
        blockGitWrites?: boolean;
        additionalReadwritePaths?: string[];
        additionalReadonlyPaths?: string[];
        ignoreMappingJson?: string;
        debugOutputDir?: string;
    };
}
```

#### 3. Event Streaming
```
ExtHost -> Main: $acceptEvent(handle: number, sessionId: string, event: ShellEvent)
```

Event types:
```typescript
type ShellEvent =
    | { type: "stdout"; data: string }
    | { type: "stderr"; data: string }
    | { type: "exit"; code: number | null };
```

#### 4. Cancel Execution
```
Main -> ExtHost: $cancel(handle: number, sessionId: string)
```

#### 5. Dispose Session
```
Main -> ExtHost: $disposeSession(handle: number, sessionId: string)
```

## Protobuf Message Schemas

Located in `out-build/proto/agent/v1/shell_exec_pb.js` (lines 94269-95186):

### SandboxPolicy (agent.v1.SandboxPolicy)
```protobuf
enum SandboxPolicy.Type {
    TYPE_UNSPECIFIED = 0;
    TYPE_INSECURE_NONE = 1;
    TYPE_WORKSPACE_READWRITE = 2;
    TYPE_WORKSPACE_READONLY = 3;
}

message SandboxPolicy {
    Type type = 1;
    optional bool network_access = 2;
    repeated string additional_readwrite_paths = 3;
    repeated string additional_readonly_paths = 4;
    optional string debug_output_dir = 5;
    optional bool block_git_writes = 6;
    optional bool disable_tmp_write = 7;
}
```

### ShellArgs (agent.v1.ShellArgs)
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

### ShellResult (agent.v1.ShellResult)
```protobuf
message ShellResult {
    oneof result {
        ShellSuccess success = 1;
        ShellFailure failure = 2;
        ShellTimeout timeout = 3;
        ShellRejected rejected = 4;
        ShellSpawnError spawn_error = 5;
        ShellPermissionDenied permission_denied = 7;
    }
    optional SandboxPolicy sandbox_policy = 101;
    optional bool is_background = 102;
    optional string terminals_folder = 103;
}
```

### ShellSuccess (agent.v1.ShellSuccess)
```protobuf
message ShellSuccess {
    string command = 1;
    string working_directory = 2;
    int32 exit_code = 3;
    string signal = 4;
    string stdout = 5;
    string stderr = 6;
    int32 execution_time = 7;
    optional OutputLocation output_location = 8;
    optional uint32 shell_id = 9;
    optional string interleaved_output = 10;
}
```

### ShellFailure (agent.v1.ShellFailure)
```protobuf
message ShellFailure {
    string command = 1;
    string working_directory = 2;
    int32 exit_code = 3;
    string signal = 4;
    string stdout = 5;
    string stderr = 6;
    int32 execution_time = 7;
    optional OutputLocation output_location = 8;
    optional string interleaved_output = 9;
    optional ShellAbortReason abort_reason = 10;
    bool aborted = 11;
}
```

### ShellStream (agent.v1.ShellStream)
```protobuf
message ShellStream {
    oneof event {
        ShellStreamStdout stdout = 1;
        ShellStreamStderr stderr = 2;
        ShellStreamExit exit = 3;
        ShellStreamStart start = 4;
        ShellRejected rejected = 5;
        ShellPermissionDenied permission_denied = 6;
    }
}

message ShellStreamStdout { string data = 1; }
message ShellStreamStderr { string data = 1; }
message ShellStreamExit {
    uint32 code = 1;
    string cwd = 2;
    optional OutputLocation output_location = 3;
    bool aborted = 4;
    optional ShellAbortReason abort_reason = 5;
}
message ShellStreamStart {
    optional SandboxPolicy sandbox_policy = 1;
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

## Background Shell Execution

Located in `out-build/proto/agent/v1/background_shell_exec_pb.js` (lines 95188-95400+):

### BackgroundShellSpawnArgs (agent.v1.BackgroundShellSpawnArgs)
```protobuf
message BackgroundShellSpawnArgs {
    string command = 1;
    string working_directory = 2;
    string tool_call_id = 3;
    ShellCommandParsingResult parsing_result = 4;
    optional SandboxPolicy sandbox_policy = 5;
    bool enable_write_shell_stdin_tool = 6;
}
```

### BackgroundShellSpawnResult (agent.v1.BackgroundShellSpawnResult)
```protobuf
message BackgroundShellSpawnResult {
    oneof result {
        BackgroundShellSpawnSuccess success = 1;
        BackgroundShellSpawnError error = 2;
        ShellRejected rejected = 3;
        ShellPermissionDenied permission_denied = 4;
    }
}

message BackgroundShellSpawnSuccess {
    uint32 shell_id = 1;
    string command = 2;
    string working_directory = 3;
}

message BackgroundShellSpawnError {
    string command = 1;
    string working_directory = 2;
    string error = 3;
}
```

### WriteShellStdinArgs (agent.v1.WriteShellStdinArgs)
```protobuf
message WriteShellStdinArgs {
    uint32 shell_id = 1;
    string chars = 2;
}
```

## Terminal Shell Integration (Separate System)

In addition to the ShellExec IPC, there's also MainThreadTerminalShellIntegration (line 797845+):

```javascript
// Events sent to ExtHost
this._proxy.$shellExecutionStart(instanceId, command, confidence, isTrusted, cwdUri)
this._proxy.$shellExecutionData(instanceId, data)
this._proxy.$shellExecutionEnd(instanceId, command, confidence, isTrusted, exitCode)
this._proxy.$closeTerminal(instanceId)
this._proxy.$shellIntegrationChange(instanceId)
this._proxy.$cwdChange(instanceId, cwdUri)
```

## Key Implementation Details

### MainThreadShellExec Class (lines 834917-835066)

1. **Instance Management**: Uses static `_instances` Map keyed by host kind (1=Local, 2=Worker, 3=Remote)
2. **Handle Pool**: Uses incrementing `_handlePool` for unique operation IDs
3. **Session State**: Maintains `_sessionEmitters` (Map<string, Emitter>) and `_sessionExecutions` (Map<string, Execution[]>)
4. **Sandbox Support**: Tracks `_rawSandboxSupported` based on terminal service version

### Event Processing (lines 834968-834991)
```javascript
_processEvent(sessionId, event) {
    // Validates emitter exists for session
    // Transforms events into normalized format:
    // - stdout/stderr: { type, data }
    // - exit: { type: "exit", code }
    // Updates execution endIndex on exit
    // Fires event on session emitter
}
```

### Sandbox Policy Conversion (lines 835138-835160)
```javascript
function Z4f(policy, logger) {
    // Converts SandboxPolicy enum types to string names
    // Serializes ignore_mapping to JSON
    // Returns: {
    //   type: string (e.g., "WORKSPACE_READWRITE"),
    //   networkAccess: boolean,
    //   additionalReadwritePaths: string[],
    //   additionalReadonlyPaths: string[],
    //   blockGitWrites: boolean,
    //   ignoreMappingJson: string,
    //   debugOutputDir: string
    // }
}
```

## Service Registration

The shell exec service is registered at line 835161:
```javascript
Rn($Kt, ibo, 0);
// $Kt = on("shellExecService")
// ibo = ShellExecService wrapper class
```

The wrapper class (ibo, lines 835067-835135) provides:
- Automatic routing between local and remote extension hosts
- Session-to-host mapping via `_sessionHost` Map
- Preference for remote host when available

## Hook System Integration

Shell execution integrates with the cursor hooks system (lines 466699-466735):

```javascript
// Hook steps
Eb.beforeShellExecution: xro  // validator
Eb.afterShellExecution: nBc   // validator

// Execution (line 479337)
await this.cursorHooksService.executeHookForStep(Eb.beforeShellExecution, {
    command: ...,
    requestedSandboxPolicy: ...
})

// After execution (line 479947)
await this.cursorHooksService.executeHookForStep(Eb.afterShellExecution, {
    effectiveSandboxPolicy: ...
})
```

## Source Locations

| Component | File | Lines |
|-----------|------|-------|
| Proxy Identifiers | workbench.desktop.main.js | 779355, 779427 |
| MainThreadShellExec | workbench.desktop.main.js | 834917-835066 |
| ShellExec Service Wrapper | workbench.desktop.main.js | 835067-835135 |
| SandboxPolicy Conversion | workbench.desktop.main.js | 835138-835160 |
| Shell Exec Protobuf | workbench.desktop.main.js | 94269-95186 |
| Background Shell Protobuf | workbench.desktop.main.js | 95188-95400+ |
| Terminal Shell Integration | workbench.desktop.main.js | 797840-797890 |
| Hook Validators | workbench.desktop.main.js | 466699-466735 |
| ShellExecPseudoTerminal | workbench.desktop.main.js | 1127552-1127673 |
| TerminalExecutionService3 | workbench.desktop.main.js | 1127719-1128060 |

## Related Tasks

- TASK-20: Sandbox Enforcement - Details on how sandbox policies are enforced
- TASK-21: Terminal Service V3 - The underlying terminal service implementation
- TASK-25: Agent V1 Schemas - Complete protobuf schema documentation

## Open Questions

1. **ExtHost Implementation Location**: The ExtHostShellExec implementation is not in the workbench.desktop.main.js file - it's likely in a separate extension host bundle
2. **Actual Process Spawning**: How does the extension host actually spawn and manage shell processes?
3. **Sandbox Enforcement Mechanism**: How is the SandboxPolicy actually enforced at the process level?
4. **Remote Execution**: How does shell execution work when connected to a remote server?

## Potential Follow-up Investigations

1. Analyze ExtHostShellExec implementation (likely in extension host worker bundle)
2. Investigate how SandboxPolicy maps to actual filesystem/network restrictions
3. Document the hook validator schemas (xro, nBc)
4. Analyze the pseudo-terminal implementation for terminal UI integration
