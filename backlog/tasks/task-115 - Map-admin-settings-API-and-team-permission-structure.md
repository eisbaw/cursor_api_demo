---
id: TASK-115
title: Map admin settings API and team permission structure
status: Done
assignee: []
created_date: '2026-01-27 22:36'
updated_date: '2026-01-28 06:41'
labels:
  - reverse-engineering
  - api
  - admin
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyze the getTeamAdminSettings API and understand the full team permission model. Key questions: What protobuf messages are involved? How does admin override user settings? What is the caching mechanism for admin settings? Reference: /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js line 305947-306020, 276314-276373
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Completed comprehensive analysis of Cursor IDE 2.3.41 admin settings API and team permission structure.

## Key Findings

### DashboardService API (aiserver.v1.DashboardService)
- Mapped 4 admin settings endpoints: `GetTeamAdminSettings`, `GetTeamAdminSettingsOrEmptyIfNotInTeam`, `GetBaseTeamAdminSettings`, `UpdateTeamAdminSettings`
- Additional team management endpoints for privacy mode, roles, SCIM/SSO

### GetTeamAdminSettingsResponse Structure (24 fields)
Core protobuf message at line 276941-277106 containing:
- Model allowlist/blocklist controls
- AutoRunControls with sandboxing
- Integration settings (GitHub, GitLab, Slack, Linear)
- MCP configuration and controls
- Background agent and CLI settings
- Deeplink controls
- BYOK disable flag
- Shared conversation settings

### Permission Enums
- TeamRole: OWNER, MEMBER, FREE_OWNER, REMOVED
- PrivacyMode: NO_STORAGE, NO_TRAINING, USAGE_DATA_TRAINING_ALLOWED, USAGE_CODEBASE_TRAINING_ALLOWED
- SandboxingMode: ENABLED, DISABLED
- NetworkingMode/GitMode: USER_CONTROLLED, ALWAYS_DISABLED
- AllowlistConfig: ALLOWLIST, BLOCKLIST

### Settings Hierarchy
1. Team-level admin settings override user settings
2. DirectoryGroup (SCIM) can have per-group AutoRunControls
3. AdminSettingsService caches settings with 5-minute refresh
4. Fallback to cached settings on network failure

### Caching Mechanism
- Storage key: `adminSettings.cached` and `autorun.cachedAdminSettings`
- Periodic refresh every 300 seconds
- Graceful degradation: keeps existing restrictions on fetch failure

## Files Produced
- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-115-admin-settings.md`

## Follow-up Tasks Created
- TASK-177: Investigate server-side enforcement
- TASK-178: Map SCIM/SSO enterprise authentication flow
- TASK-179: Analyze model allowlist/blocklist server enforcement
<!-- SECTION:FINAL_SUMMARY:END -->
