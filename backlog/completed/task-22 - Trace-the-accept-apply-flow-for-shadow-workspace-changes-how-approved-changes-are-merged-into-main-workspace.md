---
id: TASK-22
title: >-
  Trace the accept/apply flow for shadow workspace changes - how approved
  changes are merged into main workspace
status: Done
assignee: []
created_date: '2026-01-27 14:09'
updated_date: '2026-01-28 07:10'
labels: []
dependencies: []
---

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Traced applyChangesFromBgAgent implementation
- [x] #2 Documented shadow workspace service architecture
- [x] #3 Analyzed conflict resolution dialog and handling
- [x] #4 Documented undo flow for applied changes
- [x] #5 Identified Best-of-N agent coordination
- [x] #6 Documented hunk-level accept/reject for inline chat
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Traced the complete accept/apply flow for shadow workspace changes in Cursor IDE 2.3.41.

### Key Findings:

1. **Primary Apply Flow (Background Agent)**: The `applyChangesFromBgAgent()` method at line 1142158-1303 handles applying cloud agent changes to the main workspace. It uses cached diff details when available and falls back to server fetches.

2. **Shadow Workspace Architecture**: Three key services manage shadow workspaces:
   - `IShadowWorkspaceService` (line 831687) - lifecycle management
   - `IShadowWorkspaceServerService` (line 831685) - server operations
   - `INativeShadowWorkspaceManager` (line 1114235) - native platform management

3. **Conflict Resolution**: Uses git-style 3-way merge via `generateAndApplyPatch()`. Detects conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) and presents dialog with options: merge, overwrite, stash, or undo & apply.

4. **Best-of-N Coordination**: Tracks which agents in a Best-of-N group have been applied and can undo other agents before applying new changes.

5. **Undo Support**: `undoAllAppliedChanges()` at line 945576-945707 restores original content, handles renames, and manages created/deleted files.

6. **Hunk-Level Control**: For inline chat (Cmd+K), changes can be accepted/rejected per hunk using HunkData management at line 980000-980065.

### Output:
Analysis written to `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-22-shadow-apply.md`
<!-- SECTION:FINAL_SUMMARY:END -->
