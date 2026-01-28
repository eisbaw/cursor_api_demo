---
id: TASK-54
title: >-
  Document ParallelAgentWorkflow coordination - investigate multi-agent
  orchestration including FANOUT_VOTING and PAIRWISE_TOURNAMENT strategies
status: Done
assignee: []
created_date: '2026-01-27 14:48'
updated_date: '2026-01-28 07:24'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Comprehensive analysis of ParallelAgentWorkflow coordination including:
- Multi-agent orchestration architecture with parent/child composer relationships
- FANOUT_VOTING and PAIRWISE_TOURNAMENT synthesis strategy implementations
- Workflow phase state machine (STARTING -> CHILDREN_RUNNING -> GATHERING -> SYNTHESIZING -> COMPLETED)
- EnsembleStatus tracking (PARENT, CHILD, UNSPECIFIED)
- UiBestOfNJudgeService for client-side winner selection
- gRPC service methods for workflow control and status streaming
- Synthesis model configuration and default settings
- Analytics events for multi-model submissions
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Analyzed Cursor IDE 2.3.41's ParallelAgentWorkflow coordination system which enables multi-agent orchestration for code generation tasks.

## Key Findings

### Architecture
- **Dual Judging Systems:** Server-side workflow synthesis (via BackgroundComposerService) and client-side UiBestOfNJudgeService
- **Parent/Child Tracking:** Composers marked with `isBestOfNParent` or `isBestOfNSubcomposer` flags
- **Git Worktree Isolation:** Each parallel agent operates in separate worktree

### Synthesis Strategies
1. **SINGLE_AGENT (1):** No parallelism, single model execution
2. **FANOUT_VOTING (2):** Multiple agents vote on best outcome (O(n) comparisons)
3. **PAIRWISE_TOURNAMENT (3):** Bracket-style elimination with progress tracking (O(n log n) comparisons) - DEFAULT

### Coordination Flow
1. Parent composer spawns N child composers
2. Each child uses different model from ensemble config
3. PHASE_CHILDREN_RUNNING: Parallel execution in isolated worktrees
4. PHASE_GATHERING: Collect results (50% min success threshold, 5min timeout)
5. PHASE_SYNTHESIZING: Run selected synthesis strategy
6. Winner selection with reasoning stored in ComposerData

### Default Configuration
- Models: gpt-5.1-codex-high, claude-4.5-sonnet-thinking (repeated 2x for 4 total)
- Synthesis model: gpt-5.1-codex-high
- Strategy: pairwise_tournament

## Output
Analysis document: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-54-parallel-coordination.md`
<!-- SECTION:FINAL_SUMMARY:END -->
