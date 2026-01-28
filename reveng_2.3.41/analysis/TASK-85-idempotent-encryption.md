# TASK-85: Idempotent Encryption Key - Usage and Cryptographic Purpose Analysis

## Executive Summary

The **idempotent encryption key** (`x-idempotent-encryption-key` header) is a 256-bit (32-byte) cryptographically random key generated client-side and transmitted to the Cursor server. Based on analysis of the decompiled client code, **there is no client-side encryption or decryption using this key**. The key appears to be used exclusively by the server, likely for:

1. Server-side encryption of persisted stream state
2. Authentication/verification of reconnection attempts
3. Preventing unauthorized stream hijacking

## Key Generation

### Source Location
`workbench.desktop.main.js` lines 488774-488777

### Implementation
```javascript
h = o?.idempotentEncryptionKey ?? (() => {
    const E = new Uint8Array(32);  // 32 bytes = 256 bits
    return crypto.getRandomValues(E), yO(Vs.wrap(E), !1, !0)
})();
```

### Details
- **Length**: 32 bytes (256 bits)
- **Source**: `crypto.getRandomValues()` - cryptographically secure PRNG
- **Encoding**: Base64-URL (without padding) via `yO()` function
- **Generation**: Once per stream session, on first connection
- **Reuse**: Same key used for all reconnection attempts within a session

## Key Storage and Persistence

### Idempotent Stream State Structure
```javascript
idempotentStreamState: {
    idempotencyKey: string,             // UUID stream identifier
    idempotencyEventId: string,         // Last processed server event ID
    idempotentEncryptionKey: string,    // This key (base64)
    nextSeqno: number,                  // Client sequence counter
    playbackChunks: Array<[seqno, jsonString]>  // Unacked chunks
}
```

### Persistence Location
When `persist_idempotent_stream_state` feature gate is enabled:
- State stored via `_composerDataService.updateComposerData()`
- Persists across application restarts
- Key stored in base64 format for serialization

### Feature Gate
```javascript
persist_idempotent_stream_state: {
    client: true,
    default: false
}
```
Location: line 294169

## Key Transmission

### HTTP Headers
The key is transmitted as an HTTP header with every idempotent stream request:

```javascript
// Location: lines 488863-488865
headers: {
    ...n,
    "x-idempotency-key": d,              // UUID stream identifier
    "x-idempotency-event-id": f,         // Last event cursor
    "x-idempotent-encryption-key": h     // The 256-bit key (base64)
}
```

### APIs Using This Header
1. `streamUnifiedChatWithToolsIdempotent` - Initial connection
2. `streamUnifiedChatWithToolsIdempotentPoll` - Polling fallback
3. Reconnection attempts use same headers

## Client-Side Cryptographic Usage

### Critical Finding: NO Client-Side Encryption/Decryption

After exhaustive search of the decompiled source:

1. **No `crypto.subtle.encrypt()` calls** use this key
2. **No `crypto.subtle.decrypt()` calls** use this key
3. **No AES-GCM operations** reference this key
4. **Key is only generated and transmitted** - never used for local crypto operations

### What The Client DOES Use For Encryption

The client uses **different** encryption mechanisms:

| Key Type | Usage | Algorithm |
|----------|-------|-----------|
| `speculativeSummarizationEncryptionKey` | Sent in request body for server-side summarization | N/A (server-side) |
| EncryptedBlobStore keys | Local blob storage encryption | AES-256-GCM |
| MCP secrets encryption | Local secret storage | AES-256-GCM |

## Hypothesized Server-Side Purpose

Based on the client implementation, the server likely uses this key for:

### 1. Server-Side Encryption at Rest
```
Client ──────> Server
  │              │
  │ 256-bit key  │
  ├──────────────▶│
  │              │ ┌────────────────────┐
  │              │ │ Encrypt stream     │
  │              │ │ state with AES-GCM │
  │              │ │ before persisting  │
  │              │ └────────────────────┘
  │              │
  │ On Reconnect │
  │──────────────▶│
  │ (same key)   │ ┌────────────────────┐
  │              │ │ Decrypt persisted  │
  │              │ │ state to resume    │
  │              │ └────────────────────┘
```

**Purpose**: Ensures that persisted stream state on the server is encrypted with a client-provided key, providing:
- **Confidentiality**: Server cannot decrypt without client key
- **Authentication**: Only client with key can resume stream

### 2. Stream Identity Verification
The key acts as a shared secret:
- Client generates key on session start
- Server associates key with stream ID
- On reconnection, matching key proves client identity

### 3. Replay Attack Prevention
Combined with other mechanisms:
- Unique `idempotencyKey` (UUID) per session
- Event-based cursor (`idempotencyEventId`)
- Sequence number acknowledgment (`seqnoAck`)

## Comparison with Other Keys

### Idempotent Encryption Key vs Speculative Summarization Key

| Property | Idempotent Key | Speculative Key |
|----------|---------------|-----------------|
| Size | 32 bytes | 32 bytes |
| Generation | Per stream session | Per composer session |
| Transmission | HTTP header | Request body (protobuf) |
| Client crypto | None | None |
| Persistence | With stream state | With composer data |
| Purpose | Stream resumption security | Summarization caching |

### Idempotent Encryption Key vs EncryptedBlobStore Key

| Property | Idempotent Key | BlobStore Key |
|----------|---------------|---------------|
| Size | 32 bytes | String (hashed to 32 bytes) |
| Algorithm | Unknown (server) | AES-256-GCM |
| Client crypto | None | Encrypt/Decrypt |
| Purpose | Server-side encryption | Local storage encryption |

## Security Analysis

### Strengths

1. **Cryptographic Randomness**: Generated via `crypto.getRandomValues()`
2. **Adequate Key Size**: 256 bits provides strong security
3. **Per-Session Keys**: New key per stream prevents cross-session attacks
4. **TLS Protection**: Key transmitted over HTTPS (assumed)

### Potential Weaknesses

1. **Header Exposure**: Key visible in HTTP headers (TLS mitigates)
2. **Client-Side Storage**: Persisted state could be read from disk
3. **Server Trust**: Client trusts server to actually use the key
4. **No Key Rotation**: Key unchanged during session lifetime

### Security Model

The design follows a **"client-provided server encryption"** model:
- Client generates and controls the encryption key
- Server encrypts data with client key
- Only clients with the key can trigger decryption

This provides:
- **Forward secrecy** for individual streams (new key each session)
- **Client-controlled security** (server cannot decrypt without client)
- **Stateless server option** (encrypted state can be passed back to client)

## What Happens on Reconnection Failure

### Wrong Key Scenario
If a client reconnects with a mismatched key:
1. Server cannot decrypt persisted stream state
2. Server likely returns error or degraded mode
3. Client clears local state:
```javascript
// Line 488872
this._composerDataService.updateComposerData(r, {
    idempotentStreamState: void 0
})
```

### Degraded Mode
```javascript
// Lines 488870-488872
if (M.response.value.isDegradedMode === !0) {
    D = !0;
    console.warn("[composer] Idempotent streaming is in degraded mode");
    this._composerDataService.updateComposerData(r, {
        idempotentStreamState: void 0  // Clear state
    });
}
```

## Open Questions

1. **Exact server algorithm**: Is it AES-256-GCM or something else?
2. **Key derivation on server**: Is the key used directly or derived?
3. **What data is encrypted**: Full stream state or just sensitive parts?
4. **Server persistence location**: Where is encrypted state stored?
5. **Key validation timing**: Is key validated on connect or on resume?

## Source References

| Component | Location | Lines |
|-----------|----------|-------|
| Key generation | workbench.desktop.main.js | 488774-488777 |
| Header transmission | workbench.desktop.main.js | 488863-488865 |
| State persistence | workbench.desktop.main.js | 488786-488792 |
| State serialization | workbench.desktop.main.js | 267039-267040 |
| Feature gate | workbench.desktop.main.js | 294169 |
| Base64-URL encoder (yO) | workbench.desktop.main.js | 12595-12617 |
| Reconnection handling | workbench.desktop.main.js | 488940-488945 |
| Degraded mode | workbench.desktop.main.js | 488870-488872 |

## Conclusion

The `x-idempotent-encryption-key` is a **client-generated secret** used for **server-side security operations**. The client code:

1. Generates a strong 256-bit random key
2. Transmits it with every stream request
3. Persists it for session resumption
4. Does NOT perform any encryption/decryption with it

The key's actual cryptographic use is entirely on the server side, likely for:
- Encrypting persisted stream state at rest
- Authenticating reconnection attempts
- Preventing stream hijacking by malicious actors

This design provides **client-controlled encryption** where the server cannot read persisted stream data without the client-provided key, giving users privacy guarantees even when data is stored server-side.

## Related Tasks

- **TASK-39**: Idempotent Stream Resumption Protocol (covers the broader protocol)
- **TASK-12**: Stream Encryption Analysis (covers other encryption mechanisms)
- **TASK-33**: Server-Side Encryption (would need server analysis)
