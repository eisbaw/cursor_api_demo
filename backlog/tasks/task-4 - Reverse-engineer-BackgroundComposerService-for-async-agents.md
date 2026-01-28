---
id: TASK-4
title: Reverse engineer BackgroundComposerService for async agents
status: Done
assignee: []
created_date: '2026-01-27 13:38'
updated_date: '2026-01-28 07:01'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate aiserver.v1.BackgroundComposerService which appears to handle asynchronous agent tasks running in the background. Understand how tasks are queued, executed, and how results are delivered. Map the relationship with AddAsyncFollowupBackgroundComposerRequest and similar messages.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Completed comprehensive reverse engineering of the BackgroundComposerService from Cursor IDE 2.3.41.

## Key Findings

### gRPC Service Definition (Line 815697)
- 40+ methods identified for managing cloud-based async agents
- Supports task creation, follow-ups, streaming, PR operations, and lifecycle management
- Both unary and server-streaming patterns used

### Core Message Types Documented
- `StartBackgroundComposerFromSnapshotRequest` - Task creation with full devcontainer config
- `AddAsyncFollowupBackgroundComposerRequest` - Follow-up messages with sync/async modes
- `StreamConversationRequest/Response` - Offset-based conversation streaming
- `HeadlessAgenticComposerResponse` - Agent execution responses

### Client-Side Architecture
- `BackgroundComposerDataService` - Local state management
- `CloudAgentStorageService` - Disk-based caching with blob storage
- Attachment loop management for streaming connections
- Window architecture: main window vs dedicated BC windows

### Status Enums
- `BackgroundComposerStatus`: CREATING, RUNNING, FINISHED, ERROR, EXPIRED
- `CloudAgentWorkflowStatus`: RUNNING, IDLE, ERROR, ARCHIVED, EXPIRED
- `BackgroundComposerSource`: EDITOR, SLACK, WEBSITE, LINEAR, GITHUB, CLI, etc.

### Integration Points
- PR creation via `MakePRBackgroundComposer` and `OpenPRBackgroundComposer`
- Parallel workflows via `StartParallelAgentWorkflow`
- Foreground composer linked via `createdFromBackgroundAgent` field

## Output
Analysis document updated at: `reveng_2.3.41/analysis/TASK-4-background-composer.md`
<!-- SECTION:FINAL_SUMMARY:END -->
