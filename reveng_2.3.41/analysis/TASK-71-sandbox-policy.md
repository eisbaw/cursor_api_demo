# TASK-71: SandboxPolicy Schema and Enforcement for Terminal Commands

## Overview

This document provides a detailed analysis of the SandboxPolicy schema and how policies are applied to terminal commands in Cursor. The sandbox system uses a combination of protobuf-defined policies, user settings, admin controls, and allowlists to determine whether commands should run automatically, require approval, or execute within a sandbox environment.

## SandboxPolicy Protobuf Schema

### Type Definition
Location: Line ~94186-94265 in `workbench.desktop.main.js`

The `SandboxPolicy` message is defined in the `agent.v1` protobuf package:

```protobuf
message SandboxPolicy {
  Type type = 1;                                // Policy type enum
  optional bool network_access = 2;              // Allow network access
  repeated string additional_readwrite_paths = 3; // Extra writable paths
  repeated string additional_readonly_paths = 4;  // Extra readable paths
  optional string debug_output_dir = 5;          // Debug output directory
  optional bool block_git_writes = 6;            // Block git write operations
  optional bool disable_tmp_write = 7;           // Disable /tmp writes
}

enum Type {
  TYPE_UNSPECIFIED = 0;       // Unspecified (treated as unsandboxed)
  TYPE_INSECURE_NONE = 1;     // No sandbox (full system access)
  TYPE_WORKSPACE_READWRITE = 2; // Sandbox with workspace write access
  TYPE_WORKSPACE_READONLY = 3;  // Sandbox with read-only workspace
}
```

### JavaScript Class Implementation
```javascript
// Internal class name: lsi (obfuscated), referenced via xk enum
class SandboxPolicy {
    constructor(e) {
        this.type = xk.UNSPECIFIED;
        this.additionalReadwritePaths = [];
        this.additionalReadonlyPaths = [];
        // Optional: networkAccess, blockGitWrites, disableTmpWrite, ignore_mapping, debugOutputDir
    }
}
```

### Policy Type Enum (`xk`)
```javascript
xk = {
    UNSPECIFIED: 0,       // Default, treated as unsandboxed
    INSECURE_NONE: 1,     // No sandbox - full access
    WORKSPACE_READWRITE: 2, // Sandboxed with write to workspace
    WORKSPACE_READONLY: 3   // Sandboxed with read-only workspace
}
```

## Security Level Hierarchy (`dBe` enum)

Location: Line ~479222

The system defines a numeric security level scale used for policy comparison:

```javascript
dBe = {
    SandboxReadonly: 0,        // Most restrictive
    SandboxReadonlyNetwork: 5,
    SandboxNoNetwork: 10,
    SandboxNetwork: 20,
    Unsandboxed: 30            // Least restrictive
}
```

Lower numbers = more restrictive. The `H4c` function merges policies by selecting the MORE restrictive option.

## Policy Determination Flow

### 1. Auto-Run Mode Detection
Location: Line ~927465-927554

Three auto-run modes exist:
```javascript
DT = {
    ASK_EVERY_TIME: "ask_every_time",  // Always prompt user
    USE_ALLOWLIST: "use_allowlist",    // Run if on allowlist, otherwise ask
    RUN_EVERYTHING: "run_everything"   // Run all commands without approval
}
```

Mode is determined by:
```javascript
// isAutoRun = user enabled auto-run for agent mode
// isFullAutoRun = user enabled "run everything" mode
if (isAutoRun) {
    return isFullAutoRun ? DT.RUN_EVERYTHING : DT.USE_ALLOWLIST;
}
return DT.ASK_EVERY_TIME;
```

### 2. Approval Settings Object (fN function)

Location: Line ~305931-305943

For non-admin-controlled environments:
```javascript
{
    isAdminControlled: false,
    isDisabledByAdmin: false,
    browserFeatures: true,
    allowedCommands: composerState.yoloCommandAllowlist ?? [],    // User's allowlist
    blockedCommands: composerState.yoloCommandDenylist ?? [],     // User's blocklist
    deleteFileProtection: composerState.yoloDeleteFileDisabled ?? false,
    dotFilesProtection: composerState.yoloDotFilesDisabled ?? true,
    outsideWorkspaceProtection: composerState.yoloOutsideWorkspaceDisabled ?? true,
    enableRunEverything: composerState.yoloEnableRunEverything ?? false,
    mcpAllowedTools: composerState.mcpAllowedTools ?? [],
    mcpToolsProtection: composerState.yoloMcpToolsDisabled ?? true,
    playwrightProtection: false
}
```

For admin-controlled environments (Line ~306001-306014):
- Uses server-side `autoRunControls` configuration
- Can force disable run-everything mode
- Has separate MCP tool allowlist controls

### 3. Command Matching Function (`$Jt`)

Location: Line ~479088

```javascript
function $Jt(commandText, pattern) {
    // Escapes special regex characters in pattern
    const escaped = pattern.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    // Matches if command STARTS with pattern followed by whitespace or end
    return new RegExp(`^${escaped}(\\s|$)`).test(commandText.trim());
}
```

Examples:
- `$Jt("rm -rf /", "rm")` returns `true`
- `$Jt("rmdir foo", "rm")` returns `false` (doesn't start with "rm ")
- `$Jt("git push", "git")` returns `true`

## Main Policy Determination Function (`xOh`)

Location: Line ~479097-479179

This is the core function that determines whether a command needs user approval:

```javascript
function xOh(parsingResult, approvalSettings, composerHandle, compositeCommands, safeCommands, sandboxOptions) {
    // 1. Merge user policy with requested policy (take more restrictive)
    const effectivePolicy = H4c(sandboxOptions.userPolicy, sandboxOptions.requestedPolicy);

    // 2. If admin disabled auto-run, always require approval
    if (approvalSettings.isDisabledByAdmin) {
        return { needApproval: true, effectivePolicy };
    }

    // 3. If parsing failed, check run-everything mode
    if (parsingResult === undefined || parsingResult.parsingFailed) {
        if (composerHandle.shouldAutoRun_runEverythingMode() &&
            approvalSettings.blockedCommands.length === 0) {
            return { needApproval: false, effectivePolicy };
        }
        return { needApproval: true, effectivePolicy };
    }

    // 4. Check against blocklist
    for (const cmd of parsingResult.executableCommands) {
        if (approvalSettings.blockedCommands.some(b => $Jt(cmd.fullText, b))) {
            return { needApproval: true, effectivePolicy };
        }
    }

    // 5. If no commands parsed, similar to parse failure
    if (parsingResult.executableCommands.length === 0) {
        // ... similar logic to step 3
    }

    // 6. Run-everything mode bypasses further checks
    if (composerHandle.shouldAutoRun_runEverythingMode() &&
        (!approvalSettings.isAdminControlled || approvalSettings.enableRunEverything)) {
        return { needApproval: false, effectivePolicy };
    }

    // 7. Special protection for 'rm' commands
    for (const cmd of parsingResult.executableCommands) {
        if ($Jt(cmd.fullText, "rm") &&
            approvalSettings.deleteFileProtection &&
            !approvalSettings.allowedCommands.some(a => $Jt(a, "rm"))) {
            return { needApproval: true, effectivePolicy };
        }
    }

    // 8. Always block 'sudo' commands
    for (const cmd of parsingResult.executableCommands) {
        if ($Jt(cmd.fullText, "sudo")) {
            return { needApproval: true, effectivePolicy };
        }
    }

    // 9. Without sandbox, empty allowlist requires approval
    if (!sandboxOptions.sandboxEnabled && approvalSettings.allowedCommands.length === 0) {
        return {
            needApproval: true,
            candidatesForAllowlist: qJt(parsingResult.executableCommands, compositeCommands),
            effectivePolicy
        };
    }

    // 10. Filter commands not in allowlist
    const combined = [...approvalSettings.allowedCommands, ...safeCommands];
    const notAllowed = parsingResult.executableCommands.filter(
        cmd => !combined.some(a => $Jt(cmd.fullText, a))
    );

    // 11. All commands allowed - no approval needed
    if (notAllowed.length === 0) {
        return {
            needApproval: false,
            candidatesForAllowlist: qJt(parsingResult.executableCommands, compositeCommands),
            effectivePolicy
        };
    }

    // 12. With sandbox enabled, check policy restrictions
    if (sandboxOptions.sandboxEnabled) {
        // ... git write access checks, policy level comparisons
        // If sandbox policy is acceptable, may skip approval
    }

    // 13. Default: require approval
    return {
        needApproval: true,
        candidatesForAllowlist: approvalSettings.isAdminControlled ? undefined : candidates,
        effectivePolicy
    };
}
```

## Policy Merging (`H4c` Function)

Location: Line ~479196-479201

```javascript
function H4c(userPolicy, requestedPolicy) {
    if (!requestedPolicy) return userPolicy;

    const userLevel = gDs(userPolicy);      // Get numeric security level
    const requestedLevel = gDs(requestedPolicy);

    // Return the MORE restrictive policy (lower number = more restrictive)
    return userLevel > requestedLevel ? userPolicy : requestedPolicy;
}
```

## Security Level Calculation (`gDs` Function)

Location: Line ~479182-479194

```javascript
function gDs(policy) {
    if (!policy) return dBe.Unsandboxed;  // 30

    switch (policy.type) {
        case xk.INSECURE_NONE:
            return dBe.Unsandboxed;        // 30
        case xk.WORKSPACE_READWRITE:
            return policy.networkAccess
                ? dBe.SandboxNetwork        // 20
                : dBe.SandboxNoNetwork;     // 10
        case xk.UNSPECIFIED:
            return dBe.Unsandboxed;        // 30
        default:
            return dBe.Unsandboxed;        // 30
    }
}
```

Note: `WORKSPACE_READONLY` is not explicitly handled and falls through to `Unsandboxed`, which appears to be a potential bug or the readonly mode is handled differently.

## Workspace Path Enhancement (`addWorkspaceFoldersToPolicy`)

Location: Line ~479233-479251, Line ~1128648-1128663

When sandbox is enabled with `WORKSPACE_READWRITE`, all workspace folders are added to the allowed paths:

```javascript
addWorkspaceFoldersToPolicy(policy) {
    if (policy.type !== xk.WORKSPACE_READWRITE) return policy;

    const folders = this.workspaceContextService.getWorkspace().folders;
    if (folders.length <= 1) return policy;  // Single folder already included

    const existingPaths = policy.additionalReadwritePaths ?? [];
    const workspacePaths = folders.map(f => f.uri.fsPath);
    const combined = [...new Set([...existingPaths, ...workspacePaths])];

    return new SandboxPolicy({
        type: policy.type,
        networkAccess: policy.networkAccess,
        additionalReadwritePaths: combined,
        additionalReadonlyPaths: policy.additionalReadonlyPaths,
        blockGitWrites: policy.blockGitWrites,
        debugOutputDir: policy.debugOutputDir
    });
}
```

## CursorIgnore Integration

Location: Line ~1128664-1128673, Line ~479516-479519

The `.cursorignore` file patterns are attached to the sandbox policy:

```javascript
enrichPolicyWithCursorIgnore(policy) {
    if (!policy || policy.type === xk.INSECURE_NONE) return policy;

    try {
        const ignoreMapping = this.cursorIgnoreService.getSerializableIgnoreMapping();
        policy.ignore_mapping = ignoreMapping;
    } catch (e) {
        this.logService.warn("Failed to attach cursorignore mapping to sandbox policy", e);
    }
    return policy;
}
```

This ensures the sandbox respects `.cursorignore` patterns even at the OS-level enforcement layer.

## Hooks Integration

Location: Line ~479337-479403

Before terminal execution, a hook can intervene:

```javascript
const hookResult = await this.cursorHooksService.executeHookForStep(
    Eb.beforeShellExecution,
    {
        conversation_id: composerData?.composerId ?? "",
        generation_id: composerData?.latestChatGenerationUUID ?? "",
        model: composerData?.modelConfig?.modelName ?? "",
        command: params?.command ?? "UNKNOWN",
        cwd: params?.cwd ?? "",
        sandbox: sandboxEnabled
    }
);

const permission = hookResult?.permission ?? "allow";

if (permission === "deny") {
    throw new Error("Command execution was blocked by a hook");
} else if (permission === "ask") {
    // Force approval requirement
}
```

## Server-Side Configuration

### `runTerminalServerConfig` Structure

Location: Line ~827706-827714, Line ~479348-479350

```javascript
runTerminalServerConfig = {
    compositeShellCommands: [],  // Commands that should show with arguments
    safeShellCommands: []        // Commands pre-approved by server
}
```

These server-defined safe commands are combined with user allowlists during policy evaluation.

## Policy Conversion for Extension Host

Location: Line ~835138-835160

Before sending to the native sandbox layer, the policy is converted:

```javascript
function Z4f(policy, logService) {
    if (!policy) return undefined;

    let ignoreMappingJson;
    if (policy.ignore_mapping) {
        try {
            ignoreMappingJson = JSON.stringify(policy.ignore_mapping);
        } catch (e) {
            logService.warn("Failed to serialize ignore_mapping");
        }
    }

    return {
        type: xk[policy.type],  // String: "INSECURE_NONE", "WORKSPACE_READWRITE", etc.
        networkAccess: policy.networkAccess,
        additionalReadwritePaths: policy.additionalReadwritePaths ?? [],
        additionalReadonlyPaths: policy.additionalReadonlyPaths ?? [],
        blockGitWrites: policy.blockGitWrites,
        ignoreMappingJson: ignoreMappingJson,
        debugOutputDir: policy.debugOutputDir
    };
}
```

## Complete Enforcement Flow

```
1. User/Agent Requests Command Execution
                |
                v
2. Parse Command (extract executable commands)
                |
                v
3. Load Approval Settings
   - Admin controls from server
   - User allowlist/blocklist from storage
   - Protection flags (rm, sudo, dotfiles, etc.)
                |
                v
4. Determine Auto-Run Mode
   - ASK_EVERY_TIME: Always prompt
   - USE_ALLOWLIST: Check allowlist first
   - RUN_EVERYTHING: Skip most checks
                |
                v
5. Execute Hook (beforeShellExecution)
   - Hook can DENY or force ASK
                |
                v
6. Evaluate Policy (xOh function)
   - Check blocklist
   - Check special commands (rm, sudo)
   - Check allowlist
   - Check sandbox settings
   - Merge requested + user policies
                |
                v
7. If Approval Needed -> Show UI Dialog
   - User can: Accept, Reject, Add to Allowlist
                |
                v
8. Enrich Policy
   - Add workspace folders to paths
   - Attach .cursorignore mapping
                |
                v
9. Convert Policy for Extension Host (Z4f)
                |
                v
10. Execute via TerminalExecutionService3
    - Pass sandboxPolicy to shellExecService
                |
                v
11. Native Sandbox Enforcement
    - (Outside JavaScript scope)
```

## Key Configuration Locations in Beautified Code

| Component | Line Number |
|-----------|-------------|
| SandboxPolicy protobuf fields | 94196-94237 |
| SandboxPolicy.Type enum | 94251-94265 |
| Security level enum (dBe) | 479221-479222 |
| Command matching ($Jt) | 479088-479091 |
| Policy determination (xOh) | 479097-479179 |
| Security level calc (gDs) | 479182-479194 |
| Policy merging (H4c) | 479196-479201 |
| Workspace path enrichment | 479233-479251 |
| RunTerminalCommandHandler | 479325-479520 |
| Policy conversion (Z4f) | 835138-835160 |
| Shadow workspace policy | 1128648-1128673 |

## Related Tasks for Deeper Investigation

Consider creating tasks for:
1. Native sandbox binary analysis (locate actual OS-level enforcement code)
2. CursorIgnore service analysis (how patterns are compiled and passed)
3. Hook system analysis (beforeShellExecution integration points)
4. Terminal Execution Service V3 analysis (the actual command execution layer)

## Summary

The SandboxPolicy system provides a flexible, multi-layered approach to terminal command security:

1. **Policy Types**: Four levels from no sandbox to read-only workspace
2. **Policy Merging**: Always takes the more restrictive option
3. **Allowlist/Blocklist**: User and admin-controlled command filtering
4. **Special Protections**: Built-in guards for `rm`, `sudo`, dotfiles, and out-of-workspace paths
5. **Hook Integration**: External hooks can block or force approval
6. **Server Configuration**: Server-defined safe commands supplement user allowlists
7. **CursorIgnore**: File patterns are attached to sandbox policies for consistent enforcement

The JavaScript layer handles policy decisions and UI, while actual OS-level sandboxing is delegated to native code in the Extension Host.
