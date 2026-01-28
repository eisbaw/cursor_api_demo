---
id: TASK-194
title: Investigate subscription_only_degraded_extended_usage feature flag behavior
status: To Do
assignee: []
created_date: '2026-01-28 06:48'
labels:
  - reverse-engineering
  - feature-flags
  - subscription
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-86-degraded-mode.md
  - reveng_2.3.41/analysis/TASK-116-feature-gates.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
During TASK-86 analysis, discovered a feature flag `subscription_only_degraded_extended_usage` that appears to control behavior for subscription users during extended usage in degraded conditions.

Questions to investigate:
1. What triggers this flag to be enabled?
2. What UI/UX changes occur when enabled?
3. How does this interact with the model degradation status?
4. Is this related to rate limiting or usage caps?

Source location: workbench.desktop.main.js:294804-294811
<!-- SECTION:DESCRIPTION:END -->
