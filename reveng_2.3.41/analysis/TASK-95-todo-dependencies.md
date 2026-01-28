# TASK-95: Todo Dependency Resolution and Ordering Logic

**Source:** `reveng_2.3.41/beautified/workbench.desktop.main.js`
**Analysis Date:** 2026-01-28
**Related:** TASK-26-tool-schemas.md

## Overview

The Cursor agent uses a todo system for tracking task progress during agentic operations. This document analyzes the dependency resolution algorithm, todo ordering logic, and the relationship between todo items and subagent execution.

---

## Todo Item Data Structures

### aiserver.v1.TodoItem (Simple Version)
**Location:** Line ~115743

The simpler version used in client-side tool calls:

```protobuf
message TodoItem {
  string content = 1;       // Todo description text
  string status = 2;        // String status: "pending"|"in_progress"|"completed"|"cancelled"
  string id = 3;            // Unique identifier (e.g., "todo-1706483200000-abc123xyz")
  repeated string dependencies = 4;  // Array of task IDs this depends on
}
```

### agent.v1.TodoItem (Extended Version)
**Location:** Line ~224312

The extended version with timestamps used in agent state:

```protobuf
enum TodoStatus {
  TODO_STATUS_UNSPECIFIED = 0;
  TODO_STATUS_PENDING = 1;
  TODO_STATUS_IN_PROGRESS = 2;
  TODO_STATUS_COMPLETED = 3;
  TODO_STATUS_CANCELLED = 4;
}

message TodoItem {
  string id = 1;
  string content = 2;
  TodoStatus status = 3;        // Enum instead of string
  int64 created_at = 4;         // Unix timestamp milliseconds
  int64 updated_at = 5;         // Unix timestamp milliseconds
  repeated string dependencies = 6;
}
```

---

## Dependency Resolution Algorithm

### findReadyTasks Function
**Location:** Line ~484173

The core dependency resolution logic is implemented in `TodoWriteHandler.findReadyTasks()`:

```javascript
findReadyTasks(todos) {
    // Step 1: Build a set of all completed task IDs
    const completedIds = new Set(
        todos
            .filter(todo => todo.status === "completed")
            .map(todo => todo.id)
    );

    // Step 2: Find pending tasks where ALL dependencies are completed
    return todos
        .filter(todo =>
            todo.status === "pending" &&
            todo.dependencies !== undefined &&
            todo.dependencies.every(depId => completedIds.has(depId))
        )
        .map(todo => todo.id);
}
```

### Algorithm Analysis

**Type:** Simple dependency satisfaction check (NOT a topological sort)

**Key Characteristics:**
1. **No graph construction** - Does not build an explicit dependency graph
2. **Single-pass resolution** - Only identifies immediately ready tasks
3. **Pending-only filtering** - Only considers tasks with `status === "pending"`
4. **All-or-nothing dependencies** - Task is ready only if ALL dependencies are completed

**Time Complexity:** O(n * m) where n = number of todos, m = average dependencies per todo

**Limitations:**
- Does not detect circular dependencies
- Does not compute full execution order
- Does not identify unreachable tasks (depending on non-existent IDs)

---

## Todo Write Handler Flow

### TodoWriteHandler.call()
**Location:** Line ~484088

```javascript
async call(params, token, toolCallId, composerId) {
    // 1. Map incoming todos to internal format
    const mappedTodos = params.todos.map(todo => ({
        id: todo.id,
        content: todo.content,
        status: todo.status,
        dependencies: todo.dependencies
    }));

    // 2. Handle merge mode (update existing vs replace all)
    let finalTodos;
    if (params.merge === true) {
        const existingTodos = [...currentTodos];
        for (const newTodo of mappedTodos) {
            const existingIdx = existingTodos.findIndex(t => t.id === newTodo.id);
            if (existingIdx >= 0) {
                // Update existing: preserve original if new value is empty
                const existing = existingTodos[existingIdx];
                existingTodos[existingIdx] = new TodoItem({
                    id: newTodo.id,
                    content: newTodo.content || existing.content,
                    status: newTodo.status || existing.status,
                    dependencies: newTodo.dependencies.length > 0
                        ? newTodo.dependencies
                        : existing.dependencies
                });
            } else {
                existingTodos.push(newTodo);
            }
        }
        finalTodos = existingTodos.map(t => new TodoItem(t));
    } else {
        // Replace mode: new todos replace all existing
        finalTodos = mappedTodos.map(t => new TodoItem(t));
    }

    // 3. Update composer data store
    composerDataService.updateComposerData(composerId, { todos: finalTodos });

    // 4. Sync status changes to plan file (if plan exists)
    const statusMap = new Map();
    for (const todo of mappedTodos) {
        statusMap.set(todo.id, todo.status);
    }
    await composerPlanService.syncTodoUpdatesToFile(composerId, statusMap);

    // 5. Find ready tasks (dependency resolution)
    const readyTaskIds = this.findReadyTasks(finalTodos);

    // 6. Check if aggressive subagent mode is enabled
    const isAggressive = (configurationService.getValue(subagentConfig) || "conservative") === "aggressive";

    // 7. Check if agent needs to mark a task as in_progress
    const needsInProgressTodos = finalTodos.some(t => t.status === "pending")
        && finalTodos.every(t => t.status !== "in_progress");

    // 8. Return result
    return new TodoWriteResult({
        success: true,
        readyTaskIds: isAggressive ? readyTaskIds : [],
        needsInProgressTodos: needsInProgressTodos,
        finalTodos: finalTodos,
        initialTodos: currentTodos,
        wasMerge: params.merge === true
    });
}
```

---

## Subagent Configuration

### Configuration Key
**Location:** Line ~450782

```javascript
{
    type: "string",
    enum: ["off", "conservative", "aggressive"],
    default: "conservative",
    description: "Controls subagent behavior: Off (disabled), Conservative (enabled without aggressive prompting), Aggressive (enabled with aggressive prompting)"
}
```

### Ready Task ID Behavior

| Mode | readyTaskIds returned | Description |
|------|----------------------|-------------|
| `off` | `[]` | Subagents disabled |
| `conservative` | `[]` | Subagents enabled but no aggressive prompting |
| `aggressive` | Ready task IDs | Agent is prompted to work on ready tasks |

---

## Todo ID Generation

**Location:** Line ~740286

Todo IDs are generated using a timestamp-based pattern:

```javascript
id: `todo-${Date.now()}-${Math.random().toString(36).substr(2,9)}`
// Example: "todo-1706483200000-k5x9m2p1q"
```

This ensures:
- Chronological ordering by creation time
- Uniqueness via random suffix
- Human-readable format

---

## needsInProgressTodos Flag

**Location:** Line ~484135

The `needsInProgressTodos` flag is set when:
1. At least one todo has `status === "pending"` AND
2. No todo has `status === "in_progress"`

```javascript
const needsInProgressTodos =
    finalTodos.some(t => t.status === "pending") &&
    finalTodos.every(t => t.status !== "in_progress");
```

This flag signals to the AI that it should mark a task as `in_progress` before starting work, ensuring the UI reflects the current activity.

---

## Plan Integration

### syncTodoUpdatesToFile
**Location:** Line ~309393

When todos are updated, status changes are synced to the plan file:

```javascript
async syncTodoUpdatesToFile(composerId, statusMap) {
    if (statusMap.size === 0) return;

    const planUri = await this.getExistingPlanUri(composerId);
    if (!planUri) return;

    const plan = await this._planStorageService.loadPlanByUri(planUri);
    const existingTodos = plan.metadata.todos ?? [];

    if (existingTodos.length === 0) return;

    let hasChanges = false;
    const updatedTodos = existingTodos.map(todo => {
        const newStatus = statusMap.get(todo.id);
        if (newStatus !== undefined && newStatus !== todo.status) {
            hasChanges = true;
            return { ...todo, status: newStatus };
        }
        return todo;
    });

    if (hasChanges) {
        await this._planStorageService.updatePlanMetadata(planUri, {
            todos: updatedTodos
        }, composerId);
    }
}
```

### buildSelectedTodosInNewAgent
**Location:** Line ~309428

Todos can be assigned to a new agent:

```javascript
async buildSelectedTodosInNewAgent(planUri, selectedTodos) {
    // Create new composer in agent mode
    const result = await this._composerService.createComposer({
        unifiedMode: "agent",
        openInNewTab: true
    });

    // Set todos on the new composer
    composerDataService.updateComposerData(handle, {
        todos: selectedTodos
    });

    // Build prompt with assigned todos
    const todoIds = selectedTodos.map(t => t.id).join(", ");
    const todoList = selectedTodos.map((t, i) =>
        `${i+1}. [${t.id}] ${t.content}`
    ).join("\n");

    const prompt = `Implement the following to-dos from the plan...
    You have been assigned the following ${selectedTodos.length} to-do(s) with IDs: ${todoIds}

    ${todoList}

    These to-dos have already been created. Do not create them again.
    Mark them as in_progress as you work, starting with the first one.
    Don't stop until you have completed all the assigned to-dos.`;

    await this._composerChatService.submitChatMaybeAbortCurrent(composerId, prompt);
}
```

---

## Cloud Agent State

### turnStartTodoIds
**Location:** Line ~342849

The cloud agent tracks which todos were active at the start of each turn:

```protobuf
message CloudAgentState {
  // ... other fields ...
  repeated string turn_start_todo_ids = 20;
  // ... other fields ...
}
```

This enables tracking todo changes across conversation turns.

---

## UI Rendering

### Todo Status Visualization
**Location:** Line ~740524-740542

The UI renders todos with visual indicators based on status:

```javascript
const statusClasses = {
    "plan-todo-indicator-pending": !isSelected && todo.status === "pending",
    "plan-todo-indicator-in-progress": todo.status === "in_progress",
    "plan-todo-indicator-completed": !isSelected && todo.status === "completed",
    "plan-todo-indicator-cancelled": !isSelected && todo.status === "cancelled"
};
```

---

## Key Findings

1. **Simple Dependency Model**: The dependency resolution is a straightforward "all dependencies must be completed" check, not a complex graph algorithm.

2. **No Cycle Detection**: The algorithm does not detect or prevent circular dependencies. A todo depending on itself or a cycle of todos would never become "ready."

3. **Merge vs Replace**: The `merge` flag controls whether new todos update existing ones (preserving IDs) or replace the entire list.

4. **Subagent Integration**: Ready task IDs are only returned in "aggressive" mode to prompt the agent to work on unblocked tasks.

5. **Plan Persistence**: Todo status changes are persisted to plan files, enabling cross-session continuity.

6. **Status Enforcement**: The `needsInProgressTodos` flag ensures the agent maintains proper state by marking tasks as in_progress.

---

## Future Investigation Needed

- **TASK-95a**: Investigate how circular dependencies are handled (or not) in the UI
- **TASK-95b**: Analyze how subagent tasks coordinate todo status updates
- **TASK-95c**: Examine the todo grouping logic in composer rendering
