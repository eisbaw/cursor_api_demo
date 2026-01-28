# TASK-74: CreatePlan Tool Schemas and Management Analysis

## Overview

The CreatePlan tool enables Cursor's AI agent to create and manage task plans. Plans are stored as markdown files with YAML frontmatter containing structured metadata (name, overview, todos). The system supports two modes: single-plan-per-composer (default) and multi-plan mode (feature-gated).

## Protobuf Type Definitions

### Two Protocol Domains

The Plan system uses two separate protobuf namespaces:

1. **aiserver.v1** - Server-side API (params/results for streaming)
2. **agent.v1** - Agent-side tool calls (tool call structure)

---

## aiserver.v1 Schemas (Server-side)

### aiserver.v1.CreatePlanParams
**Location:** Line 116607

```typescript
{
  plan: string,           // Full markdown plan content
  title: string,          // Plan title
  summary: string,        // Plan summary
  steps: Step[],          // Structured steps (deprecated?)
  old_str: string,        // For plan modifications
  new_str: string,        // For plan modifications
  name: string,           // Plan file name
  todos: TodoItem[],      // List of todo items
  overview: string,       // Plan overview
  is_spec: boolean        // Whether plan is a specification
}
```

### aiserver.v1.CreatePlanResult
**Location:** Line 116686

```typescript
{
  result: oneof {
    accepted: CreatePlanResult.Accepted,
    rejected: CreatePlanResult.Rejected,
    modified: CreatePlanResult.Modified
  },
  plan_uri: string       // URI to the created plan file
}
```

### aiserver.v1.CreatePlanResult.Accepted
**Location:** Line 116734

```typescript
{
  final_todos: TodoItem[]  // The accepted todo list
}
```

### aiserver.v1.CreatePlanResult.Rejected
**Location:** Line 116765

```typescript
{}  // Empty - just indicates rejection
```

### aiserver.v1.CreatePlanResult.Modified
**Location:** Line 116790

Fields not fully visible but contains modified plan data.

### aiserver.v1.Step
**Location:** Line 116551

```typescript
{
  id: string,              // Step identifier
  title: string,           // Step title
  description: string,     // Step description
  instructions: string,    // Detailed instructions
  prerequisites: string[], // IDs of prerequisite steps
  sub_composer_id: string  // ID of sub-agent handling this step
}
```

### aiserver.v1.TodoItem (JR)
**Location:** Line 115751

```typescript
{
  content: string,         // Todo description
  status: string,          // "pending", "in_progress", "completed"
  id: string,              // Unique identifier
  dependencies: string[]   // IDs of dependent todos
}
```

### aiserver.v1.PlanChoice
**Location:** Line 92936

```typescript
{
  label: string,           // Display label
  sublabel?: string,       // Optional sublabel
  description?: string,    // Optional description
  value: string           // Selection value
}
```

---

## agent.v1 Schemas (Agent-side Tool Calls)

### agent.v1.CreatePlanToolCall
**Location:** Line 134850

```typescript
{
  args: CreatePlanArgs,
  result: CreatePlanResult
}
```

### agent.v1.CreatePlanArgs (TLr)
**Location:** Line 134885

```typescript
{
  plan: string,           // Markdown plan content
  todos: TodoItem[],      // List of todos
  overview: string,       // Plan overview
  name: string           // Plan name
}
```

### agent.v1.CreatePlanResult
**Location:** Line 134933

```typescript
{
  result: oneof {
    success: CreatePlanSuccess,
    error: CreatePlanError
  },
  plan_uri: string       // URI to the created plan file
}
```

### agent.v1.CreatePlanSuccess
**Location:** Line 134975

```typescript
{}  // Empty - indicates success
```

### agent.v1.CreatePlanError
**Location:** Line 135000

```typescript
{
  error: string          // Error message
}
```

### agent.v1.CreatePlanRequestQuery
**Location:** Line 135030

```typescript
{
  args: CreatePlanArgs,
  tool_call_id: string   // ID linking to tool call
}
```

### agent.v1.CreatePlanRequestResponse
**Location:** Line 135065

```typescript
{
  result: CreatePlanResult
}
```

### agent.v1.TodoItem (Xlt)
**Location:** Line 133437

```typescript
{
  id: string,
  content: string,
  status: TodoStatus,      // Enum (see below)
  created_at: int64,       // Unix timestamp
  updated_at: int64,       // Unix timestamp
  dependencies: string[]
}
```

### agent.v1.TodoStatus (Ylt)
**Location:** Line 133414

```typescript
enum TodoStatus {
  UNSPECIFIED = 0,
  PENDING = 1,
  IN_PROGRESS = 2,
  COMPLETED = 3,
  CANCELLED = 4
}
```

---

## Tool Registration

The CreatePlan tool is registered in the `ClientSideToolV2` enum:

**Location:** Line 104365

```typescript
vt.CREATE_PLAN = 14  // Tool enum value
```

The tool name mapping:
- Params case: `"createPlanParams"`
- Result case: `"createPlanResult"`
- Display name: `"CreatePlan"`

---

## Plan File Format

### File Naming
**Location:** Lines 300779, 308575, 308581

```
{sanitized-name}-{uuid8}.plan.md
```

Example: `my-plan-a1b2c3d4.plan.md`

### File Detection
**Location:** Line 300724

Plans are detected by:
1. URI scheme `cursorPlan`
2. File path ending in `.plan.md` within `/.cursor/plans/` directory

### Storage Location
**Location:** Line 308478

Plans are stored in: `~/.cursor/plans/`

### Frontmatter Format
**Location:** Lines 308400-308415

```yaml
---
name: "Plan Name"
overview: "Plan overview text"
todos:
  - id: "todo-uuid"
    content: "Todo description"
    status: "pending"
    dependencies: []
---

# Plan Body Content
Markdown content of the plan...
```

---

## Services Architecture

### ComposerPlanService (N7)
**Location:** Line 309350+

Primary interface for plan operations:

```typescript
interface ComposerPlanService {
  getOrCreatePlanFile(composerId, name, overview, todos, body): Promise<URI>
  createPlanFile(composerId, name, overview, todos, body): Promise<URI>
  getPlanByUri(uri): Promise<Plan>
  updatePlanByUri(uri, name, overview, todos, body, composerId): Promise<void>
  updatePlanByUriDirty(uri, name, overview, todos, body, composerId): Promise<void>
  syncTodoUpdatesToFile(composerId, updates: Map<string, status>): Promise<void>
  buildSelectedTodosInNewAgent(planUri, todos): Promise<string>
  getPlanDerivedStatus(uri): Promise<string>
  openPlanInEditor(uri, options): Promise<void>
  registerComposerReference(uri, composerId): Promise<void>
}
```

### PlanStorageService (Tys)
**Location:** Line 308419+

Low-level plan storage operations:

```typescript
interface PlanStorageService {
  loadPlanByUri(uri): Promise<{metadata, body}>
  updatePlanContent(uri, content): Promise<void>
  updatePlanMetadata(uri, metadata, composerId): Promise<void>
  updatePlanFull(planId, updates, composerId): Promise<void>
  createPlanForComposer(options): Promise<PlanEntry>
  getPlanForComposer(composerId): Promise<PlanEntry|undefined>
  getRegistryEntry(uri): Promise<RegistryEntry|undefined>
  registerBuild(uri, composerId, todoIds): Promise<void>
  getPlanStatus(entry, todos): string
}
```

### PlanReviewModel (UJe)
**Location:** Line 309661

Handles human review of plan actions:

```typescript
interface PlanReviewModel {
  setStatus(status: ReviewStatus): void
  submitReview(option: PlanToolHumanReviewOption): void
  // ReviewStatus: REQUESTED, APPROVED, REJECTED
}
```

---

## Plan Creation Flow

### 1. Tool Call Initiation
The AI agent invokes `CreatePlan` with args containing plan content and todos.

### 2. Streaming Handler
**Location:** Line 468800+

During streaming, `CreatePlanToolCallHandler.handleToolCallStreaming()`:
- Creates or updates plan file
- Tracks plan URI in bubble data
- Opens plan editor (if not already open)

### 3. Completion Handler
**Location:** Line 468845+

On completion, `handleToolCallCompleted()`:
- Validates plan args
- Creates/updates plan via ComposerPlanService
- Sets up PlanReviewModel for human review
- Sends analytics event
- Returns result with plan URI

### 4. Human Review (Optional)
If review is enabled:
- User can approve, reject, or modify the plan
- Rejection prevents plan execution
- Approval allows proceeding to execution

---

## Plan Execution Flow

### 1. Build Selected Todos
**Location:** Line 309428+

```typescript
buildSelectedTodosInNewAgent(planUri, selectedTodos):
  1. Create new agent composer with "agent" mode
  2. Attach plan as context (selection context)
  3. Register composer reference to plan
  4. Submit prompt with todo assignments
  5. Register build in plan registry
```

### 2. Execution Prompt Template
**Location:** Line 309478+

```text
Implement the following to-dos from the plan (the plan is attached for your reference).
Do NOT edit the plan file itself.

You have been assigned the following N to-do(s) with IDs: id1, id2, ...

1. [id1] Todo content
2. [id2] Todo content
...

These to-dos have already been created. Do not create them again.
Mark them as in_progress as you work, starting with the first one.
Don't stop until you have completed all the assigned to-dos.
```

---

## Multi-Plan Mode (Feature-Gated)

### Feature Gate
**Location:** Line 294357

```javascript
file_based_plan_edits: {
  client: false,  // Server-controlled
  default: false
}
```

### Behavior Difference

**Single-plan mode (default):**
- `getOrCreatePlanFile()` - Updates existing plan or creates new

**Multi-plan mode:**
- `createPlanFile()` - Always creates new plan file
- Uses plan title as file name

---

## Interaction Queries

### create-plan-request
**Location:** Line 469373

Handled by `handleCreatePlanRequest()`:
1. Parse plan args
2. Check multi-plan mode
3. Create/get plan file
4. Open in editor
5. Update bubble data with plan URI
6. Return success result with plan path

---

## Registry Storage

Plans are tracked in local storage with keys:
- `composer.planRegistry` - Plan metadata registry
- `composer.planRedirects` - URI redirect mapping
- `composer.planMigrationToHomeDirCompleted` - Migration flag

### Registry Entry Structure
```typescript
{
  id: string,
  uri: URI,
  createdBy: string,      // Composer ID that created plan
  editedBy: string[],     // Composer IDs that edited
  referencedBy: string[], // Composer IDs that reference
  builtBy: {              // Map of builder -> todo IDs
    [composerId]: string[]
  }
}
```

---

## Related Tools

- **TodoRead** (`vt.TODO_READ`) - Read current todo state
- **TodoWrite** (`vt.TODO_WRITE`) - Update todo statuses
- **Task** (`vt.TASK_V2`) - Execute tasks (related to plan steps)

---

## Key Code Locations

| Component | Line Number |
|-----------|-------------|
| aiserver.v1.CreatePlanParams | 116607 |
| aiserver.v1.CreatePlanResult | 116686 |
| aiserver.v1.Step | 116551 |
| aiserver.v1.TodoItem | 115751 |
| agent.v1.CreatePlanToolCall | 134850 |
| agent.v1.CreatePlanArgs | 134885 |
| agent.v1.TodoItem | 133437 |
| agent.v1.TodoStatus enum | 133414 |
| CreatePlanToolCallHandler | 468745+ |
| ComposerPlanService | 309350+ |
| PlanStorageService | 308419+ |
| Plan file format functions | 308300+ |
| file_based_plan_edits feature | 294357 |

---

## Analysis Notes

### Architectural Observations

1. **Dual Schema Design**: The aiserver.v1 and agent.v1 schemas have overlapping but different structures, suggesting evolution of the protocol over time.

2. **Todo Status Divergence**: aiserver.v1 uses string status ("pending", "in_progress", "completed") while agent.v1 uses numeric enum (0-4 including CANCELLED).

3. **Step vs Todo**: The `Step` message appears deprecated in favor of `TodoItem` for plan structure.

4. **Feature Gate Pattern**: Multi-plan mode is server-controlled, allowing gradual rollout.

5. **Plan as Context**: Plans are attached to agent sessions as selection context, not as a special plan attachment type.

### Potential Investigation Areas

1. **Plan Modification Flow**: How does old_str/new_str work for plan edits?
2. **Dependency Resolution**: How are todo dependencies validated and ordered?
3. **Plan Status Derivation**: Logic for computing overall plan status from todos
4. **Plan Review Integration**: Full flow of plan approval/rejection
