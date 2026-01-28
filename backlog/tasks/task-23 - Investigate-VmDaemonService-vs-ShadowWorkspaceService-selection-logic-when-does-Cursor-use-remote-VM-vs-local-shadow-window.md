---
id: TASK-23
title: >-
  Investigate VmDaemonService vs ShadowWorkspaceService selection logic - when
  does Cursor use remote VM vs local shadow window
status: Done
assignee: []
created_date: '2026-01-27 14:09'
updated_date: '2026-01-28 07:10'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Investigated VmDaemonService vs ShadowWorkspaceService selection logic in Cursor IDE 2.3.41.

## Key Finding

VmDaemonService and ShadowWorkspaceService are **NOT competing alternatives** - they are independent systems serving different purposes:

1. **ShadowWorkspaceService** (Local)
   - Hidden VS Code window for background code refinement
   - Disabled by default, requires explicit user opt-in
   - Only available when running Cursor locally (not SSH/WSL)
   - Uses Unix socket IPC for communication

2. **VmDaemonService** (Remote Cloud)
   - gRPC service for Background Composer VM pods
   - Runs in Cursor's cloud infrastructure
   - Gated by user privacy mode (requires code storage permission)
   - Three environment modes: dev, prod, fullLocal

## Decision Factors

- **Shadow Workspace**: User setting + local environment requirement
- **VM/Cloud Agent**: Privacy mode + explicit "Cloud" mode selection + GitHub connection

## Analysis Document

Written to: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-23-vm-vs-shadow.md`

Contains:
- Complete gRPC method lists for both services
- Configuration settings and feature flags
- Architecture diagram
- VM pod management details
- Environment selection logic
<!-- SECTION:FINAL_SUMMARY:END -->
