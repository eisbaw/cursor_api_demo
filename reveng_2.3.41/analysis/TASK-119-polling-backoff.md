# TASK-119: Polling Backoff and Interval Strategy Analysis

## Executive Summary

Cursor IDE 2.3.41 implements multiple polling and backoff strategies across different subsystems. The codebase uses a consistent pattern of exponential backoff with jitter for resilience, with configurable intervals that can be controlled server-side via dynamic configs (Statsig). This analysis documents all discovered polling mechanisms, their timing parameters, and backoff algorithms.

## Polling Subsystems Overview

### 1. Background Agent Polling (HTTP/1.0 Fallback)

**Location**: Lines 295107-295116, 295443-295447

When using HTTP/1.0 polling fallback mode (for restrictive proxy environments), the client uses this configuration:

```javascript
background_agent_polling_config: {
    defaultPollingDelayMs: 5000  // 5 seconds default poll interval
}
```

**Schema**:
```javascript
background_agent_polling_config: ls.object({
    defaultPollingDelayMs: ls.number()
})
```

This configuration is used when the HTTP/1.0 compatibility mode is enabled via `cursor.general.disableHttp1SSE: true`.

---

### 2. Statsig Experiment Polling

**Location**: Lines 973640-973741

The `ExperimentRefreshService` polls for experiment configuration updates:

```javascript
class ExperimentRefreshService {
    static MIN_POLL_INTERVAL_MS = 30 * 1000;    // 30 seconds minimum
    static BASE_POLL_INTERVAL_MS = 300 * 1000;  // 5 minutes base interval

    _calculatePollInterval(env) {
        // Dev/extension development mode uses minimum interval
        if (!env.isBuilt || env.isExtensionDevelopment) {
            return MIN_POLL_INTERVAL_MS;  // 30 seconds
        }

        // Server can override via chatConfig.clientStatsigPollIntervalMs
        const serverInterval = this.aiServerConfigService
            .cachedServerConfig.chatConfig?.clientStatsigPollIntervalMs;

        const interval = (typeof serverInterval == "number" &&
                         Number.isFinite(serverInterval) &&
                         serverInterval > 0)
            ? serverInterval
            : BASE_POLL_INTERVAL_MS;

        return Math.max(interval, MIN_POLL_INTERVAL_MS);  // Floor at 30s
    }

    _startPolling() {
        // Jitter: 0% to +20% random multiplier
        const jitterMultiplier = 1 + Math.random() * 0.2;
        const baseInterval = Math.max(this._basePollIntervalMs, MIN_POLL_INTERVAL_MS);
        const jitteredInterval = Math.floor(baseInterval * jitterMultiplier);

        this._pollInterval.value = setInterval(() => {
            this._refreshBootstrapFromServer("poll");
        }, jitteredInterval);
    }
}
```

**Key Characteristics**:
- Minimum interval: 30 seconds
- Default interval: 5 minutes (300,000ms)
- Jitter: 0-20% positive random offset
- Server-configurable via `clientStatsigPollIntervalMs`

---

### 3. GitHub Pull Request Auto-Refresh

**Location**: Lines 444830-445091

The GitHub PR service implements exponential backoff with jitter for auto-refresh:

```javascript
class GithubPRService {
    static PR_PAGE_SIZE = 5;
    static REVIEW_PAGE_SIZE = 5;
    static AUTO_REFRESH_BASE_INTERVAL_MS = 30 * 1000;    // 30 seconds
    static AUTO_REFRESH_MAX_INTERVAL_MS = 300 * 1000;    // 5 minutes max
    static AUTO_REFRESH_MAX_CONSECUTIVE_FAILURES = 10;
    static WINDOW_FOCUS_DEBOUNCE_MS = 5 * 1000;          // 5 seconds

    startAutoRefreshTimer() {
        if (this.autoRefreshConsecutiveFailures >= AUTO_REFRESH_MAX_CONSECUTIVE_FAILURES) {
            // Stop after 10 consecutive failures
            this.logService.warn("Auto-refresh stopped after too many consecutive failures");
            return;
        }

        // Exponential backoff: 2^failures multiplier
        const backoffMultiplier = Math.pow(2, this.autoRefreshConsecutiveFailures);
        const scaledInterval = AUTO_REFRESH_BASE_INTERVAL_MS * backoffMultiplier;
        const cappedInterval = Math.min(scaledInterval, AUTO_REFRESH_MAX_INTERVAL_MS);

        // Jitter: +/- 10% random offset
        const jitterOffset = cappedInterval * 0.1 * (Math.random() * 2 - 1);
        const finalInterval = Math.round(cappedInterval + jitterOffset);

        this.autoRefreshTimerHandle = setTimeout(() => {
            this.autoRefresh();
        }, finalInterval);
    }
}
```

**Backoff Progression** (with failures):
| Failures | Base Multiplier | Interval Range (with jitter) |
|----------|-----------------|------------------------------|
| 0 | 1x | 27-33 seconds |
| 1 | 2x | 54-66 seconds |
| 2 | 4x | 108-132 seconds |
| 3 | 8x | 216-264 seconds |
| 4+ | 16x+ | 270-330 seconds (capped) |
| 10 | - | Stops polling |

---

### 4. Usage Data Service Refresh

**Location**: Lines 299010-299090

```javascript
class UsageDataService {
    refreshInterval = 300 * 1000;    // 5 minutes normal refresh
    retryInterval = 1800 * 1000;     // 30 minutes on error
    CACHE_DURATION = 30 * 1000;      // 30 second cache
    PLAN_INFO_CACHE_DURATION = 30 * 1000;

    async refetch(force = false) {
        const now = Date.now();

        // Cache check - skip if recently fetched
        if (now - this.lastFetchTime < this.CACHE_DURATION &&
            !this.errorData() && !force) {
            return;
        }

        await this.performFetch(now);
    }
}

// Auto-refresh interval selection (Line ~299233)
const interval = this.errorData() ? this.retryInterval : this.refreshInterval;
// Normal: 5 minutes, On error: 30 minutes
```

---

### 5. Conversation Classification Polling

**Location**: Lines 939943-940010

```javascript
const CLASSIFICATION_POLL_INTERVAL = 600 * 1000;  // 10 minutes base (Xsm)
const CLASSIFICATION_JITTER_PERCENT = 0.1;        // +/- 10% (Qsm)
const MAX_CONVERSATIONS_PER_BATCH = 10;           // (epu)
const MAX_CONCURRENT_CLASSIFICATIONS = 3;         // (tpu)

scheduleNextPoll() {
    // Jitter: -10% to +10%
    const jitterMultiplier = (Math.random() * 2 - 1) * CLASSIFICATION_JITTER_PERCENT;
    const jitteredInterval = Math.floor(CLASSIFICATION_POLL_INTERVAL * (1 + jitterMultiplier));

    this.classificationPollingTimeoutId = setTimeout(() => {
        this.pollAndScheduleNext();
    }, jitteredInterval);
}
```

**Characteristics**:
- Base interval: 10 minutes
- Jitter: +/- 10%
- Effective range: 9-11 minutes
- Batch size: 10 conversations per poll
- Concurrency limit: 3 parallel classifications

---

### 6. Git Commit Polling

**Location**: Lines 954398-954452

```javascript
const COMMIT_POLL_INTERVAL = 600 * 1000;  // 10 minutes (zrm)

async startCommitPolling() {
    await this.gitContextService.waitForGitContextProvider();

    this.commitPollingIntervalId = setInterval(() => {
        this.pollForNewCommits().catch(err =>
            console.error("[AiCodeTracking] Polling error:", err)
        );
    }, COMMIT_POLL_INTERVAL);
}
```

**Characteristics**:
- Fixed interval: 10 minutes
- No backoff (background monitoring)
- Error handling with logging

---

### 7. Process List Polling (Proclist)

**Location**: Lines 1170560-1170617

```javascript
class CursorProclistPolling {
    loadStatsigConfig() {
        const config = this.experimentService.getDynamicConfig("extension_monitor_control");

        return {
            localEnabled: config?.local_enabled ?? false,
            backendReportingEnabled: config?.backend_reporting_enabled ?? false,
            // Clamped between 1 and 300 seconds (default 10)
            subsamplePollingRateSec: this.clampNumber(
                config?.subsample_polling_rate_sec, 10, 1, 300
            ),
            // Clamped between 1 and 30 minutes (default 5)
            samplePollingRateMin: this.clampNumber(
                config?.sample_polling_rate_min, 5, 1, 30
            )
        };
    }

    startPolling() {
        const intervalMs = this.config.samplePollingRateMin * 60 * 1000;

        this.pollTimer = setInterval(() => {
            this.poll();
        }, intervalMs);
    }

    clampNumber(value, defaultVal, min, max) {
        return Math.max(min, Math.min(max, typeof value == "number" ? value : defaultVal));
    }
}
```

**Characteristics**:
- Default: 5 minutes
- Range: 1-30 minutes
- Subsample rate: 1-300 seconds (default 10)
- Server-configurable via Statsig

---

### 8. Manual Login Polling

**Location**: Lines 1098180-1098217

```javascript
async generateLoginLink(mode) {
    let pollCount = 0;
    const MAX_POLL_ATTEMPTS = 30;
    const POLL_INTERVAL = 500;  // 500ms

    const pollingInterval = setInterval(async () => {
        const response = await fetch(`${pollingEndpoint}?uuid=${uuid}&verifier=${verifier}`);

        if (response.status === 404) {
            // Not ready yet, continue polling
            return;
        }

        const data = await response.json();
        if (data?.accessToken && data?.refreshToken) {
            clearInterval(pollingInterval);
            this.storeAccessRefreshToken(data.accessToken, data.refreshToken);
        }

        pollCount++;
        if (pollCount >= MAX_POLL_ATTEMPTS) {
            // Timeout after 15 seconds (30 * 500ms)
            clearInterval(pollingInterval);
        }
    }, POLL_INTERVAL);
}
```

**Characteristics**:
- Fixed interval: 500ms
- Max attempts: 30 (15 seconds total)
- No backoff (short-lived auth flow)

---

## Core Exponential Backoff Implementation

**Location**: Lines 300136-300153

The codebase includes a generic retry utility with exponential backoff:

```javascript
async function retryWithBackoff(operation, config) {
    let attempts = 0;
    let delay = config.initialRetryTimeMs;

    while (attempts < config.maxNumberOfRetries) {
        try {
            if (config.signal?.aborted) throw new Error("Aborted");

            const result = await operation();

            if (config.shouldRetry?.(result)) {
                if (++attempts >= config.maxNumberOfRetries) return result;
                await sleep(delay);
                delay = Math.min(delay * 2, config.maxDelayMs ?? Infinity);
                continue;
            }
            return result;
        } catch (error) {
            if (error.message === "Aborted" ||
                ++attempts >= config.maxNumberOfRetries) throw error;

            await sleep(delay);
            delay = Math.min(delay * 2, config.maxDelayMs ?? Infinity);
        }
    }
    throw new Error("Max retries reached");
}
```

**Key Features**:
- Pure exponential backoff (2x multiplier)
- Configurable max delay cap
- Abort signal support
- Custom retry condition via `shouldRetry`

---

## Retry Interceptor Configuration

**Location**: Lines 295122-295137, 295470-295488, 300964-300967

Server-configurable retry parameters for gRPC interceptor:

```javascript
// Schema
retry_interceptor_params_config: ls.object({
    maxRetries: ls.number().optional(),
    baseDelayMs: ls.number().optional(),
    maxDelayMs: ls.number().optional()
})

// Default values
retry_interceptor_params_config: {
    client: true,
    fallbackValues: {
        maxRetries: undefined,     // Server decides
        baseDelayMs: undefined,    // Server decides
        maxDelayMs: undefined      // Server decides
    }
}

// Retriable error codes
retry_interceptor_config: {
    retriableErrors: [
        { code: "Unavailable" },
        { code: "Internal" },
        { code: "DeadlineExceeded" }
    ]
}

// Header injection for retry params
function getRetryInterceptorHeaders(config) {
    const headers = {
        "X-Cursor-RetryInterceptor-Enabled": "true"
    };

    if (config?.maxRetries !== undefined) {
        headers["X-Cursor-RetryInterceptor-MaxRetries"] = String(config.maxRetries);
    }
    if (config?.baseDelayMs !== undefined) {
        headers["X-Cursor-RetryInterceptor-BaseDelayMs"] = String(config.baseDelayMs);
    }
    if (config?.maxDelayMs !== undefined) {
        headers["X-Cursor-RetryInterceptor-MaxDelayMs"] = String(config.maxDelayMs);
    }

    return headers;
}
```

**Usage Patterns** (from codebase):
- General streaming: `maxDelayMs: 1000` (Line 487901)
- Background tasks: `maxDelayMs: 300000` (5 minutes, Line 941627)
- Quick retries: `maxDelayMs: 4000` (Line 758954)

---

## Rate Limiting Response Handling

### HTTP 429 Too Many Requests

**Location**: Lines 888390-888442

```javascript
async request(url, options) {
    // Pre-check: Block if in rate limit period
    if (this._donotMakeRequestsUntil &&
        Date.now() < this._donotMakeRequestsUntil.getTime()) {
        throw new RequestError(
            `Request failed because of too many requests (429).`,
            url, "TooManyRequestsAndRetryAfter"
        );
    }

    // Clear rate limit flag on successful check
    this.setDonotMakeRequestsUntil(undefined);

    const response = await this.session.request(url, options);

    if (response.statusCode === 429) {
        const retryAfter = response.headers["retry-after"];

        if (retryAfter) {
            // Server specified retry delay
            this.setDonotMakeRequestsUntil(
                new Date(Date.now() + parseInt(retryAfter) * 1000)
            );
            throw new RequestError(..., "TooManyRequestsAndRetryAfter", ...);
        } else {
            // No retry-after header
            throw new RequestError(..., "RemoteTooManyRequests", ...);
        }
    }
}
```

### Local Rate Limiting

**Location**: Lines 888460-888473

```javascript
class RateLimitedRequestService {
    constructor(limit, interval, requestService, logService) {
        this.limit = limit;           // Max requests
        this.interval = interval;     // Time window
        this.requests = [];
        this.startTime = undefined;
    }

    request(url, options) {
        if (this.isExpired()) this.reset();

        if (this.requests.length >= this.limit) {
            throw new RequestError(
                `Too many requests. Only ${this.limit} requests allowed in ${this.interval/(1000*60)} minutes.`,
                url, "LocalTooManyRequests"
            );
        }

        this.startTime = this.startTime || new Date();
        this.requests.push(url);
        return this.requestService.request(options);
    }

    isExpired() {
        return this.startTime !== undefined &&
               new Date().getTime() - this.startTime.getTime() > this.interval;
    }
}
```

### Sentry Rate Limit Handling

**Location**: Lines 4803-4861

```javascript
const DEFAULT_RATE_LIMIT_DURATION = 60 * 1000;  // 60 seconds

function parseRateLimitHeaders(statusCode, headers, timestamp = Date.now()) {
    const rateLimits = { ...existingLimits };
    const rateLimitHeader = headers?.["x-sentry-rate-limits"];
    const retryAfterHeader = headers?.["retry-after"];

    if (rateLimitHeader) {
        // Parse comma-separated rate limit entries
        for (const entry of rateLimitHeader.trim().split(",")) {
            const [seconds, categories, , , scope] = entry.split(":", 5);
            const duration = (isNaN(parseInt(seconds)) ? 60 : parseInt(seconds)) * 1000;

            if (!categories) {
                rateLimits.all = timestamp + duration;
            } else {
                for (const category of categories.split(";")) {
                    rateLimits[category] = timestamp + duration;
                }
            }
        }
    } else if (retryAfterHeader) {
        rateLimits.all = timestamp + parseRetryAfter(retryAfterHeader, timestamp);
    } else if (statusCode === 429) {
        // Fallback: 60 second rate limit
        rateLimits.all = timestamp + DEFAULT_RATE_LIMIT_DURATION;
    }

    return rateLimits;
}

// Drop events during rate limit backoff
function processEnvelope(envelope) {
    const events = [];

    forEachItem(envelope, (item, category) => {
        if (isRateLimited(rateLimits, category)) {
            recorder.recordDroppedEvent("ratelimit_backoff", category);
        } else {
            events.push(item);
        }
    });

    if (events.length === 0) return Promise.resolve({});
    // ... send remaining events
}
```

---

## Remote Connection Reconnection Strategy

**Location**: Lines 1082499-1082665

```javascript
// Initial connection retry (5 attempts)
async function initialConnect(options, callback) {
    for (let attempt = 1; ; attempt++) {
        try {
            const result = await resolveConnection(options);
            return await callback(result);
        } catch (error) {
            if (attempt < 5) {
                logService.error(`[remote-connection][attempt ${attempt}] Error, will retry...`);
            } else {
                logService.error(`[remote-connection][attempt ${attempt}] Permanent failure`);
                throw error;
            }
        }
    }
}

// Reconnection loop with progressive delays
class RemoteConnection {
    async _runReconnectingLoop() {
        // Progressive delay sequence (in seconds)
        const delays = [0, 5, 5, 10, 10, 10, 10, 10, 30];
        let attempt = -1;

        do {
            attempt++;
            const delay = attempt < delays.length
                ? delays[attempt]
                : delays[delays.length - 1];  // Cap at 30 seconds

            if (delay > 0) {
                // Wait before reconnection attempt
                await sleep(delay * 1000);
            }

            try {
                const connection = await resolveConnection(this._options);
                await this._reconnect(connection);
                logService.info(`Reconnected on attempt ${attempt + 1}`);
                break;
            } catch (error) {
                // Grace period: 360 attempts (~3 hours at 30s intervals)
                if (attempt > 360) {
                    logService.error("Reconnection grace time expired");
                    this._onReconnectionPermanentFailure(...);
                    break;
                }

                // Handle specific error types differently
                if (isTemporarilyNotAvailable(error) ||
                    isNetworkError(error) ||
                    isCancellation(error)) {
                    continue;  // Retry
                }

                // Permanent failure for other errors
                this._onReconnectionPermanentFailure(...);
                break;
            }
        } while (!this._isPermanentFailure && !this._isDisposed);
    }
}
```

**Reconnection Delay Sequence**:
| Attempt | Delay |
|---------|-------|
| 1 | 0s (immediate) |
| 2-3 | 5s |
| 4-8 | 10s |
| 9+ | 30s (cap) |

**Grace Period**: ~3 hours (360 attempts at 30s each)

---

## Terminal Extension Host Retry

**Location**: Lines 1165490-1165504

```javascript
async createSessionWithRetry(timeout) {
    const startTime = Date.now();
    let retryDelay = 100;  // Start at 100ms
    const MAX_DELAY = 1000;
    const MAX_ATTEMPTS = 10;

    for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
        try {
            const remaining = timeout - (Date.now() - startTime);
            return await this._withTimeout(
                this._shellExecService.createSession(),
                Math.min(15000, remaining),
                "createSession timeout"
            );
        } catch (error) {
            if (!error.message.includes("not initialized")) throw error;

            const elapsed = Date.now() - startTime;
            const remaining = timeout - elapsed;

            if (attempt >= 9 || remaining <= retryDelay) {
                throw new Error(`Extension host not ready after ${attempt + 1} attempts`);
            }

            console.debug(`Extension host not ready, retrying in ${retryDelay}ms`);
            await sleep(retryDelay);
            retryDelay = Math.min(retryDelay * 2, MAX_DELAY);
        }
    }
}
```

**Backoff Sequence**: 100ms, 200ms, 400ms, 800ms, 1000ms (capped)

---

## Idempotent Stream Auto-Resume

**Location**: Lines 945190-945231

```javascript
async _autoResumeInterruptedStreams() {
    const lookbackWindow = this.experimentService.getDynamicConfigParam(
        "idempotent_stream_config",
        "retry_lookback_window_ms"
    ) ?? 7200000;  // Default: 2 hours

    const now = Date.now();

    for (const composer of allComposers) {
        const lastUpdated = composer.lastUpdatedAt ?? composer.createdAt;

        // Skip if too old
        if (now - lastUpdated > lookbackWindow) continue;

        const handle = await this.getComposerHandle(composer.composerId);
        if (!handle?.data.idempotentStreamState) continue;

        logService.info("[composer] Auto-resuming interrupted stream", {
            composerId: composer.composerId,
            timeSinceLastUpdate: now - lastUpdated
        });

        await this.submitChat(composer.composerId, "", { isResume: true });
    }
}
```

**Configuration**:
```javascript
idempotent_stream_config: {
    retry_lookback_window_ms: 7200 * 1000  // 2 hours default
}
```

---

## File Watcher Polling

**Location**: Lines 1119595-1119596

```javascript
// Recursive file watcher with optional polling mode
const usePolling = this.options?.watcher?.recursive?.usePolling;

if (usePolling === true) {
    // Global polling enabled
    watcherOptions.pollingInterval =
        this.options?.watcher?.recursive?.pollingInterval ?? 5000;
} else if (Array.isArray(usePolling) && usePolling.includes(path)) {
    // Path-specific polling
    watcherOptions.pollingInterval =
        this.options?.watcher?.recursive?.pollingInterval ?? 5000;
}
```

**Characteristics**:
- Default polling interval: 5 seconds
- Can be enabled globally or per-path
- Typically used for network mounts or filesystems without native watching

---

## Event Loop Block Detection Polling

**Location**: Lines 506808-506832

```javascript
const EventLoopBlockRenderer = (options) => {
    const threshold = options?.threshold ?? 1000;      // 1 second default
    const pollInterval = options?.pollInterval || threshold / 2;  // 500ms

    return {
        setup(client) {
            // Initial status report
            client.sendStatus({
                status: document.visibilityState,
                config: { pollInterval, anrThreshold: threshold }
            });

            // Periodic heartbeat
            setInterval(() => {
                client.sendStatus({
                    status: "alive",
                    config: { pollInterval, anrThreshold: threshold }
                });
            }, pollInterval);
        }
    };
};
```

---

## Agent Wait for Changes Clear

**Location**: Lines 945235-945244

```javascript
async _waitForAgentChangesToClear(composerId, timeout = 5000) {
    const start = Date.now();
    let delay = 50;         // Start at 50ms
    const maxDelay = 1000;  // Cap at 1 second
    const multiplier = 1.5; // Slower growth than 2x

    while (Date.now() - start < timeout) {
        const diffs = this.getAllInlineDiffs(composerId);
        if (!diffs.length) return;  // Changes cleared

        await sleep(delay);
        delay = Math.min(delay * multiplier, maxDelay);
    }
    // Timeout - changes didn't clear
}
```

---

## Composer File Operations Retry

**Location**: Lines 472350-472362

```javascript
const retryWithBackoff = async (operation, description, maxAttempts = 3) => {
    let lastError;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        try {
            return await operation();
        } catch (error) {
            lastError = error instanceof Error ? error : new Error(String(error));

            if (attempt < maxAttempts - 1) {
                // Exponential backoff: 1s, 2s, 4s (capped at 5s)
                const delay = Math.min(1000 * Math.pow(2, attempt), 5000);
                console.warn(`${description} failed (attempt ${attempt + 1}/${maxAttempts}), retrying in ${delay}ms`);
                await sleep(delay);
            }
        }
    }

    console.error(`${description} failed after ${maxAttempts} attempts`);
    throw lastError;
};
```

---

## Summary Table: All Polling Intervals

| Subsystem | Base Interval | Jitter | Backoff | Max/Cap |
|-----------|---------------|--------|---------|---------|
| Background Agent Poll | 5s | None | None | N/A |
| Statsig Experiments | 5 min | +0-20% | None | 30s min |
| GitHub PR Refresh | 30s | +/-10% | 2^failures | 5 min cap |
| Usage Data | 5 min / 30 min (error) | None | Step | N/A |
| Conversation Classification | 10 min | +/-10% | None | N/A |
| Git Commit Tracking | 10 min | None | None | N/A |
| Proclist Monitoring | 5 min | None | None | 1-30 min configurable |
| Login Polling | 500ms | None | None | 15s timeout |
| Remote Reconnection | 5s/10s/30s | None | Step | 30s cap, 3hr grace |
| Terminal Extension | 100ms | None | 2x | 1s cap |
| File Watcher | 5s | None | None | N/A |
| Event Loop Heartbeat | 500ms | None | None | N/A |

---

## Summary Table: Backoff Algorithms

| Pattern | Multiplier | Jitter | Use Case |
|---------|------------|--------|----------|
| Pure Exponential | 2x | None | Generic retry, terminal extension |
| Exponential with Cap | 2x | None | File ops, remote reconnect |
| Exponential with Jitter | 2x | +/-10% | GitHub PR refresh |
| Step Delays | [0,5,5,10...30] | None | Remote connection |
| Slow Growth | 1.5x | None | Wait for changes |
| Fixed Interval | 1x | +/-10% | Classification, stats polling |

---

## Key Source Locations

| Component | Line Range | Description |
|-----------|------------|-------------|
| Background Agent Config | 295107-295116 | Polling delay schema |
| Generic Retry Utility | 300136-300153 | Exponential backoff implementation |
| GitHub PR Auto-Refresh | 444830-445091 | Backoff with jitter |
| Usage Data Service | 299010-299090 | Refresh/retry intervals |
| Classification Polling | 939943-940010 | 10-minute polling cycle |
| Commit Polling | 954398-954452 | Git tracking interval |
| Proclist Polling | 1170560-1170617 | Configurable polling |
| Manual Login | 1098180-1098217 | Short-lived auth polling |
| Remote Reconnection | 1082499-1082665 | Progressive delay sequence |
| Rate Limit Handling | 888390-888442 | HTTP 429 response handling |
| Terminal Retry | 1165490-1165504 | Extension host retry |
| Idempotent Resume | 945190-945231 | Stream auto-resume window |

---

## Recommendations for Further Investigation

1. **TASK: Analyze adaptive polling based on response patterns** - The description mentioned "adaptive polling" but explicit adaptive mechanisms weren't found; may be server-driven
2. **TASK: Document server-side polling configuration endpoints** - How server configs like `clientStatsigPollIntervalMs` are populated
3. **TASK: Map poll request throttling under load** - Investigate if there's load-based throttling beyond rate limiting

---

## Conclusion

Cursor implements a comprehensive polling and backoff strategy that balances responsiveness with server load management. Key patterns include:

1. **Configurable intervals** - Most polling intervals are server-configurable via Statsig dynamic configs
2. **Jitter for load distribution** - Critical polling systems use +/- 10-20% jitter to prevent thundering herd
3. **Exponential backoff** - Failure scenarios use 2x multiplier with configurable caps
4. **Progressive delays** - Remote connection uses a step function for more controlled retry timing
5. **Grace periods** - Long-running operations have extended grace periods (e.g., 3 hours for remote reconnection)
6. **Rate limit respect** - Both local rate limiting and server-provided `Retry-After` headers are honored
