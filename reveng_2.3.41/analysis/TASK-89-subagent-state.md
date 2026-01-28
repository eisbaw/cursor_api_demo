# TASK-89: SubagentPersistedState and Nested Agent Conversations Analysis

## Overview

This document analyzes how Cursor IDE 2.3.41 manages subagent states within the `ConversationStateStructure`, including nested conversation state management, parent-child agent relationships, and subagent lifecycle management.

## Key Findings

### 1. SubagentPersistedState Protobuf Structure

**Location**: `agent.v1.SubagentPersistedState` (lines 141005-141045, 247730-247772)

```protobuf
message SubagentPersistedState {
  ConversationStateStructure conversation_state = 1;  // Full nested conversation state
  uint64 created_timestamp_ms = 2;                    // When subagent was created
  uint64 last_used_timestamp_ms = 3;                  // Last activity timestamp
  SubagentType subagent_type = 4;                     // Type categorization
}
```

**Key Insight**: Each subagent maintains its own complete `ConversationStateStructure`, enabling fully independent nested conversations with their own turns, todos, summaries, and file states.

### 2. ConversationStateStructure with Subagent States

**Location**: Lines 247773-247924

The parent conversation structure includes a map of subagent states:

```protobuf
message ConversationStateStructure {
  repeated bytes turns_old = 2;                       // Legacy turns
  repeated bytes root_prompt_messages_json = 1;       // Root prompts
  repeated bytes turns = 8;                           // Current turns
  repeated bytes todos = 3;                           // Todo items
  repeated string pending_tool_calls = 4;             // Active tool calls
  TokenDetails token_details = 5;                     // Token tracking
  bytes summary = 6;                                  // Conversation summary
  bytes plan = 7;                                     // Plan state
  repeated string previous_workspace_uris = 9;        // Workspace history
  AgentMode mode = 10;                                // Agent mode
  bytes summary_archive = 11;                         // Archived summaries
  map<string, bytes> file_states = 12;                // File state tracking
  map<string, FileStateV2> file_states_v2 = 15;       // Enhanced file states
  repeated bytes summary_archives = 13;               // Summary archive list
  repeated TurnTiming turn_timings = 14;              // Timing metrics
  map<string, SubagentPersistedState> subagent_states = 16;  // NESTED SUBAGENTS
  uint32 self_summary_count = 17;                     // Summary counter
  repeated string read_paths = 18;                    // Accessed file paths
}
```

**Key Point**: The `subagent_states` field (field 16) is a map keyed by string (likely subagent ID) to `SubagentPersistedState`, creating a recursive structure where each subagent can theoretically contain its own subagent states.

### 3. Subagent Type System

#### Agent-Level Types (`agent.v1.SubagentType`)
**Location**: Lines 119499-119618

```protobuf
message SubagentType {
  oneof type {
    SubagentTypeUnspecified unspecified = 1;
    SubagentTypeComputerUse computer_use = 2;
    SubagentTypeCustom custom = 3;
  }
}

message SubagentTypeUnspecified {}
message SubagentTypeComputerUse {}
message SubagentTypeCustom {
  string name = 1;  // Custom subagent identifier
}
```

#### Server-Level Types (`aiserver.v1.SubagentType`)
**Location**: Lines 121900-121919

```typescript
enum SubagentType {
  SUBAGENT_TYPE_UNSPECIFIED = 0;
  SUBAGENT_TYPE_DEEP_SEARCH = 1;
  SUBAGENT_TYPE_FIX_LINTS = 2;
  SUBAGENT_TYPE_TASK = 3;
  SUBAGENT_TYPE_SPEC = 4;
}
```

**Analysis**: Two type systems exist - one for local agent categorization (computer use, custom) and one for server-side workflow types (deep search, fix lints, task, spec).

### 4. CustomSubagent Definition

**Location**: Lines 119619-119700

```protobuf
message CustomSubagent {
  string full_path = 1;          // Path to subagent definition
  string name = 2;               // Display name
  string description = 3;        // Purpose description
  repeated string tools = 4;     // Available tools
  string model = 5;              // Model to use
  string prompt = 6;             // System prompt
  CustomSubagentPermissionMode permission_mode = 7;
}

enum CustomSubagentPermissionMode {
  CUSTOM_SUBAGENT_PERMISSION_MODE_UNSPECIFIED = 0;
  CUSTOM_SUBAGENT_PERMISSION_MODE_DEFAULT = 1;
  CUSTOM_SUBAGENT_PERMISSION_MODE_READONLY = 2;
}
```

**Key Insight**: Custom subagents are defined via markdown files in `.cursor/agents/` directory with frontmatter specifying name, description, model, and tools.

### 5. Background Subagent Lifecycle

**Location**: Lines 131850-132156, 557200-557550

#### Spawn Arguments
```protobuf
message BackgroundSubagentSpawnArgs {
  string subagent_id = 1;
  string prompt = 2;
  string tool_call_id = 3;      // Links to parent's tool call
  string subagent_type = 4;     // Type specification (string in this context)
  string description = 5;
  string model_id = 6;          // Model override
}
```

#### Lifecycle States
```typescript
enum BackgroundSubagentCompletionStatus {
  BACKGROUND_SUBAGENT_COMPLETION_STATUS_UNSPECIFIED = 0;
  BACKGROUND_SUBAGENT_COMPLETION_STATUS_COMPLETED = 1;
  BACKGROUND_SUBAGENT_COMPLETION_STATUS_FAILED = 2;
  BACKGROUND_SUBAGENT_COMPLETION_STATUS_ABORTED = 3;
}
```

#### Spawn Flow
1. **Initialization**: Create output file with description, timestamp, and prompt
2. **Status Tracking**: Write status file (RUNNING/COMPLETED/FAILED/ABORTED)
3. **Execution**: Run via `agentClientService.run()` with fresh `ConversationStateStructure`
4. **Transcript**: Append all interactions to transcript file
5. **Completion**: Fire completion event to parent composer

### 6. Parent-Child Agent Relationships

**Location**: Lines 297850-298925

#### Key Relationship Properties

```typescript
interface ComposerData {
  subagentInfo?: {
    parentComposerId: string;  // Link to parent
  };
  isBestOfNSubcomposer: boolean;
  subComposerIds: string[];     // Child subagent IDs
  selectedSubComposerId?: string;
}
```

#### Hierarchy Traversal
```typescript
// Get root composer (max depth: 10)
_getRootComposerIdRecursive(composerId, visitedSet, depth) {
  if (depth > 10) return composerId;  // Prevent infinite recursion
  if (visitedSet.has(composerId)) return composerId;  // Circular reference check

  const data = this.getComposerData(composerId);
  if (data?.subagentInfo?.parentComposerId) {
    return this._getRootComposerIdRecursive(
      data.subagentInfo.parentComposerId, visitedSet, depth + 1
    );
  }
  return composerId;
}
```

**Maximum Hierarchy Depth**: 10 levels (enforced to prevent runaway nesting)

### 7. State Sharing Between Agents

#### File Change Propagation
**Location**: Lines 557369-557382

```typescript
if (parentComposerId) {
  const fileChange = {
    ...change,
    metadata: {
      ...change.metadata,
      toolCallId: toolCallId,
      isBackgroundSubagent: true
    }
  };
  this.composerFileChangeHandlerService.handleFileChange(parentComposerId, fileChange);
}
```

**Key Insight**: File changes from subagents are propagated to parent composers with metadata marking them as subagent-originated. This enables inline diffs to be tracked in the parent's UI.

#### Approval Flow
Background subagents can request approvals through the parent:
```typescript
const approvalAccessor = f.createRemoteAccessor(async (request) => {
  const nestedHandle = this.getOrCreateNestedHandle(toolCallId);
  if (!nestedHandle) {
    return { approved: true };  // Auto-approve if no parent context
  }
  // Route approval through parent's approval service
  return await approvalService.handleApprovalRequest(nestedHandle, request);
});
```

### 8. BackgroundSubagentCompletionAction

**Location**: Lines 140011-140090, 246817-246880

```protobuf
message BackgroundSubagentCompletionAction {
  string parent_tool_call_id = 1;     // Links back to parent
  string subagent_id = 2;
  BackgroundSubagentCompletionStatus status = 3;
  string final_assistant_message = 4;
  bool final_assistant_message_truncated = 5;
  string transcript_path = 6;          // File path to full transcript
  string status_path = 7;              // File path to status file
  RequestContext request_context = 8;
}
```

**Purpose**: When a background subagent completes, this action is added to the parent's conversation to record the result.

### 9. SubagentInfo and SubagentReturnCall

**Location**: Lines 127831-127895

```protobuf
message SubagentInfo {
  SubagentType subagent_type = 1;
  string subagent_id = 2;
  oneof params {
    DeepSearchParams deep_search_params = 3;
    FixLintsParams fix_lints_params = 4;
    TaskParams task_params = 5;
    SpecParams spec_params = 6;
  }
}

message SubagentReturnCall {
  SubagentType subagent_type = 1;
  oneof return_value {
    DeepSearchReturnValue deep_search_return_value = 2;
    FixLintsReturnValue fix_lints_return_value = 3;
    TaskReturnValue task_return_value = 4;
    SpecReturnValue spec_return_value = 5;
  }
}
```

**Analysis**: Different subagent types have specialized parameter and return types, allowing type-safe communication between parent and child agents.

### 10. TaskArgs for Subagent Invocation

**Location**: Lines 139110-139160

```protobuf
message TaskArgs {
  string description = 1;        // Human-readable task description
  string prompt = 2;             // Actual prompt for subagent
  SubagentType subagent_type = 3;
  string model = 4;              // Optional model override
  string resume = 5;             // Resume ID for continuing tasks
}
```

**Task Results**:
```protobuf
message TaskResult {
  oneof result {
    CompletedTaskResult completed_task_result = 1;
    AsyncTaskResult async_task_result = 2;
  }
}

message CompletedTaskResult {
  string summary = 1;
  repeated FileResult file_results = 2;
  bool user_aborted = 3;
  bool subagent_errored = 4;
}

message AsyncTaskResult {
  string task_id = 1;
  bool user_aborted = 2;
  bool subagent_errored = 3;
}
```

## Architecture Summary

```
ConversationStateStructure (Parent)
├── turns[]
├── todos[]
├── fileStates{}
├── summary
└── subagentStates{} ──────────────────┐
    │                                   │
    ├── "subagent-1" ───────────────────┼───> SubagentPersistedState
    │   ├── conversation_state ─────────┼───> ConversationStateStructure
    │   │   ├── turns[]                 │     (Complete nested state)
    │   │   ├── todos[]                 │
    │   │   └── subagentStates{} ───────┼───> (Recursive nesting possible)
    │   ├── created_timestamp_ms        │
    │   ├── last_used_timestamp_ms      │
    │   └── subagent_type               │
    │                                   │
    └── "subagent-2" ───────────────────┴───> SubagentPersistedState
        └── ...
```

## Implementation Details

### Subagent File Storage
- Transcripts: Written to workspace-specific paths
- Status files: Track current state (RUNNING/COMPLETED/FAILED/ABORTED)
- Output files: Structured log of subagent activity

### Running Subagent Management
```typescript
private runningSubagents = new Map<string, {
  subagentId: string;
  transcriptDisplayPath: string;
  statusDisplayPath: string;
  abortRequested: boolean;
  abortController: AbortController;
  state: "RUNNING" | "COMPLETED" | "FAILED" | "ABORTED";
  startTime: Date;
}>();
```

## Security Considerations

1. **Permission Modes**: Custom subagents can be restricted to readonly mode
2. **Max Depth**: 10-level hierarchy limit prevents stack overflow
3. **Circular Reference Detection**: Tracked via visited set
4. **Abort Propagation**: Parent can abort child subagents

## Related Files

- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
  - Lines 119480-119620: SubagentType definitions
  - Lines 131850-132160: Background subagent exec protobuf
  - Lines 139095-139200: TaskArgs and completion status
  - Lines 140011-140090: BackgroundSubagentCompletionAction
  - Lines 141045-141160: ConversationStateStructure
  - Lines 247730-247925: Duplicated protobuf definitions
  - Lines 557200-557550: BackgroundSubagentManager implementation

## Open Questions

1. How are subagent states garbage collected when the parent conversation ends?
2. What triggers the transition from running state to persisted state?
3. How do subagent states interact with the speculative summarization feature?
4. Is there a limit on the number of subagents that can be spawned?

## Conclusion

Cursor's subagent architecture enables sophisticated nested agent workflows through:
- Recursive conversation state nesting
- Clear parent-child relationship tracking
- File change propagation to parent
- Multiple subagent types (computer use, custom, task-based)
- Background execution with transcript logging
- Robust lifecycle management with abort capability

The design supports both synchronous (inline) and asynchronous (background) subagent execution patterns, with complete state isolation between parent and child conversations while maintaining the ability to propagate relevant changes upward.
