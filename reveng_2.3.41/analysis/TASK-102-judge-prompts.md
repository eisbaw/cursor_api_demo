# TASK-102: Reverse Engineer Server-Side Judge Prompts via API Interception

## Executive Summary

The Best-of-N judging system in Cursor 2.3.41 uses a **server-side evaluation model** where the actual judging prompts and criteria are NOT present in the client code. This analysis documents what IS observable from the client-side code and identifies the key API interception points that would be required to reverse engineer the server-side judge prompts.

**Key Finding**: The judge prompt construction happens entirely server-side. The client only sends:
1. The original user task (as a string)
2. Git diffs from each candidate worktree

The server returns:
1. A winner composer ID
2. Reasoning text (summary + optional justification)

## Architecture Overview

### Client-Server Communication Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT                                      │
├─────────────────────────────────────────────────────────────────────┤
│  1. Collect git diffs from each worktree (mergeBase: true)          │
│  2. Create StreamUiBestOfNJudgeStartRequest                          │
│  3. Open bidirectional gRPC stream                                   │
│  4. Wait for UiBestOfNJudgeFinalResult                              │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ gRPC BiDi Stream
                                  │ (StreamUiBestOfNJudge)
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          SERVER                                      │
├─────────────────────────────────────────────────────────────────────┤
│  1. Receive task string + candidate diffs                           │
│  2. [OPAQUE] Construct judge prompt                                 │
│  3. [OPAQUE] Call judge model (gpt-5-high by default)              │
│  4. [OPAQUE] Parse model response for winner selection             │
│  5. Return winnerComposerId + reasoning                            │
└─────────────────────────────────────────────────────────────────────┘
```

## Protobuf Message Schemas

### Request Messages

#### StreamUiBestOfNJudgeClientMessage
**TypeName**: `aiserver.v1.StreamUiBestOfNJudgeClientMessage`
**Location**: Lines 159036, 529030

```protobuf
message StreamUiBestOfNJudgeClientMessage {
  oneof message {
    StreamUiBestOfNJudgeStartRequest start = 1;
    ExecClientMessage exec_client_message = 2;
    ExecClientControlMessage exec_client_control_message = 3;
  }
}
```

#### StreamUiBestOfNJudgeStartRequest
**TypeName**: `aiserver.v1.StreamUiBestOfNJudgeStartRequest`
**Location**: Lines 158963, 528964

```protobuf
message StreamUiBestOfNJudgeStartRequest {
  string task = 1;                              // Original user prompt
  repeated UiBestOfNJudgeCandidate candidates = 2;  // Candidate results
}
```

#### UiBestOfNJudgeCandidate
**TypeName**: `aiserver.v1.UiBestOfNJudgeCandidate`
**Location**: Lines 158928, 528932

```protobuf
message UiBestOfNJudgeCandidate {
  string composer_id = 1;   // Identifier for the composer session
  GitDiff diff = 2;         // Git diff of changes made
}
```

### Response Messages

#### StreamUiBestOfNJudgeServerMessage
**TypeName**: `aiserver.v1.StreamUiBestOfNJudgeServerMessage`
**Location**: Lines 159081, 529071

```protobuf
message StreamUiBestOfNJudgeServerMessage {
  oneof message {
    UiBestOfNJudgeFinalResult final_result = 1;
    ExecServerMessage exec_server_message = 2;
    ExecServerControlMessage exec_server_control_message = 3;
  }
}
```

#### UiBestOfNJudgeFinalResult
**TypeName**: `aiserver.v1.UiBestOfNJudgeFinalResult`
**Location**: Lines 158999, 528997

```protobuf
message UiBestOfNJudgeFinalResult {
  string winner_composer_id = 1;  // ID of the winning candidate
  string reasoning = 2;           // Explanation for selection
}
```

### GitDiff Structure

**TypeName**: `aiserver.v1.GitDiff`
**Location**: Line 90524

```protobuf
message GitDiff {
  repeated FileDiff diffs = 1;
  DiffType diff_type = 2;

  enum DiffType {
    DIFF_TYPE_UNSPECIFIED = 0;
    DIFF_TYPE_DIFF_TO_HEAD = 1;
    DIFF_TYPE_DIFF_FROM_BRANCH_TO_MAIN = 2;
  }
}
```

**TypeName**: `aiserver.v1.FileDiff`
**Location**: Line 90571

```protobuf
message FileDiff {
  int32 added = 4;                       // Lines added
  int32 removed = 5;                     // Lines removed
  string from = 1;                       // Original file path
  string to = 2;                         // New file path
  repeated Chunk chunks = 3;             // Diff hunks
  optional string before_file_contents = 6;
  optional string after_file_contents = 7;
}

message Chunk {
  string content = 1;          // Chunk header
  repeated string lines = 2;   // Diff lines
  int32 old_start = 3;
  int32 old_lines = 4;
  int32 new_start = 5;
  int32 new_lines = 6;
}
```

## Server Configuration (From Remote Config)

**Location**: Lines 294988-295289

```javascript
background_agent_judge_config: {
    judgeModel: "gpt-5-high",           // Model used for judging
    summarizerModel: "gpt-5-mini",      // Model for summarization
    bestOfNModels: ["gpt-5"],           // Default models for parallel runs
    patchRejectorStatus: "off"          // Patch rejection feature status
}
```

### Parallel Agent Synthesis Configuration

**Location**: Lines 295570-295576

```javascript
parallel_agent_synthesis_config: {
    strategy: "pairwise_tournament",     // Judging strategy
    synthesisModel: "gpt-5.1-codex-high",
    fanoutSize: null
}
```

This reveals the server uses a **pairwise tournament** strategy for comparing candidates.

## Reasoning Format

The client parses the reasoning to extract a summary and optional justification:

**Location**: Lines 762277-762292

```javascript
const parseReasoning = (text) => {
    const separatorIndex = text.indexOf("\n---\n");
    if (separatorIndex !== -1) {
        const summary = text.slice(0, separatorIndex).trim();
        const justification = text.slice(separatorIndex + 5).trim();
        return {
            summary: summary,
            justification: justification.length > 0 ? justification : null
        };
    }
    return {
        summary: text,
        justification: null
    };
};
```

**Expected Reasoning Format**:
```
Summary of why this result was selected
---
Detailed justification (optional)
```

## API Interception Points

### 1. gRPC Service Definition

**Service**: `aiserver.v1.AiService`
**Location**: Lines 439286, 548434

```javascript
{
    typeName: "aiserver.v1.AiService",
    methods: {
        // ... other methods ...
        streamUiBestOfNJudge: {
            name: "StreamUiBestOfNJudge",
            I: StreamUiBestOfNJudgeClientMessage,
            O: StreamUiBestOfNJudgeServerMessage,
            kind: MethodKind.BiDiStreaming  // Bidirectional streaming (kind: 3)
        },
        streamUiBestOfNJudgeSSE: {
            name: "StreamUiBestOfNJudgeSSE",
            kind: MethodKind.ServerStreaming  // SSE fallback (kind: 1)
        },
        streamUiBestOfNJudgePoll: {
            name: "StreamUiBestOfNJudgePoll",
            kind: MethodKind.ServerStreaming  // Polling fallback (kind: 1)
        }
    }
}
```

### 2. Transport Layer

**Location**: Lines 832147-832187

The client uses a Connect transport provider that routes gRPC calls through the main process:
- `$callAiConnectTransportProviderStream`
- `$pushAiConnectTransportStreamChunk`
- `$endAiConnectTransportStreamChunk`
- `$cancelAiConnectTransportStreamChunk`

### 3. Client Code Interception Point

**Location**: Lines 716470-716482

```javascript
const client = await this.aiService.aiClient();
const messageQueue = new AsyncQueue();
const startRequest = new StreamUiBestOfNJudgeStartRequest({
    task: userTask,
    candidates: candidatesWithDiffs
});

messageQueue.push(new StreamUiBestOfNJudgeClientMessage({
    message: {
        case: "start",
        value: startRequest
    }
}));

const stream = client.streamUiBestOfNJudge(messageQueue, { signal });
```

## Interception Strategies

### Strategy 1: Network Proxy (MITM)

Intercept the gRPC traffic between client and server:
- Endpoint: `https://api2.cursor.sh` (or regional variants)
- Service path: `/aiserver.v1.AiService/StreamUiBestOfNJudge`
- Protocol: HTTP/2 + gRPC

**Challenges**:
- gRPC uses binary protobuf encoding
- TLS certificate pinning may be present
- Need to decode streaming responses

### Strategy 2: Electron DevTools Protocol

Attach to the Electron process and intercept IPC calls:
- Hook `$callAiConnectTransportProviderStream`
- Log the serialized request before transmission
- Log the deserialized response after receipt

### Strategy 3: Code Injection

Modify the client code to log judge requests/responses:

```javascript
// Patch the streamUiBestOfNJudge call
const originalMethod = client.streamUiBestOfNJudge;
client.streamUiBestOfNJudge = async function*(req, opts) {
    console.log("[JUDGE_REQUEST]", JSON.stringify(req, null, 2));
    for await (const msg of originalMethod.call(this, req, opts)) {
        console.log("[JUDGE_RESPONSE]", JSON.stringify(msg, null, 2));
        yield msg;
    }
};
```

## Related Analysis Tool: ReflectTool

The codebase contains a `ReflectTool` that appears to be used for agent self-reflection:

**TypeName**: `agent.v1.ReflectArgs`
**Location**: Lines 137179, 242807

```protobuf
message ReflectArgs {
  string unexpected_action_outcomes = 1;  // What went wrong
  string relevant_instructions = 2;        // Applicable guidance
  string scenario_analysis = 3;            // Analysis of situation
  string critical_synthesis = 4;           // Key conclusions
  string next_steps = 5;                   // Recommended actions
  string tool_call_id = 6;                 // Reference to tool call
}
```

This tool is invoked by agents to analyze their progress, but is NOT the same as the Best-of-N judge - it's used for individual agent reflection, not cross-agent comparison.

## What Cannot Be Determined from Client Code

1. **Judge System Prompt** - The instructions given to the judge model are server-side only
2. **Evaluation Criteria** - The specific criteria for comparing candidates (code quality, completeness, efficiency, etc.)
3. **Scoring Mechanism** - Whether numerical scores are used internally
4. **Pairwise Comparison Details** - How the "pairwise_tournament" strategy works
5. **Model-Specific Handling** - Whether different source models are evaluated differently
6. **Tie-Breaking Logic** - How ties are resolved

## Hypothesized Judge Prompt Structure

Based on the data sent to the server, the judge prompt likely follows this structure:

```
[SYSTEM]
You are a code review judge evaluating {N} candidate implementations.

Task: {user_task}

Candidate A (model: composer-1):
```diff
{git_diff_a}
```

Candidate B (model: claude-4.5-opus-high):
```diff
{git_diff_b}
```

[... more candidates ...]

Select the best implementation and explain your reasoning.
Format your response as:
<summary>Brief explanation of selection</summary>
---
<justification>Detailed analysis (optional)</justification>
<winner>composer_id</winner>
```

## Recommendations for API Interception

1. **Use mitmproxy with gRPC plugin** - Decode protobuf traffic in real-time
2. **Build a local proxy server** - Implement `StreamUiBestOfNJudge` that logs and forwards
3. **Patch Electron IPC** - Hook the main process transport layer
4. **Monitor server responses** - Analyze the reasoning text patterns to infer prompt structure

## Files Referenced

| Location | Description |
|----------|-------------|
| Line 158920-159099 | Protobuf message definitions |
| Line 294988-295292 | Server configuration schema |
| Line 439286-440169 | gRPC service definitions |
| Line 528926-529103 | Duplicate protobuf definitions |
| Line 549300-549316 | Service method definitions |
| Line 716398-716543 | UI Best-of-N Judge Service implementation |
| Line 762277-762292 | Reasoning parser |
| Line 832147-832248 | Connect transport layer |

## Summary

The Best-of-N judge system is architected with a clear client-server boundary:

**Client Responsibilities**:
- Collect git diffs from parallel worktrees
- Submit task + diffs via gRPC stream
- Display winner selection and reasoning

**Server Responsibilities** (opaque):
- Construct judge prompt from task and diffs
- Call judge model (gpt-5-high)
- Parse model response to extract winner
- Return winner ID and reasoning text

To reverse engineer the actual judge prompts, one would need to either:
1. Intercept and decode the server-side LLM API calls
2. Analyze patterns in the reasoning responses across many judge invocations
3. Gain access to server-side source code or configuration

The client code provides all the context needed to SET UP an interception, but the actual prompt content is never visible to the client.
