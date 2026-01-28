# TASK-18: Jyh Cipher and x-cursor-checksum Security Analysis

## Executive Summary

The `Jyh` function is a simple XOR-based stream cipher used in Cursor IDE to generate the `x-cursor-checksum` HTTP header. This analysis examines the algorithm's cryptographic properties, security implications, and potential attack vectors.

**Classification:** Obfuscation mechanism, NOT cryptographic security
**Risk Level:** Low (used for fingerprinting, not authentication)
**Reversibility:** Trivially reversible given public initial key

---

## Algorithm Deep Dive

### Source Location

- **File:** `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
- **Line:** 268879-268883 (Jyh function)
- **Line:** 268885-268917 (Gyh header injection function)

### The Jyh Cipher Implementation

```javascript
function Jyh(i) {
    let e = 165;  // Initial key: 0xA5 (10100101 in binary)
    for (let t = 0; t < i.length; t++) {
        i[t] = (i[t] ^ e) + t % 256;
        e = i[t];  // Cipher feedback: output becomes next key
    }
    return i
}
```

### Cryptographic Classification

| Property | Classification | Notes |
|----------|----------------|-------|
| Cipher Type | Stream cipher with feedback | Output depends on previous output |
| Key Schedule | None (hardcoded) | Single initial value of 165 |
| Mode | CFB-like (Cipher Feedback) | Output feeds back as next key |
| Block Size | 1 byte | Operates on bytes |
| Key Size | 8 bits effective | Initial key is 1 byte |

### Mathematical Formalization

Let:
- `I[n]` = input byte at position n
- `O[n]` = output byte at position n
- `K = 165` = initial key

Then:
```
O[0] = (I[0] XOR K) + 0
O[1] = (I[1] XOR O[0]) + 1
O[2] = (I[2] XOR O[1]) + 2
...
O[n] = (I[n] XOR O[n-1]) + (n mod 256)
```

### Reverse Function (Decryption)

```javascript
function reverseJyh(encrypted) {
    const result = new Uint8Array(encrypted.length);
    let prevKey = 165;  // Same initial key
    for (let t = 0; t < encrypted.length; t++) {
        // Reverse: subtract position, then XOR with previous key
        const step1 = (encrypted[t] - t % 256 + 256) % 256;
        result[t] = step1 ^ prevKey;
        prevKey = encrypted[t];
    }
    return result;
}
```

---

## Header Generation Process

### Complete Flow

```
┌─────────────────────┐
│ Date.now()          │ Current timestamp in milliseconds
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ / 1,000,000         │ Reduce to ~16.67 minute resolution
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 6-byte big-endian   │ [b5, b4, b3, b2, b1, b0]
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Jyh cipher          │ XOR + position + feedback
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Base64 URL-safe     │ Using alphabet: A-Za-z0-9-_
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Concatenate IDs     │ {encoded}{machineId}[/{macMachineId}]
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ x-cursor-checksum   │ Final header value
└─────────────────────┘
```

### Code Reference (Gyh Function)

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
}) {
    try {
        const _ = Math.floor(Date.now() / 1e6),  // Line 268903
            E = new Uint8Array([                  // Line 268904
                _ >> 40 & 255,
                _ >> 32 & 255,
                _ >> 24 & 255,
                _ >> 16 & 255,
                _ >> 8 & 255,
                _ & 255
            ]),
            T = Jyh(E),                          // Line 268905
            D = n(T);                            // Line 268906 - base64 encode
        i.header.set("x-cursor-checksum", t === void 0
            ? `${D}${e}`
            : `${D}${e}/${t}`)                   // Line 268907
    } catch {}
    // ... additional headers set
}
```

### Base64 Encoding Details

The base64 function `yO` (line 12595-12617) is called with parameters `(Vs.wrap(t), !1, !0)`:
- First parameter: Buffer wrapper
- Second parameter: `!1` (false) = no padding
- Third parameter: `!0` (true) = URL-safe alphabet

URL-safe alphabet (line 12693):
```javascript
m3a = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
```

vs standard base64:
```javascript
f3a = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
```

---

## Security Analysis

### Cryptographic Weaknesses

#### 1. Hardcoded Initial Key

**Weakness:** The initial key value `165` (0xA5) is embedded in client-side JavaScript.

**Impact:** Anyone with access to the source (which is shipped to all users) can:
- Decrypt any checksum to recover the timestamp
- Generate valid checksums for any timestamp

**Attack Complexity:** Trivial - no computational effort required

#### 2. No Shared Secret

**Weakness:** There is no server-side secret involved in the algorithm.

**Impact:** The server cannot verify that the checksum was generated by a legitimate client versus a replay or crafted request.

**Comparison to secure alternatives:**
| Scheme | Server Secret | Verification |
|--------|---------------|--------------|
| Jyh cipher | None | Cannot verify origin |
| HMAC | Required | Cryptographic verification |
| JWT | Required | Signature validation |

#### 3. Deterministic Output

**Weakness:** Same input always produces same output.

**Impact:** Enables:
- Precomputation attacks
- Rainbow tables for timestamp lookup
- Predictable checksums for future timestamps

#### 4. Coarse Timestamp Resolution

**Weakness:** Division by 1,000,000 reduces precision to ~16.67 minute windows.

**Implications:**
- Only ~87 unique values per day
- ~31,536 unique values per year
- Replay window of ~16 minutes

#### 5. Small Effective Keyspace

With a 6-byte timestamp and 8-bit initial key:
- Total state space: 2^48 * 2^8 = 2^56
- Practical state space: ~87 * 365 * years of service

### What This Achieves (Intended Use)

Despite cryptographic weaknesses, the header serves valid purposes:

1. **Request Freshness Check**
   - Server rejects requests with timestamps too far in past/future
   - Limits replay window to ~16 minutes

2. **Device Fingerprinting**
   - `machineId` provides consistent device identifier
   - `macMachineId` adds secondary identifier on macOS

3. **Obfuscation Layer**
   - Prevents casual timestamp inspection
   - Requires understanding of algorithm to manipulate

4. **Anti-Automation Deterrent**
   - Adds complexity for automated tools
   - Not a strong barrier, but increases effort

### Attack Scenarios

#### Scenario 1: Timestamp Extraction

**Objective:** Determine when a request was made from captured traffic

**Method:**
1. Extract base64-encoded prefix (8 characters)
2. Decode from URL-safe base64
3. Apply reverse Jyh cipher
4. Convert 6 bytes to integer
5. Multiply by 1,000,000 to get approximate milliseconds

**Difficulty:** Trivial

#### Scenario 2: Request Replay

**Objective:** Replay a captured request

**Constraints:**
- Must be replayed within ~16 minute window
- Machine IDs must match (or be accepted by server)

**Difficulty:** Easy if within time window

#### Scenario 3: Checksum Forgery

**Objective:** Generate valid checksum without legitimate client

**Method:**
1. Obtain or generate valid machine IDs
2. Compute timestamp: `Math.floor(Date.now() / 1e6)`
3. Convert to 6 bytes (big-endian)
4. Apply Jyh cipher
5. Base64 URL-safe encode
6. Concatenate with machine IDs

**Difficulty:** Trivial once algorithm is known

#### Scenario 4: Machine ID Spoofing

**Objective:** Masquerade as different device

**Method:**
1. Generate or reuse valid-looking UUIDs
2. Substitute in checksum generation

**Difficulty:** Easy - format is standard UUID/hex strings

---

## Related Headers

Headers set by the same `Gyh` function:

| Header | Variable | Description |
|--------|----------|-------------|
| `x-cursor-checksum` | computed | Obfuscated timestamp + machine IDs |
| `x-cursor-client-version` | `Ydt` / `s` | IDE version string |
| `x-cursor-client-type` | hardcoded | Always "ide" |
| `x-cursor-client-os` | `g` | Operating system |
| `x-cursor-client-arch` | `p` | CPU architecture |
| `x-cursor-client-os-version` | `w` | OS version |
| `x-cursor-client-device-type` | hardcoded | Always "desktop" |
| `x-cursor-timezone` | computed | Intl timezone |
| `x-cursor-canary` | conditional | "true" if Anysphere user |
| `x-cursor-config-version` | `h` | Config version |
| `x-ghost-mode` | `sJe` | Privacy mode flag |
| `x-session-id` | `Q$l` / `d` | Session identifier |
| `x-client-key` | `X$l` / `l` | Client key |
| `x-new-onboarding-completed` | `rJe` | Onboarding status |
| `x-request-id` | `a` | Request trace ID |
| `x-amzn-trace-id` | computed | AWS trace header |

---

## Implementation Reference

### JavaScript (Node.js compatible)

```javascript
const INITIAL_KEY = 165;
const BASE64_URL_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";

function jyhCipher(bytes) {
    let key = INITIAL_KEY;
    for (let i = 0; i < bytes.length; i++) {
        bytes[i] = (bytes[i] ^ key) + i % 256;
        key = bytes[i];
    }
    return bytes;
}

function jyhDecipher(encrypted) {
    const result = new Uint8Array(encrypted.length);
    let prevKey = INITIAL_KEY;
    for (let i = 0; i < encrypted.length; i++) {
        const step1 = (encrypted[i] - i % 256 + 256) % 256;
        result[i] = step1 ^ prevKey;
        prevKey = encrypted[i];
    }
    return result;
}

function base64UrlEncode(bytes) {
    let result = "";
    for (let i = 0; i < bytes.length; i += 3) {
        const a = bytes[i];
        const b = bytes[i + 1] || 0;
        const c = bytes[i + 2] || 0;

        result += BASE64_URL_ALPHABET[a >> 2];
        result += BASE64_URL_ALPHABET[((a & 3) << 4) | (b >> 4)];
        if (i + 1 < bytes.length) result += BASE64_URL_ALPHABET[((b & 15) << 2) | (c >> 6)];
        if (i + 2 < bytes.length) result += BASE64_URL_ALPHABET[c & 63];
    }
    return result;
}

function generateCursorChecksum(machineId, macMachineId = null) {
    // Step 1: Timestamp with ~16 minute resolution
    const timestamp = Math.floor(Date.now() / 1e6);

    // Step 2: Convert to 6-byte big-endian array
    const bytes = new Uint8Array([
        (timestamp / 0x10000000000) & 255,  // >> 40 in safe way
        (timestamp / 0x100000000) & 255,    // >> 32
        (timestamp >> 24) & 255,
        (timestamp >> 16) & 255,
        (timestamp >> 8) & 255,
        timestamp & 255
    ]);

    // Step 3: Apply Jyh cipher
    jyhCipher(bytes);

    // Step 4: Base64 URL-safe encode
    const encoded = base64UrlEncode(bytes);

    // Step 5: Concatenate with machine IDs
    if (macMachineId === null) {
        return `${encoded}${machineId}`;
    }
    return `${encoded}${machineId}/${macMachineId}`;
}

function extractTimestamp(checksum) {
    // Extract first 8 characters (base64 encoded timestamp)
    const encoded = checksum.slice(0, 8);

    // Decode base64 URL-safe
    const bytes = new Uint8Array(6);
    const indices = [...encoded].map(c => BASE64_URL_ALPHABET.indexOf(c));

    bytes[0] = (indices[0] << 2) | (indices[1] >> 4);
    bytes[1] = ((indices[1] & 15) << 4) | (indices[2] >> 2);
    bytes[2] = ((indices[2] & 3) << 6) | indices[3];
    bytes[3] = (indices[4] << 2) | (indices[5] >> 4);
    bytes[4] = ((indices[5] & 15) << 4) | (indices[6] >> 2);
    bytes[5] = ((indices[6] & 3) << 6) | indices[7];

    // Reverse Jyh cipher
    const decrypted = jyhDecipher(bytes);

    // Convert to timestamp
    let timestamp = 0;
    for (let i = 0; i < 6; i++) {
        timestamp = timestamp * 256 + decrypted[i];
    }

    // Return approximate date (multiply by 1e6 for milliseconds)
    return new Date(timestamp * 1e6);
}
```

### Python

```python
import time
from typing import Optional

INITIAL_KEY = 165
BASE64_URL_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

def jyh_cipher(data: list[int]) -> list[int]:
    """Apply Jyh cipher (in-place modification)."""
    key = INITIAL_KEY
    for i in range(len(data)):
        data[i] = ((data[i] ^ key) + i % 256) % 256
        key = data[i]
    return data

def jyh_decipher(encrypted: list[int]) -> list[int]:
    """Reverse Jyh cipher."""
    result = []
    prev_key = INITIAL_KEY
    for i, byte in enumerate(encrypted):
        step1 = (byte - i % 256 + 256) % 256
        result.append(step1 ^ prev_key)
        prev_key = byte
    return result

def base64_url_encode(data: list[int]) -> str:
    """Encode bytes to URL-safe base64 without padding."""
    result = []
    for i in range(0, len(data), 3):
        a = data[i]
        b = data[i + 1] if i + 1 < len(data) else 0
        c = data[i + 2] if i + 2 < len(data) else 0

        result.append(BASE64_URL_ALPHABET[a >> 2])
        result.append(BASE64_URL_ALPHABET[((a & 3) << 4) | (b >> 4)])
        if i + 1 < len(data):
            result.append(BASE64_URL_ALPHABET[((b & 15) << 2) | (c >> 6)])
        if i + 2 < len(data):
            result.append(BASE64_URL_ALPHABET[c & 63])

    return ''.join(result)

def generate_cursor_checksum(machine_id: str, mac_machine_id: Optional[str] = None) -> str:
    """Generate x-cursor-checksum header value."""
    # Step 1: Timestamp with ~16 minute resolution
    timestamp = int(time.time() * 1000 / 1e6)

    # Step 2: Convert to 6-byte big-endian array
    bytes_arr = [
        (timestamp >> 40) & 255,
        (timestamp >> 32) & 255,
        (timestamp >> 24) & 255,
        (timestamp >> 16) & 255,
        (timestamp >> 8) & 255,
        timestamp & 255
    ]

    # Step 3: Apply Jyh cipher
    jyh_cipher(bytes_arr)

    # Step 4: Base64 URL-safe encode
    encoded = base64_url_encode(bytes_arr)

    # Step 5: Concatenate with machine IDs
    if mac_machine_id is None:
        return f"{encoded}{machine_id}"
    return f"{encoded}{machine_id}/{mac_machine_id}"
```

---

## Conclusion

The Jyh cipher is a lightweight obfuscation mechanism designed for:
1. Basic anti-replay protection via timestamp
2. Device fingerprinting via machine IDs
3. Preventing casual inspection of request metadata

It is **NOT** designed for:
- Authentication or authorization
- Cryptographic security
- Tamper detection

The algorithm is trivially reversible, and its security relies entirely on obscurity rather than cryptographic strength. This is appropriate for its intended use case (telemetry and basic abuse detection) but should not be confused with actual security.

---

## Related Documentation

- **TASK-18-checksum-algorithm.md** - Original analysis with implementation examples
- **TASK-47-machine-id.md** - Machine ID generation and fingerprinting
- **TASK-6-cursor-headers.md** - Complete header documentation (if exists)

---

## File References

| Description | File Location |
|-------------|---------------|
| Jyh function | `beautified/workbench.desktop.main.js:268879-268883` |
| Gyh header setter | `beautified/workbench.desktop.main.js:268885-268917` |
| setCommonHeaders call | `beautified/workbench.desktop.main.js:1098807-1098820` |
| base64 encoder (yO) | `beautified/workbench.desktop.main.js:12595-12617` |
| base64 alphabets | `beautified/workbench.desktop.main.js:12693` |
| Header variable names | `beautified/workbench.desktop.main.js:268959` |
