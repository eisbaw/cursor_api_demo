# TASK-73: Path Encryption Key Usage in Shadow Workspace and VM Daemon Sync

## Overview

This analysis examines how path encryption keys are used in Cursor IDE 2.3.41 to protect file paths when syncing data between the local editor, shadow workspaces, and cloud-based VM daemons. The encryption system enables Cursor to obfuscate local file system paths before transmitting them to remote services.

## Key Findings

### 1. Path Encryption Key Data Structures

#### RepositoryIndexingInfo (agent.v1.RepositoryIndexingInfo)
Location: Line 119147-119225 (`out-build/proto/agent/v1/repo_pb.js`)

```javascript
this.relativeWorkspacePath = ""
this.remoteUrls = []
this.remoteNames = []
this.repoName = ""
this.repoOwner = ""
this.isTracked = !1
this.isLocal = !1
this.workspaceUri = ""
this.pathEncryptionKey = ""  // Field no: 10
```

The `pathEncryptionKey` is a per-repository string stored alongside repository metadata including remote URLs, repo name/owner, and workspace URI.

#### SyncIndexRequest (aiserver.v1.SyncIndexRequest)
Location: Line 830795-830846

```javascript
this.rootPath = ""
this.pathEncryptionKey = ""
// Fields: root_path, repository_info, path_encryption_key, indexing_progress_threshold, async
```

Used by the VmDaemonService.syncIndex method to synchronize the index with a path encryption key.

#### SwSyncIndexRequest (aiserver.v1.SwSyncIndexRequest)
Location: Line 121455-121495

```javascript
this.pathEncryptionKey = ""
// Fields: repository_info, path_encryption_key, indexing_progress_threshold
```

Shadow workspace variant of the sync index request.

### 2. Key Source: Server Configuration

The path encryption keys are server-provisioned, not locally generated:

Location: Line 1144217-1144230

```javascript
var uLu = new Yru({
    maxConcurrentUploads: 50,
    absoluteMaxNumberFiles: 1e5,
    // ... other config
    defaultTeamPathEncryptionKey: $Ut,  // placeholder: "not a real key"
    defaultUserPathEncryptionKey: $Ut,  // placeholder: "not a real key"
    // ...
});
```

The placeholder value `$Ut = "not a real key"` (line 268991) indicates keys are meant to be replaced by actual server-provided values.

#### Key Update Logging
Location: Line 1144265

```javascript
t.indexingConfig?.defaultUserPathEncryptionKey === $Ut &&
n.indexingConfig &&
n.indexingConfig.defaultUserPathEncryptionKey !== $Ut &&
console.log("defaultUserPathEncryptionKey updated from placeholder key")
```

The system logs when the encryption key transitions from placeholder to actual server-provided key.

### 3. Key Sharing Between Contexts

#### Repository Service Key Management
Location: Lines 441169-441183

```javascript
async getPathEncryptionKey() {
    const e = Date.now();
    // Wait up to 5 seconds for indexing provider
    for (; !this.indexingProvider && Date.now() - e < 5e3;)
        await new Promise(t => setTimeout(t, 100));
    return await this.indexingProvider?.getPathEncryptionKey()
}

getOverridePathEncryptionKey(e) {
    const t = this.getQueryOnlyIndex();
    if (t !== void 0 && e.repoName === t.repositoryInfo.repoName &&
        e.repoOwner === t.repositoryInfo.repoOwner)
        return t.pathEncryptionKey
}
```

Key observations:
- Keys are obtained from the indexing provider
- Override keys can be specified per-repository for query-only indexes
- Repository name/owner matching determines which key to use

#### Background Composer Repository Info Retrieval
Location: Lines 1141394-1141403

```javascript
const n = await (await this.aiService.backgroundComposerClient())
    .getBackgroundComposerRepositoryInfo({ bcId: e });
n.repositoryInfo !== void 0 &&
n.pathEncryptionKey !== void 0 &&
n.queryOnlyRepoAccess !== void 0 &&
this.repositoryService.setQueryOnlyIndex({
    pathEncryptionKey: n.pathEncryptionKey,
    repositoryInfo: n.repositoryInfo,
    queryOnlyRepoAccess: n.queryOnlyRepoAccess
})
```

Background composers retrieve encryption keys from the cloud service along with repository info and access permissions.

#### Window-to-Window Key Sharing
Location: Lines 1143650-1143666

```javascript
async setQueryOnlyRepoInfoInsideWindow(e) {
    const t = await this.repositoryService.getNewRepoInfo();
    if (!t) return;
    const n = await this.repositoryService.getPathEncryptionKey(),
        s = await this.repositoryService.getRepoAuthId();
    await this.nativeHostService.runActionInWindow({
        windowId: e.windowId,
        actionId: bwr,
        args: {
            queryOnlyRepositoryInfo: await (async () => ({
                repositoryInfo: t,
                pathEncryptionKey: n,
                queryOnlyRepoAccess: new R7e({
                    ownerAuthId: s
                })
            }))()
        }
    })
}
```

Encryption keys are shared between editor windows using the native host IPC mechanism.

### 4. Encrypt/Decrypt Path Operations

#### Indexing Provider Interface
Location: Lines 831967-831982

```javascript
h = () => this._proxy.$getIndexProviderGetPathEncryptionKey(),
f = w => this._proxy.$getIndexProviderEncryptPaths(w),
g = w => this._proxy.$getIndexProviderDecryptPaths(w),
p = w => this._proxy.$getIndexProviderCompileGlobFilter(w);

this.repositoryService.registerIndexingProvider({
    getPathEncryptionKey: h,
    encryptPaths: f,
    decryptPaths: g,
    compileGlobFilter: p,
    // ...
})
```

The indexing provider offers:
- `encryptPaths`: Encrypt an array of paths
- `decryptPaths`: Decrypt an array of paths
- `compileGlobFilter`: Compile glob patterns with encryption key support

#### Path Decryption in Code Search Results
Location: Lines 441575-441583

```javascript
async getFinalCodeResults(e, t, n) {
    if (!this.indexingProvider) throw new Error("Indexing provider not found");
    const s = t.map(h => h.codeBlock?.relativeWorkspacePath).filter(h => h !== void 0),
        r = await this.indexingProvider.decryptPaths({
            paths: s,
            overridePathEncryptionKey: this.getOverridePathEncryptionKey(e)
        }),
        o = new Map;
    for (let h = 0; h < s.length; h++) o.set(s[h], r[h]);
    // ...
}
```

When code search results return encrypted paths, they are decrypted locally using the override key for the specific repository.

### 5. VM Daemon Service Integration

#### VmDaemonService Definition
Location: Line 831474-831570

```javascript
var oou = {
    typeName: "aiserver.v1.VmDaemonService",
    methods: {
        syncIndex: {
            name: "SyncIndex",
            I: u4f,  // SyncIndexRequest with pathEncryptionKey
            O: d4f,
            kind: Kt.Unary
        },
        compileRepoIncludeExcludePatterns: {
            name: "CompileRepoIncludeExcludePatterns",
            I: e4f,
            O: t4f,
            kind: Kt.Unary
        },
        // ... other methods: exec, readTextFile, writeTextFile, etc.
    }
};
```

The VM daemon sync includes the path encryption key in the sync request, enabling the remote VM to work with encrypted paths.

### 6. Shadow Workspace Service Integration

#### ShadowWorkspaceService Definition
Location: Line 809709-809712

```javascript
var EKt = {
    typeName: "aiserver.v1.ShadowWorkspaceService",
    methods: {
        getLintsForChange: {
            name: "GetLintsForChange",
            // ...
        }
    }
};
```

#### Shadow Workspace Server Integration
Location: Lines 1128709-1128733

```javascript
this.repositoryService.syncIndexWithGivenRepositoryInfo({
    repositoryInfo: {
        ...e.repositoryInfo
    },
    pathEncryptionKey: e.pathEncryptionKey
});

// Compile glob filters with encryption
const t = await this.repositoryService.compileGlobFilterFromPattern({
    includePattern: e.includePattern,
    excludePattern: e.excludePattern,
    repoInfo: e.repositoryInfo,
    overridePathEncryptionKey: e.pathEncryptionKey
});
```

Shadow workspaces receive the path encryption key and use it when syncing indexes and compiling file filters.

### 7. Headless Agentic Composer Repository Info

#### HeadlessAgenticComposerRepositoryInfo
Location: Lines 339475-339523

```javascript
Vuc = class Rln extends ge {
    repositoryInfo;
    pathEncryptionKey = "";
    repositoryInfoShouldQueryStaging = !1;
    repositoryInfoShouldQueryProd = !1;
    repoQueryAuthToken = "";
    shouldSyncIndex = !1;
    queryOnlyRepoAccess;
    // ...
    static typeName = "aiserver.v1.HeadlessAgenticComposerRepositoryInfo";
}
```

The headless composer transmits path encryption keys alongside repository info, staging/prod query flags, and repo authentication tokens.

### 8. Background Composer Repository Info Protocol

#### GetBackgroundComposerRepositoryInfoRequest/Response
Location: Lines 460103-460173

Request:
```javascript
this.bcId = ""
// typeName: "aiserver.v1.GetBackgroundComposerRepositoryInfoRequest"
```

Response:
```javascript
// typeName: "aiserver.v1.GetBackgroundComposerRepositoryInfoResponse"
// Fields:
//   repository_info (message, field 1)
//   path_encryption_key (scalar string, field 2, optional)
//   query_only_repo_access (message, field 3)
```

The background composer service returns the path encryption key along with repository info and access permissions.

## Architecture Summary

```
+------------------+     +---------------------+     +-------------------+
|  Local Editor    |     |  Shadow Workspace   |     |  Cloud VM Daemon  |
+------------------+     +---------------------+     +-------------------+
        |                         |                          |
        |  pathEncryptionKey      |  pathEncryptionKey       |
        +--------> Encrypt -------+--------> Encrypted ------+
        |         Paths           |         Paths            |
        |                         |                          |
        | <------ Decrypt <-------+<------- Results ---------+
        |         Paths           |                          |
+-------v---------+      +--------v----------+      +--------v----------+
| IndexingProvider|      | ShadowServer      |      | VmDaemonService   |
| - encryptPaths  |      | - syncIndex       |      | - syncIndex       |
| - decryptPaths  |      | - compileGlob     |      | - compilePatterns |
| - compileGlob   |      +-------------------+      +-------------------+
+-----------------+
```

## Key Flow

1. **Initialization**: Server configuration provides default encryption keys
2. **Authentication**: Keys may be updated based on user/team authentication
3. **Sync**: Index sync requests include the encryption key
4. **Query**: Code search results return encrypted paths
5. **Decryption**: Local editor decrypts paths for display
6. **Sharing**: Keys shared between windows and background composers

## Security Observations

1. **Placeholder Detection**: The system has explicit checks for placeholder keys (`"not a real key"`)
2. **Server-Provisioned**: Keys come from server configuration, not local generation
3. **Per-Repository Override**: Different repositories can have different encryption keys
4. **Access Control**: Keys are tied to repository access permissions (`queryOnlyRepoAccess`)
5. **Team vs User Keys**: Separate defaults for team and user path encryption

## Potential Investigation Areas

1. **Key Generation Algorithm**: How are actual encryption keys generated server-side?
2. **Encryption Algorithm**: What cipher/algorithm is used for path encryption?
3. **Key Rotation**: Are there mechanisms for rotating encryption keys?
4. **Recovery**: How does the system handle key mismatches or missing keys?
5. **Team Key Propagation**: How are team keys distributed to team members?
