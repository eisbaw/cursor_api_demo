---
id: TASK-116
title: Analyze experiment service and feature gates system
status: Done
assignee: []
created_date: '2026-01-27 22:36'
updated_date: '2026-01-28 06:34'
labels:
  - reverse-engineering
  - feature-flags
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate how the experimentService and feature gates work. Key questions: How are feature gates like 'mcp_allowlists' controlled? What is the source of feature gate values (server, local config)? How does checkFeatureGate work? Reference: /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js line 477079
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete: Experiment Service and Feature Gates System

### Key Findings

1. **Statsig Integration**: Cursor uses Statsig as the backend for feature flags, A/B tests, and dynamic configs. The client receives bootstrap configuration from the server via gRPC `bootstrapStatsig` endpoint and caches it locally.

2. **Three Configuration Types**:
   - **Feature Gates (Pke)**: ~200+ boolean flags with client/default properties
   - **Experiments (UZ)**: A/B tests with multiple parameters and fallback values
   - **Dynamic Configs (Yue)**: Server-configurable JSON objects for complex settings

3. **Gate Evaluation Priority**:
   1. Check for local overrides (dev mode only)
   2. Fall back to Statsig evaluation
   3. Use default values if Statsig unavailable

4. **Override System**: Developers can override gates locally when:
   - Running in test mode (enableSmokeTestDriver)
   - Non-production build
   - Server sets `isDevUser` context

5. **Notable Hidden Features** (gates with default=false):
   - `cloud_agent_computer_use` - Computer use capability
   - `parallel_agent_workflow` - Parallel agent execution
   - `enable_skills` - Skill system
   - `shared_chats` - Chat sharing
   - `rules_v2` - New rules system

### Analysis Document
`/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-116-feature-gates.md`

### Key Files Referenced
- Line 293382: Feature gate definitions (Pke)
- Line 295926: ExperimentService implementation
- Line 973679: Bootstrap refresh from server
<!-- SECTION:FINAL_SUMMARY:END -->
