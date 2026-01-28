---
id: TASK-144
title: Investigate BugBot licensing and tier relationship
status: To Do
assignee: []
created_date: '2026-01-28 00:11'
labels:
  - reverse-engineering
  - bugbot
  - tier-gating
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyze how BugBot tiers map to membership tiers:
- BugbotUsageTier enum (FREE_TIER, TRIAL, PAID)
- bugbotLicensesHardLimit and bugbotPlanEnabled
- bugbotWasEnabledInThisBillingCycle tracking
- bugbotGloballyDisabled flag

Key code locations:
- Line 269151: BugbotUsageTier enum
- Line 281828: Individual bugbot settings
- Line 287731: Team bugbot settings
- Line 293717: bugbot_bg_agent_upsell experiment
<!-- SECTION:DESCRIPTION:END -->
