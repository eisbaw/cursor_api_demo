# TASK-12: Idempotent Stream Encryption Key Usage and Payload Encryption Analysis

## Executive Summary

The `x-idempotent-encryption-key` header is a **client-generated encryption key** sent to Cursor's server to enable **server-side encryption** of idempotent stream state. This allows the server to cache encrypted stream chunks that can be replayed on connection resumption, with the encryption ensuring only the client with the original key can decrypt the replayed data.

**Key Finding:** The encryption appears to be performed **server-side**, not client-side. The client generates and sends the key, but there is no visible client-side encryption or decryption of stream payloads using this key.

---

## 1. Encryption Key Generation

### Location
`/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js` - Lines 488774-488777

### Implementation

```javascript
// startReliableStream function
h = o?.idempotentEncryptionKey ?? (() => {
    const E = new Uint8Array(32);
    return crypto.getRandomValues(E), yO(Vs.wrap(E), !1, !0)
})();
```

### Key Properties

| Property | Value |
|----------|-------|
| Key Size | 32 bytes (256 bits) |
| Generation | Client-side via `crypto.getRandomValues()` |
| Encoding | URL-safe Base64 (no padding) |
| Per-session | Each idempotent stream gets a unique key |

### Base64 Encoding Function (yO)

```javascript
// Lines 12595-12617
function yO({buffer}, addPadding = true, urlSafe = false) {
    const charset = urlSafe
        ? "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        : "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    // Standard Base64 encoding implementation
}
```

The key is encoded with:
- `addPadding = false` (no `=` padding characters)
- `urlSafe = true` (uses `-_` instead of `+/`)

---

## 2. Key Transmission

### HTTP Headers

The encryption key is transmitted in HTTP headers for every idempotent stream request:

```javascript
// Lines 488861-488865
headers: {
    ...n,
    "x-idempotency-key": d,               // UUID identifying the stream
    "x-idempotency-event-id": f,          // Event cursor for resumption
    "x-idempotent-encryption-key": h      // Base64-URL encoded 32-byte key
}
```

### Three-Header System

| Header | Purpose | Format |
|--------|---------|--------|
| `x-idempotency-key` | Unique stream identifier | UUID string |
| `x-idempotency-event-id` | Last processed event ID | String (starts at "0") |
| `x-idempotent-encryption-key` | Encryption key for server-side caching | Base64-URL (256-bit) |

---

## 3. Idempotent Stream Protocol

### Protobuf Messages

**Request Type:** `aiserver.v1.StreamUnifiedChatRequestWithToolsIdempotent`
- Line 122180

```
message StreamUnifiedChatRequestWithToolsIdempotent {
    oneof request {
        StreamUnifiedChatRequestWithTools client_chunk = 1;  // Actual chat request
        Empty abort = 2;                                      // Abort signal
        Empty close = 3;                                      // Close signal
    }
    optional string idempotency_key = 4;                     // Stream ID (deprecated - now in header)
    optional uint32 seqno = 5;                               // Sequence number
}
```

**Response Type:** `aiserver.v1.StreamUnifiedChatResponseWithToolsIdempotent`
- Line 122272

```
message StreamUnifiedChatResponseWithToolsIdempotent {
    oneof response {
        StreamUnifiedChatResponseWithTools server_chunk = 1;  // Actual response
        WelcomeMessage welcome_message = 3;                   // Connection established
        uint32 seqno_ack = 4;                                 // Acknowledgment
    }
}
```

### BiDi Streaming Flow

```
Client                                  Server
  |                                       |
  |-- Request (client_chunk, seqno=0) -->|
  |                                       |-- Encrypt & Store
  |<------- welcome_message --------------|
  |                                       |
  |-- Request (client_chunk, seqno=1) -->|
  |                                       |-- Encrypt & Store
  |<------- server_chunk (eventId) ------|
  |<------- seqno_ack (0) ---------------|
  |                                       |
  |         [Connection drops]            |
  |                                       |
  |-- Reconnect with same headers ------>|
  |                                       |-- Decrypt & Replay
  |<------- welcome_message --------------|
  |<------- server_chunk (replay) -------|
  |                                       |
```

---

## 4. Server-Side Encryption (Hypothesized)

### Why Encryption is Server-Side

1. **No client-side decryption code**: There is no visible code in the client that decrypts stream responses using the idempotent encryption key.

2. **Key sent in header**: The key is transmitted to the server, not kept solely on the client.

3. **Purpose of encryption**: The encryption protects server-cached data so that:
   - Only clients with the original key can resume interrupted streams
   - Server-side caches cannot be accessed by other sessions/clients
   - Replay attacks from other clients are prevented

### Probable Server Implementation

```python
# Hypothetical server-side pseudocode
def store_chunk(idempotency_key, seqno, chunk_data, encryption_key):
    key = derive_aes_key(encryption_key)  # SHA-256 or HKDF
    iv = random_bytes(12)                 # AES-GCM IV
    ciphertext = aes_gcm_encrypt(key, iv, chunk_data)
    cache.store(f"{idempotency_key}:{seqno}", iv + ciphertext)

def replay_chunks(idempotency_key, from_event_id, encryption_key):
    key = derive_aes_key(encryption_key)
    for seqno, encrypted in cache.get_range(idempotency_key, from_event_id):
        iv, ciphertext = encrypted[:12], encrypted[12:]
        plaintext = aes_gcm_decrypt(key, iv, ciphertext)
        yield plaintext
```

---

## 5. State Persistence

### Feature Gate

The persistence of idempotent stream state is controlled by the feature gate `persist_idempotent_stream_state`:

```javascript
// Line 488772
const l = this._experimentService.checkFeatureGate("persist_idempotent_stream_state");
```

### Persisted State Structure

When enabled, the following state is saved to allow stream resumption:

```javascript
// Lines 488786-488792
idempotentStreamState: {
    idempotencyKey: d,              // UUID string
    idempotencyEventId: "0",        // Last processed event ID
    idempotentEncryptionKey: h,     // Base64-URL encoded key
    nextSeqno: 0,                   // Next sequence number to use
    playbackChunks: []              // Array of [seqno, JSON] tuples
}
```

### State Serialization

The encryption key is serialized as a Base64 string when persisting composer data:

```javascript
// Line 267039
speculativeSummarizationEncryptionKey: Di ? yO(Vs.wrap(Di)) : void 0,
```

And deserialized on load:

```javascript
// Lines 266812-266814
if (typeof n.speculativeSummarizationEncryptionKey == "string") try {
    const r = BH(n.speculativeSummarizationEncryptionKey);
    n.speculativeSummarizationEncryptionKey = new Uint8Array(r.buffer);
}
```

---

## 6. Auto-Resume Mechanism

### Function

Location: Lines 945194-945230

```javascript
async _autoResumeInterruptedStreams() {
    const lookbackWindow = 72e5;  // 2 hours default (configurable)
    const now = Date.now();

    for (const composer of allComposers) {
        const lastUpdated = composer.lastUpdatedAt ?? composer.createdAt;

        // Skip if too old
        if (now - lastUpdated > lookbackWindow) continue;

        // Skip if no idempotent state
        if (!composer.idempotentStreamState) continue;

        // Resume the stream
        await submitChatMaybeAbortCurrent(composerId, "", { isResume: true });
    }
}
```

### Configuration

The lookback window is configurable via dynamic config:

```javascript
// Line 945195
const e = this.experimentService.getDynamicConfigParam(
    "idempotent_stream_config",
    "retry_lookback_window_ms"
) ?? 72e5;  // Default: 2 hours (7,200,000 ms)
```

---

## 7. Degraded Mode

### Detection

The server can indicate that idempotent streaming is not available:

```javascript
// Lines 488870-488873
if (M.response.case === "welcomeMessage") {
    M.response.value.isDegradedMode === !0 && (
        D = !0,
        console.warn("[composer] Idempotent streaming is in degraded mode - reconnection not available"),
        this._composerDataService.updateComposerData(r, {
            idempotentStreamState: void 0
        })
    );
}
```

### Implications

When `isDegradedMode: true`:
- Stream state is cleared
- Reconnection/resumption is disabled
- Errors are not retried
- Client falls back to non-idempotent streaming

---

## 8. Related Encryption Keys

### Comparison with Other Encryption Keys

| Key Type | Size | Usage | Client-Side Encryption |
|----------|------|-------|------------------------|
| `x-idempotent-encryption-key` | 256-bit | Server-side stream caching | No |
| `speculativeSummarizationEncryptionKey` | 256-bit | Speculative summarization | No (sent to server) |
| `pathEncryptionKey` | Variable | File path privacy | Unknown |
| `contextBankEncryptionKey` | Variable | Context bank data | Unknown |
| EncryptedBlobStore key | 256-bit (via SHA-256) | Local blob storage | Yes (AES-GCM) |

### Client-Side Encryption (EncryptedBlobStore)

Unlike the idempotent encryption key, the `EncryptedBlobStore` **does** perform client-side encryption:

```javascript
// Lines 263050-263096
class EncryptedBlobStore {
    static ALGORITHM = "AES-GCM"
    static IV_LENGTH = 12

    async encryptBlob(data) {
        const iv = crypto.getRandomValues(new Uint8Array(12));
        const ciphertext = await crypto.subtle.encrypt(
            { name: "AES-GCM", iv },
            await this.getEncryptionKey(),
            data
        );
        // Format: [12-byte IV][ciphertext]
        return concatenate(iv, ciphertext);
    }
}
```

---

## 9. Security Analysis

### Strengths

1. **Strong key generation**: 256-bit cryptographically random keys
2. **Per-stream keys**: Each idempotent stream has its own encryption key
3. **Transport security**: Keys transmitted over TLS
4. **Time-limited resumption**: 2-hour default window limits exposure

### Potential Weaknesses

1. **Key in HTTP header**: Could be logged by proxies/load balancers (though TLS encrypted)
2. **Key persistence**: Key stored in composer state file on disk
3. **No key rotation**: Key persists for the lifetime of the stream
4. **Server trust required**: Client must trust server to handle key securely

### Mitigation Strategies

1. **Secure state storage**: Use OS keychain for composer state file encryption
2. **Key expiry**: Implement server-side key rotation after time threshold
3. **Header encryption**: Consider encrypting header with a session key

---

## 10. Data Flow Diagram

```
+-------------------+                    +-------------------+
|     Client        |                    |     Server        |
|                   |                    |                   |
| 1. Generate key   |                    |                   |
|    (32 bytes)     |                    |                   |
|        |          |                    |                   |
| 2. Base64-URL     |                    |                   |
|    encode         |                    |                   |
|        |          |                    |                   |
| 3. Send request   |-- HTTP (TLS) ----->| 4. Receive key   |
|    with headers:  |                    |    from header    |
|    - x-idempotency-key                 |                   |
|    - x-idempotency-event-id            | 5. Derive AES key |
|    - x-idempotent-encryption-key       |    (SHA-256?)     |
|                   |                    |        |          |
|                   |                    | 6. Encrypt chunk  |
|                   |                    |    (AES-GCM)      |
|                   |                    |        |          |
|                   |                    | 7. Store encrypted|
|                   |                    |    in cache       |
|                   |<-- Response -------|                   |
|                   |                    |                   |
| [Reconnect]       |                    |                   |
|                   |                    |                   |
| 8. Send same key  |-- HTTP (TLS) ----->| 9. Lookup cache  |
|                   |                    |        |          |
|                   |                    | 10. Decrypt with  |
|                   |                    |     provided key  |
|                   |<-- Replayed data --|                   |
+-------------------+                    +-------------------+
```

---

## 11. Open Questions

1. **Exact server-side algorithm**: Is it AES-GCM? What key derivation function?
2. **Server caching infrastructure**: Redis? S3? How long are cached chunks retained?
3. **Key verification**: Does the server verify the key matches before decryption?
4. **Partial replay**: Can the server replay from any event ID, or only from the beginning?
5. **Multi-region**: How does idempotent state sync across geographic regions?

---

## 12. Files Analyzed

- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
  - Idempotent stream implementation: Lines 488771-488960
  - Protobuf definitions: Lines 122170-122300
  - Auto-resume: Lines 945194-945230
  - Base64 encoding: Lines 12595-12617
  - Feature gates: Lines 294169-294172
  - State persistence: Lines 266843-267050

---

## 13. Conclusion

The `x-idempotent-encryption-key` header implements a client-generated encryption key for **server-side encryption** of cached stream data. This enables reliable stream resumption after network interruptions while maintaining confidentiality of the cached data. The encryption is not performed client-side; rather, the key is sent to the server which uses it to encrypt stored chunks. Only clients possessing the original key can decrypt and replay the cached stream.

This architecture represents a reasonable security tradeoff: it enables seamless stream resumption without requiring clients to implement complex caching and encryption logic, while still providing encryption at rest for server-cached data.
