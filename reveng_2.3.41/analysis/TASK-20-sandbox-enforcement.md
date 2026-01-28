# TASK-20: Sandbox Enforcement Mechanism for Terminal Execution

## Executive Summary

Cursor 2.3.41 implements a sandbox system for terminal command execution, but **the actual OS-level enforcement (landlock/seccomp on Linux, sandbox-exec on macOS) is NOT implemented in the JavaScript workbench code**. The JavaScript layer handles policy definition, merging, approval workflows, and UI - but the actual process-level sandboxing must be implemented in:

1. A native binary/addon in the Extension Host
2. The `anysphere.cursor-agent-exec` extension
3. A sidecar process

This analysis documents what CAN be determined from the JavaScript code and identifies the boundary where native enforcement takes over.

## Key Finding: No OS-Level Primitives Found

Exhaustive search for OS-level sandbox mechanisms returned no matches:

| Search Term | Results | Notes |
|-------------|---------|-------|
| `landlock` | 0 | Linux kernel filesystem sandbox |
| `seccomp` | 0 | Linux syscall filtering |
| `sandbox-exec` | 0 | macOS sandbox profiles |
| `bwrap` / `bubblewrap` | 0 | Linux user-namespace sandbox |
| `firejail` | 0 | Linux application sandbox |
| `AppContainer` | 0 | Windows sandbox technology |
| `Job Objects` | 0 | Windows process isolation |

**Conclusion**: OS-level sandbox enforcement is delegated to native code outside the JavaScript bundle.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Renderer / Main Thread                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  RunTerminalCommandHandler (vDs class)                               │   │
│  │  - Policy determination (xOh function)                               │   │
│  │  - Approval workflow                                                 │   │
│  │  - UI rendering                                                      │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │  MainThreadShellExec (TKe class)                                      │   │
│  │  - Session management                                                 │   │
│  │  - Policy conversion (Z4f function)                                   │   │
│  │  - Calls ExtHostShellExec.$execute()                                  │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │ IPC
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Extension Host Process                               │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │  ExtHostShellExec                                                     │   │
│  │  - $createSession(handle, options)                                    │   │
│  │  - $execute(handle, sessionId, command, options)                      │   │
│  │  - $cancel(handle, sessionId)                                         │   │
│  │  - $disposeSession(handle, sessionId)                                 │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │  anysphere.cursor-agent-exec Extension                                │   │
│  │  [NATIVE CODE - NOT IN JAVASCRIPT BUNDLE]                             │   │
│  │  - Process spawning with sandboxPolicy                                │   │
│  │  - Actual OS-level enforcement                                        │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Operating System Level                               │
│  ┌───────────────────┬────────────────────┬────────────────────────────┐   │
│  │      Linux        │       macOS        │         Windows            │   │
│  │  landlock?        │   sandbox-exec?    │    AppContainer?           │   │
│  │  seccomp?         │   App Sandbox?     │    Job Objects?            │   │
│  │  namespaces?      │   XPC?             │    ???                     │   │
│  │  [UNKNOWN]        │   [UNKNOWN]        │    [UNKNOWN]               │   │
│  └───────────────────┴────────────────────┴────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## SandboxPolicy Data Structure

### Protobuf Definition (agent.v1.SandboxPolicy)

Location: Lines 94183-94265 in `workbench.desktop.main.js`

```protobuf
message SandboxPolicy {
  Type type = 1;                                 // Policy type enum
  optional bool network_access = 2;              // Allow network access
  repeated string additional_readwrite_paths = 3; // Extra writable paths
  repeated string additional_readonly_paths = 4;  // Extra readable paths
  optional string debug_output_dir = 5;          // Debug output directory
  optional bool block_git_writes = 6;            // Block git write operations
  optional bool disable_tmp_write = 7;           // Disable /tmp writes
}

enum Type {
  TYPE_UNSPECIFIED = 0;       // Treated as unsandboxed
  TYPE_INSECURE_NONE = 1;     // No sandbox - full system access
  TYPE_WORKSPACE_READWRITE = 2; // Sandbox with workspace write access
  TYPE_WORKSPACE_READONLY = 3;  // Sandbox with read-only workspace
}
```

### JavaScript Enum (xk)

```javascript
xk = {
    UNSPECIFIED: 0,           // Default, treated as unsandboxed
    INSECURE_NONE: 1,         // TYPE_INSECURE_NONE - no sandbox
    WORKSPACE_READWRITE: 2,   // TYPE_WORKSPACE_READWRITE
    WORKSPACE_READONLY: 3     // TYPE_WORKSPACE_READONLY
}
```

## Sandbox Support Detection

### Service Version Requirement

Location: Lines 834962-834967, 1128639-1128643

**Sandboxing requires Terminal Execution Service V3**:

```javascript
_setEffectiveSandboxSupport(e) {
    const t = Rh(this._storageService, "sandboxSupported");
    const n = this._terminalExecutionService.getServiceVersion() === "v3";
    const s = e && n;  // Both raw support AND v3 required
    t.set(s, void 0);
}

// In ShadowWorkspaceServer:
_initializeSandboxSupportFlag() {
    const serviceVersion = this._getTerminalExecutionService().getServiceVersion();
    const supported = serviceVersion === "v3";
    this.storageService.store("sandboxSupported", supported);
}
```

The `sandboxSupported` flag is stored in persistent storage and checked before enabling sandbox features.

### Platform-Specific Gates

Location: Lines 479047-479070, 294001-294016

```javascript
async function EOh(experimentService, remoteAgentService) {
    // Check if sandbox settings should be visible
    if (!experimentService.checkFeatureGate("composer_sandbox_settings_visible")) {
        return false;
    }

    const os = (await remoteAgentService.getEnvironment())?.os ?? Dm;

    // os === 3 means Linux, os === 1 means Windows
    if (os === 3 && experimentService.checkFeatureGate("sandbox_force_disable_linux")) {
        return false;
    }
    if (os === 1 && experimentService.checkFeatureGate("sandbox_force_disable_win32")) {
        return false;
    }

    return true;
}
```

**Feature Flags**:
- `composer_sandbox_settings_visible`: Master toggle for sandbox UI
- `sandbox_force_disable_linux`: Force disable on Linux
- `sandbox_force_disable_win32`: Force disable on Windows
- Note: **macOS has no force-disable flag** - appears to always support sandboxing

## Policy Conversion for Extension Host

Location: Lines 835138-835160 (Z4f function)

Before sending to the Extension Host, the policy is converted:

```javascript
function Z4f(policy, logService) {
    if (!policy) {
        logService.debug("[_convertSandboxPolicy] No policy, returning undefined");
        return;
    }

    let ignoreMappingJson;
    if (policy.ignore_mapping) {
        try {
            ignoreMappingJson = JSON.stringify(policy.ignore_mapping);
        } catch (e) {
            logService.warn("[MainThreadShellExec] Failed to serialize ignore_mapping:", e);
        }
    }

    return {
        type: xk[policy.type],                    // String: "INSECURE_NONE", etc.
        networkAccess: policy.networkAccess,
        additionalReadwritePaths: policy.additionalReadwritePaths ?? [],
        additionalReadonlyPaths: policy.additionalReadonlyPaths ?? [],
        blockGitWrites: policy.blockGitWrites,
        ignoreMappingJson: ignoreMappingJson,     // JSON string
        debugOutputDir: policy.debugOutputDir
    };
}
```

This converted object is passed via IPC to `ExtHostShellExec.$execute()`.

## IPC Protocol

### Main Thread -> Extension Host

```javascript
// Create session
await this._extHostShellExec.$createSession(handle, options);

// Execute command with sandbox policy
await this._extHostShellExec.$execute(handle, sessionId, command, {
    timeout: options?.timeout,
    sandboxPolicy: {
        type: "WORKSPACE_READWRITE",
        networkAccess: false,
        blockGitWrites: true,
        additionalReadwritePaths: ["/workspace/path"],
        additionalReadonlyPaths: [],
        ignoreMappingJson: "{...}",
        debugOutputDir: "/debug/output"
    }
});

// Cancel
await this._extHostShellExec.$cancel(handle, sessionId);

// Dispose
await this._extHostShellExec.$disposeSession(handle, sessionId);
```

### Extension Host -> Main Thread (Events)

```javascript
// Streaming events
$acceptEvent(handle, sessionId, event);

// event types:
{ type: "stdout", data: string }
{ type: "stderr", data: string }
{ type: "exit", code: number | null }
```

## Model Support Flag

Some AI models declare sandbox support:

Location: Lines 534880-535025

```javascript
// In AvailableModel protobuf message
message AvailableModel {
    string name = 1;
    bool default_on = 2;
    // ... other fields ...
    optional bool supports_sandboxing = 17;  // Field no. 17
}
```

This allows the server to indicate which models can work with sandboxed execution.

## Security Level Hierarchy

Location: Line 479222

```javascript
dBe = {
    SandboxReadonly: 0,        // Most restrictive
    SandboxReadonlyNetwork: 5,
    SandboxNoNetwork: 10,
    SandboxNetwork: 20,
    Unsandboxed: 30            // Least restrictive
}
```

When merging policies, the system takes the MORE restrictive option (lower number wins).

## CursorIgnore Integration

Location: Lines 1128664-1128673

The `.cursorignore` file patterns are attached to the sandbox policy:

```javascript
enrichPolicyWithCursorIgnore(policy) {
    if (!policy || policy.type === xk.INSECURE_NONE) return policy;

    try {
        const ignoreMapping = this.cursorIgnoreService.getSerializableIgnoreMapping();
        policy.ignore_mapping = ignoreMapping;
    } catch (e) {
        this.logService.warn("Failed to attach cursorignore mapping", e);
    }
    return policy;
}
```

This ensures the native sandbox layer can respect `.cursorignore` patterns.

## Admin/Enterprise Controls

Location: Lines 269097-269105, 276616-276640

```javascript
// SandboxingMode enum (aiserver.v1)
Tke = {
    UNSPECIFIED: 0,  // SANDBOXING_MODE_UNSPECIFIED
    ENABLED: 1,      // SANDBOXING_MODE_ENABLED
    DISABLED: 2      // SANDBOXING_MODE_DISABLED
}

// AutoRunSandboxingControls (aiserver.v1)
{
    sandboxing: Tke,              // ENABLED/DISABLED/UNSPECIFIED
    sandboxNetworking: P2e,       // USER_CONTROLLED/ALWAYS_DISABLED
    sandboxGit: L2e               // USER_CONTROLLED/ALWAYS_DISABLED
}
```

Admin controls can:
- Force-enable sandboxing for all users
- Force-disable network access in sandbox
- Force-disable git write operations in sandbox

## Storage Keys

User-configurable sandbox settings:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `sandboxSupported` | boolean | false | Whether sandbox is supported on system |
| `sandboxNetworkDefault` | "ask"\|"enabled"\|"disabled" | "ask" | Default network access setting |
| `sandboxAllowGitWrites` | boolean | false | Allow git writes in sandbox |
| `sandboxingSeen` | boolean | false | User has seen sandbox promo |
| `sandboxPromoVersionSeen` | number | 0 | Version of promo seen |
| `sandboxDebugOutputDir` | string | "" | Debug output directory |

## Key Code Locations

| Component | Lines | Description |
|-----------|-------|-------------|
| SandboxPolicy protobuf | 94183-94265 | Policy message definition |
| Policy type enum (xk) | 94251-94265 | UNSPECIFIED, INSECURE_NONE, etc. |
| SandboxingMode enum | 269097-269105 | Admin control enum |
| AutoRunSandboxingControls | 276614-276640 | Admin sandbox settings |
| Feature flag definitions | 294001-294016 | sandbox_force_disable_* |
| Platform gate (EOh) | 479047-479070 | OS-specific checks |
| Policy conversion (Z4f) | 835138-835160 | Convert to IPC format |
| MainThreadShellExec | 834917-835066 | IPC to Extension Host |
| TerminalExecutionService3 | 1127717-1128100 | Service that sends policy |
| ShadowWorkspaceServer | 1128621-1129260 | Shadow workspace enforcement |
| Extension ID | 1134770, 1135147 | anysphere.cursor-agent-exec |

## What We Know About the Native Layer

1. **Extension ID**: `anysphere.cursor-agent-exec` handles shell execution
2. **Role Code 2**: The extension has role code 2 in the extension classification system
3. **Service Version**: Must be "v3" for sandbox support
4. **IPC Interface**: ExtHostShellExec receives the sandboxPolicy via IPC
5. **Policy Fields**: The native layer receives type, paths, network, git, and ignore mapping

## Open Questions

1. **Where is the native sandbox binary?**
   - Not in the JavaScript bundle
   - Likely in Cursor's resources folder or bundled with the extension

2. **What OS primitives are used?**
   - Linux: landlock? seccomp? namespaces? bwrap?
   - macOS: sandbox-exec profiles? App Sandbox? XPC?
   - Windows: AppContainer? Job Objects? Integrity levels?

3. **How are paths enforced?**
   - additionalReadwritePaths and additionalReadonlyPaths
   - How does the native layer map these to OS restrictions?

4. **How is network access blocked?**
   - Does it use seccomp to block socket syscalls?
   - Does it use network namespaces?

5. **How are git writes blocked?**
   - File-level blocking of .git directory writes?
   - Process-level blocking of git commands?

## Recommendations for Further Investigation

1. **Examine Cursor application package**:
   - Look for native binaries in resources/
   - Look for .node addons
   - Examine cursor-agent-exec extension contents

2. **Process tracing**:
   - Use `strace` (Linux) or `dtruss` (macOS) on sandboxed commands
   - Observe what syscalls are made/blocked

3. **Network analysis**:
   - Test network access in sandboxed vs unsandboxed mode
   - Verify network blocking works

4. **File access testing**:
   - Create test files outside workspace
   - Verify read/write restrictions work

5. **ExtHostShellExec analysis**:
   - The Extension Host code may be in a separate bundle
   - May need to decompile extension host worker code

## Conclusion

The Cursor IDE implements a sophisticated sandbox policy system at the JavaScript/IPC level, but **the actual OS-level enforcement mechanism remains opaque**. The JavaScript code prepares and transmits sandbox policies, but enforcement happens in native code within the Extension Host or a sidecar process.

The system supports:
- Four policy levels (none, read-only, read-write, unrestricted)
- Network access control
- Git write blocking
- Additional path whitelisting
- CursorIgnore integration
- Admin/enterprise controls

However, without access to the native binary/extension code, we cannot verify:
- What OS primitives are actually used
- How effective the sandboxing actually is
- Whether there are bypass vulnerabilities

The fact that sandbox support requires "v3" of the terminal execution service suggests this is a relatively new feature that may still be evolving.
