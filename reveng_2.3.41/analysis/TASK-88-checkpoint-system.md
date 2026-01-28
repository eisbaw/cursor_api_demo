# TASK-88: Conversation Checkpoint System Analysis

## Overview

The Cursor IDE checkpoint system provides state persistence and recovery capabilities for AI agent conversations. It enables users to:
- Save conversation state at specific points
- Revert files to previous states
- Resume interrupted conversations
- Navigate between conversation "bubbles" (messages)

## Core Components

### 1. ComposerCheckpointStorageService

**Location**: `workbench.desktop.main.js:267211`

**Service ID**: `composerCheckpointStorageService`

**Storage Key Pattern**: `checkpointId:{composerId}:{checkpointId}`

```javascript
class ComposerCheckpointStorageService {
    // Store a new checkpoint, returns generated checkpointId
    async storeCheckpoint(composerId, checkpointData) {
        const checkpointId = generateUUID();
        this._storageService.cursorDiskKVSet(
            `checkpointId:${composerId}:${checkpointId}`,
            JSON.stringify(checkpointData)
        );
        return checkpointId;
    }

    // Update existing checkpoint with callback modifier
    async updateCheckpoint(composerId, checkpointId, modifierFn) {
        const checkpoint = await this.retrieveCheckpoint(composerId, checkpointId);
        modifierFn(checkpoint);
        this._storageService.cursorDiskKVSet(key, JSON.stringify(checkpoint));
    }

    // Retrieve checkpoint by ID
    async retrieveCheckpoint(composerId, checkpointId) {
        const data = await this._storageService.cursorDiskKVGet(key);
        return JSON.parse(data);
    }

    // Clear all checkpoints for a composer
    async clearComposerCheckpoints(composerId) {
        this._storageService.cursorDiskKVClearPrefix(`checkpointId:${composerId}:`);
    }
}
```

### 2. ComposerBlobStore

**Location**: `workbench.desktop.main.js:265299`

**Storage Key Prefixes**:
- `agentKv:blob:` - Binary blob storage
- `agentKv:checkpoint:` - Checkpoint pointers
- `agentKv:bubbleCheckpoint:` - Per-bubble checkpoint pointers

```javascript
class ComposerBlobStore {
    constructor(storageService, conversationId) {
        this.storageService = storageService;
        this.conversationId = conversationId;
    }

    // Get blob data by hash
    async getBlob(ctx, blobHash) {
        const key = `agentKv:blob:${hexEncode(blobHash)}`;
        return this.storageService.cursorDiskKVGetBinary(key);
    }

    // Store blob data
    async setBlob(ctx, blobHash, data) {
        const key = `agentKv:blob:${hexEncode(blobHash)}`;
        await this.storageService.cursorDiskKVSetBinary(key, data);
    }

    // Get latest checkpoint pointer for conversation
    async getLatestCheckpointPointer() {
        const key = `agentKv:checkpoint:${this.conversationId}`;
        const hex = await this.storageService.cursorDiskKVGet(key);
        return hex ? hexDecode(hex) : undefined;
    }

    // Get bubble-specific checkpoint
    async getBubbleCheckpoint(bubbleId) {
        const key = `agentKv:bubbleCheckpoint:${this.conversationId}:${bubbleId}`;
        const hex = await this.storageService.cursorDiskKVGet(key);
        return hex ? hexDecode(hex) : undefined;
    }
}
```

### 3. CheckpointController

**Location**: `workbench.desktop.main.js:464132`

Controls checkpoint streaming during agent execution:

```javascript
class CheckpointController {
    constructor(checkpointStream, checkpointHandler, ctx) {
        this.checkpointStream = checkpointStream;
        this.checkpointHandler = checkpointHandler;
        this.ctx = ctx;
    }

    async run() {
        for await (const checkpoint of this.checkpointStream) {
            this.checkpointHandler.handleCheckpoint(this.ctx, checkpoint);
        }
    }
}
```

### 4. CheckpointHandler Interface

**Location**: `workbench.desktop.main.js:940160`

```javascript
class CheckpointHandler {
    constructor(blobStore, conversationId, priorConversationState,
                onCheckpoint, transcriptWriter, onTranscriptWritten) {
        this.blobStore = blobStore;
        this.conversationId = conversationId;
        this.priorConversationState = priorConversationState;
        this.onCheckpoint = onCheckpoint;
        this.transcriptWriter = transcriptWriter;
    }

    handleCheckpoint = async (ctx, checkpoint) => {
        // Store checkpoint in blob store
        // Update prior state
        this.priorConversationState = checkpoint;

        // Write transcript if configured
        if (this.transcriptWriter) {
            await this.transcriptWriter(ctx, checkpoint);
        }

        // Notify listeners
        if (this.onCheckpoint) {
            this.onCheckpoint(checkpoint);
        }
    };

    getLatestCheckpoint = () => this.priorConversationState;
}
```

## Data Structures

### Checkpoint Data Structure

**Location**: `workbench.desktop.main.js:215219`

```javascript
const emptyCheckpoint = {
    files: [],              // Array of file states with diffs
    nonExistentFiles: [],   // Files that don't exist but were tracked
    newlyCreatedFolders: [],// Folders created during session
    activeInlineDiffs: [],  // Currently active inline diffs
    inlineDiffNewlyCreatedResources: {
        files: [],          // Files created via inline diffs
        folders: []         // Folders created via inline diffs
    }
};
```

### File State Within Checkpoint

```javascript
{
    uri: Uri,                      // File URI
    originalModelDiffWrtV0: [],    // Diff from original file version
    isNewlyCreated: boolean        // Whether file was created during session
}
```

### Active Inline Diff State

```javascript
{
    uri: Uri,
    originalTextDiffWrtV0: [],     // Original text diffs
    newTextDiffWrtV0: [],          // New text diffs
    generationUUID: string,        // Unique generation ID
    codeBlockId: string            // Associated code block ID
}
```

### ConversationStateStructure (Protobuf)

**Type**: `agent.v1.ConversationStateStructure`
**Location**: `workbench.desktop.main.js:247796`

```javascript
{
    rootPromptMessagesJson: [],    // Initial prompt messages
    turns: [],                     // Conversation turns (binary)
    turnsOld: [],                  // Legacy turns format
    todos: [],                     // Agent todo items
    pendingToolCalls: [],          // Pending tool call IDs
    tokenDetails: {},              // Token usage details
    summary: binary,               // Conversation summary
    plan: binary,                  // Agent plan
    previousWorkspaceUris: [],     // Previous workspace paths
    mode: string,                  // Agent mode
    summaryArchive: {},            // Archived summaries
    fileStates: {},                // File state map (legacy)
    fileStatesV2: {},              // File state map v2
    summaryArchives: [],           // Multiple archived summaries
    turnTimings: [],               // Timing data per turn
    subagentStates: {},            // Nested subagent states
    selfSummaryCount: number,      // Summary count
    readPaths: []                  // Paths that have been read
}
```

## Checkpoint Operations

### 1. Storing Checkpoints on Bubble Updates

**Location**: `workbench.desktop.main.js:472320`

```javascript
async updateComposerBubbleCheckpoint(composerId, bubbleId, options) {
    const checkpoint = await this.createCurrentCheckpoint(composerId);
    if (checkpoint) {
        await this._composerDataService.updateComposerBubbleCheckpoint(
            handle, bubbleId, checkpoint,
            { isAfterCheckpoint: options?.isAfterCheckpoint }
        );
    }
}
```

### 2. Creating Current Checkpoint

**Location**: `workbench.desktop.main.js:472042`

```javascript
async createCurrentCheckpoint(composerId, priorCheckpoint, bubbleId) {
    const composerData = this._composerDataService.getComposerData(composerId);
    const checkpoint = emptyCheckpoint();

    // Get all URIs that need checkpointing
    const uris = this.getUrisForCheckpoints(composerData);

    for (const uri of uris) {
        const originalState = composerData.originalFileStates[uri];
        // Calculate diff from original
        const diff = await this.calculateDiff(uri, originalState);
        checkpoint.files.push({
            uri: Uri.parse(uri),
            originalModelDiffWrtV0: diff,
            isNewlyCreated: originalState?.isNewlyCreated ?? false
        });
    }

    // Add inline diffs
    for (const inlineDiff of this._inlineDiffService.inlineDiffs) {
        checkpoint.activeInlineDiffs.push({
            uri: inlineDiff.uri,
            originalTextDiffWrtV0: inlineDiff.originalDiff,
            newTextDiffWrtV0: inlineDiff.newDiff,
            generationUUID: inlineDiff.generationUUID
        });
    }

    return checkpoint;
}
```

### 3. Reverting to Checkpoint

**Location**: `workbench.desktop.main.js:471800`

Two revert implementations:
- **Standard revert**: Sequential file processing
- **Fast checkpoints**: Parallel batch processing (feature-gated)

```javascript
async checkoutToCheckpoint(handle, checkpointOrBubbleId, options) {
    // Validate checkpoint content
    const validation = await this.validateCheckpointContent(handle, target);

    // Show confirmation dialog
    if (!options?.skipDialog) {
        const result = await this._prettyDialogService.openDialog({
            title: "Discard all changes up to this checkpoint?",
            message: "You can always undo this later."
        });
        if (result !== "continue") return;
    }

    // Get files to revert
    const { filesToRevert, intermediateFiles, foldersToDelete } =
        await this.getFilesToRevertForCheckpoint(handle, bubbleId);

    // Execute revert
    if (this._experimentService.checkFeatureGate("fast_checkpoints")) {
        await this._revertToCheckpointsNew(/*...*/);
    } else {
        await this._revertToCheckpointsLegacy(/*...*/);
    }
}
```

### 4. Fast Checkpoint Revert

**Location**: `workbench.desktop.main.js:472335`

Implements parallel batch processing with rollback support:

```javascript
async _revertToCheckpointsNew(composerData, composerId, checkpoint,
                               filesToRevert, intermediateFiles,
                               foldersToDelete, originalStates) {
    const BATCH_SIZE = 5;
    const BATCH_DELAY = 200;
    const backupFiles = new Map();
    const deletedFiles = new Set();
    const createdFolders = new Set();

    try {
        // Backup phase
        for (const uri of filesToRevert) {
            const content = await this._composerFileService.readFile({uri});
            backupFiles.set(uri, content);
        }

        // Process files in batches
        for (let i = 0; i < files.length; i += BATCH_SIZE) {
            const batch = files.slice(i, i + BATCH_SIZE);
            await Promise.allSettled(batch.map(async (uri) => {
                await this.revertFile(uri, checkpoint, originalStates);
            }));
            await delay(BATCH_DELAY);
        }

        // Delete newly created folders
        for (const folder of foldersToDelete) {
            await this._composerFileService.deleteFolder({uri: folder});
        }

        // Apply inline diffs
        for (const diff of checkpoint.activeInlineDiffs) {
            await this._inlineDiffService.addDecorationsOnlyDiff(diff);
        }

    } catch (error) {
        // Rollback on failure
        for (const [uri, content] of backupFiles.entries()) {
            await this._composerFileService.writeFile({uri, content});
        }
        throw error;
    }
}
```

## Conversation Resumption

### Resume Action Flow

**Location**: `workbench.desktop.main.js:466122`

When a connection is interrupted, the system can resume:

```javascript
// On connection error with checkpoint available
if (error instanceof ConnectionTimeoutError && !ctx.canceled) {
    const latestCheckpoint = checkpointHandler.getLatestCheckpoint();
    if (latestCheckpoint) {
        const resumeAction = {
            case: "resumeAction",
            value: new ResumeAction()
        };
        await this.run(ctx, latestCheckpoint, resumeAction, /*...*/);
    }
}
```

### User Message Queue Handling

```javascript
// After stream ends, check for unprocessed user messages
if (messageQueue.hasUnprocessedMessages() && !ctx.canceled) {
    const unprocessed = messageQueue.getUnprocessedUserMessages();
    const checkpoint = checkpointHandler.getLatestCheckpoint();

    if (checkpoint && unprocessed.length > 0) {
        const nextMessage = unprocessed[0];
        messageQueue.markMessageAsProcessed(nextMessage);

        await this.run(ctx, checkpoint, {
            case: "userMessageAction",
            value: { userMessage: nextMessage }
        }, /*...*/);
    }
}
```

## Feature Flags

### fast_checkpoints

**Location**: `workbench.desktop.main.js:293977`

Enables the new parallel checkpoint revert algorithm with:
- Batch processing (5 files at a time)
- 200ms delays between batches
- Automatic rollback on failure
- Dynamic timeouts based on operation count

### checkpoint_threshold_ms

**Location**: `workbench.desktop.main.js:311450`

Controls the minimum time between automatic checkpoint creation.

### enable_checkpoint_read / enable_checkpoint_write

**Location**: `workbench.desktop.main.js:311136`

Toggle checkpoint reading/writing functionality.

## Migrations

### V1 Migration (Inline to Stored)

**Location**: `workbench.desktop.main.js:265418`

Migrates checkpoints from inline conversation data to separate storage:

```javascript
const V1_MIGRATION = {
    version: 1,
    check: (data) => data._v === 0,
    migrate: async (data, services) => {
        // Store latest checkpoint
        if (data.latestCheckpoint) {
            const id = await services.composerCheckpointStorageService
                .storeCheckpoint(data.composerId, data.latestCheckpoint);
            data.latestCheckpointId = id;
            delete data.latestCheckpoint;
        }

        // Store per-bubble checkpoints
        for (const bubble of data.conversation) {
            if (bubble.checkpoint) {
                const checkpointId = await services.composerCheckpointStorageService
                    .storeCheckpoint(data.composerId, bubble.checkpoint);
                bubble.checkpointId = checkpointId;
                delete bubble.checkpoint;
            }
        }

        return data;
    }
};
```

### V11 Migration (Blob Store)

**Location**: `workbench.desktop.main.js:265780`

Migrates conversation state to blob store format:

```javascript
// Load from blob store pointer
const pointer = await blobStore.getLatestCheckpointPointer();
if (pointer) {
    const blob = await blobStore.getBlob(ctx, pointer);
    const state = ConversationStateStructure.fromBinary(blob);
}
```

## Transcript Writer

**Location**: `workbench.desktop.main.js:940160`

The transcript writer persists checkpoint changes:

```javascript
this.handleCheckpoint = async (ctx, checkpoint) => {
    // Store in blob store
    await this.blobStore.setBlob(ctx, checkpointHash, checkpoint);

    // Update state
    this.priorConversationState = checkpoint;

    // Write transcript
    if (this.transcriptWriter) {
        await this.transcriptWriter(ctx, checkpoint).then(() => {
            if (this.onTranscriptWritten) {
                this.onTranscriptWritten();
            }
        });
    }
};
```

## Error Handling

### Checkpoint Hydration Errors

**Location**: `workbench.desktop.main.js:267766`

```javascript
// Error creating helpful error message
const createHydrationError = (source) => {
    return new ConnectError(
        `Failed to hydrate conversation checkpoint from ${source}`,
        Code.DataLoss,
        undefined,
        [detailedError]
    );
};

// Hydration attempts in order:
// 1. Blob store pointer -> Blob store data
// 2. Hex string -> Binary decode
// 3. Direct ConversationStateStructure instance
```

### Rollback on Revert Failure

The fast checkpoint system maintains:
- Backup of all files before modification
- Set of deleted files for restoration
- Set of created folders for cleanup
- Map of removed inline diffs for reference

## Performance Considerations

1. **Batch Processing**: Files processed in batches of 5 with 200ms delays
2. **Dynamic Timeouts**: Timeout calculated based on operation count:
   ```javascript
   const timeout = Math.min(10000, Math.max(2000, operationCount * 150));
   ```
3. **Parallel Backup**: All file backups performed concurrently before modifications
4. **Retry Logic**: Operations retried up to 3 times with exponential backoff

## Related Tasks

- TASK-38: Conversation state analysis
- TASK-39: Stream resumption
- TASK-56: Worktree lifecycle (uses checkpoints)
- TASK-70: KV storage (underlying storage mechanism)

## Key Findings

1. **Dual Storage**: Checkpoints stored both as JSON (legacy) and protobuf binary (new)
2. **Per-Bubble Tracking**: Each conversation message can have before/after checkpoints
3. **Diff-Based Storage**: Files stored as diffs from original, not full content
4. **Inline Diff Integration**: Checkpoints track active inline diffs for restoration
5. **Feature-Gated Improvements**: Fast checkpoint system behind feature flag
6. **Robust Error Handling**: Automatic rollback prevents partial state corruption
