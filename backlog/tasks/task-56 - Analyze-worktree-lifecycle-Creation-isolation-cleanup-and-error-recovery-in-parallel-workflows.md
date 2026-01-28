---
id: TASK-56
title: >-
  Analyze worktree lifecycle: Creation, isolation, cleanup, and error recovery
  in parallel workflows
status: Done
assignee: []
created_date: '2026-01-27 14:49'
updated_date: '2026-01-27 22:36'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Completed comprehensive analysis of the Git worktree lifecycle in Cursor IDE, documenting creation, isolation, cleanup, and error recovery mechanisms.

## Key Findings

### Core Components
- **WorktreeManagerService** (`Ake`): Central service for worktree management with lock leases
- **Worktree class** (`lwt`): Individual worktree instance with git operations
- **WorktreeCleanupCron** (`A1o`): Periodic cleanup based on configurable interval (default 6 hours)

### Lifecycle Phases
1. **Creation**: Lock-based sequential creation, metadata persistence, composer association
2. **Isolation**: Separate git directories, file watchers per worktree, URI mapping
3. **Apply to Main**: Merge-based application with conflict resolution dialog (merge/overwrite/stash)
4. **Cleanup**: Automatic periodic cleanup (max 20 worktrees), protection for active/recent worktrees

### Error Recovery
- Worktree lock lease prevents race conditions
- Metadata validation removes stale entries
- Unknown worktree discovery on startup
- CursorIgnore cleanup on worktree removal

### Configuration
- `worktreeCleanupIntervalHours`: 6 (default)
- `worktreeMaxCount`: 20 (default)
- `.cursor/worktrees.json` for setup scripts

## Deliverables
- Analysis document: `reveng_2.3.41/analysis/TASK-56-worktree-lifecycle.md`
- Follow-up tasks created for deeper investigation:
  - TASK-105: Best-of-N parallel worktree execution
  - TASK-106: Merge conflict resolution algorithm
  - TASK-107: Background agent worktree synchronization
<!-- SECTION:FINAL_SUMMARY:END -->
