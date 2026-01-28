# TASK-35: Path Encryption Algorithm and encrypted_relative_path Field Population

## Executive Summary

This analysis investigates how Cursor IDE encrypts file paths before sending them to backend servers, specifically focusing on the `encrypted_relative_path` field in protobuf messages. The key finding is that **the actual encryption algorithm is implemented in native code within the extension host process**, making the cryptographic implementation not directly visible in the JavaScript bundle.

The encryption follows a **proxy-based architecture** where:
1. The server provides encryption keys via `GetServerConfig`
2. The JavaScript layer calls into native code via IPC
3. Native code performs actual encryption/decryption
4. Encrypted paths are transmitted to/from the server

## 1. Key Sources and Distribution

### 1.1 Placeholder Key (Client Default)

The client starts with a placeholder encryption key defined at line 268991:

```javascript
$Ut = "not a real key"
```

This placeholder is used in the default IndexingConfig at line 1144226-1144227:

```javascript
{
    defaultTeamPathEncryptionKey: $Ut,
    defaultUserPathEncryptionKey: $Ut,
    maxBatchBytes: 2 * 1024 * 1024,
    // ...
}
```

### 1.2 Server-Provided Keys

The real encryption keys are provided by the server via the `IndexingConfig` protobuf message (line 826704-826713):

```javascript
{
    no: 9,
    name: "default_user_path_encryption_key",
    kind: "scalar",
    T: 9,  // string
    opt: true
},
{
    no: 10,
    name: "default_team_path_encryption_key",
    kind: "scalar",
    T: 9,  // string
    opt: true
}
```

When the server provides the real key, the client logs the update (line 1144265):

```javascript
t.indexingConfig?.defaultUserPathEncryptionKey === $Ut &&
n.indexingConfig &&
n.indexingConfig.defaultUserPathEncryptionKey !== $Ut &&
console.log("defaultUserPathEncryptionKey updated from placeholder key")
```

### 1.3 Repository-Specific Keys

Each repository can have its own encryption key, stored in `RepositoryIndexingInfo` (line 119149):

```javascript
class RepositoryIndexingInfo {
    relativeWorkspacePath = "";
    remoteUrls = [];
    remoteNames = [];
    repoName = "";
    repoOwner = "";
    isTracked = false;
    isLocal = false;
    workspaceUri = "";
    pathEncryptionKey = "";  // Per-repo encryption key
}
```

### 1.4 Override Keys for Query-Only Repositories

For query-only (read-only) repositories, an override key mechanism exists (line 441181-441184):

```javascript
getOverridePathEncryptionKey(e) {
    const t = this.getQueryOnlyIndex();
    if (t !== void 0 && e.repoName === t.repositoryInfo.repoName &&
        e.repoOwner === t.repositoryInfo.repoOwner)
        return t.pathEncryptionKey
}
```

## 2. Protobuf Messages Using encrypted_relative_path

### 2.1 LocalCodebaseFileInfo (Merkle Tree File Sync)

**Location:** Line 98024-98070 (aiserver.v1.LocalCodebaseFileInfo)

```javascript
class LocalCodebaseFileInfo {
    encryptedRelativePath = "";  // Encrypted path segment
    hash = "";                   // Content hash
    children = [];               // Child nodes (recursive)
    separator = "";              // Path separator (optional)
}
```

**Purpose:** Used in merkle tree-based file synchronization to represent the file hierarchy while keeping paths encrypted.

### 2.2 GitGraphCommitFile (Git History)

**Location:** Line 821461-821497 (aiserver.v1.GitGraphCommitFile)

```javascript
class GitGraphCommitFile {
    deletions = 0;
    additions = 0;
    status = LKt.UNSPECIFIED;  // ADDED, DELETED, MODIFIED, RENAMED
    encryptedFromRelativePath = "";  // Source path (for renames)
    encryptedToRelativePath = "";    // Destination path (for renames)
}
```

**Purpose:** Represents files in git commit history with encrypted paths for privacy.

### 2.3 GetGitGraphRelatedFilesRequest

**Location:** Line 821641-821680 (aiserver.v1.GetGitGraphRelatedFilesRequest)

```javascript
class GetGitGraphRelatedFilesRequest {
    workspaceId = "";
    encryptedRelativePath = "";  // Query path (encrypted)
    maxNumFiles = 0;
}
```

**Purpose:** Request to find files related to a specific file based on git history.

### 2.4 GitGraphRelatedFile (Response)

**Location:** Line 821719-821752 (aiserver.v1.GitGraphRelatedFile)

```javascript
class GitGraphRelatedFile {
    encryptedRelativePath = "";  // Related file path (encrypted)
    weight = 0;                  // Relevance weight
}
```

**Purpose:** Response containing related files with their encrypted paths.

## 3. The Encryption/Decryption Flow

### 3.1 Architecture Diagram

```
+-------------------------------------------------------------------+
|                        JavaScript Layer                             |
+-------------------------------------------------------------------+
|                                                                     |
|   RepositoryService                  IndexingProvider (Interface)   |
|   +-----------------------+          +---------------------------+  |
|   | getPathEncryptionKey()|--------->| getPathEncryptionKey()    |  |
|   | getOverrideKey()      |          | encryptPaths({paths, key})|  |
|   | getFinalCodeResults() |<---------| decryptPaths({paths, key})|  |
|   +-----------------------+          | compileGlobFilter()       |  |
|                                      +---------------------------+  |
|                                              |                      |
|                                              | IPC Proxy            |
|                                              v                      |
+-------------------------------------------------------------------+
|                     Extension Host Process                          |
+-------------------------------------------------------------------+
|                                                                     |
|   $getIndexProviderEncryptPaths(paths) --> _indexProvider.encrypt() |
|   $getIndexProviderDecryptPaths(paths) --> _indexProvider.decrypt() |
|   $getIndexProviderGetPathEncryptionKey() --> returns key           |
|                                                                     |
|                   [NATIVE ENCRYPTION IMPLEMENTATION]                |
|                                                                     |
+-------------------------------------------------------------------+
                              |
                              | HTTPS + Protobuf
                              v
+-------------------------------------------------------------------+
|                         Server Side                                 |
+-------------------------------------------------------------------+
|   - Receives encrypted paths                                        |
|   - Stores in index with encrypted paths                            |
|   - Returns encrypted paths in search results                       |
|   - Has decryption key (key escrow model)                           |
+-------------------------------------------------------------------+
```

### 3.2 Key Retrieval Function

**Location:** Line 441169-441172

```javascript
async getPathEncryptionKey() {
    const e = Date.now();
    // Wait up to 5 seconds for indexing provider to be ready
    for (; !this.indexingProvider && Date.now() - e < 5e3;)
        await new Promise(t => setTimeout(t, 100));
    return await this.indexingProvider?.getPathEncryptionKey()
}
```

### 3.3 Decryption Example (Search Results)

**Location:** Line 441575-441600 (getFinalCodeResults)

```javascript
async getFinalCodeResults(e, t, n) {
    if (!this.indexingProvider) throw new Error("Indexing provider not found");

    // Extract encrypted paths from search results
    const s = t.map(h => h.codeBlock?.relativeWorkspacePath)
               .filter(h => h !== void 0),

    // Call native decryption
    r = await this.indexingProvider.decryptPaths({
        paths: s,
        overridePathEncryptionKey: this.getOverridePathEncryptionKey(e)
    }),

    // Map encrypted -> decrypted
    o = new Map;
    for (let h = 0; h < s.length; h++)
        o.set(s[h], r[h]);

    // Replace encrypted paths in results with decrypted paths
    // ...
}
```

### 3.4 IPC Proxy Registration

**Location:** Line 831957-831985

```javascript
async $registerIndexProvider() {
    const e = () => this._proxy.$getIndexProviderGetGlobalStatus(),
          // ... other methods
          h = () => this._proxy.$getIndexProviderGetPathEncryptionKey(),
          f = w => this._proxy.$getIndexProviderEncryptPaths(w),
          g = w => this._proxy.$getIndexProviderDecryptPaths(w),
          p = w => this._proxy.$getIndexProviderCompileGlobFilter(w);

    this.repositoryService.registerIndexingProvider({
        getGlobalStatus: e,
        // ...
        getPathEncryptionKey: h,
        encryptPaths: f,
        decryptPaths: g,
        compileGlobFilter: p,
        // ...
    })
}
```

## 4. Path Key Hash Verification

The server uses path key hashes to verify key consistency:

### 4.1 PathKeyHashType Enum

**Location:** Line 97659-97665

```javascript
(function(i) {
    i[i.UNSPECIFIED = 0] = "UNSPECIFIED",
    i[i.SHA256 = 1] = "SHA256"
})(I7e || (I7e = {}))
```

### 4.2 Usage in Repository Handshake

**Location:** Line 98073 (FastRepoInitHandshakeV2Request)

```javascript
{
    rootHash: "",
    similarityMetricType: T7e.UNSPECIFIED,
    similarityMetric: [],
    pathKeyHash: "",           // SHA256 hash of encryption key
    pathKeyHashType: I7e.UNSPECIFIED,  // SHA256 or UNSPECIFIED
    doCopy: false,
    pathKey: "",               // Actual key (for verification)
    returnAfterBackgroundCopyStarted: false
}
```

This allows the server to:
1. Verify client has correct encryption key
2. Detect key rotation/mismatch scenarios
3. Ensure encryption consistency across sessions

## 5. When Paths Are Encrypted vs Plaintext

### 5.1 Encrypted (Sent to Server)

| Message Type | Field | Purpose |
|-------------|-------|---------|
| LocalCodebaseFileInfo | encrypted_relative_path | Merkle tree sync |
| GitGraphCommitFile | encrypted_from_relative_path | Git history |
| GitGraphCommitFile | encrypted_to_relative_path | Git renames |
| GetGitGraphRelatedFilesRequest | encrypted_relative_path | Related files query |
| GitGraphRelatedFile | encrypted_relative_path | Related files response |
| Search results | relativeWorkspacePath (code blocks) | Code search |

### 5.2 Plaintext (Specific Operations)

| Message Type | Field | Purpose |
|-------------|-------|---------|
| FastUpdateFileRequest.LocalFile | unencrypted_relative_workspace_path | File updates |
| FastUpdateFileV2Request.LocalFile | unencrypted_relative_workspace_path | File updates v2 |

The unencrypted fields appear to be used for operations where the server needs to perform path-based operations (like validation or routing) without decryption overhead.

## 6. Security Analysis

### 6.1 Key Escrow Model

**Critical Finding:** The server possesses the encryption keys (via `GetServerConfig` distribution). This is a **key escrow** model, not end-to-end encryption:

- Server can decrypt all paths
- Privacy protection is against casual interception, not Cursor
- Useful for transit security, not data-at-rest privacy from provider

### 6.2 Algorithm Unknown

The actual encryption algorithm is implemented in native code and is not visible in the JavaScript bundle. Likely candidates:
- AES-GCM (most common for string encryption)
- AES-CBC with HMAC
- ChaCha20-Poly1305

### 6.3 Per-Repository Keys

The existence of per-repository keys (`pathEncryptionKey` in RepositoryIndexingInfo) suggests:
- Different workspaces can have isolated encryption
- Team vs user key distinction (defaultTeamPathEncryptionKey vs defaultUserPathEncryptionKey)
- Possible key rotation support

## 7. Extension Host Implementation

**Location:** extensionHostProcess.js (minified)

The extension host provides the IPC endpoints:

```javascript
$getIndexProviderEncryptPaths(s) {
    return this._indexProvider ?
        this._indexProvider.encryptPaths(s) :
        Promise.resolve(s.paths)  // Fallback: return unencrypted
}

$getIndexProviderDecryptPaths(s) {
    return this._indexProvider ?
        this._indexProvider.decryptPaths(s) :
        Promise.resolve(s.paths)  // Fallback: return as-is
}
```

**Important:** If no index provider is registered, paths are passed through unencrypted. This is a fallback behavior, not the normal operation.

## 8. Related Protobuf Messages for Context

### 8.1 IndexingConfig Fields (Full List)

**Location:** Line 826650-826746

```javascript
// Fields relevant to path encryption
{
    no: 9,  name: "default_user_path_encryption_key", kind: "scalar", T: 9, opt: true
},
{
    no: 10, name: "default_team_path_encryption_key", kind: "scalar", T: 9, opt: true
},
// Other indexing config fields
{
    no: 1,  name: "indexing_period_seconds", kind: "scalar", T: 5
},
{
    no: 2,  name: "sync_concurrency", kind: "scalar", T: 5
},
{
    no: 3,  name: "auto_indexing_max_num_files", kind: "scalar", T: 5
},
{
    no: 7,  name: "repo42_auth_token", kind: "scalar", T: 9
},
{
    no: 11, name: "multi_root_indexing_enabled", kind: "scalar", T: 8, opt: true
}
```

### 8.2 RootPath Request Message

**Location:** Line 830794-830821 (u4f/gBn)

```javascript
class SomeRootPathRequest {
    rootPath = "";
    pathEncryptionKey = "";  // Key for this specific request
    // Repository info and other fields...
}
```

This shows path encryption key being passed with individual requests.

## 9. Summary of Findings

### What We Know

1. **Key Source:** Server provides encryption keys via GetServerConfig, with fallback placeholder "not a real key"
2. **Key Types:** User-level, team-level, and per-repository keys exist
3. **Verification:** SHA256 hash of key used for consistency checks
4. **Architecture:** Native code implementation via IPC proxy pattern
5. **Usage:** Multiple protobuf messages use encrypted_relative_path fields
6. **Fallback:** If no IndexProvider registered, paths pass through unencrypted

### What We Don't Know

1. **Algorithm:** Specific encryption algorithm (likely AES variant)
2. **Mode:** Cipher mode (GCM, CBC, CTR, etc.)
3. **IV/Nonce:** How initialization vectors are generated/managed
4. **Key Derivation:** Whether HKDF, PBKDF2, or direct key usage
5. **Encoding:** Output encoding (base64, hex, custom)

### Privacy Implications

- **Not E2E Encrypted:** Server has keys, can decrypt paths
- **Transit Protection:** Protects paths during network transmission
- **Obfuscation:** Prevents casual path reading in logs/network traces
- **Team Isolation:** Per-team keys could isolate team path visibility

## 10. Recommendations for Further Investigation

1. **Native Code Analysis:** Analyze the Cursor native extensions (.node files) for actual algorithm
2. **Network Traffic Capture:** Examine encrypted path format to identify encoding/structure
3. **Key Rotation:** Investigate key lifecycle and rotation mechanisms
4. **Cross-Reference TASK-92:** See related analysis for additional context

---

**Related Analysis:** TASK-92-path-encryption.md contains additional architectural details about the proxy-based encryption flow.
