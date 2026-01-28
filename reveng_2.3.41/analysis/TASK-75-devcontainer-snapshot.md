# TASK-75: DevcontainerStartingPoint and Environment Snapshot Mechanism

## Overview

This analysis documents the DevcontainerStartingPoint implementation and environment snapshot mechanism used by Cursor IDE's Background Composer (cloud agent) feature. The system allows users to configure, capture, and restore development environment snapshots for cloud-based AI agent execution.

## Key Components

### 1. DevcontainerStartingPoint (Protobuf Message)

**Type Name:** `aiserver.v1.DevcontainerStartingPoint`

**Location:** Lines 337644-337711, 457233-457298

The DevcontainerStartingPoint defines the starting configuration for creating cloud VMs/pods:

```javascript
{
    url: "",                                    // Repository URL
    ref: "",                                    // Git reference (branch/commit)
    userExtensions: [],                         // Array of user extensions to install
    cursorServerCommit: "",                     // Cursor server version commit
    environmentJsonOverride: "",                // Override for environment.json
    gitDiffToApply: undefined,                  // Git diff message (for Dockerfile changes)
    dontAllowReadingEnvironmentJsonFromDatabase: false,  // Skip DB lookup
    skipBuildCaches: false                      // Force fresh builds
}
```

**Field Definitions:**
| Field No | Name | Type | Purpose |
|----------|------|------|---------|
| 1 | url | string | Git repository URL |
| 2 | ref | string | Git reference (branch/commit/tag) |
| 4 | user_extensions | repeated string | List of VS Code extensions |
| 5 | cursor_server_commit | string | Cursor server version |
| 6 | environment_json_override | string | JSON override for environment config |
| 8 | git_diff_to_apply | message | Git diff for applying changes |
| 9 | dont_allow_reading_environment_json_from_database | bool | Skip DB lookup |
| 10 | skip_build_caches | bool | Force fresh build |


### 2. Environment JSON Configuration

**Location:** `.cursor/environment.json` in workspace root

The environment.json file defines the runtime configuration for cloud agents:

```javascript
{
    build: {
        dockerfile: "Dockerfile",   // Path to Dockerfile
        context: "."                // Build context
    },
    snapshot: "snapshot-id",        // Snapshot ID to use (if any)
    install: "npm install",         // Install dependencies script
    start: "npm start",             // Start script
    terminals: [                    // Terminal configurations
        { name: "Dev Server", command: "npm run dev" }
    ]
}
```

**Watcher Implementation:** (Lines 268790-268815)
- Watches `.cursor/environment.json` for changes
- Sets `hasEnvironmentJsonOnDisk` flag in data service
- Auto-detects when file is created/deleted


### 3. Workspace Persistent Data Structure

**Storage Key:** `workbench.backgroundComposer.workspacePersistentData`

**Default Structure:** (Lines 215431-215440)
```javascript
{
    setupPath2: "default",           // Setup path type
    terminals: [],                    // Terminal configurations
    ranTerminalCommands: [],          // Commands already executed
    installScript: "",                // Install script content
    startScript: "",                  // Start script content
    customDockerfileContents: "",     // Custom Dockerfile
    isSideBarExpanded: false,         // UI state

    // Snapshot-related fields (found throughout code):
    vmSnapshotId: undefined,                    // Current snapshot ID
    snapshotUsedForDefaultVMPod: undefined,     // Snapshot for default VM
    defaultVmPod: undefined,                    // Default VM pod info
    testingVmPod: undefined,                    // Testing VM pod info
    currentSetupStep: undefined,                // Setup wizard step
    furthestSetupStep: undefined                // Progress tracking
}
```


### 4. Snapshot API Operations

#### CreateBackgroundComposerPodSnapshotRequest
**Type:** `aiserver.v1.CreateBackgroundComposerPodSnapshotRequest`

```javascript
{
    podId: "",           // Pod to snapshot
    visibility: 0,       // Visibility enum (see below)
    bcId: undefined      // Optional background composer ID
}
```

#### CreateBackgroundComposerPodSnapshotResponse
```javascript
{
    snapshotId: ""       // Created snapshot ID
}
```

#### Snapshot Visibility Enum
```javascript
const Visibility = {
    UNSPECIFIED: 0,          // "VISIBILITY_UNSPECIFIED"
    USER: 1,                 // "VISIBILITY_USER" - Private to user
    REPO_READ_WRITE: 2,      // "VISIBILITY_REPO_READ_WRITE" - Shared with repo collaborators
    PUBLIC: 4                // "VISIBILITY_PUBLIC" - Publicly accessible
};
```

#### ChangeBackgroundComposerSnapshotVisibilityRequest
```javascript
{
    snapshotId: "",
    visibility: 0,      // Visibility enum
    repoUrl: ""         // Required for REPO_READ_WRITE
}
```

#### GetBackgroundComposerSnapshotInfoRequest/Response
```javascript
// Request
{ snapshotId: "" }

// Response
{
    snapshotId: "",
    visibility: 0,
    repoUrl: "",
    createdAtMs: 0      // Unix timestamp in milliseconds
}
```


### 5. Container Initialization Flow

#### Step 1: Generate DevContainerStartingPoint
(Lines 1142827-1142862)

```javascript
async createDefaultVmPodAndSave(e) {
    const o = await this.generateDevContainerStartingPoint({
        gitState: {
            autoBranch: true,
            ref: currentBranch || "main",
            continueRef: currentBranch || "main",
            baseRef: undefined
        }
    });

    // Apply snapshot if available
    if (workspacePersistentData.snapshotUsedForDefaultVMPod) {
        a.snapshot = workspacePersistentData.snapshotUsedForDefaultVMPod;
    }

    // Set environment JSON override
    o.environmentJsonOverride = JSON.stringify(a);

    // Create pod
    const h = await s.createBackgroundComposerPod({
        devcontainerStartingPoint: o,
        includeSecrets: false,
        forceCluster: forcedCluster
    });

    return { id: h.podId, workspaceRootPath: h.workspaceRootPath };
}
```

#### Step 2: VM Pod Creation Request
**Type:** `aiserver.v1.CreateBackgroundComposerPodRequest`

```javascript
{
    devcontainerStartingPoint: DevcontainerStartingPoint,
    includeSecrets: false,
    forceCluster: undefined,        // Optional cluster override
    forceMachineTemplate: undefined, // Optional machine template
    clientIp: undefined,            // Client IP for routing
    optimisticPrewarming: false     // Pre-warm optimization
}
```

**Response:** `aiserver.v1.CreateBackgroundComposerPodResponse`
```javascript
{
    podId: "",              // Created pod ID
    workspaceRootPath: ""   // Workspace root in container
}
```


### 6. Snapshot Creation Flow

(Lines 1142946-1143018)

```javascript
async takeSnapshotOfDefaultVMPod() {
    this.setData({ isTakingSnapshot: true });

    try {
        const client = await this.aiService.backgroundComposerClient();
        const pod = this.workspacePersistentData.defaultVmPod;

        // Determine visibility based on environment.json location
        const visibility = this.data.hasEnvironmentJsonOnDisk
            ? Visibility.REPO_READ_WRITE
            : Visibility.USER;

        const response = await client.createBackgroundComposerPodSnapshot({
            podId: pod.id,
            visibility: visibility
        });

        // Notify window of success
        this.runActionInWindow({
            windowId: this._defaultVmPodWindowId,
            actionId: "showSnapshotNotification",
            args: { success: true, message: "Snapshot saved successfully." }
        });

        return response.snapshotId;
    } finally {
        this.setData({ isTakingSnapshot: false });
    }
}
```


### 7. Snapshot Restoration Flow

#### StartBackgroundComposerFromSnapshotRequest
**Type:** `aiserver.v1.StartBackgroundComposerFromSnapshotRequest`

Key fields:
```javascript
{
    snapshotNameOrId: "",                    // Snapshot identifier
    devcontainerStartingPoint: {},           // DevcontainerStartingPoint
    prompt: "",                              // Initial prompt
    richPrompt: "",                          // Rich text prompt
    files: [],                               // File attachments
    modelDetails: {},                        // Model configuration
    repositoryInfo: {},                      // Repository metadata
    snapshotWorkspaceRootPath: "",           // Workspace path in snapshot
    autoBranch: false,                       // Auto-create branch
    returnImmediately: false,                // Async start
    forceVmBackend: undefined,               // Backend override
    forceCluster: undefined,                 // Cluster override
    forceMachineTemplate: undefined,         // Machine template
    conversationHistory: [],                 // Previous messages
    documentationIdentifiers: [],            // Doc references
    useWeb: undefined,                       // Web search enabled
    externalLinks: [],                       // External link references
    bcId: "",                                // Background composer ID
    slackChannelId: undefined,               // Slack integration
    linearIssueId: undefined,                // Linear integration
    githubIssueId: undefined,                // GitHub issue integration
    baseBranch: undefined,                   // Base branch for PR
    customBranchName: undefined,             // Custom branch name
    grindModeConfig: undefined               // Grind mode settings
}
```


### 8. External Snapshot Structure (anyrun.v1)

**Type:** `anyrun.v1.ExternalSnapshot`

```javascript
{
    snapshotId: "",
    presignedUrl: "",                        // S3/blob presigned URL
    blobStorageFormat: 0                     // Storage format enum
}
```

**Blob Storage Format Enum:**
```javascript
{
    LEGACY_UNSPECIFIED: 0,    // "BLOB_STORAGE_FORMAT_LEGACY_UNSPECIFIED"
    V1: 1                     // "BLOB_STORAGE_FORMAT_V1"
}
```


### 9. DevContainerConfig (anyrun.v1)

**Type:** `anyrun.v1.DevContainerConfig`

Full container configuration:
```javascript
{
    source: { case: undefined },             // Git or tar source
    image: { case: undefined },              // Docker image config
    workspace: { case: undefined },          // Workspace setup
    prepareCommands: [],                     // Pre-install commands
    installCommands: [],                     // Install commands
    verifyCommands: [],                      // Verification commands
    startCommands: [],                       // Startup commands
    ports: [],                               // Port mappings
    env: [],                                 // Environment variables
    shell: ""                                // Default shell
}
```


### 10. UI Environment State Detection

(Lines 901730-901746)

```javascript
function _Jf(i) {
    const baseEnvironmentState = computed(() => {
        const env = i.environmentJson();
        if (!env) return "none";

        const hasDockerfile = !!env.build?.dockerfile;

        if (env.snapshot) return "snapshot";
        if (hasDockerfile) return "dockerfile";
        return "none";
    });

    const snapshotId = computed(() => i.environmentJson()?.snapshot);

    const dockerFileURI = computed(() => {
        const env = i.environmentJson();
        if (env?.build?.dockerfile) {
            return URI.joinPath(i.rootPath(), ".cursor", "Dockerfile");
        }
    });

    return { baseEnvironmentState, dockerFileURI, snapshotId };
}
```


### 11. Setup Workflow Steps

The setup wizard guides users through environment configuration:

**Default Path Steps:**
1. `connect-github` - GitHub authentication
2. `start-default-vm` - Boot and configure VM
3. `review-settings` - Configure install/start scripts
4. `final-testing` - Validate environment

**V2 Path Steps (feature-gated):**
1. `connect-github` - GitHub authentication
2. `add-environment-variables` - Environment setup
3. `install-dependencies` - Dependency installation
4. `maintain-dependencies` - Dependency maintenance
5. `set-start-commands` - Configure startup

**Reset Function:** (Lines 1142798-1142826)
```javascript
resetSetup() {
    this.setWorkspacePersistentData({
        setupPath2: "default",
        installScript: "",
        startScript: "",
        terminals: [],
        vmSnapshotId: undefined,
        currentSetupStep: undefined,
        furthestSetupStep: undefined,
        defaultVmPod: undefined,
        testingVmPod: undefined,
        customDockerfileContents: "",
        ranTerminalCommands: [],
        isSetupExited: undefined
    });
}
```


## gRPC Service Methods

**Service:** BackgroundComposer (within aiserver.v1)

| Method | Type | Request | Response |
|--------|------|---------|----------|
| CreateBackgroundComposerPod | Unary | CreateBackgroundComposerPodRequest | CreateBackgroundComposerPodResponse |
| AttachBackgroundComposerPod | ServerStreaming | AttachBackgroundComposerPodRequest | AttachBackgroundComposerPodResponse |
| CreateBackgroundComposerPodSnapshot | Unary | CreateBackgroundComposerPodSnapshotRequest | CreateBackgroundComposerPodSnapshotResponse |
| ChangeBackgroundComposerSnapshotVisibility | Unary | ChangeBackgroundComposerSnapshotVisibilityRequest | ChangeBackgroundComposerSnapshotVisibilityResponse |
| GetBackgroundComposerSnapshotInfo | Unary | GetBackgroundComposerSnapshotInfoRequest | GetBackgroundComposerSnapshotInfoResponse |
| StartBackgroundComposerFromSnapshot | Unary | StartBackgroundComposerFromSnapshotRequest | StartBackgroundComposerFromSnapshotResponse |
| SetPersonalEnvironmentJson | Unary | SetPersonalEnvironmentJsonRequest | SetPersonalEnvironmentJsonResponse |
| GetPersonalEnvironmentJson | Unary | GetPersonalEnvironmentJsonRequest | GetPersonalEnvironmentJsonResponse |
| ListPersonalEnvironments | Unary | ListPersonalEnvironmentsRequest | ListPersonalEnvironmentsResponse |


## Storage Mechanisms

### Local Storage
- **Key:** `workbench.backgroundComposer.workspacePersistentData`
- **Scope:** Workspace-specific (Storage Scope = 1)
- **Format:** JSON serialized

### Persistent Data
- **Key:** `workbench.backgroundComposer.persistentData`
- **Scope:** Application-wide (Storage Scope = -1)
- **Contains:** `lastOpenedBcIds`, `dataVersion`


## Feature Gates

- `cloud_agent_setup_v2` - Enables V2 setup workflow
- `cloud_agent_enable_blob_storage_format_v1` - New blob storage format


## Key Findings

1. **Snapshot Lifecycle:**
   - Snapshots are created from running pods
   - Can be private (USER), repo-shared (REPO_READ_WRITE), or public
   - Stored with presigned URLs for blob storage access
   - Support both legacy and V1 blob storage formats

2. **Environment Configuration Hierarchy:**
   - `.cursor/environment.json` file on disk takes priority
   - Falls back to database-stored configuration
   - Can be overridden via `environmentJsonOverride` field

3. **Pod Types:**
   - Default VM Pod: Used for setup and testing
   - Testing VM Pod: Exact copy of production environment
   - Both can have snapshots taken

4. **Integration Points:**
   - GitHub (for repo access and visibility sharing)
   - Slack (for async notifications)
   - Linear (for issue tracking)
   - Custom webhooks (for automation)


## Related Files

- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
  - Lines 268764-268861: BackgroundComposerDataService
  - Lines 336158-336539: Snapshot protobuf definitions
  - Lines 337644-337711: DevcontainerStartingPoint definition
  - Lines 901550-901828: Snapshot UI components
  - Lines 1142798-1143095: VM pod creation and snapshot logic
  - Lines 1153900-1155782: Setup workflow implementation


## Investigation Leads

1. **Blob Storage Details:** The V1 blob storage format appears to be newer - investigate how it differs from legacy format
2. **Cluster Routing:** The `forceCluster` field suggests multi-region deployment - see TASK-24-geographic-routing.md
3. **GrindModeConfig:** Mentioned in snapshot request - may relate to extended execution modes
4. **Personal Environment Storage:** SetPersonalEnvironmentJson API suggests per-user environment configuration
