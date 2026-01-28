# TASK-64: Best-of-N Agent Mode Worktree Selection and Apply Flow

## Overview

This document analyzes the complete flow for selecting a winner in Best-of-N agent mode and applying the winning worktree's changes to the main workspace. It covers:
- User selection interface (tab-based winner selection)
- The `applyWorktreeToCurrentBranch` method and its merge strategy
- Automatic cleanup of non-winning worktrees
- Undo functionality for applied changes
- Periodic worktree cleanup cron job

## Executive Summary

When users run Best-of-N mode (multiple models in parallel), each model operates in an isolated git worktree. The user can:
1. Switch between tabs to view different solutions
2. Manually select any tab and click "Keep" to apply that solution
3. Let the AI judge recommend a winner (displayed with thumbs-up indicator)

The apply process uses `_applyWorktreeToCurrentBranchViaMerge` which:
1. Copies changed files from worktree to main workspace
2. Automatically undoes any previously-applied Best-of-N results
3. Schedules background cleanup of the worktree
4. Preserves the worktree in `reservedWorktree` state for potential undo

## User Selection Mechanism

### Tab-Based Navigation

Best-of-N presents multiple parallel agent results as tabs in the composer UI. The user can click tabs to switch between different solutions.

**Location**: Lines 762323-762368

```javascript
// Tab rendering with click handling
U(ho, {
    get each() {
        return i.allConversationTabIds();  // All parallel agent IDs
    },
    children: h => {
        // Tab click handler
        const p = async () => {
            // 1. Set selected conversation
            i.setSelectedConversationComposerId(h);

            // 2. Update parent's selectedSubComposerId
            e.composerDataService.updateComposerDataSetStore(
                i.composerId(),
                Xe => Xe("selectedSubComposerId", h)
            );

            // 3. Set as last focused composer
            e.composerDataService.setLastFocusedComposerId(h);

            // 4. Track analytics event
            const Ze = f();
            if (Ze) {
                if (Ze.data.createdFromBackgroundAgent?.bcId !== void 0) {
                    const Je = e.composerService.getBackgroundAgentMetadata(Ze);
                    e.analyticsService.trackEvent("best_of_n.view_subcomposer", {
                        modelName: Ze.data.modelConfig?.modelName || "unknown",
                        bestOfNSubmitId: Je.bestOfNGroupId,
                        viewedComposerId: h
                    });
                } else {
                    const Je = e.composerService.getWorktreeMetadata(Ze);
                    e.analyticsService.trackEvent("best_of_n.view_subcomposer", {
                        modelName: Ze.data.modelConfig?.modelName || "unknown",
                        bestOfNSubmitId: Je.bestOfNGroupId,
                        viewedComposerId: h
                    });
                }
            }
        };
        // ... render tab with onClick: p
    }
})
```

### Winner Indicator Display

When the AI judge selects a winner, it's displayed with a thumbs-up indicator.

**Location**: Lines 762295-762318

```javascript
const n = ve(() => {
    const l = i.allConversationTabIds();
    for (const d of l) {
        let h;
        // Get handle for composer (current or from handles map)
        if (d === i.composerId()) {
            h = i.composerDataHandle();
        } else {
            h = e.composerDataService.allComposersData.selectedComposerHandles[d];
        }

        // Check if this is the judge's winner
        if (h?.data.bestOfNJudgeWinner === true) {
            const f = (h.data.bestOfNJudgeReasoning ?? "").trim();
            if (!f) return null;

            // Parse reasoning into summary and justification
            const { summary: g, justification: p } = t(f);
            return {
                composerId: d,
                summary: g,
                justification: p
            };
        }
    }
    return null;
});
```

The reasoning format uses `\n---\n` as a delimiter between summary and detailed justification.

### "Keep" Button Handling

The "Keep" button applies the currently selected worktree's changes to the main workspace.

**Location**: Lines 498825-498831

```javascript
const si = e.composerDataService.selectedComposerId;
if (si && e.composerDataService.getComposerData(si)?.gitWorktree?.worktreePath) {
    await e.composerService.applyWorktreeToCurrentBranch(si);
    return;
}
```

Additional "Keep" button handlers appear at:
- Line 552986: Agent layout unified mode
- Line 554060: Agent layout panel mode
- Line 733886/733916: Worktree controls
- Line 753053: Review changes dropdown
- Line 753359: Quick actions

## Composer ID Resolution

Before applying, the system resolves which composer's worktree to use.

**Location**: Lines 297828-297835

```javascript
resolveComposerIdToSelected(e) {
    const t = this.getComposerData(e);
    if (!t) return e;

    // If this is a Best-of-N parent with a selected subcomposer
    if (t.isBestOfNParent && t.selectedSubComposerId) {
        const n = t.selectedSubComposerId;
        // Verify the selected ID is valid
        if (t.subComposerIds?.includes(n)) return n;
    }

    return e;
}
```

This means when you click "Keep" on a Best-of-N parent composer, it automatically resolves to the currently-selected tab's subcomposer.

## Apply Worktree to Current Branch

### Entry Point

**Location**: Lines 945414-945417

```javascript
async applyWorktreeToCurrentBranch(e) {
    // Resolve to actual selected subcomposer
    const t = this.composerDataService.resolveComposerIdToSelected(e);
    await this._applyWorktreeToCurrentBranchViaMerge(t);
}
```

### Main Apply Logic

**Location**: Lines 948390-948710

The `_applyWorktreeToCurrentBranchViaMerge` method is the core apply logic:

```javascript
async _applyWorktreeToCurrentBranchViaMerge(e) {
    console.log("applyWorktreeToCurrentBranchViaMerge", e);

    const t = await this.composerDataService.getComposerHandleById(e);
    if (!t) {
        this._notificationService?.notify?.({
            severity: Qs.Error,
            message: "Composer not found"
        });
        return;
    }

    try {
        // 1. Mark as applying
        this.composerDataService.updateComposerDataSetStore(t, ce => {
            ce("isApplyingWorktree", true);
        });

        const n = t.data;
        const s = n.gitWorktree;

        if (!s) {
            this._notificationService?.notify?.({
                severity: Qs.Error,
                message: "Worktree not found"
            });
            return;
        }

        // 2. Resolve target branch
        const o = await this._resolveValidTargetBranch(undefined);

        // 3. Get workspace folder
        const a = this.workspaceContextService.getWorkspace().folders[0]?.uri;
        if (!a) throw new Error("No workspace open to apply changes into");

        const l = a.scheme === "file" ? a.fsPath : a.path;

        // 4. Save any pending files in the worktree
        await this._saveComposerFilesForWorktree(e, n);

        // 5. Get git root
        const h = (await this.gitContextService.executeGitCommand(l,
            ["rev-parse", "--show-toplevel"],
            { caller: "composerService._applyWorktreeToCurrentBranchViaMerge" }
        )).trim();

        const f = this.workspaceContextService.getWorkspace().folders[0]?.uri;
        if (!f) throw new Error("No workspace folder found");

        // 6. Get resources (changed files) from review service
        const { resources: g } = await this.reviewChangesService.getResources({
            composerId: e,
            mode: ld.All,  // All changes
            omitTextModelCreation: true,
            signal: undefined
        });

        // ... File processing and copying logic ...

        // 7. Check feature gate for replace behavior
        if (this.experimentService.checkFeatureGate("replace_files_on_worktree_apply")) {
            // Replace files directly (newer behavior)
            // ...
        }

        // 8. Track merge conflicts
        const ae = p.filter(pe => pe.hasMergeConflict);
        if (ae.length > 0) {
            const ce = ae.length;
            const pe = `${ce} ${ce === 1 ? "file" : "files"} have merge conflicts...`;
            this._notificationService.notify({
                severity: Qs.Warning,
                message: pe
            });
        }

        // 9. Store applied diffs
        this.composerDataService.updateComposerDataSetStore(t, ce => {
            ce("appliedDiffs", M);
        });

        // 10. Finalize and cleanup
        const B = await this.gitContextService.getCurrentBranch({ cwd: l }) ?? o;
        await this._finalizeApplyAndCleanup({
            composerId: e,
            handle: t,
            workspaceRoot: l,
            currentBranch: B,
            worktreePath: s.worktreePath,
            notifyMessage: H
        }, {
            skipWorktreeRemoval: true  // Keep worktree for undo
        });

        // 11. Preserve worktree state for undo
        const J = t.data.gitWorktree;
        this.composerDataService.updateComposerDataSetStore(t, ce => {
            if (J) {
                ce("reservedWorktree", { ...J });  // Save for undo
                ce("gitWorktree", void 0);         // Clear active worktree
            }
            ce("applied", true);
        });

        // 12. Focus the composer
        this._focusComposerAfterApply(t.data.composerId);

        // 13. Accept all diffs in the inline diff service
        this.acceptAllDiffs(e, "composer");

        // 14. Track analytics
        const te = this.composerUtilsService.getBestOfNGroupId(e);
        const ie = t.data.initialBestOfNAgentRequestId;
        this.analyticsService.trackEvent("git_worktree.apply_to_main", {
            modelName: t.data.modelConfig.modelName,
            bestOfNJudgeCompleted: t.data.bestOfNJudgeStatus === "done",
            bestOfNJudgeWinner: t.data.bestOfNJudgeWinner,
            bestOfNSubmitId: te,
            initialAgentRequestId: ie
        });

        // 15. Record telemetry event
        const ne = this.getWorktreeMetadata(t);
        this.telemService.recordCppSessionEvent({
            case: "worktreeEvent",
            event: {
                eventType: due.APPLY_TO_MAIN,
                // ... full metadata
            }
        });

    } catch (n) {
        if (!(n instanceof _vs)) {
            const s = this.formatGitErrorMessage(n,
                "Failed to apply worktree to current branch");
            this._notificationService?.notify?.({
                severity: Qs.Error,
                message: s
            });
        }
        throw n;
    } finally {
        // Clear applying state
        if (!t.isDisposed) {
            this.composerDataService.updateComposerDataSetStore(t, n => {
                n("isApplyingWorktree", false);
            });
        }
    }
}
```

## Non-Winner Cleanup

### Automatic Undo of Other Applied Best-of-N Results

When applying a worktree in Best-of-N mode, any other previously-applied results from the same group are automatically undone.

**Location**: Lines 945788-945821

```javascript
_getOtherAppliedBestOfNComposerIds(composerData) {
    const t = this.composerUtilsService.getBestOfNGroupId(composerData.composerId);
    const n = new Set();

    const s = (data) => {
        if (data) {
            n.add(data.composerId);
            for (const id of (data.subComposerIds ?? [])) {
                n.add(id);
            }
        }
    };

    // Collect all IDs in the Best-of-N group
    if (t === composerData.composerId) {
        s(composerData);
    } else {
        const o = this.composerDataService.getComposerData(t);
        s(o);
    }

    // Remove the current composer from the set
    n.delete(composerData.composerId);

    // Filter to only those that are currently applied
    const applied = [];
    for (const id of n) {
        if (this.composerDataService.getComposerData(id)?.applied) {
            applied.push(id);
        }
    }
    return applied;
}

async _undoOtherAppliedBestOfNComposers(composerData) {
    const otherIds = this._getOtherAppliedBestOfNComposerIds(composerData);
    for (const id of otherIds) {
        try {
            await this.undoAllAppliedChanges(id);
        } catch (error) {
            const data = this.composerDataService.getComposerData(id);
            const name = data?.name?.trim() ? data.name : id;
            const msg = error instanceof Error ? error.message : String(error);
            throw new Error(`Undo failed for "${name}": ${msg}`);
        }
    }
}
```

### Finalize Apply and Cleanup

**Location**: Lines 945822-945876

```javascript
async _finalizeApplyAndCleanup(e, t) {
    await this._finalizeApplyImmediate(e, {
        skipWorktreeRemoval: t?.skipWorktreeRemoval === true
    });

    // Schedule background cleanup if not skipping
    if (!t?.skipWorktreeRemoval) {
        this._scheduleBackgroundCleanup(e);
    }
}

async _finalizeApplyImmediate(e, t) {
    const { handle: n, currentBranch: s } = e;

    if (!t?.skipWorktreeRemoval) {
        this.composerDataService.updateComposerDataSetStore(n, a => {
            a("gitWorktree", undefined);
        });
    }

    if (t?.skipWorktreeRemoval) return;

    // Notify user
    const r = !!n.data.gitWorktree;
    const o = e.notifyMessage ?? (r
        ? `Applied changes to ${s} branch. The agent is now running locally. Use Undo Apply to go back to the worktree.`
        : `Applied changes to ${s} branch.`);

    this._notificationService?.notify?.({
        severity: Qs.Success,
        message: o
    });
}

_scheduleBackgroundCleanup(e) {
    const { composerId: t } = e;

    // Cancel existing cleanup timer if any
    const n = this._pendingBackgroundCleanups.get(t);
    if (n) {
        n.dispose();
        this._pendingBackgroundCleanups.delete(t);
    }

    // Schedule cleanup after 50ms
    const s = setTimeout(async () => {
        try {
            await this._finalizeApplyBackground(e);
        } finally {
            if (this._pendingBackgroundCleanups.get(t) === r) {
                this._pendingBackgroundCleanups.delete(t);
            }
        }
    }, 50);

    const r = {
        dispose: () => {
            clearTimeout(s);
            this._pendingBackgroundCleanups.delete(t);
        }
    };

    this._pendingBackgroundCleanups.set(t, r);
}
```

### Background Cleanup (Worktree Removal)

**Location**: Lines 945863-945876

```javascript
async _finalizeApplyBackground(e) {
    const { worktreePath: n } = e;
    if (!n) return;

    try {
        // Unregister cached code blocks
        const { composerId: t } = e;
        if (t) {
            const r = this.composerDataService.getWeakHandleOptimistic(t);
            if (r) {
                this.composerCodeBlockService.unregisterAllCachedCodeBlocks(r);
            }
        }

        // Remove the worktree
        await this.worktreeManagerService.removeWorktree(n);
    } catch (s) {
        this.logService.error(
            "[composer] Background cleanup failed for worktree:",
            n,
            s
        );
    }
}
```

## Undo Apply Functionality

Users can undo an applied worktree to revert changes.

**Location**: Lines 945576-945692

```javascript
async undoAllAppliedChanges(e) {
    const t = await this.composerDataService.getComposerHandleById(e);
    if (!t) {
        this._notificationService?.notify?.({
            severity: Qs.Error,
            message: "Composer not found"
        });
        return;
    }

    // Get list of applied diffs to revert
    const s = t.data.appliedDiffs?.map(r => ({
        ...r,
        worktreeUri: _e.parse(r.worktreeUri.toString())
    })) ?? [];

    // Mark as undoing
    this.composerDataService.updateComposerDataSetStore(t, g => {
        g("isUndoingWorktree", true);
    });

    try {
        // Process each applied diff
        for (const g of s) {
            // ... revert file logic ...
        }

        // Restore worktree state
        const a = t.data.reservedWorktree;  // Saved worktree reference
        const l = !!t.data.gitWorktree;

        this.composerDataService.updateComposerDataSetStore(t, g => {
            g("appliedDiffs", undefined);
            g("applied", false);

            // Restore worktree if it was reserved
            if (!l && a) {
                g("gitWorktree", { ...a });
            }
            if (a) {
                g("reservedWorktree", undefined);
            }
        });

        // Fire worktree change event
        if (!l && a) {
            this.composerDataService.fireWorktreeChanged(e, a.worktreePath);
        }

        // Track analytics
        const d = this.composerUtilsService.getBestOfNGroupId(e);
        const h = t.data.initialBestOfNAgentRequestId;
        this.analyticsService.trackEvent("git_worktree.undo_clicked", {
            modelName: t.data.modelConfig.modelName,
            bestOfNSubmitId: d,
            initialAgentRequestId: h
        });

        // Record telemetry
        // ...

    } finally {
        // Clear undoing state
        if (!t.isDisposed) {
            this.composerDataService.updateComposerDataSetStore(t, g => {
                g("isUndoingWorktree", false);
            });
        }
    }
}
```

## Periodic Worktree Cleanup

A cron job periodically cleans up old worktrees to prevent disk space exhaustion.

### Cleanup Service

**Location**: Lines 960064-960120

```javascript
class A1o extends Ve {
    constructor(e, t, n, s, r, o) {
        super();
        this.cronService = t;
        this.worktreeManagerService = n;
        this.configurationService = s;
        this.workspaceContextService = r;
        this.logService = o;

        // Initialize after startup
        e.when(3).then(() => {
            this.updateCleanupTask();
            this._register(this.configurationService.onDidChangeConfiguration(a => {
                if (a.affectsConfiguration(fes)) {  // worktreeCleanupIntervalHours
                    this.updateCleanupTask();
                }
            }));
        });
    }

    updateCleanupTask() {
        const e = this.configurationService.getValue(fes) ?? 6;  // Default 6 hours
        this.logService.info(
            `[WorktreeCleanupCron] Registering cleanup task with interval of ${e} hours`
        );
        this.registerCleanupTask(e);
    }

    registerCleanupTask(e) {
        if (this.taskDisposable) {
            this.taskDisposable.dispose();
            this.taskDisposable = undefined;
        }

        const t = e * 60 * 60 * 1000;  // Convert to milliseconds
        const n = {
            id: "worktree-cleanup-task",
            intervalMs: t,
            execute: async () => {
                try {
                    this.logService.info(
                        `[WorktreeCleanupCron] Running scheduled worktree cleanup (interval: ${e}h)`
                    );
                    await this.performCleanup();
                } catch (s) {
                    this.logService.error("[WorktreeCleanupCron] Error during cleanup:", s);
                }
            }
        };

        this.taskDisposable = this.cronService.registerTask(n);
    }

    async performCleanup() {
        this.logService.debug("[WorktreeCleanupCron] Scanning for worktrees to delete");

        const e = await this.worktreeManagerService.listWorkspaceWorktrees();
        const t = this.getCurrentWorkspaceName();
        const n = this.getMaxWorktreeCount();  // Default 20
        const s = 4;  // Buffer count

        if (e.length <= n) {
            this.logService.debug(
                `[WorktreeCleanupCron] No cleanup needed: ${e.length} worktrees (limit: ${n})`
            );
            return;
        }

        const o = e.length - n + s;  // Number to remove
        this.logService.info(
            `[WorktreeCleanupCron] Starting cleanup: ${e.length} worktrees exceeds limit of ${n}, removing ${o} oldest`
        );

        const a = await this.worktreeManagerService.cleanupWorktrees({
            maxCount: n,
            removeCountWhenExceeded: o,
            prefetchedWorktrees: e,
            dryRun: false
        });

        if (a.removed > 0) {
            this.logService.info(
                `[WorktreeCleanupCron] Cleanup completed: removed ${a.removed} worktrees, freed ${a.bytesFreed} bytes`
            );
        }
    }
}
```

### Worktree Protection Logic

Worktrees are protected from cleanup if they are young or actively in use.

**Location**: Lines 960632-960638

```javascript
shouldProtectWorktree(e) {
    // Protect worktrees younger than Bom (minimum age constant)
    if (Date.now() - e.createdAt < Bom) return true;

    // Protect worktrees with running composers
    const s = e.composerId;
    const r = this.getComposerDataService();
    const o = s && r ? r.getWeakHandleOptimistic(s) : undefined;
    return !!(o && r?.isComposerRunning(o));
}
```

The constant `Bom` is defined at line 960413:
```javascript
Bom = 600 * 1e3  // 600,000 ms = 10 minutes
```

## Configuration Settings

### Worktree Cleanup Settings

**Location**: Lines 182685-182686

```javascript
worktreeCleanupIntervalHours: Sse(6, -1, 0),  // Default 6 hours between cleanups
worktreeMaxCount: Sse(20, -1, 0),             // Maximum 20 worktrees before cleanup
```

### Feature Flag

**Location**: Lines 293885-293888

```javascript
replace_files_on_worktree_apply: {
    client: true,
    default: false  // Disabled by default
}
```

When enabled, this changes the apply behavior to directly replace files rather than using git operations.

## State Transitions During Apply

### Composer Data State Machine

```
Initial State:
  gitWorktree: { worktreePath, commitHash, branchName }
  reservedWorktree: undefined
  applied: false
  isApplyingWorktree: false

During Apply:
  isApplyingWorktree: true

After Successful Apply:
  gitWorktree: undefined
  reservedWorktree: { ...previous gitWorktree }  // Saved for undo
  applied: true
  isApplyingWorktree: false
  appliedDiffs: [list of applied file changes]

After Undo:
  gitWorktree: { ...reservedWorktree }  // Restored
  reservedWorktree: undefined
  applied: false
  isUndoingWorktree: false
  appliedDiffs: undefined
```

## UI State Indicators

### Apply Progress Indicator

**Location**: Lines 552657-552665 and 553696-553703

```javascript
Rt(() => {
    const ir = r()?.data.isApplyingWorktree === true;
    let nr;
    if (ir) {
        // Show spinner after 1 second delay
        nr = window.setTimeout(() => $i(true), 1000);
    } else {
        $i(false);
    }
    Mi(() => {
        if (nr !== undefined) {
            window.clearTimeout(nr);
        }
    });
});

const wn = ve(() => r()?.data.isApplyingWorktree === true);
const un = ve(() => r()?.data.isUndoingWorktree === true);
```

### Button Disabled States

**Location**: Lines 752975-752991

```javascript
const Pe = ve(() => {
    const tt = s();
    return tt.isApplyingWorktree === true || tt.isUndoingWorktree === true;
});

const ke = ve(() => {
    const tt = s();
    return tt.isApplyingWorktree === true || tt.isUndoingWorktree === true;
});
```

## Analytics Events

### Apply Event

**Location**: Lines 948676-948682

```javascript
this.analyticsService.trackEvent("git_worktree.apply_to_main", {
    modelName: t.data.modelConfig.modelName,
    bestOfNJudgeCompleted: t.data.bestOfNJudgeStatus === "done",
    bestOfNJudgeWinner: t.data.bestOfNJudgeWinner,
    bestOfNSubmitId: te,
    initialAgentRequestId: ie
});
```

### Undo Event

**Location**: Lines 945658-945662

```javascript
this.analyticsService.trackEvent("git_worktree.undo_clicked", {
    modelName: t.data.modelConfig.modelName,
    bestOfNSubmitId: d,
    initialAgentRequestId: h
});
```

### Telemetry Events

The WorktreeEvent enum defines event types:

**Location**: Lines 151094-151107

```javascript
i.UNSPECIFIED = 0
i.APPLY_TO_MAIN = 1
i.UNDO_APPLY = 2
i.VIEW_SUBCOMPOSER = 3
```

## Key Findings

1. **User Selection is Tab-Based**: Users select the winner by clicking on tabs representing different parallel agents. The selected tab's `selectedSubComposerId` is resolved when applying.

2. **Merge Strategy**: The apply process copies files from the worktree to the main workspace, not using git merge. File conflicts are detected and reported but not blocked.

3. **Undo Preservation**: When applying, the worktree reference is moved to `reservedWorktree`, allowing the user to undo and restore the worktree state.

4. **Automatic Sibling Undo**: When applying one Best-of-N result, any other previously-applied results from the same group are automatically undone.

5. **Delayed Cleanup**: Worktree removal is scheduled for background execution (50ms delay) to avoid blocking the UI.

6. **Protection Period**: Worktrees younger than 10 minutes are protected from cleanup.

7. **Configurable Limits**: Users can configure cleanup interval (default 6 hours) and max worktree count (default 20).

8. **Feature Gate**: The `replace_files_on_worktree_apply` feature gate controls whether files are replaced directly or processed through git operations.

## Related Analysis Documents

- TASK-101: Best-of-N Worktree Isolation and Parallel Execution Analysis
- TASK-105: Best-of-N Worktree Parallel Execution and Judging Mechanism
- TASK-57: Best-of-N Judge System Analysis
- TASK-56: Worktree Lifecycle Analysis

## Source Code Locations Summary

| Component | Line Number | Description |
|-----------|-------------|-------------|
| resolveComposerIdToSelected | 297828-297835 | Resolves parent to selected subcomposer |
| applyWorktreeToCurrentBranch | 945414-945417 | Public apply entry point |
| _applyWorktreeToCurrentBranchViaMerge | 948390-948710 | Main apply implementation |
| _getOtherAppliedBestOfNComposerIds | 945788-945810 | Find other applied composers in group |
| _undoOtherAppliedBestOfNComposers | 945811-945821 | Undo other applied results |
| _finalizeApplyAndCleanup | 945822-945826 | Finalize and schedule cleanup |
| _scheduleBackgroundCleanup | 945842-945862 | Schedule worktree removal |
| undoAllAppliedChanges | 945576-945692 | Undo applied worktree changes |
| WorktreeCleanupCron | 960064-960120 | Periodic cleanup service |
| shouldProtectWorktree | 960632-960638 | Protection logic for cleanup |
| Tab click handler | 762323-762368 | User selection via tabs |
| Winner display logic | 762295-762318 | Shows judge winner indicator |
| worktreeCleanupIntervalHours | 182685 | Cleanup interval setting (default 6h) |
| worktreeMaxCount | 182686 | Max worktrees setting (default 20) |
| Bom constant | 960413 | Minimum age for cleanup (10 min) |
