---
id: TASK-107
title: Analyze CursorIgnore service and pattern compilation
status: Done
assignee: []
created_date: '2026-01-27 22:36'
updated_date: '2026-01-28 06:55'
labels: []
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The cursorIgnoreService.getSerializableIgnoreMapping() provides ignore patterns to sandbox policies. Analyze how patterns are loaded, compiled, and passed to the native sandbox layer.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Document CursorIgnore service implementation
- [x] #2 Analyze .cursorignore file parsing logic
- [x] #3 Document pattern compilation engine (XPc/dbe)
- [x] #4 Document matching algorithm and caching
- [x] #5 Analyze admin blocklist integration
- [x] #6 Document sandbox policy integration
- [x] #7 Identify configuration options
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Comprehensive reverse engineering of the CursorIgnore service in Cursor IDE 2.3.41.

### Key Findings

**Pattern Compilation Engine (XPc class)**
- Gitignore-style pattern matching using regex transformation pipeline
- 15+ transformation rules converting glob patterns to RegExp
- Supports negation patterns (!pattern), wildcards (**/*, ?), character classes
- LRU caching for performance (2000 entries)

**Multi-Layer Ignore System**
1. Admin blocklist (teamBlocklist, teamBlockRepos) - highest priority
2. .cursorignore files in workspace directories
3. Global ignore patterns (cursor.general.globalCursorIgnoreList)
4. Hierarchical parent directory scanning (optional)
5. Automatic dot-file blocking (except .cursor)
6. Out-of-workspace file blocking

**File Discovery & Monitoring**
- Searches for **/.cursorignore on workspace load
- Real-time file watcher for add/delete/modify events
- Hierarchical mode scans parent directories (up to 100 levels)
- Symlink handling configurable via server controls

**Sandbox Integration**
- getSerializableIgnoreMapping() provides patterns to sandbox
- enrichPolicyWithCursorIgnore() adds to sandbox policies
- Patterns serialized as JSON for terminal command sandboxing

**Server Configuration**
- CursorIgnoreControls protobuf message
- Controls hierarchicalEnabled and ignoreSymlinks
- Synced via teamAdminSettings

### Files Analyzed
- /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js

### Analysis Document
- /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-107-cursorignore.md
<!-- SECTION:FINAL_SUMMARY:END -->
