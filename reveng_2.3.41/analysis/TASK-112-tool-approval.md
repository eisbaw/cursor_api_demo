# TASK-112: Tool Execution Approval Flow Analysis

## Overview

This document analyzes the tool execution approval system in Cursor 2.3.41, documenting how user approval is requested and processed for potentially dangerous tool operations.

## Key Components

### 1. Core Services

| Service | Location (line) | Purpose |
|---------|-----------------|---------|
| `composerDecisionsService` (Sxe) | 476421-476923 | Central approval coordinator |
| `toolCallHumanReviewService` (JW, rWt) | 309551-309731 | UI review model management |
| `asyncOperationRegistry` | Throughout | Tracks pending approval operations |

### 2. Approval Decision Flow

The approval flow follows this pattern:

```
Tool Call -> needApproval Check -> Review Mode -> User Decision -> Execute/Reject
```

#### Step 1: Determine if Approval is Needed

The `needApproval` flag is computed based on multiple factors:

```javascript
// From xOh function at line 479097
function xOh(parsedCommand, settings, autoRunService, ...) {
    // Cases that ALWAYS need approval (needApproval: true):
    // 1. Admin-disabled by admin policy
    // 2. Parsing failed and not in "run everything mode"
    // 3. Command matches blockedCommands list
    // 4. Empty executable commands (no auto-run)
    // 5. 'rm' command with deleteFileProtection enabled
    // 6. 'sudo' command (always blocked)
    // 7. Command not in allowlist when sandbox disabled

    // Cases that DON'T need approval (needApproval: false):
    // 1. "Run everything mode" enabled, not admin-controlled
    // 2. All commands match allowed patterns
    // 3. Sandbox policy level sufficient for command
}
```

### 3. Review Status Enum

```javascript
// ToolCallHumanReviewStatus (Zv) at line 309548
const ToolCallHumanReviewStatus = {
    NONE: "none",      // No review in progress
    REQUESTED: "requested",  // Waiting for user decision
    DONE: "done"       // User has made a decision
};
```

### 4. Review Result Types

#### Terminal Commands (lR)
```javascript
// At line 309735
const TerminalToolReviewResultType = {
    RUN: "run",           // Execute the command
    SKIP: "skip",         // Skip without error
    REJECT_AND_TELL_WHAT_TO_DO_DIFFERENTLY: "rejectAndTellWhatToDoDifferently",
    ALLOWLIST_COMMANDS: "allowlistCommands",  // Add to auto-run list
    NONE: "none"          // Review cancelled
};
```

#### MCP Tools (Mx)
```javascript
// At line 309737
const MCPToolReviewResultType = {
    RUN: "run",
    SKIP: "skip",
    REJECT_AND_TELL_WHAT_TO_DO_DIFFERENTLY: "rejectAndTellWhatToDoDifferently",
    ALLOWLIST_TOOL: "allowlistTool",  // Add tool to allowlist
    NONE: "none"
};
```

#### File Edits (zK)
```javascript
// At line 309733
const EditToolReviewResultType = {
    ACCEPT: "accept",
    REJECT_AND_TELL_WHAT_TO_DO_DIFFERENTLY: "rejectAndTellWhatToDoDifferently",
    SKIP: "skip",
    NONE: "none"
};
```

### 5. User Review Options

#### Terminal Command Options (y_)
```javascript
// At line 306159
const TerminalToolHumanReviewOption = {
    RUN: "run",
    SKIP: "skip",
    ALLOWLIST_COMMANDS: "allowlistCommands",
    REJECT_AND_TELL_WHAT_TO_DO_DIFFERENTLY: "rejectAndTellWhatToDoDifferently"
};
```

#### MCP Tool Options (Ak)
```javascript
// At line 306161
const MCPToolHumanReviewOption = {
    RUN: "run",
    SKIP: "skip",
    REJECT_AND_TELL_WHAT_TO_DO_DIFFERENTLY: "rejectAndTellWhatToDoDifferently",
    ALLOWLIST_TOOL: "allowlistTool"
};
```

#### Edit Options (dD)
```javascript
// At line 306163
const EditToolHumanReviewOption = {
    ACCEPT: "accept",
    REJECT_AND_TELL_WHAT_TO_DO_DIFFERENTLY: "rejectAndTellWhatToDoDifferently",
    SKIP: "skip",
    SWITCH_TO_DEFAULT_AGENT_MODE: "switchToDefaultAgentMode"
};
```

### 6. Approval Types for Tracking

```javascript
// TerminalApprovalType (tye) at line 306156
const TerminalApprovalType = {
    USER: "user",           // User clicked approve
    ALLOWLIST: "allowlist", // Auto-approved via allowlist
    FULL_AUTO: "full_auto", // YOLO mode enabled
    NONE: "none"            // Not executed
};
```

## Review Model Classes

### 1. TerminalToolReviewModel (aWt)

Located at lines 309885-309952. Manages terminal command review state.

```javascript
class TerminalToolReviewModel extends ReviewModel {
    getHeaderText() {
        // Returns "Run command?" or specific command prompt
        const candidates = this.getHumanReviewData()?.candidatesForAllowlist;
        if (Array.isArray(candidates) && candidates.length > 0) {
            return `Run '${candidates.join(", ")}'?`;
        }
        return "Run command?";
    }

    getCurrentlyDisplayedOptions() {
        // Shows ALLOWLIST_COMMANDS only if there are candidates
        if (candidatesForAllowlist && candidatesForAllowlist.length > 0) {
            return [RUN, SKIP, REJECT, ALLOWLIST_COMMANDS];
        }
        return [RUN, SKIP, REJECT];
    }
}
```

### 2. MCPToolReviewModel (Jht)

Located at lines 309953-310023. Manages MCP tool call review state.

```javascript
class MCPToolReviewModel extends ReviewModel {
    getHeaderText() {
        // Shows tool name and server: "Run tool_name on server_name?"
        const toolName = this.getToolName();
        const serverName = this.getServerName();
        return toolName ? `Run ${toolName}${serverName ? ` on ${serverName}` : ''}?` : "Run MCP tool?";
    }

    getCurrentlyDisplayedOptions() {
        // Always includes ALLOWLIST_TOOL if tool name is available
        const options = [RUN, SKIP, REJECT];
        if (toolName) options.push(ALLOWLIST_TOOL);
        return options;
    }
}
```

### 3. EditFileReviewModel (oWt)

Located at lines 309819-309885. Manages file edit review state.

```javascript
class EditFileReviewModel extends ReviewModel {
    getHeaderText() {
        return "Keep this edit?";
    }

    getCurrentlyDisplayedOptions() {
        return [ACCEPT, REJECT, SWITCH_TO_DEFAULT_AGENT_MODE];
    }
}
```

## YOLO Mode / Auto-Run Configuration

### Settings Structure

```javascript
// Default values at line 182267-182274
const defaultComposerState = {
    useYoloMode: false,
    yoloPrompt: "",
    yoloCommandAllowlist: [],
    yoloCommandDenylist: [],
    yoloMcpToolsDisabled: true,
    yoloDeleteFileDisabled: false,
    yoloOutsideWorkspaceDisabled: true,
    yoloDotFilesDisabled: true
};
```

### Protection Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `deleteFileProtection` | false | Block rm commands unless allowlisted |
| `dotFilesProtection` | true | Block access to dotfiles (e.g., .env) |
| `outsideWorkspaceProtection` | true | Block writes outside workspace |
| `mcpToolsProtection` | true | Require approval for MCP tools |
| `playwrightProtection` | true | Require approval for browser automation |

### Auto-Run Modes

```javascript
// At line 310158-310163
function migrateAutoRunSettings(composerState) {
    let useYolo = composerState.useYoloMode ?? false;

    // If yoloPrompt is set, disable auto-run (custom prompts need review)
    if (composerState.yoloPrompt) {
        useYolo = false;
    }

    // Apply to all agent modes
    this.getAllModes().forEach(mode => {
        mode.autoRun = useYolo;
    });
}
```

## Decision Service Implementation

### handleApprovalRequest (line 476463-476485)

Routes approval requests to appropriate handlers:

```javascript
async handleApprovalRequest(composerHandle, request) {
    switch (request.operation.type) {
        case "shell":
            return this.handleShellOperation(composerHandle, request.toolCallId, details);
        case "write":
            return this.handleWriteOperation(composerHandle, request.toolCallId, details);
        case "delete":
            return this.handleDeleteOperation(composerHandle, request.toolCallId, details);
        case "mcp":
            return this.handleMcpOperation(composerHandle, request.toolCallId, details);
        default:
            return { approved: false, reason: "Unknown operation type" };
    }
}
```

### runTerminalReviewMode (line 476807-476862)

Waits for user decision on terminal commands:

```javascript
async runTerminalReviewMode(toolFormer, bubbleId, composerHandle, abortController, candidates, toolCallId) {
    const reviewModel = this._toolCallHumanReviewService.getTerminalReviewModelForBubble(composerHandle, bubbleId);

    // Set up review state
    reviewModel.updateReviewData({ candidatesForAllowlist: candidates ?? [] });
    reviewModel.setStatus(ToolCallHumanReviewStatus.REQUESTED);

    // Add to pending decisions for UI tracking
    toolFormer.addPendingDecision(bubbleId, ToolType.RUN_TERMINAL_COMMAND_V2, toolCallId, ...);

    // Wait for status change
    return new Promise(resolve => {
        this._reactiveStorageService.onChangeEffectManuallyDisposed({
            deps: [() => reviewModel.getHumanReviewData()],
            onChange: ({ deps }) => {
                const data = deps[0];
                if (data.status === ToolCallHumanReviewStatus.DONE) {
                    // Translate selected option to result type
                    switch (data.selectedOption) {
                        case TerminalToolHumanReviewOption.RUN:
                            resolve({ type: TerminalToolReviewResultType.RUN });
                            break;
                        case TerminalToolHumanReviewOption.SKIP:
                            resolve({ type: TerminalToolReviewResultType.SKIP });
                            break;
                        // ... other options
                    }
                }
            }
        });
    });
}
```

## Hook System Integration

The `cursorHooksService` (i$) at line 451509 provides a mechanism to intercept and block operations:

```javascript
// When hook rejects a command (line 479401)
if (hookResult === "reject") {
    return Promise.reject({
        modelVisibleErrorMessage: `The terminal command was rejected by a hook that prevents execution of this command. Do not attempt to work around this restriction.`,
        actualErrorMessage: "REJECTED_BY_HOOK"
    });
}

// Hook can return: "allow", "ask", or "reject"
// "ask" forces approval even if auto-run is enabled
if (hookResult === "ask" || needApproval) {
    // Show review UI
}
```

## Allowlist Management

### Adding Commands to Allowlist

```javascript
// At line 476538
case TerminalToolReviewResultType.ALLOWLIST_COMMANDS:
    // Add approved commands to the persistent allowlist
    this._reactiveStorageService.setApplicationUserPersistentStorage(
        "composerState",
        "yoloCommandAllowlist",
        existingList => [
            ...existingList ?? [],
            ...newCommands.filter(cmd => !existingList?.includes(cmd))
        ]
    );
    return { approved: true };
```

### Adding MCP Tools to Allowlist

```javascript
// MCP allowlist check at line 476214
if (settings.mcpAllowedTools.some(pattern => matchMCPToolPattern(serverId, toolName, pattern))) {
    return { needApproval: false };
}
```

## Analytics Events

The system tracks approval decisions:

```javascript
// At line 479497-479500
this.metricsService.increment({
    stat: "terminal.tool.setup_success",
    tags: {
        needs_approval: needApproval ? "true" : "false",
        is_background: isBackground ? "true" : "false"
    }
});

// At line 479723-479727
this.analyticsService.trackEvent("terminal.command_executed", {
    executionMode: "background",
    needsApproval: reviewResult.type !== TerminalToolReviewResultType.RUN,
    model: modelConfig?.modelName,
    composerRequestID: chatGenerationUUID
});
```

## UI Integration Points

### Pending Decisions Tracking

```javascript
// At line 309685
toolFormer.pendingDecisions().userInteractionBubbleIds.some(bubbleId => {
    const data = toolFormer.getBubbleData(bubbleId);
    return data?.tool === ToolType.RUN_TERMINAL_COMMAND_V2
        && data?.additionalData?.reviewData?.status === ToolCallHumanReviewStatus.REQUESTED;
});
```

### Review Data Structure

```javascript
// Stored in bubble's additionalData.reviewData
interface ReviewData {
    status: ToolCallHumanReviewStatus;
    selectedOption: ReviewOption;
    isShowingInput: boolean;
    highlightedOption?: ReviewOption;
    candidatesForAllowlist?: string[];
    finalFeedbackText?: string;
    finalFeedbackBubbleId?: string;
    approvalType?: ApprovalType;
}
```

## Security Considerations

1. **Sudo Always Blocked**: Commands with `sudo` prefix always require approval (line 479135)
2. **rm Protection**: The `rm` command requires approval when `deleteFileProtection` is enabled (line 479130)
3. **Dotfile Protection**: Access to files starting with `.` blocked by default
4. **Workspace Boundary**: Writes outside workspace require approval when `outsideWorkspaceProtection` enabled
5. **Hook Override**: The hook system can force approval or reject regardless of other settings

## Related Tasks

- TASK-71: Sandbox Policy (for sandbox-based auto-approval)
- TASK-58: MCP Allowlist (for MCP tool auto-approval patterns)
- TASK-110: Tool Enum Mapping (for tool type identifiers)
- TASK-30: Shell Exec IPC (for terminal command execution)

## Recommendations for Deeper Investigation

1. **UI Component Analysis**: The actual approval dialog rendering is in React components (need to trace `composerViewsService.triggerScrollToBottom`)
2. **Keyboard Shortcuts**: Review models have `handleComposerShortcut` methods for keyboard navigation
3. **Background Agent Bypass**: Background agents skip approval UI (line 479420: `!ne` check)
4. **Plan Review**: The `PlanReviewModel` handles approval for AI-generated plans (CREATE_PLAN tool)
