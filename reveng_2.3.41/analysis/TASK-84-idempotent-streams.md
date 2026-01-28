# TASK-84: Server-Side Idempotent Stream Handling Analysis

## Executive Summary

This analysis examines the **server-side behavior** of Cursor's idempotent streaming protocol as inferred from client-side code in version 2.3.41. The idempotent streaming system enables reliable AI chat sessions that can survive network interruptions, application restarts, and transient failures. By analyzing the client's expectations and error handling, we can reconstruct the server's deduplication, state storage, and reconnection handling mechanisms.

## Key Findings

### 1. Server Uses x-idempotency-key for Session Deduplication

Based on client behavior, the server maintains a session state keyed by the idempotency key:

```
HTTP Headers sent on every request:
  x-idempotency-key: <UUID>           - Unique stream session identifier
  x-idempotency-event-id: <string>    - Last processed server event ID
  x-idempotent-encryption-key: <key>  - 256-bit encryption key (base64)
```

**Inferred Server Behavior:**
- Server maintains a session store indexed by `x-idempotency-key`
- On reconnection with same key, server validates the encryption key matches
- If keys match, server resumes from the stored position
- If keys mismatch, server likely rejects the request (implied by client state management)

### 2. Server-Side State Storage Mechanism

From client expectations, the server must store:

| State Element | Purpose | Inferred Storage Duration |
|---------------|---------|---------------------------|
| idempotency_key | Session identifier | At least 2 hours (client lookback window) |
| last_event_id | Cursor position for resumption | Same as session |
| encryption_key_hash | Validation of reconnection | Same as session |
| seqno_ack_watermark | Last acknowledged client seqno | Same as session |
| pending_response_chunks | Undelivered server responses | Same as session |

**Evidence from code (line 945195):**
```javascript
const e = this.experimentService.getDynamicConfigParam(
    "idempotent_stream_config",
    "retry_lookback_window_ms"
) ?? 72e5;  // Default: 7200000ms = 2 hours
```

This suggests the server retains session state for at least 2 hours, matching the client's auto-resume window.

### 3. Bidirectional Sequence Number Protocol

The protocol uses a **bidirectional seqno mechanism** for reliable delivery:

#### Client -> Server (seqno)
```javascript
// Line 488796-488803: Client assigns seqno to each chunk
const D = w++,  // Incrementing seqno
    P = new oNe({
        request: { case: "clientChunk", value: T },
        seqno: D
    });
```

#### Server -> Client (seqno_ack)
```javascript
// Line 488878-488879: Server acknowledges received chunks
if (M.response.case === "seqnoAck") {
    g.playbackChunks.delete(M.response.value);
    // Client removes from replay buffer
}
```

**Inferred Server Behavior:**
- Server tracks received seqno values per session
- Server sends seqno_ack after successfully processing each client chunk
- On reconnection, server expects replayed chunks with same seqno values
- Server **deduplicates** chunks already received (inferred from lack of duplicate handling in client)

### 4. Server Handles Conflicting seqno on Reconnection

Based on client reconnection logic (lines 488848-488860):

```javascript
const P = (async function*() {
    // First: replay all unacknowledged chunks from buffer
    for (const M of g.playbackChunks.values()) yield M;
    // Then: continue with new chunks from async pushable
    for await (const M of g.internalAsyncPushable) yield M;
})(),
A = e.streamUnifiedChatWithToolsIdempotent(P, { /* headers with same idempotency_key */ });
```

**Inferred Server Behavior:**
1. Server receives reconnection request with same `x-idempotency-key`
2. Server compares incoming seqno values against stored watermark
3. For seqno values already received:
   - Server immediately sends `seqno_ack` without reprocessing
   - Server does NOT execute duplicate chunks
4. For new seqno values:
   - Server processes normally and sends `seqno_ack`

### 5. Server Handles Partial Chunk Re-delivery

**Evidence from event_id tracking (lines 488893-488908):**
```javascript
if (M.response.case === "serverChunk") {
    const B = M.response.value;
    if (!B.eventId && !D) throw new Error("No event ID received");
    // Track position for meaningful responses
    if (B.response?.case === "streamUnifiedChatResponse" &&
        (B.response.value.text || B.response.value.thinking)) {
        f = B.eventId;  // Update cursor position
    }
}
```

**Inferred Server Behavior:**
- Server assigns monotonically increasing `event_id` to each response chunk
- On reconnection, client sends `x-idempotency-event-id` header
- Server resumes sending from **after** the specified event_id
- Server likely stores recent chunks for replay during the session window

### 6. Degraded Mode Handling

The server can signal when reliable streaming is unavailable:

```javascript
// Line 488870-488872
if (M.response.case === "welcomeMessage") {
    M.response.value.isDegradedMode === !0 && (
        D = !0,
        console.warn("[composer] Idempotent streaming is in degraded mode"),
        this._composerDataService.updateComposerData(r, {
            idempotentStreamState: void 0  // Clear state - no replay
        })
    )
}
```

**WelcomeMessage Protobuf (lines 122227-122249):**
```protobuf
message WelcomeMessage {
  string message = 1;
  bool is_degraded_mode = 2;  // Signals server cannot support resumption
}
```

**Inferred Server Triggers for Degraded Mode:**
1. Server under high load (state storage unavailable)
2. Session state expired or corrupted
3. Backend infrastructure maintenance
4. Rate limiting or resource exhaustion

### 7. Error Handling and Non-Retriable Errors

The client checks for `ErrorDetails` (FA class) to determine if retry is appropriate:

```javascript
// Line 488923-488928
if (P instanceof lb) {  // ConnectError
    const A = P.findDetails(FA);  // Extract ErrorDetails
    if (A && A.length > 0) throw this._composerDataService.updateComposerData(r, {
        isReconnecting: !1
    }), P  // Don't retry - server indicated non-retriable error
}
```

**ErrorDetails Types (lines 92684-92685):**
```javascript
// Non-retriable errors that should NOT trigger reconnection:
ERROR_BAD_API_KEY = 1
ERROR_NOT_LOGGED_IN = 2
ERROR_INVALID_AUTH_ID = 3
ERROR_NOT_HIGH_ENOUGH_PERMISSIONS = 4
ERROR_USER_NOT_FOUND = 6
ERROR_AUTH_TOKEN_NOT_FOUND = 11
ERROR_AUTH_TOKEN_EXPIRED = 12
ERROR_UNAUTHORIZED = 38
// ... and many more
```

**Inferred Server Behavior:**
- Server attaches `ErrorDetails` to response when error is non-retriable
- Presence of `ErrorDetails` signals client should abort, not reconnect
- This prevents infinite retry loops for permanent failures

## Protocol Flow Diagrams

### Normal Stream Operation

```
Client                                       Server
   |                                            |
   |──── Connect + Headers ─────────────────────>|
   |     x-idempotency-key: UUID-1              |
   |     x-idempotency-event-id: "0"            |
   |     x-idempotent-encryption-key: KEY-1     |
   |                                            |
   |<───── WelcomeMessage ──────────────────────|
   |       is_degraded_mode: false              |
   |                                            |
   |──── ClientChunk (seqno=0) ─────────────────>|
   |<───── seqno_ack: 0 ────────────────────────|
   |                                            |
   |──── ClientChunk (seqno=1) ─────────────────>|
   |<───── ServerChunk (eventId="evt-1") ───────|
   |<───── seqno_ack: 1 ────────────────────────|
   |                                            |
```

### Reconnection with Replay

```
Client                                       Server
   |                                            |
   |  ~~~ Connection Lost ~~~                   |
   |                                            |
   |──── Reconnect + Headers ───────────────────>|
   |     x-idempotency-key: UUID-1 (same)       |
   |     x-idempotency-event-id: "evt-1"        |
   |     x-idempotent-encryption-key: KEY-1     |
   |                                            |
   |<───── WelcomeMessage ──────────────────────|
   |                                            |
   |──── Replay ClientChunk (seqno=1) ──────────>|
   |<───── seqno_ack: 1 (already processed) ────|
   |                                            |
   |──── New ClientChunk (seqno=2) ─────────────>|
   |<───── Resume from eventId="evt-1" ─────────|
   |<───── ServerChunk (eventId="evt-2") ───────|
   |<───── seqno_ack: 2 ────────────────────────|
```

### Degraded Mode Flow

```
Client                                       Server
   |                                            |
   |──── Connect + Headers ─────────────────────>|
   |                                            |
   |<───── WelcomeMessage ──────────────────────|
   |       is_degraded_mode: true               |
   |                                            |
   | [Client clears idempotentStreamState]      |
   | [Client disables reconnection logic]       |
   |                                            |
   |──── ClientChunk (seqno=0) ─────────────────>|
   |<───── ServerChunk (no eventId) ────────────|
   |                                            |
   |  ~~~ Connection Lost ~~~                   |
   |                                            |
   | [Client throws error, does not retry]      |
```

## Security Analysis

### Potential Attack Vectors

#### 1. Session Hijacking via Idempotency Key
**Risk:** If attacker obtains the idempotency key, they could potentially:
- Resume a victim's stream session
- Inject malicious chunks

**Mitigations (inferred from client):**
- Encryption key (`x-idempotent-encryption-key`) must match
- Key is 256-bit cryptographically random
- Without key, hijacking should fail

#### 2. Replay Attacks
**Risk:** Attacker captures and replays legitimate requests

**Mitigations (inferred):**
- Server tracks processed seqno values
- Duplicate seqno values are acknowledged but not reprocessed
- Event IDs are monotonically increasing

#### 3. State Storage Exhaustion
**Risk:** Attacker creates many idempotent sessions to exhaust server storage

**Mitigations (inferred):**
- 2-hour default retention limit
- Degraded mode can disable persistence during load
- Per-user session limits likely enforced server-side

### Weakness: Local State Tampering

The client stores `idempotentStreamState` locally including:
- `playbackChunks` - buffered requests for replay
- `idempotencyEventId` - position cursor

A malicious client could:
1. Modify `idempotencyEventId` to request re-delivery of content
2. Inject fake chunks into `playbackChunks`

**Mitigation needed:** Server should validate chunk signatures or use server-side buffering only.

## Configuration Parameters

| Parameter | Source | Default | Purpose |
|-----------|--------|---------|---------|
| `retry_lookback_window_ms` | `idempotent_stream_config` | 7200000 (2h) | Max age for auto-resume |
| `persist_idempotent_stream_state` | Feature gate | false | Enable persistent state |
| `idempotent_agentic_composer` | Feature gate | varies | Enable for agentic mode |

## Source References

| Component | File | Lines |
|-----------|------|-------|
| startReliableStream | workbench.desktop.main.js | 488771-488960 |
| Idempotent request protobuf | workbench.desktop.main.js | 122170-122226 |
| Idempotent response protobuf | workbench.desktop.main.js | 122262-122306 |
| WelcomeMessage protobuf | workbench.desktop.main.js | 122227-122261 |
| ErrorDetails enum | workbench.desktop.main.js | 92643-92740 |
| Auto-resume logic | workbench.desktop.main.js | 945194-945231 |
| Config defaults | workbench.desktop.main.js | 295499-295502 |

## Inferred Server Requirements Summary

For a compatible server implementation:

1. **Session Store:**
   - Key: `x-idempotency-key` (UUID)
   - TTL: At least 2 hours
   - Data: encryption_key, seqno_watermark, event_id_cursor, pending_chunks

2. **On Connection:**
   - Validate encryption key matches stored key
   - Send WelcomeMessage with degraded_mode status
   - If degraded, client will not attempt reconnection

3. **On Client Chunk:**
   - Check seqno against watermark
   - If duplicate: send seqno_ack, skip processing
   - If new: process, update watermark, send seqno_ack

4. **On Reconnection:**
   - Load session from store
   - Resume sending from client's event_id position
   - Accept replayed chunks idempotently

5. **Error Handling:**
   - Attach `ErrorDetails` for non-retriable errors
   - Client will not reconnect if ErrorDetails present

## Related Tasks

- TASK-39: Stream Resumption Protocol (client-side analysis)
- TASK-85: Idempotent Encryption Key Usage
- TASK-12: Stream Encryption

## Open Questions for Further Investigation

1. **How does server validate encryption key?** Is it a hash comparison or symmetric decryption test?
2. **What triggers degraded mode?** Need traffic capture during server load.
3. **Session storage backend?** Redis? DynamoDB? In-memory?
4. **Cross-region session affinity?** What happens if client reconnects to different server?
5. **Rate limiting on reconnections?** Are there protections against aggressive retry?
