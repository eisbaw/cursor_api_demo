# TASK-5: ShadowWorkspaceService Sandbox Mechanism Analysis

## Overview

The ShadowWorkspaceService is a core component of Cursor's AI agent execution system that provides an isolated environment for the AI to make code modifications, run linters, and execute terminal commands without directly affecting the user's active workspace. It creates a hidden VS Code window that mirrors the main workspace, enabling the AI to iterate on code changes, get linter feedback, and execute terminal commands in a sandboxed environment before presenting final results to the user.

## Key Components

### 1. Service Interfaces

The system involves several related services:

| Service | Interface ID | Purpose |
|---------|-------------|---------|
| `IShadowWorkspaceService` | `on("IShadowWorkspaceService")` | Core orchestration service (line 831687) |
| `IShadowWorkspaceServerService` | `on("IShadowWorkspaceServerService")` | Server-side execution in shadow window (line 831685) |
| `INativeShadowWorkspaceManager` | `on("INativeShadowWorkspaceManager")` | Native window management (line 1114235) |

### 2. Configuration

- **Setting Key**: `cursor.general.enableShadowWorkspace` (internal variable: `oNt`)
- **Default**: Disabled (opt-in feature)
- **Description**: "Warning: this will increase the memory usage of Cursor. Some AI features use the shadow workspace to refine code in the background before presenting it to you. The shadow workspace is a hidden window running on your local machine in a copy of your current workspace."
- **Effect**: When enabled, Cursor opens a hidden VS Code window to execute AI operations

### 3. Storage Location

Shadow workspace files are stored in:
```javascript
function lwh(environmentService, productService) {
    return URI.joinPath(environmentService.userHome, productService.dataFolderName, "shadow-workspaces")
}
// e.g., ~/.cursor/shadow-workspaces/ or %USERPROFILE%\.cursor\shadow-workspaces\
```

## Architecture

### Shadow Workspace Lifecycle

```
Main Window                          Shadow Window
    |                                     |
    |-- openShadowWorkspace() ----------->|
    |                                     |
    |   (Creates workspace file)          |
    |   (Copies workspace settings)       |
    |   (Opens hidden window)             |
    |                                     |
    |<-- IPC over Unix Socket ------------->
    |    (sw{workspaceId}.sock)           |
    |                                     |
    |-- getClient() --------------------->|
    |<-- shadowHealthCheck() -------------|
    |                                     |
    |-- swCallClientSideV2Tool() -------->|
    |-- swWriteTextFileWithLints() ------>|
    |-- swRunTerminalCommand() ---------->|
    |                                     |
    |-- closeShadowWorkspace() ---------->|
    |                                     X (Window destroyed)
```

### Workspace Creation Process

```javascript
async createShadowWorkspace() {
    // Close any existing shadow workspace
    if (this.shadowWorkspaceUri) await this.closeShadowWorkspace();

    // Generate unique workspace file name
    const timestamp = Date.now() + Math.round(Math.random() * 1000);
    this.shadowWorkspaceUri = URI.joinPath(
        this.shadowWorkspacesHome,
        `Untitled-${timestamp}.code-workspace`
    );

    // Copy workspace folders with references
    const folders = this.workspaceContextService.getWorkspace().folders;
    const shadowFolders = folders.map(folder =>
        createWorkspaceFolder(folder.uri, true, folder.name, this.shadowWorkspacesHome)
    );

    // Create workspace configuration
    const config = {
        folders: shadowFolders,
        remoteAuthority: environmentService.remoteAuthority,
        transient: true  // Marks as temporary
    };

    await this.fileService.writeFile(
        this.shadowWorkspaceUri,
        Buffer.from(JSON.stringify(config, null, "\t"))
    );

    this.cleanUpOldFiles();  // Keep only last 5 workspace files
    return workspaceIdentifier;
}
```

### Window Opening Configuration

```javascript
async openShadowWorkspace() {
    const workspaceIdentifier = await this.createShadowWorkspace();

    // Copy settings with specific overrides
    await this.workspaceEditingService.copyWorkspaceSettings(workspaceIdentifier, {
        overrides: {
            "files.autoSave": "off"  // Disable auto-save in shadow
        }
    });

    // Open hidden window
    const result = await this.nativeHostService.openWindow([{
        workspaceUri: workspaceIdentifier.configPath
    }], {
        forceNewWindow: true,
        shadowWindowForWorkspaceId: this.workspaceContextService.getWorkspace().id
    });

    this.shadowWindowId = result[0]?.windowId;
}
```

### IPC Communication

The main window and shadow window communicate via Unix domain sockets (or named pipes on Windows):

```javascript
getSocketPathForWorkspaceId(workspaceId) {
    if (isWindows) {
        return `\\\\.\\pipe\\ipc-cursor-sw-${workspaceId}-sock`;
    }

    // Unix: Uses cache home directory
    let socketPath = URI.joinPath(
        this.workbenchEnvironmentService.cacheHome,
        `sw${workspaceId}.sock`
    );

    // Handle Unix socket path length limit (103 chars)
    if (socketPath.fsPath.length > 103) {
        const excess = socketPath.fsPath.length - 103;
        if (workspaceId.length - excess < 7) {
            throw new Error("Failed to create socket path! Cache home directory is too long.");
        }
        const truncatedId = workspaceId.substring(excess);
        socketPath = URI.joinPath(cacheHome, `sw${truncatedId}.sock`);
    }

    return socketPath.fsPath;
}
```

### Client-Server Communication Protocol

The shadow workspace uses a proxy-based RPC mechanism:

```javascript
// Main window creates client proxy
this.shadowWorkspaceService.provideClient(async (socketPath) => {
    await this._proxy.$createShadowClient(socketPath);

    return new Proxy({}, {
        get: (target, methodName) => {
            const inputType = EKt.methods[methodName]?.I;
            const outputType = EKt.methods[methodName]?.O;

            return async (request, options) => {
                const requestBinary = new inputType(request).toBinary();
                const responseBinary = await this._proxy.$callShadowServer(
                    methodName,
                    Buffer.wrap(requestBinary),
                    cancellationToken
                );
                return outputType.fromBinary(responseBinary);
            };
        }
    });
});
```

## gRPC Service Definition

### aiserver.v1.ShadowWorkspaceService

Located at line 809709, the service exposes these methods:

| Method | Input Type | Output Type | Purpose |
|--------|-----------|-------------|---------|
| `GetLintsForChange` | `ncl` | `Vlt` | Get linter errors for proposed code changes |
| `ShadowHealthCheck` | `PPr` | `LPr` | Verify shadow workspace is responsive |
| `SwSyncIndex` | `icl` | `APr` | Synchronize file index with main workspace |
| `SwProvideTemporaryAccessToken` | `tcl` | `RPr` | Share authentication with shadow window |
| `SwCompileRepoIncludeExcludePatterns` | `DPr` | `cas` | Handle .cursorignore patterns |
| `SwCallClientSideV2Tool` | `ecl` | `C4t` | Execute AI tools in sandbox |
| `SwGetExplicitContext` | `Yll` | `EPr` | Retrieve context for AI |
| `SwWriteTextFileWithLints` | `Kll` | `kPr` | Write files and collect lint errors |
| `SwGetEnvironmentInfo` | `Xll` | `xPr` | Get environment metadata |
| `SwGetLinterErrors` | `Qll` | `TPr` | Get current linter state |
| `SwGetMcpTools` | `Zll` | `IPr` | Get MCP tool definitions |
| `SwTrackModel` | `zll` | `_Pr` | Track text model for editing |
| `SwCallDiagnosticsExecutor` | `jll` | `CPr` | Run diagnostics |

## Sandbox Policy System

### Policy Types (agent.v1.SandboxPolicy.Type)

Located in `out-build/proto/agent/v1/sandbox_pb.js` (line 94183):

```javascript
enum SandboxPolicyType {
    TYPE_UNSPECIFIED = 0,     // Default/unknown
    TYPE_INSECURE_NONE = 1,   // No sandboxing - full access
    TYPE_WORKSPACE_READWRITE = 2, // Sandbox with r/w to workspace
    TYPE_WORKSPACE_READONLY = 3   // Sandbox with read-only access
}
```

### SandboxPolicy Structure

```protobuf
message SandboxPolicy {
    Type type = 1;                           // Sandbox mode
    optional bool network_access = 2;         // Allow network requests
    repeated string additional_readwrite_paths = 3;  // Extra writable paths
    repeated string additional_readonly_paths = 4;   // Extra readable paths
    optional string debug_output_dir = 5;     // Debug logging directory
    optional bool block_git_writes = 6;       // Prevent git operations
    optional bool disable_tmp_write = 7;      // Block /tmp writes
    // Dynamically attached:
    optional IgnoreMapping ignore_mapping;    // Cursorignore patterns
}
```

### Policy Processing Functions

```javascript
// Determine sandbox status from policy
function getSandboxStatus(policy) {
    if (!policy || policy.type === SandboxPolicyType.INSECURE_NONE) {
        return { sandboxed: false };
    }
    return {
        sandboxed: true,
        sandboxNetworkEnabled: policy.networkAccess ?? false,
        sandboxGitWritesEnabled: policy.blockGitWrites === false
    };
}

// Map string config to policy type
function convertSandboxType(typeString) {
    switch (typeString) {
        case "insecure_none": return SandboxPolicyType.INSECURE_NONE;
        case "workspace_readonly": return SandboxPolicyType.WORKSPACE_READONLY;
        case "workspace_readwrite":
        default: return SandboxPolicyType.WORKSPACE_READWRITE;
    }
}
```

### Policy Enrichment Flow

When executing terminal commands in the shadow workspace:

```javascript
// Step 1: Add workspace folders to allowed paths
addWorkspaceFoldersToPolicy(policy) {
    if (policy.type !== SandboxPolicyType.WORKSPACE_READWRITE) return policy;

    const workspaceFolders = this.workspaceContextService.getWorkspace().folders;
    if (workspaceFolders.length <= 1) return policy;

    const existingPaths = policy.additionalReadwritePaths ?? [];
    const folderPaths = workspaceFolders.map(f => f.uri.fsPath);
    const mergedPaths = [...new Set([...existingPaths, ...folderPaths])];

    return new SandboxPolicy({
        type: policy.type,
        networkAccess: policy.networkAccess,
        additionalReadwritePaths: mergedPaths,
        additionalReadonlyPaths: policy.additionalReadonlyPaths,
        blockGitWrites: policy.blockGitWrites,
        debugOutputDir: policy.debugOutputDir
    });
}

// Step 2: Attach cursorignore patterns
enrichPolicyWithCursorIgnore(policy) {
    if (!policy || policy.type === SandboxPolicyType.INSECURE_NONE) return policy;

    try {
        const ignoreMapping = this.cursorIgnoreService.getSerializableIgnoreMapping();
        policy.ignore_mapping = ignoreMapping;
    } catch (error) {
        this.logService.warn("[ShadowWorkspaceServer] Failed to attach cursorignore mapping", error);
    }

    return policy;
}
```

## Shadow Workspace Server Implementation

### Server Class Structure (line 1128621)

```javascript
class ShadowWorkspaceServer extends Disposable {
    constructor(
        aiServerConfigService,
        aiService,
        composerChatService,
        authenticationService,
        cursorIgnoreService,
        editorService,
        editorWorkerService,
        fileService,
        languageFeaturesService,
        languageService,
        logService,
        markerService,
        mcpService,
        modelService,
        nativeHostService,
        repositoryService,
        storageService,
        terminalExecutionServiceV2,
        terminalExecutionServiceV3,
        textFileService,
        textModelService,
        toolsV2HandlerRegistryService,
        environmentService,
        workspaceContextService,
        toolV2Service
    ) {
        this.models = new LRUCache(100);  // Cache for text models
        this.semaphore = new Semaphore(1); // Serialization for requests
        this.terminalSessions = new Map();
        this.destructionTimer = undefined;
        this.sandboxFlagInitialized = false;
    }
}
```

### Health Check and Sandbox Detection

```javascript
async shadowHealthCheck(request) {
    this.keepalive();  // Reset destruction timer

    // Initialize sandbox support flag on first check
    if (!this.sandboxFlagInitialized) {
        this._initializeSandboxSupportFlag();
    }

    // Wait for tool handlers to be ready
    if (!this.toolsV2HandlerRegistryService.isInitializationComplete()) {
        let waited = 0;
        while (!this.toolsV2HandlerRegistryService.isInitializationComplete() && waited < 5000) {
            this.logService.warn("tool handlers not registered yet, waiting...");
            await sleep(100);
            waited += 100;
        }
        if (!this.toolsV2HandlerRegistryService.isInitializationComplete()) {
            throw new Error("Tool handlers not registered yet");
        }
    }

    return new HealthCheckResponse();
}

_initializeSandboxSupportFlag() {
    try {
        const serviceVersion = this._getTerminalExecutionService().getServiceVersion();
        const sandboxSupported = serviceVersion === "v3";
        this.logService.info(
            `[ShadowWorkspaceServer] _initializeSandboxSupportFlag: serviceVersion=${serviceVersion}, supported=${sandboxSupported}`
        );
        // Store in reactive storage for other components
        ReactiveStorage.get(this.storageService, "sandboxSupported").set(sandboxSupported);
        this.sandboxFlagInitialized = true;
    } catch (error) {
        this.logService.warn("[ShadowWorkspaceServer] Failed to initialize sandboxSupported flag", error);
    }
}
```

## Change Staging Mechanism

### File Writing with Lint Feedback

The `swWriteTextFileWithLints()` method (line 1128921) implements lint-aware file writing:

```javascript
async swWriteTextFileWithLints(request) {
    const uri = URI.file(request.absolutePath);
    const disposables = new DisposableStore();

    try {
        // Detect language from file path/content
        const languageId = this.languageService.createByLanguageNameOrFilepathOrFirstLine(
            null, uri, request.newContents.split("\n")[0] ?? ""
        );

        // Create or get text model
        let model;
        try {
            const modelRef = await this.textModelService.createModelReference(uri);
            disposables.add(modelRef);
            model = modelRef.object.textEditorModel;
        } catch {
            // File doesn't exist - create temporary model
            model = this.modelService.createModel(request.newContents, languageId, uri);
            disposables.add(model);
        }

        // Apply content and wait for linters
        // ... (linter feedback loop)

    } finally {
        disposables.dispose();
    }
}
```

### Lint Change Tracking

The `getLintsForChange()` method implements an interesting pattern for getting linter feedback:

```javascript
async getLintsForChange(request) {
    // Track existing models
    const existingModelIds = new Set();
    this.textFileService.files.models.forEach(model => {
        if (model.textEditorModel) existingModelIds.add(model.textEditorModel.id);
        if (model.isDirty()) model.revert();  // Revert any unsaved changes
    });

    let fileModels = [];
    const disposables = [];

    try {
        let newFilesCreated = false;

        // Process each file change request
        fileModels = await Promise.all(request.files.map(async file => {
            const uri = this.workspaceContextService.resolveRelativePath(file.relativeWorkspacePath);
            let model;

            try {
                const modelRef = await this.textModelService.createModelReference(uri);
                disposables.push(modelRef);
                model = modelRef.object.textEditorModel;
                if (!existingModelIds.has(model.id)) newFilesCreated = true;
            } catch {
                // Create new model for non-existent file
                const languageId = this.languageService.createByLanguageNameOrFilepathOrFirstLine(
                    null, uri, file.finalContent.split("\n")[0] ?? ""
                );

                if (request.doNotUseInProdNewFilesShouldBeTemporarilyCreatedForIncreasedAccuracy) {
                    const tempFile = await this.createTemporaryFile(uri, file);
                    disposables.push(tempFile);
                }

                model = this.modelService.createModel(file.initialContent, languageId, uri, false, true, true);
                disposables.push(model);
                newFilesCreated = true;
            }

            // Open in editor
            const editor = await this.editorService.openEditor({
                resource: uri,
                options: { pinned: false }
            });
            disposables.push({
                dispose: async () => {
                    const input = editor?.input;
                    if (input && editor?.group?.id) {
                        await input.revert(editor.group.id);
                    }
                }
            });

            // Apply initial content
            const edits = await this.editorWorkerService.computeMoreMinimalEdits(model.uri, [{
                text: file.initialContent,
                range: model.getFullModelRange()
            }]);
            if (edits) model.pushEditOperations(null, edits, () => null);
            model.pushStackElement();

            return { file, model };
        }));

        // Prime linters if new files were created
        if (newFilesCreated) {
            let markerChanged;
            const markerChangedPromise = new Promise(resolve => { markerChanged = resolve; });
            disposables.push(Event.once(this.markerService.onMarkerChanged)(() => markerChanged("markerChanged")));

            // Inject deliberate error to trigger linters
            for (const { model } of fileModels) {
                model.pushEditOperations(null, [{
                    text: "THIS SHOULD BE A LINTER ERROR",
                    range: new Range(1, 1, 1, 1)
                }], () => null);
            }

            // Wait for markers (with 20s timeout)
            const result = await Promise.race([
                markerChangedPromise,
                new Promise(r => setTimeout(() => r("timedout"), 20000))
            ]);

            if (result === "timedout") {
                this.logService.warn("Timed out waiting for markers to show up");
            }

            // Undo the deliberate error
            for (const { model } of fileModels) {
                model.undo();
            }
        }

        // Wait for linters to settle
        await sleep(newFilesCreated ? 4000 : 2000);

        // Capture initial lint state with decorations
        const lintDecorations = new Map();
        for (const { model } of fileModels) {
            const markers = this.markerService.read({ resource: model.uri });
            const decorationIds = model.deltaDecorations([], markers.map(m => ({
                range: Range.lift(m),
                options: { description: "Lint error" }
            })));
            lintDecorations.set(model.id, markers.map((marker, i) => ({
                marker,
                decorationId: decorationIds[i]
            })));
        }

        // Apply final content
        for (const { file, model } of fileModels) {
            const edits = await this.editorWorkerService.computeMoreMinimalEdits(model.uri, [{
                text: file.finalContent,
                range: model.getFullModelRange()
            }]);
            if (edits) model.pushEditOperations(null, edits, () => null);
        }

        // Wait and collect final lints
        await sleep(2000);

        // Return new linter errors (errors that weren't present before)
        const result = [];
        for (const { model } of fileModels) {
            const newMarkers = this.markerService.read({ resource: model.uri });
            const oldDecorations = lintDecorations.get(model.id);
            // Filter to only new errors
            // ...
            result.push({ path: model.uri.fsPath, linterErrors: newMarkers });
        }

        return new LintResponse({ fileResults: result });

    } finally {
        for (const d of disposables) {
            try { await d.dispose(); } catch {}
        }
    }
}
```

## Terminal Command Execution

### swRunTerminalCommand Implementation

Located around line 1129087, handles sandboxed command execution:

```javascript
async swRunTerminalCommand(toolCall, composerId, context) {
    const TAG = "[ShadowWorkspaceServer.swRunTerminalCommand]";
    const service = this._getTerminalExecutionService();
    const serviceVersion = service.getServiceVersion();

    this.logService.info(`${TAG} START - serviceVersion=${serviceVersion}`);

    // Validate tool call
    if (toolCall.tool !== Tools.RUN_TERMINAL_COMMAND_V2 || !toolCall.params?.value) {
        throw new Error("Invalid tool call for swRunTerminalCommand");
    }

    const params = toolCall.params.value;
    this.logService.info(`${TAG} command="${params.command}", isBackground=${params.isBackground}, timeout=${params.options?.timeout}`);

    // Enrich sandbox policy
    let policy = params.requestedSandboxPolicy
        ? this.addWorkspaceFoldersToPolicy(params.requestedSandboxPolicy)
        : undefined;
    this.logService.info(`${TAG} after addWorkspaceFoldersToPolicy: ${JSON.stringify(policy)}`);

    policy = this.enrichPolicyWithCursorIgnore(policy);
    this.logService.info(`${TAG} after enrichPolicyWithCursorIgnore (final effectivePolicy): ${JSON.stringify(policy)}`);

    // Session management
    let sessionId, terminalInstance;
    if (params.isBackground) {
        // Background: Create new session
        const session = await service.startSession(undefined);
        sessionId = session.sessionId;
        terminalInstance = session.terminalInstance;
        this.logService.info(`${TAG} Created background session: sessionId=${sessionId}`);
    } else {
        // Foreground: Reuse or create session per composer
        const existingSession = this.terminalSessions.get(composerId);
        if (existingSession) {
            sessionId = existingSession;
            terminalInstance = service.getTerminalInstance(sessionId);
            if (!terminalInstance) {
                throw new Error("Terminal instance not found");
            }
        } else {
            const session = await service.startSession(undefined);
            sessionId = session.sessionId;
            this.terminalSessions.set(composerId, sessionId);
            terminalInstance = session.terminalInstance;
        }
    }

    // Abort handling
    const abortController = new AbortController();
    if (!params.isBackground) {
        if (context.signal.aborted) {
            abortController.abort();
        } else {
            const timeoutId = params.options?.timeout !== undefined
                ? setTimeout(() => abortController.abort(), params.options.timeout)
                : undefined;
            context.signal.addEventListener("abort", () => {
                abortController.abort();
                clearTimeout(timeoutId);
            });
        }
    }

    // Execute command
    const options = {
        signal: abortController.signal,
        ...params.options,
        sandboxPolicy: policy
    };

    this.logService.info(`${TAG} Calling executeStream with sessionId=${sessionId}, command="${params.command}"`);
    const streamer = service.executeStream(sessionId, params.command, options);

    // Background: Fire and forget
    if (params.isBackground) {
        (async () => {
            try {
                for await (const chunk of streamer) { /* consume */ }
                this.logService.info(`${TAG} Background command completed`);
            } catch (error) {
                this.logService.error(`${TAG} Background command error:`, error);
            }
        })();

        return new ToolResult({
            tool: Tools.RUN_TERMINAL_COMMAND_V2,
            result: {
                case: "runTerminalCommandV2Result",
                value: new RunTerminalCommandResult({
                    output: "",
                    poppedOutIntoBackground: true,
                    isRunningInBackground: true,
                    notInterrupted: true,
                    effectiveSandboxPolicy: policy
                })
            }
        });
    }

    // Foreground: Collect output
    this.logService.info(`${TAG} Non-background command - collecting output`);
    let output = "";
    let exitCode, endedReason;
    let iteration = 0;

    for (;;) {
        const { value, done } = await streamer.next();
        iteration++;

        if (done) {
            exitCode = value.exitCode;
            endedReason = value.endedReason;
            this.logService.info(`${TAG} Stream done after ${iteration} iterations: exitCode=${exitCode}, endedReason=${endedReason}`);
            break;
        }

        output = value.content;
        if (iteration <= 3) {
            this.logService.info(`${TAG} Stream iteration ${iteration}: contentLength=${output.length}`);
        }
    }

    // Handle interruption
    const interrupted = abortController.signal.aborted || endedReason === EndedReason.EXECUTION_ABORTED;
    this.logService.info(`${TAG} Command finished: interrupted=${interrupted}, exitCode=${exitCode}`);

    if (interrupted) {
        this.logService.info(`${TAG} Command was interrupted - cleaning up session`);
        service.cancelStream(sessionId);
        service.endSession(sessionId);
        this.terminalSessions.delete(composerId);
    }

    return new ToolResult({
        tool: Tools.RUN_TERMINAL_COMMAND_V2,
        result: {
            case: "runTerminalCommandV2Result",
            value: new RunTerminalCommandResult({
                output: output,
                exitCodeV2: exitCode !== undefined ? wrapInt32(exitCode) : undefined,
                poppedOutIntoBackground: false,
                isRunningInBackground: false,
                notInterrupted: !interrupted,
                resultingWorkingDirectory: terminalInstance.cwd,
                endedReason: endedReason,
                effectiveSandboxPolicy: policy
            })
        }
    });
}
```

### Tool Dispatch

```javascript
async swCallClientSideV2Tool(request, context) {
    if (request.toolCall === undefined) throw new Error("Tool call is undefined");
    if (request.toolCall.tool === Tools.UNSPECIFIED) throw new Error("Tool is unspecified");

    // Special handling for terminal commands
    if (request.toolCall.tool === Tools.RUN_TERMINAL_COMMAND_V2) {
        return new ClientSideToolResult({
            toolResult: await this.swRunTerminalCommand(request.toolCall, request.composerId, context)
        });
    }

    // Validate tool is registered
    validateRegisteredTool(request.toolCall.tool);

    // Get and invoke tool handler
    const handler = this.toolsV2HandlerRegistryService.getHandler(request.toolCall.tool);
    const abortController = new AbortController();

    if (context.signal.aborted) abortController.abort();
    context.signal.addEventListener("abort", () => abortController.abort());

    // Special context for MCP tools
    let additionalContext;
    if (request.toolCall.tool === Tools.MCP) {
        additionalContext = { type: McpContextType.RUN };
    }

    try {
        const result = await handler(
            request.toolCall,
            request.composerId,
            abortController.signal,
            additionalContext
        );
        return new ClientSideToolResult({ toolResult: result });
    } catch (error) {
        throw error;
    }
}
```

## Relationship with VmDaemonService

### aiserver.v1.VmDaemonService

The VmDaemonService (line 831475) appears to be an alternative/complementary execution backend for remote/VM-based execution:

| Method | Input Type | Output Type | Purpose |
|--------|-----------|-------------|---------|
| `SyncIndex` | `u4f` | `d4f` | Sync file index |
| `CompileRepoIncludeExcludePatterns` | `e4f` | `t4f` | Pattern compilation |
| `Upgrade` | `h4f` | `f4f` | Upgrade daemon |
| `Ping` | `s4f` | `r4f` | Health check |
| `Exec` | `$Bf` | `qBf` | Execute commands |
| `CallClientSideV2Tool` | `m4f` | `g4f` | Tool execution |
| `ReadTextFile` | `o4f` | `a4f` | File reading |
| `WriteTextFile` | `l4f` | `c4f` | File writing |
| `GetFileStats` | `XBf` | `QBf` | File metadata |
| `GetExplicitContext` | `zBf` | `jBf` | Context retrieval |
| `GetEnvironmentInfo` | `KBf` | `YBf` | Environment info |
| `ProvideTemporaryAccessToken` | `i4f` | `n4f` | Auth sharing |
| `WarmCursorServer` | `JBf` | `GBf` | Server warmup |
| `RefreshGitHubAccessToken` | `p4f` | `v4f` | GitHub auth refresh |
| `GetWorkspaceChangesHash` | `y4f` | `b4f` | Change detection |
| `GetDiff` | `BMe` | - | Get file diffs |

**Key Difference**: VmDaemonService appears to be for remote/VM-based execution, while ShadowWorkspaceService runs locally in a hidden window. Both share similar APIs for tool execution.

## Auto-Destruction Timer

Shadow workspaces self-destruct after inactivity:

```javascript
// Default timeout: 15 minutes
const DEFAULT_DESTRUCTION_MINUTES = 15;

// Parse timeout from workspace ID (e.g., "destroy-after-30-minutes-{id}")
function parseDestructionTime(workspaceId) {
    if (!workspaceId) return DEFAULT_DESTRUCTION_MINUTES;

    const match = workspaceId.match(/destroy-after-(\d+)-minutes/);
    return match ? parseInt(match[1], 10) : DEFAULT_DESTRUCTION_MINUTES;
}

keepalive() {
    // Clear existing timer
    if (this.destructionTimer !== undefined) {
        clearTimeout(this.destructionTimer);
        this.destructionTimer = undefined;
    }

    // Set new destruction timer
    const minutes = parseDestructionTime(this.environmentService.shadowWindowForWorkspaceId);
    this.destructionTimer = setTimeout(() => {
        this.nativeHostService.closeWindow();
    }, minutes * 60 * 1000);
}
```

## Commit/Rollback Behavior

### Changes Are Never Auto-Committed

The shadow workspace operates in a transient manner:
- Changes made in shadow workspace don't affect main workspace files
- The AI iterates on code in the shadow environment
- Only final approved changes are applied to main workspace
- On close, shadow workspace files are deleted

### Workspace File Cleanup

```javascript
async closeShadowWorkspace() {
    // Close the hidden window
    if (this.shadowWindowId) {
        const closePromise = this.nativeHostService.closeWindowNoFallback({
            targetWindowId: this.shadowWindowId
        });
        // Wait up to 500ms for close
        await Promise.race([closePromise, new Promise(r => setTimeout(() => r("timedout"), 500))]);

        await this.nativeHostService.destroyWindowNoFallback({
            targetWindowId: this.shadowWindowId
        });
        this.shadowWindowId = undefined;
    }

    // Delete workspace configuration file
    if (this.shadowWorkspaceUri) {
        try {
            await this.fileService.del(this.shadowWorkspaceUri);
        } catch (error) {
            console.warn("failed to delete shadow workspace (this is probably fine)", error);
        }
        this.shadowWorkspaceUri = undefined;
    }
}

async cleanUpOldFiles() {
    const directory = await this.fileService.resolve(this.shadowWorkspacesHome);
    const workspaceFiles = directory.children
        ?.filter(f => f.name.endsWith(".code-workspace"))
        .map(f => f.name);

    workspaceFiles?.sort();

    // Keep only the 5 most recent, delete the rest
    if (workspaceFiles?.length) {
        workspaceFiles.slice(0, -5).forEach(filename => {
            this.fileService.del(URI.joinPath(this.shadowWorkspacesHome, filename));
        });
    }
}
```

## Extension Filtering for Shadow Windows

Shadow windows load a filtered set of extensions:

```javascript
function filterExtensionsForShadowWindow(extensions, extensionMap, environment) {
    return extensions.filter(extension => {
        const info = extensionMap.get(extension.identifier);
        if (!info) return false;

        // Special handling for shadow windows
        if (environment.shadowWindowForWorkspaceId &&
            !environment.shadowWindowForWorkspaceId.startsWith("all-extensions-")) {
            // Allow only whitelisted extensions
            const allowedExtensions = ["vscode.json-language-features", /* ... */];
            if (!allowedExtensions.includes(extension.identifier._lower)) {
                return false;
            }
        }

        return true;
    });
}
```

## Edit History Service Integration

The shadow workspace integrates with edit history tracking:

```javascript
// Register edit history provider
async $registerEditHistoryProvider() {
    const initModel = (modelUri) => {
        this._proxy.$getEditHistoryProviderInitModel(modelUri);
    };

    const hasProcessedTextModelUptilVersion = (modelUri) => {
        return this._proxy.$getEditHistoryProviderHasProcessedTextModelUptilVersion(modelUri);
    };

    const compileGlobalDiffTrajectories = (request) => {
        return this._proxy.$getEditHistoryProviderCompileGlobalDiffTrajectories(request);
    };

    this.editHistoryService.registerEditHistoryProvider({
        initModel,
        hasProcessedTextModelUptilVersion,
        compileGlobalDiffTrajectories
    });
}
```

## Security Considerations

1. **Sandbox Enforcement**: Terminal execution respects sandbox policy to limit file access
2. **Cursorignore Integration**: AI operations respect .cursorignore patterns
3. **Git Write Blocking**: Optional `blockGitWrites` flag prevents AI from making git commits
4. **Network Access Control**: Sandbox policy controls network access
5. **Temporary Auth Tokens**: Short-lived tokens shared with shadow window
6. **Extension Isolation**: Only necessary extensions loaded in shadow window

## Dialog Skipping in Shadow Window

File dialogs are automatically skipped in shadow windows:

```javascript
skipDialogs() {
    // Skip in extension development/testing
    if (this.environmentService.isExtensionDevelopment && this.environmentService.extensionTestsLocationURI) {
        return true;
    }

    // Skip in shadow workspace
    if (this.environmentService.shadowWindowForWorkspaceId) {
        return true;
    }

    // Skip in smoke test mode
    return !!this.environmentService.enableSmokeTestDriver;
}
```

## Questions for Further Investigation

1. **How does v3 terminal execution differ from v2?** - The code checks `VSCODE_TERMINAL_EXECUTION_SERVICE_VERSION` env var, v3 supports sandboxing
2. **What is the exact sandbox enforcement mechanism?** - Likely OS-level (landlock on Linux, sandbox on macOS)
3. **How are approved changes from shadow applied to main workspace?** - Need to trace the accept/apply flow
4. **What triggers VmDaemonService vs ShadowWorkspaceService selection?** - Likely remote vs local workspace

## File References

- Shadow workspace service class: Line 831687-831798 (`Wyo`)
- Native shadow workspace manager class: Line 1114235-1114302 (`t6o`)
- Shadow workspace server class: Line 1128621-1129237 (`uIe`)
- Shadow workspace server service: Line 1129249-1129258 (`S3o`)
- Sandbox policy protobuf: Line 94183-94266 (`d7`, `xk`)
- VmDaemonService definition: Line 831474-831609 (`oou`)
- Configuration key: Line 14764, 450669 (`oNt = "cursor.general.enableShadowWorkspace"`)
- Extension filtering: Lines 1135035-1135048
- Dialog skipping: Line 1123054
