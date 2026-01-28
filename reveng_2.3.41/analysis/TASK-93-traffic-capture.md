# TASK-93: Traffic Capture - Verify Idempotent Stream Encryption

## Overview

This analysis documents methods for intercepting and analyzing Cursor IDE traffic to verify that the `x-idempotent-encryption-key` header results in actual encrypted stream data. The goal is to determine what data is encrypted vs. plaintext in the idempotent streaming protocol.

## 1. Traffic Interception Approaches

### 1.1 Proxy Configuration (Recommended)

Cursor supports standard HTTP proxy configuration through VS Code settings:

```javascript
// Settings at line 346156-346214
{
    "http.proxy": "string",              // Proxy URL (http, https, socks, socks4, socks5h)
    "http.proxyStrictSSL": true,         // Verify SSL certificates (default: true)
    "http.proxySupport": "override",     // Proxy mode: off, on, fallback, override
    "http.systemCertificates": true,     // Use system certificates
    "http.noProxy": [],                  // List of hosts to bypass proxy
    "http.proxyAuthorization": null,     // Proxy authorization header
    "http.proxyKerberosServicePrincipal": ""
}
```

**Proxy URL Pattern:**
```regex
^(https?|socks|socks4a?|socks5h?)://([^:]*(:[^@]*)?@)?([^:]+|\\[[:0-9a-fA-F]+\\])(:\\d+)?/?$
```

**Configuration for Traffic Capture:**
1. Set `http.proxy` to your interception proxy (e.g., `http://127.0.0.1:8080`)
2. Set `http.proxyStrictSSL` to `false` to allow MITM certificates
3. Add proxy CA certificate to system trust store OR set `http.systemCertificates` to `false`

### 1.2 HTTP/2 Disable Option

For proxies that don't support HTTP/2, Cursor provides a fallback option:

```javascript
// Location: line 450678
"cursor.general.disableHttp2": {
    type: "boolean",
    default: false,
    description: "Disable HTTP/2 for all requests, and use HTTP/1.1 instead.
                  This increases resource utilization and latency, but is useful
                  if you're behind a corporate proxy that blocks HTTP/2."
}
```

**Important:** Many proxies (mitmproxy, Burp Suite) have limited HTTP/2 support. Enable this setting for reliable interception.

### 1.3 SSE Disable Option

```javascript
// Location: line 450697
"cursor.general.disableHttp1SSE": {
    type: "boolean",
    default: false,
    description: "Disable HTTP/1.1 SSE for agent chat. This increases resource
                  utilization and latency, but is useful if you're behind a
                  corporate proxy that does not support HTTP/1.1 SSE streaming responses."
}
```

## 2. Certificate Validation

### 2.1 TLS Certificate Verification

Cursor performs TLS certificate issuer verification (line 911609):

```javascript
const issuerName = response.issuer.toString();
const isValidIssuer = issuerName.includes("Google Trust Services") ||
                      issuerName.includes("Amazon RSA")
    ? true
    : new Error(`Encrypted traffic is being intercepted by unrecognized certificate: ${issuerName}`);
```

**Recognized Issuers:**
- Google Trust Services (GTS)
- Amazon RSA

**Interception Detection:**
If a proxy's CA certificate is used, Cursor will detect and warn:
`"Encrypted traffic is being intercepted by unrecognized certificate: <issuer>"`

### 2.2 Certificate Acceptance/Rejection

Cursor provides UI for handling certificate errors:

```javascript
// Location: lines 372747-372756, 1137664-1137672
onCertificateError(event) {
    // Logs: "[BrowserViewManager] Certificate error for", url, "Error:", error
    // Shows certificate details: issuerName, subjectName, validStart, validExpiry, fingerprint
}

// User can accept or reject:
acceptCertificate(fingerprint, url, token)
rejectCertificate(fingerprint, token)
```

### 2.3 System Certificates Setting

```javascript
// Location: line 346195
"http.systemCertificates": {
    type: "boolean",
    default: true,
    markdownDescription: "..."
}
```

Set to `false` to disable system certificate store usage, which may help with proxy certificates not in the system store.

## 3. Network Endpoints

### 3.1 AI Backend URLs

```javascript
// Location: line 440478
mB = "https://staging.cursor.sh"           // Staging
Yxs = "https://repo42.cursor.sh"           // Repository backend
hbe = "https://dev-staging.cursor.sh"      // Dev staging
mue = "https://www.cursor.sh"              // Production (implicit)
marketplace = "https://marketplace.cursorapi.com"  // Extensions
```

### 3.2 gRPC/Connect-RPC Endpoints

The AI chat services use Connect-RPC (gRPC-Web compatible):

```javascript
// Location: line 466426-466507
// Service: aiserver.v1.ChatService
{
    streamUnifiedChat: ServerStreaming,
    streamUnifiedChatWithTools: BiDiStreaming,
    streamUnifiedChatWithToolsSSE: ServerStreaming,      // HTTP/1.1 SSE fallback
    streamUnifiedChatWithToolsPoll: ServerStreaming,     // Polling fallback
    streamUnifiedChatWithToolsIdempotent: BiDiStreaming, // Main idempotent stream
    streamUnifiedChatWithToolsIdempotentSSE: ServerStreaming,
    streamUnifiedChatWithToolsIdempotentPoll: ServerStreaming
}
```

## 4. Idempotent Stream Protocol Analysis

### 4.1 Headers to Capture

```javascript
// Location: line 488863-488865
headers: {
    "x-idempotency-key": d,           // UUID identifying the stream
    "x-idempotency-event-id": f,      // Event cursor for resumption
    "x-idempotent-encryption-key": h  // Base64-URL encoded 32-byte key (NO PADDING)
}
```

### 4.2 Key Generation

```javascript
// Location: line 488774-488777
const keyBytes = new Uint8Array(32);  // 256-bit key
crypto.getRandomValues(keyBytes);      // Cryptographically random
const encodedKey = yO(Vs.wrap(keyBytes), false, true);  // Base64-URL, no padding
```

### 4.3 Expected Protocol Flow

1. **Client Request:** Sends `StreamUnifiedChatRequestWithToolsIdempotent` with encryption key header
2. **Server Response:** `WelcomeMessage` with `isDegradedMode` flag
3. **Stream Data:** `ServerChunk` messages (potentially encrypted)
4. **Sequence Acknowledgment:** `seqno_ack` for confirmed delivery

### 4.4 Degraded Mode

When server cannot use encryption (line 488870-488877):
```javascript
if (welcomeMessage.isDegradedMode === true) {
    console.warn("[composer] Idempotent streaming is in degraded mode - reconnection not available");
    // Clear idempotent stream state
}
```

## 5. What to Look For in Captured Traffic

### 5.1 Request Headers Analysis

Capture and decode the `x-idempotent-encryption-key` header:
- Should be Base64-URL encoded (no `=` padding)
- Decoded length should be 32 bytes
- Different for each conversation session

### 5.2 Response Payload Analysis

**If Encrypted:**
- ServerChunk payloads should appear as random binary data
- Expected format: `[12-byte IV][ciphertext]` (AES-256-GCM pattern from EncryptedBlobStore)
- Cannot be decoded as valid protobuf without decryption

**If Plaintext:**
- ServerChunk payloads can be decoded as protobuf
- Text/thinking content visible in clear

### 5.3 Protobuf Message Types

```protobuf
// aiserver.v1.StreamUnifiedChatResponseWithToolsIdempotent
message StreamUnifiedChatResponseWithToolsIdempotent {
    oneof response {
        ServerChunk server_chunk = 1;      // Main data (possibly encrypted)
        WelcomeMessage welcome_message = 3; // Always plaintext
        uint32 seqno_ack = 4;              // Sequence acknowledgment
    }
}

// aiserver.v1.WelcomeMessage
message WelcomeMessage {
    string message = 1;
    bool is_degraded_mode = 2;
}
```

## 6. Built-in Network Diagnostics

Cursor has built-in network diagnostic tools (line 911490-911746):

### 6.1 Diagnostic Commands

```javascript
// Available via everythingProviderService.runCommand()
{
    "connectDebug.dnsLookup":      // DNS resolution test
    "connectDebug.inspectTLSInfo": // TLS certificate inspection
    "connectDebug.http2Ping":      // HTTP/2 connectivity test
}
```

### 6.2 NetworkDiagnostics Panel

The diagnostics panel tests:
- **DNS:** Resolution time and servers
- **HTTP/2:** Protocol negotiation
- **TLS:** Certificate chain, issuer validation
- **Unary:** Single request/response
- **Ping:** Latency measurement
- **Stream:** SSE/streaming connectivity
- **Bidi:** Bidirectional streaming
- **Marketplace:** Extension gallery connectivity

Access via: `NetworkDiagnostics` logging to console.

### 6.3 TLS Inspection Output

```javascript
// Line 911607
console.log("TLS URL:", response.url);
console.log("TLS Status:", response.status);
console.log("TLS IP:", response.ip);
console.log("TLS Issuer:", response.issuer);
console.log("TLS Name:", response.name);
console.log("TLS AltName:", response.altName);
console.log("TLS DNS Time:", response.dns_time, "ms");
console.log("TLS Connect Time:", response.connect_time, "ms");
console.log("TLS TLS Time:", response.tls_time, "ms");
```

## 7. Traffic Capture Methodology

### 7.1 Using mitmproxy

```bash
# 1. Start mitmproxy
mitmproxy --listen-port 8080

# 2. Configure Cursor settings.json
{
    "http.proxy": "http://127.0.0.1:8080",
    "http.proxyStrictSSL": false,
    "cursor.general.disableHttp2": true
}

# 3. Install mitmproxy CA certificate
# - Export: ~/.mitmproxy/mitmproxy-ca-cert.pem
# - Add to system trust store

# 4. Filter for AI traffic
# Host filter: *.cursor.sh, *.cursorapi.com

# 5. Capture idempotent stream requests
# Look for: POST to ChatService/StreamUnifiedChatWithToolsIdempotent
# Headers: x-idempotent-encryption-key
```

### 7.2 Using Wireshark (Without Decryption)

```bash
# Capture encrypted traffic metadata
# Filter: tcp port 443 and host cursor.sh
# Analyze: TLS handshakes, connection patterns, packet sizes

# Note: Cannot decrypt without TLS key extraction
```

### 7.3 Using Electron DevTools

```bash
# Launch Cursor with remote debugging
ELECTRON_ENABLE_LOGGING=1 /path/to/cursor --remote-debugging-port=9222

# Connect Chrome DevTools
# Network tab: Filter for WS/fetch requests
# View request/response headers and payloads
```

## 8. Encryption Verification Checklist

### 8.1 Key Transmission Verification

- [ ] Capture request with `x-idempotent-encryption-key` header
- [ ] Verify header is Base64-URL encoded (no padding)
- [ ] Decode and verify 32-byte length
- [ ] Confirm key changes per conversation

### 8.2 Response Encryption Analysis

- [ ] Capture `ServerChunk` responses
- [ ] Attempt protobuf decode of payload
- [ ] If decode fails, likely encrypted
- [ ] If decode succeeds, examine plaintext content

### 8.3 Degraded Mode Detection

- [ ] Check `WelcomeMessage.isDegradedMode` flag
- [ ] If `true`, server not using encryption
- [ ] If `false` or absent, encryption should be active

### 8.4 Encryption Format Verification

If encrypted, verify format matches EncryptedBlobStore (line 263046-263120):
- [ ] First 12 bytes = IV (random)
- [ ] Remaining bytes = AES-GCM ciphertext
- [ ] Attempt decryption with captured key

## 9. Data Classification

### 9.1 Always Plaintext

- HTTP headers (including encryption key)
- TLS layer (transport encryption)
- `WelcomeMessage` content
- `seqno_ack` values
- Protobuf message framing

### 9.2 Potentially Encrypted

- `ServerChunk` inner payload (AI responses)
- `ClientChunk` inner payload (user messages)
- Tool call results

### 9.3 Separately Encrypted

- `path_encryption_key`: File paths in requests
- `context_bank_encryption_key`: Context storage
- `speculative_summarization_encryption_key`: Summarization data

## 10. Known Limitations

### 10.1 Header-Based Key Transport

The encryption key is sent in HTTP headers:
- Protected by TLS in transit
- Visible to any MITM proxy with trusted certificate
- Server has full access to decryption key

### 10.2 Key Escrow Model

This is NOT end-to-end encryption:
- Client generates key
- Key sent to server
- Server can decrypt all data
- Purpose is likely for stream resumption, not privacy from server

### 10.3 No Certificate Pinning

Cursor does not implement certificate pinning:
- Accepts any certificate from recognized CAs
- Allows MITM with custom CA (with warning)
- Corporate proxies can intercept all traffic

## 11. Recommended Test Plan

1. **Configure proxy** with mitmproxy + disable HTTP/2
2. **Start chat session** with AI agent
3. **Capture initial request** - verify encryption key header
4. **Capture WelcomeMessage** - check `isDegradedMode` flag
5. **Capture ServerChunks** - attempt protobuf decode
6. **Compare with degraded mode** - force degraded mode if possible
7. **Document findings** - encrypted vs plaintext content

## 12. Further Investigation

Based on this analysis, the following tasks would help complete the picture:

1. **Server-side behavior**: Traffic analysis cannot reveal server-side encryption implementation
2. **Key usage verification**: Need to capture and attempt decryption of ServerChunk payloads
3. **Degraded mode trigger**: Determine what causes server to enter degraded mode
4. **Path encryption**: Verify `path_encryption_key` actually encrypts file paths

## References

- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
  - Proxy configuration: lines 346156-346249
  - HTTP/2 disable: lines 450678-450698
  - Certificate validation: lines 911597-911614
  - Network diagnostics: lines 911490-911780
  - Idempotent stream: lines 488771-488960
  - EncryptedBlobStore: lines 263046-263120
  - ChatService definition: lines 466426-466507
- Related analysis: TASK-12-stream-encryption.md, TASK-33-server-encryption.md
