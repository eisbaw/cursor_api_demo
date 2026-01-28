# TASK-77: Server-Side Geo-Routing for agent.api5.cursor.sh

## Executive Summary

This analysis investigates how Cursor's agent API endpoints (`agent.api5.cursor.sh` and variants) implement geographic routing. The key finding is that **geo-routing is primarily server-side, not client-side**. The client connects to a single default endpoint, and the server infrastructure (likely Cloudflare/GCP load balancing) routes requests to the nearest regional backend.

## Endpoint Architecture

### Production Agent Endpoints (Line 182746)

| Variable | URL | Privacy Mode | Region |
|----------|-----|--------------|--------|
| `u6t` | `https://agent.api5.cursor.sh` | Privacy (No Storage) | Default (Geo-routed) |
| `d6t` | `https://agentn.api5.cursor.sh` | Non-Privacy | Default (Geo-routed) |
| `h6t` | `https://agent-gcpp-uswest.api5.cursor.sh` | Privacy | US West (Direct) |
| `f6t` | `https://agentn-gcpp-uswest.api5.cursor.sh` | Non-Privacy | US West (Direct) |
| `qEl` | `https://agent-gcpp-eucentral.api5.cursor.sh` | Privacy | EU Central (Direct) |
| `JEl` | `https://agentn-gcpp-eucentral.api5.cursor.sh` | Non-Privacy | EU Central (Direct) |

### URL Naming Convention Analysis

- **`agent.*`** - Privacy mode endpoint (routes to privacy pods with no data storage)
- **`agentn.*`** - Non-privacy mode endpoint ("n" = normal)
- **`gcpp`** - GCP Pod (Google Cloud Platform regional deployment)
- **`-uswest`** - US West specific region
- **`-eucentral`** - EU Central specific region

### Key Insight: Default vs Regional Endpoints

The **default endpoints** (`agent.api5.cursor.sh`, `agentn.api5.cursor.sh`) do NOT include regional suffixes. This strongly suggests they use **server-side anycast or DNS-based geo-routing** to direct traffic to the nearest regional deployment.

The **regional endpoints** (`-gcpp-uswest`, `-gcpp-eucentral`) are **explicit regional overrides** that bypass geo-routing and connect directly to a specific region.

## Client-Side Configuration

### Agent Backend URL Structure (Line 182867-182874)

The client stores endpoints in a map structure supporting region keys:

```javascript
cursorCreds: {
    agentBackendUrlPrivacy: {
        default: "https://agent.api5.cursor.sh",
        "us-west-1": "https://agent-gcpp-uswest.api5.cursor.sh"
    },
    agentBackendUrlNonPrivacy: {
        default: "https://agentn.api5.cursor.sh",
        "us-west-1": "https://agentn-gcpp-uswest.api5.cursor.sh"
    }
}
```

### URL Selection Function (Line 440802-440830)

```javascript
getAgentBackendUrls(backendUrl) {
    // Local development - all regions point to localhost
    if (backendUrl.includes("localhost") || backendUrl.includes("lclhst.build")) {
        return {
            privacy: { default: backendUrl, "us-west-1": backendUrl },
            nonPrivacy: { default: backendUrl, "us-west-1": backendUrl }
        };
    }

    // Staging environments - all regions point to staging
    if (backendUrl.includes(stagingUrl) || backendUrl.includes(devStagingUrl)) {
        return {
            privacy: { default: backendUrl, "us-west-1": backendUrl },
            nonPrivacy: { default: backendUrl, "us-west-1": backendUrl }
        };
    }

    // Production - return standard geo-enabled endpoints
    return {
        privacy: {
            default: "https://agent.api5.cursor.sh",      // u6t
            "us-west-1": "https://agent-gcpp-uswest.api5.cursor.sh"  // h6t
        },
        nonPrivacy: {
            default: "https://agentn.api5.cursor.sh",     // d6t
            "us-west-1": "https://agentn-gcpp-uswest.api5.cursor.sh" // f6t
        }
    };
}
```

**Critical Finding:** The function always returns the map with `default` and `us-west-1` keys, but **the client code always uses the `default` key** for production. The `us-west-1` key appears to be infrastructure for future explicit region selection.

### EU Central Override (Line 440568-440588)

The EU Central configuration is a **developer/admin-only feature** accessible via `cursor.selectBackend` command:

```javascript
switchToProdEuCentral1AgentServer() {
    agentBackendUrlPrivacy: { default: qEl },     // EU Central privacy only
    agentBackendUrlNonPrivacy: { default: JEl }   // EU Central non-privacy only
}
```

Note: EU Central mode has **no regional fallback** - only a `default` key that points directly to EU endpoints.

## Server-Side Region Response Header

### `x-cursor-server-region` Header (Line 490103-490104)

The server returns the actual region handling the request:

```javascript
const handleHeader = (headers) => {
    const serverRegion = headers.get("x-cursor-server-region");
    if (serverRegion) {
        region = serverRegion;
        span?.setAttribute("server.region", serverRegion);
    }
};
```

This header is used for:
1. **Metrics/telemetry tagging** - Track which region served each request
2. **OpenTelemetry tracing** - Attribute `server.region` on spans
3. **Debugging** - Verify geo-routing is working correctly

### Metrics Integration (Line 490091-490098)

```javascript
this._metricsService.distribution({
    stat: "composer.submitChat.ttftActual",
    value: timeToFirstTokenMs,
    tags: {
        model: modelName,
        chatService: isNAL ? "agent" : "agentic-composer",
        ...region ? { region: region } : {}  // Region from x-cursor-server-region
    }
});
```

## Server-Side Geo-Routing Mechanism

### Hypothesis: DNS-Based Anycast

The default endpoints (`agent.api5.cursor.sh`) likely use one of these routing mechanisms:

1. **Cloudflare Anycast** - Cloudflare routes to nearest PoP, which proxies to nearest GCP region
2. **GCP Global Load Balancer** - Uses anycast IP with automatic geo-routing
3. **DNS-based routing** - GeoDNS returns different IPs based on client location

### Evidence Supporting Server-Side Routing

1. **No latency measurement code** - Client doesn't ping endpoints to select fastest
2. **No IP geolocation code** - Client doesn't determine user location
3. **Single default endpoint used** - Client always connects to same hostname
4. **Server returns region header** - Server knows which region handled request
5. **Cloudflare reference in code** - Line 251008 checks for Cloudflare runtime

### Regional Backend Infrastructure

Based on endpoint naming:

| Region | Privacy Endpoint | Non-Privacy Endpoint | Infrastructure |
|--------|-----------------|---------------------|----------------|
| Default (Geo-routed) | agent.api5.cursor.sh | agentn.api5.cursor.sh | Global LB |
| US West | agent-gcpp-uswest.api5.cursor.sh | agentn-gcpp-uswest.api5.cursor.sh | GCP us-west |
| EU Central | agent-gcpp-eucentral.api5.cursor.sh | agentn-gcpp-eucentral.api5.cursor.sh | GCP europe-west |

## Privacy Mode Endpoint Selection

### Selection Logic

The client selects privacy vs non-privacy endpoints based on user/team privacy settings:

```javascript
// Simplified selection logic
const usePrivacyEndpoint = (
    privacyMode === NO_STORAGE ||
    privacyMode === NO_TRAINING ||
    teamPrivacyModeForced
);

const endpointMap = usePrivacyEndpoint
    ? cursorCreds.agentBackendUrlPrivacy
    : cursorCreds.agentBackendUrlNonPrivacy;

const endpoint = endpointMap["default"];  // Always uses default key
```

### Privacy Pod Verification

The server confirms privacy pod routing via gRPC response:

```javascript
// PrivacyCheckResponse protobuf (Line 165511-165530)
{
    isOnPrivacyPod: boolean,  // True if routed to privacy infrastructure
    isGhostModeOn: boolean    // True if ghost/no-storage mode active
}
```

## Migration from Legacy Configuration

### String-to-Map Migration (Line 183009-183024)

The client includes migration logic for older configs that stored endpoints as strings:

```javascript
// Migration: convert string to map structure
if (typeof cursorCreds.agentBackendUrlPrivacy === "string") {
    const url = cursorCreds.agentBackendUrlPrivacy;
    const usWest = (url === defaultPrivacyUrl) ? usWestPrivacyUrl : url;
    cursorCreds.agentBackendUrlPrivacy = {
        default: url,
        "us-west-1": usWest
    };
}
```

### Legacy Region Name Migration (Line 183031-183045)

```javascript
// Migration: rename "Prod (us-west-1 agent)" to "Prod"
if (cursorCreds.credentialsDisplayName === "Prod (us-west-1 agent)") {
    cursorCreds.credentialsDisplayName = "Prod";
    cursorCreds.agentBackendUrlPrivacy = {
        default: defaultPrivacyUrl,
        "us-west-1": usWestPrivacyUrl
    };
}
```

This suggests an earlier version had explicit "us-west-1" as a user-selectable option that was removed.

## Retry and Fallback Mechanisms

### Server-Side Retry Interceptor

The client can request server-side retries via headers:

```javascript
const headers = {
    "X-Cursor-RetryInterceptor-Enabled": "true",
    "X-Cursor-RetryInterceptor-MaxRetries": config.maxRetries,
    "X-Cursor-RetryInterceptor-BaseDelayMs": config.baseDelayMs,
    "X-Cursor-RetryInterceptor-MaxDelayMs": config.maxDelayMs
};
```

### No Client-Side Geographic Failover

**Finding:** No code was found that implements client-side geographic failover. If the default endpoint fails, the client does NOT automatically try a regional endpoint.

## Backend Switching (Developer Feature)

### Available Modes (Line 440478-440488)

| Mode | Display Name | Purpose |
|------|-------------|---------|
| PROD | Prod | Standard production (geo-routed default) |
| PROD_EU_CENTRAL_1_AGENT | Prod (eu-central-1 agent) | Force EU Central region |
| STAGING | Staging | staging.cursor.sh |
| DEV_STAGING | DevStaging(w/local-website) | dev-staging.cursor.sh |
| LOCAL_* | Various local modes | localhost development |

### Access Control

Backend switching requires developer context key:

```javascript
precondition: he.or(jw, yU)  // Developer context or extension development
```

Regular users cannot access backend switching; it's only available in dev builds or with developer flag enabled.

## Summary: Geo-Routing Architecture

```
User Request
    |
    v
Privacy Mode Check
    |
    +-- Privacy ON  --> agentBackendUrlPrivacy["default"]
    |                        |
    +-- Privacy OFF --> agentBackendUrlNonPrivacy["default"]
                             |
                             v
                    agent.api5.cursor.sh (or agentn.*)
                             |
                             v
                    [Server-Side Geo-Routing]
                    (Cloudflare/GCP Load Balancer)
                             |
              +--------------+--------------+
              |              |              |
              v              v              v
         US West        EU Central      Other Regions
          GCP Pod         GCP Pod          ...
              |              |
              v              v
        Response with x-cursor-server-region header
```

## Open Questions

1. **Exact routing technology** - Is it Cloudflare, GCP GLB, or custom DNS?
2. **Region list completeness** - Are there more regions beyond US West and EU Central?
3. **Failover behavior** - Does the server-side LB failover between regions?
4. **Latency-based selection** - Does routing consider latency or just geography?
5. **`us-west-1` key purpose** - Future feature for explicit region selection?

## Recommendations for Reverse Engineering

1. **DNS analysis** - Resolve agent.api5.cursor.sh from different geographic locations
2. **Header inspection** - Log x-cursor-server-region values from different locations
3. **Network tracing** - Trace actual IP addresses/routes to endpoints
4. **A/B comparison** - Compare default vs explicit regional endpoint latencies

## Files Referenced

- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
  - Line 182746: Endpoint URL constant definitions
  - Line 182867-182874: Default credential configuration
  - Line 183009-183045: Migration logic
  - Line 440476-440832: cursorCredsService with backend switching
  - Line 490102-490104: x-cursor-server-region header processing
  - Line 165511-165530: PrivacyCheckResponse protobuf

## Related Tasks

- TASK-24: Geographic Endpoint Routing Logic Analysis (prior work)
- TASK-76: Privacy Mode System and Team/Enterprise Overrides
- TASK-1: Agent API analysis
