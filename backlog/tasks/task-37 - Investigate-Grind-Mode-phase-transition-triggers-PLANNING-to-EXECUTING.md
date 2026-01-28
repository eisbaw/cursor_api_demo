---
id: TASK-37
title: Investigate Grind Mode phase transition triggers (PLANNING to EXECUTING)
status: Done
assignee: []
created_date: '2026-01-27 14:47'
updated_date: '2026-01-28 07:23'
labels: []
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-34-grind-time-budget.md
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-37-grind-phase-triggers.md
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate what triggers the transition from PLANNING phase to EXECUTING phase in Grind Mode.

Related findings from TASK-34:
- Phase is controlled by server via PlanFollowupType (PLAN_FOLLOWUP_TYPE_PLAN=1, PLAN_FOLLOWUP_TYPE_EXECUTE=2)
- Initial phase can be set via StartingMessageType (PLAN_START=2, PLAN_EXECUTE=3)
- No evidence of automatic time-based phase transitions in client
- Phase transitions appear to be server-controlled, not client-initiated

See: /reveng_2.3.41/analysis/TASK-34-grind-time-budget.md
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Investigated PLANNING to EXECUTING phase transition triggers in Cursor's Grind Mode (v2.3.41). Key findings:

### Phase Transition Mechanisms

1. **StartingMessageType** (Line 335767-335778): Determines initial phase when starting a session
   - `STARTING_MESSAGE_TYPE_PLAN_START` (2): Starts in PLANNING
   - `STARTING_MESSAGE_TYPE_PLAN_EXECUTE` (3): Starts in EXECUTING

2. **PlanFollowupType** (Line 335713-335721): Controls phase transitions in followup requests
   - `PLAN_FOLLOWUP_TYPE_PLAN` (1): Stay in/return to PLANNING
   - `PLAN_FOLLOWUP_TYPE_EXECUTE` (2): Transition to EXECUTING

3. **GrindModeConfig.Phase** (Line 337750-337758): Enum values stored in state
   - `PHASE_UNSPECIFIED` (0)
   - `PHASE_PLANNING` (1)
   - `PHASE_EXECUTING` (2)

### Key Findings

- **No automatic time-based phase transitions** - All transitions require explicit user action
- **Server-controlled** - Client requests transitions via `planFollowupType`, server updates `CloudAgentState.grindModeConfig.phase`
- **Dual representation** - Phase stored as enum in config AND as string in `BackgroundComposer.grindPhase`
- **Persistent state** - Phase is part of `CloudAgentState`, survived session recovery

### Phase Transition Flow

```
User approves plan
    → Client sends AddAsyncFollowupBackgroundComposerRequest
        → planFollowupType = PLAN_FOLLOWUP_TYPE_EXECUTE (2)
    → Server updates CloudAgentState.grindModeConfig.phase = EXECUTING (2)
    → Client receives updated state via StreamConversationResponse
```

See analysis: `/reveng_2.3.41/analysis/TASK-37-grind-phase-triggers.md`
<!-- SECTION:FINAL_SUMMARY:END -->
