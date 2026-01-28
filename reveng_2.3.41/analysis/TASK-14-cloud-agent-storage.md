# TASK-14: CloudAgentStorageService Blob Format and Serialization

## Overview

The `CloudAgentStorageService` is a crucial component in Cursor's Background Composer (a.k.a. "Cloud Agent") infrastructure. It handles the persistence of agent conversation state to disk, enabling session recovery, offline access, and efficient resumption of background agent workflows.

**Source file**: `out-build/vs/workbench/services/agent/browser/cloudAgentStorageService.js`
**Location in beautified**: Lines ~343147-343450 in `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`

## Service Architecture

### Service Registration

```javascript
// Service identifier
TWt = on("cloudAgentStorageService")

// Dependencies injected via constructor
constructor(storageService, structuredLogService, composerDataService)
```

### Internal Data Structures

```javascript
// Maps for caching and state management
composerBlobStores = new Map();        // composerId -> KJ (blob store)
stateCachesByBcId = new Map();         // bcId -> rdc (state cache)
metadataProperties = new Map();        // bcId -> reactive metadata property
cloudAgentStateProperties = new Map(); // bcId -> reactive state property
bcIdToComposerId = new Map();          // bcId -> composerId mapping
blobWriteQueuesByComposerId = new Map(); // composerId -> write queue
pendingWritesByComposerId = new Map(); // composerId -> Set of pending writes
```

## Key Data Types

### 1. CloudAgentStatePersistedMetadata (Protobuf)

**Type name**: `aiserver.v1.CloudAgentStatePersistedMetadata`

This is the lightweight metadata stored separately from the full state, enabling quick lookups without deserializing the entire state.

**Fields**:
| Field # | Name | Type | Description |
|---------|------|------|-------------|
| 1 | `cloud_agent_state_blob_id` | bytes (T: 12) | Reference to the state blob |
| 2 | `offset_key` | string (T: 9) | Last processed offset for streaming |
| 3 | `timestamp_ms` | double (T: 1) | Timestamp of last update |
| 4 | `workflow_status` | enum | CloudAgentWorkflowStatus |
| 5 | `version` | enum | PersistedMetadataVersion |

**Version enum** (`PersistedMetadataVersion`):
- `PERSISTED_METADATA_VERSION_UNSPECIFIED = 0`
- `PERSISTED_METADATA_VERSION_1 = 1`

### 2. CloudAgentState (Protobuf)

**Type name**: `aiserver.v1.CloudAgentState`

The full agent state containing conversation history, PR data, configuration, and various blob references.

**Fields** (30+ fields):
| Field # | Name | Type | Description |
|---------|------|------|-------------|
| 1 | `conversation_state` | message (Fqe) | Full conversation state |
| 2 | `num_prior_interaction_updates` | uint32 (T: 13) | Count of prior interactions |
| 3 | `pr_body` | bytes (T: 12) | Pull request body blob |
| 4 | `summary` | bytes (T: 12) | Conversation summary blob |
| 5 | `branch_name` | bytes (T: 12) | Git branch name blob |
| 6 | `pr_url` | bytes (T: 12) | Pull request URL blob |
| 7 | `last_interaction_update_offset_key` | string (T: 9) | Last interaction offset |
| 8 | `agent_name` | bytes (T: 12) | Agent name blob |
| 9 | `starting_commit` | string (optional) | Starting git commit |
| 10 | `base_branch` | string (optional) | Base branch for PR |
| 11 | `config` | bytes (T: 12) | Agent configuration blob |
| 12 | `local_state_branch` | string (optional) | Local state branch |
| 13 | `original_prompt_blob_id` | bytes | Original user prompt blob |
| 14 | `repository_info_blob_id` | bytes | Repository info blob |
| 15 | `original_conversation_action_blob_id` | bytes | Original conversation action |
| 16 | `video_annotations_blob_id` | bytes | Video annotations blob |
| 17 | `last_user_turn_commit` | string (optional) | Last user turn commit |
| 18 | `last_followup_source` | enum | BackgroundComposerSource |
| 19 | `continue_rebase` | bool (optional) | Continue rebase flag |
| 20 | `turn_start_todo_ids` | repeated | TODO IDs at turn start |
| ... | (additional fields) | ... | Grind mode, commits, errors, etc. |

### 3. CloudAgentWorkflowStatus (Enum)

**Type name**: `aiserver.v1.CloudAgentWorkflowStatus`

| Value | Name | Description |
|-------|------|-------------|
| 0 | `UNSPECIFIED` | Default/unknown state |
| 1 | `RUNNING` | Agent actively processing |
| 2 | `IDLE` | Agent waiting for input |
| 3 | `ERROR` | Agent encountered error |
| 4 | `ARCHIVED` | Agent workflow archived |
| 5 | `EXPIRED` | Agent session expired |

### 4. CloudAgentErrorDetails (Protobuf)

**Type name**: `aiserver.v1.CloudAgentErrorDetails`

| Field # | Name | Type | Description |
|---------|------|------|-------------|
| 1 | `error_message` | string (T: 9) | Error message text |
| 2 | `error_code` | string (T: 9) | Error code identifier |

## Storage Mechanism

### 1. Metadata Storage

**Key format**: `{bcId}:cloudAgent:metadata`

```javascript
// Key construction
function sdc(bcId, suffix) {
    return `${bcId}:${suffix}`
}
const metadataKey = sdc(bcId, "cloudAgent:metadata");
```

**Serialization**:
```javascript
// Write metadata
async setMetadata(bcId, metadata) {
    const key = sdc(bcId, "cloudAgent:metadata");
    // Serialize protobuf to binary, then base64 encode
    await this.storageService.cursorDiskKVSet(key, DOt.enc(metadata.toBinary()));
    this.getStateCache(bcId).setMetadata(metadata);
}

// Read metadata
async getMetadataIfExists(bcId) {
    const cached = this.getStateCache(bcId).getMetadata();
    if (cached?.version === Ibs) return cached;

    const key = sdc(bcId, "cloudAgent:metadata");
    const stored = await this.storageService.cursorDiskKVGet(key);
    if (!stored) return undefined;

    // Base64 decode, then parse protobuf
    const metadata = WGr.fromBinary(DOt.dec(stored));
    if (metadata.version === Ibs) {
        this.getStateCache(bcId).setMetadata(metadata);
        return metadata;
    }
}
```

### 2. Blob Storage (KJ Class)

**Source**: `out-build/vs/workbench/contrib/composer/browser/composerBlobStore.js`

The `KJ` class (ComposerBlobStore) handles individual blob storage using a key-value pattern.

**Key prefixes**:
- `agentKv:blob:` - For individual blobs
- `agentKv:checkpoint:` - For checkpoints
- `agentKv:bubbleCheckpoint:` - For bubble checkpoints

**Key format for blobs**: `agentKv:blob:{blobIdHex}`

```javascript
// Blob ID to hex conversion
function xU(blobId) {
    try {
        return Buffer.from(blobId).toString("hex");
    } catch {
        return Array.from(blobId, t => t.toString(16).padStart(2, "0")).join("");
    }
}

// Hex to Uint8Array conversion
function ere(hexString) {
    const normalized = hexString.trim().toLowerCase();
    if (normalized.length % 2 !== 0) throw new Error("Invalid hex string length");
    const bytes = new Uint8Array(normalized.length / 2);
    for (let i = 0; i < normalized.length; i += 2) {
        bytes[i / 2] = parseInt(normalized.slice(i, i + 2), 16);
    }
    return bytes;
}
```

**Blob storage operations**:
```javascript
class KJ {
    constructor(storageService, conversationId) {
        this.storageService = storageService;
        this.conversationId = conversationId;
    }

    keyFor(blobId) {
        return `agentKv:blob:${xU(blobId)}`;
    }

    async getBlob(ctx, blobId) {
        const key = this.keyFor(blobId);
        // Try binary first (newer format)
        const binary = await this.storageService.cursorDiskKVGetBinary(key);
        if (binary !== undefined) {
            return binary.length === 1 && binary[0] === 0
                ? new Uint8Array(0)
                : binary;
        }
        // Fallback to hex-encoded string (legacy format)
        const hex = await this.storageService.cursorDiskKVGet(key);
        if (hex) {
            try {
                const decoded = ere(hex);
                return decoded.length === 1 && decoded[0] === 0
                    ? new Uint8Array(0)
                    : decoded;
            } catch {
                return undefined;
            }
        }
        return undefined;
    }

    async setBlob(ctx, blobId, value) {
        const key = this.keyFor(blobId);
        await this.storageService.cursorDiskKVSetBinary(key, value);
    }
}
```

### 3. Base64 Encoding (DOt)

**Source**: `out-build/external/bufbuild/protobuf/proto-base64.js`

The `DOt` object provides standard Base64 encoding/decoding for protobuf serialization:

```javascript
DOt = {
    // Decode base64 string to Uint8Array
    dec(input) {
        // Standard base64 decoding with padding handling
        // Returns Uint8Array
    },

    // Encode Uint8Array to base64 string
    enc(input) {
        // Standard base64 encoding
        // Returns string with '=' padding
    }
}
```

## State Caching (rdc Class)

The `rdc` class provides in-memory caching to avoid repeated disk reads:

```javascript
class rdc {
    metadata;
    currentStateBlobIdHex;
    currentState;

    getMetadata() { return this.metadata; }
    setMetadata(m) { this.metadata = m; }

    setState(blobIdHex, state) {
        this.currentStateBlobIdHex = blobIdHex;
        this.currentState = state;
    }

    getState(blobIdHex) {
        if (this.currentStateBlobIdHex === blobIdHex) {
            return this.currentState;
        }
    }

    clear() {
        this.metadata = undefined;
        this.currentStateBlobIdHex = undefined;
        this.currentState = undefined;
    }
}
```

## Core Operations

### 1. Load State from Disk

```javascript
async getCloudAgentStateFromDiskOrCache({ bcId, composerId }, blobId) {
    const blobIdHex = xU(blobId);

    // Check cache first
    const cached = this.getStateCache(bcId).getState(blobIdHex);
    if (cached !== undefined) return cached;

    // Load from disk
    const blobData = await this.getBlob({ bcId, composerId, blobId });
    if (blobData === undefined) {
        throw new Error(`Cloud agent state blob not found for bcId: ${bcId}`);
    }

    // Deserialize protobuf
    const state = CloudAgentState.fromBinary(blobData);

    // Cache for future access
    this.getStateCache(bcId).setState(blobIdHex, state);

    return state;
}
```

### 2. Save New State

```javascript
async saveNewCloudAgentState({ bcId, composerId, blobId, state, offsetKey }) {
    const blobStore = this.getComposerBlobStore(bcId, composerId);
    const ctx = lI();  // Create logging context

    // Serialize state to binary
    const binaryData = state.toBinary();

    // Store blob
    await blobStore.setBlob(ctx, blobId, binaryData);

    // Update conversation state in memory
    if (state.conversationState) {
        const handle = await this.composerDataService.getComposerHandleById(composerId);
        handle?.setData("conversationState", state.conversationState);
    }

    // Update metadata
    await this.updateMetadata(bcId, {
        cloudAgentStateBlobId: blobId,
        offsetKey: offsetKey
    });

    // Update cache
    this.getStateCache(bcId).setState(xU(blobId), state);

    // Update reactive properties
    if (this.cloudAgentStateProperties.has(bcId)) {
        const derived = await this.getDerivedPropertiesFromState({ bcId, composerId }, state);
        this.cloudAgentStateProperties.get(bcId).change(derived);
    }
}
```

### 3. Blob Queue Management

To handle high-throughput blob writes efficiently:

```javascript
// Maximum concurrent writes
const odc = 50;

getBlobWriteQueue(composerId) {
    let queue = this.blobWriteQueuesByComposerId.get(composerId);
    if (!queue) {
        queue = new zUl({ max: odc });  // Throttled queue
        this.blobWriteQueuesByComposerId.set(composerId, queue);
    }
    return queue;
}

enqueueSetBlobs({ bcId, composerId, blobs }) {
    if (blobs.length === 0) return;

    const blobStore = this.getComposerBlobStore(bcId, composerId);
    const queue = this.getBlobWriteQueue(composerId);
    const pending = this.getPendingWrites(composerId);
    const ctx = lI();

    for (const blob of blobs) {
        const promise = queue.enqueue(async () => {
            await blobStore.setBlob(ctx, blob.id, blob.value);
        }).catch(err => {
            this.structuredLogService.error("background_composer",
                "Error in enqueueSetBlobs", err, { bcId, composerId });
        }).finally(() => {
            pending.delete(promise);
        });
        pending.add(promise);
    }
}

async waitForPendingWrites({ composerId }) {
    const pending = this.pendingWritesByComposerId.get(composerId);
    if (!pending || pending.size === 0) return;
    await Promise.all(pending);
}
```

## Relationship with BackgroundComposerService

The `wY` class (BackgroundComposerService / ComposerChatService) is the primary consumer of CloudAgentStorageService.

### Dependency Injection

```javascript
// In wY constructor (line ~487592)
this._cloudAgentStorageService = Ki  // Injected via TWt service identifier
```

### Key Integration Points

1. **loadAndListenToCloudAgent**: Main function for attaching to cloud agent streams
   - Loads initial state from disk using `getConversationStateWithLastInteraction`
   - Processes streaming updates and persists them via `saveNewCloudAgentState`
   - Handles workflow status updates via `saveNewWorkflowStatus`

2. **State Streaming**: Three message types from server:
   - `cloudAgentStateWithIdAndOffset`: Full state snapshot with blobs
   - `interactionUpdateWithOffset`: Incremental interaction updates
   - `workflowStatusWithOffset`: Status-only updates

3. **Prefetched Blobs**: Server can send blobs proactively
   - Stored via `storePreFetchedBlobs` and `enqueueSetBlobs`
   - Prevents additional fetches during state hydration

### Code Flow Example

```javascript
// In loadAndListenToCloudAgent (line ~488093)
async loadAndListenToCloudAgent({ bcId, composerId, ... }) {
    // 1. Load existing state from disk
    const diskState = await this._cloudAgentStorageService
        .getConversationStateWithLastInteraction({ bcId, composerId });

    // 2. Start streaming from server with offset
    const request = new Gso({
        bcId: bcId,
        offsetKey: diskState?.metadata.offsetKey,
        // ...
    });

    // 3. Process streaming responses
    for await (const response of stream) {
        if (response.message.case === "cloudAgentStateWithIdAndOffset") {
            // Store prefetched blobs
            await this._cloudAgentStorageService.storePreFetchedBlobs({
                bcId, composerId,
                blobs: response.message.value.preFetchedBlobs
            });

            // Save new state
            await this._cloudAgentStorageService.saveNewCloudAgentState({
                bcId, composerId,
                blobId: response.message.value.blobId,
                state: response.message.value.cloudAgentState,
                offsetKey: response.message.value.offsetKey
            });
        }
    }
}
```

## Derived Properties

The service extracts human-readable properties from the state:

```javascript
async getDerivedPropertiesFromState({ bcId, composerId }, state) {
    const [prUrl, agentName, branchName] = await Promise.all([
        this.getPRUrlFromState({ bcId, composerId }, state),
        this.getAgentNameFromState({ bcId, composerId }, state),
        this.getBranchNameFromState({ bcId, composerId }, state)
    ]);

    return {
        prUrl,              // Decoded from blob
        numTurns: state.conversationState?.turns.length ?? 0,
        agentName,          // Decoded from blob
        branchName,         // Decoded from blob
        baseBranch: state.baseBranch,
        originalRequestStartTime: state.originalRequestStartUnixMs
            ? new Date(Number(state.originalRequestStartUnixMs))
            : undefined,
        initialSource: state.initialSource
    };
}
```

## Summary

The CloudAgentStorageService provides a robust persistence layer for background composer state with:

1. **Two-tier storage**: Lightweight metadata for quick lookups, full state for hydration
2. **Protobuf serialization**: Using `@bufbuild/protobuf` for efficient binary encoding
3. **Content-addressable blobs**: Binary data stored by hex-encoded blob IDs
4. **In-memory caching**: Avoiding repeated disk reads with `rdc` cache class
5. **Queued writes**: Throttled parallel writes with 50-max concurrent operations
6. **Reactive properties**: Enabling UI updates when state changes
7. **Offset-based streaming**: Supporting efficient resume with `offset_key` tracking

The system is designed for resilience, supporting:
- Offline access to previously loaded agent conversations
- Efficient resume after connection drops
- Parallel blob fetching and writing
- Graceful handling of corrupted or missing data

## Complete CloudAgentState Fields

From the decompiled source at line ~342710, the full `aiserver.v1.CloudAgentState` (xbs class) has these fields:

```javascript
class CloudAgentState extends ge {
    conversationState;                    // message (T: Fqe) - Full conversation
    numPriorInteractionUpdates = 0;       // uint32 (T: 13)
    prBody = new Uint8Array(0);           // bytes (T: 12) - PR body blob
    summary = new Uint8Array(0);          // bytes (T: 12) - Summary blob
    branchName = new Uint8Array(0);       // bytes (T: 12) - Branch name blob
    prUrl = new Uint8Array(0);            // bytes (T: 12) - PR URL blob
    agentName = new Uint8Array(0);        // bytes (T: 12) - Agent name blob
    lastInteractionUpdateOffsetKey = "";  // string (T: 9)
    startingCommit;                       // optional string
    baseBranch;                           // optional string
    config = new Uint8Array(0);           // bytes (T: 12) - Config blob
    localStateBranch;                     // optional string
    originalPromptBlobId = new Uint8Array(0);      // bytes
    repositoryInfoBlobId = new Uint8Array(0);      // bytes
    originalConversationActionBlobId = new Uint8Array(0); // bytes
    videoAnnotationsBlobId = new Uint8Array(0);    // bytes
    lastUserTurnCommit;                   // optional string
    lastFollowupSource;                   // enum BackgroundComposerSource
    continueRebase;                       // optional bool
    turnStartTodoIds = [];                // repeated
    originalRequestStartUnixMs;           // optional int64
    initialTurnLatencyReported;           // optional bool
    agentSessionId;                       // optional string
    kickoffMessageId;                     // optional string
    grindModeConfig;                      // optional message
    commits = [];                         // repeated
    commitCount;                          // optional int32
    userFacingErrorDetails;               // optional message
    initialSource;                        // enum BackgroundComposerSource
    numCompletedTurns = 0;                // int32
}
```

## Encryption Layer (EncryptedBlobStore)

**Source**: `../packages/agent-kv/src/cached-blob-store.ts` (line ~263050)

The system includes an optional encryption wrapper for blob storage:

```javascript
class EncryptedBlobStore {
    static ALGORITHM = "AES-GCM";  // AES-256-GCM encryption
    static IV_LENGTH = 12;          // 96-bit initialization vector

    constructor(blobStore, encryptionKeyStr) {
        this.blobStore = blobStore;
        this.encryptionKeyStr = encryptionKeyStr;
    }

    async getEncryptionKey() {
        if (this.encryptionKey === undefined) {
            // Derive AES key from string via SHA-256
            const keyData = new TextEncoder().encode(this.encryptionKeyStr);
            const hash = await crypto.subtle.digest("SHA-256", keyData);
            this.encryptionKey = await crypto.subtle.importKey(
                "raw", hash,
                { name: "AES-GCM", length: 256 },
                true,
                ["encrypt", "decrypt"]
            );
        }
        return this.encryptionKey;
    }

    async getBlob(ctx, blobId) {
        const encrypted = await this.blobStore.getBlob(ctx, blobId);
        if (encrypted === undefined) return undefined;

        // Extract IV (first 12 bytes) and ciphertext
        const iv = encrypted.slice(0, EncryptedBlobStore.IV_LENGTH);
        const ciphertext = encrypted.slice(EncryptedBlobStore.IV_LENGTH);

        // Decrypt using AES-GCM
        const plaintext = await crypto.subtle.decrypt(
            { name: "AES-GCM", iv: iv },
            await this.getEncryptionKey(),
            ciphertext
        );
        return new Uint8Array(plaintext);
    }

    async encryptBlob(data) {
        // Generate random 96-bit IV
        const iv = crypto.getRandomValues(new Uint8Array(EncryptedBlobStore.IV_LENGTH));

        // Encrypt with AES-GCM
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

    async setBlob(ctx, blobId, data) {
        const encrypted = await this.encryptBlob(data);
        await this.blobStore.setBlob(ctx, blobId, encrypted);
    }
}
```

**Encryption format**: `[IV: 12 bytes][Ciphertext: variable]`

Note: The encryption key is derived from a string via SHA-256 hash, then used as an AES-256 key.

## Cloud Sync Mechanism

### GetBlobForAgentKV (Server Fetch)

When blobs are not found locally, the system fetches them from the cloud backend:

**Request** (`aiserver.v1.GetBlobForAgentKVRequest`):
| Field | Type | Description |
|-------|------|-------------|
| bc_id | string | Background composer ID |
| blob_id | bytes | Blob identifier |

**Response** (`aiserver.v1.GetBlobForAgentKVResponse`):
| Field | Type | Description |
|-------|------|-------------|
| blob_data | bytes | Raw blob content |

**Usage pattern** (from line ~488152):
```javascript
// When blob not found locally, fetch from server
const response = await client.getBlobForAgentKV(new GetBlobForAgentKVRequest({
    bcId: bcId,
    blobId: blobId
}), { signal: abortSignal });

// Cache locally for future use
this._cloudAgentStorageService.enqueueSetBlobs({
    bcId: bcId,
    composerId: composerId,
    blobs: [{ id: blobId, value: response.blobData }]
});
```

### StreamConversation (State Synchronization)

**Request** (`aiserver.v1.StreamConversationRequest`):
| Field | Type | Description |
|-------|------|-------------|
| bc_id | string | Background composer ID |
| offset_key | string (optional) | Resume point for streaming |
| filter_heavy_step_data | bool (optional) | Reduce data transfer |
| should_send_prefetched_blobs_first | bool (optional) | Prioritize blobs |

**Response** (`aiserver.v1.StreamConversationResponse`):
Oneof message types:
- `initial_state` - Initial full state with blobs
- `interaction_update_with_offset` - Incremental interaction
- `cloud_agent_state_with_id_and_offset` - Full state update
- `workflow_status_with_offset` - Status-only update
- `prefetched_blobs` - Blobs to cache ahead of need

### PreFetchedBlob Format

**Proto** (`aiserver.v1.PreFetchedBlob`):
```protobuf
message PreFetchedBlob {
    bytes id = 1;     // Blob identifier (content hash)
    bytes value = 2;  // Raw blob data
}
```

### Blob Storage Format Versions

**Enum** (`anyrun.v1.BlobStorageFormat`):
| Value | Name |
|-------|------|
| 0 | BLOB_STORAGE_FORMAT_LEGACY_UNSPECIFIED |
| 1 | BLOB_STORAGE_FORMAT_V1 |

**Feature gate**: `cloud_agent_enable_blob_storage_format_v1` controls v1 format usage.

## InMemoryBlobStore (Testing/Fallback)

For testing or non-persistent scenarios:

```javascript
class InMemoryBlobStore {
    blobs = new Map();  // hexBlobId -> Uint8Array

    getBlob(ctx, blobId) {
        const key = xU(blobId);  // Convert to hex
        return Promise.resolve(this.blobs.get(key));
    }

    setBlob(ctx, blobId, data) {
        this.blobs.set(xU(blobId), data);
        return Promise.resolve();
    }

    setBlobLocallyOnly(ctx, blobId, data) {
        return this.setBlob(ctx, blobId, data);
    }

    flush(ctx) {
        return Promise.resolve();
    }
}
```

## CheckpointHandler Integration

**Source**: Line ~940158 (`nrm` class)

Checkpoints provide recovery points for agent conversations:

```javascript
class CheckpointHandler {
    constructor(blobStore, conversationId, priorState, onCheckpoint, transcriptWriter, onTranscriptWritten) {
        this.blobStore = blobStore;
        this.conversationId = conversationId;
        this.priorConversationState = priorState;
        this.onCheckpoint = onCheckpoint;
        this.transcriptWriter = transcriptWriter;
        this.onTranscriptWritten = onTranscriptWritten;

        this.handleCheckpoint = async (ctx, newState) => {
            this.onCheckpoint?.(newState);
            this.priorConversationState = newState;

            // Write transcript in background
            this.transcriptWriter?.(ctx, newState)
                .then(() => this.onTranscriptWritten?.(this.conversationId))
                .catch(err => console.error("Error writing transcript:", err));
        };

        this.getLatestCheckpoint = () => this.priorConversationState;
    }
}
```

## ExternalSnapshot (Cloud VM State)

For cloud agent snapshots with presigned URLs:

**Proto** (`anyrun.v1.ExternalSnapshot`):
| Field | Type | Description |
|-------|------|-------------|
| snapshot_id | string | Unique snapshot identifier |
| presigned_url | string | S3/GCS presigned URL for download |
| image_metadata | ImageMetadata | Container/VM image info |
| blob_storage_format | BlobStorageFormat | Format version (LEGACY or V1) |

## Security Considerations

1. **Blob IDs as Content Hashes**: Blob IDs appear to be content-addressable (hash of content), providing integrity verification
2. **AES-256-GCM Encryption**: Strong authenticated encryption for sensitive blobs
3. **IV Per Blob**: Fresh random IV for each encryption prevents pattern analysis
4. **Key Derivation**: SHA-256 hash of passphrase for key generation (could be improved with PBKDF2/Argon2)
5. **Presigned URLs**: Time-limited access to cloud storage without exposing credentials

## Related Tasks

- TASK-87: Blob Storage (lower-level storage mechanisms)
- TASK-88: Checkpoint System (recovery points)
- TASK-36: CursorDiskKV (underlying key-value store)
- TASK-38: Conversation State (state structure details)
