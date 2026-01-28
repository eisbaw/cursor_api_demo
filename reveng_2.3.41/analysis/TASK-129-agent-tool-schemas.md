# TASK-129: Agent-Related Tool Schema Definitions

Analysis of TASK, TASK_V2, AWAIT_TASK, and BACKGROUND_COMPOSER_FOLLOWUP tools from Cursor IDE 2.3.41.

Source: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`

## Executive Summary

Cursor IDE implements a sophisticated agent spawning system through client-side tools. The system has evolved from TASK (v1) to TASK_V2, with additional coordination through AWAIT_TASK and BACKGROUND_COMPOSER_FOLLOWUP. These tools enable hierarchical agent orchestration with parent-child relationships.

---

## Tool Enum Values (ClientSideToolV2)

From line ~104365:

```javascript
// aiserver.v1.ClientSideToolV2 enum
vt.TASK = 32                         // CLIENT_SIDE_TOOL_V2_TASK
vt.AWAIT_TASK = 33                   // CLIENT_SIDE_TOOL_V2_AWAIT_TASK
vt.TASK_V2 = 48                      // CLIENT_SIDE_TOOL_V2_TASK_V2
vt.BACKGROUND_COMPOSER_FOLLOWUP = 24 // CLIENT_SIDE_TOOL_V2_BACKGROUND_COMPOSER_FOLLOWUP
```

---

## 1. TASK (v1) - Original Task Tool

### Schema (aiserver.v1.TaskParams)

Location: Lines ~114604-114668

```typescript
interface TaskParams {
  // Field 1 - Required task description
  task_description: string;      // T: 9 (string)

  // Field 4 - Task title
  task_title: string;            // T: 9 (string)

  // Field 2 - Whether to run async (optional)
  async?: boolean;               // T: 8 (bool)

  // Field 3 - Directories agent can write to
  allowed_write_directories: string[];  // T: 9 (string), repeated

  // Field 5 - Override model selection (optional)
  model_override?: string;       // T: 9 (string)

  // Field 6 - Enable max mode (optional)
  max_mode_override?: boolean;   // T: 8 (bool)

  // Field 7 - UI hint for expansion (optional)
  default_expanded_while_running?: boolean;  // T: 8 (bool)
}
```

### Result Schema (aiserver.v1.TaskResult)

Location: Lines ~114669-114707

```typescript
interface TaskResult {
  result: {
    case: "completedTaskResult" | "asyncTaskResult";
    value: CompletedTaskResult | AsyncTaskResult;
  }
}
```

### CompletedTaskResult

Location: Lines ~114708-114753

```typescript
interface CompletedTaskResult {
  // Field 1 - Summary of completed work
  summary: string;               // T: 9 (string)

  // Field 2 - Files modified by task
  file_results: FileResult[];    // T: O7e (message), repeated

  // Field 3 - Whether user aborted
  user_aborted: boolean;         // T: 8 (bool)

  // Field 4 - Whether subagent encountered error
  subagent_errored: boolean;     // T: 8 (bool)
}
```

### AsyncTaskResult

Location: Lines ~114754-114793

```typescript
interface AsyncTaskResult {
  // Field 1 - ID to reference async task
  task_id: string;               // T: 9 (string)

  // Field 2 - Whether user aborted
  user_aborted: boolean;         // T: 8 (bool)

  // Field 3 - Whether subagent encountered error
  subagent_errored: boolean;     // T: 8 (bool)
}
```

---

## 2. TASK_V2 - Enhanced Task Tool

### Schema (aiserver.v1.TaskV2Params)

Location: Lines ~114819-114864

```typescript
interface TaskV2Params {
  // Field 1 - Task description for display
  description: string;           // T: 9 (string)

  // Field 2 - Full prompt for subagent
  prompt: string;                // T: 9 (string)

  // Field 3 - Type of subagent to spawn
  subagent_type: string;         // T: 9 (string)
  // Values observed: "unspecified", "custom", "computer_use"

  // Field 4 - Model override (optional)
  model?: string;                // T: 9 (string)
}
```

### Result Schema (aiserver.v1.TaskV2Result)

Location: Lines ~114865-114900

```typescript
interface TaskV2Result {
  // Field 1 - ID of spawned agent (optional)
  agent_id?: string;             // T: 9 (string)

  // Field 2 - Whether running in background
  is_background: boolean;        // T: 8 (bool)
}
```

### Task V2 Handler Flow

Location: Lines ~468600-468738

The handler creates a nested composer for the spawned task:

```javascript
// handleToolCallStarted creates params:
const params = new B7e({  // TaskV2Params
    description: args?.description || "",
    prompt: args?.prompt || "",
    subagentType: args?.subagentType?.type.case ?? "unspecified",
    model: args?.model
});

// Creates bubble with status tracking
toolFormer.getOrCreateBubbleId({
    toolCallId: toolCallId,
    toolIndex: 0,
    modelCallId: "",
    toolCallType: vt.TASK_V2,  // 48
    name: "task_v2",
    params: {
        case: "taskV2Params",
        value: params
    }
});

// handleToolCallCompleted processes result
const result = new ZMe({  // TaskV2Result
    agentId: response.agentId,
    isBackground: response.isBackground ?? false
});
```

---

## 3. AWAIT_TASK - Task Synchronization

### Schema (aiserver.v1.AwaitTaskParams)

Location: Lines ~115585-115615

```typescript
interface AwaitTaskParams {
  // Field 1 - Task IDs to wait for
  ids: string[];                 // T: 9 (string), repeated
}
```

### Result Schema (aiserver.v1.AwaitTaskResult)

Location: Lines ~115616-115652

```typescript
interface AwaitTaskResult {
  // Field 1 - Results for completed tasks
  task_results: TaskResultItem[];  // T: JRr (message), repeated

  // Field 2 - IDs that weren't found
  missing_task_ids: string[];    // T: 9 (string), repeated
}

interface TaskResultItem {
  // Field 1 - ID of completed task
  task_id: string;               // T: 9 (string)

  // Field 2 - Result from the task
  result: CompletedTaskResult;   // T: QMe (message)
}
```

### Await Task Handler

Location: Lines ~480752-480815

```javascript
class AwaitTaskHandler {
    async call(params, context, toolCallId, composerId) {
        // Validates IDs provided
        if (params.ids.length === 0) {
            throw new Lc({
                clientVisibleErrorMessage: "No task ids were provided",
                modelVisibleErrorMessage: "await_task was called without any ids"
            });
        }

        // Gets pending tasks from composer state
        const pendingTasks = composerDataService.getComposerData(composerId)?.pendingSubagentTasks;

        // Collects promises for requested task IDs
        const promises = [];
        const waitingIds = [];
        const missingIds = [];

        for (const id of params.ids) {
            const pending = pendingTasks[id];
            if (pending) {
                promises.push(pending.promise);
                waitingIds.push(id);
            } else {
                missingIds.push(id);
            }
        }

        // Awaits all found tasks
        const results = await Promise.all(promises);

        // Cleans up pending tasks after completion
        composerDataService.updateComposerDataAsync(composerId, store => {
            store("pendingSubagentTasks", tasks => {
                for (const id of waitingIds) delete tasks[id];
                return tasks;
            });
        });

        return new AwaitTaskResult({
            taskResults: results.map((result, i) => ({
                taskId: waitingIds[i],
                result: result
            })),
            missingTaskIds: missingIds
        });
    }
}
```

---

## 4. BACKGROUND_COMPOSER_FOLLOWUP

### Schema (aiserver.v1.BackgroundComposerFollowupParams)

Location: Lines ~113555-113589

```typescript
interface BackgroundComposerFollowupParams {
  // Field 1 - Proposed followup message
  proposed_followup: string;     // T: 9 (string)

  // Field 2 - Background composer ID
  bc_id: string;                 // T: 9 (string)
}
```

### Result Schema (aiserver.v1.BackgroundComposerFollowupResult)

Location: Lines ~113590-113624

```typescript
interface BackgroundComposerFollowupResult {
  // Field 1 - The followup that was sent
  proposed_followup: string;     // T: 9 (string)

  // Field 2 - Whether message was actually sent
  is_sent: boolean;              // T: 8 (bool)
}
```

### UI Approval Text

Location: Line ~215330:

```javascript
[vt.BACKGROUND_COMPOSER_FOLLOWUP]: {
    accept: "Send to background composer",
    reject: "Skip",
    waitText: "Waiting for approval"
}
```

---

## 5. Subagent Types (aiserver.v1.SubagentType)

### Enum Values

Location: Lines ~121903-121918

```javascript
// aiserver.v1.SubagentType enum
enum SubagentType {
  SUBAGENT_TYPE_UNSPECIFIED = 0,   // UNSPECIFIED
  SUBAGENT_TYPE_DEEP_SEARCH = 1,   // DEEP_SEARCH
  SUBAGENT_TYPE_FIX_LINTS = 2,     // FIX_LINTS
  SUBAGENT_TYPE_TASK = 3,          // TASK
  SUBAGENT_TYPE_SPEC = 4           // SPEC
}
```

### Agent V1 SubagentType (Oneof)

Location: Lines ~119494-119618

For TASK_V2, subagent type is a oneof message:

```typescript
// agent.v1.SubagentType
interface SubagentType {
  type: {
    case: "unspecified" | "computer_use" | "custom";
    value: SubagentTypeUnspecified | SubagentTypeComputerUse | SubagentTypeCustom;
  }
}

interface SubagentTypeUnspecified {}  // Empty message

interface SubagentTypeComputerUse {}  // Empty message

interface SubagentTypeCustom {
  name: string;  // Custom agent name
}
```

---

## 6. Subagent Info and Return Handling

### SubagentInfo

Location: Lines ~127831-127897

```typescript
interface SubagentInfo {
  // Field 1 - Type of subagent
  subagent_type: SubagentType;   // enum

  // Field 2 - Unique subagent ID
  subagent_id: string;           // T: 9 (string)

  // Field 3-7 - Type-specific params (oneof)
  params: {
    case: "deep_search_params" | "fix_lints_params" | "task_params" | "spec_params";
    value: DeepSearchSubagentParams | FixLintsSubagentParams | TaskSubagentParams | SpecSubagentParams;
  }

  // Field 5 - Parent request for hierarchy
  parent_request_id?: string;    // T: 9 (string)
}
```

### TaskSubagentParams

Location: Lines ~128050-128085

```typescript
interface TaskSubagentParams {
  // Field 1 - Task description
  task_description: string;      // T: 9 (string)

  // Field 2 - Write-allowed directories
  allowed_write_directories: string[];  // T: 9 (string), repeated
}
```

### TaskSubagentReturnValue

Location: Lines ~128086-128115

```typescript
interface TaskSubagentReturnValue {
  // Field 1 - Summary of completed work
  summary: string;               // T: 9 (string)
}
```

### SubagentReturnCall

Location: Lines ~127775-127830

```typescript
interface SubagentReturnCall {
  // Field 1 - Which type of subagent is returning
  subagent_type: SubagentType;   // enum

  // Fields 2-5 - Type-specific return values (oneof)
  return_value: {
    case: "deep_search_return_value" | "fix_lints_return_value" |
          "task_return_value" | "spec_return_value";
    value: DeepSearchSubagentReturnValue | FixLintsSubagentReturnValue |
           TaskSubagentReturnValue | SpecSubagentReturnValue;
  }
}
```

---

## 7. Tool Filtering and Mode Support

### Supported Tools Filtering

Location: Line ~450926:

```javascript
supportedTools: tools.filter(tool =>
    // These tools are excluded from supported list
    excludedSet.has(tool) ? false :

    // WEB_SEARCH conditional on mode
    (mode === "agent" || mode === "chat" || mode === "search") &&
        tool === vt.WEB_SEARCH ? webSearchEnabled :

    // KNOWLEDGE_BASE conditional
    tool === vt.KNOWLEDGE_BASE && !kbEnabled ? false :

    // AWAIT_TASK always excluded from list
    tool === vt.AWAIT_TASK ? false :

    // TASK excluded based on flag
    tool === vt.TASK && taskDisabled ? false :

    // ASK_QUESTION gated
    tool === vt.ASK_QUESTION ?
        experimentService.checkFeatureGate("ask_question_all_modes") || mode === "plan" :

    true
).filter(tool => tool !== vt.MCP)
```

### Agent Mode Enabled Tools

Location: Line ~182311:

```javascript
// Agent mode enables these specific tools
enabledTools: [vt.TASK_V2, vt.APPLY_AGENT_DIFF]
```

---

## 8. Custom Subagent Definition

Location: Lines ~119619-119700

```typescript
interface CustomSubagent {
  // Field 1 - Full path to subagent definition
  full_path: string;             // T: 9 (string)

  // Field 2 - Subagent name
  name: string;                  // T: 9 (string)

  // Field 3 - Description
  description: string;           // T: 9 (string)

  // Field 4 - Tools available to subagent
  tools: string[];               // T: 9 (string), repeated

  // Field 5 - Model to use
  model: string;                 // T: 9 (string)

  // Field 6 - System prompt
  prompt: string;                // T: 9 (string)

  // Field 7 - Permission mode
  permission_mode: CustomSubagentPermissionMode;  // enum
}

enum CustomSubagentPermissionMode {
  CUSTOM_SUBAGENT_PERMISSION_MODE_UNSPECIFIED = 0,
  CUSTOM_SUBAGENT_PERMISSION_MODE_DEFAULT = 1,
  CUSTOM_SUBAGENT_PERMISSION_MODE_READONLY = 2
}
```

---

## 9. Spec Subagent (Planning)

### SpecSubagentParams

Location: Lines ~128116-128145

```typescript
interface SpecSubagentParams {
  // Field 1 - Plan to execute
  plan: string;                  // T: 9 (string)
}
```

### SpecSubagentReturnValue

Location: Lines ~128146-128180

```typescript
interface SpecSubagentReturnValue {
  // Field 1 - Resulting spec
  spec: string;                  // T: 9 (string)
}
```

---

## 10. Parameter/Result Mapping

Location: Lines ~480097-480205:

```javascript
const toolParamMapping = {
    [vt.BACKGROUND_COMPOSER_FOLLOWUP]: {
        paramName: "backgroundComposerFollowupParams",
        returnName: "backgroundComposerFollowupResult"
    },
    [vt.TASK]: {
        paramName: "taskParams",
        returnName: "taskResult"
    },
    [vt.AWAIT_TASK]: {
        paramName: "awaitTaskParams",
        returnName: "awaitTaskResult"
    },
    [vt.TASK_V2]: {
        paramName: "taskV2Params",
        returnName: "taskV2Result"
    },
    // ... other tools
};
```

---

## Key Observations

1. **TASK vs TASK_V2 Evolution**: TASK_V2 is more flexible with typed subagent selection (unspecified, computer_use, custom) vs TASK's simpler model.

2. **Async Coordination**: AWAIT_TASK enables parallel task execution with Promise-based synchronization, tracking pending tasks in composer state.

3. **Background Composer**: BACKGROUND_COMPOSER_FOLLOWUP enables communication between foreground agents and background composers, requiring user approval.

4. **Hierarchical Agents**: The `parent_request_id` field in SubagentInfo enables parent-child agent relationships for complex orchestration.

5. **Tool Gating**: Agent-related tools are conditionally enabled based on mode and feature flags, with AWAIT_TASK notably always excluded from the supported tools list (implying it's used internally).

6. **Custom Subagents**: The system supports user-defined subagents with custom prompts, tools, and permission modes.

---

## Related Files

- `out-build/proto/aiserver/v1/tools_pb.js` - Primary tool definitions
- `out-build/vs/workbench/services/ai/browser/toolsV2/awaitTaskHandler.js` - AWAIT_TASK implementation
- `out-build/vs/workbench/services/agent/browser/toolCallHandlers/` - Tool call handlers

---

Generated: 2026-01-28
