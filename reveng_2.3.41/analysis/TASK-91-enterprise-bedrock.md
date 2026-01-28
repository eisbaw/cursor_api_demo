# TASK-91: Enterprise Admin Bedrock Access Controls

**Task**: Investigate enterprise admin Bedrock access controls in Cursor IDE 2.3.41
**Source File**: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`

## Executive Summary

Cursor IDE provides enterprise-level AWS Bedrock integration with team-level IAM role configuration. Enterprise admins can configure Bedrock access centrally for their teams without requiring individual users to manage AWS credentials. However, there is **no evidence** of Bedrock-specific model restrictions, per-user rate limiting, or audit logging in the client-side code.

---

## Key Findings

### 1. Enterprise IAM Role-Based Bedrock Access

Enterprise teams can configure IAM roles to access AWS Bedrock without requiring individual Access Keys.

**Evidence (Line 910669)**:
```javascript
return ["Configure AWS Bedrock to use Anthropic Claude models through your AWS account.", oYf(),
        "Cursor Enterprise teams can configure IAM roles to access Bedrock without any Access Keys."]
```

#### Team Object Fields (Lines 272381-272464)

The `aiserver.v1.Team` protobuf message contains Bedrock-related fields:

| Field | Type | Description |
|-------|------|-------------|
| `bedrock_iam_role` | string (field #11) | IAM role ARN for Bedrock access |
| `bedrock_external_id` | string (field #15) | External ID for cross-account IAM role assumption |
| `is_enterprise` | bool (field #13) | Enterprise team flag |

```javascript
this.bedrockIamRole = ""
this.bedrockExternalId = ""
this.isEnterprise = !1
```

### 2. IAM Role Validation API

The system validates Bedrock IAM roles before accepting them.

**gRPC Methods** (Lines 719601-719605, 720153-720157):

| Method | Request Type | Response Type |
|--------|--------------|---------------|
| `ValidateBedrockIamRole` | `aiserver.v1.ValidateBedrockIamRoleRequest` | `aiserver.v1.ValidateBedrockIamRoleResponse` |
| `DeleteBedrockIamRole` | `aiserver.v1.DeleteBedrockIamRoleRequest` | `aiserver.v1.DeleteBedrockIamRoleResponse` |

**ValidateBedrockIamRoleRequest Fields** (Lines 278987-279016):
```javascript
{
  team_id: int32,       // Field #1
  bedrock_iam_role: string,  // Field #2 - IAM role ARN
  region: string,       // Field #3 - AWS region
  model_id: string      // Field #4 - Model to test access with
}
```

**ValidateBedrockIamRoleResponse Fields** (Lines 279030-279052):
```javascript
{
  success: bool,        // Field #1
  error_message: string // Field #2
}
```

### 3. Bedrock State Management

When a team has a configured IAM role, the client automatically sets up Bedrock access.

**Membership Refresh Logic** (Lines 1098122-1098128):
```javascript
te.some(Re => Re.bedrockIamRole !== null && Re.bedrockIamRole !== "") ?
  (this._reactiveStorageService.setApplicationUserPersistentStorage("hasBedrockIamRole", !0),
   this._reactiveStorageService.setApplicationUserPersistentStorage("bedrockState", {
    useBedrock: !1,
    region: "us-east-2",
    ...this._reactiveStorageService.applicationUserPersistentStorage.bedrockState,
    accessKey: "iam",
    secretKey: "iam"
  })) : this._reactiveStorageService.setApplicationUserPersistentStorage("hasBedrockIamRole", !1)
```

Key points:
- When team has `bedrockIamRole` set, `hasBedrockIamRole` flag is stored
- Default region is `us-east-2`
- Access credentials are set to `"iam"` placeholder strings (actual IAM role assumption happens server-side)

### 4. Supported Bedrock Models

**Hardcoded Model List** (Lines 290759-290762):
```javascript
JQl = [
  "us.anthropic.claude-sonnet-4-20250514-v1:0",
  "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "us.anthropic.claude-3-5-haiku-20241022-v1:0",
  "us.anthropic.claude-haiku-4-5-20251001-v1:0",
  "us.anthropic.claude-opus-4-20250514-v1:0",
  "us.anthropic.claude-opus-4-1-20250805-v1:0",
  "us.anthropic.claude-opus-4-5-20251101-v1:0"
]
```

**Regional Model ID Transformation** (Line 894675):
```javascript
return !t || t.startsWith("us-") ? e :
  t.startsWith("ap-") ? e.replace("us.", "apac.") :
  t.startsWith("eu-") ? e.replace("us.", "eu.") :
  t.startsWith("ca-") ? e.replace("us.", "ca.") : e
```

Regions are mapped to model prefixes:
- `us-*` regions: `us.anthropic.*`
- `ap-*` regions: `apac.anthropic.*`
- `eu-*` regions: `eu.anthropic.*`
- `ca-*` regions: `ca.anthropic.*`

### 5. Bedrock Credentials Testing

**TestBedrockCredentials Method** (Lines 895192-895197):
```javascript
async testBedrockCredentials(e, t, n, s) {
    const o = await (await this.aiClient()).testBedrockCredentials({
        accessKey: e,
        secretKey: t,
        region: n,
        modelName: s
    });
```

This allows users to verify their Bedrock credentials before enabling the integration.

### 6. BedrockCredentials Protobuf Schema

**agent.v1.BedrockCredentials** (Lines 141286-141318):
```javascript
{
  access_key: string,    // Field #1
  secret_key: string,    // Field #2
  region: string,        // Field #3
  session_token: string  // Field #4 (optional)
}
```

Note: Session token support suggests temporary credential support (likely from IAM role assumption).

---

## Admin Settings and Model Controls

### Team Admin Settings Service

**AdminSettingsService** (Lines 290773-290843):
```javascript
Mps = {
  allowedModels: [],
  blockedModels: [],
  dotCursorProtection: !1,
  browserFeatures: !1,
  browserOriginAllowlist: [],
  allowedMcpConfiguration: void 0,
  byokDisabled: !1,
  sharedConversationSettings: {
    enabled: !1,
    allowedVisibilities: [],
    allowPublicIndexing: !1
  }
}
```

**Key Settings**:

| Setting | Type | Description |
|---------|------|-------------|
| `allowedModels` | string[] | Whitelist of allowed model names |
| `blockedModels` | string[] | Blacklist of blocked model names |
| `byokDisabled` | bool | Disables Bring-Your-Own-Key for team members |
| `dotCursorProtection` | bool | Protects .cursor files from modification |

### Model Blocking Logic (Line 290841):

```javascript
isModelBlocked(e) {
    const t = this.getCached(),
        n = r => r.toLowerCase().replace(/-/g, "."),
        s = n(e);
    return !!(t.blockedModels && t.blockedModels.length > 0 &&
              t.blockedModels.some(r => s.includes(n(r))) ||
              t.allowedModels && t.allowedModels.length > 0 &&
              !t.allowedModels.some(r => s.includes(n(r))))
}
```

**Important**: The `allowedModels`/`blockedModels` apply to ALL models, not just Bedrock-specific ones. There is no separate Bedrock model restriction mechanism.

### BYOK Disabled Enforcement (Lines 910505-910510):

When `byokDisabled` is true:
```javascript
e.reactiveStorageService.applicationUserPersistentStorage.useOpenAIKey &&
  e.reactiveStorageService.setApplicationUserPersistentStorage("useOpenAIKey", !1)
e.reactiveStorageService.applicationUserPersistentStorage.useClaudeKey &&
  e.reactiveStorageService.setApplicationUserPersistentStorage("useClaudeKey", !1)
e.reactiveStorageService.applicationUserPersistentStorage.useGoogleKey &&
  e.reactiveStorageService.setApplicationUserPersistentStorage("useGoogleKey", !1)
```

Enterprise admins can force team members to use company-managed API access.

---

## Related Team Settings

### Usage Pricing Controls

**SetAdminOnlyUsagePricingRequest** (Lines 275333-275342):
```javascript
{
  team_id: int32,                    // Field #1
  admin_only_usage_pricing: bool     // Field #2
}
```

### Dashboard Analytics Controls

**UpdateTeamDashboardAnalyticsSettingRequest** (Lines 283899-283908):
```javascript
{
  team_id: int32,                           // Field #1
  dashboard_analytics_requires_admin: bool  // Field #2
}
```

### Team Object Admin Settings (Line 272381):

```javascript
this.adminOnlyUsagePricing = !1
this.dashboardAnalyticsRequiresAdmin = !1
this.individualSpendLimitsBlocked = !1
```

---

## Answers to Original Questions

### 1. Can enterprise admins restrict which Bedrock models team members can use?

**Partial Yes**: Enterprise admins can use `allowedModels`/`blockedModels` in team admin settings to restrict models. However, this applies globally to ALL models, not just Bedrock specifically. There is no Bedrock-specific model restriction mechanism.

### 2. Is there per-user or per-team rate limiting for Bedrock API calls?

**No Evidence Found**: The client code shows `request_quota_per_seat` (Line 272417) for general request quota, but no Bedrock-specific rate limiting was found. Rate limiting likely happens server-side.

### 3. How does Bedrock usage integrate with Cursor's usage analytics?

**Minimal Integration Found**: The `dashboardAnalyticsRequiresAdmin` flag controls who can view analytics, but there's no evidence of Bedrock-specific usage tracking in the client. Usage tracking would be server-side.

### 4. Are there audit logs for Bedrock requests showing which user made which request?

**No Client-Side Evidence**: No audit logging mechanism for Bedrock requests was found in the client code. Audit logging would need to be implemented server-side.

---

## gRPC Service Summary

### Dashboard Service Methods (Bedrock-related):

| Method | Purpose |
|--------|---------|
| `ValidateBedrockIamRole` | Validate IAM role can access Bedrock |
| `DeleteBedrockIamRole` | Remove IAM role configuration |
| `GetTeamAdminSettings` | Retrieve team admin settings including model controls |
| `SetAdminOnlyUsagePricing` | Control usage pricing visibility |
| `UpdateTeamDashboardAnalyticsSetting` | Control analytics visibility |

### AI Service Methods:

| Method | Purpose |
|--------|---------|
| `TestBedrockCredentials` | Test AWS credentials for Bedrock access |
| `GetBedrockModels` | Retrieve available Bedrock models (for credential-based access) |

---

## Security Considerations

1. **IAM Role ARNs Transmitted to Server**: The IAM role ARN and external ID are sent to Cursor's backend, which performs the role assumption. This means Cursor's servers have the ability to access the customer's Bedrock resources.

2. **No Local Credential Storage**: With IAM role access, credentials are set to placeholder `"iam"` strings - actual AWS credential management happens server-side.

3. **BYOK Enforcement**: Enterprise can disable bring-your-own-key, forcing all AI API calls through Cursor's infrastructure.

---

## Architecture Diagram

```
+------------------+     +-------------------+     +------------------+
|   Cursor IDE     |     |  Cursor Backend   |     |   AWS Bedrock    |
|   (Client)       |     |   (aiserver)      |     |                  |
+--------+---------+     +--------+----------+     +--------+---------+
         |                        |                         |
         | 1. hasBedrockIamRole   |                         |
         |    = true              |                         |
         |                        |                         |
         | 2. API Request with    |                         |
         |    accessKey="iam"     |                         |
         +----------------------->|                         |
         |                        |                         |
         |                        | 3. AssumeRole with      |
         |                        |    team's IAM role +    |
         |                        |    external ID          |
         |                        +------------------------>|
         |                        |                         |
         |                        | 4. Temporary creds      |
         |                        |<------------------------+
         |                        |                         |
         |                        | 5. Bedrock API call     |
         |                        +------------------------>|
         |                        |                         |
         | 6. Response            | 7. Response             |
         |<-----------------------+<------------------------+
         |                        |                         |
```

---

## Files and Line References

| Component | File | Lines |
|-----------|------|-------|
| Team protobuf | workbench.desktop.main.js | 272379-272480 |
| ValidateBedrockIamRole Request | workbench.desktop.main.js | 278985-279028 |
| ValidateBedrockIamRole Response | workbench.desktop.main.js | 279030-279064 |
| DeleteBedrockIamRole Request/Response | workbench.desktop.main.js | 279065-279129 |
| BedrockCredentials protobuf | workbench.desktop.main.js | 141286-141331 |
| Bedrock model list | workbench.desktop.main.js | 290759-290762 |
| AdminSettingsService | workbench.desktop.main.js | 290773-290843 |
| Bedrock UI settings panel | workbench.desktop.main.js | 910564-910750 |
| Membership refresh with Bedrock | workbench.desktop.main.js | 1098092-1098132 |
| gRPC service definitions | workbench.desktop.main.js | 719517-719605, 720153-720157 |

---

## Recommendations for Further Investigation

1. **Server-Side Rate Limiting**: The client code suggests rate limiting exists (`request_quota_per_seat`), but Bedrock-specific limits would need server-side investigation.

2. **Audit Logging**: Investigate Cursor's backend API for audit logging endpoints - this functionality is not exposed in the client.

3. **Model Restrictions**: The general `allowedModels`/`blockedModels` could be used for Bedrock models, but enterprise docs should clarify if Bedrock-specific restrictions are available.
