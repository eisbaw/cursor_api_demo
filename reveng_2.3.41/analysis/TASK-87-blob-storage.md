# TASK-87: Blob Storage Mechanism for ConversationStateStructure

## Overview

The Cursor IDE implements a sophisticated multi-layer blob storage system for persisting conversation state. The `ConversationStateStructure` protobuf message uses bytes fields that store references (blob IDs) rather than inline data, with a content-addressable storage system backed by SHA-256 hashing.

## ConversationStateStructure Schema

Located at line 247796 in `workbench.desktop.main.js`:

```javascript
static typeName = "agent.v1.ConversationStateStructure";
static fields = k.util.newFieldList(() => [{
    no: 2, name: "turns_old", kind: "scalar", T: 12, repeated: true  // bytes[]
}, {
    no: 1, name: "root_prompt_messages_json", kind: "scalar", T: 12, repeated: true  // bytes[]
}, {
    no: 8, name: "turns", kind: "scalar", T: 12, repeated: true  // bytes[]
}, {
    no: 3, name: "todos", kind: "scalar", T: 12, repeated: true  // bytes[]
}, {
    no: 4, name: "pending_tool_calls", kind: "scalar", T: 9, repeated: true  // string[]
}, {
    no: 5, name: "token_details", kind: "message", T: t9r
}, {
    no: 6, name: "summary", kind: "scalar", T: 12, opt: true  // bytes?
}, {
    no: 7, name: "plan", kind: "scalar", T: 12, opt: true  // bytes?
}, {
    no: 9, name: "previous_workspace_uris", kind: "scalar", T: 9, repeated: true  // string[]
}, {
    no: 10, name: "mode", kind: "enum", T: k.getEnumType(iUt), opt: true
}, {
    no: 11, name: "summary_archive", kind: "scalar", T: 12, opt: true  // bytes?
}, {
    no: 12, name: "file_states", kind: "map", K: 9, V: { kind: "scalar", T: 12 }  // map<string, bytes>
}, {
    no: 15, name: "file_states_v2", kind: "map", K: 9, V: { kind: "message", T: sUl }
}, {
    no: 13, name: "summary_archives", kind: "scalar", T: 12, repeated: true  // bytes[]
}, {
    no: 14, name: "turn_timings", kind: "message", T: rUl, repeated: true
}, {
    no: 16, name: "subagent_states", kind: "map", K: 9, V: { kind: "message", T: oUl }
}, {
    no: 17, name: "self_summary_count", kind: "scalar", T: 13  // uint32
}, {
    no: 18, name: "read_paths", kind: "scalar", T: 9, repeated: true  // string[]
}]);
```

**Note**: T: 12 = bytes (protobuf scalar type), T: 9 = string, T: 13 = uint32

## Blob Storage Architecture

### Storage Layer Stack

The blob storage uses a layered architecture with multiple middleware wrappers:

```
[Application Layer]
        |
        v
+-------------------+
| ComposerBlobStore | --> Uses cursorDiskKV for local persistence
+-------------------+
        |
        v
+--------------------+
| CachedBlobStore    | --> In-memory LRU cache layer
+--------------------+
        |
        v
+----------------------+
| EncryptedBlobStore   | --> AES-GCM encryption layer
+----------------------+
        |
        v
+----------------------+
| WritethroughBlobStore| --> Remote sync middleware
+----------------------+
        |
        v
+-------------------+
| RetryBlobStore    | --> Retry logic for failures
+-------------------+
        |
        v
+--------------------+
| InMemoryBlobStore  | --> Fallback in-memory storage
+--------------------+
```

### 1. ComposerBlobStore (Primary Local Storage)

**Location**: `out-build/vs/workbench/contrib/composer/browser/composerBlobStore.js` (line 265297)

```javascript
// Key prefixes for different storage types
B7l = "agentKv:blob:"           // Blob data
U7l = "agentKv:checkpoint:"      // Checkpoint pointers
W7l = "agentKv:bubbleCheckpoint:" // Bubble-specific checkpoints

KJ = class {
    constructor(storageService, conversationId) {
        this.storageService = storageService;
        this.conversationId = conversationId;
    }

    keyFor(blobId) {
        return `${B7l}${xU(blobId)}`  // xU() converts bytes to hex string
    }

    async getBlob(ctx, blobId) {
        const key = this.keyFor(blobId);
        // Try binary first
        const binary = await this.storageService.cursorDiskKVGetBinary(key);
        if (binary !== undefined) {
            return binary.length === 1 && binary[0] === 0
                ? new Uint8Array(0)  // Handle empty blob marker
                : binary;
        }
        // Fallback to base64-encoded string
        const str = await this.storageService.cursorDiskKVGet(key);
        if (str) {
            return ere(str);  // base64 decode
        }
    }

    async setBlob(ctx, blobId, data) {
        const key = this.keyFor(blobId);
        await this.storageService.cursorDiskKVSetBinary(key, data);
    }
}
```

### 2. Blob ID Generation (Content-Addressable)

**Location**: Line 262977

```javascript
async function Yqe(data) {
    const hash = await crypto.subtle.digest("SHA-256", LVr(data));
    return new Uint8Array(hash);
}
```

Blob IDs are SHA-256 hashes of the content, making the storage content-addressable. This means:
- Identical data always produces the same blob ID
- Deduplication is automatic
- Integrity verification is built-in

### 3. EncryptedBlobStore (Encryption Layer)

**Location**: `../packages/agent-kv/src/cached-blob-store.ts` (line 263050)

```javascript
xvh = class VXe {
    static ALGORITHM = "AES-GCM";
    static IV_LENGTH = 12;

    constructor(blobStore, encryptionKeyStr) {
        this.blobStore = blobStore;
        this.encryptionKeyStr = encryptionKeyStr;
    }

    async getEncryptionKey() {
        if (this.encryptionKey === undefined) {
            const keyData = new TextEncoder().encode(this.encryptionKeyStr);
            const hash = await crypto.subtle.digest("SHA-256", keyData);
            this.encryptionKey = await crypto.subtle.importKey(
                "raw", hash,
                { name: "AES-GCM", length: 256 },
                true, ["encrypt", "decrypt"]
            );
        }
        return this.encryptionKey;
    }

    async getBlob(ctx, blobId) {
        const encrypted = await this.blobStore.getBlob(ctx, blobId);
        if (encrypted === undefined) return;

        const iv = encrypted.slice(0, 12);       // First 12 bytes = IV
        const ciphertext = encrypted.slice(12);   // Rest = encrypted data

        const plaintext = await crypto.subtle.decrypt(
            { name: "AES-GCM", iv: iv },
            await this.getEncryptionKey(),
            ciphertext
        );
        return new Uint8Array(plaintext);
    }

    async encryptBlob(data) {
        const iv = crypto.getRandomValues(new Uint8Array(12));
        const ciphertext = await crypto.subtle.encrypt(
            { name: "AES-GCM", iv: iv },
            await this.getEncryptionKey(),
            data
        );
        // Prepend IV to ciphertext
        const result = new Uint8Array(iv.length + ciphertext.byteLength);
        result.set(iv, 0);
        result.set(new Uint8Array(ciphertext), iv.length);
        return result;
    }
}
```

**Encryption Details**:
- Algorithm: AES-256-GCM (authenticated encryption)
- IV: 12 bytes, randomly generated per blob
- Key derivation: SHA-256 hash of encryption key string
- Storage format: `[12-byte IV][ciphertext]`

### 4. InMemoryBlobStore (Fallback/Testing)

**Location**: `../packages/agent-kv/src/blob-store.ts` (line 262982)

```javascript
Vdt = class {
    constructor() {
        this.blobs = new Map();  // Map<hexBlobId, Uint8Array>
    }

    getBlob(ctx, blobId) {
        return Promise.resolve(this.blobs.get(xU(blobId)));  // xU = hex encode
    }

    setBlob(ctx, blobId, data) {
        this.blobs.set(xU(blobId), data);
        return Promise.resolve();
    }
}
```

## CloudAgentStorageService

**Location**: `out-build/vs/workbench/services/agent/browser/cloudAgentStorageService.js` (line 343147)

Manages conversation state persistence with cloud sync capabilities:

```javascript
TWt = on("cloudAgentStorageService");
odc = 50;  // Max pending writes

Dbs = class extends Ve {
    constructor(storageService, structuredLogService, composerDataService) {
        this.storageService = storageService;
        this.composerBlobStores = new Map();
        this.stateCachesByBcId = new Map();
        this.metadataProperties = new Map();
        this.cloudAgentStateProperties = new Map();
        this.blobWriteQueuesByComposerId = new Map();
        this.pendingWritesByComposerId = new Map();
    }

    getComposerBlobStore(bcId, composerId) {
        let store = this.composerBlobStores.get(composerId);
        if (store === undefined) {
            store = new KJ(this.storageService, composerId);
            this.composerBlobStores.set(composerId, store);
        }
        return store;
    }

    async getBlob({ bcId, composerId, blobId }) {
        return await this.getComposerBlobStore(bcId, composerId).getBlob(lI(), blobId);
    }
}
```

## Checkpoint System

Checkpoints store pointers to blob IDs for conversation recovery:

```javascript
// Get latest checkpoint pointer for conversation
async getLatestCheckpointPointer() {
    const key = `${U7l}${this.requireConversationId()}`;
    const value = await this.storageService.cursorDiskKVGet(key);
    return value ? ere(value) : undefined;  // Returns blob ID
}

// Get bubble-specific checkpoint
async getBubbleCheckpoint(bubbleId) {
    const key = `${W7l}${this.requireConversationId()}:${bubbleId}`;
    const value = await this.storageService.cursorDiskKVGet(key);
    return value ? ere(value) : undefined;
}
```

## Hydration Flow

Loading conversation state from blob storage:

```javascript
// From line 265784
async function hydrateCheckpoint(ctx, blobStore, checkpointBlobId) {
    const blobData = await blobStore.getBlob(ctx, checkpointBlobId);
    if (blobData) {
        return U1.fromBinary(blobData);  // U1 = ConversationStateStructure
    }
}
```

## CloudAgentState Metadata

**Location**: Line 342665

```javascript
static typeName = "aiserver.v1.CloudAgentStatePersistedMetadata";
static fields = k.util.newFieldList(() => [{
    no: 1, name: "cloud_agent_state_blob_id", kind: "scalar", T: 12  // bytes
}, {
    no: 2, name: "offset_key", kind: "scalar", T: 9  // string
}, {
    no: 3, name: "timestamp_ms", kind: "scalar", T: 3  // int64
}, {
    no: 4, name: "workflow_status", kind: "enum", T: k.getEnumType(HJe)
}]);
```

## Feature Flags

```javascript
cloud_agent_enable_blob_storage_format_v1: {
    client: false,
    default: true
}
```

## Data Flow Summary

```
1. User creates/updates conversation
         |
         v
2. ConversationStateStructure is populated
   - turns[] (blob IDs referencing turn data)
   - todos[] (blob IDs referencing todo items)
   - file_states map (path -> blob ID)
   - summary (blob ID)
   - plan (blob ID)
         |
         v
3. Each field's data is serialized (protobuf toBinary)
         |
         v
4. SHA-256 hash computed -> becomes blob ID
         |
         v
5. Data encrypted with AES-GCM
         |
         v
6. Stored via cursorDiskKVSetBinary
   Key: "agentKv:blob:{hex(blobId)}"
         |
         v
7. Checkpoint pointer updated
   Key: "agentKv:checkpoint:{conversationId}"
   Value: latest blob ID
```

## Performance Metrics

The system tracks detailed performance metrics:

```javascript
agent_kv.in_memory.get_blob.duration_ms
agent_kv.in_memory.set_blob.duration_ms
agent_kv.cached.get_blob.duration_ms
agent_kv.cached.set_blob.duration_ms
agent_kv.cached.flush.duration_ms
agent_kv.encrypted.get_blob.duration_ms
agent_kv.encrypted.set_blob.duration_ms
agent_kv.writethrough.get_blob.duration_ms
agent_kv.writethrough.set_blob.duration_ms
agent_kv.writethrough.flush.duration_ms
agent_kv.retry.get_blob.duration_ms
agent_kv.retry.set_blob.duration_ms
```

## Key Storage Prefixes

| Prefix | Purpose |
|--------|---------|
| `agentKv:blob:` | Raw blob data (encrypted) |
| `agentKv:checkpoint:` | Conversation checkpoint pointers |
| `agentKv:bubbleCheckpoint:` | Per-bubble checkpoint pointers |
| `cloudAgent:metadata` | Cloud agent state metadata |

## Security Analysis

1. **Encryption at Rest**: All blobs are AES-256-GCM encrypted before storage
2. **Key Derivation**: Uses SHA-256 of encryption key string
3. **Random IV**: Each blob gets a unique 12-byte IV
4. **Authenticated Encryption**: GCM mode provides integrity verification
5. **Content Addressable**: SHA-256 blob IDs enable integrity checking

## Related Tasks

- TASK-36: cursorDiskKV storage implementation
- TASK-38: ConversationState structure analysis
- TASK-12: Stream encryption mechanisms
- TASK-14: Cloud agent storage service
