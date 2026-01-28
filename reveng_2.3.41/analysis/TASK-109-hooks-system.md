# TASK-109: Cursor Hooks System for Shell Execution

## Overview

Cursor IDE 2.3.41 implements a comprehensive hooks system that allows execution of custom scripts at various points during AI agent workflows. This system enables security policies, observability, and workflow customization by intercepting and potentially modifying or blocking agent actions.

## Hook Types

The hooks system defines 12 distinct hook steps:

### Command Execution Hooks
1. **beforeShellExecution** - Triggered before running terminal commands
2. **afterShellExecution** - Triggered after terminal command completion
3. **beforeMCPExecution** - Triggered before MCP tool invocation
4. **afterMCPExecution** - Triggered after MCP tool completion

### File Operation Hooks
5. **beforeReadFile** - Triggered before reading file contents
6. **afterFileEdit** - Triggered after file modifications
7. **beforeTabFileRead** - Triggered before tab autocomplete reads files
8. **afterTabFileEdit** - Triggered after tab autocomplete edits

### Agent Workflow Hooks
9. **beforeSubmitPrompt** - Triggered before submitting user prompts
10. **afterAgentResponse** - Triggered after agent completes response
11. **afterAgentThought** - Triggered after agent thinking/reasoning completes
12. **stop** - Triggered when agent workflow stops (completed, aborted, or error)

## Hook Configuration Sources

Hooks can be configured from four hierarchical sources (executed in order):

### 1. Enterprise Hooks
- **Location**: System-wide configuration directory
  - macOS: `/Library/Application Support/Cursor/hooks.json`
  - Windows: `C:\ProgramData\Cursor\hooks.json`
  - Linux: `/etc/cursor/hooks.json`
- **Purpose**: Organization-wide security policies
- **Trust**: Always trusted, highest priority

### 2. Team Hooks
- **Source**: Fetched from Cursor backend via `getTeamHooks` API
- **Location**: Scripts stored in `~/.cursor/managed/team_{teamId}/hooks/`
- **Refresh**: Every 30 minutes (1800 seconds)
- **OS-Specific**: Filtered by operating system (Windows, Macintosh, Linux)
- **First-time notification**: Users see prompt with Continue/View Hooks/Logout options

### 3. Project Hooks (Experimental)
- **Location**: `.cursor/hooks.json` in workspace root
- **Feature Gate**: Requires `hooks_ide_project_config` experiment flag
- **Trust**: Only executed if workspace is trusted
- **Paths**: Relative to workspace root

### 4. User Hooks
- **Location**: `~/.cursor/hooks.json`
- **Paths**: Relative to hooks.json file location

## Configuration Format

```json
{
  "version": 1,
  "hooks": {
    "beforeShellExecution": [
      { "command": "./scripts/validate-command.sh" }
    ],
    "afterShellExecution": [
      { "command": "/usr/local/bin/audit-log.sh" }
    ]
  }
}
```

### Validation Rules
- `version` must be a positive integer
- `hooks` must be an object
- Each hook step array contains objects with `command` property (string)
- Invalid configurations generate errors displayed in settings UI

## Hook Execution Flow

### Input Payload
Hooks receive JSON input via stdin (base64-encoded, piped through script):

```bash
# Unix execution
printf %s '${base64_payload}' | base64 -d | ${hook_command}

# Windows PowerShell execution
$b64='${base64_payload}'; [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($b64)) | & { $input | ${hook_command} }
```

### Common Input Fields
All hooks receive:
- `hook_event_name` - The step name (e.g., "beforeShellExecution")
- `cursor_version` - Current Cursor IDE version
- `workspace_roots` - Array of workspace folder paths
- `user_email` - Authenticated user's email (if logged in)
- `conversation_id` - Current composer/conversation ID
- `generation_id` - Current generation UUID
- `model` - Model name being used

### Step-Specific Input Fields

**beforeShellExecution / afterShellExecution:**
- `command` - Shell command being executed
- `cwd` - Working directory
- `sandbox` - Whether sandboxing is enabled
- `output` - Command output (afterShellExecution only)
- `duration` - Execution time in ms (afterShellExecution only)

**beforeMCPExecution / afterMCPExecution:**
- `tool_name` - MCP tool being called
- `tool_input` - JSON string of tool parameters
- `url` - For HTTP tools, the URL being accessed
- `result_json` - Tool result (afterMCPExecution only)
- `duration` - Execution time in seconds (afterMCPExecution only)

**beforeReadFile:**
- `content` - File content
- `file_path` - Absolute file path
- `attachments` - Array of rule attachments

**afterFileEdit:**
- `file_path` - Modified file path
- `edits` - Array of `{old_string, new_string}` objects

**beforeSubmitPrompt:**
- `prompt_text` - User's prompt text
- `attachments` - Attached rules and context

**afterAgentThought:**
- `text` - Thinking/reasoning text
- `duration_ms` - Thinking duration

**stop:**
- `status` - Stop reason: "completed", "aborted", or "error"
- `loop_count` - Number of stop hook iterations

## Response Handling

### Response Validators

Each hook type has a specific response validator:

**beforeCommandExecutionHookResponse** (shell/MCP execution):
```javascript
{
  permission: "allow" | "deny" | "ask",  // optional
  user_message: string,  // optional - shown to user
  agent_message: string  // optional - shown to AI model
}
```

**beforeReadFileResponse / beforeTabFileReadResponse:**
```javascript
{
  permission: "allow" | "deny"  // optional
}
```

**beforePromptSubmitResponse:**
```javascript
{
  continue: boolean,     // optional - false blocks submission
  user_message: string   // optional - explanation message
}
```

**stopResponse:**
```javascript
{
  followup_message: string  // optional - triggers auto-follow-up
}
```

**Other responses** (after* hooks): Any valid JSON object

### Permission Enforcement

**beforeShellExecution blocking:**
```javascript
if (permission === "deny") {
    throw new Error({
        clientVisibleErrorMessage: `Command execution was blocked by a hook${user_message}`,
        modelVisibleErrorMessage: `The terminal command was rejected by a hook...`
    });
}
```

**beforeReadFile blocking:**
```javascript
if (response?.permission === "deny") {
    throw new FileReadBlockedByHookError(filePath);
}
```

The `FileReadBlockedByHookError` class explicitly states:
> "File reading was blocked by a security hook: {path}. Do not attempt to work around this restriction using alternative methods or commands."

## Stop Hook Auto-Loop

The stop hook has special auto-follow-up behavior:

1. When agent stops (completed/aborted), `triggerStopHook` is called
2. If hook returns `followup_message`, a new chat submission is triggered
3. `stopHookLoopCount` tracks iterations
4. **Loop limit**: Maximum 5 iterations to prevent infinite loops
5. New submissions use `isAutoFollowupFromStopHook: true` flag

```javascript
// Loop protection
if (loop_count >= 5) {
    logger.logInfo(`Stop hook auto-loop limit reached`);
    return {};  // Skip further hooks
}
```

## Service Architecture

### CursorHooksService (hko class)

**Dependencies:**
- `fileService` - File system access
- `workspaceContextService` - Workspace folder information
- `pathService` - Path resolution
- `shellExecService` - Script execution
- `cursorAuthenticationService` - User/team authentication
- `workspaceTrustManagementService` - Workspace trust checks
- `experimentService` - Feature gates

**Key Methods:**
- `initialize()` - Load all hook configurations
- `reloadHooks()` - Refresh configurations from all sources
- `refreshTeamHooks()` - Fetch team hooks from backend
- `executeHookForStep(step, payload)` - Execute all hooks for a step
- `hasHookForStep(step)` - Check if any hooks configured
- `getAllConfiguredHooks()` - Return all hooks with sources
- `getHookExecutionLog()` - Return last 100 executions

### Execution Logging

Each hook execution is logged with:
- Unique ID (timestamp + random string)
- Timestamp
- Step name
- Script command
- Request payload
- Response data
- Duration in milliseconds
- Exit code
- Stderr output
- Source (enterprise/team/project/user)

Log is capped at 100 entries (oldest removed first).

## Team Hooks Backend Integration

### API Types

```protobuf
message TeamHook {
  int64 id = 1;
  string hook_step = 2;
  string script_name = 3;
  repeated string operating_systems = 4;
  bool is_active = 5;
  string script_content = 6;
}

message GetTeamHooksRequest {
  bool active_only = 1;
}

message GetTeamHooksResponse {
  repeated TeamHook hooks = 1;
}
```

### Team Hook Lifecycle
1. User logs in to team account
2. `refreshTeamHooks()` called on auth change
3. Hooks fetched from dashboard API
4. Scripts written to `~/.cursor/managed/team_{id}/hooks/`
5. Scripts made executable via `chmod +x` (Unix)
6. Old/removed hooks cleaned up from disk
7. Refresh scheduled every 30 minutes

### First-Time Notification
When team hooks are first detected:
```javascript
notificationService.prompt(Info,
    "This team uses admin-enabled hooks...", [
        { label: "Continue", run: () => {} },
        { label: "View Hooks", run: () => openPopup("hooks") },
        { label: "Logout", run: () => logout() }
    ], { sticky: true }
);
```

## Error Handling

### ERROR_HOOKS_BLOCKED

Used in protobuf error codes when hooks block an action:
```javascript
case fu.HOOKS_BLOCKED:
case "ERROR_HOOKS_BLOCKED":
    return "Submission blocked by hook";
```

### JSON Parse Failures
If hook output cannot be parsed as JSON:
- Error logged to stderr in execution log
- Execution continues to next hook
- No valid response returned

### Script Failures
- Exit codes captured and logged
- stderr captured and logged
- Execution continues to next hook

## Security Considerations

### Workspace Trust
- Project hooks only execute in trusted workspaces
- `workspaceTrustManagementService.isWorkspaceTrusted()` checked

### Enterprise Control
- Enterprise hooks have highest priority
- Cannot be overridden by user/project hooks
- Stored in system-protected directories

### Team Hook Security
- Downloaded from authenticated backend
- User can choose to logout instead of accepting
- Scripts stored in managed directory (not user-editable location)

### Blocking Enforcement
When a hook blocks an action, the error message explicitly warns:
> "Do not attempt to work around this restriction using alternative methods or commands."

This is included in the `modelVisibleErrorMessage` to inform the AI model that it should not try alternative approaches.

## Integration with Rules for AI

The hooks system integrates with Cursor Rules:

1. `beforeSubmitPrompt` hook receives `attachments` with applied rules
2. Rules are retrieved via `mBh()` function
3. Rule types filtered based on capability configuration
4. Hooks can inspect/modify based on active rules

## Developer Command

```
cursor.hooks.initializeUserHooks
```

Creates a sample hooks configuration:
- Creates `~/.cursor/hooks/` directory
- Creates `beforePromptSubmit.sh` sample script
- Creates `hooks.json` with sample configuration
- Opens hooks settings panel

Sample script logs to `/tmp/agent.log` and returns `{}`.

## Experiment Flags

- `hooks_ide_project_config` - Enables project-level hooks.json in workspace

## Key Source Locations

| Component | Approximate Line |
|-----------|-----------------|
| Hook types enum (Eb) | 466719 |
| Response validators | 466598-466754 |
| CursorHooksService | 964243-964792 |
| beforeShellExecution integration | 479337 |
| afterShellExecution integration | 479947 |
| Stop hook trigger | 488726-488753 |
| Team hooks API | 288576-288895 |
| Initialize command | 964795-964893 |

## Limitations and Gotchas

1. **Sequential execution**: Hooks execute one at a time within each source
2. **First valid response wins**: Once a hook returns valid JSON, remaining hooks skipped
3. **No async parallel execution**: All hooks are awaited sequentially
4. **30-minute team refresh**: Team hook changes may take up to 30 minutes to propagate
5. **Stop loop limit**: Maximum 5 automatic follow-ups from stop hooks
6. **100 entry log limit**: Execution history capped at 100 entries
7. **Project hooks experimental**: Requires feature flag, may change
