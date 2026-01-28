# TASK-79: Client-Side Failover Opportunities for Agent Endpoints

## Executive Summary

Cursor IDE 2.3.41 has multiple endpoint failover mechanisms, but they are primarily server-controlled through experiments/feature flags rather than client-autonomous. The client does implement retry logic with exponential backoff, but true endpoint failover (switching to alternative servers on failure) is limited.

## Key Findings

### 1. Agent Endpoint Architecture

The client maintains multiple agent endpoint configurations based on region and privacy settings:

**Production Endpoints (from line 182746):**
```javascript
// Privacy-enabled endpoints
u6t = "https://agent.api5.cursor.sh"        // Default
h6t = "https://agent-gcpp-uswest.api5.cursor.sh"  // US-West-1

// Non-privacy endpoints
d6t = "https://agentn.api5.cursor.sh"       // Default
f6t = "https://agentn-gcpp-uswest.api5.cursor.sh" // US-West-1

// EU Central endpoints
qEl = "https://agent-gcpp-eucentral.api5.cursor.sh"
JEl = "https://agentn-gcpp-eucentral.api5.cursor.sh"
```

**Other Backend URLs:**
```javascript
mue = "https://api2.cursor.sh"      // Main backend
DNe = "https://api3.cursor.sh"      // Telemetry
rcs = "https://api4.cursor.sh"      // Geo CPP
ocs = "https://api3.cursor.sh"      // CmdK backend
```

### 2. Retry Interceptor Mechanism

The client implements a server-controlled retry mechanism via HTTP headers (line 300961-300966):

```javascript
function dtc(i, e) {
    if (!i) return {};
    const t = {
        "X-Cursor-RetryInterceptor-Enabled": "true"
    };
    if (e?.maxRetries !== void 0)
        t["X-Cursor-RetryInterceptor-MaxRetries"] = String(e.maxRetries);
    if (e?.baseDelayMs !== void 0)
        t["X-Cursor-RetryInterceptor-BaseDelayMs"] = String(e.baseDelayMs);
    if (e?.maxDelayMs !== void 0)
        t["X-Cursor-RetryInterceptor-MaxDelayMs"] = String(e.maxDelayMs);
    return t
}
```

**Configuration via Experiment Service (line 556947-556954):**
```javascript
d = this.experimentService.checkFeatureGate("retry_interceptor_enabled_for_streaming"),
h = this.experimentService.getDynamicConfig("retry_interceptor_params_config"),
f = {
    maxRetries: h.maxRetries,
    baseDelayMs: h.baseDelayMs,
    maxDelayMs: h.maxDelayMs
}
```

### 3. Retryable Error Codes

**HTTP Status Codes (line 292463):**
```javascript
cec = new Set([408, 500, 502, 503, 504, 522, 524, 599])
```

**gRPC Error Codes (line 295473-295479):**
```javascript
retriableErrors: [{
    code: "Unavailable"
}, {
    code: "Internal"
}, {
    code: "DeadlineExceeded"
}]
```

### 4. Exponential Backoff Implementation

From NetworkCore.js (line 292458):
```javascript
// Exponential backoff with max delay
async function Lbh(i) {
    await new Promise(e => setTimeout(e, Math.min(rec * (i * i), oec)))
}
// rec = 500ms base, oec = 30000ms max
```

### 5. Statsig Fallback URL System

A sophisticated fallback URL mechanism exists for Statsig SDK endpoints (line 292224-292304):

**Key Features:**
- DNS-based fallback URL discovery
- URL checksum validation
- Expiry time management (H7r = 10080 * 60 * 1000 = 7 days)
- Previous URL tracking to avoid repeating failed URLs
- Cooldown period for DNS queries (YZl = 14400 * 1000 = 4 hours)

**Limitations:**
- Only applies to Statsig SDK endpoints, NOT agent endpoints
- Agent endpoints don't use this fallback mechanism

### 6. Idempotent Streaming with Reconnection

The client supports idempotent streaming for reliable message delivery (lines 488859-488960):

**Key Headers:**
```javascript
headers: {
    "x-idempotency-key": d,
    "x-idempotency-event-id": f,
    "x-idempotent-encryption-key": h
}
```

**Reconnection Logic:**
- On error (non-abort), sets `isReconnecting: true`
- Waits 1 second before retry: `await new Promise(A => setTimeout(A, 1e3))`
- Degraded mode detection disables reconnection
- Playback chunks allow resuming from last acknowledged sequence number

**Configuration:**
```javascript
idempotent_stream_config: {
    retry_lookback_window_ms: 7200 * 1000  // 2 hours
}
```

### 7. Region-Based Endpoint Selection

The client maps endpoints by region (line 440802-440830):

```javascript
getAgentBackendUrls(e) {
    // For localhost/dev environments
    if (e.includes("localhost") || e.includes("lclhst.build")) {
        return { privacy: { default: e, "us-west-1": e },
                 nonPrivacy: { default: e, "us-west-1": e } }
    }
    // For staging
    if (e.includes(mB) || e.includes(hbe)) {
        return { privacy: { default: e, "us-west-1": e },
                 nonPrivacy: { default: e, "us-west-1": e } }
    }
    // For production - uses geo-based endpoints
    return {
        privacy: { default: u6t, "us-west-1": h6t },
        nonPrivacy: { default: d6t, "us-west-1": f6t }
    }
}
```

### 8. Manual Server Switching (Developer Feature)

Users can manually switch between server configurations (line 440493-440505):
- PROD
- PROD_EU_CENTRAL_1_AGENT
- STAGING
- Various local/dev configurations

## Failover Gaps and Opportunities

### Current Limitations

1. **No Automatic Agent Endpoint Failover**: Unlike Statsig endpoints, agent endpoints don't have automatic failover to alternative servers when primary fails.

2. **Region Selection is Static**: The client doesn't dynamically switch regions based on latency or availability.

3. **Server-Controlled Retry Parameters**: Retry behavior is controlled by server-side experiments, limiting client autonomy.

4. **No Circuit Breaker Pattern**: The client lacks circuit breaker logic to temporarily avoid endpoints that are repeatedly failing.

5. **Limited Error Recovery**: The `isRetryable` flag on errors is largely server-controlled via `FA.details.isRetryable`.

### Potential Client-Side Improvements

1. **Agent Endpoint Fallback Chain**: Similar to Statsig's fallback URL system, implement cascading failover for agent endpoints:
   - Primary: `agent.api5.cursor.sh`
   - Fallback 1: `agent-gcpp-uswest.api5.cursor.sh`
   - Fallback 2: `agent-gcpp-eucentral.api5.cursor.sh`

2. **Latency-Based Routing**: Measure and cache endpoint latencies to prefer faster endpoints.

3. **Circuit Breaker Implementation**: Track failure rates per endpoint and temporarily exclude failing endpoints.

4. **Client-Side Retry Overrides**: Allow configuration to override server-provided retry parameters in emergencies.

5. **Health Check Endpoint**: Implement periodic lightweight health checks to proactively detect endpoint issues.

## Connection Error Handling Patterns

### Error Types Detected (line 1082642):
```javascript
if ((r.code === "ETIMEDOUT" || r.code === "ENETUNREACH" ||
     r.code === "ECONNREFUSED" || r.code === "ECONNRESET") &&
    r.syscall === "connect") {
    // Connection-level failure handling
}
```

### Error Message Fallback (line 705112):
```javascript
mt += "Connection failed. If the problem persists, please check your internet connection or VPN"
```

## Relevant Code Locations

| Component | Line Range | Description |
|-----------|------------|-------------|
| Endpoint definitions | 182746-182876 | Production endpoint URLs |
| NetworkCore retry | 292463-292553 | Exponential backoff implementation |
| Retry interceptor headers | 300961-300966 | X-Cursor-RetryInterceptor headers |
| Experiment config | 295470-295510 | Retry and idempotent stream configs |
| AgentClientService | 556941-556976 | Agent client with retry headers |
| Idempotent streaming | 488772-488960 | Reconnection and playback logic |
| Server switching | 440475-440831 | Manual server configuration |
| Statsig fallback | 292224-292304 | DNS-based fallback system |

## Recommendations for Investigation

1. **Investigate Statsig Fallback Pattern**: The NetworkFallbackResolver (XZl class) implements a robust fallback system that could be adapted for agent endpoints.

2. **Analyze Experiment Gates**: The feature gates `retry_interceptor_enabled_for_streaming` and `persist_idempotent_stream_state` control key behaviors.

3. **Monitor Connection Telemetry**: The `connectionErrorRaw` field (line 541627) captures raw error details for analysis.

4. **Review Background Composer Resilience**: The `disable_infinite_cloud_agent_stream_retries` experiment suggests ongoing work on retry limits.

## File Reference

Analysis based on:
- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
- File size: 1,171,817 lines
