# TASK-21: Terminal Execution Service Version Analysis

## Executive Summary

Cursor IDE 2.3.41 implements three distinct terminal execution service versions (v1, v2, v3) with a proxy pattern that dynamically selects between them. The `VSCODE_TERMINAL_EXECUTION_SERVICE_VERSION` environment variable provides a direct override mechanism, primarily used for testing and debugging. The version selection has significant implications for sandbox support and AI terminal functionality.

## Environment Variable Check

**Location:** Line 1128637 in `workbench.desktop.main.js`

```javascript
_getTerminalExecutionService() {
    return q3.env.VSCODE_TERMINAL_EXECUTION_SERVICE_VERSION === "v3"
        ? this.terminalExecutionServiceV3
        : this.terminalExecutionServiceV2
}
```

This check exists in the `ShadowWorkspaceServer` class (`uIe`), which handles terminal execution for shadow workspace operations. It provides a direct bypass of the normal version selection logic.

## Service Architecture

### Service Registration

Each service version is registered as a separate dependency injection service:

| Service | Service ID | Class | Line |
|---------|-----------|-------|------|
| v1 | `terminalExecutionServiceV1` | `p8o` | 1165397 |
| v2 | `terminalExecutionServiceV2` | `w3o` | 1128612 |
| v3 | `terminalExecutionServiceV3` | `y3o` | 1128095 |

### Proxy Pattern

The `TerminalExecutionServiceProxy` class (`y8o`, line 1165398) provides dynamic version selection based on:
1. Cached v3 health check result
2. Feature gates (`terminal_execution_service_2`, `terminal_ide_shell_exec`)
3. User settings (`useLegacyTerminalTool`)

```javascript
// Version selection priority (line 1165406):
l === !0 ? (this._delegate = v3)
  : d ? (this._delegate = v2)
  : (this._delegate = v1)
```

Where:
- `l` = cached v3 health check passed
- `d` = `terminal_execution_service_2` feature gate enabled

## Version Comparison

### V1: TerminalExecutionService1 (p8o)

**Characteristics:**
- Original implementation using VS Code's terminal service directly
- Uses `_aiService.aiClient().isTerminalFinishedV2()` for AI-based command completion detection
- Creates terminals via `_terminalService.createTerminal()`
- Direct xterm buffer access for output reading
- No sandbox support
- Supports shell integration detection

**Key Methods:**
- `executeStream()` - Polls terminal output with AI completion detection
- `_waitForPromptReady()` - Waits for shell prompt using capability detection
- `_isTerminalFinished()` - Calls AI service to determine if command is complete

**Dependencies:**
```javascript
__param(0, op),           // terminalService
__param(1, Vf),           // aiServerConfigService
__param(2, Tv),           // aiService
__param(3, gG),           // terminalProfileService
__param(4, Xj),           // environmentService
__param(5, Df),           // remoteAgentService
__param(6, nu),           // configurationService
__param(7, uje),          // composerTerminalService
__param(8, L0),           // aiServerConfigService
__param(9, Yo)            // composerDataService
```

### V2: TerminalExecutionService2 (w3o)

**Characteristics:**
- Enhanced version with warm terminal pooling
- Uses `$2m` class (`TerminalFactory`) for terminal creation
- Pre-creates terminals for faster session starts
- Shell integration with fallback to manual script sourcing
- Still uses VS Code terminal directly
- No sandbox support
- Supports `leakSession()` for background terminal detachment

**Key Methods:**
- `startSession()` - Uses warm terminal from pool
- `executeStream()` - Similar to v1 with AI hang detection
- `_terminalFactory.createNewTerminal()` - Gets pre-warmed terminal
- `leakSession()` - Detaches terminal for background execution

**Terminal Factory Features:**
- Warm terminal pre-creation with shell integration
- Supported shells: bash, fish, zsh, pwsh, git bash
- Automatic shell integration script sourcing
- 2-minute re-determination of shell path

**Dependencies:**
```javascript
__param(0, op),           // terminalService
__param(1, Tv),           // aiService
__param(2, gG),           // terminalProfileService
__param(3, Xj),           // environmentService
__param(4, Df),           // remoteAgentService
__param(5, uje),          // composerTerminalService
__param(6, L0),           // aiServerConfigService
__param(7, Bh),           // analyticsService
__param(8, yc),           // experimentService
__param(9, lE),           // metricsService
__param(10, jt)           // configurationService
```

### V3: TerminalExecutionService3 (y3o)

**Characteristics:**
- Uses `shellExecService` for command execution (extension host IPC)
- Creates pseudo-terminals (`ShellExecPseudoTerminal`) with OSC 633 sequences
- Supports mirror terminals for UI visualization
- **Enables sandbox support** - only v3 allows sandboxing
- Output buffering with truncation for large outputs
- Lazy placeholder terminals for performance

**Key Methods:**
- `startSession()` - Creates session via shellExecService
- `executeStream()` - Executes through IPC with sandbox policy support
- `createMirrorTerminal()` - Creates UI terminal mirroring shellExec session
- `registerPseudoTerminal()` / `unregisterPseudoTerminal()` - Manages PTY tracking

**Unique Features:**

1. **Pseudo-Terminal Implementation:**
   - Uses OSC 633 escape sequences for shell integration
   - Simulates VS Code terminal shell integration without actual shell
   - Commands: A (prompt start), B (prompt end), C (command start), D (command end), E (command line), P (property)

2. **Mirror Terminals:**
   - Creates visual terminals that mirror shellExec sessions
   - Replays command history when opened
   - Supports late-opening of background terminals

3. **Output Buffering:**
   - `oPu` class manages output with size limits
   - Maximum buffer size based on line count (default 10000 lines * 100 chars * 2 bytes)
   - Truncation with byte count reporting

4. **Sandbox Support:**
   - Only v3 enables `sandboxSupported` storage flag
   - Passes `sandboxPolicy` to shellExecService for execution

**Dependencies:**
```javascript
__param(0, op),           // terminalService
__param(1, $Kt),          // shellExecService
__param(2, uje),          // composerTerminalService
__param(3, jt),           // configurationService
__param(4, WC),           // historyService
__param(5, Df),           // remoteAgentService
__param(6, Xj),           // environmentService
__param(7, jU),           // terminalInstanceService
__param(8, z7),           // terminalProfileResolverService
__param(9, Yo),           // composerDataService
__param(10, Xn)           // logService
```

## Sandbox Support Connection

The critical link between v3 and sandbox support:

**Line 1128639-1128643:**
```javascript
_initializeSandboxSupportFlag() {
    const e = this._getTerminalExecutionService().getServiceVersion(),
        t = e === "v3";
    Rh(this.storageService, "sandboxSupported").set(t, void 0, void 0)
}
```

**Line 834962-834966 (MainThreadShellExec):**
```javascript
_setEffectiveSandboxSupport(e) {
    const t = Rh(this._storageService, "sandboxSupported"),
        n = this._terminalExecutionService.getServiceVersion() === "v3",
        s = e && n;  // Both raw support AND v3 required
    t.set(s, void 0)
}
```

**Implication:** Sandbox mode is ONLY enabled when:
1. The extension host reports `sandboxSupported: true`
2. AND the terminal execution service is v3

## Feature Gates

Two feature gates control version selection:

### `terminal_execution_service_2` (Line 293613)
- Client-side gate
- Default: false
- When enabled: Falls back to v2 if v3 health check fails

### `terminal_ide_shell_exec` (Line 293737)
- Client-side gate
- Default: false
- Required for v3 initialization
- Controls whether v3 is even attempted

## Version Selection Logic

From `_updateDelegateBasedOnSettings()` (Line 1165530-1165536):

```javascript
const e = useLegacyTerminalTool,
    t = checkFeatureGate("terminal_ide_shell_exec"),
    n = checkFeatureGate("terminal_execution_service_2");
let s;
e || !t ? s = n ? "v2" : "v1" : s = "v3";
```

**Decision tree:**
1. If `useLegacyTerminalTool` OR `terminal_ide_shell_exec` is disabled:
   - Use v2 if `terminal_execution_service_2` enabled
   - Otherwise use v1
2. If `terminal_ide_shell_exec` enabled AND not using legacy tool:
   - Attempt v3 with health check

## V3 Health Check

The health check (Lines 1165461-1165526) validates v3 functionality:

1. Creates a shell session via `_shellExecService.createSession()`
2. Executes `echo test` command
3. Waits for stdout/stderr output AND exit event
4. Timeout: 45 seconds for full check
5. Results cached in storage as `terminalExecutionServiceV3HealthCheckResult`

**Cached states:** "untested", "passed", "failed"

If cached result is "passed", v3 is used immediately without re-running health check.

## Session Leak Behavior

Important difference for background command execution:

**Line 479745:**
```javascript
this.terminalExecutionService.getServiceVersion() !== "v3"
    && this.terminalExecutionService.leakSession(E)
```

V2 and v1 require explicit session leaking for background commands to persist. V3 handles this differently through the shellExecService model.

## Storage Keys

| Key | Scope | Purpose |
|-----|-------|---------|
| `sandboxSupported` | Application | Whether sandbox mode is available |
| `terminalExecutionServiceV3HealthCheckResult` | Application | Cached health check result |
| `useLegacyTerminalTool` | User | Force legacy (v2) terminal behavior |

## Summary of Key Differences

| Feature | V1 | V2 | V3 |
|---------|----|----|-----|
| Terminal Creation | Direct | Warm Pool | ShellExec IPC |
| AI Completion Detection | Yes | Yes | Via shellExec events |
| Shell Integration | Capability-based | Script sourcing fallback | OSC 633 emulation |
| Sandbox Support | No | No | **Yes** |
| Mirror Terminals | No | No | **Yes** |
| Output Buffering | xterm direct | xterm direct | Custom buffer |
| Session Leaking | Yes | Yes | Not needed |
| Health Check | N/A | N/A | Required |

## Why VSCODE_TERMINAL_EXECUTION_SERVICE_VERSION Exists

The environment variable serves several purposes:

1. **Testing/Debugging:** Allows forcing v3 in shadow workspace without normal proxy selection
2. **Development:** Enables testing sandbox features before feature gates are enabled
3. **Emergency Override:** Bypasses health checks and feature gates if needed
4. **Shadow Workspace Isolation:** Shadow workspaces use direct version selection rather than the proxy pattern

The check is specifically in `ShadowWorkspaceServer` because shadow workspaces need deterministic terminal behavior for sandbox enforcement, and the normal proxy's dynamic switching could cause issues during shadow workspace operations.

## Related Investigation Areas

1. **ShellExecService IPC Protocol:** How commands are executed through the extension host
2. **Sandbox Policy Enforcement:** How v3's sandbox policies are actually enforced
3. **OSC 633 Implementation:** Full details of the shell integration emulation
4. **Extension Host Communication:** The `ExtHostShellExec` protocol
