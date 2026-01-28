# TASK-6: Cursor 2.3.41 HTTP Headers Analysis

## Overview

This document analyzes the `x-cursor-*` HTTP headers discovered in Cursor version 2.3.41. These headers are injected via the `Gyh` function (deobfuscated: `setCommonHeaders`) located around line 268885 in `workbench.desktop.main.js`.

## Header Injection Function

The main header injection happens in function `Gyh` (lines 268885-268917):

```javascript
function Gyh({
    req: i,
    machineId: e,
    macMachineId: t,
    base64Fn: n,
    cursorVersion: s,
    privacyMode: r,
    eligibleForSnippetLearning: o,
    backupRequestId: a,
    clientKey: l,
    sessionId: d,
    configVersion: h,
    isAnysphereUser: f,
    clientOs: g,
    clientArch: p,
    clientOsVersion: w
})
```

This function is called by `setCommonHeaders` method (line 1098807) in the authentication service class.

---

## Header Definitions

### 1. x-cursor-client-version (Ydt)

**Value Source:** `productService.version`
**Type:** String
**Always Set:** Yes

```javascript
i.header.set(Ydt, s)  // Ydt = "x-cursor-client-version"
```

The Cursor IDE version string (e.g., "2.3.41").

---

### 2. x-cursor-client-type

**Value:** `"ide"` (hardcoded)
**Type:** String literal
**Always Set:** Yes

```javascript
i.header.set("x-cursor-client-type", "ide")
```

Identifies the client as the IDE (as opposed to web or other clients).

---

### 3. x-cursor-client-os

**Value Source:** `process.platform`
**Type:** String (e.g., "darwin", "win32", "linux")
**Conditionally Set:** Only if `clientOs !== undefined`

```javascript
g !== void 0 && i.header.set("x-cursor-client-os", g)
```

Where `g` comes from `dVe = tW?.platform` (line 10123), and `tW` is an alias for `process`.

---

### 4. x-cursor-client-arch

**Value Source:** `process.arch`
**Type:** String (e.g., "x64", "arm64")
**Conditionally Set:** Only if `clientArch !== undefined`

```javascript
p !== void 0 && i.header.set("x-cursor-client-arch", p)
```

Where `p` comes from `n0e = tW?.arch` (line 10123).

---

### 5. x-cursor-client-os-version

**Value Source:** Not directly set in the main header function
**Type:** String
**Conditionally Set:** Only if `clientOsVersion !== undefined`

```javascript
w !== void 0 && i.header.set("x-cursor-client-os-version", w)
```

Note: In the current call site at line 1098807, `clientOsVersion` is NOT passed to the function, so this header may not be set in practice.

---

### 6. x-cursor-client-device-type

**Value:** `"desktop"` (hardcoded)
**Type:** String literal
**Always Set:** Yes

```javascript
i.header.set("x-cursor-client-device-type", "desktop")
```

Identifies the device type. Currently always "desktop" for the IDE.

---

### 7. x-cursor-canary

**Value:** `"true"` (conditional)
**Type:** String literal
**Conditionally Set:** Only when `isAnysphereUser` is true

```javascript
f && i.header.set("x-cursor-canary", "true")
```

Set for Anysphere (Cursor's parent company) employees. Determined by:
```javascript
isAnysphereUser() {
    return this._reactiveStorageService.applicationUserPersistentStorage.aiSettings.teamIds?.includes(1) ?? !1
}
```

Team ID `1` is the Anysphere internal team.

---

### 8. x-cursor-config-version

**Value Source:** `serverConfigService.cachedServerConfig.configVersion`
**Type:** String
**Conditionally Set:** Only if `configVersion !== undefined && configVersion !== ""`

```javascript
h !== void 0 && h !== "" && i.header.set("x-cursor-config-version", h)
```

Note: In the current call site at line 1098807, `configVersion` is NOT passed, so this header may not be set via `setCommonHeaders`.

---

### 9. x-cursor-timezone

**Value Source:** `Intl.DateTimeFormat().resolvedOptions().timeZone`
**Type:** String (e.g., "America/Los_Angeles", "Europe/London")
**Always Set:** Yes (wrapped in try-catch)

```javascript
try {
    const _ = Intl.DateTimeFormat().resolvedOptions().timeZone;
    i.header.set("x-cursor-timezone", _)
} catch {}
```

Uses the browser/Node.js Intl API to get the user's timezone.

---

### 10. x-cursor-server-region (RESPONSE HEADER)

**Direction:** Server -> Client (response header)
**Used at:** Line 490103

```javascript
const Uh = uu.get("x-cursor-server-region");
Uh && (jo = Uh, rt && rt.setAttribute("server.region", Uh))
```

This is a **response** header, not a request header. The client reads it to track which server region handled the request for telemetry/tracing purposes.

---

### 11. application/x-cursor-log (MIME TYPE)

**Location:** Line 477267
**Usage:** Resource link MIME type, not an HTTP header

```javascript
if (M.type === "resource_link" && M.mimeType === "application/x-cursor-log" && M.description)
```

This is a MIME type used for log file attachments in MCP (Model Context Protocol) responses, not an HTTP header.

---

## Related Headers (Not x-cursor-* prefixed)

These headers are set alongside the x-cursor headers:

### x-cursor-checksum

**Computation:** Complex checksum combining timestamp and machine IDs

```javascript
const _ = Math.floor(Date.now() / 1e6),
    E = new Uint8Array([_ >> 40 & 255, _ >> 32 & 255, _ >> 24 & 255, _ >> 16 & 255, _ >> 8 & 255, _ & 255]),
    T = Jyh(E),  // XOR cipher with rolling key
    D = n(T);    // base64 encode
i.header.set("x-cursor-checksum", t === void 0 ? `${D}${e}` : `${D}${e}/${t}`)
```

Format: `{base64_timestamp}{machineId}` or `{base64_timestamp}{machineId}/{macMachineId}`

### x-session-id (Q$l)

**Value Source:** `cppSessionId`

### x-ghost-mode (sJe)

**Value Source:** `nJe(privacyMode)`
**Possible Values:** `"true"`, `"false"`, `"implicit-false"`

```javascript
function nJe(i) {
    if (i === !0) return "true";
    if (i === !1) return "false";
    if (i === void 0) return "implicit-false";
    // fallback
    return "true"
}
```

### x-new-onboarding-completed (rJe)

**Value:** `"true"` or `"false"`
**Computation:** `(eligibleForSnippetLearning && privacyMode === false).toString()`

### x-client-key (X$l)

**Value Source:** `clientKey` parameter

### x-request-id / x-amzn-trace-id

**Value Source:** `backupRequestId`
**Format for trace ID:** `Root=${backupRequestId}`

### traceparent (GVe)

**Value Source:** `Drt()` function
**Standard:** W3C Trace Context

---

## Endpoints Using These Headers

### gRPC/Connect-ES Endpoints (via setCommonHeaders)

All gRPC streaming endpoints through the Connect-ES transport receive headers via the `setCommonHeaders` method:
- `api2.cursor.sh` - Main API
- `api3.cursor.sh` - Additional services
- `api4.cursor.sh` - Additional services
- `agent.api5.cursor.sh` - Agent backend
- `agentn.api5.cursor.sh` - Agent backend (NAL)
- `agent-gcpp-uswest.api5.cursor.sh` - Regional agent (US West)
- `agent-gcpp-eucentral.api5.cursor.sh` - Regional agent (EU Central)

### REST/Fetch Endpoints (subset of headers)

The following endpoints use a subset of headers:

1. **Auth endpoints** (`/auth/*`):
   - `/auth/full_stripe_profile`
   - `/auth/stripe_profile`
   - `/auth/has_valid_payment_method`
   - Polling endpoint

   Headers used:
   - `x-ghost-mode`
   - `x-new-onboarding-completed`
   - `traceparent`
   - `x-cursor-client-version`

2. **Marketplace endpoints** (Cursor extensions):
   - `x-cursor-client-version` only

---

## Summary Table

| Header | Value Source | Always Set | Notes |
|--------|-------------|------------|-------|
| x-cursor-client-version | productService.version | Yes | |
| x-cursor-client-type | "ide" | Yes | Hardcoded |
| x-cursor-client-os | process.platform | Conditional | |
| x-cursor-client-arch | process.arch | Conditional | |
| x-cursor-client-os-version | (not passed) | Conditional | Currently unused |
| x-cursor-client-device-type | "desktop" | Yes | Hardcoded |
| x-cursor-canary | "true" | Conditional | Anysphere employees only |
| x-cursor-config-version | serverConfig | Conditional | Currently unused in main call |
| x-cursor-timezone | Intl API | Yes | |
| x-cursor-server-region | (response) | N/A | Server response header |

---

## Open Questions / Future Investigation

1. **x-cursor-client-os-version**: The parameter exists but is not passed in the main call site. Investigate if there are other call sites or if this is dead code.

2. **x-cursor-config-version**: Similarly not passed in main call site. May be used elsewhere or planned for future use.

3. **Checksum algorithm (Jyh)**: The XOR cipher used for timestamp encoding should be further analyzed for security implications.

---

## File References

- Header injection function: `beautified/workbench.desktop.main.js:268885-268917`
- Variable definitions: `beautified/workbench.desktop.main.js:268959`
- setCommonHeaders call: `beautified/workbench.desktop.main.js:1098807-1098820`
- Platform detection: `beautified/workbench.desktop.main.js:10070-10123`
- API base URLs: `beautified/workbench.desktop.main.js:182746`
