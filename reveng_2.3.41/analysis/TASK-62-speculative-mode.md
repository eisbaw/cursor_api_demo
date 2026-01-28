# TASK-62: Speculative Full-File Execution Mode Analysis

## Overview

The "speculative-full-file" mode in Cursor Composer involves two distinct but related concepts:

1. **Source Identifier for Inline Diffs**: A constant `qZ = "speculative-full-file"` used to identify the origin of inline diff changes
2. **Speculative Summarization**: A proactive summarization system that prepares conversation summaries before they're needed

## Key Components

### 1. The `speculative-full-file` Constant

**Location**: Line 303071 in `workbench.desktop.main.js`

```javascript
qZ = "speculative-full-file"
```

This constant serves as a **source identifier** for inline diffs created by the composer system. When the composer applies changes to files, it tags the diff with this source so the system can:
- Filter diffs by source type
- Track which diffs came from the full-file editing pipeline
- Manage undo/redo operations appropriately

### 2. Usage of `qZ` as Source

The constant is used when creating inline diffs in multiple places:

**Line 301665** - Restoring diffs from storage:
```javascript
const D = {
    uri: p,
    generationUUID: h,
    currentRange: w,
    originalTextLines: d,
    prompt: "hi",
    isHidden: !1,
    attachedToPromptBar: !1,
    source: qZ,  // "speculative-full-file"
    createdAt: Date.now(),
    // ...
}
```

**Line 471181** - Creating new diffs from AI edits:
```javascript
const T = {
    uri: t,
    generationUUID: E,
    currentRange: g,
    originalTextLines: f,
    prompt: "hi2",
    source: qZ,  // "speculative-full-file"
    composerMetadata: {...}
}
```

### 3. Filtering by Source

The system filters diffs using this source identifier:

**Line 494200** - Accept All Changes command:
```javascript
s = t.inlineDiffs.nonReactive().filter(o => o.source === qZ);
```

**Line 1099072** - UI rendering of diffs:
```javascript
n = ve(() => t().filter(f => f.source === qZ).sort((f, g) => (f.createdAt ?? 0) - (g.createdAt ?? 0)))
```

## Speculative Summarization System

### Purpose

When a conversation approaches its context window limit, Cursor proactively generates summaries to prepare for truncation. This is the "speculative" part - it happens before summaries are actually needed.

### Configuration

**Dynamic config parameter**: `client_speculative_summarization_config`

**Schema** (line 294994):
```javascript
client_speculative_summarization_config: {
    tokenUsageThresholdPercentage: number,  // Default: 70-80%
    tolerancePercentage: number,            // Default: 10%
    inflightMaxAgeMinutes: number,          // Default: 5
    speculativeStreamTimeoutMinutes: number // Default: 5
}
```

### Trigger Logic

**Lines 490354-490374** - During streaming:
```javascript
// Check context usage every second during streaming
if (performance.now() - Ic >= 1000) {
    const usagePercent = hBe.getContextUsagePercentage(composerId, composerDataService);

    if (typeof usagePercent === "number") {
        const threshold = experimentService.getDynamicConfigParam(
            "client_speculative_summarization_config",
            "tokenUsageThresholdPercentage"
        ) ?? 80;
        const tolerance = experimentService.getDynamicConfigParam(
            "client_speculative_summarization_config",
            "tolerancePercentage"
        ) ?? 10;

        if (usagePercent >= threshold) {
            // Check if a nearby cached summary already exists
            const hasNearby = composerDataService.hasNearbyCachedSummary(o, usagePercent, tolerance);
            if (!hasNearby) {
                // Trigger speculative summarization
                this.getSpeculativeSummary(composerId);
            }
        }
    }
}
```

### Summarization Flow

**getSpeculativeSummary** method (line 492000):

1. Check if summarization already in-flight
2. Get encryption key for the conversation
3. Prepare cutoff conversation and context
4. Call `streamSpeculativeSummaries` API
5. Cache received summaries on conversation bubbles

```javascript
async getSpeculativeSummary(composerId) {
    // Prevent duplicate requests
    const existing = this._speculativeSummarizationInFlight.get(composerId);
    if (existing) {
        const ageMinutes = (Date.now() - existing) / 60000;
        if (ageMinutes < inflightMaxAge) return;
    }

    this._speculativeSummarizationInFlight.set(composerId, Date.now());

    // Prepare request with encryption key
    const encryptionKey = composerData.speculativeSummarizationEncryptionKey;

    // Stream summaries from server
    for await (const summary of chatClient.streamSpeculativeSummaries(request)) {
        // Cache summary on the relevant bubble
        composerDataService.updateComposerDataSetStore(composerId, m =>
            m("conversationMap", bubbleId, "cachedConversationSummary", summary)
        );
    }
}
```

### Encryption

Summaries are encrypted using a per-composer encryption key:

**Line 215139** - Key generation:
```javascript
speculativeSummarizationEncryptionKey: crypto.getRandomValues(new Uint8Array(32))
```

The key is serialized/deserialized for persistence and passed to the server for summary encryption.

## Mode Switching Logic

### Composer Modes Service

**Line 310227** - `getComposerUnifiedMode`:
```javascript
getComposerUnifiedMode(composerId) {
    const data = composerDataService.getComposerData(composerId);
    const mode = data?.unifiedMode ?? "agent";
    if (this.checkIfModeExists(mode)) return mode;
    // Fallback to "agent" if mode doesn't exist
    return "agent";
}
```

### Mode Types

Protected mode IDs (line 310309):
```javascript
["agent", "triage", "plan", "spec", "debug", "background", "chat"]
```

### Spec Mode

**Feature Gate**: `spec_mode`

When enabled (line 309217):
```javascript
isSpecModeEnabled() {
    return this._experimentService.checkFeatureGate("spec_mode") === true
}
```

The spec mode is used for:
- Creating sub-composers for plan steps
- Running specialized "spec" queries on plans
- Managing plan-based workflows

### Mode Switching

**Line 310240** - `setComposerUnifiedMode`:
```javascript
setComposerUnifiedMode(composerId, mode) {
    // Special handling for "plan" mode - validate model compatibility
    if (mode === "plan") {
        // Check if current model supports plan mode
        // Switch to compatible model if needed
    }

    // Update composer data
    composerDataService.updateComposerDataSetStore(composerId, n => {
        n("unifiedMode", mode)
    });

    // Special handling for debug mode
    if (mode === "debug") {
        this.maybeStartDebugServer();
    }
}
```

## Speculative Linter

**Feature Gate**: `use_speculative_linter`

A separate speculative feature that pre-runs linting while code is being generated, allowing faster feedback when edits complete.

## Speculative Import Action

**Lines 1150633-1150677** - Import prediction:

The system speculatively executes import commands before receiving LSP responses:

```javascript
this.speculativeInFlightAction = {
    action: command,
    cancellationToken: CancellationToken.None,
    resolveEdits: resolve,
    rejectEdits: reject,
    appliedAt: Date.now(),
    symbolName: importSymbol
};

// Execute command speculatively
const changes = await commandService.executeCommand(command.id, ...args);

// If matching bulk edit arrives, intercept it
maybeInterceptBulkEdit(bulkEdit) {
    if (bulkEdit.edits.some(e => e.textEdit.text.match(new RegExp(symbolName)))) {
        // Resolve with pre-computed edits
        speculativeAction.resolveEdits(bulkEdit);
        return true; // Intercepted
    }
}
```

## Summary Table

| Feature | Constant/Config | Purpose |
|---------|----------------|---------|
| `speculative-full-file` | `qZ` | Source identifier for composer inline diffs |
| Speculative Summarization | `client_speculative_summarization_config` | Proactive conversation summaries |
| Speculative Linter | `use_speculative_linter` | Pre-run linting during generation |
| Speculative Import | `speculativeInFlightAction` | Pre-execute import commands |
| Speculative GPT5 Routing | `should_speculatively_route_gpt5` | Route requests speculatively |

## Key Insights

1. **"Speculative-full-file" is not an execution mode** - it's a source label for inline diffs, indicating changes came from the full-file edit pipeline rather than cmd-K or other sources.

2. **Speculative summarization is proactive** - it triggers when context usage exceeds ~70-80%, generating summaries before they're needed for truncation.

3. **Encryption is mandatory** - all speculative summaries are encrypted with a per-composer key for security.

4. **Mode switching is independent** - composer modes (agent, plan, spec, chat, etc.) are separate from the speculative features.

5. **Multiple speculative systems exist** - summarization, linting, imports, and routing all have independent speculative implementations.

## Related Files

- `workbench.desktop.main.js` - Main source (1.17M lines)
- Lines 301422-303071: InlineDiffService and `lre` class
- Lines 490354-490400: Speculative summarization triggers
- Lines 492000-492114: `getSpeculativeSummary` implementation
- Lines 1150633-1150677: Speculative import action
