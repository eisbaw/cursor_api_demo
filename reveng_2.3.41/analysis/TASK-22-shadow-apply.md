# TASK-22: Shadow Workspace Accept/Apply Flow Analysis

## Overview

This document traces how Cursor's AI-generated changes flow from the shadow workspace (or worktree) through the approval UI to the main workspace. The system supports multiple pathways for applying changes depending on the mode (composer, Cmd+K, worktree, background agent) and user interaction patterns.

## Key Service Identifiers

| Service | Service ID | Purpose |
|---------|------------|---------|
| ShadowWorkspaceService | `IShadowWorkspaceService` (line 831687) | Manages shadow workspace lifecycle |
| ShadowWorkspaceServerService | `IShadowWorkspaceServerService` (line 831685) | Server-side shadow workspace operations |
| NativeShadowWorkspaceManager | `INativeShadowWorkspaceManager` (line 1114235) | Native platform shadow workspace management |

---

## Pathway 1: Background Agent Apply Changes (`applyChangesFromBgAgent`)

This is the primary flow for applying changes from Cloud/Background Agents to the main workspace.

**Key File References:**
- Line 1142158-1303: `applyChangesFromBgAgent()` implementation
- Line 756786-756833: `VAs` command class `workbench.action.backgroundComposer.applyChangesLocally`

### Flow Diagram

```
User clicks "Apply Changes Locally"
    |
    v
VAs.run() command invoked
    |
    +-- Opens progress dialog: "Applying changes locally..."
    |
    v
applyChangesFromBgAgent(bcId, options)
    |
    +-- Find background composer by bcId
    |
    +-- Get baseBranch from composer data
    |
    v
progressService.withProgress() - "Loading cloud agent data..."
    |
    +-- Parallel operations:
    |   |
    |   +-- getOptimizedDiffDetails()
    |   |   +-- Try cached diff (if diffChangesHash matches)
    |   |   +-- Fallback to server fetch
    |   |
    |   +-- getCurrentBranch()
    |
    v
_assembleFilesWithDiffs()
    |
    +-- Extract diffs from optimizedDiffDetails
    +-- Handle submodule diffs
    +-- Resolve relative paths to workspace URIs
    +-- Check for branch mismatch (show checkout prompt)
    |
    v
_getFilePatchesWithMergeConflictDialog()
    |
    +-- Detect merge conflicts
    +-- Check if other Best-of-N agents have been applied
    |
    v
[User Choice Dialog] - See "Conflict Resolution" section
    |
    v
Apply file changes (parallel, max 4):
    |
    +-- For deleted files: fileService.del()
    +-- For conflicts with "overwrite": write finalContent
    +-- For normal changes: write patchedContent
    |
    v
Update composer state:
    +-- Store appliedDiffs for undo support
    +-- Set applied = true
    +-- Update model config if Best-of-N
    |
    v
Record telemetry (worktreeEvent: APPLY_TO_MAIN)
    |
    v
Open first changed file and reveal first change
```

### Core Implementation (line 1142158-1303)

```javascript
async applyChangesFromBgAgent(bcId, options) {
    // Find the background composer
    const composer = this.backgroundComposerDataService.data.backgroundComposers
        .find(c => c.bcId === bcId);

    if (!composer) {
        this.notificationService.error("Cloud Agent data not found");
        return;
    }

    // Get optimized diff details (with caching)
    const [diffDetails, currentBranch] = await this.progressService.withProgress({
        location: 15,  // ProgressLocation.Notification
        title: "Loading cloud agent data...",
        cancellable: false
    }, async () => {
        // Try cache first
        const cachedHash = composer.diffChangesHash;
        const cached = cachedHash
            ? await this.backgroundComposerCachedDetailsStorageService
                  .getCachedDetails(composer.bcId)
            : undefined;

        if (cachedHash && cached?.detailedDiff &&
            cached.diffChangesHash === cachedHash) {
            // Cache hit - no server round trip
            return new QTs({ diff: cached.detailedDiff.diff, ... });
        }

        // Cache miss - fetch from server
        return await client.getOptimizedDiffDetails(new Wso({ bcId }));
    });

    // Assemble files with their diffs
    const filesWithDiffs = await this._assembleFilesWithDiffs({
        optimizedDiffDetails: diffDetails,
        goBack: options?.goBack,
        currentLocalBranch: currentBranch,
        baseBranch: composer.baseBranch
    });

    // Check for conflicts and show dialog
    const { choice, filesWithConflicts, fileResults } =
        await this._getFilePatchesWithMergeConflictDialog(
            filesWithDiffs,
            foregroundComposer,
            hasAppliedInBestOfN,
            options?.goBack
        );

    if (choice === "cancel") return;

    // Apply all file changes
    const appliedFiles = await wke(fileResults, async (file) => {
        if (file.isDeleted) {
            await this.fileService.del(file.uri, { recursive: false });
            return { uri, originalContent: file.originalContent ?? "", newContent: "" };
        }

        if (choice === "overwrite" && (file.hasConflicts || hasApplied)) {
            // Use agent's final content directly
            await this.fileService.writeFile(file.uri,
                Vs.fromString(file.finalContent));
        } else if (file.patchedContent !== undefined) {
            // Use merged/patched content
            await this.fileService.writeFile(file.uri,
                Vs.fromString(file.patchedContent));
        }

        return { uri, originalContent, newContent };
    }, { max: 4 });

    // Store applied diffs for undo support
    this.composerDataService.updateComposerDataSetStore(composerHandle, (set) => {
        set("appliedDiffs", appliedFiles);
        set("applied", true);
    });
}
```

---

## Pathway 2: Shadow Workspace Service Architecture

**Key File References:**
- Line 831686-831789: `IShadowWorkspaceService` and `Wyo` implementation

### Shadow Workspace Manager Pattern

```javascript
class Wyo extends Ve {  // ShadowWorkspaceService implementation
    shadowWorkspaceManagers = [];
    isOpening = false;
    _clientPromise = undefined;
    _clientProvider = undefined;

    registerShadowWorkspaceManager(manager) {
        this.shadowWorkspaceManagers.push(manager);
    }

    enabled() {
        return this.configurationService.getValue(oNt) ?? false;
    }

    async openShadowWorkspace() {
        if (this.isOpening)
            throw new Error("Already opening a shadow workspace");

        try {
            this.isOpening = true;

            // Check if any manager already has an open shadow workspace
            for (const manager of this.shadowWorkspaceManagers) {
                if (manager.hasOpenShadowWorkspace()) {
                    return { didReuse: true };
                }
            }

            // Close any existing shadow workspace first
            await this.closeShadowWorkspace();

            if (!this.enabled())
                throw new Error("Shadow workspace is not enabled");

            // Find an available manager and open
            for (const manager of this.shadowWorkspaceManagers) {
                if (manager.available()) {
                    await manager.openShadowWorkspace();
                    return { didReuse: false };
                }
            }

            throw new Error("No shadow workspace manager available");
        } finally {
            this.isOpening = false;
        }
    }

    async closeShadowWorkspace() {
        this.killClient();
        for (const manager of this.shadowWorkspaceManagers) {
            try {
                await manager.closeShadowWorkspace();
            } catch (e) {
                console.error("Failed to close shadow workspace", e);
            }
        }
    }
}
```

### Native Shadow Workspace Manager (line 1114236-1114303)

```javascript
class t6o extends Ve {  // NativeShadowWorkspaceManager
    shadowWorkspacesHome;  // Directory for shadow workspace files
    shadowWindowId = undefined;
    shadowWorkspaceUri = undefined;

    available() {
        // Only available for local (non-remote) workspaces
        return !this.nativeWorkbenchEnvironmentService.remoteAuthority;
    }

    async createShadowWorkspace() {
        if (this.shadowWorkspaceUri) {
            await this.closeShadowWorkspace();
        }

        // Create unique workspace file
        const timestamp = (Date.now() + Math.round(Math.random() * 1000)).toString();
        this.shadowWorkspaceUri = _e.joinPath(
            this.shadowWorkspacesHome,
            `Untitled-${timestamp}.${Qj}`
        );

        // Copy workspace folders configuration
        const folders = this.workspaceContextService.getWorkspace().folders;
        const shadowFolders = folders.map(f =>
            $$r(f.uri, true, f.name, this.shadowWorkspacesHome, this.uriIdentityService.extUri)
        );

        const workspace = {
            folders: shadowFolders,
            remoteAuthority: this.nativeWorkbenchEnvironmentService.remoteAuthority,
            transient: true
        };

        await this.fileService.writeFile(
            this.shadowWorkspaceUri,
            Vs.fromString(JSON.stringify(workspace, null, "\t"))
        );

        // Cleanup old shadow workspaces
        this.cleanUpOldFiles();

        return wMm(this.shadowWorkspaceUri);
    }

    async openShadowWorkspace() {
        this.closeShadowWorkspace();

        const workspaceUri = await this.createShadowWorkspace();

        // Copy workspace settings with auto-save disabled
        await this.workspaceEditingService.copyWorkspaceSettings(workspaceUri, {
            overrides: { "files.autoSave": "off" }
        });

        // Open in a new window
        const results = await this.nativeHostService.openWindow([{...}], {
            forceNewWindow: true,
            shadowWindowForWorkspaceId: this.workspaceContextService.getWorkspace().id
        });

        this.shadowWindowId = results.at(0)?.windowId;
    }

    async closeShadowWorkspace() {
        if (this.shadowWindowId) {
            // Close and destroy the window
            await Promise.race([
                this.nativeHostService.closeWindowNoFallback({
                    targetWindowId: this.shadowWindowId
                }),
                new Promise(r => setTimeout(() => r("timedout"), 500))
            ]);
            await this.nativeHostService.destroyWindowNoFallback({
                targetWindowId: this.shadowWindowId
            });
            this.shadowWindowId = undefined;
        }

        if (this.shadowWorkspaceUri) {
            try {
                await this.fileService.del(this.shadowWorkspaceUri);
            } catch (e) {
                console.warn("Failed to delete shadow workspace", e);
            }
            this.shadowWorkspaceUri = undefined;
        }
    }
}
```

---

## Conflict Resolution UI (`_getFilePatchesWithMergeConflictDialog`)

**Key File References:**
- Line 948825-948946: Composer variant
- Line 1142356-1142471: Background agent variant

### Conflict Detection

Conflicts are detected using git-style conflict markers:

```javascript
async _createPatchForFileWithoutComposer(file) {
    if (file.isDeleted) {
        return { hasConflicts: false, patchedContent: undefined, ... };
    }

    // Read current file content
    let currentContent = "";
    if (!file.isNew && await this.fileService.exists(file.path)) {
        currentContent = (await this.fileService.readFile(file.path)).value.toString();
    }

    // Generate and apply patch (3-way merge)
    const patchedContent = await this.gitContextService.generateAndApplyPatch(
        file.originalContent ?? "",   // Base content
        file.finalContent ?? "",      // Agent's changes
        currentContent                // Current local content
    );

    // Detect conflict markers
    const hasConflicts =
        /^<<<<<<<\s/m.test(patchedContent) &&
        /^=======$/m.test(patchedContent) &&
        /^>>>>>>>\s/m.test(patchedContent);

    return {
        hasConflicts,
        patchedContent,
        originalContent: file.originalContent ?? "",
        finalContent: file.finalContent
    };
}
```

### Conflict Dialog

When conflicts are detected, a dialog is shown with options:

```javascript
const dialogResult = await this.prettyDialogService.openDialog({
    title: hasConflicts
        ? "Merge Conflicts Detected"
        : "Another agent's changes have been applied",

    message: hasConflicts
        ? `Your local changes conflict with agent changes in ${count} file(s).`
        : "Do you want to keep changes from the other agent(s)?",

    primaryButton: hasPreviouslyApplied
        ? { id: "undo_apply", label: "Undo & Apply",
            hoverTooltip: "Undo other applied chats before applying this one." }
        : { id: "merge", label: "Merge manually",
            hoverTooltip: "Apply all agent changes, then review and resolve conflicts manually." },

    extraButtons: hasPreviouslyApplied
        ? [{ id: "merge", label: "Merge", type: "secondary",
             hoverTooltip: "Keep the other applied changes and merge this chat on top." }]
        : [
            { id: "stash", label: "Stash changes", type: "secondary",
              hoverTooltip: "Stash your local changes (including untracked files)." },
            { id: "overwrite", label: hasConflicts ? "Overwrite" : "Full Overwrite",
              type: "secondary",
              hoverTooltip: hasConflicts
                  ? "Overwrite files with merge conflicts with the agent's version."
                  : "Overwrite ALL files with the agent's version." }
          ],

    cancelButton: { id: "cancel", label: "Cancel" },

    dialogKey: `composer_apply_changes_pref_${composerId}`,
    shouldShowDontAskAgain: true,
    dontAskAgainLabel: "Don't show again for this agent."
});
```

### Dialog Choice Handling

| Choice | Behavior |
|--------|----------|
| `cancel` | Abort the apply operation |
| `merge` | Apply changes with conflict markers in files |
| `overwrite` | Use agent's version for conflicted files |
| `stash` | Run `git.stashIncludeUntracked` first, then apply |
| `undo_apply` | Undo other Best-of-N agents first, then apply |

### Opening Files with Conflicts

After applying with merge conflicts, the system opens each conflicted file at the conflict marker:

```javascript
async _handleOpenFilesWithMergeConflicts(filesWithConflicts) {
    if (filesWithConflicts.length > 0) {
        for (const { uri, content, isDeleted } of filesWithConflicts) {
            if (isDeleted) continue;

            // Find first conflict marker
            const start = content.indexOf("<<<<<<< ");
            const middle = content.indexOf("=======");
            const end = content.indexOf(">>>>>>> ");
            const markerLine = Math.min(start, middle, end);

            // Open file at conflict position
            const uriWithSelection = iD(uri, {
                startColumn: 1,
                startLineNumber: markerLine,
                endColumn: 1,
                endLineNumber: markerLine
            });
            await this.openerService.open(uriWithSelection);
        }

        // Show notification explaining conflict markers
        this.notificationService.notify({
            severity: Qs.Warning,
            message: `${count} file(s) have merge conflicts that need manual resolution.
The conflict markers show:
- "Current (Your changes)" - your local changes
- "Incoming (Cloud Agent changes)" - the AI's suggested changes`
        });
    }
}
```

---

## Undo Applied Changes (`undoAllAppliedChanges`)

**Key File References:**
- Line 945576-945707: `undoAllAppliedChanges()` implementation

### Undo Flow

```javascript
async undoAllAppliedChanges(composerId) {
    const handle = await this.composerDataService.getComposerHandleById(composerId);
    if (!handle) {
        this._notificationService.notify({ severity: Error, message: "Composer not found" });
        return;
    }

    // Get stored applied diffs
    const appliedDiffs = handle.data.appliedDiffs?.map(diff => ({
        ...diff,
        uri: _e.revive(diff.uri),
        workspaceUri: _e.revive(diff.workspaceUri),
        renamedFromUri: diff.renamedFromUri ? _e.revive(diff.renamedFromUri) : undefined
    }));

    if (!appliedDiffs || appliedDiffs.length === 0) {
        this._notificationService.notify({ severity: Warning, message: "No applied changes to undo" });
        return;
    }

    // Mark as undoing
    this.composerDataService.updateComposerDataSetStore(handle, set => {
        set("isUndoingWorktree", true);
    });

    try {
        for (const diff of appliedDiffs) {
            if (diff.renamedFromUri) {
                // Undo rename: delete renamed file, restore original
                await this.composerFileService.deleteFile({ uri: diff.workspaceUri });
                await this.composerFileService.writeFile({
                    uri: diff.renamedFromUri,
                    bufferOrReadableOrStream: Vs.fromString(diff.originalContent)
                });
            } else if (diff.originalContent === "") {
                // File was created by agent - delete it
                await this.composerFileService.deleteFile({ uri: diff.workspaceUri });
            } else if (diff.newContent === "") {
                // File was deleted by agent - restore it
                await this.composerFileService.writeFile({
                    uri: diff.workspaceUri,
                    bufferOrReadableOrStream: Vs.fromString(diff.originalContent)
                });
            } else {
                // Regular change - restore original content
                await this.composerFileService.writeFile({
                    uri: diff.workspaceUri,
                    bufferOrReadableOrStream: Vs.fromString(diff.originalContent)
                });
            }
        }

        // Clear applied state
        this.composerDataService.updateComposerDataSetStore(handle, set => {
            set("appliedDiffs", undefined);
            set("applied", false);
            // Restore reserved worktree if applicable
            if (!handle.data.gitWorktree && handle.data.reservedWorktree) {
                set("gitWorktree", { ...handle.data.reservedWorktree });
                set("reservedWorktree", undefined);
            }
        });

        this._notificationService.notify({
            severity: Info,
            message: `Successfully undid changes to ${appliedDiffs.length} file(s)`
        });
    } finally {
        this.composerDataService.updateComposerDataSetStore(handle, set => {
            set("isUndoingWorktree", false);
        });
    }
}
```

---

## Best-of-N Agent Coordination

When using Best-of-N mode with multiple agents, the system tracks which agents have been applied and handles conflicts between them.

**Key File References:**
- Line 1142304-1142354: `_hasAppliedInBestOfNGroup()`, `_undoOtherAppliedBestOfNComposers()`

### Detecting Applied Agents in Group

```javascript
_hasAppliedInBestOfNGroup(composerHandle, excludeSelf = false) {
    const data = composerHandle.data;

    const isApplied = (id) => {
        if (!id || (id === data.composerId && !excludeSelf)) return false;
        return !!this.composerDataService.getComposerData(id)?.applied;
    };

    // Check parent and all sub-composers
    if (data.isBestOfNParent || data.subComposerIds?.length > 0) {
        if (isApplied(data.composerId)) return true;
        for (const subId of data.subComposerIds ?? []) {
            if (isApplied(subId)) return true;
        }
        return false;
    }

    // Check sibling sub-composers
    if (data.isBestOfNSubcomposer) {
        const parentId = data.subagentInfo?.parentComposerId;
        if (isApplied(parentId)) return true;
        const siblings = parentId
            ? this.composerDataService.getComposerData(parentId)?.subComposerIds ?? []
            : [];
        for (const siblingId of siblings) {
            if (isApplied(siblingId)) return true;
        }
    }

    return isApplied(data.composerId);
}
```

### Undoing Other Applied Agents

```javascript
async _undoOtherAppliedBestOfNComposers(composerData) {
    const otherAppliedIds = this._getOtherAppliedBestOfNComposerIds(composerData);

    for (const id of otherAppliedIds) {
        try {
            await this.composerService.undoAllAppliedChanges(id);
        } catch (e) {
            const composer = this.composerDataService.getComposerData(id);
            const name = composer?.name?.trim() || id;
            throw new Error(`Undo failed for "${name}": ${e.message}`);
        }
    }
}
```

---

## Hunk-Level Accept/Reject (Inline Chat)

For inline chat (Cmd+K), changes are managed at the hunk level.

**Key File References:**
- Line 980000-980065: HunkData management
- Line 980042-980060: `discardChanges()` and `acceptChanges()` per hunk

### HunkData State Machine

```javascript
// Hunk states
const HunkState = {
    Pending: 0,    // Not yet decided
    Accepted: 1,   // User accepted
    Rejected: 2    // User rejected
};

// Per-hunk operations
const hunkInfo = {
    getState: () => data.state,
    isInsertion: () => hunk.original.isEmpty,

    getRangesN: () => {
        // Get ranges in the modified (new) model
        return data.textModelNDecorations.map(id =>
            this._textModelN.getDecorationRange(id));
    },

    getRanges0: () => {
        // Get ranges in the original model
        return data.textModel0Decorations.map(id =>
            this._textModel0.getDecorationRange(id));
    },

    discardChanges: () => {
        if (data.state === 0) {
            // Build edits to restore original content
            const edits = this._discardEdits(hunkInfo);
            this._textModelN.pushEditOperations(null, edits, () => null);
            data.state = 2;  // Mark rejected
            data.editState.applied--;
        }
    },

    acceptChanges: () => {
        if (data.state === 0) {
            // Copy modified content to original model
            const edits = [];
            const rangesN = hunkInfo.getRangesN();
            const ranges0 = hunkInfo.getRanges0();

            for (let i = 1; i < ranges0.length; i++) {
                const newText = this._textModelN.getValueInRange(rangesN[i]);
                edits.push(tp.replace(ranges0[i], newText));
            }

            this._textModel0.pushEditOperations(null, edits, () => null);
            data.state = 1;  // Mark accepted
        }
    }
};
```

### Discard All Hunks

```javascript
discardAll() {
    const allEdits = [];

    for (const hunkInfo of this.getInfo()) {
        if (hunkInfo.getState() === 0) {  // Only pending hunks
            allEdits.push(this._discardEdits(hunkInfo));
        }
    }

    const inverseEdits = [];
    this._textModelN.pushEditOperations(
        null,
        allEdits.flat(),
        (edits) => { inverseEdits.push(edits); return null; }
    );

    return inverseEdits.flat();
}

_discardEdits(hunkInfo) {
    const edits = [];
    const rangesN = hunkInfo.getRangesN();
    const ranges0 = hunkInfo.getRanges0();

    for (let i = 1; i < rangesN.length; i++) {
        const originalText = this._textModel0.getValueInRange(ranges0[i]);
        edits.push(tp.replace(rangesN[i], originalText));
    }

    return edits;
}
```

---

## Apply Confirmation UI Commands

**Key File References:**
- Line 756786-756834: `VAs` (Apply Changes Locally)
- Line 756836-756885: `PKc` (Checkout Locally)

### Apply Changes Locally Command

```javascript
class VAs extends St {
    static ID = "workbench.action.backgroundComposer.applyChangesLocally";
    static LABEL = "Apply Changes Locally";

    async run(accessor, args) {
        const composerMainService = accessor.get(uE);
        const dialogService = accessor.get(hF);

        // Show loading dialog
        dialogService.openDialog({
            title: "Applying changes locally...",
            message: "Applying changes locally. This may take a few seconds.",
            primaryButton: { id: "loading", label: "Applying", isLoading: true },
            dialogIcon: de.cloudTwo,
            dialogIconColor: "var(--cursor-text-primary)",
            dialogParentClass: "!z-[3000] pointer-events-none"
        });

        try {
            await composerMainService.focusEditor();
            await composerMainService.applyChangesFromBgAgent(args.bcId, args.options);
        } finally {
            dialogService.closeDialog();
        }
    }
}
```

### Checkout Locally Command

```javascript
class PKc extends St {
    static ID = "workbench.action.backgroundComposer.checkoutLocally";
    static LABEL = "Checkout Background Composer Locally";

    async run(accessor, args) {
        const composerMainService = accessor.get(uE);
        const dialogService = accessor.get(hF);

        dialogService.openDialog({
            title: "Checking out branch...",
            message: "Fetching and switching to the Cloud Agent branch.",
            primaryButton: { id: "loading", label: "Importing", isLoading: true },
            dialogIcon: de.cloudTwo,
            dialogIconColor: "var(--cursor-text-primary)"
        });

        try {
            await composerMainService.focusEditor();
            const composer = backgroundComposerDataService.data.backgroundComposers
                .find(c => c.bcId === args.bcId);

            if (!composer) {
                notificationService.error("Background Composer not found");
                return;
            }

            await composerMainService.checkoutLocally(composer);
        } finally {
            dialogService.closeDialog();
        }
    }
}
```

---

## Branch Checkout Prompt

When the current branch differs from the background agent's base branch:

**Key File References:**
- Line 1142629-1142700: `showBranchCheckoutPrompt()`

```javascript
async showBranchCheckoutPrompt(currentBranch, targetBranch, goBack) {
    if (currentBranch !== targetBranch) {
        const choices = [
            {
                label: `Checkout ${targetBranch}`,
                description: "Recommended to ensure correct base for changes"
            },
            {
                label: "Ignore branch difference",
                description: "Proceed anyway (changes might not apply correctly)"
            },
            {
                label: "Cancel",
                description: "Abort the operation"
            }
        ];

        const result = await this.quickInputService.pick(choices, {
            placeHolder: `Current branch does not match background agent base branch ${targetBranch}`,
            canPickMany: false,
            goBack: goBack
        });

        if (!result || result.label === "Cancel") return false;

        if (result.label.startsWith("Checkout")) {
            // Check for uncommitted changes first
            const diff = await this.gitContextService.getGitDiff();
            if (diff && diff.length > 0) {
                // Handle uncommitted changes...
            }
            // Checkout the target branch
            await this.gitContextService.checkout(targetBranch);
        }
    }
    return true;
}
```

---

## Telemetry Events

| Event | Type | Description |
|-------|------|-------------|
| `worktreeEvent` | `APPLY_TO_MAIN` | Changes applied from worktree/cloud to main |
| `worktreeEvent` | `UNDO_APPLY` | Applied changes undone |
| `git_worktree.undo_clicked` | Track | Undo button clicked |

---

## Questions for Further Investigation

1. **Speculative Mode Integration**: How does speculative-full-file mode interact with the apply flow?
2. **Real-time Sync**: How are changes synchronized between shadow workspace and server?
3. **Conflict Marker Format**: Are custom conflict markers used vs standard git format?
4. **Caching Strategy**: How long is the diffChangesHash cache valid?

---

## File References Summary

| Component | Lines | Purpose |
|-----------|-------|---------|
| applyChangesFromBgAgent | 1142158-1303 | Main apply flow for background agents |
| ShadowWorkspaceService | 831686-831789 | Shadow workspace lifecycle |
| NativeShadowWorkspaceManager | 1114236-1114303 | Native platform shadow workspace |
| _getFilePatchesWithMergeConflictDialog | 1142356-1142471 | Conflict detection and dialog |
| undoAllAppliedChanges | 945576-945707 | Undo applied changes |
| HunkData | 980000-980065 | Inline chat hunk management |
| VAs command | 756786-756834 | Apply Changes Locally action |
| generateAndApplyPatch | 296749-296751 | 3-way merge via git |
