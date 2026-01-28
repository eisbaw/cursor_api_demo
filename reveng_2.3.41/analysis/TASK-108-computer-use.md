# TASK-108: ComputerUseToolCall Action Types Deep Dive

**Source:** `reveng_2.3.41/beautified/workbench.desktop.main.js`
**Analysis Date:** 2026-01-28
**Related:** TASK-26-tool-schemas.md, TASK-52-toolcall-schema.md

## Overview

Cursor implements a `ComputerUseToolCall` tool enabling AI agents to control the computer via mouse, keyboard, and screen capture actions. This is a client-side tool (tool enum value 54) that executes locally within the Cursor IDE.

### Source Files

The implementation originates from:
- `out-build/proto/agent/v1/computer_use_tool_pb.js` (line ~103307)
- `src/proto/agent/v1/computer_use_tool_pb.ts` (line ~241664)
- `../packages/agent-exec/src/computer-use.ts` (line ~464959)

### Feature Flag

Computer use is gated by a feature flag:

```javascript
cloud_agent_computer_use: {
    client: false,   // Server-controlled flag
    default: false   // Disabled by default
}
```

**Location:** Line ~294413

---

## Enums

### MouseButton (agent.v1.MouseButton)
**Location:** Line ~103310

```protobuf
enum MouseButton {
  MOUSE_BUTTON_UNSPECIFIED = 0;
  MOUSE_BUTTON_LEFT = 1;
  MOUSE_BUTTON_RIGHT = 2;
  MOUSE_BUTTON_MIDDLE = 3;
  MOUSE_BUTTON_BACK = 4;
  MOUSE_BUTTON_FORWARD = 5;
}
```

JavaScript enum:
```javascript
{
  UNSPECIFIED: 0,
  LEFT: 1,
  RIGHT: 2,
  MIDDLE: 3,
  BACK: 4,
  FORWARD: 5
}
```

### ScrollDirection (agent.v1.ScrollDirection)
**Location:** Line ~103331

```protobuf
enum ScrollDirection {
  SCROLL_DIRECTION_UNSPECIFIED = 0;
  SCROLL_DIRECTION_UP = 1;
  SCROLL_DIRECTION_DOWN = 2;
  SCROLL_DIRECTION_LEFT = 3;
  SCROLL_DIRECTION_RIGHT = 4;
}
```

JavaScript enum:
```javascript
{
  UNSPECIFIED: 0,
  UP: 1,
  DOWN: 2,
  LEFT: 3,
  RIGHT: 4
}
```

---

## Core Types

### Coordinate (agent.v1.Coordinate)
**Location:** Line ~103354

Screen coordinates for mouse positioning.

```protobuf
message Coordinate {
  int32 x = 1;
  int32 y = 2;
}
```

| Field | Type | Description |
|-------|------|-------------|
| x | int32 | X coordinate (pixels) |
| y | int32 | Y coordinate (pixels) |

---

## Action Types (11 Total)

The `ComputerUseAction` message is a oneof containing exactly one action:

```protobuf
message ComputerUseAction {
  oneof action {
    MouseMoveAction mouse_move = 1;
    ClickAction click = 2;
    MouseDownAction mouse_down = 3;
    MouseUpAction mouse_up = 4;
    DragAction drag = 5;
    ScrollAction scroll = 6;
    TypeAction type = 7;
    KeyAction key = 8;
    WaitAction wait = 9;
    ScreenshotAction screenshot = 10;
    CursorPositionAction cursor_position = 11;
  }
}
```

### 1. MouseMoveAction (agent.v1.MouseMoveAction)
**Location:** Line ~103518

Move the mouse cursor to a coordinate.

```protobuf
message MouseMoveAction {
  Coordinate coordinate = 1;
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| coordinate | Coordinate | Yes | Target position |

**UI Display:** "Move mouse to (X, Y)" / "Moved mouse to (X, Y)"

---

### 2. ClickAction (agent.v1.ClickAction)
**Location:** Line ~103548

Perform a mouse click.

```protobuf
message ClickAction {
  optional Coordinate coordinate = 1;
  MouseButton button = 2;
  int32 count = 3;
  optional string modifier_keys = 4;
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| coordinate | Coordinate | No | Click position (uses current cursor if omitted) |
| button | MouseButton | Yes | Which button to click |
| count | int32 | Yes | Number of clicks (1=single, 2=double, 3=triple) |
| modifier_keys | string | No | Modifier keys (e.g., "ctrl", "shift") |

**UI Display:**
- Single: "Click at (X, Y)"
- Double: "Double-Click at (X, Y)"
- Triple: "Triple-Click at (X, Y)"
- Right-click: "Right-Click at (X, Y)"
- Middle-click: "Middle-Click at (X, Y)"

---

### 3. MouseDownAction (agent.v1.MouseDownAction)
**Location:** Line ~103595

Press mouse button down (without releasing).

```protobuf
message MouseDownAction {
  MouseButton button = 1;
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| button | MouseButton | Yes | Which button to press |

**UI Display:** "Press mouse button down" / "Pressed mouse button down"

---

### 4. MouseUpAction (agent.v1.MouseUpAction)
**Location:** Line ~103625

Release a pressed mouse button.

```protobuf
message MouseUpAction {
  MouseButton button = 1;
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| button | MouseButton | Yes | Which button to release |

**UI Display:** "Release mouse button" / "Released mouse button"

---

### 5. DragAction (agent.v1.DragAction)
**Location:** Line ~103655

Drag from start to end along a path of coordinates.

```protobuf
message DragAction {
  repeated Coordinate path = 1;
  MouseButton button = 2;
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| path | Coordinate[] | Yes | Array of points defining the drag path |
| button | MouseButton | Yes | Button to hold during drag |

**UI Display:** "Drag from (X1, Y1) to (X2, Y2)" (uses first and last path points)

---

### 6. ScrollAction (agent.v1.ScrollAction)
**Location:** Line ~103691

Scroll in a direction.

```protobuf
message ScrollAction {
  optional Coordinate coordinate = 1;
  ScrollDirection direction = 2;
  int32 amount = 3;
  optional string modifier_keys = 4;
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| coordinate | Coordinate | No | Position to scroll at |
| direction | ScrollDirection | Yes | Direction to scroll |
| amount | int32 | Yes | Scroll amount (pixels or lines) |
| modifier_keys | string | No | Modifier keys |

**UI Display:** "Scroll up/down/left/right" / "Scrolled up/down/left/right"

---

### 7. TypeAction (agent.v1.TypeAction)
**Location:** Line ~103738

Type text via keyboard.

```protobuf
message TypeAction {
  string text = 1;
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| text | string | Yes | Text to type |

**UI Display:** "Type 'text...'" (truncated to 30 chars with "..." suffix)

---

### 8. KeyAction (agent.v1.KeyAction)
**Location:** Line ~103768

Press a single key or key combination.

```protobuf
message KeyAction {
  string key = 1;
  optional int32 hold_duration_ms = 2;
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| key | string | Yes | Key name (e.g., "Enter", "Ctrl+C") |
| hold_duration_ms | int32 | No | How long to hold the key |

**UI Display:** "Press {key}" / "Pressed {key}"

---

### 9. WaitAction (agent.v1.WaitAction)
**Location:** Line ~103804

Pause execution for a specified duration.

```protobuf
message WaitAction {
  int32 duration_ms = 1;
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| duration_ms | int32 | Yes | Wait time in milliseconds |

**UI Display:** "Wait {N}ms" / "Waited {N}ms"

---

### 10. ScreenshotAction (agent.v1.ScreenshotAction)
**Location:** Line ~103834

Capture a screenshot of the current screen.

```protobuf
message ScreenshotAction {
  // No fields - just triggers capture
}
```

**UI Display:** "Capture screenshot" / "Captured screenshot"

---

### 11. CursorPositionAction (agent.v1.CursorPositionAction)
**Location:** Line ~103859

Query current cursor position.

```protobuf
message CursorPositionAction {
  // No fields - just queries position
}
```

**UI Display:** "Get cursor position" / "Got cursor position"

---

## Top-Level Messages

### ComputerUseArgs (agent.v1.ComputerUseArgs)
**Location:** Line ~103389

Input arguments for the ComputerUseToolCall.

```protobuf
message ComputerUseArgs {
  string tool_call_id = 1;
  repeated ComputerUseAction actions = 2;
}
```

| Field | Type | Description |
|-------|------|-------------|
| tool_call_id | string | Unique identifier for this tool call |
| actions | ComputerUseAction[] | List of actions to execute sequentially |

### ComputerUseParams (aiserver.v1.ComputerUseParams)
**Location:** Line ~117402

Server-side params wrapper (used in ClientSideToolV2Call).

```protobuf
message ComputerUseParams {
  repeated ComputerUseAction actions = 1;
}
```

---

## Result Types

### ComputerUseResult (agent.v1.ComputerUseResult)
**Location:** Line ~103886

Wrapper for success/error results.

```protobuf
message ComputerUseResult {
  oneof result {
    ComputerUseSuccess success = 1;
    ComputerUseError error = 2;
  }
}
```

### ComputerUseSuccess (agent.v1.ComputerUseSuccess)
**Location:** Line ~103923

Result when all actions completed successfully.

```protobuf
message ComputerUseSuccess {
  int32 action_count = 1;
  int32 duration_ms = 2;
  optional string screenshot = 3;
  optional string log = 4;
  optional string screenshot_path = 5;
  optional Coordinate cursor_position = 6;
}
```

| Field | Type | Description |
|-------|------|-------------|
| action_count | int32 | Number of actions executed |
| duration_ms | int32 | Total execution time |
| screenshot | string | Base64-encoded screenshot (WebP format) |
| log | string | Execution log |
| screenshot_path | string | File path to saved screenshot |
| cursor_position | Coordinate | Final cursor position |

### ComputerUseError (agent.v1.ComputerUseError)
**Location:** Line ~103982

Result when an action failed.

```protobuf
message ComputerUseError {
  string error = 1;
  int32 action_count = 2;
  int32 duration_ms = 3;
  optional string log = 4;
  optional string screenshot = 5;
  optional string screenshot_path = 6;
}
```

| Field | Type | Description |
|-------|------|-------------|
| error | string | Error message |
| action_count | int32 | Number of actions executed before failure |
| duration_ms | int32 | Time before failure |
| log | string | Execution log |
| screenshot | string | Screenshot at time of error |
| screenshot_path | string | Path to error screenshot |

---

## ComputerUseToolCall (agent.v1.ComputerUseToolCall)
**Location:** Line ~104040

The complete tool call structure stored in agent messages.

```protobuf
message ComputerUseToolCall {
  ComputerUseArgs args = 1;
  ComputerUseResult result = 2;
}
```

---

## Streaming Support

### ComputerUseStream (aiserver.v1.ComputerUseStream)
**Location:** Line ~117472

Used for progressive streaming of computer use actions.

```protobuf
message ComputerUseStream {
  ComputerUseParams params = 1;
}
```

---

## UI Implementation

### Action Icons (Codicons)
**Location:** Line ~932142 (function `Anm`)

| Action | Codicon |
|--------|---------|
| mouseMove | `inspect` |
| click | `cursorFrame` |
| drag | `move` |
| scroll | `unfold` |
| type | `wholeWord` |
| key | `keyboard` |
| wait | `watch` |
| screenshot | `deviceCamera` |
| cursorPosition | `location` |
| mouseDown | `cursorFrame` |
| mouseUp | `cursorFrame` |

### Status Display
The UI tracks three states: `loading`, `success`, `error`

Screenshot results are displayed as base64-encoded WebP images with a cursor overlay showing the last interaction point.

---

## SubagentTypeComputerUse

**Location:** Line ~119572

The computer use capability can be associated with a subagent type:

```protobuf
message SubagentTypeComputerUse {
  // Empty message - just marks subagent as having computer use capability
}
```

This is part of the `SubagentType` oneof, allowing agents to spawn specialized computer-use subagents.

---

## Tool Registration

**Location:** Line ~464959

```javascript
// Registration pattern from agent-exec/src/computer-use.ts
F3(
  i => new N3(i, O3("computerUseArgs"), B3("computerUseResult")),
  (i, e) => {
    e.register(new M3(i, W3("computerUseArgs"), U3("computerUseResult")))
  }
)
```

The tool is registered with:
- Input handler for `computerUseArgs`
- Output handler for `computerUseResult`
- Stream handler for progressive updates

---

## Usage in Agent Flow

1. **Tool Selection:** Agent selects `vt.COMPUTER_USE` (enum value 54)
2. **Params Construction:** Actions packed into `ComputerUseParams`
3. **Execution:** Client executes actions sequentially
4. **Result:** Returns `ComputerUseSuccess` or `ComputerUseError`
5. **Screenshot:** Result typically includes a screenshot for visual verification

---

## Security Considerations

- Feature is disabled by default (`cloud_agent_computer_use: { default: false }`)
- Server-controlled flag (`client: false`)
- Actions execute on user's local machine
- Screenshots may capture sensitive information

---

## Related Analysis

- **TASK-26-tool-schemas.md:** General tool schema documentation
- **TASK-52-toolcall-schema.md:** Tool call message structures
- **TASK-23-vm-vs-shadow.md:** VM execution environments (may relate to sandboxed computer use)
