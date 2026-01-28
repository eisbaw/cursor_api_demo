# TASK-70: Agent.v1 KV Storage Patterns Analysis

## Overview

The Cursor IDE uses a sophisticated key-value blob storage system (`agent-kv`) for persisting agent state, conversation checkpoints, and binary data. The system operates through protobuf-based messages with a bidirectional streaming protocol between server and client.

## Source Files

The KV storage implementation is found in:
- `src/proto/agent/v1/kv_pb.ts` (line 264596)
- `out-build/proto/agent/v1/kv_pb.js` (line 142385)
- `../packages/agent-kv/src/blob-store.ts` (line 262982)
- `../packages/agent-kv/src/cached-blob-store.ts` (line 263035)
- `../packages/agent-kv/src/controlled.ts` (line 264815)
- `../packages/agent-kv/src/remote.ts` (line 264930)
- `../packages/agent-kv/src/retry-blob-store.ts` (line 264940)
- `../packages/agent-kv/src/writethrough-middleware.ts` (line 264954)
- `out-build/vs/workbench/contrib/composer/browser/composerBlobStore.js` (line 265297)
- `out-build/vs/workbench/services/agent/browser/cloudAgentStorageService.js` (line 343147)

## Message Schemas

### KvServerMessage (Server to Client)

```protobuf
message KvServerMessage {
    uint32 id = 1;                          // Request correlation ID
    oneof message {
        GetBlobArgs get_blob_args = 2;       // Request to get a blob
        SetBlobArgs set_blob_args = 3;       // Request to set a blob
    }
    optional SpanContext span_context = 4;   // Tracing context
}
```

**Type name**: `agent.v1.KvServerMessage`

### KvClientMessage (Client to Server)

```protobuf
message KvClientMessage {
    uint32 id = 1;                           // Response correlation ID (matches request)
    oneof message {
        GetBlobResult get_blob_result = 2;   // Result of get blob operation
        SetBlobResult set_blob_result = 3;   // Result of set blob operation
    }
}
```

**Type name**: `agent.v1.KvClientMessage`

### GetBlobArgs

```protobuf
message GetBlobArgs {
    bytes blob_id = 1;                       // Binary blob identifier (Uint8Array)
}
```

**Type name**: `agent.v1.GetBlobArgs`

### GetBlobResult

```protobuf
message GetBlobResult {
    optional bytes blob_data = 1;            // Binary blob data (undefined if not found)
}
```

**Type name**: `agent.v1.GetBlobResult`

### SetBlobArgs

```protobuf
message SetBlobArgs {
    bytes blob_id = 1;                       // Binary blob identifier
    bytes blob_data = 2;                     // Binary data to store
}
```

**Type name**: `agent.v1.SetBlobArgs`

### SetBlobResult

```protobuf
message SetBlobResult {
    optional Error error = 1;                // Error message if operation failed
}
```

**Type name**: `agent.v1.SetBlobResult`

### SpanContext (for distributed tracing)

```protobuf
message SpanContext {
    string trace_id = 1;
    string span_id = 2;
    optional uint32 trace_flags = 3;
    optional string trace_state = 4;
}
```

**Type name**: `agent.v1.SpanContext`

### Error

```protobuf
message Error {
    string message = 1;
}
```

**Type name**: `agent.v1.Error`

## BlobStore Interface

All blob stores implement a common interface:

```typescript
interface BlobStore {
    getBlob(ctx: Context, blobId: Uint8Array): Promise<Uint8Array | undefined>;
    setBlob(ctx: Context, blobId: Uint8Array, data: Uint8Array): Promise<void>;
    setBlobLocallyOnly(ctx: Context, blobId: Uint8Array, data: Uint8Array): Promise<void>;
    flush(ctx: Context): Promise<void>;
}
```

## BlobStore Implementations

### 1. InMemoryBlobStore

Simple in-memory Map-based storage for testing/development:

```javascript
class InMemoryBlobStore {
    constructor() {
        this.blobs = new Map();
    }

    getBlob(ctx, blobId) {
        return this.blobs.get(hexEncode(blobId));
    }

    setBlob(ctx, blobId, data) {
        this.blobs.set(hexEncode(blobId), data);
    }
}
```

**Metrics:**
- `agent_kv.in_memory.get_blob.duration_ms`
- `agent_kv.in_memory.set_blob.duration_ms`

### 2. EncryptedBlobStore

Wraps another BlobStore with AES-256-GCM encryption:

```javascript
class EncryptedBlobStore {
    static ALGORITHM = "AES-GCM";
    static IV_LENGTH = 12;

    async getBlob(ctx, blobId) {
        const encrypted = await this.blobStore.getBlob(ctx, blobId);
        if (!encrypted) return undefined;

        const iv = encrypted.slice(0, 12);
        const ciphertext = encrypted.slice(12);
        return crypto.subtle.decrypt({ name: "AES-GCM", iv }, key, ciphertext);
    }

    async setBlob(ctx, blobId, data) {
        const iv = crypto.getRandomValues(new Uint8Array(12));
        const ciphertext = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, data);
        const encrypted = concat(iv, ciphertext);
        await this.blobStore.setBlob(ctx, blobId, encrypted);
    }
}
```

**Key derivation:** SHA-256 hash of encryption key string, imported as AES-256 key.

**Metrics:**
- `agent_kv.encrypted.get_blob.duration_ms`
- `agent_kv.encrypted.set_blob.duration_ms`

### 3. CachedBlobStore

Caching layer with cache hit/miss tracking:

**Metrics:**
- `agent_kv.cached.get_blob.duration_ms`
- `agent_kv.cached.set_blob.duration_ms`
- `agent_kv.cached.flush.duration_ms`
- `agent_kv.cached.get_blob.results` (counter with `cache_type` label)

### 4. ControlledKvManager

Bidirectional stream handler for remote KV operations. The server sends requests and the client responds:

```javascript
class ControlledKvManager {
    constructor(serverStream, clientStream, blobStore) {
        this.serverStream = serverStream;
        this.clientStream = clientStream;
        this.blobStore = blobStore;
    }

    async run(ctx) {
        for await (const message of this.serverStream) {
            switch (message.message.case) {
                case "getBlobArgs":
                    const data = await this.blobStore.getBlob(ctx, message.message.value.blobId);
                    await this.clientStream.write(new KvClientMessage({
                        id: message.id,
                        message: { case: "getBlobResult", value: { blobData: data } }
                    }));
                    break;

                case "setBlobArgs":
                    try {
                        await this.blobStore.setBlob(ctx, message.message.value.blobId, message.message.value.blobData);
                        await this.clientStream.write(new KvClientMessage({
                            id: message.id,
                            message: { case: "setBlobResult", value: { error: undefined } }
                        }));
                    } catch (e) {
                        await this.clientStream.write(new KvClientMessage({
                            id: message.id,
                            message: { case: "setBlobResult", value: { error: { message: e.message } } }
                        }));
                    }
                    break;
            }
        }
    }
}
```

**Metrics:**
- `agent_kv.controlled.get_blob.duration_ms`
- `agent_kv.controlled.set_blob.duration_ms`

### 5. RemoteKvManager

Remote blob store operations:

**Metrics:**
- `agent_kv.remote.get_blob.duration_ms`
- `agent_kv.remote.set_blob.duration_ms`

### 6. RetryBlobStore

Wraps another BlobStore with retry logic:

**Metrics:**
- `agent_kv.retry.get_blob.duration_ms`
- `agent_kv.retry.set_blob.duration_ms`
- `agent_kv.retry.set_blob_locally_only.duration_ms`
- `agent_kv.retry.flush.duration_ms`

### 7. WritethroughBlobStore

Write-through caching middleware:

**Metrics:**
- `agent_kv.writethrough.get_blob.duration_ms`
- `agent_kv.writethrough.set_blob.duration_ms`
- `agent_kv.writethrough.flush.duration_ms`

## Local Storage Layer (ComposerBlobStore)

Persists blobs to local disk via `cursorDiskKV` API:

```javascript
class ComposerBlobStore {
    constructor(storageService, conversationId) {
        this.storageService = storageService;
        this.conversationId = conversationId;
    }

    keyFor(blobId) {
        return `agentKv:blob:${hexEncode(blobId)}`;
    }

    async getBlob(ctx, blobId) {
        // Try binary first, fall back to base64-encoded string
        let data = await this.storageService.cursorDiskKVGetBinary(this.keyFor(blobId));
        if (data) return data;

        const str = await this.storageService.cursorDiskKVGet(this.keyFor(blobId));
        if (str) return base64Decode(str);
        return undefined;
    }

    async setBlob(ctx, blobId, data) {
        await this.storageService.cursorDiskKVSetBinary(this.keyFor(blobId), data);
    }
}
```

**Key prefixes:**
- `agentKv:blob:` - Binary blob data
- `agentKv:checkpoint:` - Checkpoint pointers
- `agentKv:bubbleCheckpoint:` - Bubble-specific checkpoints

## CloudAgentStorageService

High-level service managing cloud agent state and blob storage:

```javascript
class CloudAgentStorageService {
    constructor(storageService, structuredLogService, composerDataService) {
        this.composerBlobStores = new Map();      // Per-composer blob stores
        this.stateCachesByBcId = new Map();       // State caches by background composer ID
        this.blobWriteQueuesByComposerId = new Map();  // Write queues (max 50 concurrent)
    }

    getComposerBlobStore(bcId, composerId) {
        let store = this.composerBlobStores.get(composerId);
        if (!store) {
            store = new ComposerBlobStore(this.storageService, composerId);
            this.composerBlobStores.set(composerId, store);
        }
        return store;
    }

    async getBlob({ bcId, composerId, blobId }) {
        return this.getComposerBlobStore(bcId, composerId).getBlob(lI(), blobId);
    }

    async storePreFetchedBlobs({ bcId, composerId, blobs }) {
        const store = this.getComposerBlobStore(bcId, composerId);
        const queue = this.getBlobWriteQueue(composerId);
        await queue.enqueueList(blobs, async (blob) => {
            await store.setBlob(ctx, blob.id, blob.value);
        });
    }
}
```

**Key features:**
- Per-composer blob store instances
- State caching by background composer ID
- Write queue with max 50 concurrent operations
- Pending writes tracking for flush operations

## Protocol Flow

### Request-Response Pattern

1. **Server sends request** via `KvServerMessage`:
   - Assigns unique `id` for correlation
   - Includes `span_context` for distributed tracing
   - Either `get_blob_args` or `set_blob_args`

2. **Client processes request**:
   - `ControlledKvManager` reads from server stream
   - Dispatches to local `BlobStore`
   - Handles errors gracefully

3. **Client sends response** via `KvClientMessage`:
   - Matches request `id` for correlation
   - Either `get_blob_result` or `set_blob_result`

### Bidirectional Stream

The KV system uses bidirectional streaming:
- **Server stream**: `AsyncIterable<KvServerMessage>`
- **Client stream**: `WritableStream<KvClientMessage>`

This allows the server to control when blobs are read/written while the client manages local storage.

## Blob ID Format

Blob IDs are binary (`Uint8Array`) and converted to hex strings for storage keys using the `xU` function:

```javascript
function hexEncode(bytes) {
    // Convert Uint8Array to hex string
}
```

## Storage Key Patterns

| Pattern | Purpose |
|---------|---------|
| `agentKv:blob:{hex}` | Binary blob data |
| `agentKv:checkpoint:{conversationId}` | Latest checkpoint pointer |
| `agentKv:bubbleCheckpoint:{conversationId}:{bubbleId}` | Bubble-specific checkpoints |
| `cloudAgent:metadata` | Cloud agent metadata |

## Security Considerations

1. **Encryption at rest**: `EncryptedBlobStore` uses AES-256-GCM
2. **IV generation**: Random 12-byte IV per encryption
3. **Key derivation**: SHA-256 of key string (consider using proper KDF)

## Performance Instrumentation

Every blob store operation is instrumented with histograms:
- Duration tracking for get/set operations
- Cache hit/miss counters
- Flush operation timing

## Related Tasks

- TASK-14: Cloud Agent Storage Service (storage service architecture)
- TASK-36: Cursor Disk KV (underlying storage API)
- TASK-38: Conversation State (state blob management)
