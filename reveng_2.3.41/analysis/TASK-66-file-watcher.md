# TASK-66: File Watcher Integration with Outdated State Detection

## Overview

This document analyzes how Cursor IDE 2.3.41 implements file watching and outdated state detection for managing file changes during AI-assisted editing sessions.

## Architecture Summary

Cursor's file watcher system is built on VS Code's foundational file watching infrastructure, with Cursor-specific extensions for AI code block tracking and composer file synchronization.

## Core Components

### 1. VS Code Base File Watching Infrastructure

**Location**: Lines 1119570-1119748

The base file watcher system uses a dual-watcher architecture:

```javascript
// Universal watcher for recursive watching
universalWatchRequests = []
universalWatchRequestDelayer = new JM(...)

// Non-recursive watcher for targeted watching
nonRecursiveWatchRequests = []
nonRecursiveWatchRequestDelayer = new JM(...)
```

Key behaviors:
- **Watch Request Batching**: Uses a delay mechanism (0-500ms based on request count) to batch watch operations
- **Utility Process Workers**: File watchers run in separate utility processes (`vs/platform/files/node/watcher/watcherMain`)
- **Polling Support**: Can fall back to polling for specific paths with configurable intervals (default 5000ms)

### 2. File Change Event Propagation

**Event System** (`onDidFilesChange`):
- File changes propagate through `_onDidChangeFile.fire()`
- Changes are classified by type: `0` (created), `1` (updated), `2` (deleted)
- Events are debounced (typically 100ms) to reduce noise

**Configuration Watcher Example** (Line 1116801):
```javascript
this._register(t.onDidFilesChange(r => this.handleFileChangesEvent(r)))
this._register(t.onDidRunOperation(r => this.handleFileOperationEvent(r)))
```

### 3. Composer Code Block Service - Cursor-Specific File Watching

**Location**: Lines 306320-306470

The `ComposerCodeBlockService` manages file watchers specifically for AI-generated code blocks:

```javascript
// Core data structures
this._fileWatchers = new Map        // URI -> watcher disposable
this._uriToCachedCodeBlocks = new Map  // URI -> code block references
this._uriToCachedCodeBlocksQueue = new Map  // Pending code blocks
```

**Key Functions**:

#### `registerCachedCodeBlock(composerHandle, uri, codeblockId, isPending)`
Registers a file watcher for a code block location:
```javascript
if (!this._fileWatchers.has(t.toString())) {
    const a = this._composerFileService.watch({
        uri: t,
        composerData: r
    });
    this._fileWatchers.set(t.toString(), a)
}
```

#### `markUriAsOutdated(uri, hasQueuedBlocks)`
Marks code blocks as outdated when external file changes are detected:
```javascript
// For each cached code block at this URI:
if (a && a.isNotApplied) {
    // Clear diff if not applied yet
    this._composerDataService.updateComposerDataSetStore(o, l =>
        l("codeBlockData", e.toString(), r, "diffId", void 0)
    )
} else {
    // Mark as outdated and uncache
    this.setCodeBlockStatus(o, e, r, "outdated")
    this.updateComposerCodeBlock(o, e, r, { isCached: !1 })
}
```

### 4. Outdated State Detection Mechanism

#### Status Lifecycle for Code Blocks
From Line 718020:
```javascript
Udf = ["outdated", "rejected", "cancelled", "aborted", "completed", "accepted"]
```

Status color mapping (Line 718052):
- `"outdated"` -> `var(--vscode-testing-iconUnset)` (neutral/gray)
- `"generating"`, `"applying"`, `"apply_pending"` -> `var(--vscode-testing-iconQueued)` (pending)
- `"completed"` -> `var(--vscode-testing-iconPassed)` (success/green)
- Error states -> `var(--vscode-testing-iconFailed)` (error/red)

#### File Change Handler (Line 306333)
```javascript
this._register(this._composerEventService.onDidFilesChange(w => {
    const _ = Array.from(new Set([
        ...this._uriToCachedCodeBlocks.keys(),
        ...this._uriToCachedCodeBlocksQueue.keys()
    ]));
    for (const E of _) {
        const T = _e.parse(E);
        if (w.contains(T)) {
            const D = this._uriToCachedCodeBlocksQueue.get(T.toString()) ?? [];
            this.markUriAsOutdated(T, D.length > 0);
            // Move queued blocks to active cache if any
            if (D.length > 0) {
                this._uriToCachedCodeBlocks.set(T.toString(), D);
                this._uriToCachedCodeBlocksQueue.delete(T.toString());
            }
        }
    }
}));
```

### 5. Text File Model Conflict Detection

**Location**: Lines 874060-874450

The `TextFileEditorModel` tracks file state for conflict detection:

```javascript
// State tracking
this.versionId = 0
this.dirty = !1
this.inConflictMode = !1
this.inOrphanMode = !1
this.inErrorMode = !1
this.lastResolvedFileStat  // Contains mtime, ctime, size, etag
```

#### Save Conflict Detection
```javascript
// Line 874344 - Save with conflict prevention
etag: t.ignoreModifiedSince ||
      !this.filesConfigurationService.preventSaveConflicts(r.resource, o.getLanguageId())
      ? Bne   // ETAG_DISABLED constant
      : r.etag
```

If the file's etag has changed since last read, save fails with `fileOperationResult === 3` (conflict).

#### Handling Conflicts (Line 365294)
```javascript
if (s.fileOperationResult === 3) {
    // Show conflict resolution UI
    a.push(this.instantiationService.createInstance(PCs, t))  // "Compare" action
    a.push(this.instantiationService.createInstance(lbc, t, n))  // "Overwrite" action
}
```

### 6. Composer File Service

**Location**: Lines 297405-297449

Bridges VS Code's file service with Composer's event system:
```javascript
this._register(this._fileService.onDidFilesChange(d => {
    this._composerEventService.fireDidFilesChange(d)
}))
```

### 7. Markdown Plan Editor File Watching

**Location**: Lines 741527-741538

Simple file watcher for markdown plan documents:
```javascript
setupFileWatcher(e) {
    this.cleanupFileWatcher();
    this.fileWatcher = this.fileService.onDidFilesChange(async t => {
        if (t.contains(e)) {
            this.markdownPlanRendering?.reload &&
            await this.markdownPlanRendering.reload()
        }
    })
}
```

### 8. Configuration File Watching

**Location**: Lines 1116800-1116850

Configuration files use specific watching strategies:
- Watches both the file and its parent directory
- Switches between file/directory watching based on file existence
- Uses atomic reads for settings files

```javascript
onResourceExists(i) {
    i ? (this.stopWatchingDirectory(), this.watchResource())
      : (this.stopWatchingResource(), this.watchDirectory())
}
```

## State Diagram: Code Block Lifecycle

```
                    ┌──────────────┐
                    │   Creating   │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Generating  │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
   │   Applied   │  │ Apply       │  │    Error    │
   │             │  │ Pending     │  │             │
   └──────┬──────┘  └──────┬──────┘  └─────────────┘
          │                │
          │                │ External file change
          │                ▼
          │         ┌─────────────┐
          │         │  Outdated   │
          │         └─────────────┘
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼
┌────────┐  ┌─────────┐
│Accepted│  │Rejected │
└────────┘  └─────────┘
```

## Key Findings

### 1. Dual-Layer File Watching
Cursor implements file watching at two layers:
- **Base Layer**: VS Code's universal/non-recursive watcher system
- **Cursor Layer**: Composer-specific file watching for AI code blocks

### 2. Outdated Detection Strategy
- Code blocks track whether they've been applied
- External file changes trigger `markUriAsOutdated()`
- Unapplied blocks have their diff cleared
- Applied blocks are marked "outdated" and uncached

### 3. Conflict Prevention via ETags
- Files track mtime, ctime, size, and etag
- Save operations include etag for optimistic concurrency
- Conflicts show a diff editor for resolution

### 4. Event-Driven Architecture
- All file changes flow through `onDidFilesChange` events
- Debouncing prevents event storms (100ms typical)
- Multiple services listen and react independently

### 5. Caching Strategy
- Code blocks are cached to avoid re-computation
- Cache invalidation happens on external file changes
- Queue system handles pending operations

## Potential Investigation Areas

1. **Race Conditions**: What happens if file changes occur during code block application?
2. **Large File Handling**: How does the system scale with many watched files?
3. **Network File Systems**: Polling intervals for remote file systems
4. **Extension Impact**: How extensions interact with file watchers

## File References

| Component | Line Range |
|-----------|------------|
| Base watcher infrastructure | 1119570-1119748 |
| ComposerCodeBlockService | 306320-306470 |
| ComposerEventService | 297227-297330 |
| ComposerFileService | 297405-297449 |
| TextFileEditorModel | 874050-874450 |
| Save conflict handler | 365280-365510 |
| Configuration watcher | 1116700-1116850 |
| Markdown plan editor | 741515-741595 |
