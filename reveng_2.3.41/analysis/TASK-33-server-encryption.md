# TASK-33: Server-Side Encryption Key Handling via Traffic Analysis

## Overview

This analysis documents how Cursor negotiates and exchanges encryption keys with its backend servers. The key exchange model follows a **client-generated, server-acknowledged** pattern where keys are created locally and transmitted to the server in API headers or protobuf fields.

## 1. Key Exchange Architecture

### Key Philosophy: Client-Side Generation

Cursor does **not** use a traditional key exchange protocol (like Diffie-Hellman or TLS key negotiation at the application layer). Instead:

1. **Keys are generated entirely on the client side** using `crypto.getRandomValues()`
2. **Keys are transmitted to the server** via HTTP headers or protobuf message fields
3. **Server acknowledges receipt** but does not participate in key derivation
4. **TLS provides transport security** - keys are protected in transit by the HTTPS layer

This is a **key escrow model** where the server receives and stores client keys.

## 2. Encryption Key Types and Their Exchange

### 2.1 Idempotent Stream Encryption Key

**Purpose:** Encrypts idempotent stream data for resumable AI chat sessions

**Generation (line 488774-488777):**
```javascript
h = o?.idempotentEncryptionKey ?? (() => {
    const E = new Uint8Array(32);
    return crypto.getRandomValues(E), yO(Vs.wrap(E), !1, !0)
})();
```

**Transmission:** HTTP Header
```javascript
headers: {
    "x-idempotency-key": d,           // UUID for stream identity
    "x-idempotency-event-id": f,      // Event cursor for resumption
    "x-idempotent-encryption-key": h  // Base64-URL encoded 32-byte key
}
```

**Server Response:** Welcome message with degraded mode indicator
```javascript
// aiserver.v1.WelcomeMessage (line 122235)
{
    message: string,
    isDegradedMode: boolean  // true = server cannot use encryption
}
```

### 2.2 Path Encryption Key

**Purpose:** Encrypts file paths before sending to server for privacy protection

**Server-Provided Default Key:**
The server provides default encryption keys via the `GetServerConfig` endpoint:

```javascript
// Protobuf: aiserver.v1.IndexingConfig (line 826704)
{
    default_user_path_encryption_key: string,   // Field no. 9
    default_team_path_encryption_key: string    // Field no. 10
}
```

**Client Placeholder:**
```javascript
$Ut = "not a real key"  // Placeholder until server provides real key
```

**Key Exchange Flow:**
1. Client starts with placeholder key `$Ut`
2. Client calls `ServerConfigService.GetServerConfig()`
3. Server returns `IndexingConfig` with real encryption keys
4. Client updates local config and logs: `"defaultUserPathEncryptionKey updated from placeholder key"`

**Transmission in API Calls:**
```javascript
// Protobuf: aiserver.v1.RepositoryInfo (line 119208)
{
    path_encryption_key: string  // Field no. 10
}
```

### 2.3 Speculative Summarization Encryption Key

**Purpose:** Encrypts AI conversation summaries for context compression

**Generation (line 215139):**
```javascript
speculativeSummarizationEncryptionKey: crypto.getRandomValues(new Uint8Array(32))
```

**Persistence:** Serialized to Base64 via `yO(Vs.wrap(Di))`

**Regeneration on Error:**
```javascript
if (n.speculativeSummarizationEncryptionKey.byteLength === 0) {
    console.error("[composer] speculativeSummarizationEncryptionKey is empty, regenerating");
    n.speculativeSummarizationEncryptionKey = crypto.getRandomValues(new Uint8Array(32));
}
```

**Transmission:**
```javascript
// Protobuf field: speculative_summarization_encryption_key (field no. 43)
```

### 2.4 Context Bank Encryption Key

**Purpose:** Encrypts context bank data (conversation context storage)

**Protobuf Definition:**
```javascript
// Field: context_bank_encryption_key (line 123272, 168384, 330391)
{
    no: 43,
    name: "context_bank_encryption_key",
    kind: "scalar",
    T: 12  // bytes type
}
```

### 2.5 File Sync Encryption Header

**Purpose:** Provides encryption metadata for file synchronization

**Retrieval Flow:**
```javascript
async getFileSyncEncryptionHeader() {
    const e = this._everythingProviderService.onlyLocalProvider
        ?.runCommand("fileSync.getFileSyncEncryptionHeader", null);
    // ... timeout handling (5 seconds)
    return result ?? {};
}
```

**Command Registry:**
```javascript
i.GetFileSyncEncryptionHeader = "fileSync.getFileSyncEncryptionHeader"
```

### 2.6 Deeplink Encryption Key

**Purpose:** Encrypts shared deeplink data

**Request Structure (line 818094-818113):**
```javascript
// aiserver.v1.GetDeeplinkDataRequest
{
    deeplink_id: string,      // Field no. 1
    encryption_key: string    // Field no. 2
}
```

### 2.7 Bug Report Encryption Key

**Purpose:** Encrypts bug reports stored on server (Redis)

**Request Structure (line 128932-128951):**
```javascript
// aiserver.v1.GetEncryptedBugDataRequest
{
    redis_key: string,        // Field no. 1
    encryption_key: string    // Field no. 2
}
```

## 3. Server Configuration Exchange

### GetServerConfig Endpoint

**Service Definition (line 827948-827957):**
```javascript
{
    typeName: "aiserver.v1.ServerConfigService",
    methods: {
        getServerConfig: {
            name: "GetServerConfig",
            I: jOf,   // GetServerConfigRequest
            O: M2s,   // GetServerConfigResponse
            kind: Kt.Unary
        }
    }
}
```

**Configuration Refresh:**
- **Initial:** On application startup
- **Periodic:** Every 5 minutes (`300 * 1000 ms`)
- **On-demand:** After login/authentication changes

**Key Fields in Response:**
```javascript
// IndexingConfig within GetServerConfigResponse
{
    maxConcurrentUploads: 50,
    absoluteMaxNumberFiles: 100000,
    maxFileRetries: 20,
    syncConcurrency: 20,
    autoIndexingMaxNumFiles: 10000,
    indexingPeriodSeconds: 600,
    defaultTeamPathEncryptionKey: string,
    defaultUserPathEncryptionKey: string,
    // ...
}
```

## 4. Handshake Protocols (Non-Key-Exchange)

### FastRepoInitHandshake

**Purpose:** Repository indexing synchronization (not key exchange)

**Request (line 97940-97959):**
```javascript
// aiserver.v1.FastRepoInitHandshakeRequest
{
    repository: RepositoryInfo,
    root_hash: string,
    potential_legacy_repo_name: string
}
```

**Response Status:**
- `UP_TO_DATE` - Server index matches client
- `OUT_OF_SYNC` - Needs resync
- `FAILURE` - Handshake failed
- `EMPTY` - No data

### FastRepoInitHandshakeV2

**Enhanced Version (line 98079):**
```javascript
// aiserver.v1.FastRepoInitHandshakeV2Request
{
    repository: RepositoryInfo,
    root_hash: string,
    similarity_metric_type: enum,
    similarity_metric: float[],
    path_key_hash: string,
    path_key_hash_type: enum,
    do_copy: boolean,
    path_key: string,
    local_codebase_root_info: LocalCodebaseFileInfo,
    return_after_background_copy_started: boolean
}
```

**Note:** `path_key` and `path_key_hash` are used for path encryption verification, not key exchange.

### RepoHistoryInitHandshake

**Purpose:** Repository history synchronization

**Request (line 102095):**
```javascript
// aiserver.v1.RepoHistoryInitHandshakeRequest
{
    repository: RepositoryInfo,
    origin: string,
    test_origin_commit: string (optional),
    test_origin_commit_secret: string (optional),
    send_copy_candidates: boolean (optional)
}
```

## 5. Security Analysis

### Strengths

1. **Strong key generation:** 32-byte keys via `crypto.getRandomValues()` (256-bit security)
2. **Modern encryption:** AES-256-GCM with random IVs
3. **Per-session keys:** Idempotent stream keys are per-conversation
4. **Graceful degradation:** Server can indicate `isDegradedMode` when encryption unavailable

### Concerns

1. **Key transmission pattern:** All keys are sent to server - this is a key escrow model
2. **Header-based key transport:** `x-idempotent-encryption-key` sent in plain HTTP headers (relies entirely on TLS)
3. **No perfect forward secrecy:** Keys are static per conversation/session
4. **Server has plaintext access:** Server can decrypt any data at any time
5. **No key derivation ceremony:** No challenge-response or proof-of-knowledge

### Unknown Factors

1. **Server-side key storage:** How are keys stored on the server? Encrypted at rest?
2. **Key rotation:** No visible client-side key rotation mechanism
3. **Key deletion:** When/how are keys purged from server?
4. **Multi-device handling:** How are keys synchronized across devices?

## 6. Key Flow Diagrams

### Idempotent Stream Key Flow

```
Client                                  Server
  |                                       |
  |-- Generate 32-byte random key ------> |
  |                                       |
  |-- POST /stream (headers:              |
  |     x-idempotency-key: uuid           |
  |     x-idempotent-encryption-key: key) |
  |                                       |
  |<-- WelcomeMessage {                   |
  |      isDegradedMode: false }          |
  |                                       |
  |<-- ServerChunk (encrypted?) -------   |
  |                                       |
```

### Path Encryption Key Flow

```
Client                                  Server
  |                                       |
  |-- Use placeholder "$Ut" ----------->  |
  |                                       |
  |-- GetServerConfig() ---------------->  |
  |                                       |
  |<-- ServerConfigResponse {              |
  |      indexingConfig: {                |
  |        defaultUserPathEncryptionKey   |
  |      }}                               |
  |                                       |
  |-- Update local key ----------------->  |
  |                                       |
  |-- RepositoryInfo {                     |
  |      path_encryption_key: real_key }  |
  |                                       |
```

## 7. Protobuf Message Summary

| Message Type | Key Field | Transport |
|-------------|-----------|-----------|
| HTTP Headers | `x-idempotent-encryption-key` | HTTP header |
| RepositoryInfo | `path_encryption_key` | Protobuf field no. 10 |
| ChatRequest | `context_bank_encryption_key` | Protobuf field no. 43 |
| ChatRequest | `speculative_summarization_encryption_key` | Protobuf field |
| GetEncryptedBugDataRequest | `encryption_key` | Protobuf field no. 2 |
| GetDeeplinkDataRequest | `encryption_key` | Protobuf field no. 2 |
| IndexingConfig | `default_user_path_encryption_key` | Server config response |
| IndexingConfig | `default_team_path_encryption_key` | Server config response |

## 8. Further Investigation Needed

1. **Server-side encryption implementation:** What algorithm does server use?
2. **Key storage mechanism:** Redis, database, HSM?
3. **Traffic analysis:** Capture actual encrypted payloads to verify encryption is applied
4. **Key lifecycle:** When are keys created, rotated, and destroyed?
5. **Multi-tenant isolation:** How are keys isolated between users/teams?

## References

- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
  - Idempotent stream: lines 488771-488960
  - Server config: lines 1144217-1144290
  - Path encryption key handling: lines 441169-441184
  - Handshake protocols: lines 97940-102265
  - Encryption algorithms: lines 263045-263120
  - MCP secrets encryption: lines 1005445-1005553
