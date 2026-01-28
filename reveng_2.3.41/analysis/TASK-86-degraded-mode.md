# TASK-86: Degraded Mode Triggering and Fallback Behavior Analysis

## Executive Summary

Cursor IDE implements two distinct types of "degraded mode" mechanisms:

1. **Idempotent Stream Degraded Mode** - Server-signaled mode that disables stream reconnection/resumption guarantees
2. **Model Degradation Status** - Per-model availability states affecting UI and feature access

Both serve as graceful degradation mechanisms to maintain service during server stress or model availability issues.

## 1. Idempotent Stream Degraded Mode

### Location
- **Source**: `workbench.desktop.main.js:488870-488920`

### Protocol Definition

The degraded mode flag is part of the WelcomeMessage protobuf:

```protobuf
// aiserver.v1.WelcomeMessage
message WelcomeMessage {
  string message = 1;          // T: 9 (string)
  bool is_degraded_mode = 2;   // T: 8 (bool)
}
```

**Source reference** (lines 122238-122248, 329356-329367):
```javascript
this.typeName = "aiserver.v1.WelcomeMessage"
this.fields = v.util.newFieldList(() => [{
    no: 1,
    name: "message",
    kind: "scalar",
    T: 9  // string
}, {
    no: 2,
    name: "is_degraded_mode",
    kind: "scalar",
    T: 8  // bool
}])
```

### Triggering Mechanism

**Server-initiated**: The `is_degraded_mode` flag is sent by the server in the WelcomeMessage at stream establishment. The client has no control over when degraded mode is activated - it's a server-side decision.

Likely server-side triggers (inferred from behavior):
- High server load
- Backend service degradation
- Infrastructure failover events
- Rate limiting thresholds

### Client Behavior When Degraded Mode is Signaled

```javascript
// Line 488870-488876
if (M.response.case === "welcomeMessage") {
    M.response.value.isDegradedMode === !0 && (
        D = !0,  // Set local degraded flag
        console.warn("[composer] Idempotent streaming is in degraded mode - reconnection not available"),
        this._composerDataService.updateComposerData(r, {
            idempotentStreamState: void 0  // CRITICAL: Clear stream state
        })
    ),
    this._composerDataService.updateComposerData(r, {
        isReconnecting: !1
    });
    continue
}
```

### Effects of Degraded Mode

| Feature | Normal Mode | Degraded Mode |
|---------|-------------|---------------|
| Stream resumption | Enabled | Disabled |
| Client chunk replay | Buffered for replay | Not persisted |
| `idempotentStreamState` | Maintained | Cleared to `undefined` |
| Error retry | Automatic with backoff | Immediate failure |
| Event ID requirement | Required per chunk | Not enforced |

### Error Handling in Degraded Mode

```javascript
// Line 488913-488922
} catch (P) {
    console.error("[composer] Error in startReliableStream", P, {
        signalAborted: s.aborted,
        faultInjectSignalAborted: E.aborted,
        idempotencyKey: d,
        idempotencyEventId: f,
        playbackChunks: Array.from(g.playbackChunks.keys()).sort()
    });

    if (D) throw (  // D = isDegradedMode flag
        console.error("[composer] Error in degraded mode, not retrying"),
        this._composerDataService.updateComposerData(r, {
            isReconnecting: !1
        }),
        P  // Re-throw immediately - NO RETRY
    );
    // ... normal retry logic follows
}
```

### Recovery from Degraded Mode

**No automatic recovery mechanism exists in the client.**

Recovery flow:
1. Current stream completes (with or without errors)
2. User initiates new request
3. New connection established with fresh WelcomeMessage
4. If server no longer signals `is_degraded_mode`, normal operation resumes

## 2. Model Degradation Status

### Location
- **Source**: `workbench.desktop.main.js:165057-165067, 534785-534792`

### Enum Definition

```javascript
// Line 165057, 534785
i[i.UNSPECIFIED = 0] = "UNSPECIFIED"
i[i.DEGRADED = 1] = "DEGRADED"
i[i.DISABLED = 2] = "DISABLED"

// Protobuf registration
v.util.setEnumType(Gpe, "aiserver.v1.AvailableModelsResponse.DegradationStatus", [{
    no: 0,
    name: "DEGRADATION_STATUS_UNSPECIFIED"
}, {
    no: 1,
    name: "DEGRADATION_STATUS_DEGRADED"
}, {
    no: 2,
    name: "DEGRADATION_STATUS_DISABLED"
}])
```

### Per-Model Degradation

Each model in `AvailableModelsResponse.AvailableModel` can have its own degradation status:

```javascript
// Line 165168-165172
{
    no: 6,
    name: "degradation_status",
    kind: "enum",
    T: v.getEnumType(Gpe),  // DegradationStatus enum
    opt: !0  // Optional field
}
```

### UI Effects by Degradation Status

#### Status: UNSPECIFIED (0)
- Normal operation
- Model selectable without restrictions
- No visual indicators

#### Status: DEGRADED (1)
- Model remains selectable
- Warning icon (`warningTwo`) displayed
- Tooltip may show warning text via `secondaryWarningText`

```javascript
// Line 712780-712784
const xl = ks !== Gpe.UNSPECIFIED;  // ks = degradationStatus
// ...
rr = xl ? de.warningTwo : rr;  // Show warning icon if degraded
```

#### Status: DISABLED (2)
- Model becomes **unselectable** in the UI
- Grayed out in model dropdown

```javascript
// Line 712928
isDisabled: ks === Gpe.DISABLED || Ba || pe() && Xd && rm,
```

### Visual Indicators

**Warning Icon**:
```javascript
// Line 19548 - Codicon definition
warningTwo: Ht("warning-two", 60817),
```

**Warning Color**:
```javascript
// Lines 711873-711874, 766393
s.style.color = "var(--vscode-editorWarning-foreground)"
// Applied when secondaryWarningText is true
```

**Tooltip Display**:
```javascript
// Line 165069
this.primaryText = ""
this.secondaryText = ""
this.secondaryWarningText = !1  // Boolean flag for warning styling
this.icon = ""
this.tertiaryText = ""
this.tertiaryTextUrl = ""
this.markdownContent  // Optional markdown for rich tooltips
```

## 3. Analytics Degraded Warning

### Location
- **Source**: `workbench.desktop.main.js:274831-274851`

### Definition

A separate degradation flag exists for team usage analytics:

```javascript
// GetTeamUsageResponse
this.teamMemberUsage = []
this.analyticsDegradedWarning = !1

// Protobuf field
{
    no: 2,
    name: "analytics_degraded_warning",
    kind: "scalar",
    T: 8  // bool
}
```

This appears to signal when usage analytics data may be incomplete or delayed.

## 4. Feature Flag: Degraded Extended Usage

### Location
- **Source**: `workbench.desktop.main.js:294804-294811`

```javascript
subscription_only_degraded_extended_usage: {
    client: !0,  // Client-side evaluated
    fallbackValues: {
        enabled: !1
    },
    parseValue: {
        enabled: X2  // Boolean parser
    }
}
```

This feature flag appears to control behavior when subscription-based users experience extended usage in degraded conditions. The exact behavior controlled by this flag requires further investigation.

## 5. UI Reconnection Indicator

### Location
- **Source**: `workbench.desktop.main.js:714837, 751204`

When a stream is recovering (non-degraded mode), the UI shows a reconnection state:

```javascript
// Line 714837
w = ve(() => a().isReconnecting ?? !1)

// Line 751204 - Status display
n().isReconnecting === !0 && f.push("reconnecting"),
f.length > 0 ? f.join(", ") : void 0
```

**Note**: This indicator is specifically **not shown** when in degraded mode, as reconnection is disabled.

## Security Considerations

### Potential Exploitation Vectors

1. **Idempotency Bypass**: When degraded mode is active, the event ID requirement is relaxed:
   ```javascript
   // Line 488895
   if (!B.eventId && !D) throw new Error("No event ID received");
   // D = isDegradedMode - when true, missing eventId is allowed
   ```

2. **Replay Window**: Degraded mode clears the `idempotentStreamState`, which includes replay protection. If an attacker could force degraded mode, they might be able to cause duplicate operations.

3. **No Client Control**: The server unilaterally decides when to enter degraded mode. A compromised or malicious server could permanently disable reliability features.

### Mitigations Present

1. **Per-session keys**: Even without idempotency, each stream has a unique encryption key
2. **Console logging**: Degraded mode transitions are logged for debugging
3. **Graceful degradation**: System continues to function, just without reliability guarantees

## Related Configuration

### Dynamic Config

| Parameter | Location | Purpose |
|-----------|----------|---------|
| `retry_lookback_window_ms` | `idempotent_stream_config` | Max age for auto-resume (disabled in degraded mode) |

### Feature Gates

| Gate | Effect on Degraded Mode |
|------|------------------------|
| `persist_idempotent_stream_state` | Controls persistence (cleared in degraded mode) |
| `idempotent_agentic_composer` | Enables idempotent streaming for agent operations |

## Source References

| Component | File | Line Range |
|-----------|------|------------|
| WelcomeMessage protobuf | workbench.desktop.main.js | 122228-122262, 329346-329380 |
| Degraded mode handling | workbench.desktop.main.js | 488870-488922 |
| DegradationStatus enum | workbench.desktop.main.js | 165057-165067, 534785-534792 |
| AvailableModel with status | workbench.desktop.main.js | 165128-165200, 534860-534926 |
| Model dropdown UI | workbench.desktop.main.js | 712770-712930 |
| Analytics degraded warning | workbench.desktop.main.js | 274829-274864 |
| Subscription degraded flag | workbench.desktop.main.js | 294804-294811 |
| Reconnection indicator | workbench.desktop.main.js | 714837, 751204 |
| TooltipData structure | workbench.desktop.main.js | 165067-165127 |

## Conclusion

Cursor's degraded mode system is a server-controlled graceful degradation mechanism. The idempotent stream degraded mode disables reliability features during server stress, while model degradation status provides granular control over individual model availability. Neither mechanism has client-side recovery logic - recovery requires server-initiated state changes on new connections.

## Related Tasks

- TASK-39: Idempotent Stream Resumption Protocol
- TASK-84: Idempotent Streams Analysis
- TASK-116: Feature Gates Analysis
