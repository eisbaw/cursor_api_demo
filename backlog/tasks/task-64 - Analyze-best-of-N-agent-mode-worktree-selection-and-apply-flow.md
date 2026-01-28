---
id: TASK-64
title: Analyze best-of-N agent mode worktree selection and apply flow
status: Done
assignee: []
created_date: '2026-01-27 14:50'
updated_date: '2026-01-28 06:57'
labels: []
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-64-bon-apply.md
  - reveng_2.3.41/analysis/TASK-101-best-of-n-worktrees.md
  - reveng_2.3.41/analysis/TASK-105-best-of-n-execution.md
  - reveng_2.3.41/analysis/TASK-57-best-of-n-judge.md
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate how Cursor IDE handles Best-of-N agent mode, specifically:
- Worktree selection mechanisms
- Winner application to main workspace
- Non-winner cleanup
- Apply flow from worktree
- User selection of winner
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Documented user selection mechanism (tab-based)
- [x] #2 Analyzed winner application to main workspace
- [x] #3 Documented non-winner cleanup mechanisms
- [x] #4 Traced apply flow from worktree
- [x] #5 Created follow-up tasks for new investigation avenues
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Analyzed the Best-of-N agent mode worktree selection and apply flow in Cursor IDE 2.3.41. 

### Key Findings:

1. **User Selection Mechanism**
   - Tab-based interface for switching between parallel agent results
   - `selectedSubComposerId` tracks the currently viewed solution
   - `resolveComposerIdToSelected()` resolves parent to selected subcomposer when applying

2. **Apply Flow (`_applyWorktreeToCurrentBranchViaMerge`)**
   - Copies files from worktree to main workspace (not git merge)
   - Preserves worktree reference in `reservedWorktree` for undo capability
   - Automatically undoes any other previously-applied Best-of-N results
   - Schedules background cleanup (50ms delay) to avoid UI blocking

3. **Non-Winner Cleanup**
   - `_undoOtherAppliedBestOfNComposers()` reverts other applied results in same group
   - Periodic cleanup cron job (default 6 hours) removes old worktrees
   - Protection logic prevents cleanup of worktrees < 10 minutes old or with running composers

4. **State Management**
   - `isApplyingWorktree` / `isUndoingWorktree` flags for UI progress indicators
   - `appliedDiffs` stores list of applied changes for undo
   - `reservedWorktree` preserves worktree state for potential restoration

5. **Configuration**
   - `worktreeCleanupIntervalHours`: default 6 hours
   - `worktreeMaxCount`: default 20 worktrees
   - `replace_files_on_worktree_apply` feature gate (disabled by default)

### Created Follow-up Tasks:
- TASK-227: Analyze worktree apply merge conflict detection and resolution
- TASK-228: Investigate replace_files_on_worktree_apply feature gate behavior
- TASK-229: Document reviewChangesService file diffing for worktree apply

### Output:
Analysis written to `/reveng_2.3.41/analysis/TASK-64-bon-apply.md`
<!-- SECTION:FINAL_SUMMARY:END -->
