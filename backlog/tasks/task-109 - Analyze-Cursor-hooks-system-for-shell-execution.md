---
id: TASK-109
title: Analyze Cursor hooks system for shell execution
status: Done
assignee: []
created_date: '2026-01-27 22:36'
updated_date: '2026-01-28 06:54'
labels: []
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The beforeShellExecution hook can block or force approval of commands. Investigate hook registration, execution flow, and integration with Rules for AI features.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Document all 12 hook types and their purposes
- [x] #2 Explain 4-tier configuration hierarchy
- [x] #3 Detail hook execution flow and payload format
- [x] #4 Document response validators and permission model
- [x] #5 Analyze team hooks backend integration
- [x] #6 Identify security controls and workspace trust
- [x] #7 Document stop hook auto-loop behavior
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary
Completed comprehensive analysis of Cursor IDE 2.3.41 hooks system. The hooks system enables security policies, observability, and workflow customization by intercepting agent actions at 12 distinct hook points.

## Key Findings

### Hook System Architecture
- 12 hook types covering shell execution, MCP tools, file operations, and agent lifecycle
- 4 configuration sources: Enterprise > Team > Project > User (hierarchical execution)
- Configuration via hooks.json files at system, user, and project levels
- Team hooks fetched from backend API and stored in ~/.cursor/managed/

### Hook Execution Flow
- Hooks receive JSON payload via stdin (base64-encoded)
- Scripts execute sequentially, first valid response wins
- Response validators enforce permission model: allow/deny/ask
- Execution logged with last 100 entries retained

### Shell Execution Hooks
- beforeShellExecution: Can block commands with deny permission
- afterShellExecution: Post-execution observability with output/duration
- Integration with sandbox policy system
- Agent receives explicit "do not work around" warning when blocked

### Security Features
- Project hooks require workspace trust
- Enterprise hooks in protected system directories
- Team hooks require user acknowledgment on first use
- Stop hook loop protection (max 5 iterations)

### Backend Integration
- TeamHook protobuf schema for team-managed hooks
- 30-minute refresh interval for team hooks
- OS-specific filtering for cross-platform support

## Analysis Document
Written to: /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-109-hooks-system.md
<!-- SECTION:FINAL_SUMMARY:END -->
