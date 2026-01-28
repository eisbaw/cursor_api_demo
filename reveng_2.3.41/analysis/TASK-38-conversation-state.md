# TASK-38: ConversationState Protobuf Structure Analysis

## Overview

The ConversationState system in Cursor consists of two related protobuf message types:

1. **ConversationState** (`agent.v1.ConversationState`) - Used for legacy/non-NAL conversations
2. **ConversationStateStructure** (`agent.v1.ConversationStateStructure`) - Used for NAL (New Agent Layer) conversations with blob-based storage

The `Fqe` identifier in the beautified code refers to `ConversationStateStructure`, which is the newer, more comprehensive format.

## Message Definitions

### ConversationState (agent.v1.ConversationState)

**Location**: Line 247654 / Line 140921
**Class identifier**: `Ufl` / `_dh` (minified names vary)

```protobuf
message ConversationState {
  repeated string root_prompt_messages_json = 1;  // T=9 (string)
  repeated ConversationTurn turns = 8;            // message type Q9l
  repeated TodoItem todos = 3;                    // message type Lqe
  repeated string pending_tool_calls = 4;         // T=9 (string)
  optional ConversationTokenDetails token_details = 5;  // message type t9r
  optional ConversationSummary summary = 6;       // message type e9r
  optional ConversationPlan plan = 7;             // message type Z3r
  optional ConversationSummaryArchive summary_archive = 9;  // message type sUt
  map<string, FileState> file_states = 10;        // K=9 (string key), V=message nUl
  repeated ConversationSummaryArchive summary_archives = 11;  // message type sUt
}
```

### ConversationStateStructure (agent.v1.ConversationStateStructure) - "Fqe"

**Location**: Line 247796 / Line 141053
**Class identifier**: `Fqe` / `U1` (minified names vary)

```protobuf
message ConversationStateStructure {
  repeated bytes turns_old = 2;           // T=12 (bytes) - deprecated
  repeated bytes root_prompt_messages_json = 1;  // T=12 (bytes)
  repeated bytes turns = 8;               // T=12 (bytes) - serialized turn data
  repeated bytes todos = 3;               // T=12 (bytes) - serialized todos
  repeated string pending_tool_calls = 4; // T=9 (string)
  optional ConversationTokenDetails token_details = 5;  // message type
  optional bytes summary = 6;             // T=12 (bytes)
  optional bytes plan = 7;                // T=12 (bytes)
  repeated string previous_workspace_uris = 9;  // T=9 (string)
  optional AgentMode mode = 10;           // enum iUt
  optional bytes summary_archive = 11;    // T=12 (bytes)
  map<string, bytes> file_states = 12;    // K=9, V=12 (string->bytes)
  map<string, FileStateStructure> file_states_v2 = 15;  // K=9, V=message sUl
  repeated bytes summary_archives = 13;   // T=12 (bytes)
  repeated StepTiming turn_timings = 14;  // message type rUl
  map<string, SubagentPersistedState> subagent_states = 16;  // K=9, V=message oUl
  uint32 self_summary_count = 17;         // T=13 (uint32)
  repeated string read_paths = 18;        // T=9 (string)
}
```

## Key Differences Between Versions

| Feature | ConversationState | ConversationStateStructure |
|---------|-------------------|----------------------------|
| Field storage | Direct messages | Bytes (blob references) |
| Turns | ConversationTurn messages | Serialized bytes |
| File states | FileState map | FileStateStructure map + legacy bytes |
| Workspace tracking | None | previous_workspace_uris |
| Agent mode | None | AgentMode enum |
| Turn timing | None | StepTiming array |
| Subagent support | None | subagent_states map |
| Summary counting | None | self_summary_count |
| Read path tracking | None | read_paths array |

## Dependent Message Types

### ConversationTurn (agent.v1.ConversationTurn)
**Field number**: 8 in ConversationState

```protobuf
message ConversationTurn {
  oneof turn {
    AgentConversationTurn agent_conversation_turn = 1;
    ShellConversationTurn shell_conversation_turn = 2;
  }
}
```

### AgentConversationTurn (agent.v1.AgentConversationTurn)

```protobuf
message AgentConversationTurn {
  optional UserMessage user_message = 1;
  repeated ConversationStep steps = 2;
  optional string request_id = 3;
}
```

### ShellConversationTurn (agent.v1.ShellConversationTurn)

```protobuf
message ShellConversationTurn {
  optional ShellCommand shell_command = 1;
  optional ShellOutput shell_output = 2;
}
```

### ConversationStep (agent.v1.ConversationStep)

```protobuf
message ConversationStep {
  oneof message {
    AssistantMessage assistant_message = 1;
    ToolCall tool_call = 2;
    ThinkingMessage thinking_message = 3;
  }
}
```

### UserMessage (agent.v1.UserMessage)

```protobuf
message UserMessage {
  string text = 1;
  string message_id = 2;
  optional SelectedContext selected_context = 3;
  AgentMode mode = 4;
  optional bool is_simulated_msg = 5;
  optional string best_of_n_group_id = 6;
  optional bool try_use_best_of_n_promotion = 7;
  optional string rich_text = 8;
}
```

### TodoItem (agent.v1.TodoItem)

```protobuf
message TodoItem {
  string id = 1;
  string content = 2;
  TodoStatus status = 3;
  int64 created_at = 4;
  int64 updated_at = 5;
  repeated string dependencies = 6;
}
```

### ConversationTokenDetails (agent.v1.ConversationTokenDetails)

```protobuf
message ConversationTokenDetails {
  uint32 used_tokens = 1;
  uint32 max_tokens = 2;
}
```

### ConversationSummary (agent.v1.ConversationSummary)

```protobuf
message ConversationSummary {
  string summary = 1;
}
```

### ConversationSummaryArchive (agent.v1.ConversationSummaryArchive)

```protobuf
message ConversationSummaryArchive {
  repeated bytes summarized_messages = 1;
  string summary = 2;
  uint32 window_tail = 3;
  bytes summary_message = 4;
}
```

### ConversationPlan (agent.v1.ConversationPlan)

```protobuf
message ConversationPlan {
  string plan = 1;
}
```

### FileState (agent.v1.FileState)

```protobuf
message FileState {
  optional string content = 1;
  optional string initial_content = 2;
}
```

### FileStateStructure (agent.v1.FileStateStructure)

```protobuf
message FileStateStructure {
  optional bytes content = 1;
  optional bytes initial_content = 2;
}
```

### StepTiming (agent.v1.StepTiming)

```protobuf
message StepTiming {
  uint64 duration_ms = 1;
  uint64 timestamp_ms = 2;
}
```

### SubagentPersistedState (agent.v1.SubagentPersistedState)

```protobuf
message SubagentPersistedState {
  optional ConversationStateStructure conversation_state = 1;  // Recursive reference to Fqe
  uint64 created_timestamp_ms = 2;
  uint64 last_used_timestamp_ms = 3;
  optional SubagentType subagent_type = 4;
}
```

## Enums

### AgentMode (agent.v1.AgentMode)

```protobuf
enum AgentMode {
  AGENT_MODE_UNSPECIFIED = 0;
  AGENT_MODE_AGENT = 1;
  AGENT_MODE_ASK = 2;
  AGENT_MODE_PLAN = 3;
  AGENT_MODE_DEBUG = 4;
  AGENT_MODE_TRIAGE = 5;
}
```

### TodoStatus (agent.v1.TodoStatus)

```protobuf
enum TodoStatus {
  TODO_STATUS_UNSPECIFIED = 0;
  TODO_STATUS_PENDING = 1;
  TODO_STATUS_IN_PROGRESS = 2;
  TODO_STATUS_COMPLETED = 3;
  TODO_STATUS_CANCELLED = 4;
}
```

### SubagentType (agent.v1.SubagentType)

```protobuf
message SubagentType {
  oneof type {
    UnspecifiedSubagent unspecified = 1;
    ComputerUseSubagent computer_use = 2;
    CustomSubagent custom = 3;
  }
}
```

## API Messages (aiserver.v1)

### GetLatestAgentConversationStateRequest

```protobuf
message GetLatestAgentConversationStateRequest {
  string bc_id = 1;  // Background Composer ID
}
```

### LatestAgentConversationState

```protobuf
message LatestAgentConversationState {
  optional ConversationStateStructure conversation_state = 1;  // Uses Fqe/U1
  uint32 num_prior_interaction_updates = 2;
}
```

### GetLatestAgentConversationStateResponse

```protobuf
message GetLatestAgentConversationStateResponse {
  optional LatestAgentConversationState latest_conversation_state = 1;
  repeated PreFetchedBlob pre_fetched_blobs = 2;
}
```

## Code Usage Patterns

### Initialization
```javascript
// New conversation with default state
conversationState: new U1  // ConversationStateStructure

// Access file states (NAL mode)
const fileStates = conversationState.fileStatesV2;
Object.keys(fileStates).length  // count of modified files

// Check turn count
conversationState.turns.length
```

### Serialization
```javascript
// To binary
const binary = conversationState.toBinary();
const base64 = xU(binary);  // base64 encode

// From binary
const state = U1.fromBinary(data);

// From JSON
const state = U1.fromJson(jsonData);
```

### Cloud Transfer
```javascript
// Get state for cloud sync
const state = await agentCompatService.getConversationStateForCloudTransfer(composerId);
// Returns { conversationStateStructure, ... }
```

## File Reference in Code

| Minified Name | Type Name |
|---------------|-----------|
| `Ufl` | ConversationState |
| `U1` | ConversationStateStructure |
| `Fqe` | ConversationStateStructure (alternate) |
| `Q9l` | ConversationTurn |
| `Lqe` | TodoItem |
| `t9r` | ConversationTokenDetails |
| `e9r` | ConversationSummary |
| `Z3r` | ConversationPlan |
| `sUt` | ConversationSummaryArchive |
| `nUl` | FileState |
| `sUl` | FileStateStructure |
| `rUl` | StepTiming |
| `oUl` | SubagentPersistedState |
| `Z9l` | AgentConversationTurn |
| `tUl` | ShellConversationTurn |
| `v2e` | UserMessage |
| `nUt` | ConversationStep |
| `iUt` | AgentMode (enum) |
| `W9t` | TodoStatus (enum) |
| `Nhs` | SubagentType |

## Key Observations

1. **Dual Format System**: Cursor maintains two conversation state formats - the older `ConversationState` with direct message embedding and the newer `ConversationStateStructure` (Fqe) with blob-based storage for efficiency.

2. **NAL Mode Detection**: The `isNAL` flag determines which format is used. NAL mode uses `ConversationStateStructure` with blob references.

3. **Subagent Architecture**: The state structure supports nested subagent states, each with their own `ConversationStateStructure`, enabling hierarchical agent workflows.

4. **Mode Tracking**: Agent mode (Agent, Ask, Plan, Debug, Triage) is tracked in the state structure, allowing for different behavior modes within a single conversation.

5. **File State Versioning**: Two file state systems exist - the legacy `file_states` map and the newer `file_states_v2` with structured content.

6. **Summary Management**: Multiple summary archives are supported for long conversations, with window-based summarization to manage context length.

## CloudAgentState Wrapper (aiserver.v1.CloudAgentState)

The `ConversationStateStructure` (Fqe) is typically wrapped in a `CloudAgentState` message for cloud-based background agent conversations.

**Location**: Line 342710
**Class identifier**: `xbs`

```protobuf
message CloudAgentState {
  optional ConversationStateStructure conversation_state = 1;  // The Fqe message
  uint32 num_prior_interaction_updates = 2;
  bytes pr_body = 3;              // PR body content blob
  bytes summary = 4;              // Summary content blob
  bytes branch_name = 5;          // Git branch name blob
  bytes pr_url = 6;               // PR URL blob
  bytes agent_name = 8;           // Agent name blob
  string last_interaction_update_offset_key = 7;  // Stream resumption key
  optional string starting_commit = 9;
  optional string base_branch = 10;
  bytes config = 11;              // Configuration blob
  optional string local_state_branch = 12;
  bytes original_prompt_blob_id = 13;
  bytes repository_info_blob_id = 14;
  bytes original_conversation_action_blob_id = 15;
  bytes video_annotations_blob_id = 16;
  optional string last_user_turn_commit = 17;
  optional string last_followup_source = 18;
  optional bool continue_rebase = 19;
  repeated string turn_start_todo_ids = 20;
  optional int64 original_request_start_unix_ms = 21;
  optional bool initial_turn_latency_reported = 22;
  optional string agent_session_id = 23;
  optional string kickoff_message_id = 24;
  optional GrindModeConfig grind_mode_config = 25;
  repeated string commits = 26;
  optional uint32 commit_count = 27;
  optional string user_facing_error_details = 28;
  optional string initial_source = 29;
  uint32 num_completed_turns = 30;
}
```

## CloudAgentStorage Service Architecture

The `CloudAgentStorageService` (`out-build/vs/workbench/services/agent/browser/cloudAgentStorageService.js`) handles state persistence.

**Location**: Line 343147
**Service identifier**: `TWt` (cloudAgentStorageService)

### Key Components

```javascript
class CloudAgentStorageService {
  // Blob stores per composer
  composerBlobStores: Map<string, ComposerBlobStore>;

  // State caches by background composer ID
  stateCachesByBcId: Map<string, StateCache>;

  // Metadata storage
  metadataProperties: Map<string, Property>;
  cloudAgentStateProperties: Map<string, Property>;

  // Write queues for async blob persistence
  blobWriteQueuesByComposerId: Map<string, WriteQueue>;
}
```

### Storage Key Format

```javascript
// Storage key pattern: "{bcId}:{property}"
function sdc(bcId, property) {
  return `${bcId}:${property}`;
}

// Metadata key constant
const METADATA_KEY = "cloudAgent:metadata";
```

### State Persistence Flow

1. **Save State**:
```javascript
async saveNewCloudAgentState(e) {
  const { bcId, composerId, blobId, state, offsetKey } = e;
  const blobStore = getComposerBlobStore(bcId, composerId);
  const binary = state.toBinary();  // Serialize CloudAgentState
  await blobStore.setBlob(traceId, blobId, binary);
  await updateMetadata(bcId, { cloudAgentStateBlobId: blobId, offsetKey });
}
```

2. **Load State**:
```javascript
async getCloudAgentStateFromDiskOrCache(e, blobId) {
  // Check cache first
  const cached = stateCache.getState(blobIdHex);
  if (cached) return cached;

  // Load from blob store
  const blobData = await getBlob({ bcId, composerId, blobId });
  const state = xbs.fromBinary(blobData);  // CloudAgentState.fromBinary
  stateCache.setState(blobIdHex, state);
  return state;
}
```

3. **Get Conversation State with Last Interaction**:
```javascript
async getConversationStateWithLastInteraction(e) {
  const state = await getCloudAgentState({ bcId, composerId });
  return {
    value: {
      conversationState: state.value.conversationState,  // Fqe
      lastInteractionUpdateOffsetKey: state.value.lastInteractionUpdateOffsetKey
    },
    metadata: state.metadata
  };
}
```

### Metadata Versioning

```javascript
const METADATA_VERSION = 1;  // Ibs constant

// Metadata is stored with version for migration support
const metadata = new WGr({
  cloudAgentStateBlobId: blobId,
  offsetKey: key,
  workflowStatus: status,
  version: METADATA_VERSION,
  timestampMs: Date.now()
});
```

## Checkpoint Handler System

**Location**: Line 940159

The `CheckpointHandler` manages conversation state checkpoints during agent execution:

```javascript
class CheckpointHandler {
  blobStore;
  conversationId;
  priorConversationState;  // ConversationStateStructure (Fqe)
  onCheckpoint;
  transcriptWriter;
  onTranscriptWritten;

  handleCheckpoint = async (transcript, state) => {
    this.onCheckpoint?.(state);
    this.priorConversationState = state;
    this.transcriptWriter?.(transcript, state).then(() => {
      this.onTranscriptWritten?.(this.conversationId);
    });
  };

  getLatestCheckpoint = () => this.priorConversationState;
}
```

### Cloud Transfer for Background Agents

```javascript
// AgentCompatService.getConversationStateForCloudTransfer
async getConversationStateForCloudTransfer(composerId) {
  const checkpointHandler = this._activeCheckpointHandlers.get(composerId);
  let state = checkpointHandler?.getLatestCheckpoint();

  // Returns { conversationStateStructure, blobs } for cloud sync
  return {
    conversationStateStructure: state,
    blobs: [...extractBlobs(state)]
  };
}
```

## gRPC Service Definition

**Location**: Line 815724

```protobuf
service AgentService {
  // Unary call to get latest state
  rpc GetLatestAgentConversationState(GetLatestAgentConversationStateRequest)
      returns (GetLatestAgentConversationStateResponse);
}

// Service registration in code
{
  name: "GetLatestAgentConversationState",
  I: n2c,  // GetLatestAgentConversationStateRequest
  O: r2c,  // GetLatestAgentConversationStateResponse
  kind: Kt.Unary
}
```

## ConversationAction Message

**Location**: Line 139794

Defines actions that can be performed on a conversation:

```protobuf
message ConversationAction {
  oneof action {
    UserMessageAction user_message_action = 1;
    ResumeAction resume_action = 2;
    CancelAction cancel_action = 3;
    SummarizeAction summarize_action = 4;
    ShellCommandAction shell_command_action = 5;
    StartPlanAction start_plan_action = 6;
    ExecutePlanAction execute_plan_action = 7;
    AsyncAskQuestionCompletionAction async_ask_question_completion_action = 8;
    BackgroundSubagentCompletionAction background_subagent_completion_action = 9;
  }
}
```

## Workflow Status Enum

The conversation state is associated with a workflow status for background composers:

```javascript
// WorkflowStatus values from metadata
const workflowStatus = {
  ARCHIVED: "archived",
  ERROR: "error",
  EXPIRED: "expired",
  RUNNING: "running",
  // ... other statuses
};
```

## Mock Driver Implementation

**Location**: Line 858151

For testing, a mock handler is provided:

```javascript
async handleGetLatestAgentConversationState(request) {
  console.log(`[driver] handleGetLatestAgentConversationState called for bcId: ${request.bcId}`);
  return {
    state: undefined,
    preFetchedBlobs: []
  };
}
```

## Related Tasks for Further Investigation

- Analyze blob storage and retrieval mechanism for ConversationStateStructure
- Investigate checkpoint system for conversation state persistence
- Document the relationship between ConversationState and the BidiStream protocol
- Analyze SubagentPersistedState and nested agent conversation management
- Investigate GrindModeConfig and its relationship to conversation state
- Document transcript writer and conversation logging system
