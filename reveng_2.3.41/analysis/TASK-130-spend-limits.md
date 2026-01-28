# TASK-130: Spend Limit Configuration and Usage-Based Billing Schemas

## Overview

Cursor implements a comprehensive spend limit and usage-based billing system that tracks user consumption, enforces budget limits, and provides UI for configuring spending caps. The system operates at multiple levels: individual users, teams, service accounts, and billing groups.

## Core Protobuf Schemas

### 1. GetHardLimitRequest/Response (aiserver.v1)

The primary endpoint for retrieving current hard limit configuration:

```protobuf
message GetHardLimitRequest {
  optional int32 team_id = 1;
}

message GetHardLimitResponse {
  int32 hard_limit = 1;                          // Hard limit in cents/dollars
  bool no_usage_based_allowed = 2;               // Whether usage-based pricing is disabled
  optional int32 hard_limit_per_user = 3;        // Per-user limit (for teams)
  int32 per_user_monthly_limit_dollars = 4;      // Monthly limit per user
  bool is_dynamic_team_limit = 5;                // Whether team limit is dynamic
}
```

**Source location**: Lines 272149-272223 in workbench.desktop.main.js

### 2. SetHardLimitRequest/Response (aiserver.v1)

Endpoint for configuring spend limits:

```protobuf
message SetHardLimitRequest {
  optional int32 team_id = 1;
  int32 hard_limit = 2;                          // New hard limit
  bool no_usage_based_allowed = 3;               // Disable usage-based pricing
  optional int32 hard_limit_per_user = 4;        // Per-user limit
  bool preserve_hard_limit_per_user = 5;         // Keep existing per-user limit
  int32 per_user_monthly_limit_dollars = 6;      // Monthly user limit in dollars
  bool clear_per_user_monthly_limit_dollars = 7; // Clear monthly limit
  bool is_dynamic_team_limit = 8;                // Enable dynamic limits
}

message SetHardLimitResponse {
  // Empty response
}
```

**Source location**: Lines 272225-272304 in workbench.desktop.main.js

### 3. GetCurrentPeriodUsageRequest/Response (aiserver.v1)

Main endpoint for fetching current billing period usage data:

```protobuf
message GetCurrentPeriodUsageRequest {
  // Empty request
}

message GetCurrentPeriodUsageResponse {
  int64 billing_cycle_start = 1;
  int64 billing_cycle_end = 2;
  PlanUsage plan_usage = 3;
  SpendLimitUsage spend_limit_usage = 4;
  optional int32 display_threshold = 5;       // Percentage threshold for showing usage
  bool enabled = 6;
  string display_message = 7;
  optional string auto_model_selected_display_message = 8;
  optional string named_model_selected_display_message = 9;
  FreeBestOfNPromotion free_best_of_n_promotion = 10;
}

message PlanUsage {
  int32 total_spend = 1;        // Total spend in cents
  int32 included_spend = 2;      // Included spend in plan
  int32 bonus_spend = 3;         // Bonus/promotional spend
  int32 limit = 4;               // Plan limit in cents
  optional int32 auto_spend = 5; // Agent (Auto) spend
  optional int32 api_spend = 6;  // API spend
  optional bool remaining_bonus = 7;
  optional string bonus_tooltip = 8;
  optional int32 auto_percent_used = 9;
  optional int32 api_percent_used = 10;
  optional int32 total_percent_used = 11;
}

message SpendLimitUsage {
  int32 total_spend = 1;
  int32 individual_used = 2;
  int32 individual_remaining = 3;
  optional int32 individual_limit = 4;
  optional int32 total_used = 5;
  optional int32 total_remaining = 6;
  optional int32 total_limit = 7;
  string limit_type = 8;          // "team", "user-team", etc.
}
```

**Source location**: Lines 278284-278542 in workbench.desktop.main.js

### 4. ConfigureSpendLimitAction (aiserver.v1)

Action schema for configuring spend limits from chat/UI:

```protobuf
message ConfigureSpendLimitAction {
  string confirm_label = 1;
  // Part of ErrorAction oneof
}
```

This action is used in error response handling to prompt users to configure spend limits when they hit rate/usage limits.

**Source location**: Lines 93220-93230, 230556-230566 in workbench.desktop.main.js

### 5. Service Account Spend Limits (aiserver.v1)

Dedicated schemas for service account spending:

```protobuf
message GetServiceAccountSpendLimitRequest {
  int32 team_id = 1;
  string service_type = 2;
}

message GetServiceAccountSpendLimitResponse {
  optional int32 spend_limit_cents = 1;
  optional bool is_default = 2;
}

message SetServiceAccountSpendLimitRequest {
  int32 team_id = 1;
  string service_type = 2;
  int32 spend_limit_cents = 3;
}

message SetServiceAccountSpendLimitResponse {
  bool success = 1;
}
```

**Source location**: Lines 283328-283464 in workbench.desktop.main.js

## Usage-Based Billing Schemas

### UsageEventKind Enum (aiserver.v1)

Categorizes usage events for billing:

```protobuf
enum UsageEventKind {
  USAGE_EVENT_KIND_UNSPECIFIED = 0;
  USAGE_EVENT_KIND_USAGE_BASED = 1;      // Pay-as-you-go usage
  USAGE_EVENT_KIND_USER_API_KEY = 2;     // User's own API key
  USAGE_EVENT_KIND_INCLUDED_IN_PRO = 3;  // Included in Pro plan
  USAGE_EVENT_KIND_INCLUDED_IN_PLUS = 4; // Included in Plus plan
  USAGE_EVENT_KIND_BUGBOT = 5;           // BugBot feature usage
  USAGE_EVENT_KIND_ULTRA_REQUESTS = 6;   // Ultra tier requests
  USAGE_EVENT_KIND_INCLUDED_IN_BUSINESS = 7;
  USAGE_EVENT_KIND_MAX = 8;
  USAGE_EVENT_KIND_INCLUDED_IN_ULTRA = 9;
  USAGE_EVENT_KIND_FREE_CREDIT = 10;     // Free promotional credits
}
```

**Source location**: Lines 156250-156288, 526346-526385 in workbench.desktop.main.js

### UsageEventDetails (aiserver.v1)

Detailed tracking of specific usage events:

```protobuf
message UsageEventDetails {
  oneof feature {
    BugFinderTriggerV1 bug_finder_trigger_v1 = 1;
    BugBot bug_bot = 2;
    Chat chat = 3;
    FastApply fast_apply = 4;
    Composer composer = 5;
    ToolCallComposer tool_call_composer = 6;
    WarmComposer warm_composer = 7;
    ContextChat context_chat = 8;
    CmdK cmd_k = 9;
    TerminalCmdK terminal_cmd_k = 10;
    AiReviewAcceptedComment ai_review_accepted_comment = 11;
  }
}

message Chat {
  string model_name = 1;
  TokenUsage token_usage = 2;
}

message Composer {
  string model_name = 1;
  // ... additional fields
  TokenUsage token_usage = 5;
}
```

**Source location**: Lines 156296-156914 in workbench.desktop.main.js

### TokenUsage (aiserver.v1)

Tracks token consumption for cost calculation:

```protobuf
message TokenUsage {
  int32 input_tokens = 1;
  int32 output_tokens = 2;
  int32 cache_write_tokens = 3;
  int32 cache_read_tokens = 4;
  int32 total_cents = 5;           // Cost in cents
}
```

**Source location**: Lines 157217-157260 in workbench.desktop.main.js

### CheckUsageBasedPriceRequest/Response (aiserver.v1)

Pre-flight check for usage-based pricing:

```protobuf
message CheckUsageBasedPriceRequest {
  UsageEventDetails usage_event_details = 1;
}

message CheckUsageBasedPriceResponse {
  string markdown_response = 1;   // Human-readable price estimate
  string price_id = 2;            // Price identifier
}
```

**Source location**: Lines 168783-168850, 538508-538560 in workbench.desktop.main.js

## Billing Cycle Management

### GetCurrentBillingCycleRequest/Response (aiserver.v1)

```protobuf
message GetCurrentBillingCycleRequest {
  // Empty
}

message GetCurrentBillingCycleResponse {
  int64 billing_cycle_start = 1;
  int64 billing_cycle_end = 2;
  bool enabled = 3;
  string display_message = 4;
}
```

**Source location**: Lines 279414-279505 in workbench.desktop.main.js

### GetMonthlyBillingCycleRequest/Response (aiserver.v1)

```protobuf
message GetMonthlyBillingCycleRequest {
  // Empty
}

message GetMonthlyBillingCycleResponse {
  // Similar to CurrentBillingCycle
}
```

**Source location**: Lines 279474-279535 in workbench.desktop.main.js

## Team Credit Management

### TeamCreditsService (aiserver.v1.TeamCreditsService)

Service for managing team credits:

```protobuf
service TeamCreditsService {
  rpc GetTeamCredits(GetTeamCreditsRequest) returns (GetTeamCreditsResponse);
  rpc SetTeamCredits(SetTeamCreditsRequest) returns (SetTeamCreditsResponse);
  rpc ClearTeamCredits(ClearTeamCreditsRequest) returns (ClearTeamCreditsResponse);
}

message GetTeamCreditsRequest {
  int32 team_id = 1;
}

message GetTeamCreditsResponse {
  optional int32 credit_dollars = 1;
  optional bool credits_set = 2;
  optional bool credits_active = 3;
  optional int32 config_credit_dollars = 4;
}

message SetTeamCreditsRequest {
  int32 team_id = 1;
  int32 credit_dollars = 2;
}
```

**Source location**: Lines 827965-828194 in workbench.desktop.main.js

## Scenario Types for Limit Enforcement

### ScenarioType Enum (aiserver.v1)

Defines different limit enforcement scenarios:

```protobuf
enum ScenarioType {
  SCENARIO_TYPE_UNSPECIFIED = 0;
  SCENARIO_TYPE_PLAN_LIMIT = 1;           // Plan's included limit
  SCENARIO_TYPE_TIER_1_LIMIT = 2;         // Tier 1 usage limit
  SCENARIO_TYPE_TIER_2_LIMIT = 3;         // Tier 2 usage limit
  SCENARIO_TYPE_TIER_3_LIMIT = 4;         // Tier 3 usage limit
  SCENARIO_TYPE_ON_DEMAND_LIMIT = 5;      // Individual on-demand limit
  SCENARIO_TYPE_TEAM_ON_DEMAND_LIMIT = 6; // Team's on-demand limit
  SCENARIO_TYPE_MONTHLY_LIMIT = 7;        // Monthly spending limit
  SCENARIO_TYPE_POOLED_LIMIT = 8;         // Pooled/shared limit
}
```

**Source location**: Lines 829355-829385 in workbench.desktop.main.js

## Usage Status Service

### GetUsageLimitPolicyStatusResponse (aiserver.v1)

Returns current usage limit status:

```protobuf
message GetUsageLimitPolicyStatusResponse {
  bool is_in_slow_pool = 1;                    // In degraded service queue
  optional string error_title = 2;
  optional string error_detail = 3;
  optional int32 slowness_ms = 4;
  map<string, bool> features = 5;              // Feature flags
  bool can_configure_spend_limit = 6;          // User can change limit
  optional string limit_type = 7;              // "team", "user-team", etc.
  bool has_pending_request = 8;
  repeated string allowed_model_ids = 9;
  repeated string allowed_model_tags = 10;
}
```

**Source location**: Lines 278774-278850 in workbench.desktop.main.js

## Client-Side Usage Data Service

The `UsageDataService` (Evs class) manages usage data on the client:

```javascript
class UsageDataService {
    refreshInterval = 300 * 1000;      // 5 minutes
    retryInterval = 1800 * 1000;       // 30 minutes on error
    CACHE_DURATION = 30 * 1000;        // 30 seconds cache
    PLAN_INFO_CACHE_DURATION = 30 * 1000;

    // Reactive state
    planUsageData;
    spendLimitUsageData;
    displayMessageData;
    usageDisplayEnabledData;

    async refetch() {
        const response = await dashboardClient.getCurrentPeriodUsage();

        // Process plan usage
        if (response.planUsage && response.planUsage.limit > 0) {
            const total = response.planUsage.totalSpend / 100;
            const included = response.planUsage.includedSpend / 100;
            const bonus = response.planUsage.bonusSpend / 100;
            const limit = response.planUsage.limit / 100;
            const autoUsed = response.planUsage.autoSpend / 100;
            const apiUsed = response.planUsage.apiSpend / 100;
            // ...
        }

        // Process spend limit usage
        if (response.spendLimitUsage) {
            const used = response.spendLimitUsage.individualUsed / 100;
            const limit = (response.spendLimitUsage.individualLimit ?? 0) / 100;
            const percentage = limit > 0 ? Math.min(used / limit * 100, 100) : 0;
            // ...
        }
    }
}
```

**Source location**: Lines 299015-299250 in workbench.desktop.main.js

## Spend Limit UI Configuration

### Default Spend Limit Options

The UI provides predefined spend limit options based on membership tier:

```javascript
const ndo = {
    [MembershipType.PRO]: [0, 20, 50, 100],        // $0, $20, $50, $100 above current
    [MembershipType.ENTERPRISE]: [0, 50, 100, 200] // Enterprise has higher defaults
};

// If spendLimitOptions not provided, calculate based on current limit
const options = () => {
    const current = hardLimit();
    if (current === "loading") return [];
    const tier = membershipType();
    return ndo[tier].map(h => `$${h + current}`);
};
```

**Source location**: Lines 704900-704938 in workbench.desktop.main.js

### Setting Hard Limits

```javascript
async function setHardLimit(composerId, bubbleId, selectedLimit, context) {
    const amount = selectedLimit.replace(/[$,]/g, "");
    const hardLimit = amount === "0" ? "no-usage-based" : parseInt(amount);

    const client = await dashboardClient();
    const teamIds = membershipType === ENTERPRISE
        ? storage.aiSettings.teamIds
        : [];

    await client.setHardLimit({
        teamId: teamIds?.at(0),
        hardLimit: hardLimit === "no-usage-based" ? undefined : hardLimit,
        noUsageBasedAllowed: hardLimit === "no-usage-based",
        preserveHardLimitPerUser: true
    });

    notificationService.info("Spend limit set successfully!");
}
```

**Source location**: Lines 704807-704834 in workbench.desktop.main.js

### Per-User Spend Limits (Teams)

```javascript
async function setPerUserSpendLimit(composerId, bubbleId, selectedLimit, context) {
    const client = await dashboardClient();
    const teamId = storage.aiSettings.teamIds?.at(0);

    // Get current hard limit
    const current = await client.getHardLimit({ teamId });

    await client.setHardLimit({
        teamId: teamId,
        hardLimit: current.hardLimit ?? undefined,
        noUsageBasedAllowed: false,
        hardLimitPerUser: parsedAmount,
        preserveHardLimitPerUser: false
    });

    notificationService.info("Per-user spend limit set successfully!");
}
```

**Source location**: Lines 704843-704891 in workbench.desktop.main.js

## Usage-Based Pricing Modal

### Modal Display Trigger

The usage-based pricing modal is shown via the UI overlay service:

```javascript
// Show modal with usage event details
uiOverlayService.showUsageBasedPricingModal(usageEventDetails);

// Or show modal for configuration only
uiOverlayService.showUsageBasedPricingModal("justshow");

// Close modal
uiOverlayService.closeUsageBasedPricingModal();
```

**Source location**: Lines 79669-79674, 1152803 in workbench.desktop.main.js

### Modal Configuration UI

The modal allows toggling usage-based pricing and setting hard limits:

```javascript
function UsageBasedPricingModal(props) {
    const [hardLimit, setHardLimit] = useState();      // "no-usage-based" | number
    const [hardLimitInput, setHardLimitInput] = useState("");
    const [premiumRequestsEnabled, setPremiumRequestsEnabled] = useState();

    // Toggle usage-based pricing on/off
    const toggleUsageBased = async () => {
        const newLimit = hardLimit === "no-usage-based" ? "$50" : "$0";
        await setHardLimitApi(newLimit);
    };

    // Save custom hard limit
    const saveHardLimit = async (value) => {
        const parsed = value === "0" ? "no-usage-based" : parseInt(value);
        await client.setHardLimit({
            hardLimit: parsed === "no-usage-based" ? undefined : parsed,
            noUsageBasedAllowed: parsed === "no-usage-based",
            preserveHardLimitPerUser: true
        });
    };

    return (
        <>
            <Toggle
                title="Enable usage-based pricing"
                value={typeof hardLimit === "number"}
                onToggle={toggleUsageBased}
            />
            {typeof hardLimit === "number" && (
                <>
                    <Toggle
                        title="Enable usage-based pricing for premium models"
                        value={premiumRequestsEnabled}
                        onToggle={togglePremiumRequests}
                    />
                    <Input
                        placeholder="Enter usage-based spend limit"
                        value={hardLimitInput}
                        onChange={setHardLimitInput}
                    />
                    <Button title="Save" onClick={() => saveHardLimit(hardLimitInput)} />
                </>
            )}
        </>
    );
}
```

**Source location**: Lines 1157757-1158700 in workbench.desktop.main.js

## Slow Pool Enforcement

When users exceed their limits, they're moved to a "slow pool":

```javascript
const isInSlowPool = computed(() => {
    const status = usageLimitStatus();
    return status !== null && status.isInSlowPool === true;
});

// UI messaging for slow pool users
const errorTitle = computed(() => {
    const status = usageLimitStatus();
    if (status?.errorTitle) return status.errorTitle;
    if (!status?.errorTitle && !status?.errorDetail && status?.isInSlowPool) {
        return "Increase limits for faster responses";
    }
    return "";
});

const errorDetail = computed(() => {
    const status = usageLimitStatus();
    if (status?.errorDetail) return status.errorDetail;
    if (!status?.errorTitle && !status?.errorDetail && status?.isInSlowPool) {
        return "You're over your current usage limit and your requests are being processed with Auto in the slow queue.";
    }
    return "";
});
```

**Source location**: Lines 715925-716013 in workbench.desktop.main.js

## Display Threshold Configuration

The `displayThreshold` field controls when usage indicators appear:

```javascript
// Usage bar only shows when usage exceeds threshold (default 50%)
const shouldShowUsage = computed(() => {
    const displayMode = props.displayMode ?? "auto";
    if (displayMode === "never" || usageDisplayEnabled === false) return false;
    if (displayMode === "always") return planUsage !== null;

    const plan = planUsage;
    const spend = spendLimitUsage;
    if (!plan) return false;

    const combinedLimit = plan.limit + (spend?.limit ?? 0);
    const combinedUsed = plan.used + (spend?.limit > 0 ? spend?.used ?? 0 : 0);
    const percentage = combinedLimit > 0
        ? Math.min(combinedUsed / combinedLimit * 100, 100)
        : plan.usedPercentage;

    return percentage >= (plan.displayThreshold ?? 50);
});
```

**Source location**: Lines 753622-753634 in workbench.desktop.main.js

## Related gRPC Service Methods

### DashboardService Methods

```protobuf
service DashboardService {
  rpc GetHardLimit(GetHardLimitRequest) returns (GetHardLimitResponse);
  rpc SetHardLimit(SetHardLimitRequest) returns (SetHardLimitResponse);
  rpc GetCurrentBillingCycle(GetCurrentBillingCycleRequest) returns (GetCurrentBillingCycleResponse);
  rpc GetMonthlyBillingCycle(GetMonthlyBillingCycleRequest) returns (GetMonthlyBillingCycleResponse);
  rpc GetUsageBasedPremiumRequests(GetUsageBasedPremiumRequestsRequest) returns (GetUsageBasedPremiumRequestsResponse);
  rpc SetUsageBasedPremiumRequests(SetUsageBasedPremiumRequestsRequest) returns (SetUsageBasedPremiumRequestsResponse);
  rpc SetUserMonthlyLimit(SetUserMonthlyLimitRequest) returns (SetUserMonthlyLimitResponse);
  rpc GetServiceAccountSpendLimit(GetServiceAccountSpendLimitRequest) returns (GetServiceAccountSpendLimitResponse);
  rpc SetServiceAccountSpendLimit(SetServiceAccountSpendLimitRequest) returns (SetServiceAccountSpendLimitResponse);
  rpc SetUserHardLimit(...) returns (...);
}
```

**Source location**: Lines 719344-719970 in workbench.desktop.main.js

## Team Admin Configuration

### Team Settings Permissions

```protobuf
message TeamSettingsResponse {
  // ... many fields
  bool dashboard_analytics_requires_admin = 23;
  bool individual_spend_limits_blocked = 24;  // Admin can block individual limits
}
```

When `individual_spend_limits_blocked` is true, individual team members cannot configure their own spend limits.

**Source location**: Lines 272381-272515 in workbench.desktop.main.js

### Directory Group Limits

For enterprise teams using directory groups:

```protobuf
message DirectoryGroup {
  int32 directory_group_id = 1;
  // ...
  int32 per_user_monthly_limit_dollars = 4;
}
```

**Source location**: Lines 285705-285736 in workbench.desktop.main.js

## Error Handling for Billing

### Usage Pricing Required Error

When usage-based pricing is required but not configured:

```javascript
case fu.USAGE_PRICING_REQUIRED_CHANGEABLE:
case "ERROR_USAGE_PRICING_REQUIRED_CHANGEABLE":
    return details?.title ?? "Set up usage billing for premium models";
```

**Source location**: Lines 705058-705062 in workbench.desktop.main.js

### Configuring Spend Limit from Error Dialog

```javascript
case "configureSpendLimit":
    const isConfiguring = configureInProgress();
    const onClick = async () => {
        if (!configureInProgress()) {
            setConfigureInProgress(true);
            const limit = selectedLimit() === "Custom"
                ? customValue()
                : selectedLimit();

            if (configureKind() === "user-team") {
                await setPerUserSpendLimit(composerId, bubbleId, limit, context);
            } else {
                await setHardLimit(composerId, bubbleId, limit, context);
            }
            setConfigureInProgress(false);
            closeModal();
        }
    };
    break;
```

**Source location**: Lines 705245-705368 in workbench.desktop.main.js

## Summary

The Cursor spend limit system provides:

1. **Multi-level limits**: Individual, per-user, team, and service account levels
2. **Usage-based pricing toggle**: Can enable/disable pay-as-you-go billing
3. **Tiered scenarios**: Plan limits, tier-based limits, on-demand limits, monthly limits, pooled limits
4. **Slow pool degradation**: Users over limits get slower service rather than hard blocks
5. **Credit system**: Teams can have pre-paid credits
6. **Display threshold**: Configurable threshold for when to show usage indicators
7. **Admin controls**: Team admins can block individual limit configuration
8. **Premium model pricing**: Separate toggle for usage-based pricing on premium models

## Follow-Up Investigation Tasks

The following areas warrant additional investigation:

1. **Usage event pricing calculation**: How are costs calculated for different event types?
2. **Dynamic team limits**: How does `is_dynamic_team_limit` affect limit enforcement?
3. **Pooled limits**: How do pooled limits work across team members?
4. **Credit expiration**: How are team credits consumed and do they expire?
5. **BugBot billing**: Separate billing track for BugBot feature
