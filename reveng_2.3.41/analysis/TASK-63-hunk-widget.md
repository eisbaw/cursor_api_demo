# TASK-63: Hunk-Level Accept/Reject UI Widget Implementation Analysis

## Overview

This document analyzes the hunk-level accept/reject UI widget implementation in Cursor IDE 2.3.41, focusing on how diff changes are presented to users with interactive accept/reject controls.

## Key Classes and Components

### 1. HunkData Manager (`JEo` / `TYe`)

**File Location:** `workbench.desktop.main.js` around line 979887

The `JEo` class manages hunk tracking and state:

```
Key Properties:
- _HUNK_TRACKED_RANGE: Decoration descriptor for tracking hunk ranges
- _HUNK_THRESHOLD: 8 (lines threshold for merging adjacent hunks)
- _data: Map<Kum, HunkState> - stores hunk state information
- _ignoreChanges: boolean - flag to prevent recursive change handling
```

**Hunk States (`_bu` enum):**
- `0` = Pending
- `1` = Accepted
- `2` = Rejected

**Key Methods:**
- `recompute(editState, diff)` - Recomputes hunks from diff, merges adjacent ones within threshold
- `getInfo()` - Returns array of hunk info objects with methods: `getState()`, `isInsertion()`, `getRangesN()`, `getRanges0()`, `discardChanges()`, `acceptChanges()`
- `discardAll()` - Rejects all pending hunks
- `_mirrorChanges(event)` - Synchronizes changes between model0 (original) and modelN (modified)

### 2. Hunk Info Structure (`Kum`)

**File Location:** Line 980068

```javascript
class Kum {
    original: LineRange     // Original line range
    modified: LineRange     // Modified line range
    changes: InnerChange[]  // Array of character-level changes
}
```

### 3. Session Class (`wbu`)

**File Location:** Line 979802

Manages the inline chat editing session:

```
Key Properties:
- textModel0: Original text model
- textModelN: Modified text model (current)
- hunkData: JEo instance
- chatModel: Chat model reference
- _teldata: Telemetry data including acceptedHunks, discardedHunks counters
```

### 4. Strategy Class (`zEo`)

**File Location:** Line 980475

Implements the editing strategy with hunk UI rendering:

**Key Properties:**
- `_hunkData: Map<HunkInfo, DisplayData>` - Maps hunks to their UI representation
- `_lensActionsFactory: U4s` - Factory for creating code lens action widgets
- `_progressiveEditingDecorations` - Decorations for progressive edits

**Display Data Structure:**
```javascript
{
    hunk: HunkInfo,
    decorationIds: string[],
    diffViewZoneId: string,
    diffViewZone: ViewZone,
    lensActionsViewZoneIds: string[],
    distance: number,
    position: Position,
    acceptHunk: () => void,
    discardHunk: () => void,
    toggleDiff: (() => void) | undefined,
    remove: () => void,
    move: (forward: boolean) => void
}
```

### 5. Diff Hunk Widget (`$wt` / `fIo`)

**File Location:** Line 1000594

The main widget class for displaying hunk accept/reject controls:

```javascript
class $wt {
    static _idPool = 0;  // Widget ID counter

    constructor(diffInfo, change, versionId, editor, lineDelta, instantiationService) {
        // Creates overlay widget with toolbar
        this._domNode = document.createElement("div");
        this._domNode.className = "chat-diff-change-content-widget";

        // Toolbar with ChatEditingEditorHunk menu
        const toolbar = instantiationService.createInstance(
            tD,                           // Toolbar class
            this._domNode,
            Me.ChatEditingEditorHunk,     // Menu ID
            {
                telemetrySource: "chatEditingEditorHunk",
                hiddenItemStrategy: -1,
                toolbarOptions: { primaryGroup: () => true },
                menuOptions: { renderShortTitle: true, arg: this }
            }
        );
    }

    layout(lineNumber) {
        // Positions widget at right side of editor
        const lineHeight = editor.getOption(68);
        const { contentLeft, contentWidth, verticalScrollbarWidth } = editor.getLayoutInfo();
        this._position = {
            stackOridinal: 1,
            preference: {
                top: editor.getTopForLineNumber(lineNumber) - scrollTop - lineHeight * lineDelta,
                left: contentLeft + contentWidth - (2 * verticalScrollbarWidth + widgetWidth)
            }
        };
    }

    toggle(visible) {
        this._domNode.classList.toggle("hover", visible);
    }

    async reject() {
        if (this._versionId !== editor.getModel()?.getVersionId()) return false;
        return this._diffInfo.undo(this._change);
    }

    async accept() {
        if (this._versionId !== editor.getModel()?.getVersionId()) return false;
        return this._diffInfo.keep(this._change);
    }
}
```

### 6. Lens Actions Factory (`U4s`)

**File Location:** Line 980324

Creates code lens style action widgets above hunks:

```javascript
class U4s extends Ve {
    constructor(editor) {
        // Generates unique style class per editor
        this._styleClassName = "_conflictActionsFactory_" + hash(editor.getId());
        // Creates style element for lens appearance
    }

    _getLayoutInfo() {
        // Calculates font size and code lens height
        const ratio = Math.max(1.3, editor.getOption(68) / editor.getOption(54));
        return { fontSize, codeLensHeight: fontSize * ratio | 0 };
    }

    createWidget(changeAccessor, lineNumber, items, viewZoneIds) {
        const { codeLensHeight } = this._getLayoutInfo();
        return new Qum(editor, changeAccessor, lineNumber, codeLensHeight + 2,
                       this._styleClassName, items, viewZoneIds);
    }
}
```

### 7. Fixed Zone Widget (`Yum`)

**File Location:** Line 980295

Base class for widgets that appear at fixed positions in the editor:

```javascript
class Yum extends Ve {
    static counter = 0;

    constructor(editor, viewZoneAccessor, lineNumber, height, viewZoneIds) {
        // Creates view zone at line number
        this.viewZoneId = viewZoneAccessor.addZone({
            domNode: document.createElement("div"),
            afterLineNumber: lineNumber,
            heightInPx: height,
            ordinal: 50001,
            onComputedHeight: (h) => { this.widgetDomNode.style.height = `${h}px`; },
            onDomNodeTop: (top) => { this.widgetDomNode.style.top = `${top}px`; }
        });

        // Also registers as overlay widget for proper positioning
        editor.addOverlayWidget(this.overlayWidget);
    }
}
```

### 8. Conflict Actions Widget (`Qum`)

**File Location:** Line 980446

Extends `Yum` to render action buttons:

```javascript
class Qum extends Yum {
    constructor(editor, accessor, lineNumber, height, className, items, viewZoneIds) {
        this._domNode = nl("div.merge-editor-conflict-actions").root;
        this._domNode.classList.add(className);

        // Reactive state updates
        this._register(Na(reader => {
            const actions = items.read(reader);
            this.setState(actions);
        }));
    }

    setState(items) {
        const elements = [];
        for (const item of items) {
            // Separator between actions
            if (!first) elements.push(et("span", void 0, " | "));

            // Action link or plain text
            if (item.action) {
                elements.push(et("a", {
                    title: item.tooltip,
                    role: "button",
                    onclick: () => item.action()
                }, ...renderLabelWithIcons(item.text)));
            } else {
                elements.push(et("span", { title: item.tooltip },
                              ...renderLabelWithIcons(item.text)));
            }
        }
        clearNode(this._domNode);
        append(this._domNode, ...elements);
    }
}
```

### 9. Hunk Actions Integration (`o6s` class)

**File Location:** Line 1000263

Integrates diff hunks with the editor:

```javascript
class o6s {
    static _diffLineDecorationData = ModelDecorationOptions.register({
        description: "diff-line-decoration"
    });

    constructor(entry, editor, diffInfo, chatAgentService, editorService,
                accessibilitySignalService, instantiationService) {
        this._diffHunkWidgets = [];
        this._viewZones = [];

        // Renders diff hunks with widgets
        this._diffHunksRenderStore.add(autorun(reader => {
            // For each change in diff...
            const widget = editor.invokeWithinContext(ctx =>
                ctx.get(Ct).createInstance($wt, entry, change,
                    editor.getModel().getVersionId(), editor, lineDelta));
            widget.layout(change.modified.startLineNumber);
            this._diffHunkWidgets.push(widget);
        }));

        // Mouse hover handling
        this._diffHunksRenderStore.add(editor.onMouseMove(event => {
            // Show/hide widgets on hover
            if (event.target.type === 12) {  // OVERLAY_WIDGET
                const widget = this._diffHunkWidgets.find(w => w.getId() === event.target.detail);
                toggleWidget(widget);
            }
        }));
    }

    rejectNearestChange(widget) {
        widget = widget ?? this._findClosestWidget();
        if (widget instanceof $wt) {
            widget.reject();
            this.next(true);
        }
    }

    acceptNearestChange(widget) {
        widget = widget ?? this._findClosestWidget();
        if (widget instanceof $wt) {
            widget.accept();
            this.next(true);
        }
    }
}
```

## Action Handling

### Hunk Action Types (`Ebu` enum)

```javascript
enum Ebu {
    Accept = 0,
    Discard = 1,
    MoveNext = 2,
    MovePrev = 3,
    ToggleDiff = 4
}
```

### performHunkAction Method

**File Location:** Line 980536

```javascript
performHunkAction(hunkInfo, action) {
    const displayData = this._findDisplayData(hunkInfo);
    if (!displayData) {
        // No hunk found - fire accept/discard for session
        if (action === 0) this._onDidAccept.fire();
        else if (action === 1) this._onDidDiscard.fire();
        return;
    }

    switch (action) {
        case 0: displayData.acceptHunk(); break;
        case 1: displayData.discardHunk(); break;
        case 2: displayData.move(true); break;   // Next
        case 3: displayData.move(false); break;  // Previous
        case 4: displayData.toggleDiff?.(); break;
    }
}
```

### Accept/Discard Implementation

The actual edit operations in `JEo.getInfo()`:

```javascript
// acceptChanges (line 980048)
acceptChanges: () => {
    if (state === 0) {  // Only if Pending
        const edits = [];
        const rangesN = getRangesN();
        const ranges0 = getRanges0();
        for (let i = 1; i < ranges0.length; i++) {
            const range0 = ranges0[i];
            const value = textModelN.getValueInRange(rangesN[i]);
            edits.push(EditOperation.replace(range0, value));
        }
        textModel0.pushEditOperations(null, edits, () => null);
        state = 1;  // Accepted
    }
}

// discardChanges (line 980042)
discardChanges: () => {
    if (state === 0) {  // Only if Pending
        const edits = _discardEdits(this);  // Get revert edits
        textModelN.pushEditOperations(null, edits, () => null);
        state = 2;  // Rejected
        editState.applied--;
    }
}
```

## UI Styling

### CSS Classes

- `.chat-diff-change-content-widget` - Main widget container
- `.inline-chat-inserted-range` - Decoration for inserted ranges
- `.inline-chat-inserted-range-linehighlight` - Line highlight for insertions
- `.merge-editor-conflict-actions` - Container for action buttons
- `.inline-chat-original-zone2` - View zone for showing original text
- `.accessible-diff-view` - Container for accessibility view

### Menu IDs

- `Me.ChatEditingEditorHunk` - Menu ID for hunk toolbar actions
- `Bfc` - Menu ID for inline chat hunk lens actions

## Accessibility

### Accessible Diff View

The `showAccessibleHunk` method provides screen reader support:

```javascript
showAccessibleHunk(session, hunk) {
    this._elements.accessibleViewer.classList.remove("hidden");
    this._accessibleViewer.value = instantiationService.createInstance(
        Gks,  // Accessible hunk viewer
        this._elements.accessibleViewer,
        session,
        hunk,
        new XIc(parentEditor, session, hunk)  // Diff model adapter
    );
}
```

Configuration: `inlineChat.accessibleDiffView` with values: "auto", "on", "off"

### Accessibility Signals

Audio signals for screen readers:
- `wg.diffLineDeleted` - Played when cursor enters deleted line
- `wg.diffLineInserted` - Played when cursor enters inserted line
- `wg.diffLineModified` - Played when cursor enters modified line
- `wg.editsKept` - Played when edits are accepted

## Telemetry

The session tracks:
- `acceptedHunks` - Count of accepted hunks
- `discardedHunks` - Count of rejected hunks
- `edits` - Total edit count
- `finishedByEdit` - Whether session ended due to manual editing

## Integration Points

### InlineChat Controller (`k$` / `YEo`)

**File Location:** Line 980925

```javascript
class k$ {
    static ID = "editor.contrib.inlineChatController";

    acceptHunk(hunkInfo) {
        return this._strategy?.performHunkAction(hunkInfo, 0);  // Accept
    }

    discardHunk(hunkInfo) {
        return this._strategy?.performHunkAction(hunkInfo, 1);  // Discard
    }

    toggleDiff(hunkInfo) {
        return this._strategy?.performHunkAction(hunkInfo, 4);  // Toggle
    }
}
```

### InlineChat Controller 2 (`IYe` / `V4s`)

**File Location:** Line 981386

Newer controller variant:
```javascript
class IYe {
    static ID = "editor.contrib.inlineChatController2";
}
```

## Summary

The hunk-level UI implementation consists of:

1. **Data Layer** (`JEo`/`Kum`): Manages hunk state, tracking decorations, and edit operations
2. **Session Layer** (`wbu`): Coordinates between original and modified models
3. **Strategy Layer** (`zEo`): Renders UI and handles user interactions
4. **Widget Layer** (`$wt`, `Qum`, `Yum`): Overlay and view zone widgets for buttons
5. **Controller Layer** (`k$`, `IYe`): API for external components to trigger actions

The system uses VS Code's decoration and view zone APIs to overlay interactive widgets on the editor, with reactive state management for real-time updates as the user navigates and interacts with changes.

## Investigation Avenues for Future Tasks

1. **Menu Action Registration**: Investigate how `Me.ChatEditingEditorHunk` menu items are registered
2. **Keybinding Integration**: How keyboard shortcuts map to hunk actions
3. **Progressive Edit Animation**: The `makeProgressiveChanges` method with typing animation
4. **Multi-Hunk Navigation**: The move next/previous functionality
5. **Undo/Redo Integration**: How hunk operations integrate with editor undo stack
