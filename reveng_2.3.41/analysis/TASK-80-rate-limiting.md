# TASK-80: Rate Limiting Schemas and Enforcement

## Overview

Cursor implements multi-layered rate limiting across client, server, and third-party API integrations. The system distinguishes between user tiers (free vs pro), different error categories, and provides both hard limits and "changeable" limits that can be upgraded.

## Rate Limiting Error Codes (aiserver.v1.ErrorDetails.Error)

The `fu` enum in `aiserver.v1.ErrorDetails.Error` defines all rate limiting related error codes:

| Code | Name | Description |
|------|------|-------------|
| 7 | `ERROR_FREE_USER_RATE_LIMIT_EXCEEDED` | Free tier users making too many requests too quickly |
| 8 | `ERROR_PRO_USER_RATE_LIMIT_EXCEEDED` | Pro users making unusual number of AI requests |
| 9 | `ERROR_FREE_USER_USAGE_LIMIT` | Free tier usage quota exhausted |
| 10 | `ERROR_PRO_USER_USAGE_LIMIT` | Pro tier slow request queue full |
| 14 | `ERROR_OPENAI_RATE_LIMIT_EXCEEDED` | Upstream OpenAI API rate limit |
| 15 | `ERROR_OPENAI_ACCOUNT_LIMIT_EXCEEDED` | OpenAI account spending limit |
| 22 | `ERROR_GENERIC_RATE_LIMIT_EXCEEDED` | Generic rate limit catch-all |
| 28 | `ERROR_GPT_4_VISION_PREVIEW_RATE_LIMIT` | Vision model specific limit |
| 34 | `ERROR_API_KEY_RATE_LIMIT` | User's API key rate limited |
| 41 | `ERROR_RESOURCE_EXHAUSTED` | General resource exhaustion |
| 50 | `ERROR_RATE_LIMITED` | Hard rate limit (cannot upgrade) |
| 51 | `ERROR_RATE_LIMITED_CHANGEABLE` | Soft rate limit (can upgrade plan) |

**Source location**: Lines 92685-92848 in workbench.desktop.main.js

## Protobuf Schemas

### ErrorDetails (aiserver.v1.ErrorDetails)

```protobuf
message ErrorDetails {
  enum Error {
    ERROR_UNSPECIFIED = 0;
    ERROR_FREE_USER_RATE_LIMIT_EXCEEDED = 7;
    ERROR_PRO_USER_RATE_LIMIT_EXCEEDED = 8;
    ERROR_FREE_USER_USAGE_LIMIT = 9;
    ERROR_PRO_USER_USAGE_LIMIT = 10;
    ERROR_OPENAI_RATE_LIMIT_EXCEEDED = 14;
    ERROR_OPENAI_ACCOUNT_LIMIT_EXCEEDED = 15;
    ERROR_GENERIC_RATE_LIMIT_EXCEEDED = 22;
    ERROR_GPT_4_VISION_PREVIEW_RATE_LIMIT = 28;
    ERROR_API_KEY_RATE_LIMIT = 34;
    ERROR_RATE_LIMITED = 50;
    ERROR_RATE_LIMITED_CHANGEABLE = 51;
    // ... other error codes
  }

  Error error = 1;
  CustomErrorDetails details = 2;
  optional bool is_expected = 3;
}
```

### CustomErrorDetails (aiserver.v1.CustomErrorDetails)

```protobuf
message CustomErrorDetails {
  string title = 1;
  string detail = 2;
  optional bool allow_command_links_potentially_unsafe = 3;
  optional bool is_retryable = 4;
  // Additional fields for buttons, plan choices, etc.
}
```

### FSConfigResponse (aiserver.v1.FSConfigResponse) - File Sync Rate Limiter

The file sync system has its own rate limiting configuration:

```protobuf
message FSConfigResponse {
  float check_filesync_hash_percent = 1;
  optional int32 rate_limiter_breaker_reset_time_ms = 2;
  optional int32 rate_limiter_rps = 3;
  optional int32 rate_limiter_burst_capacity = 4;
  optional int32 max_recent_updates_stored = 5;
  // ... other sync configuration fields
}
```

**Source location**: Lines 144049-144160 in workbench.desktop.main.js

### ClientTracingConfig (aiserver.v1.ClientTracingConfig) - Sentry Rate Limits

Sentry error reporting has its own rate limits:

```protobuf
message ClientTracingConfig {
  double global_sample_rate = 1;
  double traces_sample_rate = 2;
  double logger_sample_rate = 3;
  double minidump_sample_rate = 4;
  double error_rate_limit = 5;
  double performance_unit_rate_limit = 6;
  double profiles_sample_rate = 7;
  double json_stringify_sample_rate = 8;
}
```

**Source location**: Lines 826846-826897 in workbench.desktop.main.js

## Client-Side Rate Limiting Implementation

### Statsig Leaky Bucket Algorithm

The Statsig SDK uses a leaky bucket algorithm for client-side rate limiting:

```javascript
// Constants from NetworkCore.js
K7r = 50;              // Max bucket capacity
lec = K7r / aec;       // Leak rate (50 requests per 1000ms = 50 RPS)
aec = 1e3;             // 1000ms time window

_isRateLimited(endpoint) {
    const now = Date.now();
    const bucket = this._leakyBucket[endpoint] ?? {
        count: 0,
        lastRequestTime: now
    };

    // Calculate leak since last request
    const timeDelta = now - bucket.lastRequestTime;
    const leaked = Math.floor(timeDelta * leakRate);

    // Apply leak
    bucket.count = Math.max(0, bucket.count - leaked);

    // Check if rate limited
    if (bucket.count >= maxCapacity) {
        return true;
    }

    // Add request to bucket
    bucket.count += 1;
    bucket.lastRequestTime = now;
    this._leakyBucket[endpoint] = bucket;
    return false;
}
```

**Source location**: Lines 292459-292568 in workbench.desktop.main.js

### HTTP 429 Handling with Retry-After

The UserDataSync service handles 429 responses with backoff:

```javascript
if (response.statusCode === 429) {
    const retryAfter = response.headers["retry-after"];
    if (retryAfter) {
        this.setDonotMakeRequestsUntil(
            new Date(Date.now() + parseInt(retryAfter) * 1000)
        );
        throw new TooManyRequestsAndRetryAfter();
    }
    throw new RemoteTooManyRequests();
}
```

**Source location**: Lines 888437-888442 in workbench.desktop.main.js

### GitHub API Rate Limit Monitoring

GitHub API calls track rate limits via headers:

```javascript
logRateLimitInfo(response, queryName) {
    const used = response.headers.get("x-ratelimit-used");
    const limit = response.headers.get("x-ratelimit-limit");
    const reset = response.headers.get("x-ratelimit-reset");

    const usedNum = used ? parseInt(used, 10) : 0;
    const limitNum = limit ? parseInt(limit, 10) : 5000;
    const resetNum = reset ? parseInt(reset, 10) : 0;
    // Log and track remaining quota
}
```

**Source location**: Lines 445493-445539 in workbench.desktop.main.js

## User-Facing Error Messages

The `QOe` class defines user-facing messages for rate limit errors:

| Error Code | Message |
|------------|---------|
| `FREE_USER_RATE_LIMIT_EXCEEDED` | "It seems like you're making too many requests too quickly. Please try again in a minute." |
| `PRO_USER_RATE_LIMIT_EXCEEDED` | "It seems like you're making an unusual number of AI requests. Please try again later." |
| `FREE_USER_USAGE_LIMIT` | "Our servers are currently overloaded for non-pro users, and you've used your free quota." |
| `PRO_USER_USAGE_LIMIT` | "We're currently receiving a large number of slow requests and could not queue yours." |

**Source location**: Lines 451148-451178 in workbench.desktop.main.js

## Rate Limit UI Handling

### Changeable vs Non-Changeable Limits

The UI distinguishes between two types of rate limits:

1. **RATE_LIMITED (50)**: Hard limit, cannot be changed by upgrading
   - Shows "Switch Models" as the only option

2. **RATE_LIMITED_CHANGEABLE (51)**: Soft limit, can upgrade plan
   - Shows upgrade options (Pro, Pro+, Ultra)
   - Listens for subscription changes to automatically dismiss

```javascript
const isChangeableRateLimit = () =>
    error === fu.RATE_LIMITED_CHANGEABLE ||
    error === "ERROR_RATE_LIMITED_CHANGEABLE";

const isHardRateLimit = () =>
    error === fu.RATE_LIMITED ||
    error === "ERROR_RATE_LIMITED";

// UI title varies based on limit type
if (isChangeableRateLimit() || isHardRateLimit()) {
    return details?.title || "You've hit your rate limit on your current plan";
}
```

**Source location**: Lines 705030-705180 in workbench.desktop.main.js

### Error Analytics Tracking

Rate limited events are tracked for analytics:

```javascript
const isRateLimited =
    error === fu.OPENAI_RATE_LIMIT_EXCEEDED ||
    error === fu.PRO_USER_RATE_LIMIT_EXCEEDED ||
    error === fu.FREE_USER_RATE_LIMIT_EXCEEDED ||
    error === fu.API_KEY_RATE_LIMIT ||
    error === fu.GPT_4_VISION_PREVIEW_RATE_LIMIT;

analyticsService.trackEvent("composer.error.provider", {
    error: fu[error] ?? "UNKNOWN",
    code: connectErrorCode,
    isRetryable: isRetryable,
    rateLimited: isRateLimited,
    model: modelName
});
```

**Source location**: Lines 490474-490489 in workbench.desktop.main.js

## Error Code Mapping

The `mapErrorCode` function translates string error codes from server responses:

```javascript
mapErrorCode(code) {
    switch (code) {
        case "RATE_LIMITED_CHANGEABLE":
            return fu.RATE_LIMITED_CHANGEABLE;
        case "FREE_USER_RATE_LIMIT_EXCEEDED":
            return fu.FREE_USER_RATE_LIMIT_EXCEEDED;
        case "PRO_USER_RATE_LIMIT_EXCEEDED":
            return fu.PRO_USER_RATE_LIMIT_EXCEEDED;
        case "RESOURCE_EXHAUSTED":
            return fu.RESOURCE_EXHAUSTED;
        case "TIMEOUT":
            return fu.TIMEOUT;
        // ...
    }
}
```

**Source location**: Lines 485863-485882 in workbench.desktop.main.js

## Sentry Rate Limit Integration

Sentry SDK handles its own rate limits via HTTP headers:

```javascript
const rateLimits = headers?.["x-sentry-rate-limits"];
const retryAfter = headers?.["retry-after"];

if (rateLimits) {
    // Parse rate limit categories
    for (const entry of rateLimits.trim().split(",")) {
        const [delay, categories, , , scope] = entry.split(":", 5);
        const delayMs = (isNaN(parseInt(delay, 10)) ? 60 : parseInt(delay, 10)) * 1000;
        // Apply rate limit per category
    }
}

// Record dropped events due to rate limiting
if (isRateLimited(disabledUntil, category)) {
    recorder.recordDroppedEvent("ratelimit_backoff", category);
}
```

**Source location**: Lines 4822-4852 in workbench.desktop.main.js

## Summary of Rate Limiting Layers

1. **Client-Side (Statsig)**: Leaky bucket algorithm, 50 requests max capacity, ~50 RPS leak rate
2. **Server-Side (AI Server)**: ErrorDetails protobuf with tier-based limits
3. **File Sync**: Configurable RPS, burst capacity, and breaker reset time
4. **Third-Party APIs**:
   - OpenAI: Account and rate limits
   - GitHub: Standard x-ratelimit headers
   - Sentry: Category-based rate limits with x-sentry-rate-limits header
5. **User Data Sync**: HTTP 429 with Retry-After header support

## Recommendations for Further Investigation

1. **Server-side rate limit configuration**: The FSConfigResponse schema suggests server-controlled rate limits (rps, burst capacity) - worth investigating how these are enforced
2. **Usage pricing limits**: The `USAGE_PRICING_REQUIRED` and `USAGE_PRICING_REQUIRED_CHANGEABLE` errors suggest a usage-based billing system
3. **Model-specific limits**: GPT-4 Vision has its own rate limit code - investigate other model-specific limits
4. **Spend limits**: The UI references "configureSpendLimit" and spend limit configuration

---

## Additional Findings (Extended Investigation)

### Queue Position Monitoring System

When requests are rate limited or queued, Cursor implements a queue position polling system:

#### CheckQueuePositionRequest (aiserver.v1.CheckQueuePositionRequest)

```protobuf
message CheckQueuePositionRequest {
  string orig_request_id = 1;
  ModelDetails model_details = 2;  // Optional model info
  string usage_uuid = 3;
}
```

**Source location**: Lines 168853-168888 in workbench.desktop.main.js

#### CheckQueuePositionResponse (aiserver.v1.CheckQueuePositionResponse)

```protobuf
message CheckQueuePositionResponse {
  int32 position = 1;                              // Queue position (-1 means not queued)
  optional int32 seconds_left_to_wait = 2;         // Estimated wait time
  optional int32 new_queue_position = 7;           // Updated position
  bool hit_hard_limit = 3;                         // Hard limit reached
  bool could_enable_usage_based_pricing_to_skip = 4;  // Can skip queue with paid tier
  UsageEventDetails usage_event_details = 5;       // Details for usage billing
  CustomLink custom_link = 6;                      // Custom link for upgrade
  optional ModelForSlowPoolNudgeData model_for_slow_pool_nudge_data = 8;  // Suggest faster model
}
```

**Source location**: Lines 168890-168958 in workbench.desktop.main.js

#### Slow Pool Nudge Data

When users are in the slow pool, the server can suggest alternative models:

```protobuf
message ModelForSlowPoolNudgeData {
  string model = 1;      // Suggested faster model
  string message = 2;    // User-facing message
}
```

**Source location**: Lines 168996-169006 in workbench.desktop.main.js

### Usage Tracking System

Cursor tracks usage events for billing and rate limiting decisions:

#### UsageEventKind Enum (aiserver.v1.UsageEventKind)

| Code | Name | Description |
|------|------|-------------|
| 0 | `USAGE_EVENT_KIND_UNSPECIFIED` | Unknown usage type |
| 1 | `USAGE_EVENT_KIND_USAGE_BASED` | Pay-per-use request |
| 2 | `USAGE_EVENT_KIND_USER_API_KEY` | User's own API key |
| 3 | `USAGE_EVENT_KIND_INCLUDED_IN_PRO` | Included in Pro plan |
| 4 | `USAGE_EVENT_KIND_INCLUDED_IN_BUSINESS` | Included in Business plan |
| 5 | `USAGE_EVENT_KIND_ERRORED_NOT_CHARGED` | Error - no charge |
| 6 | `USAGE_EVENT_KIND_ABORTED_NOT_CHARGED` | User aborted - no charge |
| 7 | `USAGE_EVENT_KIND_CUSTOM_SUBSCRIPTION` | Custom enterprise subscription |
| 8 | `USAGE_EVENT_KIND_INCLUDED_IN_PRO_PLUS` | Included in Pro+ plan |
| 9 | `USAGE_EVENT_KIND_INCLUDED_IN_ULTRA` | Included in Ultra plan |
| 10 | `USAGE_EVENT_KIND_FREE_CREDIT` | Using free credits |

**Source location**: Lines 156254-156288 in workbench.desktop.main.js

#### Usage Event Tracking Features

Usage events are tracked per feature type:

- `chat` - Standard chat interactions
- `context_chat` - Context-aware chat
- `cmd_k` - Command-K operations
- `terminal_cmd_k` - Terminal command generation
- `ai_review_accepted_comment` - AI code review comments
- `interpreter_chat` - Interpreter/REPL chat
- `slash_edit` - Slash-edit operations
- `composer` - Composer requests
- `fast_apply` - Fast apply operations
- `tool_call_composer` - Tool call operations
- `warm_composer` - Warm-up requests
- `bug_bot` - Bug detection
- `bug_finder_trigger_v1` - Bug finder triggers

**Source location**: Lines 156289-156400 in workbench.desktop.main.js

### Hard Limit System

#### GetHardLimitRequest/Response (aiserver.v1.GetHardLimit*)

```protobuf
message GetHardLimitRequest {
  // Team or user identification fields
}

message GetHardLimitResponse {
  int32 hard_limit = 1;                          // Spending limit in dollars
  bool no_usage_based_allowed = 2;               // Usage-based pricing disabled
  float per_user_monthly_limit_dollars = 3;      // Per-user monthly cap
  bool is_dynamic_team_limit = 4;                // Dynamic limit based on team size
}
```

**Source location**: Lines 272146-272185 in workbench.desktop.main.js

#### SetHardLimitRequest (aiserver.v1.SetHardLimitRequest)

```protobuf
message SetHardLimitRequest {
  int32 hard_limit = 1;
  bool no_usage_based_allowed = 3;
  bool preserve_hard_limit_per_user = 4;
  float per_user_monthly_limit_dollars = 5;
  bool clear_per_user_monthly_limit_dollars = 6;
  bool is_dynamic_team_limit = 7;
}
```

**Source location**: Lines 272224-272275 in workbench.desktop.main.js

### Client Rerun Rate Limiting

The client implements its own rate limiting for error recovery/rerun attempts:

```javascript
// Maximum 2 reruns within 5 seconds
okToRerun() {
    const now = Date.now();
    const recentTimestamps = this.rerunTimestamps.slice(-2);
    const okToRerun = recentTimestamps.length < 2 ||
                      !recentTimestamps.every(t => now - t < 5000);

    // Keep only last 2 timestamps
    this.rerunTimestamps = this.rerunTimestamps.slice(-2);
    return okToRerun;
}
```

**Source location**: Lines 451224-451233 in workbench.desktop.main.js

### Retry Interceptor Headers

The client can configure retry behavior via HTTP headers:

```javascript
function buildRetryHeaders(enabled, options) {
    const headers = {
        "X-Cursor-RetryInterceptor-Enabled": "true"
    };
    if (options?.maxRetries !== undefined) {
        headers["X-Cursor-RetryInterceptor-MaxRetries"] = String(options.maxRetries);
    }
    if (options?.baseDelayMs !== undefined) {
        headers["X-Cursor-RetryInterceptor-BaseDelayMs"] = String(options.baseDelayMs);
    }
    if (options?.maxDelayMs !== undefined) {
        headers["X-Cursor-RetryInterceptor-MaxDelayMs"] = String(options.maxDelayMs);
    }
    return headers;
}
```

**Source location**: Lines 300961-300967 in workbench.desktop.main.js

### Slow Pool vs Fast Pool

The system distinguishes between slow and fast request pools:

```javascript
// From membership status response
{
    isInSlowPool: boolean,           // User is in slow queue
    canConfigureSpendLimit: boolean, // Can set spending limits
    hasPendingRequest: boolean,      // Has pending request
    allowedModelIds: string[],       // Allowed model IDs
    allowedModelTags: string[]       // Allowed model tags
}
```

UI messaging for slow pool users:
- Title: "Increase limits for faster responses"
- Option to enable usage-based pricing to skip queue

**Source location**: Lines 278774-278780 in workbench.desktop.main.js

### Team Member Usage Tracking

For teams, individual member usage is tracked:

```protobuf
message TeamMemberUsage {
  int64 user_id = 1;
  int32 spend_cents = 2;               // Total spend in cents
  int32 fast_premium_requests = 3;     // Fast pool premium requests
  string name = 4;
  string email = 5;
  Role role = 6;
  float hard_limit_override_dollars = 7;  // Per-user override
}
```

**Source location**: Lines 279324-279330 in workbench.desktop.main.js

### DNS Query Cooldown

For fallback URL resolution, DNS queries have a cooldown period:

```javascript
_dnsQueryCooldowns = {};
YZl = 14400 * 1e3;  // 4 hour cooldown

async _tryFetchFallbackUrlsFromNetwork(urlConfig) {
    const cooldown = this._dnsQueryCooldowns[urlConfig.endpoint];
    if (cooldown && Date.now() < cooldown) {
        return null;  // Still in cooldown
    }
    this._dnsQueryCooldowns[urlConfig.endpoint] = Date.now() + YZl;
    // ... fetch fallback URLs
}
```

**Source location**: Lines 292226-292276 in workbench.desktop.main.js

### Best-of-N Promotion Cooldown

The "best of N" model promotion has its own cooldown:

```javascript
best_of_n_promotion_config: {
    cooldownMs: 300 * 60 * 1e3,        // 5 hour cooldown
    promptLengthThreshold: 256,
    promptCountThreshold: 2,
    dismissLimit: 3
}
```

**Source location**: Lines 295517-295523 in workbench.desktop.main.js

### Network Access Notification Cooldown

UI notifications for network access have cooldown periods:

```javascript
const xTs = ...; // Cooldown duration in ms

if (this.lastDismissalTime) {
    const timeSinceDismissal = Date.now() - this.lastDismissalTime;
    if (timeSinceDismissal < xTs) {
        const minutesRemaining = Math.ceil((xTs - timeSinceDismissal) / 60000);
        this.logService.trace(
            `[NetworkAccessNotification] In cooldown period, ${minutesRemaining} minutes remaining`
        );
        return;
    }
    this.lastDismissalTime = undefined;
}
```

**Source location**: Lines 449171-449190 in workbench.desktop.main.js

## Complete Rate Limiting Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                     CURSOR RATE LIMITING                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 SERVER-SIDE LIMITS                       │   │
│  │  - ErrorDetails.Error enum (fu) with 12+ rate limit codes│   │
│  │  - Tier-based: FREE vs PRO vs ULTRA                     │   │
│  │  - Changeable vs Non-Changeable limits                  │   │
│  │  - Queue position monitoring (CheckQueuePosition RPC)   │   │
│  │  - Hard limits (spending caps per user/team)            │   │
│  │  - Slow pool vs fast pool routing                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 CLIENT-SIDE LIMITS                       │   │
│  │  - Leaky bucket (Statsig): 50 req capacity, 50 RPS leak │   │
│  │  - Rerun rate limiting: max 2 retries in 5 seconds      │   │
│  │  - HTTP 429 handling with Retry-After header            │   │
│  │  - donotMakeRequestsUntil timestamp storage             │   │
│  │  - DNS query cooldowns (4 hours)                        │   │
│  │  - UI notification cooldowns                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               USAGE TRACKING & BILLING                   │   │
│  │  - UsageEventKind: 10 billing categories                │   │
│  │  - Per-feature tracking (chat, composer, cmd_k, etc.)   │   │
│  │  - Team member usage aggregation                        │   │
│  │  - Usage-based pricing skip queue option                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              THIRD-PARTY API LIMITS                      │   │
│  │  - OpenAI: rate + account limits                        │   │
│  │  - GitHub: x-ratelimit-* headers                        │   │
│  │  - Sentry: x-sentry-rate-limits header                  │   │
│  │  - User Data Sync: HTTP 429 + Retry-After               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              FILE SYNC RATE LIMITER                      │   │
│  │  - rate_limiter_rps: requests per second                │   │
│  │  - rate_limiter_burst_capacity: burst allowance         │   │
│  │  - rate_limiter_breaker_reset_time_ms: circuit breaker  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Related Tasks for Further Investigation

- TASK-69: Capability tiers (how rate limits vary by subscription)
- TASK-116: Feature gates (rate limit flags in feature configuration)
- TASK-119: Polling backoff (retry timing algorithms)
