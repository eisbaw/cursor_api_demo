# TASK-96: Shell Execution Hook Validators (xro, nBc)

## Overview

This document analyzes the shell execution hook validators in Cursor IDE 2.3.41. The `xro` and `nBc` functions are response validators for `beforeShellExecution` and `afterShellExecution` hooks respectively. These hooks are part of a broader hooks system that allows enterprise/team/user/project-level customization of command execution behavior.

## Source Files

- **Validators Location**: `out-build/vs/base/common/hooks/validators/`
  - `beforeCommandExecutionHookResponse.js` (line 466598-466611)
  - `afterShellExecutionResponse.js` (line 466698-466705)
  - `baseHookResponse.js` (line 466589-466597)
  - `base.js` (line 466580-466587)
- **Hook Types**: `out-build/vs/base/common/hooks/types.js` (line 466716-466756)
- **Hook Service**: Cursor Hooks Service (line 964242-964792)

## Validator Architecture

### Base Validation Functions (line 466580-466587)

```javascript
jOc = i => typeof i == "string"
AJt = i => i !== null && typeof i == "object" && !Array.isArray(i)
DG = (i, e = []) => ({
    isValid: i,
    errors: e
})
```

- `jOc`: String type validator
- `AJt`: Object type validator (non-null, non-array objects)
- `DG`: Creates validation result objects with `isValid` boolean and `errors` array

### Base Hook Response Validator - Qre (line 466589-466597)

```javascript
Qre = i => {
    const e = [];
    return AJt(i) ? DG(!0) : (e.push("Expected an object"), DG(!1, e))
}
```

All hook response validators extend this base validator, which simply verifies the response is a non-null object.

### xro - Before Shell Execution Validator (line 466598-466611)

**Purpose**: Validates responses from `beforeShellExecution` and `beforeMCPExecution` hooks.

```javascript
xro = i => {
    const e = [],
        t = Qre(i);  // Base validation first
    if (!t.isValid) return t;

    // Validate permission field
    if (i.permission !== void 0) {
        const n = ["allow", "deny", "ask"];
        n.includes(i.permission) || e.push(`Invalid permission value. Expected one of: ${n.join(", ")}, or undefined`)
    }

    // Validate optional string fields
    i.user_message !== void 0 && typeof i.user_message != "string" &&
        e.push("Invalid user_message value. Expected a string if provided")
    i.agent_message !== void 0 && typeof i.agent_message != "string" &&
        e.push("Invalid agent_message value. Expected a string if provided")

    return DG(e.length === 0, e)
}
```

**Valid Response Fields**:
| Field | Type | Required | Values |
|-------|------|----------|--------|
| `permission` | string | No | `"allow"`, `"deny"`, `"ask"`, or undefined |
| `user_message` | string | No | Custom message shown to user |
| `agent_message` | string | No | Message visible to the AI model |

### nBc - After Shell Execution Validator (line 466698-466705)

**Purpose**: Validates responses from `afterShellExecution` hooks.

```javascript
nBc = i => {
    const e = Qre(i);
    return e.isValid, e  // Just base object validation
}
```

**Key Observation**: The `afterShellExecution` validator is minimal - it only performs base object validation. This is because "after" hooks are observational/logging hooks that cannot modify the already-executed command.

## Hook Type Registry (line 466716-466755)

### Available Hook Types (Eb enum)

```javascript
Eb = {
    beforeShellExecution: "beforeShellExecution",
    beforeMCPExecution: "beforeMCPExecution",
    afterShellExecution: "afterShellExecution",
    afterMCPExecution: "afterMCPExecution",
    beforeReadFile: "beforeReadFile",
    afterFileEdit: "afterFileEdit",
    beforeTabFileRead: "beforeTabFileRead",
    afterTabFileEdit: "afterTabFileEdit",
    stop: "stop",
    beforeSubmitPrompt: "beforeSubmitPrompt",
    afterAgentResponse: "afterAgentResponse",
    afterAgentThought: "afterAgentThought"
}
```

### Validator Mapping (rBc)

```javascript
rBc = {
    [Eb.beforeShellExecution]: xro,      // Allow/Deny/Ask + messages
    [Eb.beforeMCPExecution]: xro,         // Same validator for MCP
    [Eb.afterShellExecution]: nBc,        // Minimal validation
    [Eb.afterMCPExecution]: iBc,          // Minimal validation
    [Eb.beforeReadFile]: KOc,             // Allow/Deny permission
    [Eb.afterFileEdit]: YOc,              // Minimal validation
    [Eb.beforeTabFileRead]: XOc,          // Allow/Deny permission
    [Eb.afterTabFileEdit]: QOc,           // Minimal validation
    [Eb.beforeSubmitPrompt]: ZOc,         // continue + user_message
    [Eb.stop]: eBc,                       // followup_message
    [Eb.afterAgentResponse]: tBc,         // Minimal validation
    [Eb.afterAgentThought]: sBc           // Minimal validation
}
```

### Master Validation Function (oBc)

```javascript
oBc = (i, e) => {
    const t = rBc[i],     // Get validator for hook type
        n = t(e);          // Execute validator
    return n.isValid ? {
        success: !0,
        data: e
    } : {
        success: !1,
        errors: n.errors
    }
}
```

## Command Blocking Flow

### Before Shell Execution (line 479337-479409)

When a shell command is about to be executed:

1. **Hook Invocation**:
```javascript
const B = await this.cursorHooksService.executeHookForStep(Eb.beforeShellExecution, {
    conversation_id: a?.composerId ?? "",
    generation_id: a?.latestChatGenerationUUID ?? "",
    model: a?.modelConfig?.modelName ?? "",
    command: e?.command ?? "UNKNOWN",
    cwd: e?.cwd ?? "",
    sandbox: P
})
```

2. **Permission Handling**:
```javascript
const H = B?.permission ?? "allow";  // Default to allow if no response

if (H === "deny") {
    console.log("[RunTerminalCommand] DENIED by hook permission");
    const ce = B?.user_message ? `: ${B.user_message}` : "",
        ae = B?.agent_message ? `: ${B.agent_message}` : "";
    throw new Lc({
        clientVisibleErrorMessage: `Command execution was blocked by a hook${ce}`,
        modelVisibleErrorMessage: `The terminal command was rejected by a hook that prevents execution of this command${ae}. Do not attempt to work around this restriction using alternative methods or commands.`,
        actualErrorMessage: "REJECTED_BY_HOOK"
    })
} else if (H === "ask" || J.needApproval) {
    G = {
        needApproval: !0,
        candidatesForAllowlist: J.candidatesForAllowlist
    }
} else {
    G = {
        needApproval: !1,
        candidatesForAllowlist: J.candidatesForAllowlist
    }
}
```

### Permission States

| Permission | Behavior |
|------------|----------|
| `"allow"` (or undefined) | Command proceeds (may still need approval based on allowlist) |
| `"deny"` | Command is blocked with error message |
| `"ask"` | User approval is required before execution |

### Error Messages

When a hook denies command execution:
- **Client-visible**: `"Command execution was blocked by a hook: {user_message}"`
- **Model-visible**: `"The terminal command was rejected by a hook that prevents execution of this command: {agent_message}. Do not attempt to work around this restriction using alternative methods or commands."`

The model-visible message explicitly instructs the AI not to attempt workarounds.

## Hook Configuration

### Configuration Locations (line 964284-964299)

Hooks are loaded from four sources with this priority order:

1. **Enterprise Hooks** (highest priority):
   - macOS: `/Library/Application Support/Cursor/hooks.json`
   - Windows: `C:\ProgramData\Cursor\hooks.json`
   - Linux: `/etc/cursor/hooks.json`

2. **Team Hooks** (managed via dashboard):
   - Location: `~/.cursor/managed/team_{teamId}/hooks/`
   - Fetched from Cursor dashboard API

3. **Project Hooks**:
   - Location: `{workspace}/.cursor/hooks.json`
   - Requires workspace trust
   - Feature-gated: `hooks_ide_project_config`

4. **User Hooks**:
   - Location: `~/.cursor/hooks.json`

### Configuration Schema (line 964211-964241)

```javascript
// Hook script validation
Bam = i => {
    const e = [];
    return AJt(i) ? (jOc(i.command) || e.push("Hook script command must be a string"), DG(e.length === 0, e))
                  : (e.push("Hook script must be an object with a command property"), DG(!1, e))
}

// Config validation
Wam = i => {
    // Must be object with version number and hooks object
    if (typeof i.version != "number") e.push("Config version must be a number")
    if (!Number.isInteger(i.version) || i.version < 1) e.push("Config version must be a positive integer")
    if (!AJt(i.hooks)) return e.push("Config hooks must be an object")

    // Validate each hook type
    for (const [s, r] of Object.entries(n)) {
        if (!validHookTypes.includes(s)) {
            e.push(`Unknown hook type: ${s}. Valid types are: ${validHookTypes.join(", ")}`)
        }
        // Validate hook scripts array
    }
}
```

### Example hooks.json Structure

```json
{
  "version": 1,
  "hooks": {
    "beforeShellExecution": [
      { "command": "./scripts/validate-command.sh" }
    ],
    "afterShellExecution": [
      { "command": "./scripts/log-execution.sh" }
    ]
  }
}
```

## Hook Execution Flow (line 964616-964790)

### Execution Process

1. **Collect hooks** from all sources (enterprise, team, project, user)
2. **Prepare request payload** with hook metadata:
   ```javascript
   const s = {
       ...t,
       hook_event_name: e,
       cursor_version: this.productService.version,
       workspace_roots: this.workspaceContextService.getWorkspace().folders.map(a => a.uri.path),
       user_email: n
   }
   ```

3. **Execute each hook script**:
   - Create shell session
   - Encode payload as base64 JSON
   - Pipe to hook script via stdin
   - Windows: PowerShell base64 decode
   - Unix: `printf | base64 -d | command`

4. **Parse and validate response**:
   ```javascript
   const Z = JSON.parse(G),
       ee = oBc(e, Z)  // Validate with appropriate validator
   ```

5. **Return first valid response** (hooks executed in order, first valid response wins)

### Stop Hook Loop Protection (line 964631-964635)

```javascript
if (e === Eb.stop) {
    const l = s.loop_count;
    if (typeof l == "number" && l >= 5) {
        this.logger.logInfo(`Stop hook auto-loop limit reached (loop_count=${l}). Skipping stop hooks`);
        return {}
    }
}
```

Prevents infinite loops in stop hooks by limiting to 5 iterations.

## Integration with Sandbox Policy

### Sandbox Policy Types (line 94252)

```javascript
i[i.UNSPECIFIED = 0] = "UNSPECIFIED"
i[i.INSECURE_NONE = 1] = "INSECURE_NONE"
i[i.WORKSPACE_READWRITE = 2] = "WORKSPACE_READWRITE"
i[i.WORKSPACE_READONLY = 3] = "WORKSPACE_READONLY"
```

### Hook-Sandbox Interaction

The `beforeShellExecution` hook receives `sandbox: P` parameter indicating whether sandboxing is enabled. Hook scripts can use this to make context-aware decisions.

The `afterShellExecution` hook also receives `sandbox: Xe` where:
```javascript
Xe = r.effectivePolicy !== void 0 && r.effectivePolicy.type !== xk.INSECURE_NONE
```

## File Read Blocking Example

Similar pattern for file reads (line 483508-483521):

```javascript
if ((await this.cursorHooksService.executeHookForStep(Eb.beforeReadFile, {
    conversation_id: _?.composerId ?? "",
    generation_id: _?.latestChatGenerationUUID ?? "",
    model: _?.modelConfig?.modelName ?? "",
    content: w,
    file_path: d.fsPath,
    attachments: h.map(M => ({
        type: "rule",
        file_path: M.name
    }))
}))?.permission === "deny") throw new Lc({
    clientVisibleErrorMessage: "File reading was blocked by a security hook",
    modelVisibleErrorMessage: "The file read operation was rejected by a security hook that prevents reading of this file. Do not attempt to work around this restriction using alternative methods or commands.",
    actualErrorMessage: "REJECTED_BY_HOOK"
})
```

## Security Considerations

1. **Enterprise Priority**: Enterprise hooks run first and cannot be overridden by user/project hooks
2. **Workspace Trust**: Project hooks only run in trusted workspaces
3. **Clear Error Messages**: Both user and AI receive explicit rejection messages
4. **Anti-Workaround Messaging**: Model-visible errors explicitly instruct AI not to bypass restrictions
5. **Loop Protection**: Stop hooks have built-in loop count limiting

## Summary

The `xro` and `nBc` validators are part of Cursor's extensible hooks system that allows organizations to enforce security policies on shell command execution:

- **xro (beforeShellExecution)**: Validates pre-execution hook responses, supporting `allow`/`deny`/`ask` permissions with custom messages
- **nBc (afterShellExecution)**: Minimal validator for post-execution observational hooks

This system integrates with sandbox policies, workspace trust, and enterprise configuration to provide a layered security model for AI-driven command execution.

---

## Related Tasks

- TASK-71: Sandbox policy analysis
- TASK-20: Sandbox enforcement mechanisms
- TASK-30: Shell exec IPC

## Line References

| Component | Lines |
|-----------|-------|
| Base validators (DG, AJt, jOc) | 466580-466587 |
| Base hook response (Qre) | 466589-466597 |
| xro validator | 466598-466611 |
| nBc validator | 466698-466705 |
| Hook types (Eb) | 466719-466731 |
| Validator mapping (rBc, oBc) | 466732-466755 |
| Hook service class | 964242-964792 |
| Config validation (Wam) | 964224-964241 |
| Hook execution | 964616-964790 |
| Command blocking logic | 479337-479409 |
| File read blocking | 483508-483521 |
