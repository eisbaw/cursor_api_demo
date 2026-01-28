# TASK-34: Grind Mode Time Budget Enforcement Mechanism

Analysis of the time budget enforcement mechanism for Cursor's Grind Mode feature in version 2.3.41.

## Executive Summary

**Key Finding**: The time budget enforcement for Grind Mode is **primarily server-side**. The Cursor IDE client passes the `GrindModeConfig` with `time_budget_ms` and `start_time_unix_ms` to the server, but the actual enforcement (timeout, expiration) happens on the AI server infrastructure. The client merely observes and displays the EXPIRED status when the server sets it.

## GrindModeConfig Structure

**Location**: Line 337712-337749 in `workbench.desktop.main.js`

```protobuf
message GrindModeConfig {
  int64 time_budget_ms = 1;              // Time budget in milliseconds
  optional int64 start_time_unix_ms = 2;  // Unix timestamp when session started
  Phase phase = 3;                        // Current phase (PLANNING/EXECUTING)
}

enum Phase {
  PHASE_UNSPECIFIED = 0;
  PHASE_PLANNING = 1;
  PHASE_EXECUTING = 2;
}
```

### Field Analysis

| Field | Type | Description |
|-------|------|-------------|
| `time_budget_ms` | int64 | Total allocated time for the grind session (milliseconds). Default: `ug.zero` (BigInt zero) |
| `start_time_unix_ms` | int64 (optional) | Unix timestamp marking session start. Server uses this to calculate elapsed time |
| `phase` | enum | Current workflow phase (PLANNING=1, EXECUTING=2) |

## Time Budget Flow

### 1. Session Initialization

When starting a grind session via `StartBackgroundComposerFromSnapshotRequest` (Line 337759-338111):

```javascript
// GrindModeConfig attached to request
{
  grindModeConfig: {
    timeBudgetMs: BigInt(timeInMs),
    startTimeUnixMs: BigInt(Date.now()),  // Set by server or client
    phase: 0  // UNSPECIFIED initially
  }
}
```

The config is stored in:
1. **Request**: `StartBackgroundComposerFromSnapshotRequest.grind_mode_config` (field 52)
2. **Agent State**: `CloudAgentState.grind_mode_config` (field 25)

### 2. Server-Side Tracking

The `CloudAgentState` persists the grind configuration (Line 342710-342912):

```javascript
// CloudAgentState includes:
{
  originalRequestStartUnixMs,  // When the original request started
  grindModeConfig,             // The grind mode configuration
  numCompletedTurns,           // Progress tracking
  commits,                     // Commit tracking
  commitCount                  // Total commits made
}
```

### 3. Budget Enforcement (Server-Side)

**Critical Discovery**: The client does NOT enforce the time budget. Evidence:

1. **No client-side timeout logic found** for `time_budget_ms`
2. **EXPIRED status comes from server** via `CloudAgentWorkflowStatus.EXPIRED` (enum value 5)
3. **Client only reacts** to workflow status changes

The server signals budget exhaustion by setting:
- `BackgroundComposerStatus.EXPIRED` (5)
- `CloudAgentWorkflowStatus.EXPIRED` (5)

### 4. Client-Side Status Handling

When the server sets EXPIRED status (Line 487977-487993):

```javascript
if (g.workflowStatus === Gy.ARCHIVED ||
    g.workflowStatus === Gy.ERROR ||
    g.workflowStatus === Gy.EXPIRED) {
    this._structuredLogService.debug(
        "background_composer",
        "cloud agent workflow is finished, stopping stream",
        { bcId, composerId, workflowStatus }
    );
    return { shouldRetry: false };
}
```

Status mapping (Line 488048-488067):

```javascript
case Gy.EXPIRED:
    d = ic.EXPIRED;  // Maps CloudAgentWorkflowStatus to BackgroundComposerStatus
    break;
```

## VM Destruction Timeout (Separate Mechanism)

There's a separate VM destruction timeout (Line 14772-14776):

```javascript
Ewr = 15,  // Default 15 minutes
u9a = i => {
    if (!i) return Ewr;
    const e = /destroy-after-(\d+)-minutes/;
    const t = i.match(e);
    return t ? parseInt(t[1], 10) : Ewr;
}
```

This is for VM lifecycle management, NOT grind mode time budget. VMs can be configured with `destroy-after-{N}-minutes` patterns.

## Client-Side Time Display

The client displays elapsed time using `formatElapsedTime` (Line 763028-763037):

```javascript
function U1f(i, e) {
    const t = Math.max(0, Math.floor((e - i) / 1e3));
    if (t < 60) return `${t}s`;
    const n = Math.floor(t / 60);
    const s = t % 60;
    if (n < 60) return `${n}m ${s}s`;
    const r = Math.floor(n / 60);
    const o = n % 60;
    return `${r}h ${o}m`;
}
```

Display text (Line 762570):
```javascript
`Working for ${Je}`  // e.g., "Working for 5m 30s"
```

This uses `createdAt` or `lastUpdatedAt`, NOT the grind mode time budget.

## VM Usage Tracking

Separate from time budget, there's VM usage tracking (Line 343007-343019):

```protobuf
message GetBackgroundComposerVmUsageRequest {
  string bc_id = 1;
}

message GetBackgroundComposerVmUsageResponse {
  int64 total_duration_ms = 1;  // Total VM usage time
}
```

API endpoint (Line 816131-816135):
```javascript
getBackgroundComposerVmUsage: {
    name: "GetBackgroundComposerVmUsage",
    kind: Kt.Unary
}
```

This tracks actual VM compute time consumed, potentially for billing/quotas.

## Discovery Budget (Different Feature)

Note: There's a separate "discovery budget" concept (Line 105683-105734):

```protobuf
message DiscoveryBudgetReminder {
  int32 discovery_rounds_remaining = 1;
  optional string discovery_effort = 2;
}
```

This is for tool call discovery phases, NOT grind mode time budget.

## Expiration Handling in UI

When workflow expires (Line 732189-732196):

```javascript
case Gy.EXPIRED:
    return "expired";  // Returns string status for UI display
```

The client then filters out expired sessions from active lists (Line 761065):

```javascript
const t = i.data.backgroundComposers.filter(
    p => !p.isOwnedByDifferentTeamMember &&
         p.status !== ic.EXPIRED
);
```

## Phase Transitions

Phase transitions (PLANNING -> EXECUTING) are **server-controlled**:

1. **StartingMessageType** determines initial phase (Line 335767-335778):
   - `STARTING_MESSAGE_TYPE_PLAN_START` (2): Start in planning
   - `STARTING_MESSAGE_TYPE_PLAN_EXECUTE` (3): Start in execution

2. **PlanFollowupType** controls transitions (Line 335713-335721):
   - `PLAN_FOLLOWUP_TYPE_PLAN` (1): Continue planning
   - `PLAN_FOLLOWUP_TYPE_EXECUTE` (2): Switch to execution

3. No evidence of automatic time-based phase transitions in the client.

## Related Configuration

### Feature Gate: vm_usage_watcher_enabled

```javascript
vm_usage_watcher_enabled: {
    client: false,  // Server-side only
    default: false
}
```

Suggests server-side VM usage monitoring capability.

## Architectural Conclusions

1. **Server Authority**: The AI server is authoritative for time budget enforcement
2. **Client Passive**: The IDE client is passive - it sends config, receives status
3. **No Client Validation**: The client doesn't validate if `time_budget_ms` has been exceeded
4. **Status-Driven**: All timeout behavior is communicated via workflow status changes
5. **Graceful Handling**: Server appears to set EXPIRED status, allowing client to clean up gracefully

## Enforcement Mechanism Summary

```
┌─────────────────┐      GrindModeConfig        ┌─────────────────┐
│   Cursor IDE    │ ──────────────────────────> │    AI Server    │
│    (Client)     │      (time_budget_ms,       │   (Enforces)    │
│                 │       start_time_unix_ms)   │                 │
└─────────────────┘                             └─────────────────┘
        │                                               │
        │                                               │ Tracks elapsed
        │                                               │ time server-side
        │                                               │
        │      CloudAgentWorkflowStatus.EXPIRED         │
        │ <─────────────────────────────────────────────│
        │                                               │
        ▼                                               │
┌─────────────────┐                             ┌─────────────────┐
│  Display status │                             │  VM destroyed/  │
│  "expired"      │                             │  session ended  │
└─────────────────┘                             └─────────────────┘
```

## Open Questions

1. **Exact Server Logic**: What's the exact algorithm the server uses? Does it check `Date.now() - start_time_unix_ms > time_budget_ms` on each request?

2. **Grace Period**: Is there any grace period before EXPIRED status is set?

3. **Mid-Task Handling**: What happens if a tool call is in progress when budget expires? Does it complete or abort immediately?

4. **Phase Impact**: Does the phase (PLANNING vs EXECUTING) affect how budget is consumed or enforced?

5. **Budget Extensions**: Can the budget be extended dynamically during a session?

6. **Billing Relationship**: How does `time_budget_ms` relate to `totalDurationMs` from VM usage?

## Recommendations for Further Investigation

1. **Network Traffic Analysis**: Capture gRPC traffic to observe actual timeout signaling
2. **Server Logs**: If accessible, examine server-side timeout implementation
3. **API Experimentation**: Test with very short `time_budget_ms` values to observe behavior
4. **Error Message Analysis**: Check if EXPIRED status includes any explanatory metadata

## File References

| Component | Location |
|-----------|----------|
| GrindModeConfig message | Line 337712-337749 |
| GrindModeConfig.Phase enum | Line 337750-337758 |
| grind_mode_config in StartRequest | Line 337810, 338107 |
| grind_mode_config in CloudAgentState | Line 342735, 342879 |
| CloudAgentState.originalRequestStartUnixMs | Line 342731, 342855 |
| CloudAgentState.numCompletedTurns | Line 342740, 342909 |
| GetBackgroundComposerVmUsage API | Line 816131-816135 |
| GetBackgroundComposerVmUsageResponse | Line 343007-343019 |
| EXPIRED status handling | Line 487977, 488061-488062 |
| Status mapping to UI | Line 732189-732195 |
| Expired session filtering | Line 761065 |
| formatElapsedTime display | Line 763028-763037 |
| VM destroy timeout pattern | Line 14772-14776 |
| vm_usage_watcher_enabled gate | Line 293553 |

## Summary

The Grind Mode time budget enforcement is a **server-side responsibility**. The Cursor IDE client:

1. **Passes** the `time_budget_ms` and `start_time_unix_ms` configuration to the server
2. **Does NOT** independently track or enforce the budget
3. **Reacts** to server-sent `EXPIRED` workflow status
4. **Displays** elapsed time using a simple formatting function
5. **Filters out** expired sessions from active views

The actual enforcement logic - tracking elapsed time, comparing against budget, and triggering expiration - occurs on the Cursor AI server infrastructure, making it a black box from the client perspective.
