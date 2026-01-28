---
id: TASK-69
title: Map capability types to membership tiers in Cursor authorization
status: Done
assignee: []
created_date: '2026-01-27 14:50'
updated_date: '2026-01-28 00:12'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary
Completed comprehensive analysis of Cursor IDE's capability types and membership tier system.

## Key Findings

### Membership Tiers
Identified 9 membership types in `aiserver.v1.PlanType`:
- FREE, FREE_TRIAL, PRO, PRO_STUDENT, PRO_PLUS, ULTRA, TEAM, ENTERPRISE

### Pricing Matrix
| Tier | Price | Included Amount |
|------|-------|-----------------|
| FREE | $0 | $0 |
| PRO | $20/mo | $20 |
| PRO_PLUS | $60/mo | $70 |
| ULTRA | $200/mo | $400 |

### 35 Composer Capability Types
Documented full enum including: LOOP_ON_LINTS, LOOP_ON_TESTS, MEGA_PLANNER, TOOL_CALL, DIFF_REVIEW, AUTO_CONTEXT, BACKGROUND_COMPOSER, THINKING, MEMORIES, SLACK_INTEGRATION, etc.

### Tier Gating Functions
- `V$l()`: Returns true for ULTRA, PRO, PRO_PLUS, ENTERPRISE, FREE_TRIAL
- `zyh()`: CPP feature gating with `shouldLetUserEnableCppEvenIfNotPro` override

### Error Codes for Tier Restrictions
- ERROR_FREE_USER_RATE_LIMIT_EXCEEDED
- ERROR_PRO_USER_RATE_LIMIT_EXCEEDED
- ERROR_PRO_USER_ONLY

### BugBot Separate Tier System
- BUGBOT_USAGE_TIER_FREE_TIER
- BUGBOT_USAGE_TIER_TRIAL
- BUGBOT_USAGE_TIER_PAID

## Files Created
- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-69-capability-tiers.md`

## Follow-up Tasks Created
- TASK-140: CPP tier gating deep-dive
- TASK-141: Feature gates to tiers mapping
- TASK-142: Upgrade flow documentation
- TASK-143: Rate limiting per tier
- TASK-144: BugBot licensing investigation
<!-- SECTION:FINAL_SUMMARY:END -->
