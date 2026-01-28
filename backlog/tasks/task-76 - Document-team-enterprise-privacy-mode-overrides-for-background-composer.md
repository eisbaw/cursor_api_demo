---
id: TASK-76
title: Document team/enterprise privacy mode overrides for background composer
status: Done
assignee: []
created_date: '2026-01-27 14:51'
updated_date: '2026-01-27 22:36'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Completed comprehensive documentation of Cursor's privacy mode system and team/enterprise override mechanisms.

## Key Findings

### Privacy Mode Levels
- `NO_STORAGE` (most restrictive) - Disables Background Agent
- `NO_TRAINING` - Allows Background Agent, no training
- `USAGE_DATA_TRAINING_ALLOWED` - Allows training on usage data
- `USAGE_CODEBASE_TRAINING_ALLOWED` - Full data sharing

### Team/Enterprise Overrides
- Team admins can enforce privacy mode via `SwitchTeamPrivacyMode` endpoint
- Most restrictive setting wins when user belongs to multiple teams
- Enterprise users have settings determined by `shouldHaveGhostModeFromEnterprise()`
- Team enforcement uses `isEnforcedByTeam` flag to block user changes

### Background Composer Impact
- Requires at least `NO_TRAINING` mode (not `NO_STORAGE`)
- UI shows contextual messages based on whether team admin or individual enforces privacy
- Team admins see "Configure Privacy Settings" while non-admins see "Contact admin"

### API Integration
- `x-ghost-mode` header sent with all requests indicates privacy status
- `GetTeamPrivacyModeForced` fetches team settings
- `GetUserPrivacyMode` returns enforcement status and grace period info

## Deliverables
- Analysis document: `/reveng_2.3.41/analysis/TASK-76-privacy-mode.md`
- Follow-up tasks created for deeper investigations (TASK-98, TASK-99, TASK-100)
<!-- SECTION:FINAL_SUMMARY:END -->
