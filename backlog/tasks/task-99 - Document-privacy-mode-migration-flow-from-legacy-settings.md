---
id: TASK-99
title: Document privacy mode migration flow from legacy settings
status: Done
assignee: []
created_date: '2026-01-27 22:36'
updated_date: '2026-01-28 06:54'
labels:
  - reverse-engineering
  - privacy
  - migration
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyze the migration flow from legacy "noStorageMode" boolean to the new granular privacy mode enum system. Includes NeedsPrivacyModeMigration endpoint, reconciliation logic, and grace period handling.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Documented the privacy mode migration flow from legacy `noStorageMode` boolean to the granular `PrivacyMode` enum system in Cursor IDE 2.3.41.

### Key Findings:

1. **Privacy Mode Enum**: 5 levels from UNSPECIFIED(0) to USAGE_CODEBASE_TRAINING_ALLOWED(4), with priority ordering for conflict resolution

2. **Legacy to New Migration**:
   - `inferPrivacyModeFromLegacyValues()` converts `noStorageMode` boolean + `eligibleForSnippetLearning` flags to enum
   - Server reconciliation uses MORE RESTRICTIVE setting when conflicts occur
   - Migration completion tracked via `hasReconciledNewPrivacyModeWithServerOnUpgrade` storage key

3. **Storage Keys Identified**:
   - Legacy: `noStorageMode`, `eligibleForSnippetLearning`, `enoughTimeElapsedSinceOnboarding`
   - New: `cursorai/donotchange/newPrivacyMode2` (JSON serialized), `cursorai/donotchange/privacyMode` (backup)

4. **Grace Period System**:
   - 24-hour onboarding grace period (864e5 ms)
   - Server-controlled `hoursRemainingInGracePeriod`
   - User acknowledgment tracking

5. **Enterprise Override**: Team privacy mode can force settings regardless of user preference via `isEnforcedByTeam`

6. **Backward Compatibility**: Every write to new system also updates legacy `noStorageMode` for code path compatibility

### Analysis Output
- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-99-privacy-migration.md`
<!-- SECTION:FINAL_SUMMARY:END -->
