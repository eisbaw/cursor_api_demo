---
id: TASK-5
title: Investigate ShadowWorkspaceService sandbox mechanism
status: Done
assignee: []
created_date: '2026-01-27 13:39'
updated_date: '2026-01-28 07:03'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate aiserver.v1.ShadowWorkspaceService which handles shadow workspace operations. This likely provides a sandboxed environment for agent code modifications before applying to the real workspace. Understand how changes are staged, previewed, and committed. Related to VmDaemonService for execution sandbox.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Completed comprehensive analysis of the ShadowWorkspaceService sandbox mechanism in Cursor IDE 2.3.41.

## Key Findings

### Architecture
- ShadowWorkspaceService creates a hidden VS Code window that mirrors the main workspace
- Enables AI to iterate on code changes, get linter feedback, and execute terminal commands in isolation
- Main window and shadow window communicate via Unix domain sockets (or named pipes on Windows)
- Uses a proxy-based RPC mechanism over protobuf for method invocation

### Sandbox Policy System
- Four policy types: UNSPECIFIED, INSECURE_NONE, WORKSPACE_READWRITE, WORKSPACE_READONLY
- Policy structure includes network access control, additional read/write paths, git write blocking, and cursorignore pattern integration
- Policy enrichment flow adds workspace folders and cursorignore mappings before execution

### Key Components
- IShadowWorkspaceService (line 831687): Core orchestration
- IShadowWorkspaceServerService (line 831685): Server-side execution
- INativeShadowWorkspaceManager (line 1114235): Native window management
- Shadow workspace server (line 1128621): Implements all tool handlers

### Features
- Lint feedback loop: Injects deliberate errors to prime linters, then collects real errors after applying changes
- Auto-destruction timer: Shadow workspaces self-close after configurable inactivity (default 15 minutes)
- Extension filtering: Only loads necessary extensions in shadow window
- Dialog skipping: Automatically skips file dialogs in shadow windows
- Edit history integration: Tracks changes via compileGlobalDiffTrajectories

### Relationship with VmDaemonService
- VmDaemonService (line 831475) provides similar API for remote/VM-based execution
- ShadowWorkspaceService is for local execution in hidden window
- Both share common method patterns (tool execution, file operations, auth sharing)

## Files Changed
- Updated /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-5-shadow-workspace.md with comprehensive documentation
<!-- SECTION:FINAL_SUMMARY:END -->
