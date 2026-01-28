---
id: TASK-95
title: Analyze Todo dependency resolution and ordering logic
status: Done
assignee: []
created_date: '2026-01-27 22:35'
updated_date: '2026-01-28 00:12'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Analyzed the Todo dependency resolution and ordering logic in Cursor's agent system. The implementation uses a simple dependency satisfaction algorithm rather than a complex graph-based approach.

## Key Findings

### Dependency Resolution Algorithm (findReadyTasks)
- **Location**: Line ~484173 in workbench.desktop.main.js
- **Algorithm**: Simple set-based dependency check - builds a Set of completed task IDs, then filters for pending tasks where ALL dependencies are in the completed set
- **Complexity**: O(n * m) where n = todos, m = avg dependencies
- **Limitations**: No cycle detection, no topological ordering, no unreachable task detection

### Data Structures
- **aiserver.v1.TodoItem** (simple): content, status (string), id, dependencies
- **agent.v1.TodoItem** (extended): adds created_at, updated_at timestamps, status as enum

### Status Values
- `pending` (1), `in_progress` (2), `completed` (3), `cancelled` (4)

### Subagent Integration
- `readyTaskIds` only returned when mode is "aggressive" (configurable)
- `needsInProgressTodos` flag signals agent should mark a task in_progress

### Plan Persistence
- Todo status syncs to plan files via syncTodoUpdatesToFile
- Supports assigning todos to new agents via buildSelectedTodosInNewAgent

## Created Follow-up Tasks
- TASK-146: Circular dependency handling
- TASK-147: Subagent todo status coordination  
- TASK-148: Todo grouping logic in UI

## Deliverable
Analysis document: reveng_2.3.41/analysis/TASK-95-todo-dependencies.md
<!-- SECTION:FINAL_SUMMARY:END -->
