# TASK-16: Grind Mode Configuration and Behavior

Analysis of "Grind Mode" in the BackgroundComposer service.

## Overview

Grind Mode is a feature in Cursor's Background Composer that allows agents to operate with a time budget and explicit planning/executing phases. It appears to be a web-based interface for running extended, time-budgeted agent tasks in cloud VMs.

## GrindModeConfig Message Type

**Location**: Line 337712-337749 in `workbench.desktop.main.js`

```protobuf
message GrindModeConfig {
  int64 time_budget_ms = 1;          // Time budget in milliseconds
  optional int64 start_time_unix_ms = 2;  // When the grind session started
  Phase phase = 3;                    // Current phase (PLANNING or EXECUTING)
}
```

### Fields

| Field | Proto Type | Description |
|-------|------------|-------------|
| `time_budget_ms` | int64 | Total time budget for the grind session in milliseconds |
| `start_time_unix_ms` | int64 (optional) | Unix timestamp when the session started |
| `phase` | enum | Current phase of operation |

## GrindModeConfig.Phase Enum

**Location**: Line 337750-337758

```
enum Phase {
  PHASE_UNSPECIFIED = 0;
  PHASE_PLANNING = 1;    // Agent is creating a plan
  PHASE_EXECUTING = 2;   // Agent is executing the plan
}
```

### Phase Semantics

1. **PHASE_PLANNING (1)**: The agent is in planning mode, analyzing the task and creating a strategy
2. **PHASE_EXECUTING (2)**: The agent is executing the planned actions

This mirrors the `PlanFollowupType` enum used in regular follow-ups, but specific to grind mode operation.

## Related Enums

### PlanFollowupType (Line 335713-335721)

```
enum PlanFollowupType {
  PLAN_FOLLOWUP_TYPE_UNSPECIFIED = 0;
  PLAN_FOLLOWUP_TYPE_PLAN = 1;     // Continue planning
  PLAN_FOLLOWUP_TYPE_EXECUTE = 2;  // Switch to execution
}
```

### StartingMessageType (Line 335767-335778)

```
enum StartingMessageType {
  STARTING_MESSAGE_TYPE_UNSPECIFIED = 0;
  STARTING_MESSAGE_TYPE_USER_MESSAGE = 1;   // Normal user-initiated
  STARTING_MESSAGE_TYPE_PLAN_START = 2;     // Start in planning mode
  STARTING_MESSAGE_TYPE_PLAN_EXECUTE = 3;   // Start in execution mode
}
```

This allows sessions to be initiated directly in a specific phase.

## Where GrindModeConfig is Used

### 1. StartBackgroundComposerFromSnapshotRequest

**Location**: Line 337810, 338107

Field `grind_mode_config` (field number 52) - allows setting grind mode configuration when starting a new background composer session.

Also includes `enable_setup_vm_environment_tool` (field 51) - enables VM environment setup tool for grind sessions.

### 2. CloudAgentState

**Location**: Line 342735, 342879

Field `grind_mode_config` (field number 25) - stored in the agent's persistent state, allowing the grind mode configuration to be tracked throughout the agent's lifecycle.

Related fields in CloudAgentState:
- `conversation_state` - Full conversation context
- `num_prior_interaction_updates` - Interaction counter
- `commits` - List of commits made
- `commit_count` - Total commit count
- `num_completed_turns` - Turn counter for progress tracking

### 3. BackgroundComposer (grindPhase field)

**Location**: Line 337377, 337571

The `BackgroundComposer` message has a `grind_phase` field (field number 36) that stores the current phase as a string (for display in listings).

## BackgroundComposerSource.GRIND_WEB

**Location**: Line 335653, 335691

```
GRIND_WEB = 12  // "BACKGROUND_COMPOSER_SOURCE_GRIND_WEB"
```

This source type indicates that the background composer was initiated from the "Grind" web interface. Full source types:

| Value | Name | Description |
|-------|------|-------------|
| 0 | UNSPECIFIED | Unknown source |
| 1 | EDITOR | Cursor IDE |
| 2 | SLACK | Slack integration |
| 3 | WEBSITE | General web interface |
| 4 | LINEAR | Linear issue tracker |
| 5 | IOS_APP | iOS app |
| 6 | API | Direct API call |
| 7 | GITHUB | GitHub integration |
| 8 | CLI | Command line interface |
| 9 | GITHUB_CI_AUTOFIX | GitHub CI auto-fix |
| 10 | GITLAB | GitLab integration |
| 11 | ENVIRONMENT_SETUP_WEB | Environment setup web |
| 12 | GRIND_WEB | Grind mode web interface |

## ListGrindModeComposers API

**Location**: Line 343087-343131, 816137-816141

A dedicated API endpoint for listing grind mode composers:

```protobuf
message ListGrindModeComposersRequest {
  int32 limit = 1;  // Maximum number of composers to return
}

message ListGrindModeComposersResponse {
  repeated BackgroundComposer composers = 1;
}
```

This API is part of the `BackgroundComposerService`:
```javascript
listGrindModeComposers: {
    name: "ListGrindModeComposers",
    I: JFc,  // Request type
    O: GFc,  // Response type
    kind: Kt.Unary
}
```

## Parallel Agent Workflow Integration

**Location**: Line 335701-335712

Grind mode can integrate with parallel agent workflows:

```
enum ParallelAgentWorkflowSynthesisStrategy {
  UNSPECIFIED = 0;
  SINGLE_AGENT = 1;           // Standard single agent
  FANOUT_VOTING = 2;          // Multiple agents vote on solution
  PAIRWISE_TOURNAMENT = 3;    // Tournament bracket comparison
}
```

Configuration (Line 295170-295576):
```javascript
parallel_agent_synthesis_config: {
    strategy: "pairwise_tournament",  // Default strategy
    synthesisModel: "gpt-5.1-codex-high",
    fanoutSize: null
}
```

## Ensemble Status

**Location**: Line 335692-335700

```
enum EnsembleStatus {
  UNSPECIFIED = 0;
  PARENT = 1;    // Orchestrating parent agent
  CHILD = 2;     // Child agent in ensemble
}
```

This allows grind mode to spawn multiple child agents for parallel task execution within the time budget.

## Time Budget Behavior

The `time_budget_ms` field suggests grind mode operates with a finite time allocation. The agent likely:

1. Tracks elapsed time from `start_time_unix_ms`
2. Monitors against `time_budget_ms` threshold
3. May transition phases or terminate when budget is exhausted

The default VM destruction timeout is 15 minutes (Line 14772: `Ewr = 15`), configurable via `destroy-after-(\d+)-minutes` pattern.

## Environment Configuration

### Background Composer Environment (Line 182285, 182907)

```javascript
backgroundComposerEnv: "dev" | "prod" | "fullLocal"
```

The environment affects:
- Backend URL routing
- Proxy configuration
- Development vs production behavior

### VM Environment Setup Tool

**Location**: Line 137359-137438

A dedicated tool `SetupVmEnvironmentArgs/SetupVmEnvironmentResult` for configuring VM environments during grind sessions.

## UI Display

### Planning Indicator

**Location**: Line 695809

```javascript
Lsf = be("<span>Planning next moves")
```

Displayed when the agent is in PLANNING phase.

### Background Composer UI Modes

**Location**: Line 185383-185414

CSS variables for different modes:
- `--composer-mode-chat-background`
- `--composer-mode-background-background`
- `--composer-mode-plan-background`
- `--composer-mode-triage-background`
- `--composer-mode-spec-background`
- `--composer-mode-debug-background`

## Model Configuration

### Background Composer Default

**Location**: Line 182754-182760, 268031-268043

```javascript
backgroundComposer: {
    defaultModel: "default",
    fallbackModels: [],
    bestOfNDefaultModels: []
}
```

Max mode is enabled by default for background composer:
```javascript
maxMode: e === "background-composer"  // Always true for background-composer
```

## Status Lifecycle

### BackgroundComposerStatus (Line 335617-335634)

```
enum BackgroundComposerStatus {
  UNSPECIFIED = 0;
  RUNNING = 1;     // Actively processing
  FINISHED = 2;    // Successfully completed
  ERROR = 3;       // Failed with error
  CREATING = 4;    // VM being provisioned
  EXPIRED = 5;     // Time limit reached
}
```

### CloudAgentWorkflowStatus (Line 335635-335652)

```
enum CloudAgentWorkflowStatus {
  UNSPECIFIED = 0;
  RUNNING = 1;     // Workflow active
  IDLE = 2;        // Waiting for input
  ERROR = 3;       // Workflow error
  ARCHIVED = 4;    // Moved to archive
  EXPIRED = 5;     // Expired
}
```

## Data Flow Summary

1. **Web Interface**: User initiates a grind session from the web (`GRIND_WEB` source)
2. **Time Budget**: System specifies `time_budget_ms`
3. **VM Provisioning**: `enable_setup_vm_environment_tool` configures environment
4. **Start Request**: `StartBackgroundComposerFromSnapshotRequest` includes `grind_mode_config`
5. **Phase Tracking**: Agent state tracks current `phase`
6. **Parallel Execution**: Optional ensemble/parallel agent integration
7. **Progress Monitoring**: `num_completed_turns`, `commit_count` tracking
8. **API Access**: `ListGrindModeComposers` provides dedicated listing of grind sessions

## Open Questions

1. **Time Budget Enforcement**: How exactly is the time budget enforced? Does the agent self-terminate or is it forcefully stopped server-side?

2. **Phase Transitions**: What triggers the transition from PLANNING to EXECUTING phase? Is it automatic or user-controlled?

3. **Budget Exhaustion**: What happens when time budget runs out mid-task? Is there graceful handling?

4. **Parallel Agent Coordination**: How do child agents in an ensemble share context during grind mode?

5. **Server-Side Logic**: Most grind mode behavior appears to be server-side. The client just passes configuration and displays phase information.

## Suggested Follow-up Tasks

- TASK-XX: Investigate time budget enforcement mechanism on server
- TASK-XX: Document the Grind web interface and user flow
- TASK-XX: Analyze phase transition triggers in conversation flow
- TASK-XX: Explore ensemble/parallel agent integration with grind mode
- TASK-XX: Reverse engineer CloudAgentState persistence and recovery

## File References

| Component | Location |
|-----------|----------|
| GrindModeConfig message | Line 337712-337749 |
| GrindModeConfig.Phase enum | Line 337750-337758 |
| grind_mode_config in StartRequest | Line 337810, 338107 |
| grind_mode_config in CloudAgentState | Line 342735, 342879 |
| grindPhase in BackgroundComposer | Line 337377, 337571 |
| ListGrindModeComposersRequest | Line 343087-343105 |
| ListGrindModeComposersResponse | Line 343106-343131 |
| ListGrindModeComposers service method | Line 816137-816141 |
| GRIND_WEB source constant | Line 335691 |
| BackgroundComposerStatus enum | Line 335617-335634 |
| CloudAgentWorkflowStatus enum | Line 335635-335652 |
| PlanFollowupType enum | Line 335713-335721 |
| StartingMessageType enum | Line 335767-335778 |
| ParallelAgentWorkflowSynthesisStrategy | Line 335701-335712 |
| EnsembleStatus enum | Line 335692-335700 |
| SetupVmEnvironmentTool | Line 137359-137438 |
| "Planning next moves" UI text | Line 695809 |
| destroy-after timeout pattern | Line 14774-14776 |
| backgroundComposerEnv settings | Line 182285, 182907, 268817 |

## Summary

Grind Mode is Cursor's time-bounded, phase-aware agent execution mode designed for long-running background tasks. Key characteristics:

1. **Time-bounded execution** with configurable `time_budget_ms`
2. **Two-phase workflow**: PLANNING then EXECUTING
3. **Parallel agent support** via ensemble/fanout strategies
4. **Web-initiated** via dedicated GRIND_WEB source
5. **Progress tracking** through turn counts and commits
6. **VM environment setup** via dedicated tool
7. **Dedicated API** for listing/managing grind sessions

The architecture separates the IDE client (display and configuration) from the server-side agent orchestration, with protobuf messages defining the contract between them.
