---
id: TASK-15
title: Investigate ParallelAgentWorkflow and synthesis strategies
status: Done
assignee: []
created_date: '2026-01-27 14:08'
updated_date: '2026-01-28 07:02'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigated ParallelAgentWorkflow implementation, synthesis strategies (SINGLE_AGENT, FANOUT_VOTING, PAIRWISE_TOURNAMENT), agent coordination logic, and result aggregation mechanisms in Cursor IDE 2.3.41.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Completed deep analysis of ParallelAgentWorkflow system in Cursor IDE 2.3.41:

### Key Discoveries

1. **Three Synthesis Strategies:**
   - SINGLE_AGENT (1): Use single best result
   - FANOUT_VOTING (2): Multiple agents vote on best outcome
   - PAIRWISE_TOURNAMENT (3): Bracket-style elimination (DEFAULT)

2. **Default Configuration:**
   - Strategy: `pairwise_tournament`
   - Synthesis Model: `gpt-5.1-codex-high`
   - Ensemble Models: GPT + Claude alternating for diversity
   - Gather Timeout: 5 minutes
   - Min Success: 50% of children must succeed

3. **Workflow Phases:** STARTING -> CHILDREN_RUNNING -> GATHERING -> SYNTHESIZING -> COMPLETED

4. **Dual Judge Systems:**
   - Server-side synthesis during tournament phase
   - Client-side UiBestOfNJudgeService for UI comparisons

5. **gRPC Methods:** Part of BackgroundComposerService
   - `StartParallelAgentWorkflow` (Unary)
   - `StreamParallelAgentWorkflowStatus` (ServerStreaming)

### Analysis Output

Written to: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-15-parallel-workflow.md`
<!-- SECTION:FINAL_SUMMARY:END -->
