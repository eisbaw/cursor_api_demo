# TASK-4: BackgroundComposerService Analysis

Analysis of `aiserver.v1.BackgroundComposerService` for async agent tasks.

## Service Overview

The BackgroundComposerService (`aiserver.v1.BackgroundComposerService`) manages asynchronous AI agent tasks that run in the cloud. It provides methods for:
- Starting background agents from snapshots
- Sending follow-up messages to running agents
- Streaming conversation updates back to the UI
- Managing agent lifecycle (pause, resume, archive)

**Source location**: Line 815697 in `workbench.desktop.main.js`

## Core gRPC Methods

### Task Management
| Method | Type | Purpose |
|--------|------|---------|
| `ListBackgroundComposers` | Unary | List all background composer instances |
| `StartBackgroundComposerFromSnapshot` | Unary | Start a new background agent from a snapshot |
| `PauseBackgroundComposer` | Unary | Pause a running agent |
| `ResumeBackgroundComposer` | Unary | Resume a paused agent |
| `ArchiveBackgroundComposer` | Unary | Archive/terminate an agent |
| `GetBackgroundComposerStatus` | Unary | Get current status of an agent |
| `GetBackgroundComposerInfo` | Unary | Get detailed info about an agent |

### Streaming & Communication
| Method | Type | Purpose |
|--------|------|---------|
| `AttachBackgroundComposer` | ServerStreaming | Attach to a running agent's stream |
| `StreamConversation` | ServerStreaming | Stream conversation updates (recommended) |
| `StreamInteractionUpdates` | ServerStreaming | Stream raw interaction updates |
| `StreamInteractionUpdatesSSE` | ServerStreaming | SSE variant for interaction updates |
| `AddAsyncFollowupBackgroundComposer` | Unary | Send a follow-up message to an agent |

### Parallel Workflows
| Method | Type | Purpose |
|--------|------|---------|
| `StartParallelAgentWorkflow` | Unary | Start multiple agents in parallel |
| `StreamParallelAgentWorkflowStatus` | ServerStreaming | Monitor parallel workflow status |

### PR/Git Operations
| Method | Type | Purpose |
|--------|------|---------|
| `MakePRBackgroundComposer` | Unary | Create a PR from agent changes |
| `OpenPRBackgroundComposer` | Unary | Open an existing PR |
| `GetBackgroundComposerPullRequest` | Unary | Get PR details |
| `CommitBackgroundComposer` | Unary | Commit changes made by agent |

## Key Message Types

### AddAsyncFollowupBackgroundComposerRequest (Line 339841)

Used to send follow-up messages to a running background agent.

```protobuf
message AddAsyncFollowupBackgroundComposerRequest {
  string bc_id = 1;                              // Background composer ID
  string followup = 2;                           // Plain text follow-up message
  bool synchronous = 3;                          // Wait for response before returning
  string rich_followup = 4;                      // Rich text version
  ConversationMessage followup_message = 5;     // Full message object
  ModelDetails model_details = 6;               // Model configuration
  BackgroundComposerSource followup_source = 7; // Source of the follow-up (EDITOR, SLACK, etc.)
  bool continue_rebase = 8;                     // Continue a rebase operation
  PlanFollowupType plan_followup_type = 9;      // PLAN or EXECUTE
  ConversationAction followup_conversation_action = 10; // Action-based follow-up
}
```

### StartBackgroundComposerFromSnapshotRequest (Line 337815)

Used to start a new background agent from a dev environment snapshot.

Key fields:
- `snapshot_name_or_id`: The snapshot to start from
- `devcontainer_starting_point`: Git URL and ref for the dev container
- `prompt` / `rich_prompt`: Initial task description
- `model_details`: AI model configuration
- `repository_info`: Git repository information
- `source`: Where the request originated (EDITOR, SLACK, WEBSITE, LINEAR, etc.)
- `conversation_history`: Previous conversation context
- `bc_id`: Optional pre-assigned composer ID
- `conversation_action`: Action-based kickoff message
- `agent_session_id`: For session continuity
- `grind_mode_config`: Configuration for "grind mode" (extended task execution)

### StreamConversationRequest (Line 338746)

Used to stream conversation updates from the server.

```protobuf
message StreamConversationRequest {
  string bc_id = 1;                         // Background composer ID
  string offset_key = 2;                    // Resume from this offset
  bool filter_heavy_step_data = 3;          // Reduce data transfer
  bool should_send_prefetched_blobs_first = 4;  // Blob optimization
  repeated bytes pre_fetched_blob_ids = 5;  // Already-fetched blobs
}
```

### StreamConversationResponse (Line 338873)

Response containing conversation updates:
- `initial_state`: Full state on connection (CloudAgentState, blobs, workflow status)
- `interaction_update_with_offset`: Incremental updates with offset tracking
- `cloud_agent_state_with_id_and_offset`: State snapshots with position
- `workflow_status_with_offset`: Status changes (RUNNING, FINISHED, ERROR, etc.)
- `prefetched_blobs`: Large data blobs pre-fetched for efficiency

### InteractionUpdate (Line 248696)

The core streaming update message type from `agent.v1`:

```protobuf
message InteractionUpdate {
  oneof message {
    TextDelta text_delta = 1;
    PartialToolCall partial_tool_call = 7;
    ToolCallDelta tool_call_delta = 15;
    ToolCallStarted tool_call_started = 2;
    ToolCallCompleted tool_call_completed = 3;
    ThinkingDelta thinking_delta = 4;
    ThinkingCompleted thinking_completed = 5;
    UserMessageAppended user_message_appended = 6;
    TokenDelta token_delta = 8;
    Summary summary = 9;
    SummaryStarted summary_started = 10;
    SummaryCompleted summary_completed = 11;
    ShellOutputDelta shell_output_delta = 12;
    Heartbeat heartbeat = 13;
    TurnEnded turn_ended = 14;
    StepStarted step_started = 16;
    StepCompleted step_completed = 17;
  }
}
```

## Enums

### BackgroundComposerStatus (Line 335617)

```
UNSPECIFIED = 0
RUNNING = 1      - Agent is actively processing
FINISHED = 2     - Agent completed its task
ERROR = 3        - Agent encountered an error
CREATING = 4     - Agent is being initialized
EXPIRED = 5      - Agent session expired
```

### BackgroundComposerSource (Line 335653)

```
UNSPECIFIED = 0
EDITOR = 1               - Cursor IDE
SLACK = 2                - Slack integration
WEBSITE = 3              - Web interface
LINEAR = 4               - Linear integration
IOS_APP = 5              - iOS mobile app
API = 6                  - Direct API access
GITHUB = 7               - GitHub integration
CLI = 8                  - Command line interface
GITHUB_CI_AUTOFIX = 9    - GitHub CI autofix feature
GITLAB = 10              - GitLab integration
ENVIRONMENT_SETUP_WEB = 11 - Web-based env setup
GRIND_WEB = 12           - Web-based grind mode
```

### CloudAgentWorkflowStatus (Line 335635)

```
UNSPECIFIED = 0
RUNNING = 1     - Workflow is active
IDLE = 2        - Workflow is waiting
ERROR = 3       - Workflow errored
ARCHIVED = 4    - Workflow was archived
EXPIRED = 5     - Workflow session expired
```

### EnsembleStatus (Line 335692)

For parallel agent workflows:
```
UNSPECIFIED = 0
PARENT = 1      - This is the parent/orchestrating agent
CHILD = 2       - This is a child agent
```

### PlanFollowupType (Line 335713)

```
UNSPECIFIED = 0
PLAN = 1        - Request agent to create a plan
EXECUTE = 2     - Request agent to execute the plan
```

## Task Queuing Flow

1. **Task Creation**: Client calls `StartBackgroundComposerFromSnapshot` with:
   - Snapshot/devcontainer configuration
   - Initial prompt and context
   - Model configuration
   - Source integration (Slack, GitHub, etc.)

2. **Follow-up Messages**: Client calls `AddAsyncFollowupBackgroundComposer`:
   - Can be synchronous (wait for response) or async
   - Supports rich text and conversation actions
   - Can specify plan vs execute mode

3. **Server Processing**: The server:
   - Validates the request
   - Queues the message for the cloud agent
   - Returns immediately (async) or waits (sync)

## Result Delivery to UI

### Streaming Architecture

1. **Client connects** via `StreamConversation`:
   - Provides `bc_id` (background composer ID)
   - Optionally provides `offset_key` to resume from a position
   - Can request prefetched blobs for efficiency

2. **Server sends `initial_state`**:
   - Full `CloudAgentState` with conversation history
   - Current `workflow_status`
   - Pre-fetched blobs for referenced data

3. **Incremental updates** via `interaction_update_with_offset`:
   - Each update has an `offset_key` for resumption
   - Contains `InteractionUpdate` messages (text, tool calls, etc.)

4. **State snapshots** via `cloud_agent_state_with_id_and_offset`:
   - Periodic full state dumps
   - Used for efficient reconnection

### Client-Side Processing

The `processConversationStream` function (around line 488100):
1. Loads cached state from disk (if available)
2. Opens streaming connection with appropriate offset
3. Processes incoming messages:
   - `prefetchedBlobs`: Stores blobs locally
   - `initialState`: Hydrates conversation state
   - `interaction_update_with_offset`: Updates UI incrementally
   - `workflow_status_with_offset`: Updates status display

The `handleCloudAgentInteractionUpdates` function (line 950186):
1. Receives stream of interaction updates
2. Processes each update type (text, tool calls, etc.)
3. Handles special cases (duplicate detection, user messages)
4. Yields unified chat responses to UI components

### Optimizations

- **Blob prefetching**: Large data (diffs, tool results) stored as blobs
- **Offset-based resumption**: Clients track position for reconnection
- **Disk caching**: Conversation state cached locally via `CloudAgentStorageService`
- **Feature gates** control streaming behavior:
  - `cloud_agent_stream_skip_disk_read`
  - `cloud_agent_stream_force_stream_from_start`
  - `cloud_agent_send_prefetched_blobs_first`
  - `cloud_agent_send_existing_blob_ids`

## Relationship with Regular ComposerService

### Connection via `createdFromBackgroundAgent`

The foreground ComposerService and BackgroundComposerService are linked through the `createdFromBackgroundAgent` field on composer data:

```javascript
createdFromBackgroundAgent: {
  bcId: string,              // Background composer ID
  shouldStreamMessages: boolean,  // Whether to stream updates
  kickoffMessageId: string   // Initial message ID
}
```

### Usage Pattern

1. **Background-first mode**: User starts a background agent, which creates a composer:
   - Composer data has `createdFromBackgroundAgent.bcId` set
   - UI displays streaming updates from cloud agent
   - Follow-ups sent via `AddAsyncFollowupBackgroundComposer`

2. **Foreground-to-background**: User promotes a foreground chat to background:
   - `StartBackgroundComposerFromSnapshot` called with conversation history
   - Composer data updated with `createdFromBackgroundAgent`
   - Subsequent messages routed to background service

3. **Status synchronization**:
   - Background status changes reflected in composer data
   - `BackgroundComposerEventService` fires events on status changes
   - UI components observe both composer status and background status

### Key Code Paths

**Follow-up submission** (line 758234):
```javascript
// When sending follow-up to background agent
await Z.addAsyncFollowupBackgroundComposer({
    bcId: i.bcId,
    synchronous: !D,  // D = isAsync
    followupConversationAction: ie,
    modelDetails: i.modelDetails,
    followupSource: A3.EDITOR
})
```

**Background submit** (line 941782):
```javascript
// Submit to existing background agent
await (await this.aiService.backgroundComposerClient()).addAsyncFollowupBackgroundComposer(new iIs({
    bcId: n,
    synchronous: !0,
    followupMessage: o,
    followupSource: A3.EDITOR
}))
```

## Related Services

- `BackgroundComposerDataService`: Manages local state of background composers
- `BackgroundComposerEventService`: Event bus for status changes
- `CloudAgentStorageService`: Disk caching for conversation state and blobs
- `ComposerAgentService`: Handles streaming and UI updates
- `WorktreeComposerDataService`: Branch selection for background agents

## Files and Line References

| Component | Location |
|-----------|----------|
| BackgroundComposerService definition | Line 815697 |
| AddAsyncFollowupBackgroundComposerRequest | Line 339841, 459507 |
| StartBackgroundComposerFromSnapshotRequest | Line 337815 |
| StreamConversationRequest/Response | Lines 338746, 338873 |
| InteractionUpdate | Line 248696 |
| BackgroundComposerStatus enum | Line 335617 |
| BackgroundComposerSource enum | Line 335653 |
| processConversationStream | ~Line 488100 |
| handleCloudAgentInteractionUpdates | Line 950186 |
| BackgroundComposerEventService | Line 463231 |
| BackgroundComposerDataService module | Line 215495 |

## Client-Side Implementation Deep Dive

### BackgroundComposerDataService (Line 268765)

This service manages the local state of background composers. Key methods:

```javascript
class BackgroundComposerDataService {
    // Check if current window is a background agent window
    bcIdForThisWindow(): string | undefined {
        const remoteAuthority = this.workbenchEnvironmentService.remoteAuthority;
        if (remoteAuthority) return parseBcIdFromAuthority(remoteAuthority);
    }

    // Check if this is a background window
    isBackgroundWindow(): boolean {
        return this.bcIdForThisWindow() !== undefined;
    }

    // Get data from current window (if BC window)
    getInWindowBcData() {
        if (this.bcIdForThisWindow()) return this.data.inWindowBackgroundComposer;
    }

    // Get data from main window
    getBcDataInMainWindow(bcId: string) {
        if (!this.bcIdForThisWindow()) {
            return this.data.backgroundComposers.find(c => c.bcId === bcId);
        }
    }
}
```

**Data structure for in-memory state**:
```javascript
{
    backgroundComposers: BackgroundComposer[],  // List of all BC instances
    inWindowBackgroundComposer: {               // For dedicated BC windows
        detailedDiff: DiffDetails,
        loadingStatus: 'loading' | 'done' | 'error'
    },
    isWindowInWindowExpanded: boolean,
    hasEnvironmentJsonOnDisk: boolean,
    backgroundComposerFollowUpInputData: InputData,
    skipBuildCaches: boolean
}
```

### CloudAgentStorageService (Line 343147)

This service provides disk-based caching for background agent state and blobs.

**Architecture**:
```javascript
class CloudAgentStorageService {
    // Per-composer blob stores
    composerBlobStores: Map<string, BlobStore>;

    // State caches by bcId
    stateCachesByBcId: Map<string, StateCache>;

    // Property observables for reactive UI
    metadataProperties: Map<string, ReactiveValue>;
    cloudAgentStateProperties: Map<string, ReactiveValue>;

    // Write queues for async blob storage
    blobWriteQueuesByComposerId: Map<string, WriteQueue>;
    pendingWritesByComposerId: Map<string, Set<Promise>>;
}
```

**Key operations**:
1. **Metadata Storage**: Stores workflow status, blob IDs, offset keys per BC
2. **Blob Storage**: Large data (tool results, diffs) stored as blobs with IDs
3. **Conversation State**: Full conversation history cached for offline access
4. **Derived Properties**: PR URL, branch name, agent name extracted from state

**Storage key format**: `${bcId}:${propertyKey}` (Line 343142)

### Attachment Loop Management (Line 488457)

The `startBackgroundAgentAttachment` method manages streaming connections:

```javascript
async startBackgroundAgentAttachment({
    bcId: string,
    composerId: string,
    shouldSetRunningStatus: boolean
}) {
    // Acquire lock to prevent race conditions
    const lock = await this._acquireBackgroundAgentAttachmentStartLock(composerId);

    // Check for existing attachment
    const existing = this._backgroundAgentAttachmentLoops.get(composerId);
    if (existing) {
        if (existing.bcId === bcId && existing.state === RUNNING) {
            return; // Already attached
        }
        // Abort existing attachment before starting new
        existing.abortController.abort();
        await existing.cleanupPromise;
    }

    // Create new attachment
    const abortController = this._abortControllerFactory.create(/*...*/);
    this._backgroundAgentAttachmentLoops.set(composerId, {
        bcId,
        abortController,
        cleanupPromise: /*...*/,
        state: RUNNING
    });
}
```

**Attachment states**:
```javascript
enum AttachmentState {
    RUNNING,   // Actively streaming
    ABORTING   // Being shut down
}
```

### Window Architecture

Cursor supports two modes for background agents:

1. **Main Window Mode** (`bcIdForThisWindow() === undefined`):
   - Background agents shown in chat panel
   - State accessed via `backgroundComposers` array
   - Multiple agents visible in sidebar

2. **Dedicated Window Mode** (`bcIdForThisWindow() !== undefined`):
   - Separate VS Code window per agent
   - `remoteAuthority` contains the BC ID
   - Full file explorer access to agent workspace
   - `inWindowBackgroundComposer` holds state

**Window communication** (Line 1155652):
```javascript
// Opening BC in dedicated window
await this.nativeHostService.openWindow({
    remoteAuthority: `bc-${bcId}`,
    //...
});

// Running actions in BC window
await this.nativeHostService.runActionInWindow({
    windowId: bcWindowId,
    actionId: 'workbench.action.reloadWindow',
    args: {}
});
```

## HeadlessAgenticComposerResponse (Line 339254)

The response format for background agent execution:

```protobuf
message HeadlessAgenticComposerResponse {
    string text = 1;                              // Generated text
    ToolCall tool_call = 2;                       // Tool invocation
    FinalToolResult final_tool_result = 3;        // Tool execution result
    StreamedBackToolCall streamed_back_tool_call = 6; // Streaming tool call
    UserMessage user_message = 4;                 // User message echo
    bool is_message_done = 5;                     // Message completion flag
    Error error = 7;                              // Error information
    ConversationMessage human_message = 8;        // Human message
    Thinking thinking = 9;                        // Reasoning/thinking
    int32 thinking_duration_ms = 10;              // Time spent thinking
    ThinkingStyle thinking_style = 12;            // Type of thinking
    Status status = 11;                           // Status update
}
```

**Status types**:
```javascript
enum StatusType {
    UNSPECIFIED = 0,
    INDEX_SYNC = 1,   // Index synchronization in progress
    GENERIC = 2       // Generic status message
}
```

## PR Creation Flow

### MakePRBackgroundComposerRequest (Line 337064)

```protobuf
message MakePRBackgroundComposerRequest {
    string bc_id = 1;           // Background composer ID
    string workflow_id = 2;     // Optional workflow ID (for parallel agents)
}
```

### MakePRBackgroundComposerResponse (Line 337099)

```protobuf
message MakePRBackgroundComposerResponse {
    string pr_url = 1;          // Pull request URL
    string branch_name = 2;     // Branch name created
    bool has_commits = 3;       // Whether there are commits
    string owner = 4;           // Repository owner
    string repo = 5;            // Repository name
}
```

### OpenPRBackgroundComposerRequest (Line 337154)

Full PR creation with metadata:
```protobuf
message OpenPRBackgroundComposerRequest {
    string bc_id = 1;                    // Background composer ID
    string title = 2;                    // PR title
    string body = 3;                     // PR description
    string base_branch = 4;              // Target branch
    bool draft = 5;                      // Create as draft PR
    bool open_as_cursor_github_app = 6;  // Open via Cursor GitHub app
    bool skip_reviewer_request = 7;      // Don't request reviewers
    bytes agent_state_blob_id = 8;       // State blob for reference
    string workflow_id = 9;              // Workflow ID
}
```

## Lifecycle State Machine

```
            +---------+
            | CREATING|
            +----+----+
                 |
                 v
            +---------+
     +----->| RUNNING |<-----+
     |      +----+----+      |
     |           |           |
  resume      pause      resume
     |           |           |
     |      +----v----+      |
     +------| PAUSED  |------+
            +---------+
                 |
              archive
                 |
            +----v----+
            | ARCHIVED|
            +---------+

      [ERROR can occur from any state]
      [EXPIRED triggered by timeout from RUNNING/PAUSED]
```

## Open Questions for Further Investigation

1. **Blob storage format**: How are blobs identified and stored? What's the serialization?
2. **Workflow synthesis**: How does `ParallelAgentWorkflowSynthesisStrategy` work?
3. **Grind mode**: What is the "grind mode" configuration and behavior?
4. **Rate limiting**: How are concurrent background agents limited?
5. **Webhook integration**: How do the webhook configs work for external integrations?
6. **Devcontainer starting point**: How does the `DevContainerStartingPoint` message work?
7. **Personal environment JSON**: What's stored in `.cursor/environment.json`?
