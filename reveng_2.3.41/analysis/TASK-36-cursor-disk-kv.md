# TASK-36: cursorDiskKV Storage Backend Implementation

## Overview

The `cursorDiskKV` is Cursor's persistent key-value storage system built on top of VS Code's SQLite-based storage infrastructure. It extends the standard VS Code storage with Cursor-specific operations for storing large binary blobs, batch operations, and prefix-based clearing. This system is critical for persisting composer conversations, checkpoints, cloud agent state, inline diffs, and various other AI-generated artifacts.

**Source Files Analyzed**:
- `out-build/vs/base/parts/storage/common/storage.js` (beautified lines ~32090-32245)
- `out-build/vs/platform/storage/common/storageService.js` (beautified lines ~33600-33750)
- `out-build/vs/platform/storage/common/storageIpc.js` (beautified lines ~883630-883800)
- `out-build/vs/workbench/contrib/composer/browser/composerBlobStore.js` (beautified lines ~265296-265365)

## Database Backend

### Storage File Location

The cursorDiskKV data is stored in an SQLite database file:

```
<globalStorageHome>/state.vscdb
```

For workspace-specific storage:
```
<workspaceStorageHome>/<workspaceStorageId>/state.vscdb
```

The `globalStorageHome` is typically `~/.config/Cursor/User/globalStorage/` on Linux.

### SQLite Configuration

The database supports optional WAL (Write-Ahead Logging) mode controlled by the `client_database_wal` feature gate. Configuration is stored in:

```
state.vscdb.options.json
```

### Table Structure

The cursorDiskKV uses the standard VS Code `ItemTable` in SQLite:

```sql
CREATE TABLE IF NOT EXISTS ItemTable (
    key TEXT PRIMARY KEY,
    value BLOB
)
```

**Key insight**: The `cursorDiskKV` operations are implemented as SQL queries against this table, separate from VS Code's built-in key-value caching layer.

## Architecture

### Class Hierarchy

```
IStorageService (interface)
    |
    +-- AbstractStorageService (abstract base)
    |       |
    |       +-- BrowserStorageService (workbench)
    |       +-- NativeStorageService (native desktop)
    |
    +-- Storage (SAe class) - In-memory cache + database delegate
            |
            +-- IStorageDatabase (interface)
                    |
                    +-- InMemoryStorageDatabase (eis class) - For testing
                    +-- SQLiteStorageDatabase - Native SQLite backend
                    +-- BaseStorageDatabaseClient (ohu class) - IPC client
```

### Storage Scopes

The system uses three storage scopes:
- **Application Storage (-1)**: Global application data, persisted across all profiles
- **Profile Storage (0)**: User profile-specific data
- **Workspace Storage (1)**: Workspace-specific data

**cursorDiskKV always operates on Application Storage (scope -1)**:

```javascript
async cursorDiskKVGet(e, t) {
    return this.getStorage(-1)?.cursorDiskKVGet(e, t)
}
```

## API Methods

### 1. cursorDiskKVGet(key: string, logFn?: Function): Promise<string | undefined>

Retrieves a string value by key. Used for JSON-serialized data.

```javascript
async cursorDiskKVGet(key, logFn) {
    logFn?.(`[storageIpc] BaseStorageDatabaseClient.cursorDiskKVGet: ${key}`);
    return this.channel.call("cursorDiskKVGet", [this.profile, this.workspace, key]);
}
```

### 2. cursorDiskKVGetWithLogs(key: string): Promise<{result: string | undefined, logs: string[]}>

Same as `cursorDiskKVGet` but returns diagnostic logs for debugging.

### 3. cursorDiskKVGetBatch(keys: string[]): Promise<[string, string][]>

Retrieves multiple keys in a single operation. Returns array of key-value tuples.

```javascript
async cursorDiskKVGetBatch(keys) {
    return this.channel.call("cursorDiskKVGetBatch", [this.profile, this.workspace, keys]);
}
```

### 4. cursorDiskKVSet(key: string, value: string | undefined): Promise<void>

Stores a string value. Setting value to `undefined` deletes the key.

### 5. cursorDiskKVSetBinary(key: string, value: Uint8Array): Promise<void>

Stores binary data directly without encoding. More efficient for large blobs.

### 6. cursorDiskKVGetBinary(key: string): Promise<Uint8Array | undefined>

Retrieves binary data. Handles the special case of empty arrays (stored as `[0]`).

### 7. cursorDiskKVClearPrefix(prefix: string): Promise<void>

Deletes all keys matching a prefix. Used for cleanup operations.

```javascript
async cursorDiskKVClearPrefix(prefix) {
    return this.channel.call("cursorDiskKVClearPrefix", {
        profile: this.profile,
        workspace: this.workspace,
        prefix: prefix
    });
}
```

### 8. cursorDiskKVOnShouldSave(callback: Function): Disposable

Registers a callback to be invoked before storage flush. Used for pre-save operations.

## IPC Protocol

### Channel Communication

The cursorDiskKV operations are proxied through VS Code's IPC channel system:

```javascript
// Client side (renderer process)
class BaseStorageDatabaseClient {
    constructor(channel, profile, workspace) {
        this.channel = channel;
        this.profile = profile;
        this.workspace = workspace;
    }

    async cursorDiskKVGet(key, logFn) {
        return this.channel.call("cursorDiskKVGet", [this.profile, this.workspace, key]);
    }
}
```

### Batch Size Limits

Large updates are chunked to avoid IPC threshold limits:

```javascript
const drt = /* IPC threshold constant */;

// In updateItems()
if (r + o < drt) {
    return this.channel.call("updateItems", { ... });
}
// Else chunk the updates
```

Items exceeding the IPC threshold are sent individually with a warning:

```javascript
if (itemSize > drt) {
    console.warn(`[storage] Item exceeds IPC threshold: key="${key.substring(0,100)}..." size=${itemSize.toLocaleString()} bytes`);
    await this.channel.call("updateItems", { insert: [[key, value]] });
}
```

## Key Prefixes

### Blob Storage

| Prefix | Purpose | Example Key |
|--------|---------|-------------|
| `agentKv:blob:` | Binary blob storage | `agentKv:blob:a1b2c3d4e5f6...` |
| `agentKv:checkpoint:` | Conversation checkpoints | `agentKv:checkpoint:{conversationId}` |
| `agentKv:bubbleCheckpoint:` | Bubble-specific checkpoints | `agentKv:bubbleCheckpoint:{conversationId}:{bubbleId}` |

### Composer Data

| Prefix | Purpose | Example Key |
|--------|---------|-------------|
| `composerData:` | Main composer state | `composerData:{composerId}` |
| `checkpointId:` | Composer checkpoints | `checkpointId:{composerId}:{checkpointId}` |
| `bubbleId:` | Conversation messages | `bubbleId:{composerId}:{bubbleId}` |
| `codeBlockDiff:` | Code diff storage | `codeBlockDiff:{composerId}:{diffId}` |
| `codeBlockPartialInlineDiffFates:` | Partial diff states | `codeBlockPartialInlineDiffFates:{composerId}:{fatesId}` |
| `messageRequestContext:` | Message context data | `messageRequestContext:{composerId}:{messageId}` |
| `composer.content.` | Content-addressed storage | `composer.content.{hash}` |

### Cloud Agent Storage

| Prefix | Purpose | Example Key |
|--------|---------|-------------|
| `{bcId}:cloudAgent:metadata` | Agent metadata | `bc123:cloudAgent:metadata` |

### Background Composer

| Prefix | Purpose | Example Key |
|--------|---------|-------------|
| `bcCachedDetails:` | Cached BC details | `bcCachedDetails:{bcId}` |

### Inline Diff

| Prefix | Purpose | Example Key |
|--------|---------|-------------|
| `inlineDiffUndoRedo:` | Undo/redo data | `inlineDiffUndoRedo:{diffId}` |

### AI Code Tracking

| Prefix | Purpose | Example Key |
|--------|---------|-------------|
| `ai_hashes.` | Hash backups by date | `ai_hashes.2024-01-15` |
| `ai_accepted_diffs.` | Accepted diff records | `ai_accepted_diffs.2024-01-15.{diffKey}` |

## Encoding Formats

### String Values (Text/JSON)

Standard JSON serialization, stored as-is in the database.

### Binary Values

Binary data handling has two formats for backward compatibility:

**Current format (Binary)**:
```javascript
await this.storageService.cursorDiskKVSetBinary(key, binaryData);
```

**Legacy format (Hex string)**:
```javascript
// xU: Uint8Array to hex
function xU(blobId) {
    try {
        return Buffer.from(blobId).toString("hex");
    } catch {
        return Array.from(blobId, t => t.toString(16).padStart(2, "0")).join("");
    }
}

// ere: hex to Uint8Array
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

**Empty array handling**:
Empty arrays are stored as `[0]` to distinguish from undefined:
```javascript
// Reading
if (binary.length === 1 && binary[0] === 0) {
    return new Uint8Array(0);
}
// Writing empty
await this.storageService.cursorDiskKVSetBinary(key, new Uint8Array([0]));
```

## ComposerBlobStore

The `KJ` class (ComposerBlobStore) provides content-addressable blob storage:

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
            return ere(hex);  // Decode hex to bytes
        }
        return undefined;
    }

    async setBlob(ctx, blobId, value) {
        const key = this.keyFor(blobId);
        await this.storageService.cursorDiskKVSetBinary(key, value);
    }
}
```

## Lifecycle Integration

### Flush on Shutdown

The system flushes pending writes before shutdown:

```javascript
async close() {
    this.emitWillSaveState(uW.SHUTDOWN);
    for (const callback of this.onDiskShouldSaveCallbacks) {
        try {
            await callback(uW.SHUTDOWN);
        } catch (e) {
            console.error(e);
        }
    }
    await Promise.allSettled([
        this.applicationStorage.close(),
        this.profileStorage.close(),
        this.workspaceStorage?.close() ?? Promise.resolve()
    ]);
}
```

### Periodic Flush

The storage service flushes pending changes periodically:
```javascript
static DEFAULT_FLUSH_DELAY = 100;  // milliseconds
```

## InMemoryStorageDatabase

For testing, an in-memory implementation is provided that no-ops all cursorDiskKV operations:

```javascript
class InMemoryStorageDatabase {
    async cursorDiskKVGet(key, logFn) {
        logFn?.(`[storage] InMemoryStorageDatabase.cursorDiskKVGet: ${key} undefined`);
        // Returns undefined - no persistence
    }

    async cursorDiskKVSet(key, value) {}
    async cursorDiskKVSetBinary(key, value) {}
    async cursorDiskKVGetBinary(key) {}
    async cursorDiskKVClearPrefix(prefix) {}
}
```

## Diagnostic Features

### Debug Logging

Recent cursorKV keys are tracked for diagnostics:

```javascript
// In error reporting
if (verbose && this.lastCursorKVKeys.length > 0) {
    diagnosticInfo += `
--- Recent cursorKV keys ---
${this.lastCursorKVKeys.join('\n')}`;
}
```

### Storage Path Reveal

A command exposes storage paths:

```javascript
const info = `AI Code Tracking Paths
${"=".repeat(50)}

cursorDiskKV Database:
${storagePath}

Database Details:
  Table: cursorDiskKV
  Key Prefixes:
    - ai_hashes.<yyyy-mm-dd> (for hash backups)
    - ai_accepted_diffs.<yyyy-mm-dd>.<diffKey> (for accepted diffs)
${"=".repeat(50)}`;
```

## Related Tasks for Deeper Investigation

The following areas warrant separate deep-dive investigations:

1. **SQLite Schema Details**: The actual SQL queries for cursorDiskKV operations in the main process
2. **Storage Migration**: How data is migrated between VS Code and Cursor versions
3. **Encryption at Rest**: Whether cursorDiskKV data is encrypted (appears to be plaintext)
4. **Quota Management**: How storage size is managed and limited
5. **Corruption Recovery**: Error handling for corrupted SQLite databases

## Summary

The cursorDiskKV system is a well-designed extension of VS Code's storage infrastructure that adds:

1. **Binary blob support**: Efficient storage of protobuf-serialized data
2. **Batch operations**: Bulk key retrieval for performance
3. **Prefix-based cleanup**: Efficient deletion of related keys
4. **Content-addressable storage**: Blob IDs based on content hashes
5. **Backward compatibility**: Legacy hex-encoded format support

The system uses SQLite for durability, IPC for cross-process access, and integrates with VS Code's lifecycle management for reliable persistence.
