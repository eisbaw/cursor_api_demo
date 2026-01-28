# TASK-76: Privacy Mode System and Team/Enterprise Overrides

Analysis of Cursor's privacy mode system and how team/enterprise administrators can override individual user privacy settings, particularly affecting Background Composer (Cloud Agents).

## Privacy Mode Enum Definition

**Source location**: Line 269165 in `workbench.desktop.main.js`

```javascript
// Privacy mode levels (ordered from most restrictive to least restrictive)
wh = {
  UNSPECIFIED: 0,        // Default/unknown state
  NO_STORAGE: 1,         // Most restrictive - no code storage, Background Agent disabled
  NO_TRAINING: 2,        // No training, but code may be stored for Background Agent
  USAGE_DATA_TRAINING_ALLOWED: 3,     // Usage data can be used for training
  USAGE_CODEBASE_TRAINING_ALLOWED: 4  // Full data sharing including codebase
}
```

### Priority Ranking (a8t)

**Source location**: Line 290762 in `workbench.desktop.main.js`

```javascript
a8t = {
  [wh.NO_STORAGE]: 1,                    // Priority 1 (most restrictive wins)
  [wh.NO_TRAINING]: 2,                   // Priority 2
  [wh.USAGE_DATA_TRAINING_ALLOWED]: 3,   // Priority 3
  [wh.USAGE_CODEBASE_TRAINING_ALLOWED]: 4 // Priority 4 (least restrictive)
}
```

The lower the priority number, the more restrictive the mode. When multiple teams set different privacy modes, **the most restrictive (lowest number) wins**.

## HTTP Headers for Privacy Mode

**Source location**: Line 268959 in `workbench.desktop.main.js`

```javascript
sJe = "x-ghost-mode"           // Header name for privacy mode
rJe = "x-new-onboarding-completed"  // Header for onboarding status
```

The `nJe()` function converts privacy mode to header values:
```javascript
function nJe(i) {
  if (i === true) return "true";
  if (i === false) return "false";
  if (i === undefined) return "implicit-false";
  return "true";  // For any other value (including enum values)
}
```

## Team/Enterprise Override Mechanism

### Team Privacy Mode Fetch (Source: Line 1098305-1098354)

When a user belongs to one or more teams, the client fetches privacy mode settings for **all teams** and applies the **most restrictive** setting:

```javascript
// For each team, fetch privacy settings
await Promise.allSettled(teamIds.map(async teamId =>
  await dashboardClient.getTeamPrivacyModeForced({
    teamId: teamId
  })
));

// Aggregate logic - most restrictive wins
pe.forEach(({ value: Re }) => {
  if (Re.privacyMode !== wh.UNSPECIFIED &&
      (Le.privacyMode === wh.UNSPECIFIED ||
       a8t[Re.privacyMode] < a8t[Le.privacyMode])) {
    Le.privacyMode = Re.privacyMode;
    Le.privacyModeForced = Re.privacyModeForced;
  }
});

// Force flag for restrictive modes
if (Le.privacyMode === wh.NO_STORAGE ||
    Le.privacyMode === wh.NO_TRAINING ||
    Le.privacyMode === wh.UNSPECIFIED) {
  Le.privacyModeForced = true;
}
```

### User Privacy Mode Reconciliation (Source: Line 1097822-1097843)

When team enforcement is active, individual user preferences are overridden:

```javascript
// If team enforces privacy OR user's current mode is already equal/more restrictive
if (ne.isEnforcedByTeam || a8t[userCurrentMode] >= a8t[serverMode]) {
  this.DANGEROUS_setUserPrivacyMode(serverMode);
} else {
  // User can potentially keep more restrictive setting
  await this.updateUserPrivacyMode({ privacyMode: userCurrentMode });
}
```

### Enterprise Override Logic (Source: Line 1098424-1098429)

For enterprise membership, the client checks team settings first:

```javascript
reactivePrivacyMode() {
  const e = this.noStorageModeEnabledOrTooCloseToOnboarding();

  if (this.reactiveMembershipType() === aa.ENTERPRISE) {
    // If team forces privacy mode, use it
    if (this.shouldHaveGhostModeFromEnterprise().privacyModeForced) {
      // Force noStorageMode in local storage
      this._reactiveStorageService.setApplicationUserPersistentStorage("noStorageMode", true);
      return true;  // Privacy mode enabled
    }
    // If team settings fetched and not forced, user has freedom
    if (this.isTeamPrivacyModeFetched) {
      return false;
    }
    // Fall back to user's local setting while fetching
    return e;
  }
  return e;  // Non-enterprise users use their own settings
}
```

## Impact on Background Composer (Cloud Agents)

### Background Composer Enablement (Source: Line 1098960-1098976)

```javascript
isBackgroundComposerEnabled() {
  switch (this.granularPrivacyModeRawEnum()) {
    case wh.USAGE_DATA_TRAINING_ALLOWED:
    case wh.USAGE_CODEBASE_TRAINING_ALLOWED:
    case wh.NO_TRAINING:
      return true;   // Background Agent available
    case wh.NO_STORAGE:
    case wh.UNSPECIFIED:
    default:
      return false;  // Background Agent disabled
  }
}
```

**Key insight**: `NO_TRAINING` mode allows Background Agent because it permits code storage (just not training). Only `NO_STORAGE` (Legacy Privacy Mode) disables it.

### UI Behavior for Blocked Users (Source: Line 842957-842993)

When Background Composer is disabled due to privacy settings, the UI shows contextual messages:

```javascript
if (!n.isBackgroundComposerEnabled()) {
  const isTeamEnforced = n.getTeamId() !== undefined ?
    n.shouldHaveGhostModeFromEnterprise().privacyModeForced : false;

  // Check if user is team admin
  const isTeamAdmin = (await dashboardClient.getTeams({}))
    .teams.some(t => t.seats > 0 &&
      (t.role === Y2.OWNER || t.role === Y2.FREE_OWNER));

  if (isTeamEnforced) {
    if (isTeamAdmin) {
      // Admin can configure privacy settings
      message = "...currently disabled in your team's privacy settings.";
      button = "Configure Privacy Settings";
    } else {
      // Non-admin must contact admin
      message = "...disabled by your team administrator. Please contact your admin...";
      button = "OK";
    }
  } else {
    // Individual user can change their own settings
    message = "...disabled in your privacy settings. Please update...";
    button = "Open Settings";
  }
}
```

## gRPC API Endpoints

### Team Privacy Mode Endpoints (Source: Line 719277-719284)

```javascript
// Dashboard service endpoints for team privacy
getTeamPrivacyModeForced: {
  name: "GetTeamPrivacyModeForced",
  // Request: GetTeamPrivacyModeForcedRequest { teamId }
  // Response: GetTeamPrivacyModeForcedResponse { privacyModeForced, privacyMode, privacyModeMigrationOptedOut }
}

switchTeamPrivacyMode: {
  name: "SwitchTeamPrivacyMode",
  // Request: SwitchTeamPrivacyModeRequest { teamId, privacyModeForced, privacyMode }
  // Response: SwitchTeamPrivacyModeResponse {}
}
```

### User Privacy Mode Endpoints (Source: Line 719847-719878)

```javascript
getUserPrivacyMode: {
  name: "GetUserPrivacyMode",
  // Request: GetUserPrivacyModeRequest { inferredPrivacyMode }
  // Response: GetUserPrivacyModeResponse {
  //   privacyMode, hoursRemainingInGracePeriod, isEnforcedByTeam,
  //   isNotMigratedToServerSourceOfTruth, partnerDataShare,
  //   hasAcknowledgedGracePeriodDisclaimer
  // }
}

setUserPrivacyMode: {
  name: "SetUserPrivacyMode",
  // Request: SetUserPrivacyModeRequest { privacyMode }
  // Response: SetUserPrivacyModeResponse {}
}

skipPrivacyModeGracePeriod: {
  name: "SkipPrivacyModeGracePeriod",
  // Allows users to skip the grace period before sharing starts
}

needsPrivacyModeMigration: {
  name: "NeedsPrivacyModeMigration",
  // Checks if user needs to migrate from legacy privacy settings
}
```

## Privacy Mode UI Options

**Source location**: Line 905709-905842 in `workbench.desktop.main.js`

### Available Modes in Settings UI

1. **Share Data** (`USAGE_DATA_TRAINING_ALLOWED` or `USAGE_CODEBASE_TRAINING_ALLOWED`)
   - Usage data stored and used for training
   - Background Agent available

2. **Privacy Mode** (`NO_TRAINING`)
   - No training, but code may be stored
   - Background Agent and other features available

3. **Privacy Mode (Legacy)** (`NO_STORAGE`)
   - No training and no storage
   - Background Agent and storage-dependent features disabled

### Enterprise-Controlled UI

When team admin controls privacy, the UI shows "Controlled by Admin, cannot change":
```javascript
if (membershipType === aa.ENTERPRISE) {
  switch (teamPrivacyMode) {
    case wh.NO_STORAGE:
    case wh.NO_TRAINING:
      return [{ id: "...", label: "Privacy Mode", jsx: "Controlled by Admin" }];
    case wh.USAGE_CODEBASE_TRAINING_ALLOWED:
    case wh.USAGE_DATA_TRAINING_ALLOWED:
      return [{ id: "...", label: "Share Data", jsx: "Controlled by Admin" }];
  }
}
```

## Metrics and Telemetry Integration

Privacy mode status is included in metrics tags:

```javascript
// Source: Line 893842
tags.push(`privacy_mode:${this._privacyModeEnabled}`);
tags.push(`is_background_composer:${this.isBackgroundComposer}`);

// Source: Line 893853
metrics.privacy_mode = String(this._privacyModeEnabled);
```

The metrics service respects privacy mode settings:
```javascript
// Source: Line 893859
isEnabled() {
  if (!this._metricsConfig) return true;
  return this._privacyModeEnabled ?
    this._metricsConfig.enabledInPrivacyMode === true :
    this._metricsConfig.enabledInNonPrivacyMode === true;
}
```

## Storage Keys

**Source location**: Line 290759-290769 in `workbench.desktop.main.js`

```javascript
// Legacy privacy mode key
a7r = "cursorai/donotchange/privacyMode"

// New granular privacy mode
o8t = "cursorai/donotchange/newPrivacyMode2"

// Grace period tracking
Ips = "cursorai/donotchange/newPrivacyModeHoursRemainingInGracePeriod"

// Partner data sharing
Dps = "cursorai/donotchange/partnerDataShare"

// Migration reconciliation flag
Rps = "cursorai/donotchange/hasReconciledNewPrivacyModeWithServerOnUpgrade"
```

## Grace Period System

**Source location**: Line 1097819-1097821 in `workbench.desktop.main.js`

New users have a grace period before data sharing begins:
```javascript
hoursRemainingInNewPrivacyModeGracePeriod = () => {
  const value = this.storageService.get(Ips, -1);
  return value !== null ? Number(value) : 0;
}
```

The server returns `hoursRemainingInGracePeriod` in the `GetUserPrivacyModeResponse`.

## Summary

1. **Team admins can enforce privacy mode** for all team members via `SwitchTeamPrivacyMode`
2. **Most restrictive wins** when user belongs to multiple teams
3. **Enterprise users** have their settings determined by `shouldHaveGhostModeFromEnterprise()`
4. **Background Composer requires** `NO_TRAINING` or less restrictive mode (not `NO_STORAGE`)
5. **Privacy mode affects**:
   - Background Agent availability
   - Data storage capabilities
   - Training data collection
   - Partner data sharing
   - Metrics collection
6. **The `x-ghost-mode` header** is sent with all API requests to indicate privacy status
