# TASK-114: Speculative Import Prediction System

## Overview

Cursor IDE 2.3.41 implements a sophisticated speculative import prediction system that attempts to auto-import symbols before LSP responses arrive. This is achieved by detecting lint errors (undefined symbols), fetching code actions from the language service, then speculatively executing import commands while intercepting the resulting bulk edits.

## Architecture

### Service Registration

```javascript
// Service identifier
q$e = on("importPredictionService")

// Implementation class: pUo
Rn(q$e, pUo, 1)
```

Location: Lines 185454, 1150703

### Core Components

1. **ImportPredictionService** (`pUo` class) - Lines 1149848-1150703
2. **ImportPredictionWidget** (`gUo` class) - Lines 1149770-1149840
3. **Bulk Edit Interception** - Line 779496
4. **Backend Classification API** - `getCppEditClassification` gRPC call

## Key Mechanisms

### 1. Speculative In-Flight Action Tracking

The system tracks speculative actions awaiting LSP bulk edit responses:

```javascript
// Line 1149874
this.actionApplyTimeout = 1e4  // 10 second timeout

// Lines 1150633-1654
this.speculativeInFlightAction = {
    action: e,
    cancellationToken: xs.None,
    resolveEdits: a,
    rejectEdits: l,
    appliedAt: Date.now(),
    symbolName: n
};

setTimeout(() => {
    this.speculativeInFlightAction === d && (
        this.speculativeInFlightAction = void 0,
        l("action was not applied in time")
    )
}, this.actionApplyTimeout);
```

### 2. Bulk Edit Interception (maybeInterceptBulkEdit)

When LSP returns a workspace edit, the service intercepts it:

```javascript
// Lines 779495-779499
return this._importPredictionService?.isEnabled() === !0 &&
       this._importPredictionService.maybeInterceptBulkEdit(s)
    ? Promise.resolve(!1)
    : this._bulkEditService.apply(s, {...});

// Lines 1150673-1150677
maybeInterceptBulkEdit(e) {
    const t = this.getSpeculativeInFlightAction(),
          n = 250;  // 250ms grace period
    return t !== void 0 &&
           e.edits.some(s => "textEdit" in s &&
               s.textEdit.text.match(new RegExp("(?<!\\w)" + t.symbolName)))
        ? (e.edits.length > 0 && (t.resolveEdits(e), this.speculativeInFlightAction = void 0), !0)
        : t !== void 0 && Date.now() - t.appliedAt < n
}
```

The interception logic:
1. Checks if there's a speculative action in flight
2. Matches the edit text against the expected symbol name using regex
3. If matched, resolves the pending promise with the edits
4. Returns `true` to prevent normal bulk edit application

### 3. Lint Error Pattern Matching

Import patterns for different language servers:

```javascript
// Lines 1149853-1149873
this.importPatterns = [
    {
        source: "ts",
        codeMatches: _ => ["2304", "2503", "2552"].includes(_),
        getSymbolName: _ => {
            const E = _.match(/^Cannot find name '(.*?)'/);
            if (E) return E[1]
        }
    },
    {
        source: "Pylance",
        codeMatches: _ => _?.value === "reportUndefinedVariable",
        getSymbolName: _ => {
            const E = _.match(/^"(.*?)" is not defined$/);
            if (E) return E[1]
        }
    },
    {
        source: "basedpyright",
        codeMatches: _ => _?.value === "reportUndefinedVariable",
        getSymbolName: _ => {
            const E = _.match(/^"(.*?)" is not defined$/);
            if (E) return E[1]
        }
    }
]
```

TypeScript error codes:
- **2304**: "Cannot find name 'X'"
- **2503**: "Cannot find namespace 'X'"
- **2552**: "Cannot find name 'X'. Did you mean 'Y'?"

### 4. File Support Detection

```javascript
// Lines 1149894-1149896
doesSupportFile(e) {
    return [".js", ".ts", ".jsx", ".tsx",
            ...this.pythonEnabled() ? [".py"] : []]
        .some(n => e.toString().endsWith(n))
}
```

## Prediction Flow

### Step 1: Detect Lint Errors

```javascript
// Lines 1149897-1149947
async handleUpdatedLintErrors({
    openEditor: e,
    uri: t,
    position: n,
    allMarkers: s,
    source: r
}) {
    // Filter errors by severity
    const l = s.filter(f =>
        [yl.Error, yl.Warning].includes(f.severity) &&
        wu.isEqual(f.resource, t));

    // Sort by distance from cursor
    const h = l.sort((f, g) =>
        Math.abs(f.startLineNumber - n.lineNumber) -
        Math.abs(g.startLineNumber - n.lineNumber))
        .filter(d);

    // Process
    h.length > 0 && await this.maybeAutoImport(e, h)
}
```

### Step 2: Fetch Code Actions

```javascript
// Lines 1149971-1149974
h = await ose(
    this._languageFeaturesService.codeActionProvider,
    n,
    yt.lift(d),
    {
        type: 2,
        triggerAction: B2.QuickFix
    },
    xs.None
);
```

### Step 3: Filter Import Actions

```javascript
// Lines 1149984-1149990
const g = h.allActions.filter(D =>
    !D.action.disabled &&
    (D.action.title.includes("Add import from") ||
     D.action.title.includes("Update import from") ||
     f(D.action))  // Python-specific check
);
```

### Step 4: Backend Classification

The system sends potential imports to the AI backend for ranking:

```javascript
// Lines 1150113-1150138
const H = new oMr({
    cppRequest: {
        ...T,
        controlToken: EW.LOUD,
        modelName: P(),
        linterErrors: M
    },
    suggestedEdits: D,
    markerTouchesGreen: B,
    currentFileContentsForLinterErrors: this.cppMethods?.truncateCurrentFile(...)
});

const Z = await (await this.aiClient()).getCppEditClassification(H, {
    headers: { ...G }
});
```

### Step 5: Noop Decision Logic

```javascript
// Lines 1150171-1150188
shouldNoop({
    bestEditLogprobs: e,
    generationEditLogprobs: t,
    opEditString: n,
    symbolName: s,
    markerTouchesGreen: r
}) {
    // Find token position for the import text
    const a = findLastIndex(e.tokens, (w, _) =>
        e.tokens.slice(_).join("").trim().startsWith(n.trim()));

    // Find symbol within tokens
    const l = e.tokens.findIndex((w, _) =>
        _ >= a && !!e.tokens.slice(a, _).join("").trim()
            .match(new RegExp(`\\b${s}\\b`)));

    const d = e.tokenLogprobs[a],
          h = Math.min(0, ...e.tokenLogprobs.slice(a + 1, l));

    const g = r ? 2 : 1;  // Boost if touches green highlight

    // High confidence: don't noop
    if (f && f.includes(s) && Math.exp(d) * g > .1) return false;

    // Low confidence: noop
    return Math.exp(d + h) * g < .02;
}
```

## Caching System

### Seen Lint Errors Cache

```javascript
// Line 1149853
this.seenLintErrors = new Xp(100)  // LRU cache with 100 entries

// Cache key structure (Line 1150209-1150215)
getKey(e, t) {
    return JSON.stringify({
        owner: t.owner,
        uri: t.resource.toString(),
        symbolName: this.getSymbolName(t),
        startLineNumber: t.startLineNumber
    })
}
```

### Lint Error Status States

```javascript
// Various statuses throughout the code:
- "debouncing"   // Initial detection, waiting
- "computing"    // Fetching code actions
- "pending"      // Import suggestion ready
- "accepted"     // User accepted
- "rejected"     // User rejected
- "noop"         // System decided not to show
- "no-actions"   // No import actions available
- "error"        // Error occurred
```

### Pending Imports Queue

```javascript
// Line 1149853
this.pendingImports = []

// Limited to 20 entries (Line 1150192)
const a = [...this.pendingImports]
    .sort((d, h) =>
        (this.getLintError(e, h.marker)?.seenAt.getTime() ?? 0) -
        (this.getLintError(e, d.marker)?.seenAt.getTime() ?? 0))
    .slice(0, 20);
```

### Recent Green Ranges Cache

```javascript
// Line 1149853
this.recentGreenRanges = []

// Track AI-generated code regions (Lines 1150528-1150534)
handleNewGreens(e, t) {
    const n = Date.now();
    this.recentGreenRanges = this.recentGreenRanges
        .filter(s => n - s.timestamp <= 3e4)  // 30 second expiry
        .concat(t.map(s => ({
            uri: e.uri,
            range: s,
            timestamp: n
        })))
}
```

## Autocomplete Integration

### Coordination with CPP (Cursor Prediction Provider)

```javascript
// Line 1145979 - Block CPP suggestions while import showing
if (this.getCurrentSuggestion() === void 0 &&
    !(this.persistentStorage().cppAutoImportEnabled &&
      this._importPredictionService.isShowingImportSuggestion())) {
    // Proceed with CPP
}

// Line 1147591 - Similar check during suggestion display
this.persistentStorage().cppAutoImportEnabled &&
this._importPredictionService.isShowingImportSuggestion()

// Line 1148562 - Tab acceptance coordination
if (t || (t = this._codeEditorService.getActiveCodeEditor()),
    !t || !q4m(e) && this.hasMultipleLinesSelection() &&
    !this.isInVimNonInsertMode() ||
    this.persistentStorage().cppAutoImportEnabled &&
    t !== null &&
    this._importPredictionService.maybeAcceptShownImport(t)) return;
```

### Widget Conflict Resolution

```javascript
// Lines 1150567-1150580
hideWidgetsIfConflictsWithCppSuggestion(e, t) {
    const n = this.shownImportInfo;
    if (n) {
        const { shownImport: s, decorationId: r } = n;
        if (this.importIsInOpenEditor(s, e)) {
            const o = e.getModel();
            if (o === null) return;
            const a = o.getDecorationRange(r);
            a !== null &&
            t.startLineNumber <= a.startLineNumber &&
            t.endLineNumberExclusive > a.startLineNumber &&
            this.hideShownImport(e)
        }
    }
}
```

## UI Widget

### ImportPredictionWidget Display

```javascript
// Lines 1149799-1149805
updateTextContent() {
    const e = this._actionTitle.match(
        /import from "([^"]*)"|"from ((?:\w|\.|:)+) import |"import ((?:\w|\.|:)+)"|"import ((?:\w|\.|:)+) as ((?:\w|\.|:)+)"/
    );
    const t = e ? e[1] ?? e[2] ?? e[3] ?? e[4] ?? "" : "";
    const n = this._reactiveStorageService
        .applicationUserPersistentStorage
        .howManyTimesHasUserAcceptedImportPrediction ?? 0;
    const s = this._isHovering || n < 3;

    const r = this._tabKeybinding
        ? ` (press ${this._tabKeybinding} or ESC)`
        : " (press TAB or ESC)";

    // Full text for new users or hovering
    if (s) {
        this._textDomNode.textContent =
            `import ${this._symbolName}${r}`;
    } else {
        // Compact text after 3 acceptances
        this._textDomNode.textContent =
            `\u2191 import from "${t}"`;  // Unicode arrow
    }
}
```

### Decoration Styles

```javascript
// Lines 1150343-1150349
const o = this._reactiveStorageService
    .applicationUserPersistentStorage
    .cppAutoImportDecorationStyle;

const a = [{
    range: new yt(t.marker.startLineNumber, ...),
    options: {
        className: o === "squiggle"
            ? "squiggly-ai cpp-pending-import-decoration"
            : "auto-import-suggestion-blue-background",
        stickiness: 1,
        zIndex: 5,
    }
}];
```

## Configuration

### Enable/Disable Logic

```javascript
// Lines 1150598-1150599
isEnabled() {
    return !!(
        this._reactiveStorageService
            .applicationUserPersistentStorage.cppAutoImportEnabled &&
        !this._reactiveStorageService
            .applicationUserPersistentStorage.backendHasDisabledCppAutoImport &&
        this._reactiveStorageService
            .applicationUserPersistentStorage.cppEnabled
    )
}
```

### Python Support Flag

```javascript
// Lines 1149891-1149892
pythonEnabled() {
    return this._reactiveStorageService
        .applicationUserPersistentStorage
        .cppConfig?.importPredictionConfig?.pythonEnabled === !0 ||
        this._reactiveStorageService
        .applicationUserPersistentStorage
        .userHasEnabledImportPredictionForPython === !0
}
```

## Latency Monitoring

```javascript
// Lines 1150461-1150477
handleLatency(e, t) {
    this.lastLatencies.push(e);

    if (e > this.shouldLogEventTimesThreshold) {  // > 10ms
        console.warn(`[Cpp] showCorrectUI took ${e}ms...`);
    }

    // Report bug if average latency too high
    if (this.lastLatencies.length > this.howManyLatenciesToStore) {
        const avg = this.lastLatencies.reduce((s, r) => s + r, 0) /
                    this.lastLatencies.length;
        if (avg > this.tooLongLatencyThreshold && !this.hasReportedBug) {
            // Report to backend
            this.hasReportedBug = true;
            (await this.aiClient()).reportBug({
                bug: `average latency too high: ${avg}ms`,
                bugType: aD.MISC_AUTOMATIC_ERROR
            });
        }
    }
}
```

## gRPC API

### GetCppEditClassification Request

```javascript
// Lines 145217-145250
oMr = class H0i extends K {
    static typeName = "aiserver.v1.GetCppEditClassificationRequest"
    static fields = v.util.newFieldList(() => [
        { no: 1, name: "cpp_request", kind: "message", T: jas },
        { no: 25, name: "suggested_edits", kind: "message", T: Yas, repeated: true },
        { no: 26, name: "marker_touches_green", kind: "scalar", T: 8 },
        { no: 27, name: "current_file_contents_for_linter_errors", kind: "scalar", T: 9 }
    ])
}
```

### GetCppEditClassification Response

```javascript
// Lines 145263-145295
kml = class $0i extends K {
    static typeName = "aiserver.v1.GetCppEditClassificationResponse"
    static fields = v.util.newFieldList(() => [
        { no: 1, name: "scored_edits", kind: "message", T: Xas, repeated: true },
        { no: 2, name: "noop_edit", kind: "message", T: Xas },
        { no: 3, name: "should_noop", kind: "scalar", T: 8 },
        // ... generation_edit field likely follows
    ])
}
```

## Important Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `actionApplyTimeout` | 10000ms | Time to wait for LSP bulk edit |
| `maxConcurrentCodeActionsRequests` | 5 | Parallel code action requests |
| `seenLintErrors` capacity | 100 | LRU cache size |
| `pendingImports` max | 20 | Maximum pending imports |
| `recentGreenRanges` expiry | 30000ms | AI code region tracking |
| `tooLongLatencyThreshold` | 1.5ms | Latency warning threshold |
| `shouldLogEventTimesThreshold` | 10ms | Performance logging threshold |

## Vim Mode Integration

```javascript
// Lines 1150512-1150516
isInVimInsertMode() {
    const e = this._statusbarService.getViewModel();
    for (const t of [...e.getEntries(0), ...e.getEntries(1)])
        if (t.id === "vscodevim.vim.primary" &&
            ["INSERT"].some(n => t.container.innerText.includes(n)))
            return true;
    return false;
}
```

## Summary

The speculative import prediction system is a complex feature that:

1. **Monitors lint errors** for undefined symbol patterns from TypeScript/Pylance/basedpyright
2. **Fetches code actions** from the language server for potential imports
3. **Sends to backend** for AI-based classification and ranking
4. **Speculatively executes** import commands before LSP fully responds
5. **Intercepts bulk edits** to match them with pending speculative actions
6. **Displays widget** with Tab/ESC acceptance UI
7. **Coordinates with CPP** to avoid suggestion conflicts

The system prioritizes imports for symbols near recently generated AI code ("green ranges") and uses log probability thresholds to decide whether to show suggestions or "noop".
