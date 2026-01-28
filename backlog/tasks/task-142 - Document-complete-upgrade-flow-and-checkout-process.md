---
id: TASK-142
title: Document complete upgrade flow and checkout process
status: To Do
assignee: []
created_date: '2026-01-28 00:11'
labels:
  - reverse-engineering
  - subscription
  - upgrade-flow
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Document the upgrade flow from FREE to ULTRA:
- api/auth/checkoutDeepControl endpoint
- tryImmediateUpgrade function
- upgradeConfirmationModal handling
- Subscription status transitions

Key code locations:
- Line 294954: checkout endpoint
- Line 705032: upgradeToPlanOrGetUrl
- Lines 912108-912118: upgrade flow with OBe function
- Line 1098631: start-subscription-now endpoint
<!-- SECTION:DESCRIPTION:END -->
