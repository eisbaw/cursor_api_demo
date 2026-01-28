# TASK-40: Key Rotation Mechanisms Analysis

## Executive Summary

Analysis of Cursor IDE 2.3.41 reveals **no formal key rotation mechanism** exists. Keys are generated once and persist indefinitely until a decryption failure triggers data loss and key regeneration. The system prioritizes data availability over security through key rotation.

## Key Encryption Systems Identified

### 1. Platform Secret Storage Service (SecretStorageService)

**Location**: `vs/platform/secrets/common/secrets.js` (line 466779)

This is the primary secret storage layer that wraps platform-specific encryption.

```javascript
// EIs class - SecretStorageService base implementation
constructor(e, t, n, s) {
    this._useInMemoryStorage = e,
    this._storageService = t,
    this._encryptionService = n,
    this._logService = s,
    this._storagePrefix = "secret://",
    this._type = "unknown"  // becomes "persisted" or "in-memory"
}
```

**Key lifecycle**:
1. On initialization, checks if encryption is available via platform service
2. If encryption available: uses persisted storage with platform encryption
3. If not available: falls back to in-memory storage (secrets lost on restart)

**Error handling** (line 466803-466804):
```javascript
} catch (r) {
    this._logService.error(r), this.delete(e);  // DELETES SECRET ON DECRYPT FAILURE
    return
}
```

**Critical finding**: Decryption failures delete the secret entirely - no rotation attempt.

### 2. MCP Encryption Key System

**Location**: `vs/workbench/contrib/mcp` (line 1005452-1005477)

Constants:
```javascript
c_u = "mcpEncryptionKey"      // Secret key storage identifier
b6s = "AES-GCM"               // Algorithm
rpm = 256                      // Key length bits
opm = 12                       // IV length bytes
VIo = 1                        // Data version
u_u = "mcpInputs"             // Storage key for MCP data
```

**Key generation flow** (w6s class, line 1005466-1005477):
```javascript
this._getEncryptionKey = new Zg(() => WIo.secretSequencer.queue(async () => {
    // Try to retrieve existing key
    const o = await this._secretStorageService.get(c_u);
    if (o) try {
        const d = JSON.parse(o);
        return await crypto.subtle.importKey("jwk", d, b6s, !1, ["encrypt", "decrypt"])
    } catch {}

    // Generate new key if retrieval fails
    const a = await crypto.subtle.generateKey({
            name: b6s,
            length: rpm
        }, !0, ["encrypt", "decrypt"]),
        l = await crypto.subtle.exportKey("jwk", a);
    return await this._secretStorageService.set(c_u, JSON.stringify(l)), a
}))
```

**Key versioning** (line 1005479-1005485):
```javascript
const o = this._storageService.getObject(u_u, this._scope);
return o?.version === VIo ? {  // Check version equals 1
    ...o
} : {
    version: VIo,              // Reset if version mismatch
    values: {}                 // DATA LOST
}
```

**Unsealing error handling** (line 1005548-1005550):
```javascript
} catch (e) {
    this._logService.warn("Error unsealing MCP secrets", e),
    this._record.value.secrets = void 0  // CLEARS SECRETS ON FAILURE
}
return {}  // Returns empty - data lost
```

### 3. Encrypted Blob Store

**Location**: `vs/workbench/contrib/composer` (line 263050-263119)

```javascript
xvh = class VXe {
    constructor(e, t) {
        this.blobStore = e,
        this.encryptionKeyStr = t  // Key passed from external source
    }
    static ALGORITHM = "AES-GCM"
    static IV_LENGTH = 12

    async getEncryptionKey() {
        if (this.encryptionKey === void 0) {
            const t = new TextEncoder().encode(this.encryptionKeyStr),
                n = await crypto.subtle.digest("SHA-256", t);
            this.encryptionKey = await crypto.subtle.importKey("raw", n, {
                name: VXe.ALGORITHM,
                length: 256
            }, !0, ["encrypt", "decrypt"])
        }
        return this.encryptionKey
    }
}
```

**Key derivation**: SHA-256 hash of a string key, then import as AES-GCM key. Key is cached in memory.

## Platform-Specific Encryption Backends

**Enumeration** (line 466770-466772):

Password store preferences:
```javascript
i.kwallet = "kwallet"
i.kwallet5 = "kwallet5"
i.gnomeLibsecret = "gnome-libsecret"
i.basic = "basic"
```

Key storage provider types:
```javascript
i.unknown = "unknown"
i.basicText = "basic_text"
i.gnomeAny = "gnome_any"
i.gnomeLibsecret = "gnome_libsecret"
i.gnomeKeyring = "gnome_keyring"
i.kwallet = "kwallet"
i.kwallet5 = "kwallet5"
i.kwallet6 = "kwallet6"
i.dplib = "dpapi"           // Windows DPAPI
i.keychainAccess = "keychain_access"  // macOS Keychain
```

## Migration System (Encryption-Adjacent)

### Linux Password Store Migration

**Location**: line 1169738-1169751

```javascript
async migrateToGnomeLibsecret() {
    if (!mv || this.storageService.getBoolean("encryption.migratedToGnomeLibsecret", -1, !1))
        return;  // Skip if not Linux or already migrated

    const e = await this.fileService.readFile(this.environmentService.argvResource),
        t = qSs(e.value.toString());

    // Migrate from gnome/gnome-keyring to gnome-libsecret
    if (t["password-store"] === "gnome" || t["password-store"] === "gnome-keyring") {
        this.jsonEditingService.write(this.environmentService.argvResource, [{
            path: ["password-store"],
            value: "gnome-libsecret"
        }], !0);
    }
    this.storageService.store("encryption.migratedToGnomeLibsecret", !0, -1, 0)
}
```

**Purpose**: One-time migration from deprecated GNOME keyring to libsecret. This is a **backend migration**, not key rotation.

### Composer Data Migrations

**Location**: `vs/workbench/contrib/composer/browser/composerMigrations.js` (line 265413)

Data structure migration system with version tracking:
```javascript
V7l = { version: 1, check: i => i._v === 0, migrate: async (i, e) => {...} }
H7l = { version: 2, check: i => i._v === 1, migrate: async (i, e) => {...} }
// ... up to version 11
```

These migrations handle **data format changes**, not encryption key rotation.

## Encryption Fallback Behavior

### Native Secret Storage Service (line 1130871-1130914)

When encryption is unavailable:
1. Checks key storage provider type
2. For `basic_text` - offers user option to use plaintext storage
3. For GNOME backends - shows specific error message
4. For KWallet backends - shows specific error message
5. Always notifies user of security degradation

```javascript
async notifyOfNoEncryption() {
    if (s === "basic_text") {
        // Option to explicitly enable basic (insecure) storage
        run: async () => {
            await this._encryptionService.setUsePlainTextEncryption()
            await this._jsonEditingService.write(this._environmentService.argvResource, [{
                path: ["password-store"],
                value: "basic"
            }], !0)
            this.reinitialize()
        }
    }
}
```

## Key Types Found in Protocol Buffers

Several encryption keys are exchanged in API requests:

| Field Name | Location | Purpose |
|------------|----------|---------|
| `path_encryption_key` | line 119208, 243541 | Path obfuscation |
| `context_bank_encryption_key` | line 123272, 168384 | Context storage |
| `speculative_summarization_encryption_key` | line 123471, 330590 | Summary caching |
| `encryption_key` | line 128948 | Generic data encryption |

These keys appear to be **session-based** or **per-conversation**, generated client-side and sent to server.

## Key Rotation Analysis

### What Exists

1. **Data Version Checks**: Multiple systems check `_v` or `version` fields
2. **Backend Migration**: One-time migration between encryption backends (e.g., gnome-keyring to libsecret)
3. **Format Migration**: Data structure versioning without key changes

### What Does NOT Exist

1. **Automatic Key Rotation**: No scheduled or triggered key refresh
2. **Key Versioning**: No mechanism to track key generations
3. **Graceful Re-encryption**: No capability to decrypt with old key, re-encrypt with new
4. **Key Expiry**: No TTL or expiration enforcement
5. **Rollback Protection**: No forward secrecy mechanisms

### Failure Behavior

When a key becomes invalid (platform key deleted, keychain reset, etc.):

| System | Behavior | Data Fate |
|--------|----------|-----------|
| SecretStorageService | Delete secret | Lost |
| MCP Encryption | Clear secrets, regenerate key | Lost |
| Blob Store | Decryption fails | Lost |

## Security Implications

1. **Single Point of Failure**: One key loss = complete data loss
2. **No Rotation = Extended Exposure**: Compromised keys remain valid indefinitely
3. **Platform Dependency**: Key security depends entirely on OS keychain implementation
4. **In-Memory Fallback**: On keychain failure, secrets exist only in RAM (lost on restart)

## Recommendations for Investigation

1. **Test key deletion scenarios**: What happens when platform keychain is cleared?
2. **Investigate server-side key handling**: How does server manage encryption keys sent in requests?
3. **Examine backup/restore**: Any mechanism to export/import encrypted data?

## Related Files

- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
  - Lines 466760-466860: SecretStorageService
  - Lines 1005452-1005554: MCP encryption
  - Lines 263040-263119: EncryptedBlobStore
  - Lines 1130870-1130916: NativeSecretStorageService
  - Lines 1169738-1169752: Linux password store migration

## Conclusion

Cursor IDE 2.3.41 implements **no key rotation mechanism**. Keys are:
- Generated once on first use
- Stored in platform keychain
- Never rotated or refreshed
- Lost entirely on decryption failure

The architecture prioritizes simplicity and availability over key lifecycle management. Any key compromise or corruption results in data loss rather than graceful recovery or rotation.
