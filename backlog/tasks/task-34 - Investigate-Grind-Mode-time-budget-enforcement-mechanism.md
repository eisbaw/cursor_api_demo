---
id: TASK-34
title: Investigate Grind Mode time budget enforcement mechanism
status: Done
assignee: []
created_date: '2026-01-27 14:47'
updated_date: '2026-01-28 07:17'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigated time budget enforcement for Grind Mode. Key finding: Enforcement is server-side. The client passes GrindModeConfig (time_budget_ms, start_time_unix_ms, phase) but does not enforce the budget. The server tracks elapsed time and sets CloudAgentWorkflowStatus.EXPIRED when budget is exhausted. Client only reacts to this status change.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Identified GrindModeConfig structure (time_budget_ms, start_time_unix_ms, phase)
- [x] #2 Confirmed time budget enforcement is server-side
- [x] #3 Documented EXPIRED status handling in client
- [x] #4 Created analysis document TASK-34-grind-time-budget.md
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Investigated the time budget enforcement mechanism for Cursor's Grind Mode feature in version 2.3.41.

## Key Findings

1. **Server-Side Enforcement**: The time budget is NOT enforced by the client. The Cursor IDE passes `GrindModeConfig` to the server, which tracks elapsed time and triggers expiration.

2. **GrindModeConfig Structure**:
   - `time_budget_ms` (int64): Total time budget in milliseconds
   - `start_time_unix_ms` (int64, optional): Session start timestamp
   - `phase` (enum): PLANNING (1) or EXECUTING (2)

3. **Expiration Flow**:
   - Server sets `CloudAgentWorkflowStatus.EXPIRED` (enum value 5)
   - Client receives status via streaming updates
   - Client maps to `BackgroundComposerStatus.EXPIRED`
   - UI displays "expired" and filters from active lists

4. **Separate VM Timeout**: There's a distinct VM destruction timeout (default 15 min) via `destroy-after-{N}-minutes` pattern, separate from grind mode budget.

5. **Client Time Display**: Uses `formatElapsedTime()` to show "Working for Xm Ys" but this is based on `createdAt`, not remaining budget.

## Analysis Document
Created: `/reveng_2.3.41/analysis/TASK-34-grind-time-budget.md`
<!-- SECTION:FINAL_SUMMARY:END -->
