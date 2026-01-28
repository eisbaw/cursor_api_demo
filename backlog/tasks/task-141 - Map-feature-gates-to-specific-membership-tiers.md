---
id: TASK-141
title: Map feature gates to specific membership tiers
status: To Do
assignee: []
created_date: '2026-01-28 00:11'
labels:
  - reverse-engineering
  - tier-gating
  - feature-gates
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create a comprehensive mapping of feature gates to membership tiers. Analyze:
- Which gates are available at FREE tier
- Which gates unlock at PRO
- Which gates require PRO_PLUS or ULTRA
- Enterprise-only gates

Key feature gates to investigate:
- editor_bugbot, editor_bugbot_composer_upsell
- spec_mode
- mcp_discovery
- enable_agent_web_search
- use_usage_limit_policy_experiment

Source: checkFeatureGate calls throughout the codebase
<!-- SECTION:DESCRIPTION:END -->
