---
id: TASK-158
title: Investigate inline diff service integration with checkpoints
status: To Do
assignee: []
created_date: '2026-01-28 06:34'
labels:
  - agent
  - persistence
  - diff
dependencies:
  - TASK-88
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The checkpoint system heavily relies on the InlineDiffService for tracking active code changes. During checkpoint creation and revert operations, inline diffs are:
- Tracked in checkpoint.activeInlineDiffs with originalTextDiffWrtV0/newTextDiffWrtV0
- Removed during revert operations
- Restored via addDecorationsOnlyDiff when reverting to a checkpoint

Key areas to investigate:
- InlineDiffService interface and methods
- How diffs are calculated (originalModelDiffWrtV0 format)
- Integration with ComposerCodeBlockService.applyDiffToLines()
- Decoration rendering for inline diffs
<!-- SECTION:DESCRIPTION:END -->
