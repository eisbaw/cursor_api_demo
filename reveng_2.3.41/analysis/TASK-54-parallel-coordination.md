# TASK-54: ParallelAgentWorkflow Coordination - Multi-Agent Orchestration Analysis

## Executive Summary

This analysis provides a detailed examination of Cursor IDE 2.3.41's multi-agent orchestration system, focusing on the coordination mechanisms for FANOUT_VOTING and PAIRWISE_TOURNAMENT synthesis strategies. The system orchestrates multiple AI agents working in parallel, each operating in isolated git worktrees, with sophisticated result aggregation and winner selection mechanisms.

## Source File

**Primary Source:** `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`

---

## 1. Multi-Agent Orchestration Architecture

### 1.1 High-Level Coordination Flow

```
User Request
     |
     v
+--------------------+
| Parent Composer    | <-- isBestOfNParent = true
+--------------------+
     |
     | Creates child composers (one per model)
     v
+----+----+----+----+
| C1 | C2 | C3 | C4 |  <-- isBestOfNSubcomposer = true
+----+----+----+----+
  |    |    |    |
  v    v    v    v
+----+----+----+----+
|W1  |W2  |W3  |W4  |  <-- Isolated git worktrees
+----+----+----+----+
     |
     | PHASE_GATHERING (collect results)
     v
+--------------------+
| Synthesis Phase    | <-- FANOUT_VOTING or PAIRWISE_TOURNAMENT
+--------------------+
     |
     | PHASE_COMPLETED
     v
Winner Selected
```

### 1.2 Parent-Child Relationship Tracking

**Data Structure Fields (Location: Lines 215122-215134, 266922-266939)**

```javascript
// Parent Composer Data
{
  isBestOfNParent: true,              // Identifies as coordinator
  subComposerIds: ["cid1", "cid2"],   // Array of child composer IDs
  selectedSubComposerId: "cid1",       // Currently selected/winning child
  bestOfNJudgeStatus: "done" | "judging" | undefined,
  initialBestOfNAgentRequestId: string // Original request UUID
}

// Child Composer Data
{
  isBestOfNSubcomposer: true,         // Identifies as child agent
  bestOfNJudgeWinner: boolean,         // True if this is the winning candidate
  bestOfNJudgeReasoning: string        // Judge's reasoning for selection
}
```

---

## 2. Synthesis Strategy Implementations

### 2.1 Strategy Enum Definition

**Location:** Lines 335701-335712, 455147-455159

```javascript
// aiserver.v1.ParallelAgentWorkflowSynthesisStrategy
{
  UNSPECIFIED: 0,
  SINGLE_AGENT: 1,
  FANOUT_VOTING: 2,
  PAIRWISE_TOURNAMENT: 3
}

// Protobuf name mapping
{
  0: "PARALLEL_AGENT_WORKFLOW_SYNTHESIS_STRATEGY_UNSPECIFIED",
  1: "PARALLEL_AGENT_WORKFLOW_SYNTHESIS_STRATEGY_SINGLE_AGENT",
  2: "PARALLEL_AGENT_WORKFLOW_SYNTHESIS_STRATEGY_FANOUT_VOTING",
  3: "PARALLEL_AGENT_WORKFLOW_SYNTHESIS_STRATEGY_PAIRWISE_TOURNAMENT"
}
```

### 2.2 FANOUT_VOTING Strategy

**Conceptual Model:**
- All N agents execute the same task in parallel
- Each produces an independent solution
- A voting/consensus mechanism determines the best result
- Requires majority or plurality agreement

**Limitations in Client Code:**
- The actual voting logic is server-side
- No explicit fanout-specific progress tracking (unlike tournament)
- `fanoutSize` configuration parameter available but details not visible

**Configuration (Lines 338262-338285):**
```javascript
ParallelAgentWorkflowSynthesisConfig {
  strategy: FANOUT_VOTING,
  synthesis_model: ModelDetails,     // Model performing vote aggregation
  fanout_size: optional int32        // Number of voters/candidates
}
```

### 2.3 PAIRWISE_TOURNAMENT Strategy

**Conceptual Model:**
- Bracket-style elimination tournament
- Pairs of candidates compared head-to-head
- Winners advance to next round
- Final round produces single winner

**Progress Tracking (Lines 338474-338515):**

```javascript
// aiserver.v1.SynthesisTournamentProgress
{
  current_round: int32,           // 1-indexed current round
  total_rounds: int32,            // ceil(log2(initial_candidates))
  candidates_remaining: int32,    // Candidates still in tournament
  initial_candidates: int32       // Starting number of candidates
}
```

**Example Tournament Progression:**
```
Initial: 4 candidates
Round 1: [A vs B] -> B, [C vs D] -> C
         candidates_remaining: 2
Round 2: [B vs C] -> C (winner)
         candidates_remaining: 1
```

**Status Update Stream (Lines 338407-338438):**
```javascript
ParallelAgentWorkflowStatusUpdate {
  phase: Phase,                              // PHASE_SYNTHESIZING during tournament
  synthesis_bc_id: optional string,          // Background composer doing synthesis
  error_message: optional string,
  tournament_progress: SynthesisTournamentProgress  // Only for PAIRWISE_TOURNAMENT
}
```

---

## 3. Agent Coordination Lifecycle

### 3.1 Workflow Phases

**Location:** Lines 338453-338474

```javascript
// aiserver.v1.ParallelAgentWorkflowStatusUpdate.Phase
{
  PHASE_UNSPECIFIED: 0,
  PHASE_STARTING: 1,           // Initializing workflow
  PHASE_CHILDREN_RUNNING: 2,   // Parallel execution in progress
  PHASE_GATHERING: 3,          // Collecting child results
  PHASE_SYNTHESIZING: 4,       // Running synthesis strategy
  PHASE_COMPLETED: 5,          // Successfully finished
  PHASE_ERROR: 6               // Error state
}
```

### 3.2 Child Agent Spawning

**Location:** Lines 766655-766728

The multi-model submission flow creates child composers:

```javascript
// Simplified flow from actual code
for (const [index, modelSlug] of modelsToUse.entries()) {
  // 1. Create child composer with unique worktree
  const childComposerId = await createComposer({
    isBestOfNSubcomposer: true,
    modelConfig: { modelName: modelSlug },
    worktreeLockLease: index === 0 ? lease : undefined,
    tryUseBestOfNPromotion: isPromotion
  });

  // 2. Track request ID for analytics
  composerDataService.updateComposerData(childComposerId, {
    initialBestOfNAgentRequestId: generationUUID
  });

  // 3. Fire analytics event
  analyticsService.trackEvent("best_of_n.agent_request", {
    model: modelSlug,
    bestOfNSubmitId: groupId,
    agentRequestId: generationUUID,
    composerId: childComposerId
  });

  promises.push(agentSubmissionPromise);
}

// Track multi-model submission
analyticsService.trackEvent("agent_layout.multi_model_submission", {
  numModels: modelsToUse.length
});
```

### 3.3 Result Gathering Configuration

**Location:** Lines 338220-338258

```javascript
// aiserver.v1.ParallelAgentWorkflowGatherConfig
{
  timeout_ms: int64,              // Max wait for children (default: 300000ms = 5min)
  min_success_count: int32,       // Absolute minimum successes required
  min_success_percentage: float   // Percentage minimum (default: 0.5 = 50%)
}
```

**Default Configuration (Lines 295561-295568):**
```javascript
parallel_agent_ensemble_config: {
  models: [
    "gpt-5.1-codex-high",
    "claude-4.5-sonnet-thinking",
    "gpt-5-codex-high",
    "claude-4.5-sonnet-thinking"
  ],
  gatherTimeoutMs: 300000,           // 5 minutes
  gatherMinSuccessPercentage: 0.5,   // 50% must succeed
  gatherMinSuccessCount: null        // No absolute minimum
}
```

**Key Design Decisions:**
1. **Model Diversity:** Mix of GPT and Claude models for varied approaches
2. **Redundancy:** Models listed twice (4 total) for increased parallelism
3. **Fault Tolerance:** Only 50% need to succeed for synthesis to proceed
4. **Conservative Timeout:** 5 minutes accommodates complex tasks

---

## 4. EnsembleStatus Tracking

### 4.1 Status Enum

**Location:** Lines 335692-335700

```javascript
// aiserver.v1.EnsembleStatus
{
  UNSPECIFIED: 0,    // Not part of ensemble
  PARENT: 1,         // Workflow coordinator
  CHILD: 2           // Worker agent
}

// Protobuf names
{
  0: "ENSEMBLE_STATUS_UNSPECIFIED",
  1: "ENSEMBLE_STATUS_PARENT",
  2: "ENSEMBLE_STATUS_CHILD"
}
```

### 4.2 Background Composer Integration

**Location:** Lines 337368-337378

```javascript
// BackgroundComposer message includes ensemble tracking
BackgroundComposer {
  // ... other fields ...
  ensemble_status: EnsembleStatus,  // PARENT, CHILD, or UNSPECIFIED
  workflow_id: optional string,     // Links to parallel workflow
  model_details: ModelDetails       // Model used by this composer
}
```

---

## 5. UI Best-of-N Judge Service

### 5.1 Service Architecture

**Location:** Lines 716398-716541

```javascript
class UiBestOfNJudgeService {
  // Dependencies injected via DI
  constructor(
    aiService,
    gitContextService,
    composerDataService,
    composerViewsService,
    workspaceContextService,
    agentExecProvider
  )

  // Status management
  setStatusFor(composerIds: string[], status: "judging" | "done")
  setWinner(composerId: string, reasoning: string)

  // Judge orchestration
  async startBestOfNJudge(parentId, candidateIds, task)
}
```

### 5.2 Judge Execution Flow

**Location:** Lines 716442-716541

```javascript
async startBestOfNJudge(parentId, candidateIds, task) {
  // 1. Deduplicate and validate candidates
  const uniqueCandidates = Array.from(new Set(candidateIds));
  if (uniqueCandidates.length < 2) return;

  // 2. Mark all candidates as "judging"
  this.setStatusFor(uniqueCandidates, "judging");

  // 3. Collect diffs from each candidate's worktree
  const candidates = await Promise.all(
    uniqueCandidates.map(async (composerId) => {
      const worktreePath = getComposerData(composerId)?.gitWorktree?.worktreePath;
      if (!worktreePath) return undefined;

      const diff = await gitContextService.getDiff({
        cwd: worktreePath,
        mergeBase: true,
        maxUntrackedFiles: 200
      });

      return { composerId, diff: diff?.diff };
    })
  );

  // 4. Filter candidates with actual changes
  const validCandidates = candidates.filter(c => c?.diff);
  if (validCandidates.length < 2) {
    this.setStatusFor(uniqueCandidates, "done");
    return;
  }

  // 5. Wait for all to have file edits (5s timeout)
  const allHaveEdits = await Promise.all(
    validCandidates.map(c => this.waitForFileEdits(c.composerId, 5000))
  );

  if (allHaveEdits.some(hasEdits => !hasEdits)) {
    console.info("[best-of-n judge] Skipping - at least one made zero edits");
    this.setStatusFor(uniqueCandidates, "done");
    return;
  }

  // 6. Stream to server-side judge
  const aiClient = await this.aiService.aiClient();
  const stream = aiClient.streamUiBestOfNJudge(...);

  // 7. Process server responses
  for await (const message of stream) {
    if (message.case === "finalResult") {
      const winnerId = message.winnerComposerId;
      const reasoning = message.reasoning;

      this.setStatusFor(uniqueCandidates, "done");
      if (winnerId && uniqueCandidates.includes(winnerId)) {
        this.setWinner(winnerId, reasoning);
      }
      this.markParentComposerUnread(parentId);
      break;
    }
  }
}
```

### 5.3 Judge Protocol Messages

**Location:** Lines 158918-159091

```javascript
// Request: Candidate information
UiBestOfNJudgeCandidate {
  composer_id: string,
  diff: DiffMessage        // Git diff of changes
}

// Request: Start judge
StreamUiBestOfNJudgeStartRequest {
  task: string,            // Original user task/prompt
  candidates: repeated UiBestOfNJudgeCandidate
}

// Response: Final result
UiBestOfNJudgeFinalResult {
  winner_composer_id: string,
  reasoning: string        // Explanation of why this candidate won
}

// Bidirectional message wrappers
StreamUiBestOfNJudgeClientMessage {
  oneof message {
    start: StreamUiBestOfNJudgeStartRequest,
    execClientMessage: ...,
    execClientControlMessage: ...
  }
}

StreamUiBestOfNJudgeServerMessage {
  oneof message {
    final_result: UiBestOfNJudgeFinalResult,
    execServerMessage: ...,
    execServerControlMessage: ...
  }
}
```

---

## 6. gRPC Service Methods

### 6.1 BackgroundComposerService Methods

**Location:** Lines 815753-815763

```javascript
// Part of aiserver.v1.BackgroundComposerService
{
  // Start parallel workflow
  startParallelAgentWorkflow: {
    name: "StartParallelAgentWorkflow",
    I: StartParallelAgentWorkflowRequest,
    O: StartParallelAgentWorkflowResponse,
    kind: Unary
  },

  // Stream workflow status updates
  streamParallelAgentWorkflowStatus: {
    name: "StreamParallelAgentWorkflowStatus",
    I: StreamParallelAgentWorkflowStatusRequest,
    O: ParallelAgentWorkflowStatusUpdate,
    kind: ServerStreaming
  }
}
```

### 6.2 Composer Service Methods

**Location:** Lines 440152-440168

```javascript
// Part of aiserver.v1.ComposerService
{
  // UI-initiated judging
  streamUiBestOfNJudge: {
    name: "StreamUiBestOfNJudge",
    I: StreamUiBestOfNJudgeClientMessage,
    O: StreamUiBestOfNJudgeServerMessage,
    kind: BiDiStreaming
  },

  // SSE fallback
  streamUiBestOfNJudgeSSE: {
    name: "StreamUiBestOfNJudgeSSE",
    kind: ServerStreaming
  },

  // Polling fallback
  streamUiBestOfNJudgePoll: {
    name: "StreamUiBestOfNJudgePoll",
    kind: ServerStreaming
  }
}
```

---

## 7. Synthesis Model Configuration

### 7.1 Default Synthesis Model

**Location:** Lines 295570-295576

```javascript
parallel_agent_synthesis_config: {
  client: false,  // Server-controlled
  fallbackValues: {
    strategy: "pairwise_tournament",    // DEFAULT strategy
    synthesisModel: "gpt-5.1-codex-high", // Judge model
    fanoutSize: null                     // Auto-determined
  }
}
```

### 7.2 Background Agent Judge Configuration

**Location:** Lines 294988-294992, 295283-295290

```javascript
background_agent_judge_config: {
  client: false,
  fallbackValues: {
    judgeModel: "gpt-5-high",       // Main comparison model
    summarizerModel: "gpt-5-mini",  // For generating summaries
    bestOfNModels: ["gpt-5"],       // Eligible models for selection
    patchRejectorStatus: "off"      // ["off", "warn", "on"]
  }
}
```

---

## 8. Analytics and Telemetry

### 8.1 Tracked Events

```javascript
// Multi-model submission triggered
"agent_layout.multi_model_submission" {
  numModels: number  // Count of parallel agents
}

// Individual agent request
"best_of_n.agent_request" {
  model: string,             // Model slug
  bestOfNSubmitId: string,   // Group identifier
  agentRequestId: string,    // Request UUID
  composerId: string         // Composer ID
}

// Worktree applied to main
"git_worktree.apply_to_main" {
  modelName: string,
  bestOfNJudgeCompleted: boolean,  // Was judging finished
  bestOfNJudgeWinner: boolean,     // Was this the winner
  bestOfNSubmitId: string,
  initialAgentRequestId: string
}

// Model picker interaction
"composer.ensemble_model_picker.button_clicked" {
  modelCount: number,
  nextModelCount: number
}
```

---

## 9. Key Findings

### 9.1 Dual Judging Systems

The system has **two distinct judging mechanisms**:

1. **Server-Side Workflow Synthesis (ParallelAgentWorkflow)**
   - Triggered via `startParallelAgentWorkflow` RPC
   - Uses FANOUT_VOTING or PAIRWISE_TOURNAMENT strategies
   - Progress tracked via `streamParallelAgentWorkflowStatus`
   - Part of background composer infrastructure

2. **Client-Side UI Judge (UiBestOfNJudgeService)**
   - Triggered after multi-model submission (Lines 766722-766728)
   - Uses `streamUiBestOfNJudge` bidirectional RPC
   - Compares git diffs from each candidate's worktree
   - Updates composer data with winner/reasoning

### 9.2 Coordination Mechanisms

| Mechanism | Description | Location |
|-----------|-------------|----------|
| Parent/Child Tracking | `isBestOfNParent`/`isBestOfNSubcomposer` flags | ComposerData |
| Subcomposer Registry | `subComposerIds` array on parent | ComposerData |
| Winner Selection | `selectedSubComposerId` on parent | ComposerData |
| Group ID | `best_of_n_group_id` in requests | Protocol messages |
| Workflow ID | Links background composers to workflow | BackgroundComposer |

### 9.3 Fault Tolerance Design

- 50% minimum success threshold (configurable)
- 5-minute timeout for child completion
- Graceful degradation if candidates < 2
- Skip judging if no file edits detected

### 9.4 Strategy Comparison

| Aspect | FANOUT_VOTING | PAIRWISE_TOURNAMENT |
|--------|--------------|---------------------|
| Complexity | O(n) comparisons | O(n log n) comparisons |
| Progress UI | No specific progress | Round-by-round updates |
| Default | No | Yes |
| Best For | Quick consensus | Quality-focused selection |

---

## 10. Gaps and Unknowns

### 10.1 Server-Side Logic Not Visible

1. **Voting Algorithm:** How FANOUT_VOTING aggregates votes
2. **Tournament Brackets:** How pairs are matched in PAIRWISE_TOURNAMENT
3. **Comparison Prompts:** What prompts are used for head-to-head comparisons
4. **Tie-Breaking:** How ties are resolved in voting or tournament

### 10.2 Configuration Details

1. **fanoutSize Impact:** How it affects FANOUT_VOTING behavior
2. **patchRejectorStatus:** Full behavior when set to "warn" or "on"
3. **Dynamic Model Selection:** How model list is customized per-user

---

## 11. Related Tasks

This analysis complements:
- **TASK-15:** Overall ParallelAgentWorkflow structure
- **TASK-55:** Tournament algorithm details
- **TASK-57:** Best-of-N judge protocol
- **TASK-101:** Best-of-N worktree management
- **TASK-102:** Judge prompts analysis
- **TASK-105:** Best-of-N execution flow

---

## 12. References

| Topic | Lines |
|-------|-------|
| Synthesis Strategy Enum | 335701-335712, 455147-455159 |
| EnsembleStatus Enum | 335692-335700 |
| Phase State Machine | 338453-338474 |
| Tournament Progress | 338474-338515 |
| Gather Config | 338220-338258 |
| Default Ensemble Config | 295561-295576 |
| Multi-Model Submission | 766655-766728 |
| UiBestOfNJudgeService | 716398-716541 |
| gRPC Service Methods | 815753-815763, 440152-440168 |
| ComposerData Fields | 215122-215134, 266922-266939 |

---

*Analysis completed: 2026-01-28*
*Cursor IDE Version: 2.3.41*
*Task: TASK-54 - Document ParallelAgentWorkflow coordination*
