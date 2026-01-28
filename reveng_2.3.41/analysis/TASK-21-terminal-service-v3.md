# Terminal Execution Service Versioning Analysis (TASK-21)

## Overview

Cursor implements three versions of terminal execution services (v1, v2, v3) that provide progressively more sophisticated terminal interaction capabilities. The version selection is controlled by feature flags, health checks, and user preferences.

## Version Architecture

### TerminalExecutionServiceProxy (y8o)
Location: Line ~1165398

The proxy class manages version selection at runtime:
- Initializes with cached v3 health check result or falls back to v1/v2
- Monitors `useLegacyTerminalTool` user setting
- Listens for experiment flag changes
- Performs health checks before switching to v3

### Version Selection Logic

```
if (useLegacyTerminalTool) -> v2 (forced legacy)
else if (terminal_ide_shell_exec flag && v3 health check passes) -> v3
else if (terminal_execution_service_2 flag) -> v2
else -> v1
```

## Version Differences

### TerminalExecutionService v1 (p8o)
Location: Line ~1165000-1165396
Service ID: `v8o` / `terminalExecutionServiceV1`

**Characteristics:**
- Basic terminal execution using `sendText()` directly to terminal instances
- Relies on xterm buffer scraping for output capture
- Uses command detection capability (`capabilities.get(2)`) when available
- Output captured via polling terminal buffer with `_getTerminalFullContent()`
- Session management via simple Map of terminal instances
- Timeout-based command completion detection
- AI-based hang detection optional (`aiCheckForHangs`)

**Limitations:**
- No sandbox support
- Output capture depends on xterm buffer state
- Less reliable command completion detection
- No session history persistence

### TerminalExecutionService v2 (w3o)
Location: Line ~1128400-1128610
Service ID: `LVs` / `terminalExecutionServiceV2`

**Characteristics:**
- Similar to v1 but with improved terminal factory usage
- Uses `_terminalFactory` for creating warm terminals
- Better prompt detection with `waitForPromptReady()`
- Supports AI hang detection with metrics tracking
- Creates persistent and background AI terminals
- Session priming concept (`primed: true/false`)
- `getServiceVersion()` returns "v2"

**Improvements over v1:**
- More reliable terminal creation via factory pattern
- Better handling of Ctrl+C before command execution
- Metrics tracking for AI hang detection usage

### TerminalExecutionService v3 (y3o)
Location: Line ~1127700-1128093
Service ID: `Gei` / `terminalExecutionServiceV3`

**Characteristics:**
- Uses `shellExecService` (an IPC service via extension host) for command execution
- Full sandbox policy support
- Session-based architecture with explicit session IDs from shell exec backend
- Mirror terminal support (`createMirrorTerminal()`)
- Pseudo-terminal (PTY) implementation via `ShellExecPseudoTerminal` class
- Event-driven output streaming via `shellExecService.onEvent()`
- Session history persistence (`getSessionHistory()`)
- Output buffering with `oPu` class (limited scrollback buffer)
- `getServiceVersion()` returns "v3"

**Key Capabilities:**
1. **Sandbox Support**: Full integration with sandbox policies
   - `INSECURE_NONE` - No sandboxing
   - `WORKSPACE_READWRITE` - Sandbox with workspace read/write
   - `WORKSPACE_READONLY` - Sandbox with workspace read-only
   - Additional options: `blockGitWrites`, `networkAccess`, `additionalReadwritePaths`

2. **Shell Exec Service Integration**:
   - `createSession({cwd})` - Create new shell session
   - `execute(sessionId, command, {interactive, sandboxPolicy})` - Execute command
   - `cancel(sessionId)` - Cancel running execution
   - `disposeSession(sessionId)` - Clean up session
   - `getSessionHistory(sessionId)` - Get execution history
   - `onEvent(sessionId, callback)` - Stream stdout/stderr/exit events

3. **Mirror Terminal**: User-visible terminal that mirrors hidden AI terminal output
   - Implemented via `ShellExecPseudoTerminal` (W2m class)
   - Supports OSC 633 escape sequences for rich command detection
   - Replays session history when opened

4. **Output Management**:
   - Per-session output buffers with configurable scrollback
   - Command output history (`_sessionCommandOutputs`)
   - Adaptive throttling based on output volume

## Environment Variable

`VSCODE_TERMINAL_EXECUTION_SERVICE_VERSION` can force v3 selection in shadow workspace context (Line 1128637):
```javascript
return q3.env.VSCODE_TERMINAL_EXECUTION_SERVICE_VERSION === "v3"
    ? this.terminalExecutionServiceV3
    : this.terminalExecutionServiceV2
```

## Health Check Mechanism

V3 requires a health check before activation (Line ~1165461-1165483):

1. Create session with retry (up to 10 attempts, exponential backoff)
2. Execute `echo test` command
3. Wait for stdout output and exit code
4. Cache result in storage (`terminalExecutionServiceV3HealthCheckResult`)
5. Timeout: 45 seconds total

## Feature Flags

| Flag | Purpose |
|------|---------|
| `terminal_ide_shell_exec` | Enable v3 shell exec backend |
| `terminal_execution_service_2` | Enable v2 as fallback when v3 disabled |
| `terminal_ui_2` | Related UI improvements (separate from execution) |

## Storage Keys

| Key | Purpose |
|-----|---------|
| `sandboxSupported` | Boolean indicating if sandboxing is available |
| `terminalExecutionServiceV3HealthCheckResult` | Cached v3 health check (passed/failed/untested) |
| `useLegacyTerminalTool` | User preference to force v2 |

## Metrics Tracking

The proxy tracks version switches and health check outcomes:
- `terminal_execution_service.ai_hang_detection` - Hang detection usage
- `terminal_execution_service.switched_to_v3` - Successful v3 switch
- `terminal_execution_service.v3_health_check_failed` - Failed health check
- `terminal_execution_service.v3_fallback` - Fallback from v3
- `terminal_execution_service.forced_legacy` - User forced v2

## Why Version Check Exists

1. **Reliability**: v3 depends on extension host IPC which may fail to initialize
2. **Compatibility**: Not all environments support the shell exec backend
3. **Gradual Rollout**: Feature flags allow controlled v3 deployment
4. **User Control**: `useLegacyTerminalTool` gives users escape hatch
5. **Remote Support**: Different backends may be needed for local vs remote workspaces

## Sandbox Support (v3 Only)

The `sandboxSupported` flag is only set to true when:
1. Shell exec service reports sandbox capability
2. **AND** terminal execution service is v3

This means sandbox policies (workspace restrictions, git write blocking, network access control) are only enforced with v3.

## Key Files/Lines Reference

- Proxy class: Line 1165398
- V1 class: Line ~1165000
- V2 class: Line ~1128400
- V3 class: Line ~1127700
- ShellExecPseudoTerminal: Line ~1127550
- MainThreadShellExec: Line ~834915
- Sandbox policy proto: Line ~221726
- Feature flags: Line ~293613

## Related Tasks for Deeper Investigation

- Shell exec IPC protocol details (extension host communication)
- Sandbox implementation in shell exec backend
- Mirror terminal OSC 633 escape sequences
- Session history persistence mechanism
