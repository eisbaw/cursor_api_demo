---
id: TASK-66
title: Document file watcher integration with outdated state detection
status: Done
assignee: []
created_date: '2026-01-27 14:50'
updated_date: '2026-01-28 07:08'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary
Completed comprehensive analysis of file watcher integration and outdated state detection in Cursor IDE 2.3.41.

## Key Findings

### Architecture
- **Dual-layer file watching**: VS Code base layer (universal/non-recursive watchers) plus Cursor-specific ComposerCodeBlockService layer
- **Event-driven system**: All file changes flow through `onDidFilesChange` events with 100ms debouncing
- **Utility process workers**: File watchers run in separate processes for isolation

### Outdated State Detection
- Code blocks track applied/unapplied state
- External file changes trigger `markUriAsOutdated()` method
- Status lifecycle: generating -> applied/pending -> outdated/accepted/rejected
- ETags used for optimistic concurrency in save conflict detection

### Core Components Documented
1. ComposerCodeBlockService (Lines 306320-306470) - AI code block tracking
2. ComposerFileService (Lines 297405-297449) - File service bridge
3. TextFileEditorModel (Lines 874060-874450) - Conflict detection
4. Save conflict handler (Lines 365280-365510) - Resolution UI
5. Configuration watcher (Lines 1116700-1116850) - Settings file watching

## Deliverables
- Analysis document: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-66-file-watcher.md`

## Follow-up Tasks Created
- TASK-245: Investigate race conditions in code block application
- TASK-246: Document ComposerDataService reactive storage architecture
- TASK-247: Analyze file watcher polling configuration
<!-- SECTION:FINAL_SUMMARY:END -->
