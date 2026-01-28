# TASK-78: AWS Bedrock IAM Role Authentication for Enterprise Cursor

## Executive Summary

Cursor Enterprise supports AWS Bedrock integration through two authentication mechanisms:
1. **User-provided AWS credentials** (Access Key ID + Secret Access Key) - available to all users
2. **Team-configured IAM role assumption** - Enterprise-only feature where admins configure a cross-account IAM role that Cursor's backend assumes on behalf of team members

The IAM role approach allows enterprise teams to use Bedrock without individual users needing AWS credentials. The client signals IAM role usage by sending `accessKey: "iam"` and `secretKey: "iam"` as sentinel values.

## Architecture Overview

```
+-------------------------------------------------------------------+
|                      CURSOR CLIENT                                 |
+-------------------------------------------------------------------+
|  BedrockState (local storage)                                      |
|  +-- accessKey: string (user's key OR "iam" sentinel)             |
|  +-- secretKey: string (user's key OR "iam" sentinel)             |
|  +-- region: string (e.g., "us-east-2")                           |
|  +-- useBedrock: boolean                                           |
|  +-- sessionToken: string (optional, for STS tokens)              |
+-------------------------------------------------------------------+
|  hasBedrockIamRole: boolean (set from team config)                 |
+----------------------------+--------------------------------------+
                             |
                             v
+-------------------------------------------------------------------+
|                    CURSOR AI SERVER                                |
+-------------------------------------------------------------------+
|  Team Entity (aiserver.v1.Team)                                    |
|  +-- bedrockIamRole: string (ARN of IAM role)                     |
|  +-- bedrockExternalId: string (external ID for STS)              |
+-------------------------------------------------------------------+
|  When credentials.accessKey == "iam":                              |
|  -> Server performs STS AssumeRole using team's bedrockIamRole    |
|  -> Returns temporary credentials to make Bedrock API calls        |
+----------------------------+--------------------------------------+
                             |
                             v
+-------------------------------------------------------------------+
|                        AWS BEDROCK                                 |
|  (Customer's AWS Account)                                          |
+-------------------------------------------------------------------+
```

## Protobuf Schemas

### Team Configuration (Server-side)

```protobuf
// aiserver.v1.Team - Field definitions (lines 272380-272516)
message Team {
  string name = 1;
  int32 id = 2;
  Role role = 3;
  int32 seats = 4;
  bool has_billing = 5;
  int32 request_quota_per_seat = 6;
  bool privacy_mode_forced = 7;
  bool allow_sso = 8;
  bool admin_only_usage_pricing = 9;
  string subscription_status = 10;
  string bedrock_iam_role = 11;        // <-- IAM role ARN for Bedrock
  bool verified = 12;
  bool is_enterprise = 13;
  bool privacy_mode_migration_opted_out = 14;
  string bedrock_external_id = 15;     // <-- External ID for STS AssumeRole
  string membership_type = 16;
  // ... additional fields for billing/spend
}
```

### BedrockState (Client-side Storage)

```protobuf
// aiserver.v1.BedrockState (lines 91731-91780)
message BedrockState {
  string access_key = 1;      // User's AWS Access Key ID or "iam" sentinel
  string secret_key = 2;      // User's AWS Secret Key or "iam" sentinel
  string region = 3;          // AWS region (e.g., "us-east-2")
  bool use_bedrock = 4;       // Toggle to enable Bedrock
  string session_token = 5;   // Optional STS session token
}
```

### BedrockCredentials (Agent Request)

```protobuf
// agent.v1.BedrockCredentials (lines 141286-141331)
message BedrockCredentials {
  string access_key = 1;
  string secret_key = 2;
  string region = 3;
  optional string session_token = 4;
}

// agent.v1.ModelDetails (lines 141332-141414)
message ModelDetails {
  string model_id = 1;
  string display_model_id = 3;
  string display_name = 4;
  string display_name_short = 5;
  repeated string aliases = 6;
  optional ThinkingDetails thinking_details = 2;
  optional bool max_mode = 7;
  oneof credentials {
    ApiKeyCredentials api_key_credentials = 8;
    AzureCredentials azure_credentials = 9;
    BedrockCredentials bedrock_credentials = 10;  // <-- Bedrock option
  }
}
```

### IAM Role Validation API

```protobuf
// aiserver.v1.ValidateBedrockIamRoleRequest (lines 278985-279029)
message ValidateBedrockIamRoleRequest {
  int32 team_id = 1;
  string bedrock_iam_role = 2;   // IAM role ARN to validate
  string region = 3;              // AWS region
  string model_id = 4;            // Model to test access
}

// aiserver.v1.ValidateBedrockIamRoleResponse (lines 279030-279064)
message ValidateBedrockIamRoleResponse {
  bool success = 1;
  string error_message = 2;
}

// aiserver.v1.DeleteBedrockIamRoleRequest (lines 279065-279094)
message DeleteBedrockIamRoleRequest {
  int32 team_id = 1;
}

// aiserver.v1.DeleteBedrockIamRoleResponse (lines 279095-279129)
message DeleteBedrockIamRoleResponse {
  bool success = 1;
  string error_message = 2;
}
```

### Bedrock Credentials Testing API

```protobuf
// aiserver.v1.TestBedrockCredentialsRequest (lines 174773-174817)
message TestBedrockCredentialsRequest {
  string access_key = 1;
  string secret_key = 2;
  string region = 3;
  string model_name = 4;
}

// aiserver.v1.TestBedrockCredentialsResponse (lines 174818-174858)
message TestBedrockCredentialsResponse {
  bool success = 1;
  optional string error = 2;
}

// aiserver.v1.GetBedrockModelsRequest (lines 174854-174894)
message GetBedrockModelsRequest {
  string access_key = 1;
  string secret_key = 2;
  string region = 3;
}

// aiserver.v1.GetBedrockModelsResponse (lines 174894-174930)
message GetBedrockModelsResponse {
  repeated string models = 1;
  optional string error = 2;
}
```

## gRPC Service Endpoints

### DashboardService (aiserver.v1.DashboardService)

```javascript
// Line 719601-719606
validateBedrockIamRole: {
    name: "ValidateBedrockIamRole",
    I: ValidateBedrockIamRoleRequest,
    O: ValidateBedrockIamRoleResponse,
    kind: Kt.Unary
}

// Line 720153-720158
deleteBedrockIamRole: {
    name: "DeleteBedrockIamRole",
    I: DeleteBedrockIamRoleRequest,
    O: DeleteBedrockIamRoleResponse,
    kind: Kt.Unary
}

// Line 718911-718915
getTeams: {
    name: "GetTeams",
    I: GetTeamsRequest,
    O: GetTeamsResponse,
    kind: Kt.Unary
}
```

### AIService

```javascript
// Line 440248-440253 / 549396-549401
testBedrockCredentials: {
    name: "TestBedrockCredentials",
    I: TestBedrockCredentialsRequest,
    O: TestBedrockCredentialsResponse,
    kind: Kt.Unary
}
```

## Authentication Flows

### Flow 1: Enterprise IAM Role (Automatic)

1. **Team Setup** (Admin Dashboard):
   - Admin configures `bedrock_iam_role` ARN in team settings
   - Admin sets `bedrock_external_id` for secure cross-account access
   - Server validates the role via `ValidateBedrockIamRole` RPC

2. **Client Detection** (on login/membership refresh):
   ```javascript
   // Line 1098122-1098128
   te.some(Re => Re.bedrockIamRole !== null && Re.bedrockIamRole !== "") ? (
     this._reactiveStorageService.setApplicationUserPersistentStorage("hasBedrockIamRole", !0),
     this._reactiveStorageService.setApplicationUserPersistentStorage("bedrockState", {
       useBedrock: !1,
       region: "us-east-2",
       ...this._reactiveStorageService.applicationUserPersistentStorage.bedrockState,
       accessKey: "iam",    // <-- Sentinel value
       secretKey: "iam"     // <-- Sentinel value
     })
   ) : this._reactiveStorageService.setApplicationUserPersistentStorage("hasBedrockIamRole", !1)
   ```

3. **UI Behavior**:
   - When `hasBedrockIamRole === true`, shows simplified UI (line 910596):
     - Message: "Your team has configured AWS Bedrock access. You can use your teams Bedrock instance without any additional configuration."
     - Only requires region selection (no access keys)

4. **Request Flow**:
   - Client sends `accessKey: "iam"` and `secretKey: "iam"` as credentials
   - Server detects the sentinel values
   - Server performs `sts:AssumeRole` using the team's `bedrockIamRole` and `bedrockExternalId`
   - Temporary credentials are used to call Bedrock APIs

### Flow 2: User-Provided Credentials (Manual)

1. **User Configuration**:
   - User enters AWS Access Key ID in settings
   - User enters AWS Secret Access Key in settings
   - User selects region

2. **Credential Conversion** (lines 940418-940443):
   ```javascript
   convertModelDetailsToCredentials(e) {
     return e.azureState?.useAzure === !0 ? {
       case: "azureCredentials",
       value: new AzureCredentials({...})
     } : e.bedrockState?.useBedrock === !0 ? {
       case: "bedrockCredentials",
       value: new BedrockCredentials({
         accessKey: e.bedrockState.accessKey,
         secretKey: e.bedrockState.secretKey,
         region: e.bedrockState.region,
         sessionToken: e.bedrockState.sessionToken
       })
     } : e.apiKey ? {
       case: "apiKeyCredentials",
       value: new ApiKeyCredentials({...})
     } : { case: void 0 }
   }
   ```

3. **Validation** (lines 895192-895202):
   ```javascript
   async testBedrockCredentials(accessKey, secretKey, region, modelName) {
     const response = await this.aiClient().testBedrockCredentials({
       accessKey: accessKey,
       secretKey: secretKey,
       region: region,
       modelName: modelName
     });
     return {
       valid: response.success,
       error: response.error
     }
   }
   ```

## Supported Bedrock Models

The client supports these Bedrock model IDs with regional prefixes (line 290762):

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

### Regional Prefix Mapping

```javascript
// Line 910571-910573
if (region.startsWith("ap-")) {
  modelId = modelId.replace("us.", "apac.");
} else if (region.startsWith("eu-")) {
  modelId = modelId.replace("us.", "eu.");
} else if (region.startsWith("ca-")) {
  modelId = modelId.replace("us.", "ca.");
}
```

| Region Pattern | Model Prefix |
|----------------|--------------|
| `us-*` | `us.anthropic.*` |
| `ap-*` | `apac.anthropic.*` |
| `eu-*` | `eu.anthropic.*` |
| `ca-*` | `ca.anthropic.*` |

## AWS IAM Requirements

### Customer's AWS Account (Target)

1. **IAM Role Trust Policy**:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "AWS": "arn:aws:iam::CURSOR_ACCOUNT_ID:role/cursor-bedrock-service"
         },
         "Action": "sts:AssumeRole",
         "Condition": {
           "StringEquals": {
             "sts:ExternalId": "<team_bedrock_external_id>"
           }
         }
       }
     ]
   }
   ```

2. **Bedrock Permissions Policy**:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "bedrock:InvokeModel",
           "bedrock:InvokeModelWithResponseStream"
         ],
         "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.*"
       }
     ]
   }
   ```

### Cursor's AWS Account (Source)

The server-side role needs permission to assume customer roles:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::*:role/*",
      "Condition": {
        "StringLike": {
          "sts:ExternalId": "*"
        }
      }
    }
  ]
}
```

## Enterprise Admin Controls

### BYOK (Bring Your Own Key) Disabled

Enterprise admins can disable BYOK, forcing all users to use team-managed Bedrock access (lines 910505-910520):

```javascript
if (byokDisabled) {
  // Disable individual keys
  e.reactiveStorageService.setApplicationUserPersistentStorage("useOpenAIKey", !1);
  e.reactiveStorageService.setApplicationUserPersistentStorage("useClaudeKey", !1);
  e.reactiveStorageService.setApplicationUserPersistentStorage("useGoogleKey", !1);

  // Disable Azure state
  const rt = e.reactiveStorageService.applicationUserPersistentStorage.azureState;
  rt?.useAzure && e.reactiveStorageService.setApplicationUserPersistentStorage("azureState", {
    ...rt,
    useAzure: !1
  });

  // Disable user Bedrock state
  const bt = e.reactiveStorageService.applicationUserPersistentStorage.bedrockState;
  bt?.useBedrock && e.reactiveStorageService.setApplicationUserPersistentStorage("bedrockState", {
    ...bt,
    useBedrock: !1
  });
}
```

### Model Blocking

Enterprise admins can block specific models using `allowedModels`/`blockedModels` lists (line 290841):

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

## Security Considerations

1. **External ID**: The `bedrockExternalId` field prevents confused deputy attacks when assuming cross-account roles

2. **Sentinel Values**: Using `"iam"` as sentinel for access/secret keys:
   - Pros: Clean detection mechanism on server
   - Cons: Potential collision if user literally has "iam" as credentials (extremely unlikely)

3. **No Client-Side Role Assumption**: The IAM role assumption happens server-side, so:
   - Customer role ARN is never exposed to client
   - Temporary credentials are managed by Cursor's backend
   - Users don't need AWS CLI or SDK locally

4. **Privacy Mode Integration**: Bedrock state respects privacy mode settings

5. **Credential Clearing on Team Change**: When membership changes (lines 1098098, 1098132):
   - `hasBedrockIamRole` is set to false when user leaves team
   - Team IDs are cleared from storage

## File References

| Component | File Location | Line Numbers |
|-----------|---------------|--------------|
| BedrockState proto | workbench.desktop.main.js | 91731-91780 |
| Team proto | workbench.desktop.main.js | 272380-272516 |
| ValidateBedrockIamRole proto | workbench.desktop.main.js | 278985-279129 |
| TestBedrockCredentials proto | workbench.desktop.main.js | 174773-174930 |
| BedrockCredentials (agent) | workbench.desktop.main.js | 141286-141331 |
| ModelDetails (with oneof) | workbench.desktop.main.js | 141332-141414 |
| Membership refresh logic | workbench.desktop.main.js | 1098090-1098132 |
| Settings UI | workbench.desktop.main.js | 910555-910820 |
| Credential conversion | workbench.desktop.main.js | 940418-940443 |
| Supported models (JQl) | workbench.desktop.main.js | 290762 |
| Regional prefix mapping | workbench.desktop.main.js | 910571-910573, 894673-894694 |
| Service definitions | workbench.desktop.main.js | 719601-720158 |
| Admin settings (BYOK) | workbench.desktop.main.js | 290773-290843, 910505-910520 |
| getTeams RPC | workbench.desktop.main.js | 1098447-1098473 |

## Key Observations

1. **Server-Side Credential Management**: The client never sees actual AWS credentials when using IAM role mode. All STS AssumeRole operations happen on Cursor's backend.

2. **Graceful Fallback**: The system defaults to `region: "us-east-2"` when IAM role is configured but no region is specified.

3. **Model Activation Flow**: When Bedrock is enabled, the client automatically adds Bedrock models to the user's available model list and enables them (lines 910570-910573).

4. **Validation Before Use**: The `ValidateBedrockIamRole` RPC allows admins to test the IAM role configuration before deploying to their team.

## Open Questions / Further Investigation

1. **Server-side implementation**: How exactly does the server perform STS AssumeRole? What's the TTL for temporary credentials?

2. **Rate limiting**: Are there per-team rate limits for Bedrock requests via IAM role?

3. **Audit logging**: Does Cursor log which user made which Bedrock request for enterprise compliance?

4. **Model access**: Can enterprise admins restrict which Bedrock models team members can use? (Likely yes via `allowedModels`/`blockedModels`)

5. **Cross-region**: How are cross-region Bedrock requests handled when the IAM role is region-specific?

6. **Credential caching**: Does the server cache assumed role credentials, or does it call AssumeRole for each request?

---

*Analysis completed: 2026-01-28*
*Source: Cursor IDE 2.3.41 workbench.desktop.main.js*
