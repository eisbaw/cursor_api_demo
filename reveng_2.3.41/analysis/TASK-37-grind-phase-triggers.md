# TASK-37: Grind Mode Phase Transition Triggers (PLANNING to EXECUTING)

Analysis of phase transition triggers in Cursor's Grind Mode feature in version 2.3.41.

## Executive Summary

**Key Finding**: Phase transitions from PLANNING to EXECUTING in Grind Mode are **entirely server-controlled**. The Cursor IDE client:
1. Sends initial phase via `StartingMessageType` or `GrindModeConfig.phase`
2. Can request phase changes via `PlanFollowupType` in followup requests
3. Receives phase updates via `CloudAgentState.grindModeConfig.phase` in streaming responses
4. **Does NOT** autonomously trigger phase transitions - all transitions are orchestrated by the server

There are **no automatic time-based client-side phase transitions**.

## Phase Enum Definitions

### GrindModeConfig.Phase

**Location**: Line 337750-337758 in `workbench.desktop.main.js`

```javascript
_bs = (i => (
    i[i.UNSPECIFIED = 0] = "UNSPECIFIED",
    i[i.PLANNING = 1] = "PLANNING",
    i[i.EXECUTING = 2] = "EXECUTING",
    i
))(_bs || {})

k.util.setEnumType(_bs, "aiserver.v1.GrindModeConfig.Phase", [
    { no: 0, name: "PHASE_UNSPECIFIED" },
    { no: 1, name: "PHASE_PLANNING" },
    { no: 2, name: "PHASE_EXECUTING" }
])
```

### GrindModeConfig Message

**Location**: Line 337712-337749

```protobuf
message GrindModeConfig {
  int64 time_budget_ms = 1;              // Time budget in milliseconds
  optional int64 start_time_unix_ms = 2;  // Unix timestamp when session started
  Phase phase = 3;                        // Current phase (PLANNING/EXECUTING)
}
```

## Mechanisms That Can Trigger Phase Transitions

### 1. Initial Phase via StartingMessageType

**Location**: Line 335767-335778

The `StartingMessageType` enum determines the initial phase when starting a background composer:

```javascript
Sbs = (i => (
    i[i.UNSPECIFIED = 0] = "UNSPECIFIED",
    i[i.USER_MESSAGE = 1] = "USER_MESSAGE",
    i[i.PLAN_START = 2] = "PLAN_START",
    i[i.PLAN_EXECUTE = 3] = "PLAN_EXECUTE",
    i
))(Sbs || {})

k.util.setEnumType(Sbs, "aiserver.v1.StartingMessageType", [
    { no: 0, name: "STARTING_MESSAGE_TYPE_UNSPECIFIED" },
    { no: 1, name: "STARTING_MESSAGE_TYPE_USER_MESSAGE" },
    { no: 2, name: "STARTING_MESSAGE_TYPE_PLAN_START" },      // Starts in PLANNING
    { no: 3, name: "STARTING_MESSAGE_TYPE_PLAN_EXECUTE" }     // Starts in EXECUTING
])
```

**Usage**: Part of `StartBackgroundComposerFromSnapshotRequest` (field 41):
- `STARTING_MESSAGE_TYPE_PLAN_START` (2): Begin session in PLANNING phase
- `STARTING_MESSAGE_TYPE_PLAN_EXECUTE` (3): Begin session in EXECUTING phase

### 2. Phase Transition via PlanFollowupType

**Location**: Line 335713-335721

The `PlanFollowupType` enum allows requesting phase transitions in followup requests:

```javascript
bbs = (i => (
    i[i.UNSPECIFIED = 0] = "UNSPECIFIED",
    i[i.PLAN = 1] = "PLAN",
    i[i.EXECUTE = 2] = "EXECUTE",
    i
))(bbs || {})

k.util.setEnumType(bbs, "aiserver.v1.PlanFollowupType", [
    { no: 0, name: "PLAN_FOLLOWUP_TYPE_UNSPECIFIED" },
    { no: 1, name: "PLAN_FOLLOWUP_TYPE_PLAN" },     // Stay in/return to PLANNING
    { no: 2, name: "PLAN_FOLLOWUP_TYPE_EXECUTE" }   // Transition to EXECUTING
])
```

**Usage**: Part of `AddAsyncFollowupBackgroundComposerRequest` (field 9):

```javascript
// Line 339826-339909
s1h = class Oln extends ge {
    bcId = "";
    followup = "";
    richFollowup = "";
    synchronous = !1;
    followupMessage;
    modelDetails;
    followupSource;
    continueRebase;
    planFollowupType;  // <-- Controls phase transition
    followupConversationAction;
    // ...
}
```

When a user approves a plan and wants to execute it, the client sends a followup request with `planFollowupType = PLAN_FOLLOWUP_TYPE_EXECUTE` (2).

### 3. Phase State in CloudAgentState

**Location**: Line 342735, 342879

The current phase is persisted in `CloudAgentState.grindModeConfig`:

```javascript
xbs = class wun extends ge {
    // ... other fields ...
    grindModeConfig;  // Contains current phase
    // ... other fields ...
}

// Field definition
{
    no: 25,
    name: "grind_mode_config",
    kind: "message",
    T: MGr,  // GrindModeConfig type
    opt: !0
}
```

### 4. Phase in BackgroundComposer Response

**Location**: Line 337377, 337571

The `BackgroundComposer` message includes a `grindPhase` string field:

```javascript
xWt = class qan extends ge {
    // ... other fields ...
    grindPhase;  // String representation of current phase
    // ... other fields ...
}

// Field definition
{
    no: 36,
    name: "grind_phase",
    kind: "scalar",
    T: 9,  // string type
    opt: !0
}
```

Note: This is a **string** field (`T: 9`), not an enum reference, suggesting it may contain human-readable phase names like "planning" or "executing".

## Phase Transition Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           CLIENT (Cursor IDE)                            │
└──────────────────────────────────────────────────────────────────────────┘
                │                                      ▲
                │ StartBackgroundComposerFromSnapshotRequest               │
                │   - startingMessageType: PLAN_START (2)                  │
                │   OR                                                     │
                │   - grindModeConfig.phase: PLANNING (1)                  │
                ▼                                                          │
┌──────────────────────────────────────────────────────────────────────────┐
│                            SERVER (AI Server)                            │
│                                                                          │
│  1. Receives request with initial phase setting                          │
│  2. Creates CloudAgentState with grindModeConfig.phase = PLANNING        │
│  3. Streams updates to client                                            │
└──────────────────────────────────────────────────────────────────────────┘
                │                                      │
                │ StreamConversationResponse           │
                │   - cloudAgentState with phase       │
                ▼                                      │
┌──────────────────────────────────────────────────────────────────────────┐
│                           CLIENT (Cursor IDE)                            │
│                                                                          │
│  User reviews plan and approves it                                       │
│  UI triggers followup with phase transition request                      │
└──────────────────────────────────────────────────────────────────────────┘
                │                                      ▲
                │ AddAsyncFollowupBackgroundComposerRequest                │
                │   - planFollowupType: EXECUTE (2)   │                   │
                ▼                                      │
┌──────────────────────────────────────────────────────────────────────────┐
│                            SERVER (AI Server)                            │
│                                                                          │
│  1. Receives followup with planFollowupType = EXECUTE                    │
│  2. Updates CloudAgentState.grindModeConfig.phase = EXECUTING            │
│  3. Begins execution phase                                               │
│  4. Streams updated state to client                                      │
└──────────────────────────────────────────────────────────────────────────┘
                │
                │ StreamConversationResponse
                │   - cloudAgentState.grindModeConfig.phase = EXECUTING
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                           CLIENT (Cursor IDE)                            │
│                                                                          │
│  Displays "Executing" phase UI                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

## Key Observations

### 1. No Automatic Time-Based Transitions

There is **no evidence** of automatic phase transitions based on:
- Time elapsed in planning phase
- Time budget consumption
- Number of interactions/turns

Phase transitions require explicit user action (approve plan -> execute).

### 2. Server Authority

The server is the source of truth for phase state:
- Client requests transitions via `planFollowupType`
- Server updates `CloudAgentState.grindModeConfig.phase`
- Client receives updates via streaming responses

### 3. Dual Phase Representations

Phase is represented in two ways:
1. **Enum** in `GrindModeConfig.phase` (integer: 0, 1, 2)
2. **String** in `BackgroundComposer.grindPhase` (e.g., "planning", "executing")

This suggests some API flexibility or backward compatibility considerations.

### 4. Phase is Part of Persistent State

Phase is stored in `CloudAgentState`, which is:
- Persisted to blob storage
- Recovered during session reconnection
- Part of the durable conversation state

## Related Protobuf Messages

| Message | Field | Type | Description |
|---------|-------|------|-------------|
| `GrindModeConfig` | phase | enum (0,1,2) | Canonical phase state |
| `BackgroundComposer` | grindPhase | string | Human-readable phase |
| `CloudAgentState` | grindModeConfig | message | Contains phase in config |
| `StartBackgroundComposerFromSnapshotRequest` | startingMessageType | enum | Initial phase selection |
| `StartBackgroundComposerFromSnapshotRequest` | grindModeConfig | message | Full config with phase |
| `AddAsyncFollowupBackgroundComposerRequest` | planFollowupType | enum | Phase transition request |

## UI Integration Points

The client likely uses phase information for:
1. **Phase-specific UI rendering** (Plan view vs Execute view)
2. **Action buttons** (Approve Plan -> triggers EXECUTE transition)
3. **Status display** ("Planning..." vs "Executing...")
4. **Tool availability** (different tools may be available in each phase)

## Open Questions

1. **Plan Approval Flow**: What specific UI action triggers the `planFollowupType = EXECUTE` request? Is it a button click on a plan review component?

2. **Phase Rejection**: Can the server reject a phase transition request? What happens if EXECUTE is requested but the plan isn't complete?

3. **Phase Regression**: Can you go from EXECUTING back to PLANNING? The enum doesn't prevent it, but the workflow might.

4. **Phase-Specific Behavior**: Do different phases have different:
   - Tool restrictions?
   - Time budget consumption rates?
   - Model selections?

5. **grindPhase String Values**: What are the exact string values in `BackgroundComposer.grindPhase`? Are they lowercase ("planning", "executing") or match the enum names?

## File References

| Component | Location |
|-----------|----------|
| GrindModeConfig.Phase enum | Line 337750-337758 |
| GrindModeConfig message | Line 337712-337749 |
| StartingMessageType enum | Line 335767-335778 |
| PlanFollowupType enum | Line 335713-335721 |
| BackgroundComposer.grindPhase | Line 337377, 337571 |
| CloudAgentState.grindModeConfig | Line 342735, 342879 |
| AddAsyncFollowupBackgroundComposerRequest | Line 339826-339909 |
| StartBackgroundComposerFromSnapshotRequest | Line 337759-338111 |

## Summary

Phase transitions in Grind Mode follow a request-response pattern:

1. **PLANNING -> EXECUTING**: User approves plan, client sends `AddAsyncFollowupBackgroundComposerRequest` with `planFollowupType = PLAN_FOLLOWUP_TYPE_EXECUTE`

2. **Initial Phase Selection**: When starting a new grind session, `startingMessageType` or `grindModeConfig.phase` determines whether to start in PLANNING or directly in EXECUTING

3. **No Automatic Transitions**: All phase changes are explicitly requested by the client based on user action

4. **Server Control**: The server processes requests, updates state, and streams the new phase back to the client

This design ensures human oversight of the planning phase before execution begins, a key safety feature for autonomous coding agents.
