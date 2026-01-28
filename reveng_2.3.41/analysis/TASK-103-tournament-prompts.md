# TASK-103: Server-Side Tournament Prompts - Pairwise Comparison Analysis

**Source**: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
**Date**: 2026-01-28

## Executive Summary

Cursor IDE implements a **pairwise tournament system** as the default synthesis strategy for parallel agent workflows. The system runs multiple AI agents in parallel, collects their outputs (diffs), and uses a server-side judging mechanism to select the best solution. The evaluation happens server-side via the `StreamUiBestOfNJudge` bidirectional streaming RPC.

## Tournament Architecture

### Synthesis Strategies (Enum)

```javascript
// aiserver.v1.ParallelAgentWorkflowSynthesisStrategy
{
  UNSPECIFIED: 0,
  SINGLE_AGENT: 1,      // No tournament - single agent execution
  FANOUT_VOTING: 2,     // Multiple agents vote on solution
  PAIRWISE_TOURNAMENT: 3 // Bracket-style tournament (DEFAULT)
}
```

**Default Strategy**: `pairwise_tournament` is the fallback default (line 295573)

### Default Configuration

```javascript
// parallel_agent_synthesis_config fallback values (line 295570-295576)
{
  strategy: "pairwise_tournament",
  synthesisModel: "gpt-5.1-codex-high",  // Judge model
  fanoutSize: null
}

// parallel_agent_ensemble_config fallback values (line 295561-295568)
{
  models: [
    "gpt-5.1-codex-high",
    "claude-4.5-sonnet-thinking",
    "gpt-5-codex-high",
    "claude-4.5-sonnet-thinking"
  ],
  gatherTimeoutMs: 300000,          // 5 minute timeout
  gatherMinSuccessPercentage: 0.5,  // 50% must complete
  gatherMinSuccessCount: null
}
```

## Tournament Progress Tracking

### SynthesisTournamentProgress Message

```protobuf
// aiserver.v1.SynthesisTournamentProgress (line 338483-338504)
message SynthesisTournamentProgress {
  int32 current_round = 1;      // Current round in tournament
  int32 total_rounds = 2;       // Total rounds needed
  int32 candidates_remaining = 3; // Remaining candidates
  int32 initial_candidates = 4;  // Starting candidate count
}
```

This structure tracks bracket progression through elimination rounds.

### Parallel Agent Workflow Phases

```javascript
// aiserver.v1.ParallelAgentWorkflowStatusUpdate.Phase (line 338453-338473)
{
  UNSPECIFIED: 0,
  STARTING: 1,           // Workflow initialization
  CHILDREN_RUNNING: 2,   // Parallel agents executing
  GATHERING: 3,          // Collecting results
  SYNTHESIZING: 4,       // Tournament/voting in progress
  COMPLETED: 5,          // Winner selected
  ERROR: 6               // Workflow failed
}
```

## Candidate Evaluation: UiBestOfNJudge Protocol

### Request Format

The tournament uses a bidirectional streaming RPC `StreamUiBestOfNJudge`.

```protobuf
// aiserver.v1.StreamUiBestOfNJudgeStartRequest (line 158963-158977)
message StreamUiBestOfNJudgeStartRequest {
  string task = 1;                       // Original user task/prompt
  repeated UiBestOfNJudgeCandidate candidates = 2;  // Solutions to compare
}

// aiserver.v1.UiBestOfNJudgeCandidate (line 158928-158941)
message UiBestOfNJudgeCandidate {
  string composer_id = 1;    // ID of the agent/composer that produced this
  Diff diff = 2;             // The actual code changes (diff)
}
```

### Response Format

```protobuf
// aiserver.v1.UiBestOfNJudgeFinalResult (line 158999-159012)
message UiBestOfNJudgeFinalResult {
  string winner_composer_id = 1;  // ID of winning solution
  string reasoning = 2;           // Explanation of selection
}
```

### Client/Server Message Protocol

```protobuf
// aiserver.v1.StreamUiBestOfNJudgeClientMessage (line 159036-159057)
message StreamUiBestOfNJudgeClientMessage {
  oneof message {
    StreamUiBestOfNJudgeStartRequest start = 1;
    ExecClientMessage exec_client_message = 2;
    ExecClientControlMessage exec_client_control_message = 3;
  }
}

// aiserver.v1.StreamUiBestOfNJudgeServerMessage (line 159081-159102)
message StreamUiBestOfNJudgeServerMessage {
  oneof message {
    UiBestOfNJudgeFinalResult final_result = 1;
    ExecServerMessage exec_server_message = 2;
    ExecServerControlMessage exec_server_control_message = 3;
  }
}
```

## Winner Selection Logic

### Client-Side Judging Flow (line 716442-716540)

```javascript
async startBestOfNJudge(e, t, n) {
    const s = Array.from(new Set(t));
    if (s.length < 2) return;  // Need at least 2 candidates

    this.setStatusFor(s, "judging");

    // 1. Gather diffs from each candidate's worktree
    const a = s.map(async Z => {
        const te = this.composerDataService.getComposerData(Z)
            ?.gitWorktree?.worktreePath;
        if (!te) return;

        const ne = (await this.gitContextService.getDiff(new BMe({
            cwd: te,
            mergeBase: true,
            maxUntrackedFiles: 200
        })))?.diff;

        if (ne) return new HMr({
            composerId: Z,
            diff: ne
        });
    });

    const d = (await Promise.all(a)).filter(Z => Z !== void 0);
    if (d.length < 2) {
        this.setStatusFor(s, "done");
        return;
    }

    // 2. Wait for file edits to complete (5 second timeout)
    if ((await Promise.all(d.map(Z =>
        this.waitForFileEdits(Z.composerId, 5000)
    ))).some(Z => !Z)) {
        console.info("[best-of-n judge] Skipping judge because at least one composer made zero file edits");
        this.setStatusFor(s, "done");
        return;
    }

    // 3. Start streaming judge request
    const g = await this.aiService.aiClient();
    const p = new l$(void 0);
    const w = new $Mr({
        task: n,      // Original user task
        candidates: d  // Array of {composerId, diff}
    });

    p.push(new y5t({
        message: {
            case: "start",
            value: w
        }
    }));

    const _ = g.streamUiBestOfNJudge(p, { signal: o });

    // 4. Process responses
    for await (const ne of _) {
        const ce = ne.message;
        if (ce.case === "execServerMessage") {
            Z.push(ce.value);
        } else if (ce.case === "execServerControlMessage") {
            Z.push(ce.value);
        } else if (ce.case === "finalResult") {
            const ae = ce.value.winnerComposerId;
            const pe = ce.value.reasoning;

            this.setStatusFor(s, "done");
            if (ae && s.includes(ae)) {
                this.setWinner(ae, pe);  // Mark winner
            }
            this.markParentComposerUnread(e);
            break;
        }
    }
}
```

### Winner State Management

```javascript
// Setting winner status (line 716408-716411)
setWinner(e, t) {
    this.composerDataService.updateComposerDataSetStore(e, n => {
        n("bestOfNJudgeWinner", true);
        n("bestOfNJudgeReasoning", t);
    });
}

// Setting judging status (line 716402-716406)
setStatusFor(e, t) {
    for (const n of e) {
        this.composerDataService.updateComposerDataSetStore(n, s => {
            s("bestOfNJudgeStatus", t);
            if (t === "judging") {
                s("bestOfNJudgeWinner", false);
                s("bestOfNJudgeReasoning", void 0);
            }
        });
    }
}
```

## Best-of-N Model Configuration

### Default Models for Best-of-N

```javascript
// bestOfNDefaultModels array (line 711400, 182750)
["composer-1", "claude-4.5-opus-high", "gpt-5.1-codex"]

// Selection function (line 711402-711404)
function vdo(i) {
    const e = i?.composer;
    return e?.bestOfNDefaultModels && e.bestOfNDefaultModels.length > 0
        ? e.bestOfNDefaultModels
        : Pcf;  // fallback to default array
}
```

### Triggering Best-of-N Judge (line 766720-766729)

```javascript
// After agent completion, trigger UI judge
if (l() && !Kwe && !ote) {
    try {
        const fM = [Jr.data.composerId, ...ox];  // Parent + children
        await e.instantiationService.invokeFunction(async VV => {
            await VV.get(vJc).startBestOfNJudge(
                Jr.data.composerId,  // Parent composer ID
                fM,                  // All composer IDs
                xn                   // Task/prompt
            );
        });
    } catch (fM) {
        console.error("[best-of-n judge] Failed to run UI judge", fM);
    }
}
```

## Ensemble Status

```javascript
// aiserver.v1.EnsembleStatus (line 335692-335700)
{
  UNSPECIFIED: 0,
  PARENT: 1,   // Parent orchestrator
  CHILD: 2     // Child agent in ensemble
}
```

## Parallel Agent Workflow Protocol

### Starting Workflow Request

```protobuf
// aiserver.v1.StartParallelAgentWorkflowRequest (line 338308-338330)
message StartParallelAgentWorkflowRequest {
  BaseRequest base_request = 1;
  repeated ModelDetails child_model_details = 2;  // Models for children
  ParallelAgentWorkflowGatherConfig gather_config = 3;
  ParallelAgentWorkflowSynthesisConfig synthesis_config = 4;
}
```

### Response

```protobuf
// aiserver.v1.StartParallelAgentWorkflowResponse (line 338352-338363)
message StartParallelAgentWorkflowResponse {
  string parent_bc_id = 1;   // Parent background composer ID
  string workflow_id = 2;    // Workflow tracking ID
}
```

### Streaming Status Updates

```protobuf
// aiserver.v1.StreamParallelAgentWorkflowStatusRequest (line 338383-338394)
message StreamParallelAgentWorkflowStatusRequest {
  string workflow_id = 1;
  string bc_id = 2;  // Background composer ID
}

// aiserver.v1.ParallelAgentWorkflowStatusUpdate (line 338416-338440)
message ParallelAgentWorkflowStatusUpdate {
  Phase phase = 1;
  optional string synthesis_bc_id = 2;
  optional string error_message = 3;
  optional SynthesisTournamentProgress tournament_progress = 4;
}
```

## API Endpoints

| Method | Request Type | Response Type | Streaming |
|--------|--------------|---------------|-----------|
| `StartParallelAgentWorkflow` | StartParallelAgentWorkflowRequest | StartParallelAgentWorkflowResponse | Unary |
| `StreamParallelAgentWorkflowStatus` | StreamParallelAgentWorkflowStatusRequest | ParallelAgentWorkflowStatusUpdate | Server |
| `StreamUiBestOfNJudge` | StreamUiBestOfNJudgeClientMessage | StreamUiBestOfNJudgeServerMessage | BiDi |
| `StreamUiBestOfNJudgeSSE` | ExecStartRequest | StreamUiBestOfNJudgeServerMessage | Server |
| `StreamUiBestOfNJudgePoll` | PollRequest | PollResponse | Server |

## Key Findings

### 1. Server-Side Evaluation

The actual comparison/judging logic happens **server-side**. The client:
- Collects diffs from each candidate's git worktree
- Sends the task prompt and candidate diffs to the server
- Receives winner ID and reasoning from server

The server presumably:
- Uses the `synthesisModel` (default: `gpt-5.1-codex-high`) to evaluate
- Runs pairwise comparisons in bracket format
- Returns reasoning explaining the selection

### 2. Tournament Bracket Structure

Based on `SynthesisTournamentProgress`:
- `initial_candidates` - Starting number of solutions
- `total_rounds` - Number of elimination rounds (log2 of candidates)
- `current_round` - Progress through tournament
- `candidates_remaining` - Who's left in competition

### 3. Diff-Based Comparison

Candidates are compared based on their **diffs against main/base branch**:
- Uses `mergeBase: true` for proper diff calculation
- Includes up to 200 untracked files
- Each candidate identified by their `composerId`

### 4. Winner Display

The winning solution is marked with:
- `bestOfNJudgeWinner: true`
- `bestOfNJudgeReasoning: <explanation>`

Reasoning is parsed into summary/justification for display (line 762295-762305).

## Related Tasks

- TASK-101: Best-of-N worktrees analysis
- TASK-105: Best-of-N execution flow
- TASK-55: Tournament algorithm details
- TASK-57: Best-of-N judge mechanism

## Open Questions

1. **Exact tournament prompt**: The server-side prompt used to evaluate candidates is not visible in client code
2. **Bracket seeding**: How are initial matchups determined in the pairwise tournament?
3. **Tie handling**: What happens when tournament produces ambiguous results?
4. **Caching**: Are tournament results cached or re-evaluated on restart?

## Lines of Interest

| Line Number | Description |
|-------------|-------------|
| 295561-295576 | Default ensemble/synthesis config |
| 335701-335712 | Synthesis strategy enum |
| 338453-338473 | Workflow phase enum |
| 338483-338504 | Tournament progress structure |
| 528927-529101 | Judge message types |
| 716442-716540 | startBestOfNJudge implementation |
| 766720-766729 | Judge invocation after completion |
