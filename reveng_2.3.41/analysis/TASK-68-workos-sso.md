# TASK-68: WorkOS SSO Integration Analysis

## Executive Summary

Analysis of Cursor IDE v2.3.41 reveals that **WorkOS is NOT directly used for SSO authentication**. The WorkOS reference found in the codebase is only a copyright notice for Radix UI Primitives (a UI component library created by WorkOS). Cursor uses its own proprietary authentication system with Auth0-style OAuth flows for enterprise SSO.

## WorkOS Reference - Clarification

The only WorkOS reference found (line 1171803):
```javascript
/*!
 * Portions of this file are based on code from radix-ui-primitives.
 * MIT Licensed, Copyright (c) 2022 WorkOS.
 *
 * Credits to the Radix UI team:
 * https://github.com/radix-ui/primitives/...
 */
```

This is purely a library attribution, not SSO integration.

## Actual Authentication Architecture

### Authentication Infrastructure

| Component | Production Value | Description |
|-----------|-----------------|-------------|
| Website URL | `https://cursor.com` | User-facing auth portal |
| Backend URL | `https://api2.cursor.sh` | Main API server |
| Auth Domain | `prod.authentication.cursor.sh` | Custom Auth0 tenant |
| Auth Client ID | `KbZUR41cY7W6zRSdpSUJ7I7mLYBKOCmB` | OAuth client identifier |
| Repo Backend | `https://repo42.cursor.sh` | Repository indexing service |
| Agent Backend | `https://agent.api5.cursor.sh` | Background agent service |

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    CURSOR AUTH FLOW                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. User clicks "Sign In"                                       │
│     │                                                           │
│     ▼                                                           │
│  2. Generate PKCE challenge (SHA-256)                           │
│     │  - Random 32-byte verifier                                │
│     │  - Base64URL encode                                       │
│     │  - Create challenge hash                                  │
│     ▼                                                           │
│  3. Open browser to /loginDeepControl                           │
│     │  URL: cursor.com/loginDeepControl?                        │
│     │       challenge={hash}&uuid={session}&mode={login|signup} │
│     ▼                                                           │
│  4. User authenticates via:                                     │
│     │  - Email/Password                                         │
│     │  - Google OAuth                                           │
│     │  - GitHub OAuth                                           │
│     │  - Enterprise SSO (if configured)                         │
│     ▼                                                           │
│  5. Poll /auth/poll endpoint (every 500ms, max 30 attempts)     │
│     │  GET api2.cursor.sh/auth/poll?uuid={}&verifier={}         │
│     ▼                                                           │
│  6. Receive tokens on successful auth                           │
│     │  - accessToken (JWT)                                      │
│     │  - refreshToken                                           │
│     │  - authId (user identifier)                               │
│     ▼                                                           │
│  7. Store tokens & refresh membership                           │
│     │  - cursorAuth/accessToken (storage)                       │
│     │  - cursorAuth/refreshToken (storage)                      │
│     │  - Fetch team membership info                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Token Storage Keys

```javascript
// Primary authentication tokens
"cursorAuth/accessToken"    // JWT access token
"cursorAuth/refreshToken"   // Refresh token for renewal

// Additional auth storage
"cursorAuth/openAIKey"      // User's own OpenAI API key
"cursorAuth/claudeKey"      // User's own Anthropic API key
"cursorAuth/googleKey"      // User's own Google AI key
"cursorAuth/teamId"         // Enterprise team identifier
```

## Enterprise Authentication (SSO)

### Membership Types

```javascript
// aa enum - Membership tier definitions
aa = {
    FREE: "free",
    PRO: "pro",
    PRO_PLUS: "pro_plus",
    ENTERPRISE: "enterprise",
    FREE_TRIAL: "free_trial",
    ULTRA: "ultra"
}
```

### Enterprise Team Structure

```javascript
// Team data model from aiserver.v1
Team = {
    id: number,                    // Team identifier
    name: string,                  // Team display name
    hasBilling: boolean,           // Has active billing
    seats: number,                 // Licensed seats
    isEnterprise: boolean,         // Enterprise tier flag
    bedrockIamRole: string | null, // AWS Bedrock integration
    role: TeamRole                 // User's role in team
}

// Y2 enum - Team roles
TeamRole = {
    UNSPECIFIED: 0,
    OWNER: 1,
    MEMBER: 2,
    FREE_OWNER: 3,
    REMOVED: 4
}
```

### Enterprise Detection Flow

```javascript
// refreshMembership() logic
async refreshMembership() {
    const teams = await this.getTeams();
    const hasBillableTeams = teams.some(t => t.hasBilling && t.seats > 0);

    if (hasBillableTeams) {
        // Store team IDs for API calls
        this.setTeamIds(teams.map(t => t.id));

        // Check enterprise status
        this.setIsEnterprise(teams.some(t =>
            t.hasBilling && t.seats > 0 && t.isEnterprise
        ));

        // Set membership type to ENTERPRISE
        this.storeMembershipType(aa.ENTERPRISE);

        // Handle AWS Bedrock IAM integration
        if (teams.some(t => t.bedrockIamRole)) {
            this.setHasBedrockIamRole(true);
            this.setBedrockState({
                useBedrock: false,
                region: "us-east-2",
                accessKey: "iam",
                secretKey: "iam"
            });
        }
    } else {
        // Fall back to individual subscription check
        const profile = await fetch('/auth/full_stripe_profile');
        // ...
    }
}
```

### Enterprise Provider Configuration

```javascript
// Enterprise auth provider switching
static providerId(config) {
    return config.getValue(`${completionsAdvancedSetting}.authProvider`)
        === enterpriseProviderId
        ? enterpriseProviderId
        : providerId;
}

// Enterprise detection from token
function detectEnterpriseFromSession(session) {
    return a === enterpriseProviderId ||
           session.account.label.includes("_");
}
```

## Enterprise Admin Settings

### Team Admin Settings Schema

```javascript
// aiserver.v1.GetTeamAdminSettingsResponse
TeamAdminSettings = {
    allowedModels: string[],          // Whitelist of AI models
    blockedModels: string[],          // Blacklist of AI models
    dotCursorProtection: boolean,     // .cursor rules protection
    browserFeatures: boolean,         // Browser tool access
    browserOriginAllowlist: string[], // Allowed browser origins
    allowedMcpConfiguration: {        // MCP server restrictions
        disableAll: boolean,
        allowedMcpServers: string[]
    }
}
```

### Admin Settings Service

```javascript
// AdminSettingsService - fetches and caches team policies
class AdminSettingsService {
    static STORAGE_KEY = "adminSettings.cached";

    async refresh() {
        const client = await this.cursorAuthenticationService.dashboardClient();
        const teams = await client.getTeams({});
        const team = teams.find(t => t.seats !== 0);

        if (team) {
            this.cached = await client.getTeamAdminSettings({
                teamId: team.id
            });
        }
    }

    isModelBlocked(modelName) {
        return this.cached.blockedModels.includes(modelName);
    }
}
```

## Privacy Mode (Enterprise Feature)

### Privacy Mode Levels

```javascript
// wh enum - Privacy mode granularity
PrivacyMode = {
    UNSPECIFIED: 0,
    NO_STORAGE: 1,                    // Maximum privacy
    USAGE_DATA_TRAINING_ALLOWED: 2,   // Allow usage data
    USAGE_CODEBASE_TRAINING_ALLOWED: 3 // Allow codebase training
}
```

### Enterprise Privacy Enforcement

```javascript
// Enterprise can force privacy mode on users
shouldHaveGhostModeFromEnterprise() {
    return this.isTeamsPrivacyModeOn();
    // Returns { privacyModeForced: boolean, privacyMode: PrivacyMode }
}

// Privacy mode determination
reactivePrivacyMode() {
    if (this.reactiveMembershipType() === aa.ENTERPRISE) {
        const enterpriseSettings = this.shouldHaveGhostModeFromEnterprise();
        if (enterpriseSettings.privacyModeForced) {
            return true; // Forced privacy mode
        }
        if (this.isTeamPrivacyModeFetched) {
            return false; // Team allows data storage
        }
    }
    return this.noStorageModeEnabledOrTooCloseToOnboarding();
}
```

### Privacy Mode User Settings

```javascript
// User privacy mode request
GetUserPrivacyModeResponse = {
    privacyMode: PrivacyMode,
    hoursRemainingInGracePeriod: number,  // Grace period countdown
    isEnforcedByTeam: boolean,            // Team override flag
    isNotMigratedToServerSourceOfTruth: boolean,
    partnerDataShare: boolean,
    hasAcknowledgedGracePeriodDisclaimer: boolean
}
```

## SSO Sign-In Methods

The codebase references these authentication methods (from Supabase integration):

```javascript
// p4a - Supported auth methods
authMethods = [
    "reauthenticate",
    "signInAnonymously",
    "signInWithOAuth",      // Google, GitHub
    "signInWithIdToken",    // Token-based
    "signInWithOtp",        // One-time password
    "signInWithPassword",   // Email/password
    "signInWithSSO",        // Enterprise SSO
    "signOut",
    "signUp",
    "verifyOtp"
]
```

### Known Auth Providers

```javascript
// jue enum - Authentication providers
AuthProvider = {
    UNKNOWN: "unknown",
    AUTH_0: "Auth_0",
    GOOGLE: "Google",
    GITHUB: "Github"
}
```

## Token Handling

### JWT Token Operations

```javascript
// Token parsing (Gst function)
function parseJwtPayload(token) {
    const payload = token.split('.')[1];
    return JSON.parse(atob(payload));
    // Returns: { exp: number, ... }
}

// Token refresh
async refreshAccessToken() {
    const refreshToken = this.storageService.get("cursorAuth/refreshToken");

    if (refreshToken) {
        const response = await fetch(`${backendUrl}/auth/refresh`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ refreshToken })
        });

        const result = await response.json();

        if (result.shouldLogout) {
            this.logout();
        } else {
            this.storeAccessRefreshToken(
                result.access_token,
                result.access_token
            );
        }
    }
}
```

### Authorization Headers

```javascript
// Standard auth header construction
headers: {
    Authorization: `Bearer ${accessToken}`,
    "x-cursor-privacy-mode": privacyModeHeader,
    "x-cursor-eligible-for-snippet-learning": eligibilityString,
    "x-client-key": clientKey,
    "x-cursor-version": productVersion
}
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/loginDeepControl` | GET | Browser auth redirect |
| `/auth/poll` | GET | Token polling |
| `/auth/refresh` | POST | Token refresh |
| `/auth/full_stripe_profile` | GET | Subscription info |
| `/auth/stripe_profile` | GET | Legacy subscription |
| `/api/auth/logout` | GET | Session termination |
| `/api/auth/connect-github` | GET | GitHub connection |

## AWS Bedrock Integration (Enterprise)

Enterprise teams can configure AWS Bedrock for private AI deployment:

```javascript
// Bedrock state from team configuration
bedrockState = {
    useBedrock: boolean,
    region: string,        // Default: "us-east-2"
    accessKey: string,     // "iam" for IAM role auth
    secretKey: string,     // "iam" for IAM role auth
    sessionToken?: string
}

// Detection
if (teams.some(t => t.bedrockIamRole !== null && t.bedrockIamRole !== "")) {
    this.setHasBedrockIamRole(true);
}
```

## Conclusions

1. **No Direct WorkOS Integration**: Cursor does not use WorkOS for SSO. The reference is only a library attribution.

2. **Custom Auth System**: Cursor uses a custom OAuth 2.0 + PKCE flow with their own auth domain (`prod.authentication.cursor.sh`).

3. **Enterprise SSO**: Enterprise SSO is handled through:
   - Team-based authentication via `/auth/poll`
   - Team membership detection via `getTeams()` API
   - Admin-enforced privacy settings

4. **Auth0-Compatible**: The auth infrastructure appears Auth0-compatible (client IDs, domains) but is self-hosted.

5. **Multi-Tier Privacy**: Enterprise admins can enforce privacy modes on team members.

## Related Tasks

- TASK-29: Authentication schemas analysis
- TASK-76: Privacy mode deep dive
- TASK-78: AWS Bedrock integration

## Source References

- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
  - Lines 182740-182900: Credentials configuration
  - Lines 440400-440800: CursorCredsService
  - Lines 890270-890370: Default account authentication
  - Lines 1097660-1098600: CursorAuthenticationService
