---
id: TASK-105
title: Analyze Best-of-N worktree parallel execution and judging mechanism
status: Done
assignee: []
created_date: '2026-01-27 22:36'
updated_date: '2026-01-28 06:35'
labels:
  - reverse-engineering
  - worktree
  - best-of-n
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Deep dive into how multiple parallel worktrees are created for Best-of-N agent runs, how they are compared/judged, and how the winning worktree is selected.

Key areas to investigate:
- worktrees_bon_judge feature flag
- bestOfNJudgeStatus/bestOfNJudgeWinner state
- isBestOfNSubcomposer/isBestOfNParent relationships
- Parallel worktree creation with shared lock lease
- Judge algorithm and comparison logic
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Documented WorktreeLockLease serialization mechanism
- [x] #2 Analyzed parallel subcomposer creation flow
- [x] #3 Documented StreamUiBestOfNJudge RPC protocol
- [x] #4 Analyzed winner selection and non-winner undo logic
- [x] #5 Documented worktree cleanup and protection mechanisms
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Created comprehensive analysis document at `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-105-best-of-n-execution.md`

### Key Findings

1. **WorktreeLockLease System**
   - Serializes worktree creation to prevent git race conditions
   - Uses promise-based queue: each creation waits for previous to complete
   - First parallel agent gets the lock lease, others wait

2. **Parallel Execution Flow**
   - Multi-model detection via comma-separated modelName
   - First model reuses parent composer, others create subcomposers
   - Each subcomposer clones parent's context and capabilities
   - All agents run in parallel after worktree creation

3. **Judging Mechanism**
   - StreamUiBestOfNJudge bidirectional RPC
   - Collects git diffs from each worktree (mergeBase=true)
   - Waits up to 5 seconds for file edits before judging
   - Server returns winner ID and reasoning string

4. **Winner Application**
   - `_undoOtherAppliedBestOfNComposers` cleans up non-winning worktrees
   - Parent tracks all subcomposers via `subComposerIds[]`
   - `selectedSubComposerId` tracks currently viewed child

5. **Configuration**
   - `worktrees_bon_judge` feature flag (default: true)
   - `bestOfNCountPreference` and `bestOfNEnsemblePreferences` user settings
   - Default models: ["composer-1", "claude-4.5-opus-high", "gpt-5.1-codex"]

### Related Tasks Already Exist
- TASK-101 covers worktree isolation architecture
- TASK-57 covers the judge service protobuf schemas
<!-- SECTION:FINAL_SUMMARY:END -->
