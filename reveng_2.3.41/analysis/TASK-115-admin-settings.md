# TASK-115: Admin Settings API and Team Permission Structure Analysis

**Source:** `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
**Cursor Version:** 2.3.41
**Analysis Date:** 2026-01-28

## Executive Summary

This analysis maps the admin settings API infrastructure in Cursor IDE, revealing a hierarchical permission system with team-level admin controls that can override individual user settings. The system uses Protocol Buffers (protobuf) for all API communication via the `aiserver.v1.DashboardService` gRPC service.

---

## 1. Core Admin API Endpoints

### DashboardService Methods (aiserver.v1.DashboardService)

Located at line 718909, the service defines these admin-related endpoints:

| Method | Request Type | Response Type | Purpose |
|--------|--------------|---------------|---------|
| `GetTeamAdminSettings` | `GetTeamAdminSettingsRequest` | `GetTeamAdminSettingsResponse` | Fetch admin settings for a team |
| `GetTeamAdminSettingsOrEmptyIfNotInTeam` | `GetTeamAdminSettingsRequest` | `GetTeamAdminSettingsResponse` | Safe fetch that returns empty if not in team |
| `GetBaseTeamAdminSettings` | `GetBaseTeamAdminSettingsRequest` | `GetTeamAdminSettingsResponse` | Get base/default team settings |
| `UpdateTeamAdminSettings` | `UpdateTeamAdminSettingsRequest` | `UpdateTeamAdminSettingsResponse` | Update team admin settings |
| `GetTeamPrivacyModeForced` | `GetTeamPrivacyModeForcedRequest` | `GetTeamPrivacyModeForcedResponse` | Check privacy mode enforcement |
| `SwitchTeamPrivacyMode` | `SwitchTeamPrivacyModeRequest` | `SwitchTeamPrivacyModeResponse` | Change team privacy mode |
| `UpdateRole` | `UpdateRoleRequest` | `UpdateRoleResponse` | Change team member role |
| `SetAdminOnlyUsagePricing` | `SetAdminOnlyUsagePricingRequest` | `SetAdminOnlyUsagePricingResponse` | Restrict usage pricing to admins |
| `GetDirectoryGroups` | `GetDirectoryGroupsRequest` | `GetDirectoryGroupsResponse` | SCIM directory groups |
| `UpdateDirectoryGroupSettings` | `UpdateDirectoryGroupSettingsRequest` | `UpdateDirectoryGroupSettingsResponse` | Update directory group settings |
| `GetSsoConfigurationLinks` | Request | Response | SSO configuration |
| `GetScimConfigurationLinks` | Request | Response | SCIM configuration |

---

## 2. Team Admin Settings Structure

### GetTeamAdminSettingsResponse (aiserver.v1.GetTeamAdminSettingsResponse)

**Location:** Line 276941-277106

```protobuf
message GetTeamAdminSettingsResponse {
  repeated string allowed_models = 1;           // Model allowlist
  repeated string blocked_models = 2;           // Model blocklist
  AutoRunControls auto_run_controls = 3;        // Auto-run configuration
  CursorIgnoreControls cursor_ignore_controls = 4;  // .cursorignore settings
  bool dot_cursor_protection = 5;               // .cursor folder protection
  AllowedMCPConfiguration allowed_mcp_configuration = 6;  // MCP server config
  BackgroundAgentSettings background_agent_settings = 7;  // Background agent config
  CliSettings cli_settings = 8;                 // CLI configuration
  MCPControls mcp_controls = 9;                 // MCP tool controls
  PromptDeeplinkControls prompt_deeplink_controls = 10;
  CommandDeeplinkControls command_deeplink_controls = 11;
  DeeplinkControls deeplink_controls = 12;
  GithubIntegrationSettings github_integration_settings = 13;
  SlackIntegrationSettings slack_integration_settings = 14;
  LinearIntegrationSettings linear_integration_settings = 15;
  WorkspaceTrustControls workspace_trust_controls = 16;
  GitlabIntegrationSettings gitlab_integration_settings = 17;
  optional bool browser_features = 18;
  optional bool byok_disabled = 19;             // Block BYOK (Bring Your Own Key)
  optional bool dashboard_analytics_requires_admin = 20;
  SharedConversationSettings shared_conversation_settings = 21;
  optional string allowed_extensions = 22;
  repeated string browser_origin_allowlist = 23;
  optional bool disable_conversation_insights = 24;
}
```

---

## 3. Auto-Run Controls (aiserver.v1.AutoRunControls)

**Location:** Line 276314-276386

Controls automated command execution behavior:

```protobuf
message AutoRunControls {
  bool enabled = 1;                              // Master enable
  repeated string allowed = 2;                   // Command allowlist
  repeated string blocked = 3;                   // Command blocklist
  bool disable_mcp_auto_run = 4;                // Disable MCP auto-run
  bool delete_file_protection = 5;              // Block file deletion
  bool enable_run_everything = 6;               // Allow run-everything mode
  repeated string mcp_tool_allowlist = 7;       // MCP tool allowlist
  AutoRunSandboxingControls sandboxing_controls = 8;  // Sandboxing config
  bool browser_protection = 9;                  // Browser protection
}
```

### Sandboxing Controls (aiserver.v1.AutoRunSandboxingControls)

**Location:** Line 276614-276653

```protobuf
message AutoRunSandboxingControls {
  SandboxingMode sandboxing = 1;                // ENABLED, DISABLED, UNSPECIFIED
  NetworkingMode sandbox_networking = 2;        // USER_CONTROLLED, ALWAYS_DISABLED
  GitMode sandbox_git = 3;                      // USER_CONTROLLED, ALWAYS_DISABLED
}
```

---

## 4. Permission Enums

### TeamRole (aiserver.v1.TeamRole)

**Location:** Line 269065-269080

```
TEAM_ROLE_UNSPECIFIED = 0
TEAM_ROLE_OWNER = 1
TEAM_ROLE_MEMBER = 2
TEAM_ROLE_FREE_OWNER = 3
TEAM_ROLE_REMOVED = 4
```

### PrivacyMode (aiserver.v1.PrivacyMode)

**Location:** Line 269165-269180

```
PRIVACY_MODE_UNSPECIFIED = 0
PRIVACY_MODE_NO_STORAGE = 1           // No data storage
PRIVACY_MODE_NO_TRAINING = 2          // No AI training
PRIVACY_MODE_USAGE_DATA_TRAINING_ALLOWED = 3
PRIVACY_MODE_USAGE_CODEBASE_TRAINING_ALLOWED = 4
```

### SandboxingMode (aiserver.v1.SandboxingMode)

**Location:** Line 269096-269106

```
SANDBOXING_MODE_UNSPECIFIED = 0
SANDBOXING_MODE_ENABLED = 1
SANDBOXING_MODE_DISABLED = 2
```

### NetworkingMode / GitMode

**Location:** Line 269107-269127

```
NETWORKING_MODE_UNSPECIFIED = 0
NETWORKING_MODE_USER_CONTROLLED = 1
NETWORKING_MODE_ALWAYS_DISABLED = 2

GIT_MODE_UNSPECIFIED = 0
GIT_MODE_USER_CONTROLLED = 1
GIT_MODE_ALWAYS_DISABLED = 2
```

### AllowlistConfig (aiserver.v1.AllowlistConfig)

**Location:** Line 269140-269149

```
ALLOWLIST_CONFIG_UNSPECIFIED = 0
ALLOWLIST_CONFIG_ALLOWLIST = 1        // Only allow listed items
ALLOWLIST_CONFIG_BLOCKLIST = 2        // Block listed items
```

### SharedConversationVisibility (aiserver.v1.SharedConversationVisibility)

**Location:** Line 269287-269300

```
SHARED_CONVERSATION_VISIBILITY_UNSPECIFIED = 0
SHARED_CONVERSATION_VISIBILITY_PRIVATE = 1
SHARED_CONVERSATION_VISIBILITY_TEAM = 2
SHARED_CONVERSATION_VISIBILITY_PUBLIC = 3
```

---

## 5. Background Agent & CLI Settings

### BackgroundAgentSettings (aiserver.v1.BackgroundAgentSettings)

**Location:** Line 276496-276541

```protobuf
message BackgroundAgentSettings {
  repeated string allowlist = 1;
  AllowlistConfig allowlist_config = 2;         // ALLOWLIST or BLOCKLIST mode
  bool team_followup_enabled = 3;
  AutoCreatePrMode auto_create_pr = 4;          // ALWAYS, SINGLE, NEVER
}
```

### CliSettings (aiserver.v1.CliSettings)

**Location:** Line 276542-276577

```protobuf
message CliSettings {
  repeated string allowlist = 1;
  AllowlistConfig allowlist_config = 2;
}
```

### MCPControls (aiserver.v1.MCPControls)

**Location:** Line 276578-276613

```protobuf
message MCPControls {
  bool enabled = 1;
  repeated string allowed_tools = 2;
}
```

### AllowedMCPConfiguration (aiserver.v1.AllowedMCPConfiguration)

**Location:** Line 276459-276495

```protobuf
message AllowedMCPConfiguration {
  optional bool disable_all = 1;
  repeated AllowedMcpServer allowed_mcp_servers = 2;
}
```

---

## 6. Integration Settings

### GithubIntegrationSettings / GitlabIntegrationSettings / SlackIntegrationSettings / LinearIntegrationSettings

**Location:** Lines 276749-276868

All follow the same pattern:
```protobuf
message [X]IntegrationSettings {
  bool hidden = 1;                               // Hide integration from users
}
```

### DeeplinkControls (aiserver.v1.DeeplinkControls)

**Location:** Line 276714-276748

```protobuf
message DeeplinkControls {
  bool enabled = 1;
  bool allow_public_deeplinks = 2;
}
```

---

## 7. Team Structure (aiserver.v1.Team)

**Location:** Line 272379-272528

```protobuf
message Team {
  string name = 1;
  int32 id = 2;
  TeamRole role = 3;                             // User's role in team
  int32 seats = 4;
  bool has_billing = 5;
  int32 request_quota_per_seat = 6;
  bool privacy_mode_forced = 7;                  // Team forces privacy mode
  bool allow_sso = 8;                            // SSO enabled
  bool admin_only_usage_pricing = 9;
  string subscription_status = 10;
  string bedrock_iam_role = 11;                  // AWS Bedrock integration
  bool verified = 12;
  bool is_enterprise = 13;
  bool privacy_mode_migration_opted_out = 14;
  string bedrock_external_id = 15;
  string membership_type = 16;
  optional int32 purchased_seats = 17;
  optional int64 billing_cycle_start = 18;
  optional int64 billing_cycle_end = 19;
  optional string pricing_strategy = 20;
  optional int32 total_committed_dollars = 21;
  bool data_sharing_discount_eligible = 22;
  bool dashboard_analytics_requires_admin = 23;
  bool individual_spend_limits_blocked = 24;
}
```

---

## 8. Enterprise Directory Groups (SCIM)

### DirectoryGroup (aiserver.v1.DirectoryGroup)

**Location:** Line 285590-285649

```protobuf
message DirectoryGroup {
  string name = 1;
  int32 id = 2;
  int32 member_count = 3;
  int32 hard_limit_per_user_dollars = 4;        // Spend limit
  AutoRunControls auto_run_controls = 5;         // Group-specific auto-run
  string external_id = 6;                        // SCIM external ID
  int32 per_user_monthly_limit_dollars = 7;
}
```

### UpdateDirectoryGroupSettingsRequest

**Location:** Line 285706-285751

```protobuf
message UpdateDirectoryGroupSettingsRequest {
  int32 directory_group_id = 1;
  optional int32 hard_limit_per_user_dollars = 2;
  int32 per_user_monthly_limit_dollars = 4;
  AutoRunControls auto_run_controls = 3;
}
```

---

## 9. Settings Hierarchy & Override Mechanism

### Admin Settings Service Implementation

**Location:** Line 290773-290843 (`adminSettingsService.js`)

The service maintains a cache and periodic refresh:

```javascript
class AdminSettingsService {
  static STORAGE_KEY = "adminSettings.cached";

  constructor(cursorAuthenticationService, storageService) {
    this.cached = DEFAULT_SETTINGS;
    this.loadFromStorage();

    // Refresh on login
    cursorAuthenticationService.addLoginChangedListener(() => this.refresh());

    // Periodic refresh every 5 minutes
    setInterval(() => this.refresh(), 300 * 1000);
  }

  async refresh() {
    const client = await this.cursorAuthenticationService.dashboardClient();
    const teams = await client.getTeams({});
    const team = teams.teams?.find(t => t.seats !== 0);
    if (team) {
      this.cached = await client.getTeamAdminSettings({ teamId: team.id });
      this.saveToStorage();
    }
  }

  isModelBlocked(modelName) {
    const settings = this.getCached();
    const normalize = (name) => name.toLowerCase().replace(/-/g, ".");
    const normalizedName = normalize(modelName);

    // Blocked if in blocklist
    if (settings.blockedModels?.length > 0 &&
        settings.blockedModels.some(m => normalizedName.includes(normalize(m)))) {
      return true;
    }

    // Blocked if allowlist exists and model not in it
    if (settings.allowedModels?.length > 0 &&
        !settings.allowedModels.some(m => normalizedName.includes(normalize(m)))) {
      return true;
    }

    return false;
  }
}
```

### Auto-Run Settings Fetch & Cache

**Location:** Line 305947-306040

```javascript
async function fetchTeamAdminSettings(cursorAuthService, storageService) {
  const client = await cursorAuthService.dashboardClient();
  const teamId = cursorAuthService.getTeamId();

  if (teamId) {
    try {
      const settings = await client.getTeamAdminSettings({ teamId });
      // Cache settings as JSON
      storageService.store(
        "autorun.cachedAdminSettings",
        settings.toJsonString(),
        -1,  // global scope
        1    // storage target
      );
      return settings;
    } catch (error) {
      // Fall back to cached settings on network error
      const cached = storageService.get("autorun.cachedAdminSettings", -1);
      if (cached) {
        return GetTeamAdminSettingsResponse.fromJsonString(cached);
      }
      throw error;
    }
  }
}
```

### Permission Enforcement in UI

**Location:** Line 905102-905147

```javascript
// Auto-run mode label reflects admin control
function getAutoRunModeLabel() {
  if (adminSettings.isDisabledByAdmin) {
    return "Auto-Run Mode Disabled by Team Admin";
  }
  if (adminSettings.isAdminControlled) {
    if (adminSettings.sandboxingControls?.sandboxing === "enabled" && hasSandboxing()) {
      return "Auto-Run Mode Controlled by Team Admin (Sandbox Enabled)";
    }
    return "Auto-Run Mode Controlled by Team Admin";
  }
  return "Auto-Run Mode";
}

// UI disables controls when admin-controlled
function isAutoRunEnabled() {
  if (adminSettings.isDisabledByAdmin) return false;
  if (adminSettings.isAdminControlled) {
    return adminSettings.enableRunEverything === true ||
           adminSettings.allowedCommands?.length > 0 ||
           adminSettings.mcpAllowedTools?.length > 0 ||
           adminSettings.sandboxingControls?.sandboxing === "enabled";
  }
  return true;
}
```

---

## 10. Settings Storage Structure

### applicationUserPersistentStorage.teamAdminSettings

**Location:** Line 182801-182806

```javascript
teamAdminSettings: {
  cursorIgnore: {
    hierarchicalEnabled: false,  // Apply .cursorignore hierarchically
    ignoreSymlinks: false        // Skip symlinks in discovery
  }
}
```

This local storage mirrors the relevant portions of admin settings and is updated when admin settings are fetched.

---

## 11. Key Control Flow Patterns

### Model Blocking

1. Admin sets `allowedModels` or `blockedModels` via dashboard
2. `AdminSettingsService.isModelBlocked()` checks model name against lists
3. UI filters blocked models from model selection dropdowns
4. API requests with blocked models are rejected

### Auto-Run Control

1. Admin configures `AutoRunControls` with allowed/blocked commands
2. Client fetches settings via `getTeamAdminSettings`
3. Settings cached locally with fallback on network failure
4. UI shows appropriate mode based on `isAdminControlled` and `isDisabledByAdmin`
5. Command execution checks against allowlist before running

### Privacy Mode Enforcement

1. Team admin sets `privacyModeForced` or specific `PrivacyMode`
2. Client fetches via `getTeamPrivacyModeForced`
3. `isEnforcedByTeam` flag prevents user from changing mode
4. UI disables privacy controls when enforced

---

## 12. Security Observations

1. **Caching with Fallback**: Settings are cached locally, falling back to cache on network failure. This means temporary network issues won't break admin controls.

2. **Periodic Refresh**: 5-minute refresh interval ensures settings stay reasonably current without excessive API calls.

3. **Graceful Degradation**: When settings were previously enforced but fetch fails, existing restrictions are kept (`dqr()` check).

4. **Client-Side Enforcement**: Many restrictions are enforced client-side (UI disabling, model filtering). Server-side enforcement likely exists but would need API analysis.

5. **Enterprise Features**: SCIM integration and Directory Groups suggest enterprise SSO/provisioning support with per-group policy controls.

---

## 13. Open Questions for Future Investigation

1. **Server-side Validation**: How does the server enforce admin settings for API requests?
2. **Audit Logging**: Are admin setting changes logged? Where?
3. **Group Inheritance**: How do Directory Group settings interact with Team-level settings?
4. **BYOK Flow**: How does `byok_disabled` affect the API key configuration flow?
5. **Extension Allowlisting**: Format and enforcement of `allowed_extensions` field?

---

## Related Tasks

- TASK-116 (suggested): Investigate server-side enforcement of admin settings
- TASK-117 (suggested): Map SCIM/SSO enterprise authentication flow
- TASK-118 (suggested): Analyze model allowlist/blocklist server enforcement
