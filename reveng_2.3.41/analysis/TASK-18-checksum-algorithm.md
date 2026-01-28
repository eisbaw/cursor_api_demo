# TASK-18: x-cursor-checksum Algorithm Analysis (Jyh Cipher)

## Overview

The `x-cursor-checksum` HTTP header is a request header sent by Cursor IDE to its API servers. It combines an obfuscated timestamp with machine identifiers for device fingerprinting and request validation.

## Algorithm Location

- **Function:** `Jyh` at line 268879 in `beautified/workbench.desktop.main.js`
- **Usage:** `Gyh` function at line 268885 (header injection)
- **Call site:** `setCommonHeaders` method at line 1098807

## Header Format

```
x-cursor-checksum: {obfuscated_timestamp}{machineId}
x-cursor-checksum: {obfuscated_timestamp}{machineId}/{macMachineId}
```

The format depends on whether `macMachineId` is available (macOS-specific identifier).

## The Jyh Cipher

### Source Code

```javascript
function Jyh(i) {
    let e = 165;  // Initial key: 0xa5
    for (let t = 0; t < i.length; t++) {
        i[t] = (i[t] ^ e) + t % 256;
        e = i[t];  // Rolling key: output becomes next key
    }
    return i;
}
```

### Algorithm Breakdown

1. **Initial Key:** Fixed value `165` (0xa5)
2. **For each byte at position t:**
   - XOR the input byte with the current key
   - Add the position index (mod 256)
   - The result becomes the key for the next iteration (rolling key)

### Mathematical Description

```
output[0] = (input[0] XOR 165) + 0
output[1] = (input[1] XOR output[0]) + 1
output[2] = (input[2] XOR output[1]) + 2
...
output[n] = (input[n] XOR output[n-1]) + (n % 256)
```

## Complete Checksum Generation

### Step 1: Timestamp Generation

```javascript
const timestamp = Math.floor(Date.now() / 1e6);  // Milliseconds / 1,000,000
```

This produces a value that:
- Represents roughly 16.7 minute intervals (1e6 ms)
- Is currently around 1,769,525 for January 2026
- Fits in a 48-bit integer (6 bytes)

### Step 2: Timestamp to Bytes

```javascript
const bytes = new Uint8Array([
    (timestamp >> 40) & 255,  // Most significant byte
    (timestamp >> 32) & 255,
    (timestamp >> 24) & 255,
    (timestamp >> 16) & 255,
    (timestamp >> 8) & 255,
    timestamp & 255           // Least significant byte
]);
```

### Step 3: Apply Jyh Cipher

The 6-byte timestamp array is passed through `Jyh()`.

### Step 4: Base64 URL-Safe Encoding

```javascript
// Uses URL-safe base64 alphabet (no padding)
const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
const encoded = base64UrlSafe(obfuscatedBytes);  // 8 characters output
```

### Step 5: Concatenate with Machine IDs

```javascript
// Final header value
const checksum = macMachineId === undefined
    ? `${encoded}${machineId}`           // 8 chars + machineId
    : `${encoded}${machineId}/${macMachineId}`;  // 8 chars + machineId + "/" + macMachineId
```

## Example Output

For timestamp `1769525` (Jan 2026):

| Stage | Value |
|-------|-------|
| Timestamp (decimal) | 1769525 |
| Timestamp (hex) | 0x1B0035 |
| Byte array | [0, 53, 0, 27, 0, 53] |
| After Jyh cipher | [165, 145, 147, 139, 143, 191] |
| Base64 encoded | `pZGTi4-_` |
| With machineId | `pZGTi4-_abc123def456` |
| With both IDs | `pZGTi4-_abc123def456/mac789xyz000` |

## Reverse Engineering (Decryption)

The Jyh cipher is **completely reversible** since the initial key is hardcoded:

```javascript
function reverseJyh(encrypted) {
    const result = new Uint8Array(encrypted.length);
    let prevKey = 165;  // Same initial key
    for (let t = 0; t < encrypted.length; t++) {
        // Reverse: subtract index, then XOR with previous key
        const step1 = (encrypted[t] - t % 256 + 256) % 256;
        result[t] = step1 ^ prevKey;
        prevKey = encrypted[t];
    }
    return result;
}
```

## Machine ID Sources

### machineId

- **Source:** `telemetryService.machineId` or `abuseService.getMachineId()`
- **Storage:** `storage.serviceMachineId` key in local storage
- **Format:** UUID string (e.g., `a1b2c3d4-e5f6-7890-abcd-ef1234567890`)
- **Generation:** Random UUID if not present (`Pft` function at line 352912)

### macMachineId

- **Source:** `telemetryService.macMachineId` or `abuseService.getMacMachineId()`
- **Platform:** macOS-specific hardware identifier
- **Purpose:** Additional device fingerprint

## Security Analysis

### Classification: Obfuscation, NOT Encryption

| Property | Assessment |
|----------|------------|
| Confidentiality | WEAK - Trivially reversible |
| Integrity | WEAK - No HMAC/signature |
| Replay Protection | PARTIAL - Timestamp provides limited window |
| Device Binding | MODERATE - Machine IDs are persistent |

### Weaknesses

1. **Hardcoded Initial Key:** The value `165` is embedded in client code
2. **Deterministic:** Same input always produces same output
3. **No Server Secret:** No shared secret between client and server
4. **Timestamp Resolution:** ~16 minute granularity is very coarse
5. **Client-Generated IDs:** Machine IDs can be spoofed

### What This IS:

- **Device fingerprinting** for analytics and abuse detection
- **Request freshness indicator** (coarse timestamp)
- **Anti-automation deterrent** (obscurity, not security)

### What This is NOT:

- **Authentication mechanism** - No cryptographic binding to user
- **Tamper detection** - No HMAC or digital signature
- **Rate limiting token** - No cryptographic proof-of-work

## Implications for API Clients

### For Legitimate Use

To generate a valid `x-cursor-checksum`:

1. Generate consistent machine IDs (store and reuse)
2. Compute timestamp as `Math.floor(Date.now() / 1e6)`
3. Apply Jyh cipher to 6-byte timestamp
4. Base64 URL-safe encode (no padding)
5. Concatenate with machine ID(s)

### For Server Validation

The server can:

1. Decode base64 and reverse Jyh to get timestamp
2. Check if timestamp is within acceptable range
3. Track machine IDs for abuse patterns
4. Correlate requests from same device

The server likely:
- Rejects requests with timestamps too far in past/future
- Tracks request patterns per machine ID
- May flag suspicious machine ID patterns

## File References

| Description | Location |
|-------------|----------|
| Jyh function | `beautified/workbench.desktop.main.js:268879-268883` |
| Header injection (Gyh) | `beautified/workbench.desktop.main.js:268885-268917` |
| setCommonHeaders call | `beautified/workbench.desktop.main.js:1098807-1098820` |
| Base64 encoder (yO) | `beautified/workbench.desktop.main.js:12595-12617` |
| Base64 alphabets | `beautified/workbench.desktop.main.js:12693` |
| Machine ID generation | `beautified/workbench.desktop.main.js:352912-352928` |

## Related Headers

The checksum is set alongside these headers in `Gyh`:

- `x-cursor-client-version` - IDE version
- `x-cursor-client-type` - Always "ide"
- `x-cursor-client-os` - OS platform
- `x-cursor-client-arch` - Architecture
- `x-cursor-timezone` - User timezone
- `x-ghost-mode` - Privacy mode flag
- `x-session-id` - Session identifier
- `x-client-key` - Client key

## Conclusion

The `x-cursor-checksum` header implements a lightweight device fingerprinting mechanism using a simple XOR-based cipher (Jyh) combined with machine identifiers. It provides obfuscation rather than security, making it suitable for analytics and basic abuse detection but not for authentication or authorization.

The algorithm is trivially reversible by anyone with access to the client code, which limits its effectiveness against determined adversaries. Its primary value is in correlating requests from the same device and detecting anomalous patterns.

---

## Implementation Reference

### JavaScript (Node.js)

```javascript
function generateCursorChecksum(machineId, macMachineId = undefined) {
    // Step 1: Timestamp
    const timestamp = Math.floor(Date.now() / 1e6);

    // Step 2: To bytes (big-endian 48-bit)
    const bytes = new Uint8Array([
        (timestamp >> 40) & 255,
        (timestamp >> 32) & 255,
        (timestamp >> 24) & 255,
        (timestamp >> 16) & 255,
        (timestamp >> 8) & 255,
        timestamp & 255
    ]);

    // Step 3: Jyh cipher
    let key = 165;
    for (let i = 0; i < bytes.length; i++) {
        bytes[i] = (bytes[i] ^ key) + i % 256;
        key = bytes[i];
    }

    // Step 4: Base64 URL-safe (no padding)
    const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
    let encoded = "";
    for (let i = 0; i < bytes.length; i += 3) {
        const a = bytes[i], b = bytes[i + 1] || 0, c = bytes[i + 2] || 0;
        encoded += alphabet[a >> 2];
        encoded += alphabet[((a & 3) << 4) | (b >> 4)];
        if (i + 1 < bytes.length) encoded += alphabet[((b & 15) << 2) | (c >> 6)];
        if (i + 2 < bytes.length) encoded += alphabet[c & 63];
    }

    // Step 5: Concatenate
    return macMachineId === undefined
        ? `${encoded}${machineId}`
        : `${encoded}${machineId}/${macMachineId}`;
}
```

### Python

```python
import time

def generate_cursor_checksum(machine_id: str, mac_machine_id: str = None) -> str:
    # Step 1: Timestamp
    timestamp = int(time.time() * 1000 / 1e6)

    # Step 2: To bytes (big-endian 48-bit)
    bytes_arr = [
        (timestamp >> 40) & 255,
        (timestamp >> 32) & 255,
        (timestamp >> 24) & 255,
        (timestamp >> 16) & 255,
        (timestamp >> 8) & 255,
        timestamp & 255
    ]

    # Step 3: Jyh cipher
    key = 165
    for i in range(len(bytes_arr)):
        bytes_arr[i] = ((bytes_arr[i] ^ key) + i % 256) % 256
        key = bytes_arr[i]

    # Step 4: Base64 URL-safe (no padding)
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    encoded = ""
    for i in range(0, len(bytes_arr), 3):
        a, b, c = bytes_arr[i], bytes_arr[i + 1] if i + 1 < len(bytes_arr) else 0, bytes_arr[i + 2] if i + 2 < len(bytes_arr) else 0
        encoded += alphabet[a >> 2]
        encoded += alphabet[((a & 3) << 4) | (b >> 4)]
        if i + 1 < len(bytes_arr):
            encoded += alphabet[((b & 15) << 2) | (c >> 6)]
        if i + 2 < len(bytes_arr):
            encoded += alphabet[c & 63]

    # Step 5: Concatenate
    if mac_machine_id is None:
        return f"{encoded}{machine_id}"
    return f"{encoded}{machine_id}/{mac_machine_id}"
```
