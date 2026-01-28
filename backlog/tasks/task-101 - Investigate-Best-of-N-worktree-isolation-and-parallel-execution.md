---
id: TASK-101
title: Investigate Best-of-N worktree isolation and parallel execution
status: Done
assignee: []
created_date: '2026-01-27 22:36'
updated_date: '2026-01-28 07:30'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate how Cursor IDE's Best-of-N feature handles worktree isolation and parallel agent execution. Analyze the decompiled source to understand:
- How git worktrees are created and managed for parallel agents
- Resource isolation mechanisms between parallel runs
- Concurrent agent execution limits and orchestration
- File system isolation and conflict prevention
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Document worktree isolation mechanism
- [x] #2 Identify parallel agent execution limits
- [x] #3 Analyze git worktree management patterns
- [x] #4 Document resource isolation approaches
- [x] #5 Document concurrent agent configuration
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary
Comprehensive analysis of Cursor IDE's Best-of-N worktree isolation and parallel agent execution mechanisms completed.

## Key Findings

### Worktree Isolation Architecture
- Each parallel agent gets its own git worktree in `~/.cursor/worktrees/<workspace>/<worktree-id>/`
- Worktrees provide complete filesystem isolation preventing file conflicts during concurrent execution
- Maximum 20 worktrees per workspace (configurable via settings)
- Automatic cleanup cron runs every 6 hours (configurable)

### Parallel Execution Coordination
- Up to 8 agents can run in parallel (UI limit)
- Worktree creation is serialized via WorktreeLockLease despite parallel agent execution
- Only first agent in Best-of-N group receives the lock lease; others wait in sequence
- Promise.allSettled pattern ensures all agents complete even if some fail

### Server-Side Configuration
- `parallel_agent_ensemble_config`: Controls models, 5-minute gather timeout, 50% minimum success rate
- `parallel_agent_synthesis_config`: Pairwise tournament strategy by default using gpt-5.1-codex-high
- Server-controlled configs allow A/B testing of synthesis strategies

### Workflow Phases
1. STARTING - Workflow initialization
2. CHILDREN_RUNNING - Parallel agents executing  
3. GATHERING - Collecting results from agents
4. SYNTHESIZING - Comparing/judging results
5. COMPLETED - Winner selected

### Best-of-N Judging
- UiBestOfNJudgeService collects git diffs from each worktree
- Diffs sent to server via StreamUiBestOfNJudge BiDi streaming
- Winner marked with bestOfNJudgeWinner flag and reasoning stored

### Additional Isolation: BcIdWindow
- Background agents run in special BcId Windows with modified behavior
- Repository tracking skipped in BcIdWindow mode
- Provides visual separation for background agent contexts

## Analysis Document
/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-101-bon-isolation.md

## Follow-up Tasks Created
- TASK-299: Investigate WorktreeLockLease race condition prevention
- TASK-300: Investigate BcIdWindow isolation mechanism for background agents
<!-- SECTION:FINAL_SUMMARY:END -->
