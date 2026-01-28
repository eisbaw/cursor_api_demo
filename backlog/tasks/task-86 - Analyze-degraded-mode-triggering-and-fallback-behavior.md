---
id: TASK-86
title: Analyze degraded mode triggering and fallback behavior
status: Done
assignee: []
created_date: '2026-01-27 22:34'
updated_date: '2026-01-28 06:47'
labels:
  - reverse-engineering
  - reliability
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-39-stream-resumption.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The WelcomeMessage includes an is_degraded_mode flag that disables idempotent streaming guarantees.

Investigate:
1. What server conditions trigger degraded mode?
2. How does client handle ongoing operations when degraded mode is signaled mid-stream?
3. Can degraded mode be exploited to bypass idempotency protections?
4. What user-visible effects occur in degraded mode?
5. Is there telemetry on degraded mode frequency?

Source location: workbench.desktop.main.js:488870-488875
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Documented what triggers degraded mode (server-signaled via WelcomeMessage)
- [x] #2 Analyzed client handling of ongoing operations when degraded mode is signaled
- [x] #3 Identified potential security implications of idempotency protection bypass
- [x] #4 Documented user-visible effects in degraded mode (warning icons, disabled models)
- [x] #5 No telemetry tracking for degraded mode frequency found in client code
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Analyzed degraded mode triggering and fallback behavior in Cursor IDE 2.3.41.

### Key Findings

**Two Distinct Degraded Mode Types:**

1. **Idempotent Stream Degraded Mode** (server-signaled)
   - Transmitted via `is_degraded_mode` boolean in WelcomeMessage protobuf
   - Disables stream reconnection/resumption guarantees
   - Clears `idempotentStreamState` preventing chunk replay
   - Errors are re-thrown immediately without retry
   - No client-side recovery mechanism - requires new connection

2. **Model Degradation Status** (per-model)
   - Three-state enum: UNSPECIFIED, DEGRADED, DISABLED
   - DEGRADED: Model selectable but shows warning icon (warningTwo)
   - DISABLED: Model completely unselectable in UI
   - Tooltip data can include warning text via `secondaryWarningText`

**Additional Degradation Mechanisms:**
- `analytics_degraded_warning` in GetTeamUsageResponse
- `subscription_only_degraded_extended_usage` feature flag

**Security Considerations:**
- Event ID requirement relaxed in degraded mode (potential bypass vector)
- Replay protection cleared when degraded mode activates
- Server has unilateral control over degraded mode activation

### Source Locations
- WelcomeMessage: lines 122228-122262
- Degraded mode handling: lines 488870-488922
- DegradationStatus enum: lines 165057-165067
- Model UI handling: lines 712770-712930

### Output
Analysis written to: `reveng_2.3.41/analysis/TASK-86-degraded-mode.md`
<!-- SECTION:FINAL_SUMMARY:END -->
