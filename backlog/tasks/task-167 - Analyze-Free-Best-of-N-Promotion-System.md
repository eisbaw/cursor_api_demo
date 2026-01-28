---
id: TASK-167
title: Analyze Free Best-of-N Promotion System
status: To Do
assignee: []
created_date: '2026-01-28 06:35'
labels:
  - reverse-engineering
  - best-of-n
  - promotions
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate the promotional system that provides free Best-of-N trials to users.

Key areas to investigate:
- `freeBestOfNPromotion` data structure (trialsUsed, trialsRemaining)
- Storage keys: `freeBestOfN.lastShownAt`, `freeBestOfN.promptCount`, `freeBestOfN.dismissCount`, `freeBestOfN.disabled`
- Analytics events: `composer.bestOfN.freePromotion.triggered`, `.disabled`, `.dismissed`, `.accepted`
- `best_of_n_promotion` and `best_of_n_promotion_config` server config
- How cooldownMs, promptLengthThreshold, promptCountThreshold, dismissLimit are used
- `tryUseBestOfNPromotion` flag in chat submission
<!-- SECTION:DESCRIPTION:END -->
