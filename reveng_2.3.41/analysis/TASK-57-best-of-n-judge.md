# TASK-57: Best-of-N Judge System Analysis

## Overview

The Best-of-N Judge is a feature in Cursor that evaluates and recommends the best result from multiple parallel agent runs. When a user submits a task with multiple models selected (e.g., "composer-1", "claude-4.5-opus-high", "gpt-5.1-codex"), each model runs in parallel in separate git worktrees, and a judge model evaluates which result is best.

## Architecture

### Key Components

1. **UI Judge Service** (`uiBestOfNJudgeService`)
   - Located around line 716398 in workbench.desktop.main.js
   - Coordinates the judging process on the client side
   - Communicates with the server via streaming gRPC

2. **Protobuf Message Types** (aiserver.v1 namespace)
   - `UiBestOfNJudgeCandidate` - Represents a candidate result
   - `StreamUiBestOfNJudgeStartRequest` - Initiates judging
   - `UiBestOfNJudgeFinalResult` - Contains winner and reasoning
   - `StreamUiBestOfNJudgeClientMessage` - Client-to-server messages
   - `StreamUiBestOfNJudgeServerMessage` - Server-to-client messages

### Message Schemas

#### UiBestOfNJudgeCandidate
```javascript
{
    composerId: string,    // Identifier for the composer session
    diff: DiffMessage      // Git diff of changes made by this candidate
}
```

#### StreamUiBestOfNJudgeStartRequest
```javascript
{
    task: string,          // The original user task/prompt
    candidates: [          // Array of candidates to evaluate
        UiBestOfNJudgeCandidate
    ]
}
```

#### UiBestOfNJudgeFinalResult
```javascript
{
    winnerComposerId: string,  // The ID of the winning candidate
    reasoning: string          // Explanation for why this candidate won
}
```

## Judging Process Flow

### 1. Triggering the Judge

The judge is triggered when:
- Multiple models are selected for a task
- The `worktrees_bon_judge` feature flag is enabled (default: true)
- The `disableBestOfNRecommender` setting is false
- The task is not in "plan" mode

```javascript
// From line 766720-766729
const Kwe = e.configurationService.getValue(Zwr) ?? !1;  // disableBestOfNRecommender
const ote = Jr.data.unifiedMode === "plan";

if (l() && !Kwe && !ote) {
    const fM = [Jr.data.composerId, ...ox];
    await VV.get(vJc).startBestOfNJudge(Jr.data.composerId, fM, xn);
}
```

### 2. Candidate Collection

Before judging, the service:
1. Collects candidates from all parallel composer sessions
2. Gets the git diff for each candidate's worktree
3. Waits up to 5 seconds for file edits to complete
4. Filters out candidates that made no file changes

```javascript
// From line 716442-716469
async startBestOfNJudge(e, t, n) {
    const s = Array.from(new Set(t));
    if (s.length < 2) return;  // Need at least 2 candidates

    this.setStatusFor(s, "judging");

    // Get diffs for each candidate
    const a = s.map(async Z => {
        const te = this.composerDataService.getComposerData(Z)?.gitWorktree?.worktreePath;
        if (!te) return;

        const ne = await this.gitContextService.getDiff(new BMe({
            cwd: te,
            mergeBase: !0,
            maxUntrackedFiles: 200
        }));

        if (ne?.diff) {
            return new UiBestOfNJudgeCandidate({
                composerId: Z,
                diff: ne.diff
            });
        }
    });

    const d = (await Promise.all(a)).filter(Z => Z !== void 0);

    // Skip if fewer than 2 valid candidates
    if (d.length < 2) {
        this.setStatusFor(s, "done");
        return;
    }
}
```

### 3. Server-Side Evaluation

The actual judging happens server-side. The client:
1. Opens a bidirectional stream to `StreamUiBestOfNJudge`
2. Sends the start request with task and candidates
3. Receives the final result with winner and reasoning

```javascript
// From line 716471-716482
const g = await this.aiService.aiClient();
const w = new StreamUiBestOfNJudgeStartRequest({
    task: n,
    candidates: d
});

p.push(new StreamUiBestOfNJudgeClientMessage({
    message: {
        case: "start",
        value: w
    }
}));

const _ = g.streamUiBestOfNJudge(p, { signal: o });
```

## Configuration

### Feature Flags

| Flag | Default | Description |
|------|---------|-------------|
| `worktrees_bon_judge` | `true` | Enable/disable the BON judge feature |

### User Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `disableBestOfNRecommender` | boolean | `false` | "Disable the Best-of-N recommender feature that judges and recommends the best result from multiple parallel agent runs." |

### Server Configuration

```javascript
// From line 294988-295292
background_agent_judge_config: {
    judgeModel: "gpt-5-high",       // Model used for judging
    summarizerModel: "gpt-5-mini",  // Model for summarization
    bestOfNModels: ["gpt-5"],       // Default models for BON runs
    patchRejectorStatus: "off"      // Patch rejection feature status
}
```

### Default Best-of-N Models

```javascript
// From line 182750
bestOfNDefaultModels: ["composer-1", "claude-4.5-opus-high", "gpt-5.1-codex"]
```

## UI Display

### Winner Indication

The winning result is indicated with a thumbs-up icon:

```javascript
// From line 762606
`${ot.asClassName(de.thumbsup)} model-card__best-indicator`
```

### Reasoning Display

The reasoning is parsed to extract a summary and optional justification:

```javascript
// From line 762277-762292
const t = l => {
    const d = l.indexOf("\n---\n");
    if (d !== -1) {
        const h = l.slice(0, d).trim();
        const f = l.slice(d + 5).trim();
        return {
            summary: h,
            justification: f.length > 0 ? f : null
        };
    }
    return {
        summary: l,
        justification: null
    };
};
```

The reasoning format appears to be:
```
Summary of why this result was selected
---
Detailed justification (optional)
```

### Composer State

Each composer tracks judge-related state:

```javascript
// From line 215129-215131
bestOfNJudgeStatus: void 0,    // "judging" | "done"
bestOfNJudgeWinner: !1,        // boolean
bestOfNJudgeReasoning: void 0, // string
```

## Judging Criteria (Server-Side - NOT VISIBLE)

**Important Note:** The actual judging criteria and prompts are NOT present in the client-side code. The evaluation happens entirely on the server side. The client only:

1. Collects git diffs from each candidate
2. Sends the original task and diffs to the server
3. Receives the winner ID and reasoning

Based on the data sent to the server, the judge likely evaluates:

1. **Code Quality** - Based on the git diff content
2. **Task Completion** - How well the changes address the original task
3. **Implementation Approach** - The strategy used to solve the problem

The server returns a `reasoning` string that explains the selection, which is displayed to the user.

## Analytics Events

### Events Tracked

```javascript
// From line 762352-762368
"best_of_n.view_subcomposer" {
    modelName: string,
    bestOfNSubmitId: string,
    viewedComposerId: string
}
```

```javascript
// From line 766709-766711
"agent_layout.multi_model_submission" {
    numModels: number
}
```

## RPC Service Endpoints

From line 440152-440165 and 549300-549313:

```javascript
streamUiBestOfNJudge: {
    name: "StreamUiBestOfNJudge",
    I: StreamUiBestOfNJudgeClientMessage,
    O: StreamUiBestOfNJudgeServerMessage,
    kind: MethodKind.BiDiStreaming
},
streamUiBestOfNJudgeSSE: {
    name: "StreamUiBestOfNJudgeSSE",
    // SSE fallback variant
},
streamUiBestOfNJudgePoll: {
    name: "StreamUiBestOfNJudgePoll",
    // Polling fallback variant
}
```

## Related Features

### Agent Exec Integration

The judge service integrates with the agent execution system for additional evaluation:

```javascript
// From line 716498-716500
const B = this.agentExecProvider.createRemoteAccessor(D, P, A, {
    workspacePaths: T
}, M, Ut.None);
```

### Worktree Management

Each candidate runs in a separate git worktree:

```javascript
const te = this.composerDataService.getComposerData(Z)?.gitWorktree?.worktreePath;
```

## Limitations of This Analysis

1. **Judge Prompts Not Visible** - The actual system prompts used by the judge model are server-side only
2. **Scoring Logic Not Visible** - How candidates are scored/compared is server-side
3. **Criteria Weights Unknown** - We cannot determine what factors matter most in selection
4. **Model-Specific Handling Unknown** - Whether different models are handled differently by the judge

## Summary

The Best-of-N Judge system allows Cursor to:
1. Run multiple AI models in parallel on the same task
2. Collect the git diffs produced by each model
3. Send the task description and all diffs to a judge model (gpt-5-high by default)
4. Receive a winner selection with reasoning
5. Display the recommended result to the user with explanation

The judging logic and prompts are entirely server-side, meaning the actual criteria for selection are not visible in the client code. The client is responsible only for collecting candidate diffs and displaying the results.
