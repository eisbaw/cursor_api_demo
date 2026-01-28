# TASK-99: Privacy Mode Migration Flow Analysis

## Executive Summary

Cursor IDE 2.3.41 implements a sophisticated privacy mode migration system that transitions users from the legacy boolean `noStorageMode` to a granular enum-based `PrivacyMode` system. The migration involves client-side inference, server reconciliation, grace period handling, and backward compatibility preservation. Enterprise/team users have additional enforcement layers.

## Privacy Mode Enum Definition

**Source:** `workbench.desktop.main.js:269165-269166`

```javascript
// aiserver.v1.PrivacyMode enum (wh variable)
i[i.UNSPECIFIED = 0] = "UNSPECIFIED"
i[i.NO_STORAGE = 1] = "NO_STORAGE"       // Maximum privacy, no data storage
i[i.NO_TRAINING = 2] = "NO_TRAINING"     // No training, but allows storage
i[i.USAGE_DATA_TRAINING_ALLOWED = 3] = "USAGE_DATA_TRAINING_ALLOWED"  // Usage data for training
i[i.USAGE_CODEBASE_TRAINING_ALLOWED = 4] = "USAGE_CODEBASE_TRAINING_ALLOWED"  // Full training including code
```

**Privacy Mode Priority Ordering:**
```javascript
// a8t - priority map (higher = more permissive)
{
    [wh.NO_STORAGE]: 1,
    [wh.NO_TRAINING]: 2,
    [wh.USAGE_DATA_TRAINING_ALLOWED]: 3,
    [wh.USAGE_CODEBASE_TRAINING_ALLOWED]: 4
}
```

## Legacy Storage Format

### Legacy Storage Keys

| Key | Purpose | Scope |
|-----|---------|-------|
| `noStorageMode` | Boolean privacy toggle | Application persistent storage |
| `eligibleForSnippetLearning` | Codebase learning eligibility | Application persistent storage |
| `enoughTimeElapsedSinceOnboarding` | 24-hour waiting period flag | Application persistent storage |
| `selectedPrivacyForOnboarding` | Initial privacy choice | Application persistent storage |
| `onboardingDataPrivacyVersion` | Onboarding UI version (legacy/new/new2) | Application persistent storage |

### New Privacy Storage Keys

**Source:** `workbench.desktop.main.js:290762`

| Key | Variable | Purpose |
|-----|----------|---------|
| `cursorai/donotchange/privacyMode` | `a7r` | Simple boolean privacy mode backup |
| `cursorai/donotchange/newPrivacyMode2` | `o8t` | Serialized granular privacy mode (JSON) |
| `cursorai/donotchange/newPrivacyModeHoursRemainingInGracePeriod` | `Ips` | Grace period countdown |
| `cursorai/donotchange/partnerDataShare` | `Dps` | Partner data sharing consent |
| `cursorai/donotchange/hasReconciledNewPrivacyModeWithServerOnUpgrade` | `Rps` | Migration completion flag |

## Migration Flow

### 1. Legacy Value Inference

**Source:** `workbench.desktop.main.js:1098005-1098007`

```javascript
inferPrivacyModeFromLegacyValues = () => {
    const noStorageMode = this._reactiveStorageService
        .applicationUserPersistentStorage.noStorageMode;

    // If noStorageMode is explicitly true -> NO_STORAGE
    if (noStorageMode === true) return wh.NO_STORAGE;

    // If noStorageMode is undefined (never set) -> UNSPECIFIED (triggers migration)
    if (noStorageMode === undefined) return wh.UNSPECIFIED;

    // If noStorageMode is false AND eligible for snippet learning
    // AND enough time elapsed -> USAGE_CODEBASE_TRAINING_ALLOWED
    if (this._reactiveStorageService.applicationUserPersistentStorage.eligibleForSnippetLearning
        && this._reactiveStorageService.applicationUserPersistentStorage.enoughTimeElapsedSinceOnboarding === true) {
        return wh.USAGE_CODEBASE_TRAINING_ALLOWED;
    }

    // Otherwise -> USAGE_DATA_TRAINING_ALLOWED (basic usage data)
    return wh.USAGE_DATA_TRAINING_ALLOWED;
}
```

### 2. Server Reconciliation Flow

**Source:** `workbench.desktop.main.js:1097822-1097843`

```javascript
fetchUserPrivacyMode = async (requestContext) => {
    const dashboardClient = await this.dashboardClient();
    const inferredMode = this.inferPrivacyModeFromLegacyValues();

    // Send inferred mode to server
    const response = await dashboardClient.getUserPrivacyMode(
        new GetUserPrivacyModeRequest({ inferredPrivacyMode: inferredMode }),
        { headers: requestHeaders }
    );

    const serverMode = response.privacyMode;
    const gracePeriodHours = response.hoursRemainingInGracePeriod;
    const partnerDataShare = response.partnerDataShare;

    // Store partner data share setting
    this.storageService.store(Dps, partnerDataShare.toString(), -1, 0);
    this.storeHoursRemainingInGracePeriod(gracePeriodHours);

    // Check if already reconciled on previous upgrade
    if (this.storageService.get(Rps, -1, "false") === "true") {
        // Already reconciled - just accept server's value
        this.DANGEROUS_setUserPrivacyMode(serverMode);
        this.hasFetchedUserPrivacyMode = true;
        return;
    }

    // First-time reconciliation logic
    const localDefault = inferredMode === wh.UNSPECIFIED ? wh.NO_STORAGE : inferredMode;
    const serverDefault = serverMode === wh.UNSPECIFIED ? wh.NO_STORAGE : serverMode;

    // Use the MORE RESTRICTIVE setting (higher privacy)
    // Priority: a8t[Le] >= a8t[Re] means local is more permissive
    if (response.isEnforcedByTeam || a8t[localDefault] >= a8t[serverDefault]) {
        // Server is more restrictive OR team enforced - accept server
        this.DANGEROUS_setUserPrivacyMode(serverDefault);
        this.storageService.store(Rps, "true", -1, 0);  // Mark reconciled
        this.hasFetchedUserPrivacyMode = true;
    } else {
        // Local is more restrictive - push to server
        await this.updateUserPrivacyMode({
            privacyMode: localDefault,
            requestId: requestContext?.requestId
        });
    }
}
```

### 3. Privacy Mode Reconciliation on Startup

**Source:** `workbench.desktop.main.js:1098385-1098391`

```javascript
reconcilePrivacyMode() {
    try {
        // If the simple backup key shows privacy was enabled,
        // but current reactive state says it's not, force it on
        if (this.storageService.get(a7r, -1) === "true"
            && this.reactivePrivacyMode() !== true) {
            this._reactiveStorageService.setApplicationUserPersistentStorage("noStorageMode", true);
        }
    } catch (e) {
        console.error(e);
    }
}
```

### 4. Setting Privacy Mode (Backward Compatibility Write)

**Source:** `workbench.desktop.main.js:1097854-1097884`

When setting the new granular privacy mode, the code also updates legacy `noStorageMode`:

```javascript
DANGEROUS_setUserPrivacyMode = (privacyMode) => {
    // Enable background composer when transitioning FROM NO_STORAGE
    if (this.parsePrivacyModeFromStorage() === wh.NO_STORAGE
        && privacyMode !== wh.NO_STORAGE) {
        this.backgroundComposerDataService.setPersistentData("isBackgroundComposerEnabled", true);
    }

    // Write to new granular storage
    this.storageService.store(o8t, new PrivacyModeCacheInfo({
        privacyMode: privacyMode
    }).toJsonString(), -1, 0);

    // Backward compatibility: write to legacy noStorageMode
    try {
        switch (privacyMode) {
            case wh.NO_STORAGE:
            case wh.NO_TRAINING:
                this._reactiveStorageService.setApplicationUserPersistentStorage("noStorageMode", true);
                break;
            case wh.USAGE_DATA_TRAINING_ALLOWED:
                this._reactiveStorageService.setApplicationUserPersistentStorage("noStorageMode", false);
                break;
            case wh.USAGE_CODEBASE_TRAINING_ALLOWED:
                // Also enable snippet learning for full training
                this._reactiveStorageService.setApplicationUserPersistentStorage("eligibleForSnippetLearning", true);
                this._reactiveStorageService.setApplicationUserPersistentStorage("noStorageMode", false);
                break;
        }
    } catch (e) {
        console.error(e);
    }

    // Toggle version flag to trigger reactive updates
    const currentToggle = this._reactiveStorageService
        .applicationUserPersistentStorage.privacyModeVersionToggle ?? false;
    this._reactiveStorageService.setApplicationUserPersistentStorage(
        "privacyModeVersionToggle", !currentToggle
    );
}
```

## Grace Period System

### 24-Hour Onboarding Grace Period

**Source:** `workbench.desktop.main.js:1097993-1097997`

```javascript
// 864e5 = 86400000 milliseconds = 24 hours
hasEnoughTimeElapsedSinceOnboarding = () => {
    const elapsed = this.timeElapsedSinceOnboarding();
    return elapsed === undefined ? false : elapsed > 864e5;  // 24 hours
}

disableNoStorageModeIfEnoughTimePassedSinceOnboarding = () => {
    if (this.hasEnoughTimeElapsedSinceOnboarding()
        && this._reactiveStorageService.applicationUserPersistentStorage.eligibleForSnippetLearning) {
        this._reactiveStorageService.setApplicationUserPersistentStorage(
            "enoughTimeElapsedSinceOnboarding", true
        );
    }
}
```

### Server-Side Grace Period

**Source:** `workbench.desktop.main.js:282876`

The `GetUserPrivacyModeResponse` includes:
- `hoursRemainingInGracePeriod` - Server-controlled grace period countdown
- `hasAcknowledgedGracePeriodDisclaimer` - Whether user acknowledged the grace period notice

## Enterprise/Team Privacy Enforcement

### Team Privacy Mode Override

**Source:** `workbench.desktop.main.js:1098424-1098426`

```javascript
reactivePrivacyMode() {
    const localNoStorageMode = this.noStorageModeEnabledOrTooCloseToOnboarding();

    if (this.reactiveMembershipType() === aa.ENTERPRISE) {
        // Enterprise user - check team enforcement
        if (this.shouldHaveGhostModeFromEnterprise().privacyModeForced) {
            // Team forces privacy mode - update local storage and return true
            if (this.isTeamPrivacyModeFetched) {
                this._reactiveStorageService.setApplicationUserPersistentStorage("noStorageMode", true);
            }
            return true;
        }
        // Team doesn't force but we've fetched - return false (allow)
        if (this.isTeamPrivacyModeFetched) return false;
        // Haven't fetched yet - use local value
        return localNoStorageMode;
    }

    // Non-enterprise - use local value
    return localNoStorageMode;
}
```

### Team Migration Opt-Out

**Source:** `workbench.desktop.main.js:287533-287553`

Teams can opt out of privacy mode migration:

```javascript
// UpdateTeamPrivacyModeMigrationOptOutRequest
{
    teamId: number,       // Team identifier
    optOut: boolean       // Whether to opt out of migration
}
```

**API Endpoint:** `UpdateTeamPrivacyModeMigrationOptOut`

## Protobuf Schemas

### GetUserPrivacyModeRequest
```protobuf
message GetUserPrivacyModeRequest {
    PrivacyMode inferred_privacy_mode = 1;  // Client-inferred mode from legacy values
}
```

### GetUserPrivacyModeResponse
```protobuf
message GetUserPrivacyModeResponse {
    PrivacyMode privacy_mode = 1;           // Server's authoritative mode
    int32 hours_remaining_in_grace_period = 2;
    bool is_enforced_by_team = 3;           // Team overrides user choice
    bool is_not_migrated_to_server_source_of_truth = 4;  // Migration incomplete
    bool partner_data_share = 5;            // Partner data sharing consent
    bool has_acknowledged_grace_period_disclaimer = 6;
}
```

### SetUserPrivacyModeRequest
```protobuf
message SetUserPrivacyModeRequest {
    PrivacyMode privacy_mode = 1;
}
```

### NeedsPrivacyModeMigrationRequest/Response
```protobuf
message NeedsPrivacyModeMigrationRequest {
    // Empty - just checks if migration is needed
}

message NeedsPrivacyModeMigrationResponse {
    bool needs_migration = 1;
}
```

### GetTeamPrivacyModeForcedResponse
```protobuf
message GetTeamPrivacyModeForcedResponse {
    bool privacy_mode_forced = 1;
    PrivacyMode privacy_mode = 2;
    bool privacy_mode_migration_opted_out = 3;
}
```

## Onboarding Privacy Versions

**Source:** `workbench.desktop.main.js:1140355-1140358`

Three onboarding UI versions exist:
- `legacy` - Original privacy onboarding
- `new` - Updated privacy onboarding
- `new2` - Latest privacy onboarding (default for new users)

## State Machine

```
+------------------+
|    UNSPECIFIED   |  <-- User never set privacy preference
+--------+---------+
         |
         v
+--------+---------+     Migration Trigger
|  inferFromLegacy |  <-- Check noStorageMode, eligibleForSnippetLearning
+--------+---------+
         |
         v
+--------+---------+
|   Server Fetch   |  <-- getUserPrivacyMode with inferred value
+--------+---------+
         |
         +------------+--------------+
         |            |              |
         v            v              v
   Team Enforced   Local More    Server More
                   Restrictive   Restrictive
         |            |              |
         v            |              v
   Accept Server  Push to Server  Accept Server
         |            |              |
         +------------+--------------+
                      |
                      v
              +-------+-------+
              | Mark Reconciled|
              | (Rps = "true") |
              +---------------+
```

## Key Implementation Notes

1. **Privacy preference preservation**: During migration, the MORE RESTRICTIVE setting wins. If local has `NO_STORAGE` but server has `USAGE_DATA_TRAINING_ALLOWED`, the system keeps `NO_STORAGE` and pushes to server.

2. **Grace period**: New users have a 24-hour grace period before their privacy preferences take full effect. This allows time for them to understand and configure settings.

3. **Backward compatibility**: Every write to the new granular system also writes to the legacy `noStorageMode` boolean, ensuring older code paths continue to work.

4. **Enterprise override**: Team/enterprise settings can force privacy mode regardless of user preference. This is checked on every privacy mode read.

5. **Reactive storage**: Privacy mode changes trigger reactive updates via a version toggle (`privacyModeVersionToggle`) that flips on each change.

## Related Files

- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
  - Lines 269165-269179: PrivacyMode enum definition
  - Lines 282844-282915: GetUserPrivacyMode request/response
  - Lines 283085-283138: NeedsPrivacyModeMigration request/response
  - Lines 290759-290770: Storage key definitions and priority map
  - Lines 1097805-1098440: CursorAuthenticationService implementation

## Security Considerations

1. **Storage keys marked "donotchange"**: The prefix indicates these should not be modified by extensions or user scripts.

2. **DANGEROUS_setUserPrivacyMode naming**: The "DANGEROUS_" prefix warns developers that this method has significant side effects and should only be called through proper channels.

3. **Server as source of truth**: After initial migration, server values take precedence (unless team enforced), preventing local tampering.

## Investigation Suggestions

1. Team privacy mode enforcement logic is complex - may warrant deeper analysis
2. The interaction between `eligibleForSnippetLearning` and workspace-level settings
3. How the grace period disclaimer acknowledgment flows through the system
