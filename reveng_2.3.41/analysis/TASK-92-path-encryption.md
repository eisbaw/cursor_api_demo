# TASK-92: Path Encryption Algorithm Implementation Analysis

## Executive Summary

Path encryption in Cursor IDE is implemented through a **proxy-based architecture** where the actual encryption/decryption happens in the extension host process (native code), not in the visible JavaScript bundle. The client JavaScript code only calls into this native layer via IPC proxy methods.

**Key Finding:** The encryption algorithm implementation is **NOT visible** in the decompiled JavaScript. It resides in the native extension host, likely in compiled Node.js native addon code (.node files) or within the bundled `extensionHostProcess.js`.

## 1. Architecture Overview

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Client Side                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────────┐        ┌─────────────────────────────────┐   │
│   │  RepositoryService  │ ──────>│     IndexingProvider (Proxy)    │   │
│   │    (JS/Browser)     │        │     encryptPaths()              │   │
│   │                     │<────── │     decryptPaths()              │   │
│   └─────────────────────┘        │     getPathEncryptionKey()      │   │
│                                  └─────────────────────────────────┘   │
│                                              │                          │
│                                              │ IPC Proxy                │
│                                              ▼                          │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │              ExtensionHost Process (Native Code)                 │  │
│   │    $getIndexProviderEncryptPaths(paths)                         │  │
│   │    $getIndexProviderDecryptPaths(paths)                         │  │
│   │    $getIndexProviderGetPathEncryptionKey()                      │  │
│   │                                                                  │  │
│   │    [ACTUAL ENCRYPTION ALGORITHM - NOT VISIBLE IN JS]            │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTPS + Protobuf
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           Server Side                                    │
├─────────────────────────────────────────────────────────────────────────┤
│   Receives: encrypted_relative_path (string)                            │
│   Stores:   encrypted paths in index                                    │
│   Returns:  encrypted paths in search results                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## 2. Encryption Key Sources

### 2.1 Server-Provided Default Keys (IndexingConfig)

The server provides encryption keys via `GetServerConfig` endpoint:

**Protobuf Definition (line 826658 - aiserver.v1.IndexingConfig):**
```javascript
{
    no: 9,
    name: "default_user_path_encryption_key",
    kind: "scalar",
    T: 9  // string
},
{
    no: 10,
    name: "default_team_path_encryption_key",
    kind: "scalar",
    T: 9  // string
}
```

**Placeholder Value:**
```javascript
$Ut = "not a real key"  // Line 268991
```

The client starts with this placeholder and updates when the server provides a real key:
```javascript
// Line 1144265
t.indexingConfig?.defaultUserPathEncryptionKey === $Ut &&
n.indexingConfig &&
n.indexingConfig.defaultUserPathEncryptionKey !== $Ut &&
console.log("defaultUserPathEncryptionKey updated from placeholder key")
```

### 2.2 Repository-Specific Keys (RepositoryInfo)

Each repository can have its own encryption key:

**Protobuf Definition (line 119155 - agent.v1.RepositoryIndexingInfo):**
```javascript
{
    no: 10,
    name: "path_encryption_key",
    kind: "scalar",
    T: 9  // string
}
```

### 2.3 Override Keys for Query-Only Repositories

```javascript
// Line 441181-441184
getOverridePathEncryptionKey(e) {
    const t = this.getQueryOnlyIndex();
    if (t !== void 0 && e.repoName === t.repositoryInfo.repoName &&
        e.repoOwner === t.repositoryInfo.repoOwner)
        return t.pathEncryptionKey
}
```

## 3. When Paths Are Encrypted vs Plaintext

### Encrypted (Server-Bound)

| Protobuf Message | Field | Usage |
|-----------------|-------|-------|
| `aiserver.v1.LocalCodebaseFileInfo` | `encrypted_relative_path` | Merkle tree file sync |
| `aiserver.v1.GitGraphCommitFile` | `encrypted_from_relative_path` | Git history tracking |
| `aiserver.v1.GitGraphCommitFile` | `encrypted_to_relative_path` | Git history (renames) |
| `aiserver.v1.GetGitGraphRelatedFilesRequest` | `encrypted_relative_path` | Query related files |
| `aiserver.v1.GitGraphRelatedFile` | `encrypted_relative_path` | Related file results |
| Search results (`codeBlock.relativeWorkspacePath`) | Server returns encrypted | Code search results |

### Plaintext (Local Operations)

| Protobuf Message | Field | Usage |
|-----------------|-------|-------|
| `aiserver.v1.FastUpdateFileRequest.LocalFile` | `unencrypted_relative_workspace_path` | File updates |
| `aiserver.v1.FastUpdateFileV2Request.LocalFile` | `unencrypted_relative_workspace_path` | File updates V2 |

## 4. Encryption/Decryption Call Sites

### 4.1 Decryption (Server Results -> Local Paths)

**Location: line 441575-441600 - `getFinalCodeResults()`**

```javascript
async getFinalCodeResults(e, t, n) {
    if (!this.indexingProvider) throw new Error("Indexing provider not found");

    // Extract encrypted paths from server results
    const s = t.map(h => h.codeBlock?.relativeWorkspacePath)
               .filter(h => h !== void 0),

    // Decrypt via native extension
    r = await this.indexingProvider.decryptPaths({
        paths: s,
        overridePathEncryptionKey: this.getOverridePathEncryptionKey(e)
    }),

    // Build decrypted path map
    o = new Map;
    for (let h = 0; h < s.length; h++)
        o.set(s[h], r[h]);

    // Replace encrypted paths with decrypted
    // ... (processing continues)
}
```

### 4.2 IPC Proxy Registration

**Location: line 831957-831985 - `$registerIndexProvider()`**

```javascript
async $registerIndexProvider() {
    const h = () => this._proxy.$getIndexProviderGetPathEncryptionKey(),
          f = w => this._proxy.$getIndexProviderEncryptPaths(w),
          g = w => this._proxy.$getIndexProviderDecryptPaths(w),
          p = w => this._proxy.$getIndexProviderCompileGlobFilter(w);

    this.repositoryService.registerIndexingProvider({
        // ... other methods
        getPathEncryptionKey: h,
        encryptPaths: f,
        decryptPaths: g,
        compileGlobFilter: p,
        // ...
    })
}
```

### 4.3 Key Retrieval

**Location: line 441169-441172 - `getPathEncryptionKey()`**

```javascript
async getPathEncryptionKey() {
    const e = Date.now();
    // Wait up to 5 seconds for indexing provider
    for (; !this.indexingProvider && Date.now() - e < 5e3;)
        await new Promise(t => setTimeout(t, 100));
    return await this.indexingProvider?.getPathEncryptionKey()
}
```

## 5. Path Key Hash Verification

The server uses path key hashes to verify encryption key consistency:

**Protobuf Enum (line 97660 - PathKeyHashType):**
```javascript
(function(i) {
    i[i.UNSPECIFIED = 0] = "UNSPECIFIED",
    i[i.SHA256 = 1] = "SHA256"
})(I7e || (I7e = {}))
```

**Usage in FastRepoInitHandshakeV2Request (line 98073):**
```javascript
{
    rootHash: "",
    similarityMetricType: T7e.UNSPECIFIED,
    similarityMetric: [],
    pathKeyHash: "",        // SHA256 hash of path encryption key
    pathKeyHashType: I7e.UNSPECIFIED,
    doCopy: false,
    pathKey: "",            // Actual path key (for verification)
    returnAfterBackgroundCopyStarted: false
}
```

## 6. Security Observations

### What We Know

1. **Key Distribution:** Server provides default encryption keys via `GetServerConfig`
2. **Key Verification:** SHA256 hash used to verify key consistency with server
3. **Encryption Location:** Happens in native extension host, not visible JS
4. **Bidirectional:** Paths encrypted before sending, decrypted after receiving

### What We Don't Know (Requires Native Code Analysis)

1. **Algorithm:** Likely AES-based but specific mode (GCM, CBC, etc.) unknown
2. **IV Handling:** How initialization vectors are generated/managed
3. **Key Derivation:** Whether raw key is used or derived (HKDF, PBKDF2)
4. **Padding:** Block cipher padding scheme (if not using AEAD mode)

### Privacy Implications

- **Server Can Decrypt:** Server has the encryption key (key escrow model)
- **Purpose:** Prevents casual path reading, not cryptographic privacy
- **Scope:** Only file paths are encrypted, not file contents (contents have different encryption)

## 7. Related Data Structures

### LocalCodebaseFileInfo (Merkle Tree Node)
```javascript
// Line 98024-98057 - aiserver.v1.LocalCodebaseFileInfo
{
    encryptedRelativePath: "",  // Encrypted path segment
    hash: "",                   // Content hash
    children: [],               // Child nodes (recursive)
    separator: ""               // Path separator (optional)
}
```

### GitGraphCommitFile (Git History)
```javascript
// Line 821461-821497 - aiserver.v1.GitGraphCommitFile
{
    deletions: 0,
    additions: 0,
    status: LKt.UNSPECIFIED,  // ADDED, DELETED, MODIFIED, RENAMED
    encryptedFromRelativePath: "",
    encryptedToRelativePath: ""
}
```

## 8. Investigation Recommendations

### High Priority (New Tasks)

1. **TASK-XX:** Analyze native extension host code (`extensionHostProcess.js`) for actual encryption implementation
2. **TASK-XX:** Capture network traffic to examine encrypted path format/structure
3. **TASK-XX:** Reverse engineer `.node` native addons if present in Cursor installation

### Medium Priority

4. **TASK-XX:** Analyze key rotation/refresh mechanisms
5. **TASK-XX:** Document key lifecycle (creation, distribution, expiry)

## 9. Code References

| Component | File | Line Numbers |
|-----------|------|--------------|
| IndexingConfig protobuf | workbench.desktop.main.js | 826650-826746 |
| RepositoryIndexingInfo protobuf | workbench.desktop.main.js | 119147-119225 |
| LocalCodebaseFileInfo protobuf | workbench.desktop.main.js | 98024-98070 |
| PathKeyHashType enum | workbench.desktop.main.js | 97659-97665 |
| RepositoryService.getPathEncryptionKey | workbench.desktop.main.js | 441169-441172 |
| RepositoryService.getOverridePathEncryptionKey | workbench.desktop.main.js | 441181-441184 |
| RepositoryService.getFinalCodeResults (decryption) | workbench.desktop.main.js | 441575-441600 |
| IPC proxy registration | workbench.desktop.main.js | 831957-831985 |
| Placeholder key definition | workbench.desktop.main.js | 268991 |
| Server config update | workbench.desktop.main.js | 1144265-1144267 |

## 10. Conclusion

Path encryption in Cursor is a **privacy feature** that obscures file paths when communicating with Cursor's backend servers. The actual encryption algorithm is implemented in native code (extension host process) and is not visible in the decompiled JavaScript bundle.

**Key Architectural Decision:** By implementing encryption in native code, Cursor achieves:
1. Performance (native crypto operations)
2. Security through obscurity (harder to reverse engineer)
3. Consistent key management across all path operations

**Limitation of This Analysis:** Without access to the native extension code, we cannot determine the specific encryption algorithm, IV handling, or key derivation functions used.
