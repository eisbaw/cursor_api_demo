---
id: TASK-88
title: Investigate conversation checkpoint system
status: Done
assignee: []
created_date: '2026-01-27 22:35'
updated_date: '2026-01-28 06:33'
labels:
  - agent
  - persistence
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Document the checkpoint mechanism that persists ConversationState/Structure. Includes handleCheckpoint, getLatestCheckpoint, and transcriptWriter functionality observed in the codebase.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Document checkpoint storage mechanism
- [x] #2 Document checkpoint data structures
- [x] #3 Document revert/rollback mechanisms
- [x] #4 Document conversation resumption flow
- [x] #5 Document feature flags and migrations
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Documented the comprehensive checkpoint system in `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-88-checkpoint-system.md`.

### Key Components Identified:

1. **ComposerCheckpointStorageService** - Primary checkpoint storage using `cursorDiskKV` with key pattern `checkpointId:{composerId}:{checkpointId}`

2. **ComposerBlobStore** - Binary blob storage with three key prefixes:
   - `agentKv:blob:` - Raw blob data
   - `agentKv:checkpoint:` - Checkpoint pointers
   - `agentKv:bubbleCheckpoint:` - Per-bubble checkpoints

3. **CheckpointController** - Manages streaming checkpoints during agent execution

4. **CheckpointHandler** - Interface implementing `handleCheckpoint()` and `getLatestCheckpoint()` with transcript writer integration

### Checkpoint Data Structure:
- files[] - File states with diffs from original (originalModelDiffWrtV0)
- nonExistentFiles[] - Tracked but non-existent files
- newlyCreatedFolders[] - Folders created during session
- activeInlineDiffs[] - Currently active inline diffs
- inlineDiffNewlyCreatedResources - Resources created via inline diffs

### Revert Mechanisms:
- Standard revert: Sequential file processing
- Fast checkpoints (feature-gated): Parallel batch processing with rollback support
  - 5 files per batch, 200ms delays
  - Automatic backup and rollback on failure

### Conversation Resumption:
- Uses `resumeAction` to continue from latest checkpoint after connection errors
- Handles queued user messages with checkpoint state

### Feature Flags:
- `fast_checkpoints` - Enables parallel revert algorithm
- `checkpoint_threshold_ms` - Minimum time between auto-checkpoints
- `enable_checkpoint_read/write` - Toggle checkpoint functionality
<!-- SECTION:FINAL_SUMMARY:END -->
