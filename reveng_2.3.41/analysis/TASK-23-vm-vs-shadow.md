# TASK-23: VmDaemonService vs ShadowWorkspaceService Selection Logic

Analysis of when Cursor uses remote VM execution vs local shadow window for AI agent operations.

## Executive Summary

Cursor implements two distinct execution environments for AI agent operations:

1. **ShadowWorkspaceService** - A local hidden VS Code window for isolated code operations
2. **VmDaemonService / BackgroundComposer Pods** - Cloud-based VMs for persistent async tasks

The selection between these modes is **not automatic** based on project characteristics. Instead, it's determined by:
- User privacy settings (primary factor)
- Explicit user selection of "background" (cloud) mode
- Whether the user is in a background agent window
- A user-controlled setting for local shadow workspace

## Key Finding: Two Independent Systems

The investigation reveals that **VmDaemonService and ShadowWorkspaceService serve different purposes**:

| System | Purpose | Location | User Control |
|--------|---------|----------|--------------|
| **ShadowWorkspace** | Background code refinement | Local | Opt-in setting |
| **VM/Background Composer** | Cloud agent execution | Remote Cloud | Privacy mode + explicit selection |

## ShadowWorkspaceService (Local)

### Service Architecture
- **Service ID**: `IShadowWorkspaceService` (line 831687)
- **Implementation**: `Wyo` class (line 831688)
- **Manager**: `INativeShadowWorkspaceManager` (line 1114235)

### Configuration Setting (Line 450669-450672)
```javascript
[oNt]: {
    type: "boolean",
    default: false,  // DISABLED by default
    description: "Warning: this will increase the memory usage of Cursor.
                  Some AI features use the shadow workspace to refine code
                  in the background before presenting it to you. The shadow
                  workspace is a hidden window running on your local machine
                  in a copy of your current workspace."
}
```

### Enabling Logic (Line 831707-831708)
```javascript
enabled() {
    return this.configurationService.getValue(oNt) ?? false
}
```

### Availability Constraint (Line 1114243-1114244)
```javascript
available() {
    return !this.nativeWorkbenchEnvironmentService.remoteAuthority
}
```

**Critical Constraint**: Shadow workspace is **NOT available when using remote workspaces** (SSH, WSL, containers). It only works when Cursor runs locally on the user's machine.

### How It Works
1. Opens a hidden VS Code window with same workspace folders
2. Creates socket-based IPC communication (Unix socket or named pipe)
3. Socket path format: `sw{workspaceId}.sock`
4. Auto-closes on lifecycle shutdown

### gRPC Service Methods (Line 809709-809788)
| Method | Purpose |
|--------|---------|
| `GetLintsForChange` | Get linting errors for code changes |
| `ShadowHealthCheck` | Health check |
| `SwSyncIndex` | Sync repository index |
| `SwProvideTemporaryAccessToken` | Auth token handling |
| `SwCompileRepoIncludeExcludePatterns` | Gitignore patterns |
| `SwCallClientSideV2Tool` | Execute AI tools |
| `SwGetExplicitContext` | Get context for AI |
| `SwWriteTextFileWithLints` | Write files and lint |
| `SwGetEnvironmentInfo` | Environment information |
| `SwGetLinterErrors` | Get linting errors |
| `SwGetMcpTools` | MCP tool definitions |
| `SwTrackModel` | Model usage tracking |
| `SwCallDiagnosticsExecutor` | Run diagnostics |

## VmDaemonService (Remote Cloud)

### Service Definition (Line 831475)
```javascript
typeName: "aiserver.v1.VmDaemonService"
```

This is a **gRPC service definition** for communicating with remote VM pods in Cursor's cloud infrastructure.

### gRPC Service Methods (Line 831476-831608)
| Method | Purpose |
|--------|---------|
| `SyncIndex` | Sync repository index to VM |
| `CompileRepoIncludeExcludePatterns` | Handle gitignore patterns |
| `Upgrade` | Upgrade VM daemon |
| `Ping` | Health check |
| `Exec` | Execute commands |
| `CallClientSideV2Tool` | Call AI tools |
| `ReadTextFile` | Read files |
| `WriteTextFile` | Write files |
| `GetFileStats` | Get file metadata |
| `GetExplicitContext` | Get context for AI |
| `GetEnvironmentInfo` | Get VM environment info |
| `ProvideTemporaryAccessToken` | Auth token handling |
| `WarmCursorServer` | Pre-warm connections |
| `RefreshGitHubAccessToken` | GitHub OAuth |
| `GetWorkspaceChangesHash` | Track changes |
| `GetDiff` | Get file diffs |
| `GetLinterErrors` | Run linting |
| `GetLogs` | Get execution logs |
| `InstallExtensions` | Install VS Code extensions |
| `GetMcpTools` | Get MCP tool definitions |
| `TrackModel` | Model usage tracking |
| `CallDiagnosticsExecutor` | Run diagnostics |

## Background Composer (Cloud Agent) Environment Selection

### Three Environment Modes (Line 756489-756505)
Users can select between:

1. **Development** (`"dev"`) - Development environment
2. **Production** (`"prod"`) - Production environment (default)
3. **Full Local** (`"fullLocal"`) - Non-VM running locally

### Environment Selection Command
```javascript
// "Switch Cloud Agent Environment" command
// Line 756486-756507
const items = [
    { label: "Development", picked: env === "dev" },
    { label: "Production", picked: env === "prod" },
    { label: "Full Local", description: "Use full local environment (non-VM running locally)", picked: env === "fullLocal" }
];
```

### Backend URL Routing (Line 440546-440547)
```javascript
getBcProxyDevUrl() {
    const env = this.reactiveStorageService.applicationUserPersistentStorage.backgroundComposerEnv ?? "prod";
    return this.getBackendUrl().includes("localhost") || env === "dev" || env === "fullLocal"
        ? EN + this.localBackendPort()  // Local backend
        : mue  // Cloud backend
}
```

When `backgroundComposerEnv` is `"fullLocal"` or `"dev"`, it uses a local backend port instead of cloud.

### Default Values
- Workspace storage default: `"dev"` (line 182285)
- Application persistent storage default: `"prod"` (line 182907)

## VM Pod Management

### Pod Creation (Line 1142827-1142860)
```javascript
async createDefaultVmPodAndSave(e) {
    const existingPod = this.backgroundComposerDataService.workspacePersistentData.defaultVmPod;
    const isExpired = existingPod && (!existingPod.createdAt || Date.now() - existingPod.createdAt > aLu);

    if (existingPod && !e.forceRetry && !isExpired) return existingPod;

    const client = await this.aiService.backgroundComposerClient();
    const response = await client.createBackgroundComposerPod({
        devcontainerStartingPoint: o,
        includeSecrets: false,
        forceCluster: forcedCluster === "prod" ? undefined : forcedCluster
    });

    return {
        id: response.podId,
        workspaceRootPath: response.workspaceRootPath,
        createdAt: Date.now()
    };
}
```

### Pod Data Structure
```javascript
workspacePersistentData: {
    defaultVmPod: { id, workspaceRootPath, createdAt },
    testingVmPod: { id, workspaceRootPath, createdAt },
    snapshotUsedForDefaultVMPod: string,
    installScript: string,
    startScript: string,
    terminals: [],
    vmSnapshotId: string
}
```

### Rebuild Pod (Line 1142930-1142944)
```javascript
rebuildDefaultVMPod() {
    this.backgroundComposerDataService.setWorkspacePersistentData({
        defaultVmPod: undefined,
        ranTerminalCommands: [],
        installScript: "",
        startScript: "",
        terminals: []
    });

    const step = this.experimentService.checkFeatureGate("cloud_agent_setup_v2")
        ? "install-dependencies"
        : "start-default-vm";
    // ... continue setup flow
}
```

## Feature Flags Controlling Cloud Agent

### Setup Version Feature Gate
```javascript
// Line 1142938
const step = this.experimentService.checkFeatureGate("cloud_agent_setup_v2")
    ? "install-dependencies"
    : "start-default-vm"
```

### Related Feature Flags (Line 293541-294390)
| Flag | Purpose |
|------|---------|
| `cloud_agent_setup_v2` | Setup flow version |
| `cloud_agent_polished_recordings` | Recording feature |
| `cloud_agent_artifacts_enable` | Artifacts feature |
| `cloud_agent_artifacts_web_rendering_enabled` | Web rendering |
| `cloud_agent_artifacts_vscode_rendering_enabled` | VS Code rendering |
| `cloud_agent_internal_sdk` | Internal SDK |
| `cloud_agent_new_conversation_stream` | New streaming |
| `cloud_agent_new_conversation_stream_writes` | Stream writes |
| `cloud_agent_stream_skip_disk_read` | Skip disk reads |
| `cloud_agent_stream_force_stream_from_start` | Force stream start |
| `cloud_agent_send_prefetched_blobs_first` | Blob optimization |
| `cloud_agent_send_existing_blob_ids` | Blob ID handling |
| `vm_usage_watcher_enabled` | VM usage monitoring |

## Architecture Diagram

```
+---------------------------+          +---------------------------+
|     LOCAL EXECUTION       |          |    CLOUD EXECUTION        |
+---------------------------+          +---------------------------+
            |                                      |
            v                                      v
+---------------------------+          +---------------------------+
|   IShadowWorkspaceService |          |  Background Composer      |
|   (opt-in user setting)   |          |  (privacy mode dependent) |
+---------------------------+          +---------------------------+
            |                                      |
            v                                      v
+---------------------------+          +---------------------------+
|   Hidden VS Code Window   |          |  VmDaemonService (gRPC)   |
|   (same workspace copy)   |          |  (remote VM pod)          |
+---------------------------+          +---------------------------+
            |                                      |
      Unix Socket                            gRPC over HTTPS
            |                                      |
            v                                      v
+---------------------------+          +---------------------------+
|  ShadowWorkspaceService   |          |   Cloud VM Infrastructure |
|  (gRPC server)            |          |   (pod-{uuid})            |
+---------------------------+          +---------------------------+
```

## Decision Logic Summary

### When Shadow Workspace is Used
1. User has **explicitly enabled** the shadow workspace setting
2. User is running Cursor **locally** (not SSH/WSL/container)
3. AI features need background code refinement

### When VM/Cloud Agent is Used
1. User's **privacy mode allows code storage** (not NO_STORAGE mode)
2. User **explicitly selects** "Cloud" or "background" mode
3. User initiates Background Composer setup flow
4. GitHub connection is established (for most features)

### Key Differences
| Aspect | Shadow Workspace | VM/Background Composer |
|--------|-----------------|----------------------|
| **Location** | Local machine | Cursor cloud |
| **Default** | Disabled | Enabled (if privacy allows) |
| **Memory** | Increases local usage | Cloud resources |
| **Persistence** | Session-based | Persistent with snapshots |
| **Privacy** | No data leaves machine | Requires code storage permission |
| **Availability** | Local only | Available with remote workspaces |
| **Purpose** | Code refinement | Long-running async tasks |

## Conclusions

1. **No automatic selection logic** exists between VM and Shadow - they are independent systems
2. Shadow workspace is a **local optimization** that must be explicitly enabled
3. VM/Cloud Agent is the **primary remote execution** environment for Background Composer
4. The `fullLocal` option provides a way to run Background Composer without cloud VMs
5. Privacy mode is the **gating factor** for cloud execution
6. Feature flags control advanced cloud agent capabilities

## Open Questions for Further Investigation

1. What specific AI features trigger shadow workspace usage?
2. How does cost/billing work for cloud VM pods?
3. What is the snapshot retention policy for VM pods?
4. How does the system handle concurrent shadow workspaces?
5. What fallback logic exists when shadow workspace is unavailable?

---
*Analysis based on Cursor IDE 2.3.41 beautified source code*
*Source file: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`*
*Generated: 2026-01-28*
