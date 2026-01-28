# TASK-15: ParallelAgentWorkflow and Synthesis Strategies - Deep Analysis

## Executive Summary

This analysis provides a comprehensive examination of Cursor IDE 2.3.41's ParallelAgentWorkflow system, focusing on synthesis strategies, agent coordination, and result aggregation mechanisms. The system implements a sophisticated parallel agent architecture with three synthesis strategies for combining results from multiple concurrent AI agents.

## Source File

**Primary Source:** `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`

---

## 1. ParallelAgentWorkflow Implementation

### 1.1 Core Data Structures

#### ParallelAgentWorkflowSynthesisStrategy Enum

**Location:** Lines 335701-335712, 455147-455159

```javascript
// aiserver.v1.ParallelAgentWorkflowSynthesisStrategy
{
  UNSPECIFIED: 0,
  SINGLE_AGENT: 1,
  FANOUT_VOTING: 2,
  PAIRWISE_TOURNAMENT: 3
}
```

The enum is registered twice in the codebase - once in the primary protobuf section and again in what appears to be a secondary module definition.

#### EnsembleStatus Enum

**Location:** Lines 335692-335700

```javascript
// aiserver.v1.EnsembleStatus
{
  UNSPECIFIED: 0,    // No ensemble role
  PARENT: 1,         // Parent workflow coordinator
  CHILD: 2           // Child agent worker
}
```

This status is stored on background composer state to indicate whether a composer is coordinating a parallel workflow or executing as a child worker.

### 1.2 Workflow Phase State Machine

**Location:** Lines 338453-338474, 458030-458053

```javascript
// aiserver.v1.ParallelAgentWorkflowStatusUpdate.Phase
{
  PHASE_UNSPECIFIED: 0,
  PHASE_STARTING: 1,           // Workflow initialization
  PHASE_CHILDREN_RUNNING: 2,   // Parallel execution phase
  PHASE_GATHERING: 3,          // Collecting child results
  PHASE_SYNTHESIZING: 4,       // Merging/selecting best result
  PHASE_COMPLETED: 5,          // Successfully finished
  PHASE_ERROR: 6               // Error state
}
```

---

## 2. Synthesis Strategy Selection

### 2.1 Strategy Configuration Schema

**Location:** Lines 295172-295176

```javascript
parallel_agent_synthesis_config: ls.object({
  strategy: ls.enum(["single_agent", "fanout_voting", "pairwise_tournament"]),
  synthesisModel: ls.string(),
  fanoutSize: ls.number().nullable()
})
```

### 2.2 Default Configuration

**Location:** Lines 295570-295576

```javascript
parallel_agent_synthesis_config: {
  client: false,  // Server-controlled config
  fallbackValues: {
    strategy: "pairwise_tournament",   // DEFAULT: Tournament-style selection
    synthesisModel: "gpt-5.1-codex-high",
    fanoutSize: null
  }
}
```

**Key Finding:** The default synthesis strategy is `pairwise_tournament`, not simple voting or single-agent selection. This indicates Cursor defaults to the most rigorous comparison method.

---

## 3. FANOUT_VOTING vs PAIRWISE_TOURNAMENT

### 3.1 Strategy Differences

| Aspect | FANOUT_VOTING | PAIRWISE_TOURNAMENT |
|--------|--------------|---------------------|
| Approach | Multiple agents vote on best outcome | Bracket-style elimination rounds |
| Complexity | O(n) comparisons | O(n log n) comparisons |
| Progress Tracking | Not documented | SynthesisTournamentProgress messages |
| Default | No | Yes |

### 3.2 PAIRWISE_TOURNAMENT Progress Tracking

**Location:** Lines 338474-338515, 458053-458095

```javascript
// aiserver.v1.SynthesisTournamentProgress
{
  current_round: int32,          // Current tournament round (1-indexed)
  total_rounds: int32,           // Total rounds needed (log2 of candidates)
  candidates_remaining: int32,   // Candidates still in tournament
  initial_candidates: int32      // Starting number of candidates
}
```

The tournament progress is streamed via `ParallelAgentWorkflowStatusUpdate.tournament_progress` field, allowing the UI to display elimination round status.

### 3.3 Synthesis Model Configuration

The `synthesis_model` field in `ParallelAgentWorkflowSynthesisConfig` specifies which AI model performs the judge/arbitration role:

```javascript
// Default synthesis model
synthesisModel: "gpt-5.1-codex-high"
```

This suggests a high-capability model is used for the critical task of comparing and selecting between agent outputs.

---

## 4. Agent Coordination Logic

### 4.1 Ensemble Configuration

**Location:** Lines 295166-295171, 295561-295568

```javascript
parallel_agent_ensemble_config: {
  client: false,  // Server-controlled
  fallbackValues: {
    models: [
      "gpt-5.1-codex-high",
      "claude-4.5-sonnet-thinking",
      "gpt-5-codex-high",
      "claude-4.5-sonnet-thinking"
    ],
    gatherTimeoutMs: 300000,           // 5 minutes
    gatherMinSuccessPercentage: 0.5,   // 50% must succeed
    gatherMinSuccessCount: null
  }
}
```

**Key Findings:**
1. **Model Diversity:** Default uses alternating GPT and Claude models for diverse approaches
2. **Duplication:** Models are listed twice (4 total), likely for increased parallelism
3. **Fault Tolerance:** Only 50% of children need to succeed for synthesis to proceed
4. **Timeout:** 5-minute timeout for child execution gathering

### 4.2 Request/Response Structures

#### StartParallelAgentWorkflowRequest

**Location:** Lines 338299-338344, 457864-457910

```javascript
{
  base_request: ComposerRequest,              // The original composer request
  child_model_details: repeated ModelDetails,  // Models for child agents
  gather_config: ParallelAgentWorkflowGatherConfig,
  synthesis_config: ParallelAgentWorkflowSynthesisConfig
}
```

#### StartParallelAgentWorkflowResponse

**Location:** Lines 338345-338375

```javascript
{
  parent_bc_id: string,   // Parent background composer ID
  workflow_id: string     // Unique workflow identifier
}
```

The response provides IDs for tracking: the parent background composer that coordinates and a unique workflow ID for status streaming.

### 4.3 gRPC Service Methods

**Location:** Lines 815753-815763

Part of `aiserver.v1.BackgroundComposerService`:

```javascript
startParallelAgentWorkflow: {
  name: "StartParallelAgentWorkflow",
  I: HNc,  // StartParallelAgentWorkflowRequest
  O: $Nc,  // StartParallelAgentWorkflowResponse
  kind: Kt.Unary
},
streamParallelAgentWorkflowStatus: {
  name: "StreamParallelAgentWorkflowStatus",
  I: qNc,  // StreamParallelAgentWorkflowStatusRequest
  O: JNc,  // ParallelAgentWorkflowStatusUpdate
  kind: Kt.ServerStreaming
}
```

---

## 5. Result Aggregation

### 5.1 Gather Configuration

**Location:** Lines 338220-338258, 457776-457819

```javascript
// aiserver.v1.ParallelAgentWorkflowGatherConfig
{
  timeout_ms: optional int64,           // Max wait time for child completion
  min_success_count: optional int32,    // Absolute minimum successful children
  min_success_percentage: optional float // Percentage-based minimum
}
```

The gather phase collects results from child agents with configurable success thresholds. This allows the workflow to proceed even if some children fail.

### 5.2 Status Update Streaming

**Location:** Lines 338376-338452

```javascript
// StreamParallelAgentWorkflowStatusRequest
{
  workflow_id: string,  // From StartParallelAgentWorkflowResponse
  bc_id: string         // Background composer ID to monitor
}

// ParallelAgentWorkflowStatusUpdate
{
  phase: Phase,                              // Current workflow phase
  synthesis_bc_id: optional string,          // ID of synthesis composer (during SYNTHESIZING)
  error_message: optional string,            // Error details (during ERROR)
  tournament_progress: optional SynthesisTournamentProgress
}
```

---

## 6. UI Best-of-N Judge Integration

### 6.1 Judge Service

**Location:** Lines 716398-716541

```javascript
class UiBestOfNJudgeService {
  // Dependencies: aiService, gitContextService, composerDataService,
  //               composerViewsService, workspaceContextService, agentExecProvider

  setStatusFor(composerIds, status) {
    // Sets status to "judging" or "done"
    // Resets winner/reasoning when starting judging
  }

  setWinner(composerId, reasoning) {
    // Marks winning composer
    // Stores judge reasoning
  }

  async startBestOfNJudge(parentId, candidateIds, task) {
    // Main entry point for UI-side judge orchestration
  }
}
```

### 6.2 Judge Flow (Lines 716442-716541)

```javascript
async startBestOfNJudge(parentId, candidateIds, task) {
  // 1. Deduplicate candidate IDs
  const uniqueCandidates = Array.from(new Set(candidateIds));
  if (uniqueCandidates.length < 2) return;

  // 2. Set all candidates to "judging" status
  this.setStatusFor(uniqueCandidates, "judging");

  // 3. Collect diffs from each candidate's worktree
  const candidates = await Promise.all(
    uniqueCandidates.map(async id => {
      const worktreePath = composerData.gitWorktree?.worktreePath;
      const diff = await getDiff({ cwd: worktreePath, mergeBase: true });
      return { composerId: id, diff };
    })
  );

  // 4. Filter candidates with actual file edits
  if (candidates.filter(c => c.diff).length < 2) {
    this.setStatusFor(uniqueCandidates, "done");
    return;
  }

  // 5. Wait for all candidates to have file edits (5s timeout)
  const allHaveEdits = await Promise.all(
    candidates.map(c => this.waitForFileEdits(c.composerId, 5000))
  );

  // 6. Stream to server-side judge
  const stream = aiClient.streamUiBestOfNJudge(...);

  // 7. Process server messages for winner selection
  for await (const message of stream) {
    if (message.case === "finalResult") {
      const winnerId = message.winnerComposerId;
      const reasoning = message.reasoning;
      this.setStatusFor(uniqueCandidates, "done");
      this.setWinner(winnerId, reasoning);
      break;
    }
  }
}
```

### 6.3 Judge Protocol Messages

**Location:** Lines 158918-159091

```javascript
// UiBestOfNJudgeCandidate
{
  composer_id: string,
  diff: DiffMessage
}

// StreamUiBestOfNJudgeStartRequest
{
  task: string,
  candidates: repeated UiBestOfNJudgeCandidate
}

// UiBestOfNJudgeFinalResult
{
  winner_composer_id: string,
  reasoning: string
}

// StreamUiBestOfNJudgeClientMessage (oneof message)
{
  start: StreamUiBestOfNJudgeStartRequest,
  execClientMessage: ...,
  execClientControlMessage: ...
}

// StreamUiBestOfNJudgeServerMessage (oneof message)
{
  final_result: UiBestOfNJudgeFinalResult,
  execServerMessage: ...,
  execServerControlMessage: ...
}
```

The judge uses bidirectional streaming for interactive evaluation.

---

## 7. Background Agent Judge Configuration

**Location:** Lines 294988-294992, 295283-295290

```javascript
background_agent_judge_config: {
  client: false,  // Server-controlled
  fallbackValues: {
    judgeModel: "gpt-5-high",
    summarizerModel: "gpt-5-mini",
    bestOfNModels: ["gpt-5"],
    patchRejectorStatus: "off"
  }
}
```

**Configuration Options:**
- `judgeModel`: Model used for comparing/judging outputs (gpt-5-high)
- `summarizerModel`: Model for summarization tasks (gpt-5-mini)
- `bestOfNModels`: Models eligible for best-of-n selection
- `patchRejectorStatus`: Patch rejection feature ["off", "warn", "on"]

---

## 8. Composer Data Model Extensions

### 8.1 Best-of-N Related Fields

**Location:** Lines 215122-215134

```javascript
ComposerData {
  // ... other fields ...
  isBestOfNSubcomposer: boolean,       // Is this a child in best-of-n
  isBestOfNParent: boolean,            // Is this the parent coordinator
  bestOfNJudgeStatus: "judging" | "done" | undefined,
  bestOfNJudgeWinner: boolean,
  bestOfNJudgeReasoning: string | undefined,
  subComposerIds: string[],            // Child composer IDs
  selectedSubComposerId: string,       // Currently selected child
  initialBestOfNAgentRequestId: string // Original request ID
}
```

### 8.2 Resolution Logic

**Location:** Lines 297826-297835

```javascript
resolveComposerIdToSelected(composerId) {
  const data = this.getComposerData(composerId);
  if (!data) return composerId;

  // If this is a best-of-n parent with a selected child, return the child
  if (data.isBestOfNParent && data.selectedSubComposerId) {
    if (data.subComposerIds?.includes(data.selectedSubComposerId)) {
      return data.selectedSubComposerId;
    }
  }
  return composerId;
}
```

---

## 9. Analytics Events

Key events tracked for parallel workflows:

```javascript
// Model picker interaction
"composer.ensemble_model_picker.button_clicked" {
  modelCount: number,
  nextModelCount: number
}

// Multi-model submission
"agent_layout.multi_model_submission" {
  numModels: number
}

// Individual agent request tracking
"best_of_n.agent_request" {
  model: string,
  bestOfNSubmitId: string,
  agentRequestId: string,
  composerId: string
}

// Worktree application
"git_worktree.apply_to_main" {
  modelName: string,
  bestOfNJudgeCompleted: boolean,
  bestOfNJudgeWinner: boolean,
  bestOfNSubmitId: string,
  initialAgentRequestId: string
}
```

---

## 10. Key Findings

### 10.1 Architecture Insights

1. **Server-Side Orchestration:** The parallel workflow logic (gathering, synthesis) runs server-side. The client primarily handles UI state and displays results.

2. **Dual Judge Systems:** There are two judging mechanisms:
   - Server-side synthesis during `PHASE_SYNTHESIZING` (pairwise tournament)
   - Client-side `UiBestOfNJudgeService` for UI-initiated comparisons

3. **Git Worktree Isolation:** Each parallel agent operates in a separate git worktree, enabling true isolation without file conflicts.

4. **Fault-Tolerant Design:** The 50% minimum success threshold allows workflows to complete even with partial child failures.

### 10.2 Strategy Comparison

| Strategy | Use Case | Trade-offs |
|----------|----------|------------|
| SINGLE_AGENT | Fast, deterministic | No diversity benefits |
| FANOUT_VOTING | Consensus-based | Requires agreement |
| PAIRWISE_TOURNAMENT | Best quality selection | More expensive (multiple comparisons) |

### 10.3 Model Selection

Default ensemble uses model diversity:
- GPT models (gpt-5.1-codex-high, gpt-5-codex-high)
- Claude models (claude-4.5-sonnet-thinking)

This provides diverse problem-solving approaches that are then compared.

---

## 11. Gaps and Unknown Details

### 11.1 Not Visible in Client Code

1. **Tournament Bracket Logic:** The actual pairwise comparison algorithm is server-side
2. **Voting Aggregation:** FANOUT_VOTING consensus mechanism details not present
3. **Synthesis Prompts:** The prompts used by the synthesis model for comparisons
4. **Result Merging:** Whether/how non-conflicting changes from multiple agents are merged

### 11.2 Recommended Follow-up Investigations

1. **TASK: Investigate server-side synthesis prompts** - Capture network traffic during tournament to extract judge prompts
2. **TASK: Analyze worktree merge strategies** - How are winning agent changes applied to main branch
3. **TASK: Document FANOUT_VOTING implementation** - When is voting used vs tournament
4. **TASK: Investigate patch rejector feature** - What does patchRejectorStatus do when enabled

---

## 12. References

- Lines 295561-295576: Default ensemble and synthesis configurations
- Lines 335692-338520: Protobuf message definitions (first module)
- Lines 455135-458095: Protobuf message definitions (second module)
- Lines 716398-716541: UiBestOfNJudgeService implementation
- Lines 815697-815764: BackgroundComposerService gRPC definitions
- Lines 766689-766729: Multi-model submission flow

---

*Analysis completed: 2026-01-28*
*Cursor IDE Version: 2.3.41*
