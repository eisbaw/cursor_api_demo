# TASK-24: Geographic Endpoint Routing Logic Analysis

## Overview

This analysis documents how Cursor selects geographic endpoints for its Agent API (`api5.cursor.sh`). The investigation reveals that **the current implementation does NOT use latency-based routing** - instead it uses a **configuration-based static endpoint selection** determined at build/startup time.

## Endpoint URL Mapping

### Production Agent Endpoints

| Variable | URL | Privacy | Region |
|----------|-----|---------|--------|
| `u6t` | https://agent.api5.cursor.sh | Yes (Privacy Pod) | Default |
| `d6t` | https://agentn.api5.cursor.sh | No | Default |
| `h6t` | https://agent-gcpp-uswest.api5.cursor.sh | Yes (Privacy Pod) | US West |
| `f6t` | https://agentn-gcpp-uswest.api5.cursor.sh | No | US West |
| `qEl` | https://agent-gcpp-eucentral.api5.cursor.sh | Yes (Privacy Pod) | EU Central |
| `JEl` | https://agentn-gcpp-eucentral.api5.cursor.sh | No | EU Central |

**Source:** Line 182746 in `beautified/workbench.desktop.main.js`

### URL Naming Convention

- **`agent.*`** = Privacy mode enabled (no data storage)
- **`agentn.*`** = Non-privacy mode ("n" = normal/non-privacy)
- **`gcpp`** = GCP Pod (Google Cloud Platform deployment)
- **`-uswest`** = US West region
- **`-eucentral`** = EU Central region

## Endpoint Selection Logic

### 1. Configuration Structure

The client stores endpoints in a map structure with region keys:

```javascript
// Line 182867-182874
agentBackendUrlPrivacy: {
    default: "https://agent.api5.cursor.sh",       // u6t
    "us-west-1": "https://agent-gcpp-uswest.api5.cursor.sh"  // h6t
}
agentBackendUrlNonPrivacy: {
    default: "https://agentn.api5.cursor.sh",      // d6t
    "us-west-1": "https://agentn-gcpp-uswest.api5.cursor.sh" // f6t
}
```

### 2. Backend Mode Selection (getAgentBackendUrls function)

**Location:** Line 440802-440830

```javascript
getAgentBackendUrls(e) {
    // Local development - use localhost for all regions
    if (e.includes("localhost") || e.includes("lclhst.build")) {
        return {
            privacy: { default: e, "us-west-1": e },
            nonPrivacy: { default: e, "us-west-1": e }
        };
    }

    // Staging environments - use staging URL for all regions
    if (e.includes(stagingUrl) || e.includes(devStagingUrl)) {
        return {
            privacy: { default: e, "us-west-1": e },
            nonPrivacy: { default: e, "us-west-1": e }
        };
    }

    // Production - use geographic endpoints
    return {
        privacy: {
            default: u6t,           // agent.api5.cursor.sh
            "us-west-1": h6t        // agent-gcpp-uswest.api5.cursor.sh
        },
        nonPrivacy: {
            default: d6t,           // agentn.api5.cursor.sh
            "us-west-1": f6t        // agentn-gcpp-uswest.api5.cursor.sh
        }
    };
}
```

### 3. EU Central Mode (Explicit Selection)

**Location:** Line 440568-440588

The EU Central configuration is a **developer/admin option** that explicitly overrides to EU endpoints:

```javascript
switchToProdEuCentral1AgentServer() {
    // Only has 'default' key - no regional fallback
    agentBackendUrlPrivacy: { default: qEl },     // EU Central privacy
    agentBackendUrlNonPrivacy: { default: JEl }   // EU Central non-privacy
}
```

## Key Finding: No Automatic Geographic Routing

### What the Code Shows

1. **No Latency Measurement:** There is no code that measures ping/latency to endpoints
2. **No IP Geolocation:** No client-side IP geolocation to determine user location
3. **No DNS-based Routing:** The client hardcodes specific endpoints
4. **Static Region Key:** The "us-west-1" key exists but no code was found that selects between "default" and "us-west-1"

### Probable Routing Architecture

Based on the endpoint structure, the **actual geographic routing likely happens server-side**:

1. **`default` endpoints** (`agent.api5.cursor.sh`, `agentn.api5.cursor.sh`) - Likely use DNS-based geo-routing or anycast to route to nearest region
2. **`-gcpp-uswest` endpoints** - Direct connection to US West GCP deployment
3. **`-gcpp-eucentral` endpoints** - Direct connection to EU Central GCP deployment

The `"us-west-1"` key in the client config appears to be **infrastructure for future explicit region selection** that is not yet actively used in production.

## Privacy Mode Selection

### How Privacy Mode Affects Endpoint

**Location:** Line 1098400-1098429

```javascript
shouldHaveGhostModeFromEnterprise() {
    // Enterprise teams can force privacy mode
    if (membershipType === ENTERPRISE) {
        if (teamPrivacyModeForced) {
            return { privacyModeForced: true, privacyMode: NO_STORAGE };
        }
    }
    return userPrivacySettings;
}

reactivePrivacyMode() {
    const noStorageMode = applicationStorage.noStorageMode;
    if (membershipType === ENTERPRISE) {
        if (shouldHaveGhostModeFromEnterprise().privacyModeForced) {
            setNoStorageMode(true);
            return true;
        }
    }
    return noStorageMode;
}
```

When privacy mode is enabled:
- Uses `agent.*` endpoints (privacy pods)
- Server responds with `isOnPrivacyPod: true`
- No data is stored/used for training

## Retry/Fallback Mechanisms

### Retry Interceptor (Server-Side)

**Location:** Line 556947-556955

The client can request server-side retries via headers:

```javascript
const retryConfig = experimentService.getDynamicConfig("retry_interceptor_params_config");
const headers = {
    "X-Cursor-RetryInterceptor-Enabled": "true",
    "X-Cursor-RetryInterceptor-MaxRetries": retryConfig.maxRetries,
    "X-Cursor-RetryInterceptor-BaseDelayMs": retryConfig.baseDelayMs,
    "X-Cursor-RetryInterceptor-MaxDelayMs": retryConfig.maxDelayMs
};
```

### Client-Side Fallback

**Finding:** No client-side geographic fallback mechanism was found. If a regional endpoint fails, the client does not automatically try another region.

## Backend Switching (Dev/Admin Feature)

**Location:** Line 440845-440885

A developer feature allows explicit backend switching:

| Mode | Key Binding | Description |
|------|-------------|-------------|
| Prod | 1814 | Standard production (default + us-west-1) |
| ProdEuCentral1Agent | 1813 | Force EU Central endpoints |
| Staging | 1815 | Use staging.cursor.sh |
| DevStaging | 1821 | Use dev-staging.cursor.sh |
| LocalExceptCppAndEmbeddings | 1817 | localhost:8000 |

These are gated behind developer/admin context keys and not available to regular users.

## Architecture Summary

```
User Request
    |
    v
Privacy Mode Check (noStorageMode)
    |
    +-- Privacy ON  --> Use agentBackendUrlPrivacy
    |                       |
    +-- Privacy OFF --> Use agentBackendUrlNonPrivacy
                            |
                            v
                    Get URL from map["default"]
                            |
                            v
                    Connect to endpoint
                    (Server handles actual geo-routing)
```

## Open Questions / Further Investigation Needed

1. **Server-Side Geo-Routing:** How does `agent.api5.cursor.sh` route requests to different regions? (DNS, anycast, load balancer)

2. **"us-west-1" Key Usage:** Is there planned functionality to allow users to select explicit regions?

3. **Endpoint Health Checks:** Does the server-side retry interceptor include cross-region failover?

4. **Latency Metrics:** Are latency metrics collected for endpoint performance analysis?

## Recommendations

1. **Client-side geo-routing could improve latency** - Measure latency to each endpoint and select fastest
2. **Add explicit region selection UI** - Allow users in EU to force EU endpoints
3. **Implement client-side failover** - If primary endpoint fails, try alternative region

---

## Files Referenced

- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
  - Line 182746: URL constant definitions
  - Line 182867-182874: agentBackendUrl default configuration
  - Line 440476-440887: cursorCredsService with backend switching
  - Line 440802-440830: getAgentBackendUrls function
  - Line 556940-556977: AgentClientService with retry interceptor
  - Line 1098400-1098429: Privacy mode determination

## Related Tasks

- TASK-1: Agent API analysis (prior work)
