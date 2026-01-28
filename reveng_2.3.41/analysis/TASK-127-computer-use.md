# TASK-127: COMPUTER_USE Tool (ID 54) - Implementation and Capabilities Analysis

**Source:** `reveng_2.3.41/beautified/workbench.desktop.main.js`
**Analysis Date:** 2026-01-28
**Related:** TASK-108-computer-use.md, TASK-26-tool-schemas.md

## Executive Summary

The COMPUTER_USE tool (ClientSideToolV2 enum value 54) enables AI agents to control the user's computer through mouse actions, keyboard input, and screen capture. This is a client-side tool that executes locally within Cursor IDE, with execution handled by the agent-exec package.

**Key Finding:** Computer use is currently **disabled by default** and is **server-controlled**, making it a carefully gated feature likely intended for cloud agent scenarios.

---

## 1. Tool Definition (Line 104365)

```javascript
// Tool enum definition
i[i.COMPUTER_USE = 54] = "COMPUTER_USE"

// Protobuf registration
{
    no: 54,
    name: "CLIENT_SIDE_TOOL_V2_COMPUTER_USE"
}
```

### Source Files
- `out-build/proto/agent/v1/computer_use_tool_pb.js` (line ~103307)
- `src/proto/agent/v1/computer_use_tool_pb.ts` (line ~241664)
- `../packages/agent-exec/src/computer-use.ts` (line ~464959)
- `aiserver.v1.ComputerUseParams` (line ~117402)
- `aiserver.v1.ComputerUseResult` (line ~117435)

---

## 2. Feature Flag and Security Controls

### Feature Gate (Line 294413)

```javascript
cloud_agent_computer_use: {
    client: false,   // Server-controlled, not client-configurable
    default: false   // Disabled by default
}
```

**Security Implications:**
- `client: false` means users cannot enable this themselves via settings
- `default: false` means it's off unless explicitly enabled server-side
- This suggests Cursor controls who gets access to computer use capabilities

### Related Feature Flags

```javascript
enable_cloud_agent_record_screen: {
    client: false,
    default: false
}
```

Screen recording is similarly gated, indicating a coordinated approach to computer control features.

---

## 3. Action Types (11 Types)

The `ComputerUseAction` message supports 11 distinct action types:

### Mouse Actions

| Action | Proto Field | Description | Parameters |
|--------|-------------|-------------|------------|
| MouseMoveAction | `mouse_move` | Move cursor | `coordinate: {x, y}` |
| ClickAction | `click` | Click at position | `coordinate`, `button`, `count`, `modifier_keys` |
| MouseDownAction | `mouse_down` | Press button down | `button` |
| MouseUpAction | `mouse_up` | Release button | `button` |
| DragAction | `drag` | Drag along path | `path: Coordinate[]`, `button` |
| ScrollAction | `scroll` | Scroll screen | `coordinate`, `direction`, `amount`, `modifier_keys` |

### Keyboard Actions

| Action | Proto Field | Description | Parameters |
|--------|-------------|-------------|------------|
| TypeAction | `type` | Type text | `text: string` |
| KeyAction | `key` | Press key combo | `key: string`, `hold_duration_ms` |

### Utility Actions

| Action | Proto Field | Description | Parameters |
|--------|-------------|-------------|------------|
| WaitAction | `wait` | Pause execution | `duration_ms` |
| ScreenshotAction | `screenshot` | Capture screen | (none) |
| CursorPositionAction | `cursor_position` | Query position | (none) |

### Enums

```javascript
// MouseButton (agent.v1.MouseButton)
enum MouseButton {
  UNSPECIFIED = 0,
  LEFT = 1,
  RIGHT = 2,
  MIDDLE = 3,
  BACK = 4,
  FORWARD = 5
}

// ScrollDirection (agent.v1.ScrollDirection)
enum ScrollDirection {
  UNSPECIFIED = 0,
  UP = 1,
  DOWN = 2,
  LEFT = 3,
  RIGHT = 4
}
```

---

## 4. Message Schemas

### ComputerUseParams (Input)

```protobuf
// aiserver.v1.ComputerUseParams (line 117402)
message ComputerUseParams {
  repeated ComputerUseAction actions = 1;
}
```

### ComputerUseArgs (Agent Exec)

```protobuf
// agent.v1.ComputerUseArgs (line 103389)
message ComputerUseArgs {
  string tool_call_id = 1;
  repeated ComputerUseAction actions = 2;
}
```

### ComputerUseResult (Output)

```protobuf
// agent.v1.ComputerUseResult (line 103886)
message ComputerUseResult {
  oneof result {
    ComputerUseSuccess success = 1;
    ComputerUseError error = 2;
  }
}
```

### ComputerUseSuccess

```protobuf
// agent.v1.ComputerUseSuccess (line 103923)
message ComputerUseSuccess {
  int32 action_count = 1;
  int32 duration_ms = 2;
  optional string screenshot = 3;      // Base64 WebP
  optional string log = 4;
  optional string screenshot_path = 5;
  optional Coordinate cursor_position = 6;
}
```

### ComputerUseError

```protobuf
// agent.v1.ComputerUseError (line 103982)
message ComputerUseError {
  string error = 1;
  int32 action_count = 2;
  int32 duration_ms = 3;
  optional string log = 4;
  optional string screenshot = 5;
  optional string screenshot_path = 6;
}
```

---

## 5. Execution Architecture

### Agent-Exec Package Registration (Line 464959)

```javascript
// ../packages/agent-exec/src/computer-use.ts
P2h = F3(
  i => new N3(i, O3("computerUseArgs"), B3("computerUseResult")),
  (i, e) => {
    e.register(new M3(i, W3("computerUseArgs"), U3("computerUseResult")))
  }
)
```

This registers handlers for:
- `computerUseArgs` - input parameters
- `computerUseResult` - output results

### Agent Exec Service (Line 557608)

```javascript
kBe = on("agentExecProviderService");
```

The `agentExecProviderService` manages tool execution through a provider pattern that:
1. Spawns execution sessions via `spawn()`
2. Creates remote accessors for tool calls
3. Handles streaming results
4. Supports cancellation by tool call ID

### Tool Call Flow (Lines 467178-467184)

```javascript
case "computerUseToolCall": {
    l = vt.COMPUTER_USE;
    const w = i.tool.value.args;
    w && (a = new J7e({  // J7e = ComputerUseParams
        actions: w.actions
    }));
    break
}
```

---

## 6. UI Implementation (Lines 932060-932700)

### Component: Mnm (ComputerUseToolCallBlock)

The UI component renders:
1. Action descriptions (human-readable)
2. Status indicators (loading/success/error)
3. Screenshot results with cursor overlay
4. Expandable action lists

### Action Display Logic (Line 932082)

```javascript
function $gu(i, e, t) {
    const n = i.action.case;
    switch (n) {
        case "mouseMove": {
            const s = i.action.value.coordinate,
                r = e ? "Moved" : t ? "Moving" : "Move";
            return s ? `${r} mouse to (${s.x}, ${s.y})` : `${r} mouse`
        }
        case "click": {
            // Double/Triple click, Right/Middle click handling
            const d = e ? `${a}${l}Clicked` : t ? `${a}${l}Clicking` : `${a}${l}Click`;
            return s ? `${d} at (${s.x}, ${s.y})` : d
        }
        // ... etc
    }
}
```

### Action Icons (Line 932142)

```javascript
function Anm(i) {
    switch (i.action.case) {
        case "mouseMove": return de.inspect;
        case "click": return de.cursorFrame;
        case "drag": return de.move;
        case "scroll": return de.unfold;
        case "type": return de.wholeWord;
        case "key": return de.keyboard;
        case "wait": return de.watch;
        case "screenshot": return de.deviceCamera;
        case "cursorPosition": return de.location;
        // ...
    }
}
```

### Screenshot Rendering

Screenshots are rendered as base64-encoded WebP images with a cursor overlay showing the last interaction point:

```javascript
// Line 932276
const ne = ve(() => {
    const Ne = ie();
    return Ne?.screenshot ?
        Ne.screenshot.startsWith("data:") ?
            Ne.screenshot :
            `data:image/webp;base64,${Ne.screenshot}`
        : null
});
```

---

## 7. Browser Automation Integration

### BrowserAutomationService (Line 446614)

Computer use appears to integrate with browser automation:

```javascript
// out-build/vs/workbench/contrib/composer/browser/browserAutomationService.js
class BrowserAutomationService extends Ve {
    static STORAGE_KEY_LAST_URL = "browserAutomation.lastUrl"
    static STORAGE_KEY_ZOOM_LEVEL = "browserAutomation.zoomLevel"
    static STORAGE_KEY_BOOKMARKS = "browserAutomation.bookmarks"
    // ...
}
```

### Playwright MCP Integration

Cursor includes Playwright MCP integration for browser control:

```javascript
// Line 196213
[Qi.playwright_mcp]: "Browser"

// Line 293841
playwright_mcp_provider: { ... }

// Line 294025
playwright_autorun: { ... }
```

This suggests computer use may leverage Playwright for browser-specific automation.

---

## 8. Screen Recording Capability

### RecordScreen Tool (Line 131599)

A related `RecordScreen` tool exists with modes:

```javascript
enum RecordingMode {
  UNSPECIFIED = 0,
  START_RECORDING = 1,
  SAVE_RECORDING = 2,
  DISCARD_RECORDING = 3
}
```

### RecordScreenResult

```protobuf
message RecordScreenResult {
  oneof result {
    RecordScreenStartSuccess start_success = 1;
    RecordScreenSaveSuccess save_success = 2;
    RecordScreenDiscardSuccess discard_success = 3;
    RecordScreenFailure failure = 4;
  }
}
```

---

## 9. SubagentTypeComputerUse (Line 119572)

Computer use capability can be associated with specialized subagents:

```protobuf
message SubagentTypeComputerUse {
  // Empty message - marks subagent as having computer use capability
}
```

This is part of the `SubagentType` oneof, allowing agents to spawn specialized computer-use subagents in the cloud agent architecture.

---

## 10. Security Analysis

### Access Control Mechanisms

1. **Server-side gating:** `client: false` prevents user self-enablement
2. **Default disabled:** Requires explicit server-side activation
3. **No found approval UI:** Unlike terminal commands, no explicit user approval flow was found for computer use actions
4. **Screenshot capture:** Results include screenshots which could capture sensitive information

### Potential Risks

1. **Full desktop access:** Actions execute on the user's local machine with full access
2. **Credential exposure:** Type actions could enter passwords visible on screen
3. **Screenshot sensitivity:** Captures may include sensitive data
4. **No sandbox isolation:** Unlike shadow workspace edits, computer use appears to run directly

### Missing Controls (Not Found)

- User approval flow for computer use actions
- Sandboxing mechanism for computer use
- Action filtering or restriction lists
- Rate limiting on actions

---

## 11. Relationship to Other Tools

| Tool | Enum | Relationship |
|------|------|--------------|
| COMPUTER_USE | 54 | Primary computer control |
| GENERATE_IMAGE | 53 | Adjacent tool (image generation) |
| WRITE_SHELL_STDIN | 55 | Adjacent tool (shell input) |
| RUN_TERMINAL_COMMAND_V2 | 15 | Terminal execution |
| MCP | 19 | Playwright MCP for browser |

---

## 12. Implementation Status

Based on the analysis:

1. **Protobuf schemas:** Complete and well-defined
2. **UI components:** Fully implemented
3. **Agent-exec handlers:** Registered
4. **Feature flag:** Exists but disabled
5. **Actual executor:** Not found in client code - likely server-side or extension

**Hypothesis:** The actual mouse/keyboard automation is likely handled by:
- A native module (not visible in JS bundle)
- A server-side execution environment (cloud agent)
- Playwright MCP for browser-specific actions

---

## 13. Key Line References

| Component | Line Number |
|-----------|-------------|
| Tool enum definition | 104365 |
| Proto registration | 104497 |
| Feature flag | 294413 |
| ComputerUseParams class | 117394 |
| ComputerUseResult class | 117425 |
| Agent-exec registration | 464959 |
| Tool call handling | 467178 |
| UI component (Mnm) | 932172 |
| Action icons | 932142 |
| Action descriptions | 932082 |

---

## 14. Open Questions

1. **Native implementation:** Where is the actual mouse/keyboard automation code?
2. **Permission model:** How are computer use actions approved?
3. **Cloud vs local:** Is this primarily for cloud agent or local execution?
4. **Playwright integration:** How does browser automation connect?
5. **Security boundary:** What prevents malicious computer use?

---

## 15. Recommendations for Further Investigation

1. Search native modules for mouse/keyboard automation
2. Investigate extension host for computer use handlers
3. Analyze cloud agent server-side handling
4. Compare with Claude's computer use implementation
5. Examine Playwright MCP provider code

---

## Related Analysis

- **TASK-108-computer-use.md:** Action types deep dive
- **TASK-26-tool-schemas.md:** General tool schema documentation
- **TASK-23-vm-vs-shadow.md:** VM execution environments
- **TASK-5-shadow-workspace.md:** Sandboxed editing comparison
