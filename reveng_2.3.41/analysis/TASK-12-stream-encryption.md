# TASK-12: Stream Encryption Analysis

## Overview

This analysis documents the encryption mechanisms used in Cursor's streaming protocol, including the idempotent stream encryption, payload encryption for blob storage, and various encryption keys used throughout the system.

## 1. Idempotent Stream Encryption

### Key Generation

The idempotent stream encryption uses a **client-generated 32-byte random key**:

```javascript
// Location: line 488774-488777
h = o?.idempotentEncryptionKey ?? (() => {
    const E = new Uint8Array(32);
    return crypto.getRandomValues(E), yO(Vs.wrap(E), !1, !0)
})();
```

The key is:
1. Generated client-side using `crypto.getRandomValues()`
2. 32 bytes (256 bits) in length
3. Base64-URL encoded (without padding) via `yO()` function before transmission

### Key Transmission

The encryption key is sent as an HTTP header with each idempotent stream request:

```javascript
// Location: line 488865
headers: {
    ...n,
    "x-idempotency-key": d,           // UUID for stream identity
    "x-idempotency-event-id": f,      // Event cursor for resumption
    "x-idempotent-encryption-key": h  // Base64-URL encoded 32-byte key
}
```

### Idempotent Stream State Persistence

When the feature gate `persist_idempotent_stream_state` is enabled, the encryption key is persisted:

```javascript
// Location: line 488786-488792
idempotentStreamState: {
    idempotencyKey: d,
    idempotencyEventId: "0",
    idempotentEncryptionKey: h,
    nextSeqno: 0,
    playbackChunks: []
}
```

### Protocol Messages

The idempotent stream uses protobuf messages:

**Request Type:** `aiserver.v1.StreamUnifiedChatRequestWithToolsIdempotent`
- Fields: `client_chunk`, `abort`, `close`, `idempotency_key`, `seqno`

**Response Type:** `aiserver.v1.StreamUnifiedChatResponseWithToolsIdempotent`
- Fields: `server_chunk`, `welcome_message`, `seqno_ack`

### Degraded Mode

When the server returns `isDegradedMode: true` in the welcome message, reconnection/resumption is not available and the idempotent stream state is cleared.

## 2. EncryptedBlobStore (AES-GCM)

### Implementation Details

Location: lines 263046-263120

```javascript
class EncryptedBlobStore {
    static ALGORITHM = "AES-GCM"
    static IV_LENGTH = 12

    constructor(blobStore, encryptionKeyStr) {
        this.blobStore = blobStore;
        this.encryptionKeyStr = encryptionKeyStr;
    }
}
```

### Key Derivation

The encryption key is derived from a string key:

```javascript
async getEncryptionKey() {
    const keyBytes = new TextEncoder().encode(this.encryptionKeyStr);
    const hash = await crypto.subtle.digest("SHA-256", keyBytes);
    return await crypto.subtle.importKey("raw", hash, {
        name: "AES-GCM",
        length: 256
    }, true, ["encrypt", "decrypt"]);
}
```

**Key derivation process:**
1. String key encoded to UTF-8 bytes
2. SHA-256 hash computed
3. Hash used as raw AES-256 key material

### Encryption Format

```javascript
async encryptBlob(data) {
    const iv = crypto.getRandomValues(new Uint8Array(12));  // 12-byte IV
    const ciphertext = await crypto.subtle.encrypt({
        name: "AES-GCM",
        iv: iv
    }, await this.getEncryptionKey(), data);

    // Format: [12-byte IV][ciphertext]
    const result = new Uint8Array(iv.length + ciphertext.byteLength);
    result.set(iv, 0);
    result.set(new Uint8Array(ciphertext), iv.length);
    return result;
}
```

### Decryption

```javascript
async getBlob(key, options) {
    const encrypted = await this.blobStore.getBlob(key, options);
    const iv = encrypted.slice(0, 12);       // First 12 bytes
    const ciphertext = encrypted.slice(12);  // Remaining bytes

    const plaintext = await crypto.subtle.decrypt({
        name: "AES-GCM",
        iv: iv
    }, await this.getEncryptionKey(), ciphertext);
    return new Uint8Array(plaintext);
}
```

## 3. Encryption Key Types

### 3.1 Speculative Summarization Encryption Key

**Purpose:** Encrypts speculative summarization data for conversation context

**Generation:**
```javascript
// Location: line 215139
speculativeSummarizationEncryptionKey: crypto.getRandomValues(new Uint8Array(32))
```

**Serialization:** Base64-encoded via `yO(Vs.wrap(Di))` when sent to server

### 3.2 Path Encryption Key

**Purpose:** Encrypts file paths before sending to server (privacy)

**Protobuf field:** `path_encryption_key` (field type 12 = bytes)

**Usage contexts:**
- Repository info in streaming requests
- File sync operations
- Indexing operations

### 3.3 Context Bank Encryption Key

**Purpose:** Encrypts context bank data

**Protobuf location:** Field `context_bank_encryption_key` (field no. 43, type bytes)

### 3.4 File Sync Encryption Header

**Purpose:** Header for file sync encryption

**Retrieval:**
```javascript
async getFileSyncEncryptionHeader() {
    const result = this._everythingProviderService.onlyLocalProvider
        ?.runCommand("fileSync.getFileSyncEncryptionHeader", null);
    // ... timeout handling
    return result ?? {};
}
```

## 4. Secret Storage Encryption

### MCP (Model Context Protocol) Secrets

Location: lines 1005460-1005553

**Algorithm:** AES-GCM with 256-bit keys

```javascript
const encryptionKey = await crypto.subtle.generateKey({
    name: "AES-GCM",
    length: 256
}, true, ["encrypt", "decrypt"]);
```

**Key storage:** JWK format in SecretStorageService

**IV:** Random 12-byte (value from `opm` constant)

### System Secret Storage

Location: lines 466767-466859

Uses platform-specific encryption:
- **Linux:** kwallet, gnome-libsecret, gnome-keyring
- **Windows:** DPAPI
- **macOS:** Keychain Access

Falls back to in-memory storage if encryption unavailable.

## 5. Base64 Encoding Utilities

### yO() - Base64 Encoder

Location: lines 12595-12617

```javascript
function yO({buffer}, addPadding = true, urlSafe = false) {
    const charset = urlSafe ? urlSafeBase64Chars : standardBase64Chars;
    // ... encoding logic
}
```

**Parameters:**
- `addPadding`: Whether to add `=` padding (default: true)
- `urlSafe`: Use URL-safe Base64 alphabet (default: false)

### BH() - Base64 Decoder

Decodes Base64 strings back to Uint8Array.

## 6. Security Observations

### Strengths

1. **AES-256-GCM** - Modern authenticated encryption for blob storage
2. **Random IVs** - Fresh 12-byte IVs for each encryption operation
3. **Client-side key generation** - Keys generated locally, not server-provided
4. **Platform key storage** - Leverages OS-level secure storage when available

### Potential Concerns

1. **Key transmission in headers** - Idempotent encryption key sent in HTTP header
2. **Key derivation from string** - EncryptedBlobStore uses simple SHA-256 of string key (no salt, no iterations)
3. **Base64 encoding** - Keys sent encoded, not encrypted in transit (relies on TLS)

### Unknown/Unclear

1. **Server-side handling** of `x-idempotent-encryption-key` - What does the server do with this key?
2. **Path encryption algorithm** - Not visible in client code
3. **Context bank encryption** - Full implementation not analyzed

## 7. Protobuf Schema Summary

| Message Type | Field | Purpose |
|-------------|-------|---------|
| `StreamUnifiedChatRequestWithToolsIdempotent` | Header: `x-idempotent-encryption-key` | Stream encryption key |
| Various request types | `path_encryption_key` | File path privacy |
| Chat request | `context_bank_encryption_key` | Context bank encryption |
| Chat request | `speculative_summarization_encryption_key` | Summarization encryption |

## 8. Further Investigation Needed

1. **Server-side encryption handling** - Requires server code or traffic analysis
2. **Full path encryption flow** - How paths are actually encrypted
3. **Context bank encryption details** - Complete implementation
4. **Key rotation mechanisms** - If/how keys are rotated
5. **Encrypted relative path format** - How `encrypted_relative_path` field is populated

## References

- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
  - Idempotent stream: lines 488771-488960
  - EncryptedBlobStore: lines 263046-263120
  - Secret storage: lines 466767-466859
  - MCP secrets: lines 1005460-1005553
  - Base64 utilities: lines 12580-12630
