# TASK-58: MCP Tool Allowlist Persistence and Matching Logic

## Overview

This analysis documents how Cursor stores and matches MCP tool allowlist entries for auto-run permissions. The MCP allowlist system allows users to pre-approve specific MCP tools to run without manual confirmation.

## Allowlist Entry Format

### Format: `serverId:toolName`

Allowlist entries use a colon-separated format:
- `server:tool` - Allow specific tool from specific server
- `server:*` - Allow all tools from a specific server
- `*:tool` - Allow a specific tool from any server (rarely used)
- `*:*` - Allow all tools from all servers

**Reserved Characters:**
- `:` (colon) - Separator between server and tool
- `*` (asterisk) - Wildcard for matching all

Defined at line 476246:
```javascript
UJt = ":", bY = "*", g4c = [UJt, bY]
```

### Validation Rules (function `ihe` at line 476110)
- Name cannot be empty
- Name cannot exceed 256 characters
- Name cannot be only whitespace
- Name cannot contain reserved characters (`:` or `*`) unless it IS the wildcard

## Storage Mechanism

### Location
MCP allowlist is stored in the **Reactive Storage Service** under:
```
applicationUserPersistentStorage.composerState.mcpAllowedTools
```

This is a **user-level persistent storage** that persists across sessions.

### Default Value
From line 182269, the default value is an empty array:
```javascript
// Part of composerState defaults
mcpAllowedTools: []  // Not explicitly shown but derived from eic() function
```

### Storage Operations

**Reading allowlist:**
```javascript
this.reactiveStorageService.applicationUserPersistentStorage.composerState.mcpAllowedTools ?? []
```

**Writing to allowlist:**
```javascript
this.reactiveStorageService.setApplicationUserPersistentStorage("composerState", "mcpAllowedTools", newArray)
```

**Adding an entry (function `Yro` at line 476234):**
```javascript
function Yro(toolName, serverId, existingAllowlist) {
    // Validate names don't contain reserved characters
    if (!valid) return existingAllowlist;

    // Create entry string "serverId:toolName"
    const newEntry = d4c(serverId, toolName);

    // Don't add if exact entry already exists
    if (existingAllowlist.includes(newEntry)) return existingAllowlist;

    // Don't add if wildcard already covers this (server:*)
    const wildcardEntry = d4c(serverId, "*");
    if (existingAllowlist.includes(wildcardEntry)) return existingAllowlist;

    return [...existingAllowlist, newEntry];
}
```

## Matching Logic

### Core Matching Function: `f4c` (line 476187)

```javascript
function f4c(serverId, toolName, allowlistEntry) {
    const parsed = vOh(allowlistEntry);  // Parse "server:tool" string

    if (!parsed) {
        console.warn(`Invalid MCP allowlist entry: ${allowlistEntry}`);
        return false;
    }

    // Case 1: Entry server is wildcard (*)
    if (parsed.serverId === "*") {
        // *:* matches everything
        if (parsed.toolName === "*") return true;
        // *:tool matches if tool name matches
        return parsed.toolName === toolName;
    }

    // Case 2: Entry server doesn't match
    if (parsed.serverId !== serverId) return false;

    // Case 3: Server matches, check tool
    // server:* matches all tools for this server
    if (parsed.toolName === "*") return true;
    // Exact match required
    return parsed.toolName === toolName;
}
```

### Matching Priority Order
1. `*:*` - Global wildcard (matches everything)
2. `*:toolName` - Tool-specific wildcard (any server)
3. `serverId:*` - Server wildcard (all tools from server)
4. `serverId:toolName` - Exact match

### Permission Decision Function: `m4c` (line 476192)

This function determines if a tool call needs user approval:

```javascript
function m4c(toolName, serverId, settings, composerModes) {
    // Validate names
    if (!validNames) return { needApproval: true };

    // Check if it's a Playwright (browser) tool - special handling
    const isPlaywright = dxe.includes(serverId);
    const protectionEnabled = isPlaywright ? settings.playwrightProtection : settings.mcpToolsProtection;

    // Admin disabled all MCP
    if (settings.isDisabledByAdmin || protectionEnabled) {
        return { needApproval: true };
    }

    // Playwright tools bypass allowlist when protection is off
    if (isPlaywright) {
        return { needApproval: false };
    }

    // Check auto-run modes
    const useAllowlist = composerModes.shouldAutoRun_eitherUseAllowlistOrRunEverythingMode();
    const runEverything = composerModes.shouldAutoRun_runEverythingMode();

    // Run Everything mode - no approval needed (unless admin controlled)
    if (runEverything && !settings.isAdminControlled) {
        return { needApproval: false };
    }

    // Not in auto-run mode - always need approval
    if (!useAllowlist && !runEverything) {
        return { needApproval: true };
    }

    // Check allowlist - if any entry matches, no approval needed
    if (settings.mcpAllowedTools.some(entry => f4c(serverId, toolName, entry))) {
        return { needApproval: false };
    }

    // Admin controlled - check protection setting
    if (settings.isAdminControlled) {
        // ... admin logic
    }

    // Not in allowlist - need approval, but offer to add
    return {
        needApproval: true,
        candidatesForAllowlist: [{ tool: toolName, server: serverId }]
    };
}
```

## Feature Gate: `mcp_allowlists`

The allowlist feature is controlled by a feature gate:
```javascript
this.experimentService.checkFeatureGate("mcp_allowlists")
```

When enabled (lines 477079-477088):
- Uses the new `m4c` function for granular allowlist matching
- Provides `candidatesForAllowlist` for UI to offer adding to allowlist

When disabled:
- Uses simpler boolean check: `yoloMcpToolsDisabled` setting
- No allowlist matching, just global MCP protection toggle

## Admin Controls (Team Settings)

Admin settings are fetched from backend via `getTeamAdminSettings` API call.

### Protobuf Schema (line 276314-276373)
```protobuf
message AutoRunControls {
    bool enabled = 1;
    repeated string allowed = 2;           // Shell command allowlist
    repeated string blocked = 3;           // Shell command blocklist
    bool disable_mcp_auto_run = 4;         // Global MCP protection
    bool delete_file_protection = 5;
    bool enable_run_everything = 6;
    repeated string mcp_tool_allowlist = 7; // Admin MCP allowlist
    SandboxingControls sandboxing_controls = 8;
    bool browser_protection = 9;
}
```

### Admin Override Logic (line 305992-306020)

When admin controls are enabled:
- `isAdminControlled: true`
- User's local allowlist is IGNORED
- Only admin's `mcpToolAllowlist` is used
- `isDisabledByAdmin` set if no allowlist/commands and no run-everything

## UI Integration Points

### Settings Page (line 904944+)
- Validates and stores allowlist entries
- Shows warning when admin-controlled
- Format validation: must have exactly one `:` separator

### Tool Call Review (line 929420+)
- Shows "Add to allowlist" option when tool not in allowlist
- Offers to run and add to allowlist in one action
- Displays current allowlist status

## Auto-Run Modes

Three modes determine tool approval behavior:

1. **ASK_EVERY_TIME** (`ask_every_time`)
   - Every tool call needs manual approval
   - Allowlist not consulted

2. **YOLO / Use Allowlist** (`yolo`)
   - Consult allowlist for auto-approval
   - Tools not in allowlist need approval

3. **FULL_YOLO / Run Everything** (`full_yolo`)
   - Auto-run all tools without approval
   - Allowlist ignored (unless admin controlled)

Determined by:
```javascript
shouldAutoRun_eitherUseAllowlistOrRunEverythingMode() {
    return fN().isDisabledByAdmin ? false : this.composerModesService.getComposerAutoRun() ?? false;
}

shouldAutoRun_runEverythingMode() {
    return fN().isDisabledByAdmin ? false :
        this.shouldAutoRun_eitherUseAllowlistOrRunEverythingMode() &&
        (this.composerModesService.getComposerFullAutoRun() ?? false);
}
```

## Special Cases

### Playwright/Browser Tools
Server IDs: `cursor-browser-extension`, `cursor-ide-browser`

These have separate protection:
- Controlled by `playwrightProtection` setting
- Not affected by MCP allowlist when protection is off
- When protection is on, requires manual approval always

### Tool Name Extraction (function `h4c` at line 476162)
MCP tool names internally use format: `mcp_serverid_toolname`

```javascript
function h4c(toolName, fallbackServerId) {
    if (toolName.startsWith("mcp_")) {
        const rest = toolName.substring(4);  // Remove "mcp_"
        const underscoreIndex = rest.indexOf("_");
        if (underscoreIndex !== -1) {
            return {
                serverId: rest.substring(0, underscoreIndex),
                actualToolName: rest.substring(underscoreIndex + 1)
            };
        }
    }
    return { serverId: fallbackServerId, actualToolName: toolName };
}
```

## Key Functions Reference

| Function | Line | Purpose |
|----------|------|---------|
| `ihe` | 476110 | Validate server/tool name |
| `d4c` | 476133 | Create allowlist entry string |
| `vOh` | 476145 | Parse allowlist entry string |
| `h4c` | 476162 | Extract server/tool from internal name |
| `f4c` | 476187 | Match tool against allowlist entry |
| `m4c` | 476192 | Determine if approval needed |
| `Yro` | 476234 | Add tool to allowlist |
| `eic` | 305930 | Load user settings (non-admin) |
| `ASh` | 305972 | Fetch and apply admin settings |
| `fN` | 306085 | Get current autorun settings |

## Related Settings

| Setting Path | Type | Default | Description |
|--------------|------|---------|-------------|
| `composerState.mcpAllowedTools` | string[] | [] | User's MCP tool allowlist |
| `composerState.yoloMcpToolsDisabled` | boolean | false | Legacy global MCP protection |
| `composerState.playwrightProtection` | boolean | true | Browser tool protection |
| `composerState.useYoloMode` | boolean | false | Auto-run enabled |
| `composerState.yoloEnableRunEverything` | boolean | false | Run everything mode |

## Follow-up Investigations

1. **TASK-59**: Investigate reactive storage service persistence mechanism (IndexedDB? localStorage?)
2. **TASK-60**: Map admin settings API and team permission structure
3. **TASK-61**: Analyze the experiment service and feature gates system
