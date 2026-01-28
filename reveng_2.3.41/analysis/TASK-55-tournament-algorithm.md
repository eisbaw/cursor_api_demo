# TASK-55: Tournament Algorithm Analysis

## Overview

This document details how Cursor's pairwise agent comparison tournament system works, including bracket structure, comparison logic, and winner selection mechanisms.

## Tournament Architecture

### Synthesis Strategies Enum

**Source Location:** Lines 335701-335712

```javascript
// aiserver.v1.ParallelAgentWorkflowSynthesisStrategy
{
  UNSPECIFIED: 0,
  SINGLE_AGENT: 1,           // Use single agent result
  FANOUT_VOTING: 2,          // Multiple agents vote on best
  PAIRWISE_TOURNAMENT: 3     // Tournament-style elimination (DEFAULT)
}
```

The **PAIRWISE_TOURNAMENT** strategy is the default configuration.

### Default Configuration

**Source Location:** Lines 295570-295576

```javascript
parallel_agent_synthesis_config: {
  strategy: "pairwise_tournament",
  synthesisModel: "gpt-5.1-codex-high",  // Judge model
  fanoutSize: null
}
```

## Tournament Progress Tracking

### SynthesisTournamentProgress Protobuf

**Source Location:** Lines 338474-338515, Type: `aiserver.v1.SynthesisTournamentProgress`

```javascript
{
  current_round: int32,        // Which elimination round (1, 2, 3...)
  total_rounds: int32,         // Total rounds needed (log2(candidates))
  candidates_remaining: int32, // Candidates still in tournament
  initial_candidates: int32    // Starting number of candidates
}
```

**Example for 4 candidates:**
- Round 1: 4 candidates -> 2 winners
- Round 2: 2 candidates -> 1 winner (final)
- Total rounds: 2

### Workflow Status Update

**Source Location:** Lines 338407-338452, Type: `aiserver.v1.ParallelAgentWorkflowStatusUpdate`

```javascript
{
  phase: enum,                 // STARTING, CHILDREN_RUNNING, GATHERING, SYNTHESIZING, COMPLETED, ERROR
  synthesis_bc_id: string,     // Background composer ID for synthesis
  error_message: string,       // Error details if any
  tournament_progress: SynthesisTournamentProgress  // Current bracket state
}
```

## Judge Service Implementation

### Best-of-N Judge Service

**Source Location:** Lines 716398-716543

The `UiBestOfNJudgeService` class manages the pairwise comparison flow:

```javascript
class UiBestOfNJudgeService {
  constructor(aiService, gitContextService, composerDataService,
              composerViewsService, workspaceContextService, agentExecProvider) {}

  // Set judge status for all candidate composers
  setStatusFor(composerIds, status) {
    // status: "judging" | "done"
    // Resets winner/reasoning when status === "judging"
  }

  // Mark the winning composer with reasoning
  setWinner(composerId, reasoning) {
    // Sets bestOfNJudgeWinner = true
    // Sets bestOfNJudgeReasoning = reasoning string
  }

  // Start the judging process
  async startBestOfNJudge(parentComposerId, candidateComposerIds, task) {
    // 1. Require at least 2 candidates
    // 2. Collect git diffs from each candidate's worktree
    // 3. Filter out candidates with zero file edits
    // 4. Stream to StreamUiBestOfNJudge gRPC service
    // 5. Process final_result message with winner
  }
}
```

### Candidate Preparation Flow

**Source Location:** Lines 716442-716469

```javascript
async startBestOfNJudge(e, t, n) {
  const s = Array.from(new Set(t));
  if (s.length < 2) return;  // Minimum 2 candidates

  this.setStatusFor(s, "judging");

  // Collect diffs from each candidate's worktree
  const a = s.map(async composerId => {
    const worktreePath = this.composerDataService
      .getComposerData(composerId)?.gitWorktree?.worktreePath;

    if (!worktreePath) return;

    const diff = (await this.gitContextService.getDiff({
      cwd: worktreePath,
      mergeBase: true,
      maxUntrackedFiles: 200
    }))?.diff;

    if (diff) return new UiBestOfNJudgeCandidate({
      composerId: composerId,
      diff: diff
    });
  });

  const candidates = (await Promise.all(a)).filter(c => c !== undefined);

  // Skip if less than 2 valid candidates
  if (candidates.length < 2) {
    this.setStatusFor(s, "done");
    return;
  }

  // Wait for file edits (5s timeout per candidate)
  const editsCheck = await Promise.all(
    candidates.map(c => this.waitForFileEdits(c.composerId, 5000))
  );

  if (editsCheck.some(hasEdits => !hasEdits)) {
    console.info("[best-of-n judge] Skipping judge because at least one composer made zero file edits");
    this.setStatusFor(s, "done");
    return;
  }

  // ... proceed to streaming judge
}
```

## Protobuf Message Definitions

### UiBestOfNJudgeCandidate

**Source Location:** Lines 158920-158954, Type: `aiserver.v1.UiBestOfNJudgeCandidate`

```javascript
{
  composer_id: string,   // Unique composer/agent identifier
  diff: DiffMessage      // Git diff of agent's changes
}
```

### StreamUiBestOfNJudgeStartRequest

**Source Location:** Lines 158955-158990, Type: `aiserver.v1.StreamUiBestOfNJudgeStartRequest`

```javascript
{
  task: string,                             // Original task description
  candidates: repeated UiBestOfNJudgeCandidate  // All candidates to compare
}
```

### UiBestOfNJudgeFinalResult

**Source Location:** Lines 158991-159025, Type: `aiserver.v1.UiBestOfNJudgeFinalResult`

```javascript
{
  winner_composer_id: string,  // ID of winning agent
  reasoning: string            // Explanation for selection
}
```

### StreamUiBestOfNJudgeClientMessage

**Source Location:** Lines 159026-159070, Type: `aiserver.v1.StreamUiBestOfNJudgeClientMessage`

```javascript
// One-of message types sent to server:
{
  start: StreamUiBestOfNJudgeStartRequest,        // Initial request
  exec_client_message: ExecClientMessage,         // Tool execution response
  exec_client_control_message: ExecClientControlMessage  // Control signals
}
```

### StreamUiBestOfNJudgeServerMessage

**Source Location:** Lines 159071-159115, Type: `aiserver.v1.StreamUiBestOfNJudgeServerMessage`

```javascript
// One-of message types received from server:
{
  final_result: UiBestOfNJudgeFinalResult,        // Winner announcement
  exec_server_message: ExecServerMessage,         // Tool execution request
  exec_server_control_message: ExecServerControlMessage  // Control signals
}
```

## gRPC Service Methods

**Source Location:** Lines 440152-440167

```javascript
AiServer {
  streamUiBestOfNJudge: {
    name: "StreamUiBestOfNJudge",
    I: StreamUiBestOfNJudgeClientMessage,
    O: StreamUiBestOfNJudgeServerMessage,
    kind: BiDiStreaming  // Bidirectional streaming
  },

  streamUiBestOfNJudgeSSE: {
    name: "StreamUiBestOfNJudgeSSE",
    kind: ServerStreaming
  },

  streamUiBestOfNJudgePoll: {
    name: "StreamUiBestOfNJudgePoll",
    kind: ServerStreaming
  }
}
```

## Winner Selection Logic

### Final Result Processing

**Source Location:** Lines 716519-716527

```javascript
for await (const message of serverStream) {
  const msgCase = message.message;

  if (msgCase.case === "execServerMessage") {
    // Forward tool execution request
  } else if (msgCase.case === "execServerControlMessage") {
    // Handle control messages
  } else if (msgCase.case === "finalResult") {
    const winnerComposerId = msgCase.value.winnerComposerId;
    const reasoning = msgCase.value.reasoning;

    this.setStatusFor(s, "done");

    if (winnerComposerId && s.includes(winnerComposerId)) {
      this.setWinner(winnerComposerId, reasoning);
    }

    this.markParentComposerUnread(parentComposerId);
    break;
  }
}
```

### Reasoning Format

**Source Location:** Lines 762277-762292

The judge's reasoning is parsed with a summary/justification separator:

```javascript
const parseReasoning = (reasoning) => {
  const separator = reasoning.indexOf("\n---\n");

  if (separator !== -1) {
    const summary = reasoning.slice(0, separator).trim();
    const justification = reasoning.slice(separator + 5).trim();

    return {
      summary: summary,
      justification: justification.length > 0 ? justification : null
    };
  }

  return {
    summary: reasoning,
    justification: null
  };
};
```

**Expected Reasoning Format:**
```
Brief summary of why this solution was selected.
---
Detailed justification with specific comparisons between candidates,
analysis of code quality, completeness, and adherence to requirements.
```

## Data Flow Diagram

```
1. User initiates parallel agent workflow
   |
   v
2. Multiple agents run in isolated git worktrees
   |
   v
3. GATHERING phase: Collect results from agents
   |
   v
4. SYNTHESIZING phase: Tournament begins
   |
   +---> Collect git diffs from each worktree
   |     (getDiff with mergeBase: true)
   |
   +---> Build UiBestOfNJudgeCandidate for each agent
   |     (composerId + diff)
   |
   +---> Filter candidates with zero file edits
   |
   v
5. StreamUiBestOfNJudge bidirectional stream
   |
   +---> Client sends: start request with task + candidates
   |
   +---> Server processes pairwise comparisons
   |     (actual tournament logic is server-side)
   |
   +---> Client handles: exec_server_message for tool calls
   |
   v
6. Server sends: final_result
   |
   +---> winner_composer_id: string
   +---> reasoning: string (summary\n---\njustification)
   |
   v
7. UI updates
   |
   +---> Mark winner: bestOfNJudgeWinner = true
   +---> Store reasoning: bestOfNJudgeReasoning
   +---> Status update: bestOfNJudgeStatus = "done"
   |
   v
8. User can apply winning worktree to main branch
```

## Judge Configuration

**Source Location:** Lines 294988-295289

```javascript
background_agent_judge_config: {
  judgeModel: "gpt-5-high",           // Model used for judging
  summarizerModel: "gpt-5-mini",      // Model for summarization
  bestOfNModels: ["gpt-5"],           // Models eligible for best-of-n
  patchRejectorStatus: "off"          // Patch rejection setting
}
```

## Feature Flags

### worktrees_bon_judge

**Source Location:** Lines 293653-293656

```javascript
worktrees_bon_judge: {
  client: true,
  default: true   // Enabled by default
}
```

## UI Components

### Judge Status Display

**Source Location:** Lines 762537-762546

The UI displays the winner with visual indicators:
- Trophy/crown icon for winner tab
- "Suggested Response" aria-label
- Reasoning tooltip/expandable section

### Composer Data Fields

**Source Location:** Lines 215125-215131

```javascript
ComposerData {
  isBestOfNSubcomposer: false,
  isBestOfNParent: false,
  bestOfNJudgeStatus: undefined,     // "judging" | "done" | undefined
  bestOfNJudgeWinner: false,         // true if this is the winner
  bestOfNJudgeReasoning: undefined   // Reasoning string from judge
}
```

## Analytics Events

Key events tracked:
- `best_of_n.view_subcomposer` - User views a subcomposer tab
- `git_worktree.apply_to_main` - User applies winning worktree
  - Includes: `bestOfNJudgeCompleted`, `bestOfNJudgeWinner`

## Key Insights

1. **Server-Side Tournament Logic:** The actual pairwise comparison algorithm runs on Cursor's servers via `StreamUiBestOfNJudge`. The client only provides candidates and receives the final result.

2. **Diff-Based Comparison:** Candidates are compared based on their git diffs, not the final state. This means the judge evaluates the changes made, not just what code exists.

3. **Bidirectional Streaming:** The judge can request tool execution during evaluation via `exec_server_message`, allowing it to analyze code, run tests, etc.

4. **Reasoning Structure:** Responses follow a `summary\n---\njustification` format, allowing the UI to show a brief summary with expandable details.

5. **Minimum Candidates:** At least 2 candidates with file edits are required for judging to proceed.

6. **5-Second Edit Timeout:** The system waits up to 5 seconds for each candidate to have file edits before proceeding.

7. **Worktree Isolation:** Each candidate runs in a completely isolated git worktree, preventing interference.

## Open Questions

1. **Bracket Structure:** How are pairwise matchups organized when there are more than 2 candidates? Is it random or seeded?

2. **Tiebreakers:** How are ties handled in the tournament?

3. **Judge Prompts:** What specific prompts are used for pairwise comparison on the server side?

4. **Tournament Rounds:** How does the server implement multiple elimination rounds?

5. **Fanout Voting Details:** How does the alternative `FANOUT_VOTING` strategy work?

## Parallel Agent Ensemble Configuration

### Ensemble Model Configuration

**Source Location:** Lines 295561-295577

The parallel agent ensemble configures which models run in competition:

```javascript
parallel_agent_ensemble_config: {
  models: [
    "gpt-5.1-codex-high",
    "claude-4.5-sonnet-thinking",
    "gpt-5-codex-high",
    "claude-4.5-sonnet-thinking"
  ],
  gatherTimeoutMs: 300000,         // 5 minutes (300 * 1000ms)
  gatherMinSuccessPercentage: 0.5, // Need 50% of agents to succeed
  gatherMinSuccessCount: null      // No minimum count requirement
}
```

### User Preferences

**Source Location:** Lines 182638-182639

Users can configure their best-of-N preferences:

```javascript
{
  bestOfNCountPreference: 1,           // Default: 1 agent (no tournament)
  bestOfNEnsemblePreferences: "{}"     // JSON map of count -> model array
}
```

When a user selects multiple models for comparison, the system stores their preference keyed by the count. For example, with 2 models selected:
```json
{
  "2": ["gpt-5.1-codex-high", "claude-4.5-sonnet-thinking"]
}
```

### Best-of-N Group ID Tracking

**Source Location:** Lines 123538-123553, 140261-140276

Requests include group tracking fields:

```javascript
{
  best_of_n_group_id: string,        // Links related agent runs together
  try_use_best_of_n_promotion: bool  // Request promoted resource allocation
}
```

The `best_of_n_group_id` allows the server to correlate all agents in a single tournament, while `try_use_best_of_n_promotion` requests priority resource allocation for parallel runs.

### Selected Sub-Composer Tracking

**Source Location:** Lines 297826-297836

The parent composer tracks which sub-composer (agent) is currently selected:

```javascript
resolveComposerIdToSelected(composerId) {
  const data = this.getComposerData(composerId);
  if (!data) return composerId;

  if (data.isBestOfNParent && data.selectedSubComposerId) {
    const selected = data.selectedSubComposerId;
    if (data.subComposerIds?.includes(selected)) {
      return selected;
    }
  }
  return composerId;
}
```

## Tournament Round Calculation

The total number of rounds is calculated based on initial candidates:
- **2 candidates:** 1 round (final)
- **3-4 candidates:** 2 rounds (semifinals + final)
- **5-8 candidates:** 3 rounds (quarterfinals + semifinals + final)

Formula: `total_rounds = ceil(log2(initial_candidates))`

Progress is tracked per round:
```
Round 1: candidates_remaining = initial_candidates
Round N: candidates_remaining = initial_candidates / 2^(N-1)
Final:   candidates_remaining = 2 → 1 winner
```

## Error Handling

The workflow handles several error conditions:

1. **Insufficient Candidates:** Less than 2 candidates with file edits skips judging
2. **Timeout:** Agents must complete within `gatherTimeoutMs` (5 minutes default)
3. **Success Threshold:** At least `gatherMinSuccessPercentage` (50%) of agents must succeed
4. **Phase Errors:** `PHASE_ERROR` state with `errorMessage` field for debugging

## Related Tasks

- TASK-15: Parallel Agent Workflow Analysis (foundation)
- TASK-57: Best-of-N Judge Service Analysis
- TASK-101: Best-of-N Worktrees Analysis
- TASK-103: Tournament Prompts Analysis
- Potential: TASK-XX: Investigate server-side tournament prompts
- Potential: TASK-XX: Analyze fanout voting mechanism
- Potential: TASK-XX: Worktree lifecycle and cleanup
