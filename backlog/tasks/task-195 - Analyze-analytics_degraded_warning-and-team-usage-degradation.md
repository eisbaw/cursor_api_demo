---
id: TASK-195
title: Analyze analytics_degraded_warning and team usage degradation
status: To Do
assignee: []
created_date: '2026-01-28 06:48'
labels:
  - reverse-engineering
  - analytics
  - team-features
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-86-degraded-mode.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
During TASK-86 analysis, discovered `analytics_degraded_warning` boolean in GetTeamUsageResponse.

This appears to signal when team usage analytics data may be incomplete or delayed. Worth investigating:
1. What server conditions trigger this warning?
2. How is this displayed to team admins?
3. What data might be missing when degraded?
4. Is there a related settings panel or notification?

Source location: workbench.desktop.main.js:274829-274864 (GetTeamUsageResponse)
<!-- SECTION:DESCRIPTION:END -->
