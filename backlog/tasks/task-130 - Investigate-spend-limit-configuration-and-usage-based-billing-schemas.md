---
id: TASK-130
title: Investigate spend limit configuration and usage-based billing schemas
status: Done
assignee: []
created_date: '2026-01-28 00:10'
updated_date: '2026-01-28 07:28'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analysis of Cursor IDE 2.3.41 spend limit configuration and usage-based billing schemas. Documented protobuf schemas for hard limits, spend limits, usage tracking, billing cycles, team credits, and client-side usage data services.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Completed Investigation

Analyzed Cursor IDE 2.3.41's spend limit and usage-based billing system from `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`.

### Key Findings

**Core Protobuf Schemas Documented:**
- `GetHardLimitRequest/Response` - Retrieve hard limit configuration
- `SetHardLimitRequest/Response` - Configure spend limits with 8 fields including per-user limits
- `GetCurrentPeriodUsageRequest/Response` - Billing period usage with PlanUsage and SpendLimitUsage sub-messages
- `ConfigureSpendLimitAction` - Action for prompting limit configuration from errors
- Service account spend limit schemas (`Get/SetServiceAccountSpendLimit`)
- `TeamCreditsService` with get/set/clear credit operations
- `TokenUsage` schema tracking input/output/cache tokens and cost in cents

**Usage Event Tracking:**
- `UsageEventKind` enum with 11 categories (usage-based, API key, included in Pro/Plus/Business/Ultra, BugBot, free credit)
- `UsageEventDetails` with feature-specific schemas (Chat, Composer, CmdK, BugBot, etc.)

**Limit Enforcement:**
- `ScenarioType` enum: Plan limit, Tier 1-3 limits, On-demand limit, Team on-demand, Monthly limit, Pooled limit
- Slow pool mechanism for users over limits (degraded service instead of hard blocks)
- `displayThreshold` configurable (default 50%) for when to show usage indicators

**Client-Side Implementation:**
- `UsageDataService` with 5-minute refresh interval, 30-second cache
- Reactive state management for planUsageData, spendLimitUsageData
- UI for configuring limits with predefined options ($0, $20, $50, $100 above current)

**Output:** Analysis document at `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-130-spend-limits.md`
<!-- SECTION:FINAL_SUMMARY:END -->
