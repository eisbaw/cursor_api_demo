# TASK-29: Authentication and Authorization Message Schemas

## Overview

This document catalogs the authentication and authorization gRPC message schemas discovered in the Cursor IDE beautified source (version 2.3.41). The schemas are part of the `aiserver.v1` and `agent.v1` protobuf packages.

## 1. AuthService (aiserver.v1)

The main authentication gRPC service is defined at line ~814570:

```protobuf
service AuthService {
    rpc GetEmail(GetEmailRequest) returns (GetEmailResponse);
    rpc EmailValid(EmailValidRequest) returns (EmailValidResponse);
    rpc DownloadUpdate(DownloadUpdateRequest) returns (DownloadUpdateResponse);
    rpc MarkPrivacy(MarkPrivacyRequest) returns (MarkPrivacyResponse);
    rpc SwitchCmdKFraction(SwitchCmdKFractionRequest) returns (SwitchCmdKFractionResponse);
    rpc GetCustomerId(CustomerIdRequest) returns (CustomerIdResponse);
    rpc SetPrivacyMode(SetPrivacyModeRequest) returns (SetPrivacyModeResponse);
    rpc GetSessionToken(GetSessionTokenRequest) returns (GetSessionTokenResponse);
    rpc CheckSessionToken(CheckSessionTokenRequest) returns (CheckSessionTokenResponse);
    rpc ListActiveSessions(ListActiveSessionsRequest) returns (ListActiveSessionsResponse);
    rpc RevokeSession(RevokeSessionRequest) returns (RevokeSessionResponse);
    rpc ListJwtPublicKeys(ListJwtPublicKeysRequest) returns (ListJwtPublicKeysResponse);
}
```

## 2. User Message Schema

**Source Location:** Line ~813503

```protobuf
message User {
    string id = 2;
    optional string email = 3;
    optional bool email_verified = 4;
    optional string first_name = 5;
    optional string last_name = 6;
    optional string created_at = 7;
    optional string updated_at = 8;
}
```

## 3. Session Management Schemas

### Session Message (Line ~813570)

```protobuf
message Session {
    string session_id = 1;
    SessionType type = 2;
    string created_at = 3;
    string expires_at = 4;
}

enum SessionType {
    SESSION_TYPE_UNSPECIFIED = 0;
    SESSION_TYPE_WEB = 1;
    SESSION_TYPE_CLIENT = 2;
    SESSION_TYPE_BUGBOT = 3;
    SESSION_TYPE_BACKGROUND_AGENT = 4;
    SESSION_TYPE_SUPPORT_IMPERSONATION = 5;
    SESSION_TYPE_API_KEY_TOKEN = 6;
    SESSION_TYPE_TRAINING = 7;
}
```

### GetSessionTokenRequest (Line ~813769)

```protobuf
message GetSessionTokenRequest {
    User user = 1;
    Destination destination = 2;
    optional string stub = 3;
    optional string code = 4;

    enum Destination {
        DESTINATION_UNSPECIFIED = 0;
        DESTINATION_PORTAL = 1;
        DESTINATION_AISERVER = 2;
        DESTINATION_AUTH_PROXY = 3;
    }
}
```

### GetSessionTokenResponse (Line ~813833)

```protobuf
message GetSessionTokenResponse {
    string session_token = 1;
    optional string id = 2;
    bool should_show_trial = 3;
    bool enable_trial_for_deep_control = 4;
}
```

### CheckSessionTokenRequest/Response (Lines ~813880, ~813916)

```protobuf
message CheckSessionTokenRequest {
    string session_token = 1;
    User user = 2;
}

message CheckSessionTokenResponse {
    bool valid = 1;
}
```

### ListActiveSessionsRequest/Response (Lines ~813644, ~813670)

```protobuf
message ListActiveSessionsRequest {
    // Empty
}

message ListActiveSessionsResponse {
    repeated Session sessions = 1;
}
```

### RevokeSessionRequest/Response (Lines ~813702, ~813738)

```protobuf
message RevokeSessionRequest {
    string session_id = 1;
    SessionType type = 2;
}

message RevokeSessionResponse {
    bool success = 1;
}
```

## 4. Login/Logout Schemas

### LoginRequest/Response (Lines ~100763, ~100788)

```protobuf
message LoginRequest {
    // Empty - triggers login flow
}

message LoginResponse {
    string login_url = 1;
}
```

### PollLoginRequest/Response (Lines ~100873, ~100898)

```protobuf
message PollLoginRequest {
    // Empty - polls login status
}

message PollLoginResponse {
    Status status = 1;

    enum Status {
        STATUS_UNSPECIFIED = 0;
        STATUS_LOGGED_IN = 1;
        STATUS_FAILURE = 2;
        STATUS_CHECKING = 3;
    }
}
```

### IsLoggedInRequest/Response (Lines ~100818, ~100843)

```protobuf
message IsLoggedInRequest {
    // Empty
}

message IsLoggedInResponse {
    bool logged_in = 1;
}
```

### LogoutRequest/Response (Lines ~100112, ~100137)

```protobuf
message LogoutRequest {
    // Empty
}

message LogoutResponse {
    Status status = 1;

    enum Status {
        STATUS_UNSPECIFIED = 0;
        STATUS_SUCCESS = 1;
        STATUS_FAILURE = 2;
        STATUS_NOT_LOGGED_IN = 3;
    }
}
```

## 5. Email Validation Schemas

### GetEmailRequest/Response (Lines ~814116, ~814142)

```protobuf
message GetEmailRequest {
    // Empty
}

message GetEmailResponse {
    string email = 1;
    SignUpType sign_up_type = 2;

    enum SignUpType {
        SIGN_UP_TYPE_UNSPECIFIED = 0;
        SIGN_UP_TYPE_AUTH_0 = 1;
        SIGN_UP_TYPE_GITHUB = 2;
        SIGN_UP_TYPE_GOOGLE = 3;
        SIGN_UP_TYPE_WORKOS = 4;
    }
}
```

### EmailValidRequest/Response (Lines ~814197, ~814228)

```protobuf
message EmailValidRequest {
    string email = 1;
}

message EmailValidResponse {
    bool valid = 1;
}
```

### CustomerIdRequest/Response (Lines ~813955, ~813986)

```protobuf
message CustomerIdRequest {
    string email = 1;
}

message CustomerIdResponse {
    optional string customer_id = 1;
}
```

## 6. JWT Public Keys

### ListJwtPublicKeysRequest/Response (Lines ~814483, ~814545)

```protobuf
message ListJwtPublicKeysRequest {
    // Empty
}

message ListJwtPublicKeysResponse {
    repeated JwtPublicKey keys = 1;
}

message JwtPublicKey {
    string kid = 1;
    string public_key = 2;
}
```

## 7. Privacy Mode Schemas

### SetPrivacyModeRequest/Response (Lines ~814394, ~814457)

```protobuf
message SetPrivacyModeRequest {
    bool privacy_mode_enabled = 1;
    string machine_identifier = 2;
    bool new_onboarding_done = 3;
    bool new_change_management_done = 4;
    bool eligible_for_snippet_learning = 5;
    optional int64 timestamp_of_onboarding = 6;
    optional int64 timestamp_of_change_management = 7;
}

message SetPrivacyModeResponse {
    // Empty
}
```

### MarkPrivacyRequest/Response (Lines ~814018, ~814090)

```protobuf
message MarkPrivacyRequest {
    bool privacy = 1;
    optional bool current_privacy_mode = 2;
    optional bool onboarding_privacy_mode = 3;
    bool is_using_current_and_onboarding_format = 4;
    optional string onboarding_data_privacy_version = 5;
    optional double time_elapsed_since_onboarding = 6;
    optional bool first_after_waiting_period = 7;
    optional bool configured_privacy_mode_for_settings = 8;
}

message MarkPrivacyResponse {
    // Empty
}
```

## 8. Token Refresh Mechanism

The token refresh is implemented client-side at line ~1098039. Key details:

### OAuth Token Refresh Flow

```javascript
// Endpoint: ${backendUrl}/oauth/token
// Method: POST
// Content-Type: application/json

// Request body:
{
    "grant_type": "refresh_token",
    "client_id": "<auth_client_id>",
    "refresh_token": "<stored_refresh_token>"
}

// Response:
{
    "access_token": "<new_access_token>",
    "shouldLogout": boolean  // If true, triggers logout
}
```

### Token Storage Keys
- `cursorAuth/accessToken` - Current access token
- `cursorAuth/refreshToken` - Refresh token for getting new access tokens

### Token Expiration
- Tokens are checked against `Q8s` constant for expiration threshold
- JWT expiration is decoded from token payload (`exp` field)
- Automatic refresh occurs when token is expired or about to expire

## 9. Membership Types (Authorization Levels)

**Source Location:** Line ~268990

```typescript
enum MembershipType {
    FREE = "free",
    PRO = "pro",
    PRO_PLUS = "pro_plus",
    ENTERPRISE = "enterprise",
    FREE_TRIAL = "free_trial",
    ULTRA = "ultra"
}
```

These membership types control feature access throughout the application.

## 10. Team Authorization Schemas

### Team Message (Line ~272387)

```protobuf
message Team {
    string name = 1;
    int32 id = 2;
    TeamRole role = 3;
    int32 seats = 4;
    bool has_billing = 5;
    int32 request_quota_per_seat = 6;
    bool privacy_mode_forced = 7;
    bool allow_sso = 8;
    bool admin_only_usage_pricing = 9;
    string subscription_status = 10;
    string bedrock_iam_role = 11;
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

### TeamRole Enum (Line ~269065)

```protobuf
enum TeamRole {
    TEAM_ROLE_UNSPECIFIED = 0;
    TEAM_ROLE_OWNER = 1;
    TEAM_ROLE_MEMBER = 2;
    TEAM_ROLE_FREE_OWNER = 3;
    TEAM_ROLE_REMOVED = 4;
}
```

### TeamMember Message (Line ~273308)

```protobuf
message TeamMember {
    string name = 1;
    string email = 2;
    int32 id = 3;
    TeamRole role = 4;
    bool is_removed = 5;
}
```

## 11. API Key Authorization

### ApiKey Message (Line ~273715)

```protobuf
message ApiKey {
    int32 id = 1;
    string masked_key = 2;
    string name = 3;
    int64 created_at = 4;
    optional string service_account_name = 5;
    repeated string scopes = 6;
}
```

### User API Key Operations

```protobuf
message CreateUserApiKeyRequest { }
message CreateUserApiKeyResponse { string api_key = 1; }
message RevokeUserApiKeyRequest { }
message RevokeUserApiKeyResponse { }
message ListUserApiKeysRequest { }
message ListUserApiKeysResponse { repeated ApiKey api_keys = 1; }
message CheckUserApiKeyAccessRequest { }
message CheckUserApiKeyAccessResponse { bool has_access = 1; }
```

### Team API Key Operations

```protobuf
message CreateTeamApiKeyRequest { int32 team_id = 1; string name = 2; }
message CreateTeamApiKeyResponse { string api_key = 1; }
message RevokeTeamApiKeyRequest { int32 team_id = 1; int32 key_id = 2; }
message RevokeTeamApiKeyResponse { }
message ListTeamApiKeysRequest { int32 team_id = 1; }
message ListTeamApiKeysResponse { repeated ApiKey api_keys = 1; }
```

## 12. Permission Denied Messages (Agent Operations)

### Agent Operation Permissions (agent.v1)

```protobuf
message WritePermissionDenied {
    string path = 1;
    string directory = 2;
    string operation = 3;
    string error = 4;
    bool is_readonly = 5;
}

message ReadPermissionDenied {
    string path = 1;
    // Additional fields for error details
}

message DeletePermissionDenied {
    string path = 1;
    // Additional fields
}

message ShellPermissionDenied {
    // Shell command permission fields
}

message McpPermissionDenied {
    // MCP tool permission fields
}

message DiagnosticsPermissionDenied {
    // Diagnostics access permission fields
}

message EditReadPermissionDenied {
    // Edit operation read permission
}

message EditWritePermissionDenied {
    // Edit operation write permission
}
```

### Subagent Permission Mode (Line ~119485)

```protobuf
enum CustomSubagentPermissionMode {
    CUSTOM_SUBAGENT_PERMISSION_MODE_UNSPECIFIED = 0;
    CUSTOM_SUBAGENT_PERMISSION_MODE_DEFAULT = 1;
    CUSTOM_SUBAGENT_PERMISSION_MODE_READONLY = 2;
}
```

## 13. Composer Capability Types

The application uses capabilities to control feature access:

```protobuf
enum ComposerCapabilityType {
    COMPOSER_CAPABILITY_TYPE_UNSPECIFIED = 0;
    COMPOSER_CAPABILITY_TYPE_LOOP_ON_LINTS = 1;
    COMPOSER_CAPABILITY_TYPE_LOOP_ON_TESTS = 2;
    COMPOSER_CAPABILITY_TYPE_MEGA_PLANNER = 3;
    COMPOSER_CAPABILITY_TYPE_LOOP_ON_COMMAND = 4;
    COMPOSER_CAPABILITY_TYPE_TOOL_CALL = 5;
    COMPOSER_CAPABILITY_TYPE_DIFF_REVIEW = 6;
    COMPOSER_CAPABILITY_TYPE_CONTEXT_PICKING = 7;
    COMPOSER_CAPABILITY_TYPE_EDIT_TRAIL = 8;
    COMPOSER_CAPABILITY_TYPE_AUTO_CONTEXT = 9;
    COMPOSER_CAPABILITY_TYPE_CONTEXT_PLANNER = 10;
    COMPOSER_CAPABILITY_TYPE_DIFF_HISTORY = 11;
    COMPOSER_CAPABILITY_TYPE_REMEMBER_THIS = 12;
    COMPOSER_CAPABILITY_TYPE_DECOMPOSER = 13;
    COMPOSER_CAPABILITY_TYPE_USES_CODEBASE = 14;
    COMPOSER_CAPABILITY_TYPE_TOOL_FORMER = 15;
    COMPOSER_CAPABILITY_TYPE_CURSOR_RULES = 16;
    COMPOSER_CAPABILITY_TYPE_TOKEN_COUNTER = 17;
    COMPOSER_CAPABILITY_TYPE_USAGE_DATA = 18;
    COMPOSER_CAPABILITY_TYPE_CHIMES = 19;
    COMPOSER_CAPABILITY_TYPE_CODE_DECAY_TRACKER = 20;
    COMPOSER_CAPABILITY_TYPE_BACKGROUND_COMPOSER = 21;
    COMPOSER_CAPABILITY_TYPE_SUMMARIZATION = 22;
    COMPOSER_CAPABILITY_TYPE_AI_CODE_TRACKING = 23;
    COMPOSER_CAPABILITY_TYPE_QUEUING = 24;
    COMPOSER_CAPABILITY_TYPE_MEMORIES = 25;
    COMPOSER_CAPABILITY_TYPE_RCP_LOGS = 26;
    COMPOSER_CAPABILITY_TYPE_KNOWLEDGE_FETCH = 27;
    COMPOSER_CAPABILITY_TYPE_SLACK_INTEGRATION = 28;
    COMPOSER_CAPABILITY_TYPE_SUB_COMPOSER = 29;
    COMPOSER_CAPABILITY_TYPE_THINKING = 30;
    COMPOSER_CAPABILITY_TYPE_CONTEXT_WINDOW = 31;
    COMPOSER_CAPABILITY_TYPE_ONLINE_METRICS = 32;
    COMPOSER_CAPABILITY_TYPE_NOTIFICATIONS = 33;
    COMPOSER_CAPABILITY_TYPE_SPEC = 34;
}
```

## 14. Slack Authentication

### SetSlackAuthRequest/Response (Lines ~272740, ~272786)

```protobuf
message SetSlackAuthRequest {
    string slack_team_id = 1;
    string slack_user_id = 2;
    string nonce = 3;
    optional bool setup_complete = 4;
}

message SetSlackAuthResponse {
    // Empty
}
```

## 15. GitHub Permission Info

### GithubPermissionInfo (Line ~281025)

```protobuf
message GithubPermissionInfo {
    bool has_permission = 1;
    string permission_settings_url = 2;
}
```

---

## Key Source File Locations

| Schema Group | Approx. Line Numbers |
|--------------|---------------------|
| AuthService definition | 814570-814646 |
| User message | 813503-813568 |
| Session schemas | 813570-813768 |
| GetSessionToken | 813769-813878 |
| CheckSessionToken | 813880-813945 |
| Login/Logout | 100112-100934 |
| Email validation | 814116-814249 |
| JWT keys | 814483-814568 |
| Privacy mode | 814018-814473 |
| MembershipType enum | 268990 |
| Team schemas | 272380-272562 |
| TeamRole enum | 269065-269080 |
| API Key schemas | 273590-273830 |
| Permission denied msgs | 129155-134081 |
| Capabilities enum | 117857-117964 |

---

## 16. MCP OAuth Token Schemas

### StoreMcpOAuthTokenRequest (Line ~271275)

```protobuf
message StoreMcpOAuthTokenRequest {
    string server_url = 1;
    string refresh_token = 2;
    optional string client_id = 3;
    optional string client_secret = 4;
    optional string redirect_uri = 5;
}
```

### StoreMcpOAuthTokenResponse (Line ~271328)

```protobuf
message StoreMcpOAuthTokenResponse {
    // Empty
}
```

### ValidateMcpOAuthTokensRequest/Response (Lines ~271353, ~271384)

```protobuf
message ValidateMcpOAuthTokensRequest {
    repeated string server_urls = 1;
}

message ValidateMcpOAuthTokensResponse {
    repeated Result results = 1;

    message Result {
        string server_url = 1;
        bool has_valid_token = 2;
    }
}
```

### StoreMcpOAuthPendingStateRequest/Response (Lines ~271450, ~271503)

```protobuf
message StoreMcpOAuthPendingStateRequest {
    string server_url = 1;
    string code_verifier = 2;
    optional string client_id = 3;
    optional string client_secret = 4;
    optional string redirect_uri = 5;
}

message StoreMcpOAuthPendingStateResponse {
    string state_id = 1;
}
```

### McpOAuthStoredData (Line ~448872)

```protobuf
message McpOAuthStoredData {
    string refresh_token = 1;
    string client_id = 2;
    optional string client_secret = 3;
    repeated string redirect_uris = 4;
}
```

### McpOAuthStoredClientInfo (Line ~448919)

```protobuf
message McpOAuthStoredClientInfo {
    string client_id = 1;
    optional string client_secret = 2;
    repeated string redirect_uris = 3;
}
```

## 17. GitHub Access Token Schemas

### RefreshGithubAccessTokenRequest (agent.v1, Line ~807042)

```protobuf
message RefreshGithubAccessTokenRequest {
    string github_access_token = 1;
    string hostname = 2;
}
```

### RefreshGithubAccessTokenResponse (agent.v1, Line ~807078)

```protobuf
message RefreshGithubAccessTokenResponse {
    // Empty
}
```

### GetMcpRefreshTokensRequest/Response (agent.v1, Lines ~807484, ~807510)

```protobuf
message GetMcpRefreshTokensRequest {
    // Empty
}

message GetMcpRefreshTokensResponse {
    map<string, string> refresh_tokens = 1;  // server_url -> token
}
```

### GetGithubAccessTokenForReposRequest (Line ~340575/460320)

```protobuf
message GetGithubAccessTokenForReposRequest {
    // Repository info fields
}
```

### GetGithubAccessTokenForReposResponse (Line ~340617/460363)

```protobuf
message GetGithubAccessTokenForReposResponse {
    Status status = 1;
    string access_token = 2;

    enum Status {
        STATUS_UNSPECIFIED = 0;
        STATUS_SUCCESS = 1;
        STATUS_FAILURE = 2;
        // Additional statuses
    }
}
```

### RefreshGithubAccessTokenInBackgroundComposerRequest/Response (Lines ~336089, ~336113)

```protobuf
message RefreshGithubAccessTokenInBackgroundComposerRequest {
    // Request fields
}

message RefreshGithubAccessTokenInBackgroundComposerResponse {
    // Response fields
}
```

### RefreshGitHubAccessTokenRequest (aiserver.v1, Line ~831016)

```protobuf
message RefreshGitHubAccessTokenRequest {
    string github_access_token = 1;
    string hostname = 2;
}
```

### RefreshGitHubAccessTokenResponse (aiserver.v1, Line ~831052)

```protobuf
message RefreshGitHubAccessTokenResponse {
    // Empty
}
```

## 18. Temporary Access Token Schemas

### ProvideTemporaryAccessTokenRequest/Response (Lines ~830539, ~830570)

```protobuf
message ProvideTemporaryAccessTokenRequest {
    string access_token = 1;
}

message ProvideTemporaryAccessTokenResponse {
    // Empty
}
```

### SwProvideTemporaryAccessTokenRequest/Response (Lines ~121358, ~121388)

```protobuf
message SwProvideTemporaryAccessTokenRequest {
    string access_token = 1;
}

message SwProvideTemporaryAccessTokenResponse {
    // Empty - used in shadow workspace context
}
```

## 19. Service Account Schemas

### CreateTeamServiceAccountRequest/Response (Lines ~273833, ~273874)

```protobuf
message CreateTeamServiceAccountRequest {
    int32 team_id = 1;
    string name = 2;
}

message CreateTeamServiceAccountResponse {
    string service_account_id = 1;
}
```

### ListTeamServiceAccountsRequest/Response (Lines ~273909, ~273939)

```protobuf
message ListTeamServiceAccountsRequest {
    int32 team_id = 1;
}

message ListTeamServiceAccountsResponse {
    repeated ServiceAccount service_accounts = 1;
}
```

### DeleteTeamServiceAccountRequest/Response (Lines ~274108, ~274143)

```protobuf
message DeleteTeamServiceAccountRequest {
    int32 team_id = 1;
    string service_account_id = 2;
}

message DeleteTeamServiceAccountResponse {
    // Empty
}
```

### ServiceAccountKeyInfo (Line ~274062)

```protobuf
message ServiceAccountKeyInfo {
    int32 api_key_id = 1;
    string masked_api_key = 2;
    repeated string scopes = 3;
    int64 created_at = 4;
}
```

### RotateServiceAccountApiKeyRequest/Response (Lines ~274168, ~274209)

```protobuf
message RotateServiceAccountApiKeyRequest {
    int32 team_id = 1;
    string service_account_id = 2;
    optional int32 old_api_key_id = 3;
}

message RotateServiceAccountApiKeyResponse {
    string api_key = 1;
    ServiceAccountKeyInfo key_info = 2;
}
```

### GetServiceAccountSpendLimitRequest/Response (Lines ~283333, ~283369)

```protobuf
message GetServiceAccountSpendLimitRequest {
    int32 team_id = 1;
    string service_account_id = 2;
}

message GetServiceAccountSpendLimitResponse {
    optional float spend_limit = 1;
}
```

## 20. User API Key Schemas (Detailed)

### CreateUserApiKeyRequest/Response (Lines ~274244, ~274274)

```protobuf
message CreateUserApiKeyRequest {
    string name = 1;
}

message CreateUserApiKeyResponse {
    string api_key = 1;
}
```

### RevokeUserApiKeyRequest/Response (Lines ~274304, ~274334)

```protobuf
message RevokeUserApiKeyRequest {
    int32 id = 1;
}

message RevokeUserApiKeyResponse {
    // Empty
}
```

### ListUserApiKeysRequest/Response (Lines ~274359, ~274384)

```protobuf
message ListUserApiKeysRequest {
    // Empty
}

message ListUserApiKeysResponse {
    repeated ApiKey api_keys = 1;
}
```

### CheckUserApiKeyAccessRequest/Response (Lines ~285488, ~285513)

```protobuf
message CheckUserApiKeyAccessRequest {
    // Empty
}

message CheckUserApiKeyAccessResponse {
    bool has_access = 1;
}
```

## 21. Repository Authorization Schemas

### QueryOnlyRepoAccess (Line ~100414)

```protobuf
message QueryOnlyRepoAccess {
    string owner_auth_id = 1;
    string access_token = 2;
    string user_repo_owner = 3;
    string user_repo_name = 4;
}
```

### RepositoryStatusResponse Auth Errors (Lines ~101460, ~101485)

```protobuf
message RepositoryStatusResponse {
    // ... other fields

    message AuthTokenNotFound {
        // Nested message for auth token not found error
    }

    message AuthTokenNotAuthorized {
        // Nested message for auth token not authorized error
    }
}
```

## 22. Scope Upgrade Schemas

### UpgradeScopeRequest/Response (Lines ~100942, ~100973)

```protobuf
message UpgradeScopeRequest {
    repeated string scopes = 2;
}

message UpgradeScopeResponse {
    Status status = 1;

    enum Status {
        STATUS_UNSPECIFIED = 0;
        STATUS_SUCCESS = 1;
        STATUS_FAILURE = 2;
    }
}
```

## 23. Linear Auth URL Schemas

### GetLinearAuthUrlRequest/Response (Lines ~283965, ~283995)

```protobuf
message GetLinearAuthUrlRequest {
    // Request fields
}

message GetLinearAuthUrlResponse {
    string auth_url = 1;
}
```

## 24. Client-Side Token Management Implementation

**Source Location:** Lines ~1097663-1098999

### Token Storage Keys

```javascript
// Storage keys used by CursorAuthenticationService
const TOKEN_STORAGE_KEYS = {
    accessToken: "cursorAuth/accessToken",
    refreshToken: "cursorAuth/refreshToken",
    membershipType: "<dJe key>",           // Membership enum storage
    subscriptionStatus: "<Eps key>",        // Subscription status
    email: "<xps key>",                     // User email
    signUpType: "<Tps key>",                // Sign-up type enum
    openAIKey: "cursorAuth/openAIKey",      // Optional OpenAI API key
    claudeKey: "cursorAuth/claudeKey",      // Optional Claude API key
    googleKey: "cursorAuth/googleKey"       // Optional Google API key
};
```

### Token Refresh Implementation (Line ~1098039)

```javascript
// Token expiration threshold: 1272 hours * 60 min * 60 sec * 1000 ms
const Q8s = 1272 * 60 * 60 * 1000;

// Refresh endpoint: ${backendUrl}/oauth/token
// Request body:
{
    "grant_type": "refresh_token",
    "client_id": authClientId,
    "refresh_token": storedRefreshToken
}

// Response handling:
// - If shouldLogout === true: trigger logout flow
// - Otherwise: store new access_token (refresh token typically unchanged)
```

### Token Expiration Check (Line ~1097699)

```javascript
isTokenExpired(token) {
    const payload = decodeJwt(token);  // Gst function
    return new Date(payload.exp * 1000).getTime() < Date.now();
}
```

### Auto-Refresh Scheduling (Line ~1097688)

```javascript
// When storing new tokens:
const payload = decodeJwt(accessToken);
const expirationDate = new Date(payload.exp * 1000);
const refreshDate = new Date(expirationDate.getTime() - Q8s);

if (refreshDate.getTime() > Date.now()) {
    setTimeout(() => this.refreshAccessToken(),
               refreshDate.getTime() - Date.now());
}
```

## 25. Error Codes Related to Authentication

**Source Location:** Lines ~92685-92823

```javascript
const AUTH_ERROR_CODES = {
    ERROR_NOT_HIGH_ENOUGH_PERMISSIONS: "Permission level insufficient",
    ERROR_TASK_NO_PERMISSIONS: "Task permission denied",
    ERROR_AGENT_REQUIRES_LOGIN: "Agent requires authentication",
    ERROR_FREE_USER_USAGE_LIMIT: "Free tier usage limit reached",
    ERROR_PRO_USER_USAGE_LIMIT: "Pro tier usage limit reached",
    ERROR_USAGE_PRICING_REQUIRED: "Usage-based pricing required",
    ERROR_USAGE_PRICING_REQUIRED_CHANGEABLE: "Usage pricing required (changeable)"
};
```

## 26. gRPC Service Methods Summary

### aiserver.v1.AuthService Methods
| Method | Request | Response |
|--------|---------|----------|
| GetEmail | GetEmailRequest | GetEmailResponse |
| EmailValid | EmailValidRequest | EmailValidResponse |
| DownloadUpdate | DownloadUpdateRequest | DownloadUpdateResponse |
| MarkPrivacy | MarkPrivacyRequest | MarkPrivacyResponse |
| SwitchCmdKFraction | SwitchCmdKFractionRequest | SwitchCmdKFractionResponse |
| GetCustomerId | CustomerIdRequest | CustomerIdResponse |
| SetPrivacyMode | SetPrivacyModeRequest | SetPrivacyModeResponse |
| GetSessionToken | GetSessionTokenRequest | GetSessionTokenResponse |
| CheckSessionToken | CheckSessionTokenRequest | CheckSessionTokenResponse |
| ListActiveSessions | ListActiveSessionsRequest | ListActiveSessionsResponse |
| RevokeSession | RevokeSessionRequest | RevokeSessionResponse |
| ListJwtPublicKeys | ListJwtPublicKeysRequest | ListJwtPublicKeysResponse |

### agent.v1.ControlService Auth-Related Methods
| Method | Request | Response |
|--------|---------|----------|
| RefreshGithubAccessToken | RefreshGithubAccessTokenRequest | RefreshGithubAccessTokenResponse |
| GetMcpRefreshTokens | GetMcpRefreshTokensRequest | GetMcpRefreshTokensResponse |

---

## Recommendations for Further Investigation

1. **Token validation flow** - Investigate how tokens are validated server-side and what claims they contain
2. **SSO integration** - WorkOS SSO flow details (SignUpType WORKOS)
3. **Feature flags** - How capabilities are enabled/disabled based on membership
4. **Rate limiting** - How authentication ties into rate limiting schemas
5. **Bedrock IAM** - AWS Bedrock integration for enterprise authentication
6. **MCP OAuth PKCE** - Code verifier storage suggests PKCE flow implementation
7. **Service account scopes** - Full enumeration of available API key scopes
8. **GitHub installation permissions** - Team-level GitHub access control
