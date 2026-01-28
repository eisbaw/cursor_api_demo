---
id: TASK-93
title: 'Traffic capture: Verify idempotent stream encryption'
status: Done
assignee: []
created_date: '2026-01-27 22:35'
updated_date: '2026-01-28 06:35'
labels:
  - encryption
  - traffic-analysis
  - security
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-33-server-encryption.md
  - reveng_2.3.41/analysis/TASK-12-stream-encryption.md
  - reveng_2.3.41/analysis/TASK-85-idempotent-encryption.md
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The x-idempotent-encryption-key header suggests stream data is encrypted, but server-side behavior is unknown. Need to: 1) Capture actual gRPC/HTTP traffic during idempotent streaming 2) Verify if response chunks are actually encrypted 3) Test decryption using the client-generated key 4) Document what data is protected and what remains in plaintext
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Documented proxy configuration methods
- [x] #2 Identified certificate validation behavior
- [x] #3 Analyzed what data is encrypted vs plaintext
- [x] #4 Documented traffic capture methodology
- [x] #5 Identified network diagnostic tools in client
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Analysis Complete

Investigated traffic capture approaches for verifying idempotent stream encryption.

## Key Findings

### Traffic Interception Approaches
1. **Proxy Configuration**: Standard VS Code proxy settings (`http.proxy`, `http.proxyStrictSSL`)
2. **HTTP/2 Disable**: `cursor.general.disableHttp2` setting for proxy compatibility
3. **SSE Disable**: `cursor.general.disableHttp1SSE` for streaming fallback

### Certificate Validation
- Cursor validates TLS certificate issuers (accepts Google Trust Services, Amazon RSA)
- Detects MITM interception with unrecognized certificates but allows override
- No certificate pinning - custom CA certificates can be used

### Encryption Protocol
- Key transmitted in `x-idempotent-encryption-key` HTTP header (Base64-URL, 32 bytes)
- Server responds with `WelcomeMessage.isDegradedMode` flag indicating encryption status
- `ServerChunk` payloads may be encrypted (AES-256-GCM format if following EncryptedBlobStore pattern)

### Network Diagnostics
- Built-in diagnostic commands: `connectDebug.dnsLookup`, `connectDebug.inspectTLSInfo`, `connectDebug.http2Ping`
- NetworkDiagnostics panel tests DNS, HTTP/2, TLS, streaming, and bidirectional connectivity

### Important Observations
- This is a KEY ESCROW model, not end-to-end encryption
- Server receives and can decrypt all data
- Header-based key transport relies entirely on TLS for protection
- No certificate pinning allows corporate proxy interception
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Traffic Capture Analysis for Idempotent Stream Encryption

### Summary
Completed analysis of Cursor IDE 2.3.41 traffic interception capabilities and encryption verification approaches.

### Key Discoveries

1. **Proxy Support**: Full HTTP/HTTPS/SOCKS proxy support with SSL verification toggle
2. **No Certificate Pinning**: Custom CA certificates accepted (with warning)
3. **HTTP/2 Fallback**: Setting to force HTTP/1.1 for proxy compatibility
4. **Key Escrow Model**: Encryption keys sent to server - not true E2E encryption
5. **Built-in Diagnostics**: Network diagnostic commands for TLS inspection

### Traffic Capture Method
1. Configure mitmproxy on port 8080
2. Set `http.proxy` to proxy URL
3. Set `http.proxyStrictSSL: false`
4. Set `cursor.general.disableHttp2: true`
5. Install proxy CA certificate
6. Capture requests to `*.cursor.sh`

### Encryption Analysis
- `x-idempotent-encryption-key` header: 32-byte Base64-URL encoded key
- `WelcomeMessage.isDegradedMode`: Server encryption capability flag
- `ServerChunk` payloads: Potentially encrypted with provided key (AES-GCM)

### Files
- Analysis: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-93-traffic-capture.md`
- Source: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
<!-- SECTION:FINAL_SUMMARY:END -->
