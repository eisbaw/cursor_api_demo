---
id: TASK-214
title: Analyze team privacy mode enforcement and workspace-level overrides
status: To Do
assignee: []
created_date: '2026-01-28 06:54'
labels:
  - reverse-engineering
  - privacy
  - enterprise
dependencies:
  - TASK-99
references:
  - reveng_2.3.41/analysis/TASK-99-privacy-migration.md
  - reveng_2.3.41/beautified/workbench.desktop.main.js
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Deep-dive into the enterprise/team privacy mode enforcement system. This includes:

1. The `shouldHaveGhostModeFromEnterprise()` method and how it determines team-forced privacy
2. The `GetTeamPrivacyModeForced` RPC endpoint
3. The `SwitchTeamPrivacyMode` RPC endpoint for team administrators
4. How workspace-level privacy settings interact with user-level settings
5. The `workspaceEligibleForSnippetLearning` vs `eligibleForSnippetLearning` distinction
6. Team migration opt-out functionality via `UpdateTeamPrivacyModeMigrationOptOut`

Related to TASK-99 findings - the interaction between team enforcement and individual user settings is complex with multiple fallback paths.
<!-- SECTION:DESCRIPTION:END -->
