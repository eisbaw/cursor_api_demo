# TASK-113: Composer Mode System Architecture

## Executive Summary

The Cursor IDE 2.3.41 implements a comprehensive composer mode system through the `composerModesService` that manages different operational modes for the AI assistant. The system supports 10 protected modes with configurable tool availability, auto-run behavior, and UI theming.

## Core Service: ComposerModesService

**Location**: `out-build/vs/workbench/contrib/composer/browser/composerModesService.js` (line ~310126)

**Service Identifier**: `composerModesService` (created via `on("composerModesService")`)

### Class Structure

```javascript
class ComposerModesService extends Ve {
    static ACTION_ID_PREFIX = "composerMode."
    static PROTECTED_MODE_IDS = [
        "agent", "chat", "edit", "background",
        "plan", "spec", "debug", "triage",
        "review-edits", "yolo-mode"
    ]
}
```

## Protected Modes (Cannot Be Deleted)

### 1. Agent Mode (`id: "agent"`)
- **Name**: "Agent"
- **Icon**: "infinity"
- **Description**: "Plan, search, make edits, run commands"
- **Action ID**: `composerMode.agent`
- **Default Keybinding**: `Cmd+I` / `Ctrl+I`
- **Configuration**:
  - `autoRun: true` - Commands auto-execute
  - `fullAutoRun: false` - Requires terminal command approval
  - `shouldAutoApplyIfNoEditTool: true` - Auto-applies changes
  - `autoFix: true`
  - `enabledTools: []` - All tools available (empty = no restriction)
  - `thinkingLevel: "none"`

### 2. Triage Mode (`id: "triage"`)
- **Name**: "Triage"
- **Icon**: "rocket"
- **Description**: "Coordinate long-horizon tasks with delegated subagents"
- **Feature Gate**: `nal_async_task_tool` (hidden if disabled)
- **Configuration**:
  - `autoRun: true`
  - `fullAutoRun: false`
  - `enabledTools: [vt.TASK_V2, vt.APPLY_AGENT_DIFF]` - Only subagent delegation tools
  - `shouldAutoApplyIfNoEditTool: false`

### 3. Plan Mode (`id: "plan"`)
- **Name**: "Plan"
- **Icon**: "todos"
- **Description**: "Create detailed plans for accomplishing tasks"
- **Configuration**:
  - `autoRun: false`
  - `shouldAutoApplyIfNoEditTool: false`
  - `autoFix: false`
  - Special model filtering: Only models that support `mys()` (planning capability)

### 4. Spec Mode (`id: "spec"`)
- **Name**: "Spec"
- **Icon**: "checklist"
- **Description**: "Create structured plans with implementation steps"
- **Feature Gate**: `spec_mode` (hidden if disabled)
- **Configuration**:
  - `autoRun: false`
  - `shouldAutoApplyIfNoEditTool: false`
  - `unifiedMode: "spec"` used for creating structured specifications

### 5. Debug Mode (`id: "debug"`)
- **Name**: "Debug"
- **Icon**: "bug"
- **Description**: "Systematically diagnose and fix bugs using runtime traces"
- **Special Behavior**: Triggers `_debugServerService.getConfig()` on activation
- **Configuration**:
  - `autoRun: false`
  - `shouldAutoApplyIfNoEditTool: true`
  - `autoFix: false`

### 6. Chat Mode (`id: "chat"`)
- **Name**: "Ask"
- **Icon**: "chat"
- **Description**: "Ask Cursor questions about your codebase"
- **Configuration**:
  - `autoRun: false`
  - `shouldAutoApplyIfNoEditTool: false`
  - `autoFix: true`
  - Chat-like behavior (no edit tools)

### 7. Background Mode (`id: "background"`)
- **Name**: "Cloud"
- **Icon**: "cloudTwo"
- **Description**: Cloud-based background agent execution
- **Precondition**: `aW.INSTANCE` (requires background composer enabled)
- **Dynamic Registration**: Registered via `maybeRegisterBackgroundModeAction()`
- **Privacy Mode**: Disabled in legacy privacy mode
- **Configuration**:
  - `autoRun: false`
  - `thinkingLevel: "none"`
  - `shouldAutoApplyIfNoEditTool: false`

### 8. Edit Mode (`id: "edit"`)
- **Status**: Legacy/Hidden (filtered out in migrations)
- **Behavior**: Returns empty `supportedTools: []` from `getAvailableTools()`
- **Note**: Line 944252 shows migration removes edit mode: `o.modes4 = o.modes4.filter(a => a.id !== "edit")`

### 9. Review-Edits Mode (`id: "review-edits"`)
- **Constant**: `FL.REVIEW_EDITS = "review-edits"`
- **Purpose**: Review mode for AI-generated edits
- **Special Rules**:
  - `autoRun` always returns `false`
  - `fullAutoRun` always returns `false`
  - Cannot enable auto-run behavior

### 10. YOLO Mode (`id: "yolo-mode"`)
- **Constant**: `FL.YOLO_MODE = "yolo-mode"`
- **Purpose**: Unrestricted execution mode
- **Tool Behavior**: Gets same tool filtering as core modes

## Mode Configuration Schema

```typescript
interface ModeConfig {
    id: string;                          // Unique identifier
    name: string;                        // Display name
    actionId: string;                    // Command action ID (e.g., "composerMode.agent")
    icon: string;                        // Icon name
    description?: string;                // Mode description
    thinkingLevel: "none" | string;      // AI thinking visibility level
    shouldAutoApplyIfNoEditTool: boolean; // Auto-apply when no EDIT_FILE tool
    autoFix: boolean;                    // Auto-fix linting errors
    autoRun: boolean;                    // Auto-run tool calls
    fullAutoRun: boolean;                // Full auto-approval (including terminal)
    enabledTools: ToolType[];            // Restricted tool list (empty = all)
    enabledMcpServers: string[];         // MCP server restrictions
    model?: string;                      // Mode-specific model override
    useMax?: boolean;                    // Use max mode for model
}
```

## State Management

### Storage Location
Mode configurations stored in `applicationUserPersistentStorage.composerState.modes4`:

```javascript
this._reactiveStorageService.applicationUserPersistentStorage.composerState?.modes4
```

### Composer Data Association
Each composer session has a `unifiedMode` field:

```javascript
// Get current mode for a composer
getComposerUnifiedMode(composerId) {
    const data = this._composerDataService.getComposerData(composerId);
    return data?.unifiedMode ?? "agent"; // Default to agent
}

// Set mode for a composer
setComposerUnifiedMode(composerId, modeId) {
    this._composerDataService.updateComposerDataSetStore(composerId, n => {
        n("unifiedMode", modeId)
    });
}
```

### Mode Fallback Logic
```javascript
// If mode doesn't exist, fallback to agent
if (!this.checkIfModeExists(modeId)) {
    this.setComposerUnifiedMode(composerId, "agent");
    return "agent";
}
```

## Tool Availability Per Mode

### Tool Filtering Logic (line ~450906)

```javascript
async getAvailableTools(modeId, composerId) {
    // Edit mode: No tools
    if (modeId === "edit") return { supportedTools: [] };

    const mode = this.composerModesService.getMode(modeId);
    let tools = Array.from(this.availableTools);

    // Custom modes use enabledTools restriction
    if (modeId !== "agent" && modeId !== "chat" && modeId !== "plan"
        && modeId !== "spec" && modeId !== "debug" && modeId !== "search"
        && modeId !== "review-edits" && modeId !== "yolo-mode"
        && mode?.enabledTools) {
        tools = mode.enabledTools;
    }

    // Special filtering
    return tools.filter(t => {
        // Web search: Only for agent/chat/search modes with setting enabled
        if ((modeId === "agent" || modeId === "chat" || modeId === "search")
            && t === vt.WEB_SEARCH) return webSearchEnabled;

        // Knowledge base: Requires memory service
        if (t === vt.KNOWLEDGE_BASE && !memoriesEnabled) return false;

        // Task tools: Require specific config
        if (t === vt.AWAIT_TASK) return false;
        if (t === vt.TASK && taskToolDisabled) return false;

        // ASK_QUESTION: Only for plan mode or with feature gate
        if (t === vt.ASK_QUESTION)
            return experimentService.checkFeatureGate("ask_question_all_modes")
                   || modeId === "plan";

        return true;
    }).filter(t => t !== vt.MCP); // MCP always filtered out
}
```

## Mode Switching

### Switch Mode Tool
The AI can request mode switches via the `SWITCH_MODE` tool:

```javascript
// Tool call handler (line ~484181)
case "switchModeToolCall": {
    const params = toolCall.switchModeParams;
    this.composerModesService.setComposerUnifiedMode(composerId, params.toModeId);
    return { case: "switchModeResult", value: { success: true } };
}
```

### Switch Mode Timeout
Mode switch requests have a timeout mechanism:

```javascript
if (toolType === vt.SWITCH_MODE && !this.switchModeTimeouts.has(toolCallId)) {
    const timeout = setTimeout(() => {
        this.rejectToolCall(toolCallId);
        this.switchModeTimeouts.delete(toolCallId);
    }, TIMEOUT_MS);
    this.switchModeTimeouts.set(toolCallId, timeout);
}
```

### Programmatic Mode Switching

```javascript
// From UI component
e.composerModesService.setComposerUnifiedMode(composerId, "plan");

// With data update
this._composerDataService.updateComposerData(composerId, {
    unifiedMode: "agent"
});
```

## UI Integration

### Mode Icons and Theming

CSS variables define mode-specific colors (line ~185383):

```javascript
const modeThemes = {
    chat: {
        background: "var(--composer-mode-chat-background)",
        text: "var(--composer-mode-chat-text)",
        iconButton: "var(--composer-mode-chat-text)"
    },
    background: {
        background: "var(--composer-mode-background-background)",
        text: "var(--composer-mode-background-text)",
        iconButton: "var(--composer-mode-background-text)"
    },
    plan: {
        background: "var(--composer-mode-plan-background)",
        text: "var(--composer-mode-plan-text)",
        iconButton: "var(--composer-mode-plan-icon)",
        border: "var(--composer-mode-plan-border)"
    },
    triage: {
        background: "var(--composer-mode-triage-background, transparent)",
        text: "var(--composer-mode-triage-text, var(--vscode-input-foreground))",
        iconButton: "var(--composer-mode-triage-icon, var(--vscode-button-background))",
        border: "var(--composer-mode-triage-border, var(--vscode-focusBorder))"
    },
    spec: {
        background: "var(--composer-mode-spec-background)",
        text: "var(--composer-mode-spec-text)",
        iconButton: "var(--composer-mode-spec-icon)",
        border: "var(--composer-mode-spec-border)"
    },
    debug: {
        background: "var(--composer-mode-debug-background)",
        text: "var(--composer-mode-debug-text)",
        iconButton: "var(--composer-mode-debug-icon)",
        border: "var(--composer-mode-debug-border)"
    }
};
```

### Mode Quick Menu

The agent layout includes a mode grid for selection (line ~847253):

```javascript
class AgentLayoutQuickMenu {
    renderModeGrid() {
        // Renders mode selection tiles
    }

    renderModeOption(mode) {
        const tile = createElement("div");
        tile.className = "agent-layout-quick-menu__mode-option";
        if (mode.isSelected) tile.classList.add("is-selected");

        // Icon container
        const iconContainer = createElement("div");
        iconContainer.className = "agent-layout-quick-menu__mode-icon-container";
        mode.renderIcon(iconContainer);

        // Label
        const label = createElement("span");
        label.className = "agent-layout-quick-menu__mode-label";
        label.textContent = mode.label;
    }
}
```

### Mode Descriptions

```javascript
getModeDescription(modeId) {
    switch (modeId) {
        case "agent":
            return "Plan, search, build anything";
        case "chat":
            return "Ask Cursor questions about your codebase";
        case "edit":
            return "Manually decide what gets added to the context (no tools)";
        case "plan":
            return "Create detailed plans for accomplishing tasks";
        case "spec":
            return "Create structured plans with implementation steps";
        case "triage":
            return "Coordinate long-horizon tasks with delegated subagents";
        default:
            return this.getMode(modeId)?.description;
    }
}
```

## Auto-Run Behavior

### Auto-Run Settings

```javascript
// Get auto-run for mode
getModeAutoRun(modeId) {
    // Review-edits and admin-disabled modes always return false
    if (modeId === "review-edits" || fN().isDisabledByAdmin) return false;
    return this.getAllModes().find(m => m.id === modeId)?.autoRun ?? false;
}

// Full auto-run (no terminal approval needed)
getModeFullAutoRun(modeId) {
    if (modeId === "review-edits" || fN().isDisabledByAdmin) return false;
    return this.getAllModes().find(m => m.id === modeId)?.fullAutoRun ?? false;
}

// Convenience methods for agent mode
getComposerAutoRun() {
    return this.getModeAutoRun("agent") ?? false;
}
setComposerAutoRun(enabled) {
    this.setModeAutoRun("agent", enabled);
    if (!enabled) this.setModeFullAutoRun("agent", false);
}
```

### Auto-Approve Pending Reviews

When fullAutoRun is enabled, pending terminal reviews are auto-approved:

```javascript
_autoApproveAllComposersInMode(modeId) {
    const composerIds = this._composerDataService.loadedComposers.store.ids;
    for (const id of composerIds) {
        if (this.getComposerUnifiedMode(id) === modeId) {
            this._autoApprovePendingTerminalReviews(id);
        }
    }
}
```

## Keybinding Management

### Mode Keybinding Registration

```javascript
async saveModeKeybinding(modeId, keybinding) {
    const mode = this.getMode(modeId);

    // Check for conflicts
    const conflictingMode = this.getAllModes().find(m => {
        if (m.id === modeId) return false;
        const kb = this._keybindingService.lookupKeybinding(m.actionId);
        return kb?.getUserSettingsLabel() === keybinding;
    });

    if (conflictingMode) {
        throw new Error(`Keybinding "${keybinding}" already used by mode "${conflictingMode.name}"`);
    }

    // Generate action ID if needed
    let actionId = mode.actionId;
    if (!actionId) {
        actionId = this.generateActionIdForMode(mode);
        this.updateModeSetStore(modeId, s => s("actionId", actionId));
    }

    // Register keybinding
    await this._keybindingEditingService.addKeybindingRule(actionId, keybinding);
    this.registerModeAction(mode, actionId);
}
```

### Action Registration

```javascript
registerModeAction(mode, actionId) {
    const action = registerAction(class extends StandardAction {
        constructor() {
            super({
                id: actionId,
                title: { value: `Open Chat in ${mode.name} Mode` },
                precondition: mode.id === "background" ? aW.INSTANCE : undefined,
                f1: true  // Available in command palette
            });
        }

        run(accessor) {
            return accessor.get($n).executeCommand(RNe, mode.id);
        }
    });

    this.modeActionDisposables.set(mode.id, action);
}
```

## Feature Gates

Several modes are gated behind experiments:

```javascript
// Spec mode requires feature gate
this._experimentService.checkFeatureGate("spec_mode") !== true && s.push("spec");

// Triage mode requires async task tool
this._experimentService.checkFeatureGate("nal_async_task_tool") || s.push("triage");

// ASK_QUESTION tool gated per mode
g === vt.ASK_QUESTION ?
    this.experimentService.checkFeatureGate("ask_question_all_modes") || modeId === "plan"
    : true
```

## Migration History

### Agent Keybinding Migration
```javascript
if (!_.hasMigratedToAgentIsCmdI) {
    const keybinding = `${this.getPlatformModifier()}+i`;
    this.saveModeKeybinding("agent", keybinding);
    this._reactiveStorageService.setApplicationUserPersistentStorage(
        "composerState", "hasMigratedToAgentIsCmdI", true
    );
}
```

### Background Mode Keybinding Removal
```javascript
// Remove legacy Cmd+E binding for background mode
const bgKeybindings = this._keybindingService.getKeybindings()
    .filter(k => k.command === "composerMode.background");
for (const kb of bgKeybindings) {
    const label = kb.resolvedKeybinding?.getUserSettingsLabel()?.toLowerCase();
    if (label === "cmd+e" || label === "ctrl+e" || label === "meta+e") {
        this._keybindingEditingService.removeKeybinding(kb);
    }
}
```

### Edit Mode Removal
```javascript
// Line 944252 - Migration removes edit mode from modes4
if (o.modes4) {
    o.modes4 = o.modes4.filter(a => a.id !== "edit");
    if (o.defaultMode2 === "edit") {
        o.defaultMode2 = "agent";
    }
}
```

## Key Findings

1. **10 Protected Modes**: Cannot be deleted by users
2. **Agent as Default**: Fallback for invalid/missing modes
3. **Tool Restrictions**: Custom modes can restrict available tools via `enabledTools`
4. **MCP Server Control**: Modes can restrict which MCP servers are available via `enabledMcpServers`
5. **Auto-Run Hierarchy**: `autoRun` controls general tool execution, `fullAutoRun` controls terminal commands
6. **Feature Gating**: Some modes (spec, triage) hidden behind experiment flags
7. **Review-Edits Special Case**: Never allows auto-run behavior
8. **Mode Switching**: AI can request mode switches via SWITCH_MODE tool with timeout protection

## Related Services

- `composerDataService`: Manages composer session data including current mode
- `backgroundComposerDataService`: Manages background/cloud composer data
- `composerService`: High-level composer operations
- `modelConfigService`: Model configuration per mode
- `reactiveStorageService`: Persistent storage for mode configurations

## Files Referenced

- `workbench.desktop.main.js` lines:
  - 182260-182367: Default mode configurations
  - 185383-185414: Mode theme CSS variables
  - 310126-310542: ComposerModesService implementation
  - 450906-450928: Tool availability filtering
  - 847253-847437: Mode quick menu UI
