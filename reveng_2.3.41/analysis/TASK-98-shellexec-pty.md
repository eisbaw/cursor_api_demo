# TASK-98: ShellExecPseudoTerminal UI Integration Analysis

## Overview

The `ShellExecPseudoTerminal` class (obfuscated as `W2m`) provides a custom PTY implementation that bridges Cursor's shell execution service with VS Code's terminal UI. This is a read-only pseudo-terminal that displays AI-executed shell commands and their outputs while integrating with VS Code's shell integration protocol via OSC 633 escape sequences.

## Source Location

**File**: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
**Lines**: 1127550-1127675

## Class Definition

```javascript
// Obfuscated as W2m, extends Ve (Disposable base class)
var W2m = class extends Ve {
    constructor(i, e, t, n = "Cursor Shell", s = 80, r = 30, o = "/") {
        // Parameters:
        // i = _sessionId
        // e = _shellExecService
        // t = _terminalExecutionService
        // n = _name (default "Cursor Shell")
        // s = _cols (default 80)
        // r = _rows (default 30)
        // o = _cwd (default "/")

        this._sessionId = i;
        this._shellExecService = e;
        this._terminalExecutionService = t;
        this._name = n;
        this._cols = s;
        this._rows = r;
        this._cwd = o;

        // Instance properties
        this.id = 0;
        this.shouldPersist = false;
        this.isReadOnly = true;  // Critical: read-only terminal

        // Event emitters for VS Code terminal integration
        this._onProcessData = this._register(new Ce);
        this.onProcessData = this._onProcessData.event;
        this._onProcessReady = this._register(new Ce);
        this.onProcessReady = this._onProcessReady.event;
        this._onDidChangeProperty = this._register(new Ce);
        this.onDidChangeProperty = this._onDidChangeProperty.event;
        this._onProcessExit = this._register(new Ce);
        this.onProcessExit = this._onProcessExit.event;
        this._onReadOnlyInput = this._register(new Ce);
        this.onReadOnlyInput = this._onReadOnlyInput.event;

        // State flags
        this._isStarted = false;
        this._isExecutingCommand = false;
        this._isReplayingHistory = false;
    }
}
```

## OSC 633 Shell Integration Protocol

The class implements VS Code's shell integration protocol using OSC 633 escape sequences:

### Escape Sequence Generator

```javascript
_osc633(i, ...e) {
    // Generates: ESC ] 633 ; <command> ; <args...> BEL
    return `\x1B]633;${[i,...e].filter(n=>n!==void 0).join(";")}\x07`
}

_escapeOscValue(i) {
    // Escapes special characters in OSC values
    return i.replace(/\\/g, "\\\\")
            .replace(/;/g, "\\x3b")
            .replace(/[\x00-\x1f]/g, e => `\\x${e.charCodeAt(0).toString(16).padStart(2,"0")}`)
}
```

### Implemented OSC 633 Commands

| Command | Code | Purpose | Usage in ShellExecPseudoTerminal |
|---------|------|---------|----------------------------------|
| A | Prompt Start | Marks beginning of shell prompt | `_showPrompt()` |
| B | Command Start | Marks end of prompt, beginning of command input | `_showPrompt()` |
| C | Command Executed | Marks that command has started executing | `_showCommand()` |
| D | Command Finished | Reports exit code | `_showCommandCompleted(exitCode)` |
| E | Command Line | Sets the command text | `_showCommand()` |
| P | Property | Sets terminal properties | Cwd and HasRichCommandDetection |

### Shell Integration Initialization

On `start()`:
```javascript
// 1. Send current working directory property
this._emitImmediate(this._osc633("P", `Cwd=${this._escapeOscValue(this._cwd)}`));

// 2. Enable rich command detection
this._emitImmediate(this._osc633("P", "HasRichCommandDetection=True"));

// 3. Fire property change for VS Code
this._onDidChangeProperty.fire({ type: "initialCwd", value: this._cwd });
```

## Terminal Lifecycle

### Startup Flow

```javascript
async start() {
    if (this._isStarted) return;
    this._isStarted = true;

    // 1. Subscribe to shell exec events
    this._eventListener = this._shellExecService.onEvent(this._sessionId, e => {
        this._handleShellExecEvent(e)
    });

    // 2. Get session history
    const history = this._shellExecService.getSessionHistory(this._sessionId);

    // 3. Signal process ready (PID -1 indicates pseudo-terminal)
    this._onProcessReady.fire({
        pid: -1,
        cwd: this._cwd,
        windowsPty: undefined
    });

    // 4. Initialize shell integration
    this._emitImmediate(this._osc633("P", `Cwd=${...}`));
    this._emitImmediate(this._osc633("P", "HasRichCommandDetection=True"));

    // 5. Replay history if exists, else show prompt
    if (history) {
        await this._replayHistory(history);
    } else {
        this._showPrompt();
    }
}
```

### History Replay

The terminal can reconstruct its state from session history:

```javascript
// Session history structure from shellExecService:
{
    events: [],
    executions: [
        {
            command: string,
            cwd: string | undefined,
            startIndex: number,
            endIndex: number | undefined  // undefined = still running
        }
    ],
    cwd: string | undefined
}
```

History replay shows:
1. Previous commands with their outputs (if available via `getSessionCommandOutputs`)
2. Exit codes for completed commands
3. Current executing command (if any)

### Event Handling

```javascript
_handleShellExecEvent(event) {
    if (!this._isStarted || this._isReplayingHistory) return;

    if (event.type === "stdout" || event.type === "stderr") {
        const data = this._convertNewlines(event.data);
        this._onProcessData.fire(data);
    } else if (event.type === "exit") {
        this._showCommandCompleted(event.code);
        this._showPrompt();
        this._isExecutingCommand = false;
    }
}
```

## Read-Only Terminal Behavior

### Input Handling

The terminal is read-only but handles specific input:

```javascript
input(i) {
    if (i === "\x03") {  // Ctrl+C
        const history = this._shellExecService.getSessionHistory(this._sessionId);
        // If command is running (no endIndex), cancel it
        if (history?.executions.length > 0 &&
            history.executions[history.executions.length - 1].endIndex === undefined) {
            this._shellExecService.cancel(this._sessionId);
        } else {
            this._onReadOnlyInput.fire();  // Flash read-only warning
        }
        return;
    }
    this._onReadOnlyInput.fire();  // All other input triggers read-only warning
}
```

### Read-Only Detection in Terminal Instance

```javascript
// Lines 730475-730479
_isReadOnlyTerminal() {
    const hasCustomPty = this._shellLaunchConfig.customPtyImplementation !== undefined;
    const hasCursorName = this._shellLaunchConfig.name?.startsWith("Cursor (") === true
                       || this._shellLaunchConfig.name?.startsWith("Agent Terminal") === true;
    const hasInfinityIcon = this._shellLaunchConfig.icon === de.infinity;
    return hasCustomPty && (hasCursorName || hasInfinityIcon);
}
```

### Visual Feedback

When user attempts input on read-only terminal:
```javascript
// Lines 730711-730714
_flashReadOnlyTerminal() {
    if (this._wrapperElement) {
        this._wrapperElement.classList.remove("flash-read-only");
        this._wrapperElement.offsetWidth;  // Force reflow
        this._wrapperElement.classList.add("flash-read-only");
        this._readOnlyFlashTimeout = setTimeout(() => {
            this._wrapperElement?.classList.remove("flash-read-only");
        }, 300);
    }
}
```

## Terminal Creation

### Factory Function

```javascript
// Lines 1127677-1127682
function rPu(sessionId, shellExecService, terminalExecutionService, name, command, cwd) {
    return (instanceId, cols, rows) => {
        const pty = new W2m(sessionId, shellExecService, terminalExecutionService, name, cols, rows, cwd || "/");
        if (command) pty.setCommand(command);
        return pty;
    }
}
```

### Integration with VS Code Terminal Service

```javascript
// Lines 1128049-1128059 - Creating mirror terminal
const terminal = await this._terminalService.createTerminal({
    config: {
        name: `Cursor (${commandDescription})`,
        icon: de.infinity,
        isFeatureTerminal: false,
        isTransient: false,
        hideFromUser: false,
        strictEnv: false,
        customPtyImplementation: rPu(sessionId, this._shellExecService, this, name, command, cwd)
    }
});
```

## PseudoTerminal Registration System

### Registration with TerminalExecutionService

```javascript
// In constructor:
this._terminalExecutionService.registerPseudoTerminal?.(this._sessionId, this);

// In dispose:
this._terminalExecutionService.unregisterPseudoTerminal?.(this._sessionId, this);
```

### TerminalExecutionService Registry

```javascript
// Lines 1128078-1128088
registerPseudoTerminal(sessionId, pty) {
    if (!this._sessionPseudoTerminals.has(sessionId)) {
        this._sessionPseudoTerminals.set(sessionId, new Set());
    }
    this._sessionPseudoTerminals.get(sessionId).add(pty);
}

unregisterPseudoTerminal(sessionId, pty) {
    const ptys = this._sessionPseudoTerminals.get(sessionId);
    if (ptys) {
        ptys.delete(pty);
        if (ptys.size === 0) {
            this._sessionPseudoTerminals.delete(sessionId);
        }
    }
}

_notifyPseudoTerminalsCommandStart(sessionId, command) {
    const ptys = this._sessionPseudoTerminals.get(sessionId);
    if (ptys) {
        for (const pty of ptys) {
            pty.onCommandStart?.(command);
        }
    }
}
```

## Output Buffer Management

### oPu - Truncating Output Buffer

```javascript
// Lines 1127684-1127716
var oPu = class {
    constructor(scrollback) {
        this._buffer = "";
        this._totalBytesDropped = 0;
        const clampedScrollback = Math.min(10000, Math.max(100, scrollback));
        this._maxBufferSize = clampedScrollback * 100 * 2;  // ~200 bytes per line
    }

    append(data) {
        this._buffer += data;
        this._enforceLimit();
    }

    _enforceLimit() {
        const currentSize = this._buffer.length * 2;
        if (currentSize > this._maxBufferSize) {
            const excess = currentSize - this._maxBufferSize;
            const charsToRemove = Math.ceil(excess / 2);
            this._totalBytesDropped += charsToRemove * 2;
            this._buffer = this._buffer.substring(charsToRemove);
        }
    }

    getOutput() {
        if (this._totalBytesDropped > 0) {
            return `[Terminal output truncated: ~${Math.round(this._totalBytesDropped/1024)}KB dropped from beginning]\n${this._buffer}`;
        }
        return this._buffer;
    }
}
```

## VS Code Terminal API Compliance

### Required PseudoTerminal Interface Methods

| Method | Implementation |
|--------|---------------|
| `start()` | Initializes terminal, subscribes to events, replays history |
| `input(data)` | Handles Ctrl+C, fires read-only warning for other input |
| `shutdown(immediate)` | Cancels session, disposes after delay |
| `resize(cols, rows)` | No-op (output-only terminal) |
| `processBinary(data)` | No-op |
| `clearBuffer()` | No-op |
| `acknowledgeDataEvent(charCount)` | No-op |
| `setUnicodeVersion(version)` | No-op |
| `getInitialCwd()` | Returns stored cwd |
| `getCwd()` | Returns current cwd |
| `refreshProperty(property)` | Throws "not supported" error |
| `updateProperty(property, value)` | No-op |

### Custom Methods for Cursor Integration

| Method | Purpose |
|--------|---------|
| `setCommand(cmd)` | Sets current command for display |
| `onCommandStart(cmd)` | Callback when TerminalExecutionService starts command |

## Shell Integration Protocol Reference

### OSC 633 Sequence Format

```
ESC ] 633 ; <command> [ ; <arg1> [ ; <arg2> ... ] ] BEL
\x1B]633;<command>;<args>\x07
```

### Command Flow Example

```
1. _showPrompt():
   \x1B]633;A\x07          # Prompt start
   $
   \x1B]633;B\x07          # Command start

2. _showCommand("ls -la"):
   \x1B]633;E;ls -la\x07   # Set command line
   ls -la\r\n              # Display command
   \x1B]633;C\x07          # Command executed

3. [Output streams as onProcessData events]

4. _showCommandCompleted(0):
   \x1B]633;D;0\x07        # Command finished with exit code
```

### Property Commands

```
Cwd:                    \x1B]633;P;Cwd=<escaped-path>\x07
HasRichCommandDetection: \x1B]633;P;HasRichCommandDetection=True\x07
```

## Disposal

```javascript
dispose() {
    // 1. Unregister from terminal execution service
    this._terminalExecutionService.unregisterPseudoTerminal?.(this._sessionId, this);

    // 2. Cancel any running command
    this._shellExecService.cancel(this._sessionId).catch(() => {});

    // 3. Dispose session
    this._shellExecService.disposeSession(this._sessionId).catch(() => {});

    // 4. Clean up event listener
    this._eventListener?.dispose();

    // 5. Call base dispose
    super.dispose();
}
```

## Architecture Diagram

```
+-------------------+     +------------------------+     +------------------+
|  VS Code Terminal |     | ShellExecPseudoTerminal|     | ShellExecService |
|   Instance        |<--->|       (W2m)            |<--->|    (Backend)     |
+-------------------+     +------------------------+     +------------------+
        |                          |                            |
        | onProcessData            | _handleShellExecEvent      | onEvent
        | onProcessReady           | _showPrompt()              | execute()
        | onProcessExit            | _showCommand()             | cancel()
        | onDidChangeProperty      | _showCommandCompleted()    | getSessionHistory()
        | onReadOnlyInput          |                            |
        |                          |                            |
   +----v----+              +------v------+              +-------v-------+
   | xterm.js|              | OSC 633     |              | Node.js       |
   | renderer|              | Protocol    |              | child_process |
   +---------+              +-------------+              +---------------+
```

## Key Observations

1. **Read-Only Design**: The terminal is intentionally read-only to prevent users from interfering with AI-controlled shell sessions. Only Ctrl+C is handled to allow command cancellation.

2. **History Replay**: The terminal can reconstruct its display state from session history, enabling reconnection to ongoing sessions.

3. **Shell Integration**: Full implementation of VS Code's OSC 633 protocol enables rich command detection, including command boundaries, exit codes, and working directory tracking.

4. **Multiple PTY Support**: A single session can have multiple registered pseudo-terminals, all receiving command notifications.

5. **Buffer Truncation**: Output is truncated from the beginning when exceeding limits, with a header indicating truncation.

## Related Components

- **TerminalExecutionService V3** (`y3o`): Manages terminal sessions and executes commands
- **MainThreadShellExec** (`TKe`): IPC bridge to extension host shell execution
- **ComposerTerminalService**: Manages AI composer terminal instances
- **OutputBuffer** (`oPu`): Handles output truncation for long-running commands

## Investigation Avenues

1. **Shell execution sandbox integration** - How sandboxPolicy affects command execution
2. **Mirror terminal creation flow** - How "Open in External Terminal" creates mirror views
3. **History persistence** - Whether/how session history persists across editor restarts
4. **Ctrl+C signal propagation** - How cancel propagates through IPC to actual process
