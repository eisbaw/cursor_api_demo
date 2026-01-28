# TASK-15: Parallel Agent Workflow Analysis

## Overview

Cursor implements a sophisticated parallel agent workflow system that allows multiple AI agents to work concurrently on the same task, with mechanisms to synthesize and select the best results.

## Core Architecture

### 1. Parallel Agent Workflow Types (aiserver.v1)

**Source Location:** Lines 335692-338520

#### EnsembleStatus Enum
```javascript
// aiserver.v1.EnsembleStatus
{
  UNSPECIFIED: 0,
  PARENT: 1,     // Parent workflow coordinator
  CHILD: 2       // Child agent worker
}
```

#### Workflow Phases
```javascript
// aiserver.v1.ParallelAgentWorkflowStatusUpdate.Phase
{
  UNSPECIFIED: 0,
  STARTING: 1,           // Initial setup
  CHILDREN_RUNNING: 2,   // Parallel execution phase
  GATHERING: 3,          // Collecting results
  SYNTHESIZING: 4,       // Merging/selecting results
  COMPLETED: 5,          // Successfully finished
  ERROR: 6               // Error state
}
```

### 2. Synthesis Strategies

**Source Location:** Lines 335701-335712

Three distinct strategies for combining parallel agent results:

```javascript
// aiserver.v1.ParallelAgentWorkflowSynthesisStrategy
{
  UNSPECIFIED: 0,
  SINGLE_AGENT: 1,           // Use single agent result
  FANOUT_VOTING: 2,          // Multiple agents vote on best
  PAIRWISE_TOURNAMENT: 3     // Tournament-style elimination
}
```

**Default Configuration (Line 295570-295576):**
```javascript
parallel_agent_synthesis_config: {
  strategy: "pairwise_tournament",
  synthesisModel: "gpt-5.1-codex-high",
  fanoutSize: null
}
```

### 3. Protobuf Message Definitions

#### ParallelAgentWorkflowGatherConfig (Lines 338220-338258)
```javascript
{
  timeout_ms: optional int64,          // Max wait time for children
  min_success_count: optional int32,   // Minimum successful children required
  min_success_percentage: optional float // Min success ratio required
}
```

#### ParallelAgentWorkflowSynthesisConfig (Lines 338259-338298)
```javascript
{
  strategy: ParallelAgentWorkflowSynthesisStrategy,
  synthesis_model: ModelDetails,
  fanout_size: optional int32
}
```

#### StartParallelAgentWorkflowRequest (Lines 338299-338344)
```javascript
{
  base_request: ComposerRequest,
  child_model_details: repeated ModelDetails,  // Models for child agents
  gather_config: ParallelAgentWorkflowGatherConfig,
  synthesis_config: ParallelAgentWorkflowSynthesisConfig
}
```

#### StartParallelAgentWorkflowResponse (Lines 338345-338375)
```javascript
{
  parent_bc_id: string,   // Parent background composer ID
  workflow_id: string     // Unique workflow identifier
}
```

#### SynthesisTournamentProgress (Lines 338474-338515)
```javascript
{
  current_round: int32,
  total_rounds: int32,
  candidates_remaining: int32,
  initial_candidates: int32
}
```

### 4. Default Ensemble Configuration

**Source Location:** Lines 295561-295569

```javascript
parallel_agent_ensemble_config: {
  models: [
    "gpt-5.1-codex-high",
    "claude-4.5-sonnet-thinking",
    "gpt-5-codex-high",
    "claude-4.5-sonnet-thinking"
  ],
  gatherTimeoutMs: 300000,         // 5 minutes
  gatherMinSuccessPercentage: 0.5, // 50% must succeed
  gatherMinSuccessCount: null
}
```

### 5. gRPC Service Methods

**Source Location:** Lines 815753-815763

```javascript
BackgroundComposerService {
  startParallelAgentWorkflow: {
    name: "StartParallelAgentWorkflow",
    kind: Unary
  },
  streamParallelAgentWorkflowStatus: {
    name: "StreamParallelAgentWorkflowStatus",
    kind: ServerStreaming
  }
}
```

## Best-of-N Judge System

### Overview

A specialized subsystem for evaluating and selecting the best result from multiple parallel agent runs.

### Key Components

**Source Location:** Lines 158920-159082, 716398-716543

#### UiBestOfNJudgeCandidate
```javascript
{
  composer_id: string,
  diff: DiffMessage
}
```

#### StreamUiBestOfNJudgeStartRequest
```javascript
{
  task: string,
  candidates: repeated UiBestOfNJudgeCandidate
}
```

#### UiBestOfNJudgeFinalResult
```javascript
{
  winner_composer_id: string,
  reasoning: string
}
```

### Judge Service Implementation (Lines 716398-716543)

```javascript
class UiBestOfNJudgeService {
  setStatusFor(composerIds, status) {
    // Sets judge status: "judging" or "done"
    // Resets winner/reasoning when starting
  }

  setWinner(composerId, reasoning) {
    // Marks winning composer and stores reasoning
  }

  async startBestOfNJudge(parentId, candidateIds, task) {
    // 1. Collects diffs from all candidate worktrees
    // 2. Filters candidates with actual file edits
    // 3. Streams to StreamUiBestOfNJudge service
    // 4. Processes winner selection
  }
}
```

### Judge Configuration

**Source Location:** Lines 294988-295286

```javascript
background_agent_judge_config: {
  judgeModel: "gpt-5-high"
}
```

## Worktree Isolation

### How Parallel Agents Stay Isolated

Each parallel agent operates in its own git worktree, providing complete file system isolation.

**Key Data Structures (Lines 215040-215139):**
```javascript
ComposerData {
  gitWorktree: {
    worktreePath: string
  },
  reservedWorktree: object,
  isCreatingWorktree: boolean,
  isApplyingWorktree: boolean,
  isUndoingWorktree: boolean,
  applied: boolean,
  isBestOfNSubcomposer: boolean,
  isBestOfNParent: boolean,
  bestOfNJudgeStatus: "judging" | "done" | undefined,
  bestOfNJudgeWinner: boolean,
  bestOfNJudgeReasoning: string,
  subComposerIds: string[]
}
```

## Merge/Conflict Resolution

### Apply Worktree to Main Branch

**Source Location:** Lines 948390-948711

The `_applyWorktreeToCurrentBranchViaMerge` method handles merging agent changes:

1. **Collect Changes:** Gets all file changes from the worktree
2. **Detect Conflicts:** Compares agent changes against local changes
3. **User Dialog:** Presents merge conflict resolution options:
   - **Merge manually:** Apply changes with conflict markers
   - **Stash changes:** Stash local changes first
   - **Overwrite:** Use agent's version for conflicting files
   - **Undo & Apply:** Undo other applied agents first (for best-of-n)

### Conflict Dialog Options (Lines 948825-948960)

```javascript
// Dialog choices for merge conflicts
{
  "merge": "Apply all agent changes, then review and resolve conflicts manually",
  "stash": "Stash your local changes so you can apply them later",
  "overwrite": "Overwrite files with merge conflicts with agent's version",
  "undo_apply": "Undo all previously applied chats before applying this one",
  "cancel": "Cancel the operation"
}
```

### Conflict Markers
```
"Current (Your changes)" - local changes
"Incoming (Agent changes)" - AI's suggested changes
```

## UI Integration

### Parallel Agents Walkthrough (Lines 760400-760440)

```javascript
{
  key: "ParallelAgents",
  title: "Parallel Agents",
  description: "Run up to 8 Agents or models at the same time and choose the best outcome."
}
```

### Agent Layout Modes
```javascript
{
  GetStarted: "get_started",
  ManageAgents: "manage_agents",
  ChatCenter: "chat_center",
  ParallelAgents: "parallel_agents",
  EditorFocus: "editor_focus",
  UnifiedReview: "unified_review"
}
```

## Subagent System

### Subagent Types (Lines 121904-121918)

```javascript
// aiserver.v1.SubagentType
{
  UNSPECIFIED: 0,
  DEEP_SEARCH: 1,   // Deep code search
  FIX_LINTS: 2,     // Lint fixing
  TASK: 3,          // Task execution
  SPEC: 4           // Specification generation
}
```

### Custom Subagents (Lines 119481-119627)

```javascript
// agent.v1.CustomSubagentPermissionMode
{
  UNSPECIFIED: 0,
  DEFAULT: 1,
  READONLY: 2
}

// Custom subagent configuration
CustomSubagent {
  name: string,
  description: string,
  permission_mode: CustomSubagentPermissionMode
}
```

## Feature Flag

**Source Location:** Line 294441-294444

```javascript
parallel_agent_workflow: {
  client: true,
  default: false  // Disabled by default
}
```

## Workflow Lifecycle

```
1. STARTING
   - Create parent workflow
   - Initialize child model configurations
   - Reserve worktrees for each child

2. CHILDREN_RUNNING
   - Spawn child agents in parallel
   - Each child works in isolated worktree
   - Monitor progress and timeouts

3. GATHERING
   - Collect results from children
   - Apply success threshold filters
   - Prepare candidates for synthesis

4. SYNTHESIZING
   - Apply selected strategy:
     a) SINGLE_AGENT: Pick best single result
     b) FANOUT_VOTING: Agents vote on best
     c) PAIRWISE_TOURNAMENT: Bracket elimination
   - Judge evaluates diffs and task completion
   - Select winner with reasoning

5. COMPLETED / ERROR
   - Mark winner in UI
   - Allow user to apply winning worktree
   - Handle conflict resolution on merge
```

## Analytics Events

Key events tracked for parallel workflows:
- `composer.ensemble_model_picker.button_clicked`
- `git_worktree.apply_to_main`
- `git_worktree.apply_to_main.modal_choice`
- `git_worktree.apply_to_main.preference_saved`

## Key Findings

1. **Isolation via Worktrees:** Each parallel agent operates in a completely isolated git worktree, preventing conflicts during execution.

2. **Tournament-Style Selection:** The default synthesis strategy is `pairwise_tournament`, where agents compete in elimination rounds judged by a powerful model (gpt-5.1-codex-high).

3. **8-Agent Limit:** The UI advertises support for up to 8 parallel agents simultaneously.

4. **Model Diversity:** Default configuration uses a mix of GPT and Claude models for diversity in approaches.

5. **Intelligent Conflict Resolution:** When applying results, the system detects conflicts with local changes and provides multiple resolution strategies.

6. **Best-of-N Judge:** A specialized service streams diffs to a judge model that selects the winner with reasoning.

## Recommendations for Further Investigation

1. **Tournament Algorithm Details:** How exactly are pairwise comparisons structured? What prompts are used for judging?

2. **Fanout Voting Mechanism:** How is voting implemented? What consensus threshold is required?

3. **Worktree Lifecycle Management:** How are worktrees cleaned up after workflow completion?

4. **Error Recovery:** How does the system handle partial failures (some children succeed, some fail)?

5. **Custom Subagent Integration:** How do custom subagents participate in parallel workflows?
