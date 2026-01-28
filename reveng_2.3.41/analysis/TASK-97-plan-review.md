# TASK-97: PlanReviewModel and Human Approval Flow for Plans

## Summary

This analysis documents Cursor IDE's plan review system, which provides human approval gating for AI-generated plans before execution. The system uses a hierarchical model architecture where `PlanReviewModel` extends a base `ReviewModel` class, with approval states managed through a three-state machine.

## Source Location

- File: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
- Key module: `out-build/vs/workbench/contrib/composer/browser/toolCallHumanReviewService.js`
- Plan service: `out-build/vs/workbench/contrib/composer/browser/services/composerPlanService.js`
- Types: `out-build/vs/workbench/contrib/composer/browser/toolCallHumanReviewTypes.js`

## Key Types and Enums

### ToolCallHumanReviewStatus (Zv)

The approval state machine uses three states (line ~306152):

```javascript
(function(i) {
    i.NONE = "None",
    i.REQUESTED = "Requested",  // Awaiting human decision
    i.DONE = "Done"             // Decision made
})(Zv || (Zv = {}))
```

### ToolCallHumanReviewKind (z4)

Four kinds of tool review (line ~306154):

```javascript
(function(i) {
    i.EDIT = "edit",       // File edits
    i.TERMINAL = "terminal", // Terminal commands
    i.MCP = "mcp",         // MCP tool calls
    i.PLAN = "plan"        // Plan approval
})(z4 || (z4 = {}))
```

### PlanToolHumanReviewOption (HW)

User choices for plan review (line ~306164):

```javascript
(function(i) {
    i.NONE = "none",
    i.APPROVE = "approve",                              // Accept and execute plan
    i.REJECT_AND_TELL_WHAT_TO_DO_DIFFERENTLY = "rejectAndTellWhatToDoDifferently",  // Reject with feedback
    i.EDIT = "edit"                                     // Open plan in editor for manual edits
})(HW || (HW = {}))
```

## Class Hierarchy

### Base ReviewModel (qht)

Abstract base class at line ~309738 providing:

- `getIsShowingInput()` - Check if feedback input box is visible
- `setIsShowingInput(i)` - Toggle feedback input box
- `submitFeedbackText(i, e)` - Submit rejection feedback
- `closeInputBox()` - Close feedback input
- `getHighlightedOption()` - Get currently highlighted menu option
- `setHighlightedOption(i)` - Set highlighted option
- `selectHighlightedOption()` - Apply highlighted selection
- `setStatus(i)` - Set approval status
- `getOrCreateInputBoxBubble(i)` - Create input bubble for feedback
- `highlightOptionAbove()` / `highlightOptionBelow()` - Navigate options with keyboard

### PlanReviewModel (UJe)

Extends `qht` at line ~310024 with plan-specific behavior:

```javascript
UJe = class extends qht {
    constructor(i, e, t, n, s, r) {
        super();
        this.toolFormer = i;       // Tool execution manager
        this.bubbleId = e;         // Bubble ID in conversation
        this.composerDataService = t;
        this.composerPlanService = s;
        this.composerViewsService = r;
        this.composerId = n.data.composerId;
    }
}
```

Key methods:

#### getFreshHandle()
```javascript
getFreshHandle() {
    return this.composerDataService.getWeakHandleOptimistic(this.composerId)
}
```

#### getHumanReviewData()
Retrieves review data from bubble, validates tool type is CREATE_PLAN:
```javascript
getHumanReviewData() {
    const i = this.toolFormer.getBubbleData(this.bubbleId);
    if (!(!i || i.tool !== vt.CREATE_PLAN))
        return i.additionalData?.reviewData
}
```

#### setSelectedOption(i, e)
Main approval handler at line ~310049:

```javascript
setSelectedOption(i, e) {
    this.updateReviewData({ selectedOption: i });
    const t = this.getFreshHandle();

    // APPROVE: Execute the plan
    if (i === HW.APPROVE) {
        if (!t) {
            console.warn("[PlanReviewModel] Cannot approve plan: composer handle not available");
            return
        }
        const s = this.toolFormer.getBubbleData(this.bubbleId)?.additionalData?.planUri;
        if (!s) {
            console.warn("[PlanReviewModel] No plan URI in bubble data");
            return
        }
        const r = _e.parse(s);
        this.setStatus(Zv.DONE);
        this.composerPlanService.acceptPlan(t, r, this.bubbleId, "manual", e);
    }

    // REJECT: Show feedback input
    if (i === HW.REJECT_AND_TELL_WHAT_TO_DO_DIFFERENTLY) {
        this.setIsShowingInput(!0);
        this.composerViewsService.focus(this.composerId, !0);
    }

    // EDIT: Open plan in editor
    if (i === HW.EDIT) {
        this.setStatus(Zv.DONE);
        const n = this.toolFormer.getBubbleData(this.bubbleId);
        if (n?.tool === vt.CREATE_PLAN) {
            const s = n.additionalData?.planUri;
            if (s) {
                const r = jve(s);  // Parse plan URI
                this.composerPlanService.openPlanInEditor(r, {
                    stealFocus: !0,
                    composerId: this.composerId
                });
            }
        }
    }
}
```

#### getCurrentlyDisplayedOptions()
Returns available choices:
```javascript
getCurrentlyDisplayedOptions() {
    return [HW.APPROVE, HW.REJECT_AND_TELL_WHAT_TO_DO_DIFFERENTLY, HW.EDIT]
}
```

#### getDefaultReviewData()
Initial state:
```javascript
getDefaultReviewData() {
    return {
        status: Zv.NONE,
        selectedOption: HW.NONE,
        isShowingInput: !1,
        highlightedOption: void 0
    }
}
```

#### isExecutionBlocking()
Plans are non-blocking (line ~310110):
```javascript
isExecutionBlocking() {
    return !1
}
```

This differs from terminal and MCP reviews which return `true`.

#### getKeyboardShortcut(i, e)
```javascript
getKeyboardShortcut(i, e) {
    switch (i) {
        case HW.APPROVE:
            return FK("\u23CE");  // Enter key
        case HW.REJECT_AND_TELL_WHAT_TO_DO_DIFFERENTLY:
            return "Esc";
        default:
            return e ? FK("\u23CE") : ""
    }
}
```

## ToolCallHumanReviewService (rWt / JW)

The service managing all review models at line ~309553:

### Key Methods

#### getPlanReviewModelForBubble(e, t)
Creates or retrieves PlanReviewModel at line ~309661:
```javascript
getPlanReviewModelForBubble(e, t) {
    const n = this.composerDataService.getToolFormer(e);
    if (!n) return;
    const s = this._reviewModelCache.get(t);
    if (s !== void 0 && s instanceof UJe) return s;
    const r = n.getBubbleData(t);
    if (r && r.tool === vt.CREATE_PLAN) {
        const o = new UJe(n, t, this.composerDataService, e,
                         this.composerPlanService, this.composerViewsService);
        return this._reviewModelCache.set(t, o), o
    }
}
```

#### isToolformerCurrentlyWaitingForPlanReview(e)
Checks if plan review is pending at line ~309704:
```javascript
isToolformerCurrentlyWaitingForPlanReview(e) {
    const t = this.composerDataService.getToolFormer(e);
    return t ? t.pendingDecisions().userInteractionBubbleIds.some(s => {
        const r = po(() => t.getBubbleData(s));
        return r && r.tool === vt.CREATE_PLAN &&
               r?.additionalData?.reviewData?.status === Zv.REQUESTED
    }) : !1
}
```

#### getReviewModelForLastBubbleUnderReview(e)
Retrieves review model checking for pending state:
```javascript
// At line 309591-309600
if (t.bubbleTool === vt.CREATE_PLAN) {
    const o = n.getBubbleData(t.bubbleId)?.additionalData?.planUri;
    if (o) try {
        const l = jve(o);
        if (!this.composerPlanService.isPlanPendingByUri(l)) return
    } catch { return }
    const a = new UJe(n, t.bubbleId, this.composerDataService, e,
                     this.composerPlanService, this.composerViewsService);
    return this._reviewModelCache.set(t.bubbleId, a), a
}
```

## ComposerPlanService (N7)

Located at line ~308987, manages plan lifecycle.

### acceptPlan(e, t, n, s, r)
Executes an approved plan at line ~309075:

```javascript
async acceptPlan(e, t, n, s, r) {
    const o = e.data.composerId;
    const a = e.data;
    let l, d, h = [];

    try {
        const H = await this._planStorageService.loadPlanByUri(t);
        l = H.body;
        d = H.metadata.name;
        h = H.metadata.todos ?? [];
    } catch (H) {
        console.warn("[ComposerPlanService] Failed to load plan content");
    }

    // Filter incomplete todos
    const P = h.filter(H => H.status !== "completed" && H.status !== "cancelled");

    // Register build with storage service
    try {
        const H = P.map(J => J.id);
        await this._planStorageService.registerBuild(t, o, H);
    } catch (H) {
        console.warn("[ComposerPlanService] Failed to register build");
    }

    // Get execution config and submit chat
    const B = this.getPlanExecutionConfigForExecution(e);
    await this._composerChatService.submitChatMaybeAbortCurrent(e.data.composerId, _, {
        isPlanExecution: !0,
        modelOverride: B.modelName,
        planUri: t.toString()
    });

    this._composerViewsService.focus(e.data.composerId, !0);
    this.setupAutoOpenReviewPaneAfterFirstEdit(o, t, s);
}
```

### hasPendingPlan(e)
Checks if plan awaits approval at line ~309062:

```javascript
hasPendingPlan(e) {
    const t = this.getMostRecentPlanBubbleId(e);
    if (!t) return !1;
    const s = this.getPlanBubbleData(e, t)?.additionalData?.planUri;
    if (!s) return !1;
    try {
        const r = jve(s);
        const o = this._planStorageService.getRegistryEntrySync(r);
        return o ? Object.keys(o.builtBy).length === 0 : !1
    } catch {
        return !1
    }
}
```

### isPlanPendingByUri(e)
Check by URI at line ~309421:
```javascript
isPlanPendingByUri(e) {
    const t = this._planStorageService.getRegistryEntrySync(e);
    return t ? Object.keys(t.builtBy).length === 0 : !1
}
```

## Plan Storage and Registry

### Registry Entry Structure

Plans are tracked in a registry with this structure (line ~308600):

```javascript
{
    name: e.name,
    uri: a,
    createdBy: e.composerId,
    editedBy: [e.composerId],
    referencedBy: [e.composerId],
    builtBy: {},           // Empty = pending approval
    lastUpdatedAt: f,
    createdAt: f
}
```

The `builtBy` field being empty indicates a pending (unexecuted) plan.

### registerBuild(e, t, n)
Marks a plan as built at line ~308792:
```javascript
async registerBuild(e, t, n) {
    await this.loadRegistry();
    const s = await this.getRegistryEntry(e);
    // Adds composerId to builtBy map
}
```

## UI Integration

### Status Display

The UI shows "Awaiting plan review" status (line ~753909):
```javascript
if (e.composerPlanService.hasPendingPlan(n))
    return "Awaiting plan review";
```

### Keyboard Shortcuts

Enter key triggers approval via existing composer shortcut handling (line ~767649):
```javascript
const xn = Gr ? e.toolCallHumanReviewService.getReviewModelForLastBubbleUnderReview(Gr) : void 0;
if (xn?.getKind() === z4.PLAN)
    return xn.setSelectedOption(HW.APPROVE), !0;
```

### Review UI Component

Plan review is rendered in conversation bubbles at line ~937399:
```javascript
const bt = e.toolCallHumanReviewService.getPlanReviewModelForBubble(f(), i.bubbleId);
const tt = ve(() =>
    e.toolCallHumanReviewService.getReviewModelForLastBubbleUnderReview(f())?.bubbleId === i.bubbleId &&
    bt?.getHumanReviewData()?.status === Zv.REQUESTED
);
```

## Plan Rejection Flow

When user rejects a plan (line ~468924):

```javascript
const D = r.getPlanReviewModelForBubble(l, a);
D && D.setStatus(Zv.REQUESTED);
const P = new Flt({
    result: {
        case: "rejected",
        value: {}
    }
});
```

## Auto-Approval Behavior

In plan mode, automatic approval can occur when first edit is applied (line ~481946):

```javascript
if (Oe && Oe.unifiedMode === "plan") {
    const Ze = this.composerPlanService.getMostRecentPlanBubbleId(Ne);
    if (Ze && this.composerPlanService.hasPendingPlan(Ne)) {
        const Ke = this.composerPlanService.getPlanUriFromBubble(Ne, Ze);
        Ke && await this.composerPlanService.acceptPlan(Ne, Ke, Ze, "auto")
    }
    this.composerModesService.setComposerUnifiedMode(Ne, "agent")
}
```

The `"auto"` vs `"manual"` approval source is tracked for analytics.

## Architecture Diagram

```
+---------------------------+
|  Conversation Bubble      |
|  (tool: CREATE_PLAN)      |
+------------+--------------+
             |
             v
+---------------------------+
| PlanReviewModel (UJe)     |
| - bubbleId                |
| - composerId              |
| - toolFormer              |
+------------+--------------+
             |
             | setSelectedOption()
             v
+---------------------------+       +---------------------------+
| APPROVE                   |       | REJECT                    |
| - acceptPlan()            |       | - setIsShowingInput(true) |
| - registerBuild()         |       | - focus input             |
| - submitChatMaybeAbort()  |       +---------------------------+
+------------+--------------+
             |                      +---------------------------+
             |                      | EDIT                      |
             |                      | - openPlanInEditor()      |
             |                      +---------------------------+
             v
+---------------------------+
| PlanStorageService        |
| - loadPlanByUri()         |
| - registerBuild()         |
| - registry tracking       |
+---------------------------+
```

## Comparison with Other Review Models

| Feature | PlanReviewModel | TerminalToolReviewModel | MCPToolReviewModel |
|---------|-----------------|------------------------|-------------------|
| Minified class | UJe | aWt | Jht |
| Kind enum | z4.PLAN | z4.TERMINAL | z4.MCP |
| Options enum | HW | y_ | Ak |
| isExecutionBlocking() | false | true | true |
| Can edit | Yes (open editor) | No | No |
| Allowlist option | No | Yes | Yes |

## Data Flow Summary

1. AI generates plan via `CREATE_PLAN` tool call
2. Bubble created with `additionalData.planUri` and `reviewData.status = NONE`
3. ToolCallHumanReviewService creates `PlanReviewModel`
4. Status set to `REQUESTED` for user interaction
5. UI displays approval buttons: Approve / Reject / Edit
6. User selection triggers `setSelectedOption()`:
   - **APPROVE**: Calls `composerPlanService.acceptPlan()`, registers build, starts execution
   - **REJECT**: Opens feedback input, user provides alternative instructions
   - **EDIT**: Opens plan file in editor for manual modification
7. Status changes to `DONE` on approval/edit

## Related Services

- `IToolCallHumanReviewService` (JW) - Service identifier
- `composerPlanService` (N7) - Plan lifecycle management
- `planStorageService` (nWt) - Plan persistence
- `composerDataService` (Yo) - Composer data access
- `composerViewsService` (qb) - UI focus management

## Feature Gates

Plan mode availability is controlled by feature gate (line ~309217):
```javascript
isSpecModeEnabled() {
    return this._experimentService.checkFeatureGate("spec_mode") === !0
}
```

Model support for plan mode (line ~165265):
```javascript
{
    no: 22,
    name: "supports_plan_mode",
    kind: "scalar",
    T: 8,
    opt: !0
}
```
