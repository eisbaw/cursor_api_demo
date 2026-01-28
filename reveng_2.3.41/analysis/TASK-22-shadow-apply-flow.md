# TASK-22: Shadow Workspace Accept/Apply Flow Analysis

## Overview

This document traces how Cursor's AI-generated changes flow from the shadow workspace (or worktree) through the approval UI to the main workspace. The system supports multiple pathways for applying changes depending on the mode (composer, Cmd+K, worktree) and user interaction patterns.

## Change Application Pathways

### Pathway 1: Inline Diff Service (Cmd+K & Composer)

The `InlineDiffService` manages changes that appear directly in the editor with inline diffs.

**Key File References:**
- Line 301423-303071: `inlineDiffService.js` module
- Line 302069-302124: `acceptDiff()` implementation
- Line 302125-302167: `rejectDiff()` implementation

#### Accept Flow

```
User clicks "Accept" button
    |
    v
inlineDiffService.acceptDiff(diffId, options)
    |
    +-- Push undo element for reversal capability
    +-- Collect line changes (added/removed)
    +-- diffHandler.accept() - The actual model update
    +-- Fire _onDidAcceptDiff event
    +-- Remove diff decorations
    v
composerCodeBlockService stores partial diff fates
```

**Code Snippet (line 302069-302096):**
```javascript
acceptDiff(e, t) {
    const n = this.diffHandlers.get(e);
    if (!n) return;

    // Telemetry and undo support
    this.telemetryService.publicLogCapture(k8a, {...});
    this.pushUndoElement(new D7("Undo Accept Diff", ...));

    // Collect change details for tracking
    let s = [], r = [];
    const o = [];
    n instanceof lre && (n.inlineDiff.changes.forEach(a => {
        const l = n.inlineDiff.newTextLines.slice(...);
        const d = n.inlineDiff.originalTextLines.slice(...);
        s.push(...l); r.push(...d);
        // Track fates for analytics
        o.push({ ...fate: "accepted" });
    }));

    // Apply the actual change
    n.accept();

    // Notify listeners
    this._onDidAcceptDiff.fire({...});
    this.remove(e, { closePromptBar: true, accepted: true });
}
```

#### Reject Flow

The reject flow reverses changes by applying the original text back to the modified model:

```javascript
reject(options, actorRequestId) {
    // Build edit operations to restore original content
    const edits = [];
    for (const change of this.inlineDiff.changes) {
        let text = change.removedTextLines.join(EOL);
        const range = this.getGreenRange(change);
        edits.push({ range, text, forceMoveMarkers: true });
    }

    // Apply edits to restore original content
    this.modelRef.object.textEditorModel.applyEdits(edits);

    // Push undo element for re-accept capability
    this.inlineDiffService.pushUndoElement(...);
}
```

### Pathway 2: Chat Editing Session (Native VSCode Chat Integration)

For the chat editing integration, changes are managed through a working set model.

**Key File References:**
- Line 1000141-1000245: `Hwt` (ModifiedFileEntry) class
- Line 1002757-1002985: Editing session accept/reject methods

#### File Entry Accept/Reject

```javascript
// Entry accept (line 1000190-1192)
async accept(e) {
    this._stateObs.get() === 0 && (
        await this._doAccept(e),
        this._stateObs.set(1, e),  // State: Accepted
        this._autoAcceptCtrl.set(void 0, e),
        this._notifyAction("accepted")
    )
}

// Entry reject (line 1000193-1195)
async reject(e) {
    this._stateObs.get() === 0 && (
        await this._doReject(e),
        this._stateObs.set(2, e),  // State: Rejected
        this._autoAcceptCtrl.set(void 0, e),
        this._notifyAction("rejected")
    )
}
```

#### Actual Change Application (_doAccept/_doReject)

```javascript
// _doAccept (line 1000955-962)
async _doAccept(e) {
    // Copy modified content to original model (makes change permanent)
    this.originalModel.setValue(this.modifiedModel.createSnapshot());
    this._diffInfo.set(UYe, e);  // Reset diff info
    this._edit = PK.empty;
    await this._collapse(e);

    // Save the file if not auto-save enabled
    if (!this._fileConfigService.getAutoSaveConfiguration(...).autoSave ||
        !this._textFileService.isDirty(this.modifiedURI)) {
        await this._textFileService.save(this.modifiedURI, {...});
    }
}

// _doReject (line 1000964-971)
async _doReject(e) {
    if (this.createdInRequestId === this._telemetryInfo.requestId) {
        // File was created by AI - delete it
        await this.docFileEditorModel.revert({ soft: true });
        await this._fileService.del(this.modifiedURI);
        this._onDidDelete.fire();
    } else {
        // Restore original content
        this._setDocValue(this.originalModel.getValue());
        if (this._allEditsAreFromUs) {
            await this.docFileEditorModel.save({...});
        }
        await this._collapse(e);
    }
}
```

### Pathway 3: Worktree Apply (Background Agent)

For background agent mode with git worktrees, changes are applied via git operations.

**Key File References:**
- Line 948430-948710: `_applyWorktreeToMainBranch()` method

#### Worktree Apply Flow

```
User clicks "Apply to Main"
    |
    v
reviewChangesService.getResources() - Get all changed files
    |
    v
For each file:
    - Read worktree content
    - Read HEAD content for comparison
    - Compute patch
    |
    v
_getFilePatchesWithMergeConflictDialog() - Check for conflicts
    |
    +-- If conflicts: Show dialog with options:
    |   - "merge" - Keep conflict markers
    |   - "overwrite" - Use agent changes
    |   - "cancel" - Abort
    |
    v
Apply file changes:
    - Write patched content to workspace files
    - Handle renames/deletes
    |
    v
If merge conflicts exist:
    - Open files at conflict markers
    - Show notification explaining markers
    |
    v
acceptAllDiffs() - Accept any remaining inline diffs
_finalizeApplyAndCleanup() - Remove worktree
```

## Hunk-Level Accept/Reject (Granular Control)

Users can accept or reject individual hunks within a diff.

**Key File References:**
- Line 1000902-923: `_acceptHunk()` / `_rejectHunk()`
- Line 1001255-1287: Notebook cell variant

```javascript
// _acceptHunk (line 1000902-912)
async _acceptHunk(e) {
    if (!this._diffInfo.get().changes.includes(e)) return false;

    // Build edits to apply this hunk's changes to original model
    const edits = [];
    for (const n of e.innerChanges ?? []) {
        const s = this.modifiedModel.getValueInRange(n.modifiedRange);
        edits.push(tp.replace(n.originalRange, s));
    }

    // Apply to original model
    this.originalModel.pushEditOperations(null, edits, n => null);

    // Recompute diff
    await this._updateDiffInfoSeq();

    // Auto-accept file if all hunks accepted
    if (this._diffInfo.get().identical) {
        this._stateObs.set(1, void 0);
    }

    this._accessibilitySignalService.playSignal(wg.editsKept, {...});
    return true;
}

// _rejectHunk (line 1000913-923)
async _rejectHunk(e) {
    if (!this._diffInfo.get().changes.includes(e)) return false;

    // Build edits to restore original content in modified model
    const edits = [];
    for (const n of e.innerChanges ?? []) {
        const s = this.originalModel.getValueInRange(n.originalRange);
        edits.push(tp.replace(n.modifiedRange, s));
    }

    // Apply to modified model (reverting the change)
    this.modifiedModel.pushEditOperations(null, edits, n => null);

    // Recompute diff
    await this._updateDiffInfoSeq();

    // Auto-reject file if all hunks rejected
    if (this._diffInfo.get().identical) {
        this._stateObs.set(2, void 0);
    }

    this._accessibilitySignalService.playSignal(wg.editsUndone, {...});
    return true;
}
```

## Code Block Status State Machine

Code blocks (AI-generated changes) have a status lifecycle:

```
generating -> completed -> [applying -> accepted/rejected]
                        -> cancelled
                        -> aborted
                        -> outdated
```

**Key File References:**
- Line 215187: Status types definition
- Line 306468-306521: `getCodeBlockStatus()` / `setCodeBlockStatus()`

**Status Types (line 215187):**
```javascript
["completed", "cancelled", "accepted", "rejected", "outdated", "applying"]
```

**Outdated Detection (line 306445-460):**
When the underlying file changes externally, code blocks are marked as "outdated":

```javascript
markUriAsOutdated(uri, hasQueuedCodeBlocks) {
    const cachedCodeBlocks = this._uriToCachedCodeBlocks.get(uri);
    for (const { composerId, codeblockId } of cachedCodeBlocks) {
        const codeBlock = this.getComposerCodeBlock(handle, uri, codeblockId);
        if (codeBlock && codeBlock.isNotApplied) {
            // Just clear the diffId, keep for reapply
            this._composerDataService.updateComposerDataSetStore(...);
        } else {
            // Mark as outdated - cannot be applied
            this.setCodeBlockStatus(handle, uri, codeblockId, "outdated");
            this.updateComposerCodeBlock(handle, uri, codeblockId, {
                isCached: false
            });
        }
    }
}
```

## Conflict Resolution Mechanisms

### 1. Worktree Merge Conflicts

When applying worktree changes to main workspace, conflicts are detected via git-style patching:

**Key File References:**
- Line 948499-948614: Conflict dialog and handling

```javascript
const { choice, filesWithConflicts, fileResults } =
    await this._getFilePatchesWithMergeConflictDialog(changes, composerData, hasApplied);

if (choice === "cancel") return;

// If "merge" selected, files retain conflict markers
if (filesWithConflicts.length > 0 && choice !== "overwrite") {
    // Open each conflicted file at the conflict marker
    for (const { uri, content } of filesWithConflicts) {
        const markerLine = Math.min(
            content.indexOf("<<<<<<< "),
            content.indexOf("======="),
            content.indexOf(">>>>>>> ")
        );
        await this.openerService.open(uri, { selection: { startLineNumber: markerLine } });
    }

    // Notify user
    this._notificationService.notify({
        severity: Qs.Warning,
        message: `${filesWithConflicts.length} file(s) have merge conflicts that need manual resolution...`
    });
}
```

**Conflict Marker Format:**
```
<<<<<<< Current (Your changes)
[user's local content]
=======
[AI's suggested changes]
>>>>>>> Incoming (Agent changes)
```

### 2. Inline Diff Conflicts (Outdated State)

For inline diffs, conflicts are handled by marking code blocks as "outdated" when the underlying file changes:

- File watcher detects external changes
- `markUriAsOutdated()` is called
- Code blocks transition to "outdated" status
- UI disables accept/reject buttons for outdated blocks
- User must regenerate or manually resolve

### 3. Chat Editing Session Conflicts

The chat editing session maintains original/modified model pairs:

```javascript
// Original model holds the pristine content
// Modified model holds the AI-changed content
// Diff is computed between them

// On external file change:
if (fileChanged && state === 0) {
    // Only pending changes can become outdated
    this._onDidDelete.fire();  // Signal that change context is lost
}
```

## Composer Service Accept/Reject All

**Key File References:**
- Line 946287-946333: `accept()`, `reject()`, `acceptAll()`, `rejectAll()`

```javascript
// acceptAll (line 946310-324)
async acceptAll(composerId) {
    const handle = this.composerDataService.getWeakHandleOptimistic(composerId);
    const data = handle?.data;

    // Track analytics
    this.analyticsService.trackEvent("composer.accept_all", {...});

    // Run any accept-all capabilities
    if (data && handle) {
        const lastHumanBubbleId = this.composerDataService.getLastHumanBubbleId(handle);
        if (lastHumanBubbleId) {
            await this.composerUtilsService.runCapabilitiesForProcess(
                handle, "accept-all-edits", { composerId, humanBubbleId }
            );
        }
    }

    // Accept all inline diffs
    this.acceptAllDiffs(composerId, "composer");
}

// acceptAllDiffs (line 946293-300)
acceptAllDiffs(composerId, sourceContext) {
    const handle = this.composerDataService.getWeakHandleOptimistic(composerId);
    if (!handle) return;

    const inlineDiffs = this.composerCodeBlockService.getAllInlineDiffs(handle);
    for (const diff of inlineDiffs) {
        this.inlineDiffService.acceptDiff(diff.id, { sourceContext });
    }
}
```

## Auto-Accept Behavior

The system supports auto-accept with a configurable delay:

**Key File References:**
- Line 1000161-1168: Auto-accept controller setup
- Line 1000220-1241: `acceptStreamingEditsEnd()` auto-accept logic

```javascript
// Auto-accept configuration
const autoAcceptDelay = A2("chat.editing.autoAcceptDelay", 0, configService);

// Review mode determination
this.reviewMode = derived(g => {
    const timeout = this._autoAcceptTimeout.read(g);
    return this._reviewModeTempObs.read(g) ?? timeout === 0;
});

// Auto-accept countdown after streaming ends
async acceptStreamingEditsEnd(e) {
    this._resetEditsState(e);

    if (await this._areOriginalAndModifiedIdentical()) {
        // No changes - auto-accept immediately
        this.accept(e);
    } else if (!this.reviewMode.get() && !this._autoAcceptCtrl.get()) {
        const timeout = this._autoAcceptTimeout.get() * 1000;
        const endTime = Date.now() + timeout;

        const tick = () => {
            if (this.reviewMode.get()) {
                this._autoAcceptCtrl.set(void 0, void 0);
                return;
            }
            const remaining = Math.round(endTime - Date.now());
            if (remaining <= 0) {
                this.accept(void 0);  // Auto-accept!
            } else {
                const timer = setTimeout(tick, 100);
                this._autoAcceptCtrl.set(new lgm(timeout, remaining, () => {
                    clearTimeout(timer);
                    this._autoAcceptCtrl.set(void 0, void 0);
                }), void 0);
            }
        };
        tick();
    }
}
```

## Undo/Redo Support

All accept/reject operations support undo/redo:

**Key File References:**
- Line 302074-302076: Undo element creation in acceptDiff
- Line 302133-302134: Undo element creation in rejectDiff

```javascript
// UndoRedoElement class (D7)
class D7 {
    constructor(label, code, diffId, uri, undoFn, redoFn) {
        this.type = 0;  // UndoRedoElementType.Resource
        this.resource = uri;
        this.label = label;
        this.code = code;
        this.undo = undoFn;
        this.redo = redoFn;
    }
}

// Usage in rejectDiff
const undoElement = new D7(
    "Undo Reject Suggestion",
    "undo-reject-suggestion",
    diffId,
    uri,
    () => {
        // Undo: reapply the rejected edits
        model.applyEdits(inverseEdits);
    },
    () => {
        // Redo: apply the rejection again
        model.applyEdits(rejectEdits);
    }
);
this.undoRedoService.pushElement(undoElement);
```

## Commands and Keybindings

| Command ID | Description | Context |
|------------|-------------|---------|
| `chatEditing.acceptFile` | Accept changes for single file | Multi-diff toolbar |
| `chatEditing.discardFile` | Reject changes for single file | Multi-diff toolbar |
| `chatEditing.acceptAllFiles` | Accept all pending changes | Ctrl+Shift+Enter in chat |
| `chatEditing.discardAllFiles` | Reject all pending changes | Chat toolbar |
| `chatEditing.clearWorkingSet` | Clear the working set | Chat toolbar |

## Event Flow Diagram

```
AI Generates Code
      |
      v
[Shadow Workspace / Worktree]
      |
      +--[Mode: Cmd+K]--> InlineDiffService.streamDiff()
      |                         |
      |                         v
      |                   Diff decorations in editor
      |                         |
      |                   +-----+-----+
      |                   |           |
      |                Accept    Reject
      |                   |           |
      |                   v           v
      |              Save file   Restore original
      |
      +--[Mode: Composer]--> composerCodeBlockService
      |                              |
      |                              v
      |                        Code block UI
      |                              |
      |                        +-----+-----+
      |                        |           |
      |                   Accept All  Reject All
      |                        |           |
      |                        v           v
      |                   Apply all   Revert all
      |                   inline      inline
      |                   diffs       diffs
      |
      +--[Mode: Worktree]--> Git worktree operations
                                   |
                                   v
                          "Apply to Main" button
                                   |
                                   v
                          Compute patches
                                   |
                          +--------+--------+
                          |                 |
                     No conflicts      Has conflicts
                          |                 |
                          v                 v
                     Apply patches    Show dialog:
                                      - Merge
                                      - Overwrite
                                      - Cancel
                                          |
                                          v
                                     Apply with
                                     conflict markers
                                          |
                                          v
                                     User resolves
                                     manually
```

## Questions for Further Investigation

1. **How does the speculative execution ("speculative-full-file") mode work?** - See line 303072, appears to be a full-file speculative application mode
2. **What is the exact UI component for the hunk-level accept/reject?** - The `$wt` class (line 1000594) appears to be a widget for this
3. **How does the best-of-N agent mode integrate with the apply flow?** - Multiple worktrees with selection
4. **What triggers the "outdated" state detection precisely?** - File watchers but timing/debouncing unclear

## File References Summary

| Component | Lines | Purpose |
|-----------|-------|---------|
| InlineDiffService | 301423-303071 | Core diff management |
| ModifiedFileEntry (Hwt) | 1000141-1000245 | Chat editing file state |
| EditingSession | 1002757-1003086 | Session-level accept/reject |
| ComposerService | 946287-946425 | Composer accept/reject all |
| Worktree Apply | 948430-948710 | Git worktree to main |
| CodeBlockService | 306320-306521 | Code block status tracking |
