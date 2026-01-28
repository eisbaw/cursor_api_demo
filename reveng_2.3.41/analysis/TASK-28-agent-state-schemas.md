# TASK-28: CloudAgentState and InteractionUpdate Message Schemas

## Overview

This document analyzes the protobuf message schemas used for cloud agent state management and interaction updates in Cursor's background composer/agent system.

## 1. CloudAgentState Schema

**Protobuf Type:** `aiserver.v1.CloudAgentState`

**Location:** Line 342745 (beautified/workbench.desktop.main.js)

### Fields

| Field # | Name | Type | Description |
|---------|------|------|-------------|
| 1 | `conversation_state` | message (Fqe) | Current conversation state |
| 2 | `num_prior_interaction_updates` | uint32 | Count of previous interaction updates |
| 3 | `pr_body` | bytes | Pull request body content |
| 4 | `summary` | bytes | Agent summary |
| 5 | `branch_name` | bytes | Git branch name |
| 6 | `pr_url` | bytes | Pull request URL |
| 7 | `last_interaction_update_offset_key` | string | Offset key for resuming streams |
| 8 | `agent_name` | bytes | Display name for the agent |
| 9 | `starting_commit` | string (optional) | Starting git commit hash |
| 10 | `base_branch` | string (optional) | Base branch for comparison |
| 11 | `config` | bytes | Agent configuration blob |
| 12 | `local_state_branch` | string (optional) | Local state branch reference |
| 13 | `original_prompt_blob_id` | bytes | Blob ID for original prompt |
| 14 | `repository_info_blob_id` | bytes | Blob ID for repository info |
| 15 | `original_conversation_action_blob_id` | bytes | Blob ID for original action |
| 16 | `video_annotations_blob_id` | bytes | Blob ID for video annotations |
| 17 | `last_user_turn_commit` | string (optional) | Commit hash at last user turn |
| 18 | `last_followup_source` | enum (BackgroundComposerSource) | Source of last followup |
| 19 | `continue_rebase` | bool (optional) | Whether to continue a rebase |
| 20 | `turn_start_todo_ids` | repeated string | Todo IDs at turn start |
| 21+ | Additional fields include: `originalRequestStartUnixMs`, `initialTurnLatencyReported`, `agentSessionId`, `kickoffMessageId`, `grindModeConfig`, `commits`, `commitCount`, `userFacingErrorDetails`, `initialSource`, `numCompletedTurns` |

### CloudAgentStatePersistedMetadata

**Protobuf Type:** `aiserver.v1.CloudAgentStatePersistedMetadata`

Metadata wrapper for persisted state:

| Field | Type | Description |
|-------|------|-------------|
| `cloudAgentStateBlobId` | bytes | Blob ID reference |
| `offsetKey` | string | Stream offset key |
| `timestampMs` | int64 | Timestamp in milliseconds |
| `workflowStatus` | enum | Current workflow status |
| `version` | enum | Persisted metadata version |

**Version Enum:**
- `PERSISTED_METADATA_VERSION_UNSPECIFIED` = 0
- `PERSISTED_METADATA_VERSION_1` = 1

---

## 2. InteractionUpdate Schema

**Protobuf Type:** `agent.v1.InteractionUpdate`

**Location:** Line 248696 (beautified/workbench.desktop.main.js)

### Message Union (oneof "message")

| Field # | Name | Type | Description |
|---------|------|------|-------------|
| 1 | `text_delta` | TextDeltaUpdate | Incremental text content |
| 7 | `partial_tool_call` | PartialToolCallUpdate | Streaming tool call with args |
| 15 | `tool_call_delta` | ToolCallDeltaUpdate | Delta updates for tool calls |
| 2 | `tool_call_started` | ToolCallStartedUpdate | Tool call initiation |
| 3 | `tool_call_completed` | ToolCallCompletedUpdate | Tool call completion |
| 4 | `thinking_delta` | ThinkingDeltaUpdate | Thinking/reasoning content |
| 5 | `thinking_completed` | ThinkingCompletedUpdate | Thinking phase complete |
| 6 | `user_message_appended` | UserMessageAppendedUpdate | User message added |
| 8 | `token_delta` | TokenDeltaUpdate | Token count update |
| 9 | `summary` | SummaryUpdate | Conversation summary |
| 10 | `summary_started` | SummaryStartedUpdate | Summary generation started |
| 11 | `summary_completed` | SummaryCompletedUpdate | Summary generation complete |
| 12 | `shell_output_delta` | ShellOutputDeltaUpdate | Shell command output |
| 13 | `heartbeat` | HeartbeatUpdate | Keep-alive signal |
| 14 | `turn_ended` | TurnEndedUpdate | Agent turn completion |
| 16 | `step_started` | StepStartedUpdate | Step execution started |
| 17 | `step_completed` | StepCompletedUpdate | Step execution complete |

### Update Message Types Detail

#### TextDeltaUpdate
```
Field 1: text (string) - Incremental text content
```

#### ToolCallStartedUpdate
```
Field 1: call_id (string) - Unique call identifier
Field 2: tool_call (message) - Tool call details
Field 3: model_call_id (string) - Model call reference
```

#### ToolCallCompletedUpdate
```
Field 1: call_id (string) - Unique call identifier
Field 2: tool_call (message) - Completed tool call
Field 3: model_call_id (string) - Model call reference
```

#### ToolCallDeltaUpdate
```
Field 1: call_id (string) - Call identifier
Field 2: tool_call_delta (message) - Delta changes
Field 3: model_call_id (string) - Model call reference
```

#### PartialToolCallUpdate
```
Field 1: call_id (string) - Call identifier
Field 2: tool_call (message) - Partial tool call
Field 3: args_text_delta (string) - Incremental argument text
Field 4: model_call_id (string) - Model call reference
```

#### ThinkingDeltaUpdate
```
Field 1: text (string) - Incremental thinking content
```

#### ThinkingCompletedUpdate
```
Field 1: thinking_duration_ms (int32) - Duration of thinking phase
```

#### TokenDeltaUpdate
```
Field 1: tokens (int32) - Token count increment
```

#### StepStartedUpdate
```
Field 1: step_id (uint64) - Step identifier
```

#### StepCompletedUpdate
```
Field 1: step_id (uint64) - Step identifier
Field 2: step_duration_ms (int64) - Step duration in ms
```

#### ShellOutputDeltaUpdate (oneof "event")
```
Field 1: stdout (message) - Standard output
Field 2: stderr (message) - Standard error
Field 3: exit (message) - Exit code
Field 4: start (message) - Process started
```

---

## 3. Workflow Status State Machine

**Protobuf Type:** `aiserver.v1.CloudAgentWorkflowStatus`

### States

| Value | Proto Name | Description |
|-------|------------|-------------|
| 0 | `CLOUD_AGENT_WORKFLOW_STATUS_UNSPECIFIED` | Initial/unknown state |
| 1 | `CLOUD_AGENT_WORKFLOW_STATUS_RUNNING` | Agent is actively processing |
| 2 | `CLOUD_AGENT_WORKFLOW_STATUS_IDLE` | Agent is waiting/completed turn |
| 3 | `CLOUD_AGENT_WORKFLOW_STATUS_ERROR` | Agent encountered an error |
| 4 | `CLOUD_AGENT_WORKFLOW_STATUS_ARCHIVED` | Agent session archived |
| 5 | `CLOUD_AGENT_WORKFLOW_STATUS_EXPIRED` | Agent session expired |

### State Transitions

```
                    +---------------+
                    |  UNSPECIFIED  |
                    +-------+-------+
                            |
                            v
                    +-------+-------+
         +--------->|    RUNNING    |<---------+
         |          +-------+-------+          |
         |                  |                  |
         |      +-----------+-----------+      |
         |      |           |           |      |
         |      v           v           v      |
    +----+----+ +-----+-----+ +--------+-------+
    |  ERROR  | |   IDLE    | |    ARCHIVED    |
    +---------+ +-----+-----+ +----------------+
                      |
                      | (timeout)
                      v
              +-------+-------+
              |    EXPIRED    |
              +---------------+
```

### Mapping to BackgroundComposerStatus

The client maps CloudAgentWorkflowStatus to local BackgroundComposerStatus:

| WorkflowStatus | BackgroundComposerStatus |
|----------------|--------------------------|
| RUNNING | RUNNING |
| IDLE | FINISHED |
| ERROR | ERROR |
| ARCHIVED | FINISHED |
| EXPIRED | EXPIRED |
| UNSPECIFIED | UNSPECIFIED |

---

## 4. StreamConversationResponse

**Protobuf Type:** `aiserver.v1.StreamConversationResponse`

The main streaming response wrapper for cloud agent communications.

### Message Union (oneof "message")

| Field # | Name | Type | Description |
|---------|------|------|-------------|
| 3 | `initial_state` | InitialState | Initial state snapshot |
| 4 | `interaction_update_with_offset` | InteractionUpdateWithOffset | Interaction update with offset |
| 5 | `cloud_agent_state_with_id_and_offset` | CloudAgentStateWithIdAndOffset | State update with blob ID |
| 6 | `workflow_status_with_offset` | WorkflowStatusWithOffset | Status change notification |
| 7 | `prefetched_blobs` | PrefetchedBlobs | Pre-loaded blob data |

### InitialState

Contains:
- `blob_id` (bytes) - State blob identifier
- `cloud_agent_state` (CloudAgentState) - Full state snapshot
- `pre_fetched_blobs` (repeated) - Pre-loaded blobs
- `workflow_status` (enum) - Current workflow status

### InteractionUpdateWithOffset

Contains:
- `offset_key` (string) - Stream position for resumption
- `interaction_update` (InteractionUpdate) - The actual update

---

## 5. UI Update Flow

### Update Pipeline

1. **Server** sends `StreamConversationResponse` messages via gRPC stream
2. **BackgroundComposerService** receives and dispatches messages:
   - `initialState` -> Initializes composer state
   - `interactionUpdateWithOffset` -> Queued for processing
   - `cloudAgentStateWithIdAndOffset` -> Persists to storage
   - `workflowStatusWithOffset` -> Updates status

3. **ComposerAgentService.handleCloudAgentInteractionUpdates()** processes updates:
   - Creates `AgentResponseAdapter` for handling
   - Routes updates to `sendUpdate()` method

4. **AgentResponseAdapter.sendUpdate()** handles each update type:
   - `text-delta` -> `handleTextDelta()` appends to current bubble
   - `thinking-delta` -> `handleThinkingDelta()` updates thinking UI
   - `tool-call-started` -> Creates tool call bubble
   - `tool-call-completed` -> Updates tool call with result
   - `turn-ended` -> Marks conversation as completed

5. **ComposerDataService** methods update React state:
   - `appendComposerBubbles()` - Adds new conversation bubbles
   - `updateComposerBubble()` - Modifies existing bubbles
   - `updateComposerDataSetStore()` - Batch state updates

### Event Emission

- `fireDidBcStatusChange()` - Notifies UI of background composer status changes
- Status changes trigger re-renders through reactive state management

---

## 6. Background Composer Sources

**Enum:** `aiserver.v1.BackgroundComposerSource`

Tracks where agent interactions originate:

| Value | Name | Description |
|-------|------|-------------|
| 0 | UNSPECIFIED | Unknown source |
| 1 | EDITOR | Cursor editor |
| 2 | SLACK | Slack integration |
| 3 | WEBSITE | Web interface |
| 4 | LINEAR | Linear integration |
| 5 | IOS_APP | iOS mobile app |
| 6 | API | Direct API calls |
| 7 | GITHUB | GitHub integration |
| 8 | CLI | Command line |
| 9 | GITHUB_CI_AUTOFIX | GitHub CI autofix |
| 10 | GITLAB | GitLab integration |
| 11 | ENVIRONMENT_SETUP_WEB | Environment setup web |
| 12 | GRIND_WEB | Grind mode web interface |

---

## 7. Parallel Agent Workflow

For multi-agent coordination, there's a separate status system:

**Enum:** `aiserver.v1.ParallelAgentWorkflowStatusUpdate.Phase`

| Value | Name |
|-------|------|
| 0 | UNSPECIFIED |
| 1 | STARTING |
| 2 | CHILDREN_RUNNING |
| 3 | GATHERING |
| 4 | SYNTHESIZING |
| 5 | COMPLETED |
| 6 | ERROR |

---

## Key Insights

1. **Offset-based Resumption**: The system uses offset keys to enable stream resumption after disconnection

2. **Blob Storage**: Large content (prompts, configs, video annotations) stored as blobs with ID references

3. **Dual Status Systems**: Separate workflow status (cloud) and composer status (client) with mapping layer

4. **Reactive UI Updates**: State changes flow through a reactive store (likely SolidJS signals based on `setData` patterns)

5. **Step Tracking**: Agent work organized into discrete steps with IDs and duration tracking

6. **Stall Detection**: Client monitors for stream stalls with configurable thresholds
