# TASK-105: Best-of-N Worktree Parallel Execution and Judging Mechanism

## Overview

This document provides a deep dive into how Cursor's Best-of-N system orchestrates parallel agent execution across multiple git worktrees and how the judging mechanism selects the best result. This analysis focuses on the execution flow, coordination mechanisms, and the worktree lock lease system that ensures safe parallel creation.

## Executive Summary

Best-of-N enables running multiple AI models (e.g., "composer-1", "claude-4.5-opus-high", "gpt-5.1-codex") simultaneously on the same task. Each model operates in an isolated git worktree, with the results compared by a server-side judge that selects the best implementation.

Key mechanisms:
1. **WorktreeLockLease** - Serializes worktree creation to prevent race conditions
2. **Parent/Subcomposer hierarchy** - Coordinates parallel agents
3. **Server-side StreamUiBestOfNJudge** - Evaluates results and picks winner
4. **Automatic undo** - Cleans up non-winning worktrees on apply

## Architecture Components

### 1. Composer Hierarchy

**Parent Composer State**:
```javascript
// Line 215127-215131
isBestOfNSubcomposer: !1,      // False for parent
isBestOfNParent: !1,            // True when coordinating N agents
bestOfNJudgeStatus: void 0,     // "judging" | "done" | undefined
bestOfNJudgeWinner: !1,         // Not relevant for parent
bestOfNJudgeReasoning: void 0,  // Not relevant for parent

// Line 215104
subComposerIds: [],             // Array of child composer IDs
selectedSubComposerId: void 0   // Currently viewed child
```

**Subcomposer State**:
```javascript
isBestOfNSubcomposer: !0,       // True for children
subagentInfo: {
    parentComposerId: "...",    // Link back to parent
    conversationLengthAtSpawn: 0
}
```

### 2. Default Model Configuration

**Location**: Lines 182747-182751

```javascript
composer: {
    defaultModel: scs,          // Dynamic based on time
    fallbackModels: [],
    bestOfNDefaultModels: ["composer-1", "claude-4.5-opus-high", "gpt-5.1-codex"]
}
```

Note: `scs` is computed dynamically based on promotional periods:
```javascript
// Lines 182744-182746
HEl = new Date("2025-11-24T20:00:00Z");
$El = new Date("2025-12-06T11:59:00Z");
scs = Date.now() >= HEl.getTime() && Date.now() < $El.getTime()
    ? "claude-4.5-opus-high-thinking" : "default"
```

### 3. User Preferences

**Location**: Lines 182638-182639

```javascript
bestOfNCountPreference: Sse(1),           // Number of parallel models (1 = disabled)
bestOfNEnsemblePreferences: q1e("{}"),    // JSON map: count -> model array
```

The ensemble preferences allow users to configure which models to use for different counts.

## Parallel Execution Flow

### Step 1: Multi-Model Submission Detection

**Location**: Lines 766614-766623

When a user submits with multiple models:

```javascript
// Check if this is a Best-of-N scenario
const UV = p().isBestOfNParent === !0 || (p().subComposerIds?.length ?? 0) > 0;
const mb = p().isBestOfNSubcomposer === !0 || !!p().gitWorktree;

// Extract models (comma-separated in modelName)
const ED = p().modelConfig?.modelName || "default";
const RB = ED.includes(",") ? ED.split(",").map(gE => gE.trim()) : [ED];
let ok = RB.length > 0 ? RB : [];

// Determine if parallel execution is needed
const h8 = !!p().createdFromBackgroundAgent?.bcId;  // Not from background agent
const NF = J();  // Current mode
const Zoe = NF === "agent" || NF === "plan" || NF === "chat";
const rz = !UV && !mb && ok.length > 1 && !h8 && Zoe;  // Multiple models, not already in BON
```

### Step 2: Worktree Lock Lease Acquisition

**Location**: Line 766645

Before creating worktrees, the system acquires a lock lease to serialize worktree creation:

```javascript
rte = Hr.u(ok.length > 1 ? e.worktreeManagerService.acquireWorktreeLockLease() : null)
```

**Lock Lease Implementation** (Lines 960662-960668):

```javascript
acquireWorktreeLockLease() {
    const e = this._worktreeCreationLock;  // Current lock promise
    let t;
    this._worktreeCreationLock = new Promise(n => {
        t = n  // Resolver for next waiter
    });
    return new s$r(e, t);  // WorktreeLockLease
}
```

**WorktreeLockLease Class** (Line 296805):
- `currentLock`: Promise that resolves when previous creation completes
- `dispose()`: Releases the lock for next waiter

This creates a queue system where only one worktree is created at a time, preventing race conditions in git operations.

### Step 3: Parallel Subcomposer Creation

**Location**: Lines 766648-766707

For each model (starting from index 0):

```javascript
for (let fM = 0; fM < ok.length; fM++) {
    const VV = ok[fM];  // Model name
    const LB = (async () => {
        let HV, Ywe;

        if (fM === 0) {
            // First model uses the existing (parent) composer
            HV = Jr.data.composerId;
            Ywe = io;  // Bubble ID
            ox.push(HV);
        } else {
            // Create new subcomposer for additional models
            const KXe = e.modelConfigService.getModelConfig("composer");
            const YXe = {
                ...KXe,
                modelName: VV,
                maxMode: XY || !c6e
            };

            let mM;
            if (Sc()) {  // Using NAL (New Agent Layer)
                const oz = e.instantiationService.invokeFunction(WCt => WCt.get(q_));
                mM = await oz.deepCloneComposer(p(), ate, { skipCapabilities: !0 });
                mM.modelConfig = YXe;
                mM.isBestOfNSubcomposer = !0;
                mM.name = Jr.data.name ?? (PB || "New Agent");
            } else {
                mM = HO(YXe);  // Create new composer data
                mM.isBestOfNSubcomposer = !0;
                mM.name = Jr.data.name ?? (PB || "New Agent");
                mM.isNAL = p().isNAL;
            }

            // Set up capabilities and context
            const XXe = WZ(e.instantiationService, mM.composerId);
            mM.capabilities = XXe;
            mM.context = u3(p().context);  // Clone context

            // Register subcomposer
            await e.composerDataService.appendSubComposer(mM);
            await e.composerDataService.updateComposerDataSetStore(mM.composerId,
                oz => oz("isBestOfNSubcomposer", !0));

            // Link to parent
            await e.composerDataService.updateComposerDataSetStore(Jr.data.composerId,
                oz => oz("subComposerIds", ate => [...ate, mM.composerId]));
            await e.composerDataService.updateComposerDataSetStore(Jr.data.composerId,
                oz => oz("isBestOfNParent", !0));

            // Set subagent info
            await e.composerDataService.updateComposerDataSetStore(mM.composerId,
                oz => oz("subagentInfo", ate => ({
                    ...ate ?? {},
                    parentComposerId: Jr.data.composerId,
                    conversationLengthAtSpawn: Jr.data.fullConversationHeadersOnly.length
                })));

            HV = mM.composerId;
            Ywe = void 0;
            ox.push(HV);
        }

        // Determine if worktree is needed
        const IIe = Ss?.createWorktreeForAgent === !0 ||
                    ok.length > 1 ||
                    e.composerDataService.getComposerData(HV)?.pendingCreateWorktree === !0;

        // Submit chat with worktree creation flag
        await e.composerChatService.submitChatMaybeAbortCurrent(HV, xn, {
            richText: u0,
            bubbleId: Ywe,
            createWorktreeForAgent: IIe,
            modelOverride: VV,
            worktreeLockLease: fM === 0 && rte !== null ? rte : void 0,  // First gets the lease
            tryUseBestOfNPromotion: QY
        });
    })();

    gE.push(LB);  // Add to promise array
}

// Wait for all parallel submissions
const W$ = (await Promise.allSettled(gE)).find(fM => fM.status === "rejected");
```

### Step 4: Worktree Creation (Per Agent)

**Location**: Lines 960456-960488

Each agent's worktree is created when the submission reaches the agent layer:

```javascript
async createWorktree(e, t) {
    const n = t ?? this.acquireWorktreeLockLease();
    await n.currentLock;  // Wait for previous worktree creation

    const s = e?.composerId || `manual-${Date.now()}`;
    try {
        let r;
        if (e?.baseBranch) {
            r = await this.gitContextService.createWorktreeWithBranch({
                baseBranch: e.baseBranch,
                branchName: e.branchName,
                worktreeFilePath: e.worktreeFilePath,
                targetPath: e.targetWorktreePath,
                excludeDirtyFiles: e.excludeDirtyFiles
            });
        } else {
            r = await this.gitContextService.createWorktree(s, e?.targetWorktreePath);
        }

        if (!r) return;

        // Get workspace name
        const o = this.workspaceContextService.getWorkspace();
        const a = o.folders.length > 0 ? Bl(o.folders[0].uri.path) : "default";

        // Create metadata
        const l = {
            path: r.worktreePath,
            commitHash: r.commitHash,
            createdAt: Date.now(),
            workspaceName: a,
            id: Bl(r.worktreePath),
            composerId: e?.composerId,
            lastAccessedAt: Date.now(),
            branchName: r.branchName || e?.branchName
        };

        this.worktreeMetadata.set(l.path, l);
        this.saveMetadata();

        const d = this.instantiationService.createInstance(lwt, l);
        this._onDidCreateWorktree.fire(d);

        return d;
    } finally {
        n.dispose();  // Release lock for next worktree
    }
}
```

**Worktree Path Structure**:
```
~/.cursor/worktrees/<workspace-name>/<worktree-id>/
```

### Step 5: Shared Name Generation

**Location**: Lines 766714-766719

After all agents are running, a shared name is generated and applied:

```javascript
const fM = await YY;  // AI-generated name
await Promise.all(ox.map(VV =>
    e.composerDataService.updateComposerDataAsync(VV, LB => LB("name", fM))
));
```

## Judging Mechanism

### Judge Trigger Conditions

**Location**: Lines 766720-766729

```javascript
const Kwe = e.configurationService.getValue(Zwr) ?? !1;  // disableBestOfNRecommender
const ote = Jr.data.unifiedMode === "plan";

if (l() && !Kwe && !ote) {  // Feature flag enabled, not disabled, not plan mode
    try {
        const fM = [Jr.data.composerId, ...ox];  // Parent + all subcomposers
        await e.instantiationService.invokeFunction(async VV => {
            await VV.get(vJc).startBestOfNJudge(Jr.data.composerId, fM, xn)
        });
    } catch (fM) {
        console.error("[best-of-n judge] Failed to run UI judge", fM);
    }
}
```

### Judge Service Implementation

**Service**: `uiBestOfNJudgeService` (Line 716398)

**Location**: Lines 716400-716543

```javascript
class Sdo {
    constructor(aiService, gitContextService, composerDataService,
                composerViewsService, workspaceContextService, agentExecProvider) {
        // Dependencies injected
    }

    setStatusFor(composerIds, status) {
        for (const id of composerIds) {
            this.composerDataService.updateComposerDataSetStore(id, s => {
                s("bestOfNJudgeStatus", status);
                if (status === "judging") {
                    s("bestOfNJudgeWinner", !1);
                    s("bestOfNJudgeReasoning", void 0);
                }
            });
        }
    }

    setWinner(composerId, reasoning) {
        this.composerDataService.updateComposerDataSetStore(composerId, n => {
            n("bestOfNJudgeWinner", !0);
            n("bestOfNJudgeReasoning", reasoning);
        });
    }

    composerHasFileEdits(composerId) {
        const data = this.composerDataService.getComposerData(composerId);
        if (!data) return false;

        if (data.isNAL === true) {
            // NAL uses fileStatesV2
            const s = data.conversationState?.fileStatesV2;
            return !!(s && Object.keys(s).length > 0);
        }

        // Legacy uses codeBlockData
        const n = data.codeBlockData;
        if (!n) return false;
        for (const s of Object.keys(n)) {
            const r = n[s];
            if (r && Object.keys(r).length > 0) return true;
        }
        return false;
    }

    async waitForFileEdits(composerId, timeout = 5000) {
        const start = Date.now();
        const interval = 100;
        while (Date.now() - start < timeout) {
            if (this.composerHasFileEdits(composerId)) return true;
            await new Promise(r => setTimeout(r, interval));
        }
        return false;
    }

    async startBestOfNJudge(parentComposerId, composerIds, task) {
        const unique = Array.from(new Set(composerIds));
        if (unique.length < 2) return;  // Need at least 2 candidates

        this.setStatusFor(unique, "judging");
        const abortController = new AbortController();

        try {
            // Collect diffs from each worktree
            const diffPromises = unique.map(async composerId => {
                const worktreePath = this.composerDataService
                    .getComposerData(composerId)?.gitWorktree?.worktreePath;
                if (!worktreePath) return;

                const diffResult = await this.gitContextService.getDiff(new BMe({
                    cwd: worktreePath,
                    mergeBase: true,
                    maxUntrackedFiles: 200
                }));

                if (diffResult?.diff) {
                    return new HMr({
                        composerId: composerId,
                        diff: diffResult.diff
                    });
                }
            });

            const candidates = (await Promise.all(diffPromises))
                .filter(c => c !== undefined);

            if (candidates.length < 2) {
                this.setStatusFor(unique, "done");
                return;
            }

            // Wait for file edits (max 5 seconds per candidate)
            const hasEdits = await Promise.all(
                candidates.map(c => this.waitForFileEdits(c.composerId, 5000))
            );

            if (hasEdits.some(h => !h)) {
                console.info("[best-of-n judge] Skipping judge because at least one composer made zero file edits");
                this.setStatusFor(unique, "done");
                return;
            }

            // Start streaming judge request
            const client = await this.aiService.aiClient();
            const messageQueue = new l$(void 0);
            const startRequest = new $Mr({
                task: task,
                candidates: candidates
            });

            messageQueue.push(new y5t({
                message: {
                    case: "start",
                    value: startRequest
                }
            }));

            const stream = client.streamUiBestOfNJudge(messageQueue, {
                signal: abortController.signal
            });

            // Process server responses
            for await (const response of stream) {
                const msg = response.message;
                if (msg.case === "finalResult") {
                    const winnerId = msg.value.winnerComposerId;
                    const reasoning = msg.value.reasoning;

                    this.setStatusFor(unique, "done");
                    if (winnerId && unique.includes(winnerId)) {
                        this.setWinner(winnerId, reasoning);
                    }
                    this.markParentComposerUnread(parentComposerId);
                    break;
                }
            }
        } catch (error) {
            this.setStatusFor(unique, "done");
            console.error("[best-of-n judge] Service error", error);
        }
    }
}
```

### Protobuf Message Types

**Location**: Lines 158920-159099

```javascript
// Candidate representation
class UiBestOfNJudgeCandidate {
    typeName = "aiserver.v1.UiBestOfNJudgeCandidate"
    composerId = ""
    diff = DiffMessage
}

// Start request
class StreamUiBestOfNJudgeStartRequest {
    typeName = "aiserver.v1.StreamUiBestOfNJudgeStartRequest"
    task = ""           // User's original prompt
    candidates = []     // Array of UiBestOfNJudgeCandidate
}

// Final result from server
class UiBestOfNJudgeFinalResult {
    typeName = "aiserver.v1.UiBestOfNJudgeFinalResult"
    winnerComposerId = ""
    reasoning = ""
}

// Client-to-server message wrapper
class StreamUiBestOfNJudgeClientMessage {
    typeName = "aiserver.v1.StreamUiBestOfNJudgeClientMessage"
    message: {
        case: "start" | "execClientMessage" | "execClientControlMessage"
        value: StartRequest | ExecMessage | ControlMessage
    }
}

// Server-to-client message wrapper
class StreamUiBestOfNJudgeServerMessage {
    typeName = "aiserver.v1.StreamUiBestOfNJudgeServerMessage"
    message: {
        case: "finalResult" | "execServerMessage" | "execServerControlMessage"
        value: FinalResult | ExecMessage | ControlMessage
    }
}
```

## Applying the Winner

### Undo Non-Winner Worktrees

**Location**: Lines 945811-945821

When the user applies the winning result, other applied worktrees are automatically undone:

```javascript
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

### Get Other Applied Composers

**Location**: Lines 945788-945810

```javascript
_getOtherAppliedBestOfNComposerIds(composerData) {
    const groupId = this.composerUtilsService.getBestOfNGroupId(composerData.composerId);
    const allIds = new Set();

    const collectIds = (data) => {
        if (data.isBestOfNParent || data.subComposerIds?.length > 0) {
            allIds.add(data.composerId);
            for (const id of (data.subComposerIds || [])) {
                allIds.add(id);
            }
        }
        if (data.isBestOfNSubcomposer && data.subagentInfo?.parentComposerId) {
            const parent = this.composerDataService.getComposerData(data.subagentInfo.parentComposerId);
            if (parent) {
                allIds.add(parent.composerId);
                for (const id of (parent.subComposerIds || [])) {
                    allIds.add(id);
                }
            }
        }
    };

    // Collect from current and group members
    if (groupId === composerData.composerId) {
        collectIds(composerData);
    } else {
        const groupData = this.composerDataService.getComposerData(groupId);
        if (groupData) {
            collectIds(groupData);
        } else if (composerData.isBestOfNSubcomposer && composerData.subagentInfo?.parentComposerId) {
            const parent = this.composerDataService.getComposerData(composerData.subagentInfo.parentComposerId);
            collectIds(parent);
        }
    }

    // Remove current composer
    allIds.delete(composerData.composerId);

    // Return only those that are applied
    const applied = [];
    for (const id of allIds) {
        if (this.composerDataService.getComposerData(id)?.applied) {
            applied.push(id);
        }
    }
    return applied;
}
```

## Feature Flags and Configuration

### Feature Gate

**Location**: Line 293653-293656

```javascript
worktrees_bon_judge: {
    client: !0,    // Client-side flag
    default: !0    // Enabled by default
}
```

### Setting to Disable

**Location**: Line 450741

```javascript
{
    description: "Disable the Best-of-N recommender feature that judges and recommends the best result from multiple parallel agent runs."
}
```

## Analytics Events

### Submission Events

```javascript
// Line 766678-766680
"best_of_n.submit" {
    model: string,           // Model name
    bestOfNSubmitId: string  // Group ID for tracking
}

// Line 766697-766702
"best_of_n.agent_request" {
    model: string,
    bestOfNSubmitId: string,
    agentRequestId: string,
    composerId: string
}

// Line 766709-766711
"agent_layout.multi_model_submission" {
    numModels: number
}
```

### View Events

```javascript
// Line 762352-762354
"best_of_n.view_subcomposer" {
    modelName: string,
    bestOfNSubmitId: string,
    viewedComposerId: string
}
```

## Worktree Cleanup

### Cleanup Settings

**Location**: Lines 182685-182686

```javascript
worktreeCleanupIntervalHours: Sse(6, -1, 0),  // Default 6 hours
worktreeMaxCount: Sse(20, -1, 0),             // Max 20 worktrees
```

### Protection Logic

**Location**: Lines 960632-960637

Worktrees are protected from cleanup if:
1. Created less than `Bom` (minimum age) ago
2. Associated with a currently running composer

```javascript
shouldProtectWorktree(worktreeData) {
    // Protect young worktrees
    if (Date.now() - worktreeData.createdAt < Bom) return true;

    // Protect worktrees with running composers
    const composerId = worktreeData.composerId;
    const composerService = this.getComposerDataService();
    const handle = composerId && composerService
        ? composerService.getWeakHandleOptimistic(composerId)
        : undefined;
    return !!(handle && composerService?.isComposerRunning(handle));
}
```

## Summary

The Best-of-N system provides a sophisticated parallel execution framework:

1. **Serialized Worktree Creation**: The `WorktreeLockLease` system ensures worktrees are created one at a time, preventing git race conditions.

2. **Parent/Child Hierarchy**: A parent composer coordinates multiple subcomposers, each running a different model.

3. **Shared Context**: Subcomposers clone the parent's context and receive the same initial prompt.

4. **Server-Side Judging**: The `StreamUiBestOfNJudge` RPC collects git diffs from each worktree and determines the best result.

5. **Automatic Cleanup**: When applying a winner, other applied results are automatically undone.

6. **Configurable Limits**: Worktree count and cleanup intervals are user-configurable.

The judging criteria and prompts are entirely server-side, making the actual evaluation logic opaque to client-side analysis.
