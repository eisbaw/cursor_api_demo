# TASK-101: Best-of-N Worktree Isolation and Parallel Execution Analysis

## Overview

This document analyzes how Cursor's Best-of-N system uses git worktrees to isolate parallel agents during execution. When users run multiple AI models simultaneously (the "Best-of-N" feature), each model operates in a completely isolated git worktree, preventing file conflicts and enabling independent execution.

## Architecture Summary

### Key Components

1. **Best-of-N Parent/Child Hierarchy**
   - `isBestOfNParent`: Boolean marking the parent composer that coordinates subcomposers
   - `isBestOfNSubcomposer`: Boolean marking child composers that execute in isolation
   - `subComposerIds[]`: Array of child composer IDs tracked by the parent

2. **Worktree Isolation**
   - Each subcomposer gets its own git worktree via `gitWorktree.worktreePath`
   - Worktrees are created in `~/.cursor/worktrees/<workspace>/<worktree-id>/`

3. **Coordination Identifiers**
   - `best_of_n_group_id`: Groups related parallel agents for the same task
   - `promptGroupId`: Server-side identifier for parallel agent group
   - `initialBestOfNAgentRequestId`: Links initial request across all parallel agents

## Parallel Agent Creation Flow

### Step 1: Subcomposer Creation (`createSubComposersForGroup`)

**Location**: Line 1141842-1141874

When a Best-of-N workflow starts, the system creates multiple subcomposers:

```javascript
async createSubComposersForGroup(groupComposers, parentComposerId, name) {
    const kickoffMessageId = this.composerDataService
        .getComposerData(parentComposerId)?.createdFromBackgroundAgent?.kickoffMessageId;
    const created = [];

    // Skip first (it's the parent), create subcomposers for rest
    for (let i = 1; i < groupComposers.length; i++) {
        const composer = groupComposers[i];

        // Create new composer data
        const composerData = {
            name: name,
            createdFromBackgroundAgent: {
                bcId: composer.bcId,
                shouldStreamMessages: true,
                kickoffMessageId: kickoffMessageId
            },
            isBestOfNSubcomposer: true,  // Mark as subcomposer
            modelConfig: {
                modelName: composer.modelDetails.modelName,
                maxMode: composer.modelDetails.maxMode
            },
            subagentInfo: {
                subagentType: "SPEC",
                parentComposerId: parentComposerId,  // Link to parent
                conversationLengthAtSpawn: 0
            }
        };

        await this.composerDataService.appendSubComposer(composerData);
        created.push({ composerId: composerData.composerId, bcId: composer.bcId });
    }
    return created;
}
```

### Step 2: Parent-Child Linking

**Location**: Lines 1141951-1952

```javascript
// Link subcomposers to parent
const subComposers = await this.createSubComposersForGroup(groupComposers, parent.composerId, name);

if (subComposers.length > 0) {
    this.composerDataService.updateComposerDataSetStore(parent.composerId, data => {
        data("subComposerIds", subComposers.map(s => s.composerId));
        data("isBestOfNParent", true);
    });
}
```

### Step 3: Worktree Creation Per Agent

Each parallel agent automatically gets a worktree when needed. The `createWorktree` method:

**Location**: Lines 298880-298913

```javascript
async createWorktree(composerId, lockLease, baseBranch, targetPath, excludeDirtyFiles) {
    try {
        this.updateComposerDataSetStore(composerId, d => d("isCreatingWorktree", true));

        // Reset code block data for clean slate
        this.updateComposerDataSetStore(composerId, d => {
            d("codeBlockData", {});
            d("originalFileStates", {});
            d("newlyCreatedFiles", []);
            d("newlyCreatedFolders", []);
        });

        // Create worktree via WorktreeManager
        const worktree = await this._worktreeManagerService.createWorktree({
            composerId: composerId,
            baseBranch: baseBranch,
            targetWorktreePath: targetPath,
            excludeDirtyFiles: excludeDirtyFiles
        }, lockLease);

        if (worktree) {
            const worktreeState = {
                worktreePath: worktree.path,
                commitHash: worktree.commitHash,
                branchName: worktree.branchName
            };

            // Store worktree reference in composer data
            this.updateComposerDataSetStore(composerId, d => d("gitWorktree", worktreeState));

            // Start watching worktree for file changes
            this._startWorktreeWatcher(composerId, worktreeState.worktreePath);

            return worktreeState;
        }
    } finally {
        this.updateComposerDataSetStore(composerId, d => d("isCreatingWorktree", false));
    }
}
```

## Isolation Mechanisms

### 1. Filesystem Isolation

Each agent operates in its own worktree directory:

```
~/.cursor/worktrees/
├── workspace-name-1/
│   ├── worktree-abc123/      <- Agent 1 (e.g., gpt-5)
│   │   ├── .git/
│   │   └── [project files]
│   ├── worktree-def456/      <- Agent 2 (e.g., claude-4.5)
│   │   ├── .git/
│   │   └── [project files]
│   └── worktree-ghi789/      <- Agent 3 (e.g., composer-1)
│       ├── .git/
│       └── [project files]
```

### 2. File Path Mapping

**Location**: Lines 730466-730474

When resolving file paths for a Best-of-N subcomposer, the system maps to the correct worktree:

```javascript
_getActiveWorktreePath() {
    const selectedSubComposerId = composerData.selectedSubComposerId;

    if (selectedSubComposerId) {
        const subComposerData = this._composerDataService.getComposerData(selectedSubComposerId);
        // Use subcomposer's worktree if it's a Best-of-N subcomposer
        if (subComposerData?.isBestOfNSubcomposer === true &&
            subComposerData?.gitWorktree?.worktreePath) {
            return subComposerData.gitWorktree.worktreePath;
        }
    }

    return composerData.gitWorktree?.worktreePath;
}
```

### 3. Independent File Watchers

Each worktree gets its own file watcher:

**Location**: Lines 298939-298949

```javascript
_startWorktreeWatcher(composerId, worktreePath) {
    this._stopWorktreeWatcher(composerId);  // Cleanup existing

    const uri = URI.file(worktreePath);
    const options = { recursive: true, excludes: [] };
    const watcher = this._fileService.watch(uri, options);

    this._worktreeWatchers.set(composerId, watcher);

    watcher.onDidChange(changes => {
        this._composerEventService.fireDidFilesChange(changes);
    });
}
```

### 4. Git Branch Isolation

Each worktree operates on its own branch, created from the same base:

```javascript
// WorktreeManager.createWorktree (line 960456-960488)
async createWorktree(options, lockLease) {
    // Acquire lock to prevent race conditions
    await lockLease.currentLock;

    let result;
    if (options?.baseBranch) {
        // Create worktree with new branch from base
        result = await this.gitContextService.createWorktreeWithBranch({
            baseBranch: options.baseBranch,
            branchName: options.branchName,
            targetPath: options.targetWorktreePath
        });
    } else {
        // Create worktree at current commit
        result = await this.gitContextService.createWorktree(
            options?.composerId,
            options?.targetWorktreePath
        );
    }

    // Store metadata for cleanup tracking
    const metadata = {
        path: result.worktreePath,
        commitHash: result.commitHash,
        createdAt: Date.now(),
        workspaceName: workspaceName,
        composerId: options?.composerId,
        branchName: result.branchName
    };

    this.worktreeMetadata.set(metadata.path, metadata);
    return new Worktree(metadata);
}
```

## Coordination Mechanism

### Best-of-N Group ID

**Location**: Lines 450273-450276

All agents in a Best-of-N run share the same group ID:

```javascript
getBestOfNGroupId(composerId) {
    const data = this._composerDataService.getComposerData(composerId);

    // If this is a subcomposer, return parent's ID as group ID
    if (data && data.isBestOfNSubcomposer && data.subagentInfo?.parentComposerId) {
        return data.subagentInfo.parentComposerId;
    }

    // Otherwise, this composer is its own group
    return composerId;
}
```

### WorktreeEvent Protobuf

**Location**: Lines 151018-151079

Telemetry events track worktree operations with full group context:

```protobuf
message WorktreeEvent {
    enum EventType {
        UNSPECIFIED = 0;
        APPLY_TO_MAIN = 1;
        UNDO_APPLY = 2;
        VIEW_SUBCOMPOSER = 3;
    }

    EventType event_type = 1;
    string model_name = 2;
    string best_of_n_group_id = 3;           // Links all parallel agents
    repeated string all_worktree_paths = 4;   // All worktrees in group
    string applied_worktree_path = 5;         // Which one was applied
    repeated WorktreeComposerMapping worktree_composer_mappings = 6;
    repeated BackgroundAgentComposerMapping background_agent_composer_mappings = 7;
    string applied_composer_id = 8;
    string viewed_composer_id = 9;
}

message WorktreeComposerMapping {
    string worktree_path = 1;
    string composer_id = 2;
}

message BackgroundAgentComposerMapping {
    string bc_id = 1;
    string composer_id = 2;
}
```

## Best-of-N Judge Integration

### Judge Service (`UiBestOfNJudgeService`)

**Location**: Lines 716398-716543

The judge collects diffs from all worktrees and selects the winner:

```javascript
async startBestOfNJudge(parentComposerId, candidateComposerIds, task) {
    const candidates = Array.from(new Set(candidateComposerIds));
    if (candidates.length < 2) return;

    this.setStatusFor(candidates, "judging");

    // 1. Collect git diffs from each candidate's worktree
    const diffs = await Promise.all(
        candidates.map(async composerId => {
            const worktreePath = this.composerDataService
                .getComposerData(composerId)?.gitWorktree?.worktreePath;

            if (!worktreePath) return;

            const diffResult = await this.gitContextService.getDiff({
                cwd: worktreePath,  // Each agent's isolated worktree
                mergeBase: true,
                maxUntrackedFiles: 200
            });

            if (diffResult?.diff) {
                return new UiBestOfNJudgeCandidate({
                    composerId: composerId,
                    diff: diffResult.diff
                });
            }
        })
    );

    const validCandidates = diffs.filter(d => d !== undefined);

    // 2. Wait for file edits (5s timeout)
    const hasEdits = await Promise.all(
        validCandidates.map(c => this.waitForFileEdits(c.composerId, 5000))
    );

    if (hasEdits.some(h => !h)) {
        console.info("[best-of-n judge] Skipping - at least one composer made zero edits");
        this.setStatusFor(candidates, "done");
        return;
    }

    // 3. Stream to server for judging
    const client = await this.aiService.aiClient();
    const request = new StreamUiBestOfNJudgeStartRequest({
        task: task,
        candidates: validCandidates
    });

    const stream = client.streamUiBestOfNJudge(request);

    // 4. Process server response
    for await (const message of stream) {
        if (message.case === "finalResult") {
            const winnerId = message.value.winnerComposerId;
            const reasoning = message.value.reasoning;

            this.setStatusFor(candidates, "done");

            if (winnerId && candidates.includes(winnerId)) {
                this.setWinner(winnerId, reasoning);
            }

            break;
        }
    }
}
```

## Data Structures

### ComposerData (Best-of-N Fields)

**Location**: Lines 215104-215131

```typescript
interface ComposerData {
    // Worktree state
    gitWorktree?: {
        worktreePath: string;
        commitHash: string;
        branchName?: string;
    };

    // Best-of-N flags
    isBestOfNSubcomposer: boolean;      // Is this a child agent?
    isBestOfNParent: boolean;           // Is this the parent coordinator?
    subComposerIds: string[];           // Child composer IDs (for parent)
    selectedSubComposerId?: string;     // Currently viewed subcomposer

    // Judge state
    bestOfNJudgeStatus?: "judging" | "done";
    bestOfNJudgeWinner: boolean;        // Is this the winner?
    bestOfNJudgeReasoning?: string;     // Why this was selected

    // Parent linkage (for subcomposers)
    subagentInfo?: {
        parentComposerId: string;
        subagentType: "SPEC" | "TASK" | "FIX_LINTS" | "DEEP_SEARCH";
        conversationLengthAtSpawn: number;
    };

    // Request tracking
    initialBestOfNAgentRequestId?: string;
}
```

### Worktree Metadata

**Location**: Lines 960400-960410

```typescript
interface WorktreeMetadata {
    path: string;               // Filesystem path
    commitHash: string;         // Base commit hash
    createdAt: number;          // Unix timestamp
    workspaceName: string;      // Parent workspace name
    id: string;                 // Unique identifier
    composerId?: string;        // Associated composer
    lastAccessedAt?: number;    // Last touch time
    branchName?: string;        // Current branch
    sizeInBytes?: number;       // Disk usage
}
```

## UI Integration

### Determining Worktree Display Mode

**Location**: Lines 715033

```javascript
// Should show worktree controls?
const showWorktreeControls = computed(() => {
    // Hide if already in background mode
    if (mode() === "background") return true;

    // Hide worktree toggle for Best-of-N (worktree is automatic)
    if (data.isBestOfNSubcomposer || data.isBestOfNParent || data.gitWorktree) {
        return false;
    }

    return canUseWorktree && (mode() === "agent" || mode() === "plan" || mode() === "chat");
});
```

### Setup Warning Suppression

**Location**: Line 489554

Best-of-N subcomposers don't show worktree setup warnings:

```javascript
// Don't show worktree setup warning for Best-of-N subcomposers
if (composerData.isBestOfNSubcomposer !== true) {
    this.worktreeSetupWarningShownCount.set(count + 1);
}
```

## Execution Timeline

```
1. User submits task with multiple models selected
   |
   v
2. Parent composer created with models: ["gpt-5", "claude-4.5", "composer-1"]
   |
   +---> Track as isBestOfNParent = true
   |
   v
3. createSubComposersForGroup() called
   |
   +---> Create subcomposer for model 2 (claude-4.5)
   |     - isBestOfNSubcomposer = true
   |     - parentComposerId = parent.composerId
   |
   +---> Create subcomposer for model 3 (composer-1)
         - isBestOfNSubcomposer = true
         - parentComposerId = parent.composerId
   |
   v
4. Parent.subComposerIds = [sub1.composerId, sub2.composerId]
   |
   v
5. Each agent starts executing in parallel
   |
   +---> Each agent calls createWorktree() when making changes
   |     - Creates isolated worktree at ~/.cursor/worktrees/
   |     - Starts file watcher for that worktree
   |
   v
6. Agents work independently in isolated worktrees
   |
   +---> Agent 1: ~/.cursor/worktrees/proj/worktree-abc/
   +---> Agent 2: ~/.cursor/worktrees/proj/worktree-def/
   +---> Agent 3: ~/.cursor/worktrees/proj/worktree-ghi/
   |
   v
7. Agents complete execution
   |
   v
8. Best-of-N Judge triggered
   |
   +---> Collect git diffs from each worktree
   +---> Send to server for evaluation
   +---> Receive winner and reasoning
   |
   v
9. Winner marked with bestOfNJudgeWinner = true
   |
   v
10. User can apply winning worktree to main branch
```

## Key Source Locations

| Component | Line Number | Description |
|-----------|-------------|-------------|
| UiBestOfNJudgeService | 716398-716543 | Coordinates judging process |
| createSubComposersForGroup | 1141842-1141874 | Creates parallel subcomposers |
| WorktreeManager.createWorktree | 960456-960488 | Creates isolated worktrees |
| ComposerDataService.createWorktree | 298880-298913 | High-level worktree creation |
| getBestOfNGroupId | 450273-450276 | Group ID resolution |
| WorktreeEvent protobuf | 151018-151079 | Telemetry schema |
| ComposerData defaults | 215104-215131 | Data structure with BON fields |

## Configuration

### Default Best-of-N Models

**Location**: Line 182750

```javascript
bestOfNDefaultModels: ["composer-1", "claude-4.5-opus-high", "gpt-5.1-codex"]
```

### Maximum Parallel Agents

The UI supports up to 8 parallel agents simultaneously (referenced in parallel agent walkthrough).

### Feature Flags

| Flag | Default | Description |
|------|---------|-------------|
| `worktrees_bon_judge` | true | Enable Best-of-N judging |
| `worktree_nal_only` | true | NAL-only mode for worktrees |

## Key Insights

1. **Complete Filesystem Isolation**: Each parallel agent operates in a separate git worktree, ensuring no file conflicts during concurrent execution.

2. **Lazy Worktree Creation**: Worktrees are created on-demand when an agent first needs to modify files, not upfront.

3. **Parent-Child Hierarchy**: The parent composer tracks all subcomposers and their worktrees, enabling coordinated cleanup and winner selection.

4. **Diff-Based Judging**: The judge compares git diffs (changes made), not final file states, allowing fair comparison of different approaches.

5. **Server-Side Evaluation**: The actual winner selection logic runs server-side; the client only collects diffs and displays results.

6. **Worktree Lock Lease**: A locking mechanism prevents race conditions during concurrent worktree creation.

## Open Questions

1. **Worktree Reuse**: Can worktrees be reused across Best-of-N runs, or are they always created fresh?

2. **Partial Failure**: How does the system handle cases where some agents complete but others fail?

3. **Conflict Detection**: Is there any cross-worktree conflict detection before the judge runs?

4. **Resource Limits**: What prevents resource exhaustion with 8 parallel agents creating worktrees?

## Parallel Agent Workflow Configuration

### Server-Side Parallel Agent Config

**Location**: Lines 295560-295576

The parallel agent system uses server-configurable ensemble settings:

```javascript
parallel_agent_ensemble_config: {
    client: false,  // Server-controlled
    fallbackValues: {
        models: ["gpt-5.1-codex-high", "claude-4.5-sonnet-thinking",
                 "gpt-5-codex-high", "claude-4.5-sonnet-thinking"],
        gatherTimeoutMs: 300 * 1000,           // 5 minute timeout to collect results
        gatherMinSuccessPercentage: 0.5,        // Need 50% of agents to succeed
        gatherMinSuccessCount: null             // Or specific minimum count
    }
},
parallel_agent_synthesis_config: {
    client: false,  // Server-controlled
    fallbackValues: {
        strategy: "pairwise_tournament",        // Tournament comparison strategy
        synthesisModel: "gpt-5.1-codex-high",   // Model used for judging
        fanoutSize: null
    }
}
```

### Workflow Phases

**Location**: Lines 338453-338475

The parallel agent workflow progresses through defined phases:

```javascript
ParallelAgentWorkflowStatusUpdate.Phase = {
    UNSPECIFIED: 0,
    STARTING: 1,          // Workflow initialization
    CHILDREN_RUNNING: 2,   // Parallel agents executing
    GATHERING: 3,          // Collecting results from agents
    SYNTHESIZING: 4,       // Comparing/judging results
    COMPLETED: 5,          // Winner selected
    ERROR: 6               // Workflow failed
}
```

### Synthesis Strategies

**Location**: Lines 335701-335712

Three synthesis strategies determine how winners are selected:

```javascript
ParallelAgentWorkflowSynthesisStrategy = {
    UNSPECIFIED: 0,
    SINGLE_AGENT: 1,           // No comparison (single agent)
    FANOUT_VOTING: 2,          // Multiple judges vote
    PAIRWISE_TOURNAMENT: 3     // Tournament bracket comparison (default)
}
```

## Worktree Lock Lease System

### Serializing Worktree Creation

**Location**: Lines 960662-960668

Worktree creation is serialized via a lock lease to prevent race conditions:

```javascript
acquireWorktreeLockLease() {
    const previousLock = this._worktreeCreationLock;
    let releaseFn;

    // Chain locks - each new lease waits for previous
    this._worktreeCreationLock = new Promise(resolve => {
        releaseFn = resolve;
    });

    return new WorktreeLockLease(previousLock, releaseFn);
}
```

### Lock Lease Usage in Best-of-N

**Location**: Line 766645

When submitting multiple models, only the first agent gets the lock lease:

```javascript
// Acquire single lock lease for all parallel agents
const worktreeLockLease = ok.length > 1
    ? e.worktreeManagerService.acquireWorktreeLockLease()
    : null;

// Only first agent (fM === 0) gets the lease
worktreeLockLease: fM === 0 && worktreeLockLease !== null
    ? worktreeLockLease
    : undefined
```

This ensures worktrees are created sequentially even when agents run in parallel.

## Best-of-N Execution Flow (Detailed)

### Multi-Model Submission Detection

**Location**: Lines 766620-766624

```javascript
const isBackgroundAgent = !!composerData.createdFromBackgroundAgent?.bcId;
const mode = getCurrentMode();
const isValidMode = mode === "agent" || mode === "plan" || mode === "chat";

// Trigger Best-of-N when multiple models selected
const shouldCreateSubComposers =
    !isUndoView &&
    !hasPendingMcpChanges &&
    selectedModels.length > 1 &&
    !isBackgroundAgent &&
    isValidMode;
```

### Subcomposer Deep Clone

**Location**: Lines 766666-766675

Each subcomposer is a deep clone with model override:

```javascript
// Deep clone the parent composer for subcomposer
const subComposerData = await composerUtils.deepCloneComposer(parentData, viewState, {
    skipCapabilities: true
});

// Override model configuration
subComposerData.modelConfig = {
    ...modelConfig,
    modelName: selectedModel,
    maxMode: useMaxMode || !supportsNonMaxMode
};

// Mark as subcomposer
subComposerData.isBestOfNSubcomposer = true;
subComposerData.name = parentData.name ?? (truncatedPrompt || "New Agent");
subComposerData.unifiedMode = parentData.unifiedMode;
```

### Parallel Submission via Promise.allSettled

**Location**: Lines 766707-766713

All agents are submitted in parallel, with failures isolated:

```javascript
// Submit all agents in parallel
const submissions = [];
for (let i = 0; i < selectedModels.length; i++) {
    submissions.push(submitAgent(selectedModels[i], i));
}

// Wait for all to settle (complete or fail)
const results = await Promise.allSettled(submissions);

// Check for any failures
const firstFailure = results.find(r => r.status === "rejected");
if (firstFailure) {
    rejectionReason = firstFailure.reason;
}
```

## Worktree Cleanup and Resource Management

### Worktree Cleanup Cron

**Location**: Lines 960060-960125

Automatic cleanup runs periodically to prevent resource exhaustion:

```javascript
class WorktreeCleanupCron {
    updateCleanupTask() {
        const intervalHours = this.configurationService.getValue(CLEANUP_INTERVAL_KEY) ?? 6;
        const intervalMs = intervalHours * 60 * 60 * 1000;

        this.cronService.registerTask({
            interval: intervalMs,
            run: async () => {
                try {
                    await this.performCleanup();
                } catch (error) {
                    this.logService.error("[WorktreeCleanupCron] Error during cleanup:", error);
                }
            }
        });
    }

    async performCleanup() {
        const worktrees = await this.worktreeManagerService.listWorkspaceWorktrees();
        const maxCount = this.getMaxWorktreeCount();  // Default: 20
        const buffer = 4;  // Remove extra to avoid frequent cleanups

        if (worktrees.length <= maxCount) {
            return;  // No cleanup needed
        }

        const removeCount = worktrees.length - maxCount + buffer;

        await this.worktreeManagerService.cleanupWorktrees({
            maxCount: maxCount,
            removeCountWhenExceeded: removeCount,
            prefetchedWorktrees: worktrees,
            dryRun: false
        });
    }

    getMaxWorktreeCount() {
        const configured = this.configurationService.getValue(MAX_WORKTREES_KEY);
        if (typeof configured !== "number" || Number.isNaN(configured)) {
            return 20;  // Default
        }
        return Math.max(1, Math.floor(configured));
    }
}
```

### Configuration Settings

**Location**: Lines 450728-450741

```javascript
{
    // Cleanup interval
    [CLEANUP_INTERVAL_KEY]: {
        type: "number",
        default: 6,
        description: "Interval in hours for periodic worktree cleanup. Default is 6 hours."
    },

    // Maximum worktrees
    [MAX_WORKTREES_KEY]: {
        type: "number",
        default: 20,
        description: "Maximum number of worktrees to keep per workspace. Default is 20 worktrees."
    },

    // Disable Best-of-N recommender
    [DISABLE_BON_KEY]: {
        type: "boolean",
        default: false,
        description: "Disable the Best-of-N recommender feature that judges and recommends the best result from multiple parallel agent runs."
    }
}
```

## BcIdWindow Isolation

### Background Composer ID Window

**Location**: Lines 14771, 1120387

Background agent composers run in isolated "BcId Windows" for visual separation:

```javascript
// Global flag for BcId window mode
LVe = {
    isBcIdWindow: false
}

// Detection based on remote authority
function initializeWindow(options) {
    if (options.windowInWindow !== undefined) {
        IQ.parentWindowId = options.windowInWindow;
        IQ.parentWindowDimensions = options.windowInWindowParentDimensions;
    }

    // Check if this is a background composer window
    if (isBcIdRemoteAuthority(options.remoteAuthority)) {
        LVe.isBcIdWindow = true;
    }
}
```

### BcIdWindow Behavioral Changes

When `isBcIdWindow` is true:
1. Repository tracking is skipped (line 1036953-1036967)
2. Default view container changes (line 290955-290960)
3. Workspace folder tracking is disabled (line 1036961-1036967)

## Ensemble Status Tracking

### Parent/Child Enumeration

**Location**: Lines 335692-335700

```javascript
EnsembleStatus = {
    UNSPECIFIED: 0,
    PARENT: 1,      // Coordinating composer
    CHILD: 2        // Parallel subcomposer
}
```

### Protobuf Field in BackgroundComposer

**Location**: Lines 337373, 337543-337550

```javascript
class BackgroundComposer {
    // ... other fields ...
    ensembleStatus = 0;  // EnsembleStatus enum
    workflowId;          // Parallel workflow identifier
    // ...
}

// Field definition
{
    no: 32,
    name: "ensemble_status",
    kind: "enum",
    T: EnsembleStatus
}
```

## Analytics Events

### Best-of-N Tracking

**Location**: Lines 766678-766701, 766709-766711

```javascript
// Per-agent submission tracking
analyticsService.trackEvent("best_of_n.submit", {
    model: modelName,
    bestOfNSubmitId: parentComposerId
});

// Per-agent request tracking
analyticsService.trackEvent("best_of_n.agent_request", {
    model: modelName,
    bestOfNSubmitId: parentComposerId,
    agentRequestId: requestId,
    composerId: agentComposerId
});

// Multi-model submission tracking
analyticsService.trackEvent("agent_layout.multi_model_submission", {
    numModels: selectedModels.length
});

// Model picker interactions
analyticsService.trackEvent("composer.ensemble_model_picker.button_clicked", {
    modelCount: currentCount,
    nextModelCount: newCount
});
```

## Best-of-N Promotion Feature

### Promotion Configuration

**Location**: Lines 295517-295524

```javascript
best_of_n_promotion_config: {
    client: true,
    fallbackValues: {
        cooldownMs: 300 * 60 * 1000,        // 5 hour cooldown
        promptLengthThreshold: 256,          // Min prompt length to trigger
        promptCountThreshold: 2,             // Min prompts before suggesting
        dismissLimit: 3                      // Max dismissals before stopping
    }
}
```

### Free Best-of-N Promotion

**Location**: Lines 278352-278356

The server can offer free Best-of-N trials:

```javascript
// In model configuration response
{
    no: 8,
    name: "free_best_of_n_promotion",
    kind: "message",
    T: FreeBestOfNPromotion,
    opt: true
}
```

## Key Insights (Updated)

1. **Sequential Worktree Creation**: Despite parallel agent execution, worktree creation is serialized via lock leases to prevent git conflicts.

2. **Configurable Limits**: Maximum 20 worktrees by default (configurable), with cleanup every 6 hours.

3. **8 Agent Maximum**: UI supports up to 8 parallel agents as mentioned in walkthrough (line 760432).

4. **Pairwise Tournament Default**: Winner selection uses tournament-style pairwise comparisons by default.

5. **Server-Controlled Config**: Ensemble and synthesis configs are server-controlled, allowing A/B testing of strategies.

6. **BcId Window Isolation**: Background agents run in special windows with modified behavior for visual separation.

7. **Promise.allSettled Pattern**: Parallel execution uses allSettled to collect all results even if some fail.

8. **Shared Name Generation**: All subcomposers receive the same AI-generated name for visual consistency.

## Related Tasks

- TASK-56: Worktree Lifecycle Analysis (prerequisite)
- TASK-55: Tournament Algorithm Analysis (judge selection logic)
- TASK-57: Best-of-N Judge System Analysis (judge service details)
- TASK-15: Parallel Agent Workflow Analysis (workflow orchestration)
- TASK-54: Parallel Coordination Analysis (related coordination mechanisms)
