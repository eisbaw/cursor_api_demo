# TASK-111: Speculative Summarization Encryption Flow

## Overview

Speculative summarization is a feature in Cursor IDE that proactively generates conversation summaries when context window usage reaches a threshold. This allows the AI to maintain context efficiently by summarizing older parts of conversations before they need to be truncated. The encryption key is generated client-side and sent to the server, suggesting server-side encryption/decryption of summary data.

## Key Components

### 1. Encryption Key Generation

**Location**: Line 215139 (initial generation), Lines 266811-266818 (restoration)

```javascript
// Initial key generation - 32 bytes (256 bits) of random data
speculativeSummarizationEncryptionKey: crypto.getRandomValues(new Uint8Array(32)),
```

The encryption key is:
- Generated using Web Crypto API's `getRandomValues()`
- 32 bytes (256 bits) in length
- Stored as `Uint8Array`
- Generated per-composer session
- Regenerated if corrupted or empty

### 2. Key Persistence and Restoration

**Location**: Lines 266811-266818

When a composer session is restored from storage, the key is deserialized:

```javascript
// Key is stored as base64 string, restored via BH function
if (typeof n.speculativeSummarizationEncryptionKey == "string") {
    try {
        const r = BH(n.speculativeSummarizationEncryptionKey);  // Base64 decode
        n.speculativeSummarizationEncryptionKey = new Uint8Array(r.buffer);
        // Validation: regenerate if empty
        if (n.speculativeSummarizationEncryptionKey.byteLength === 0) {
            console.error("[composer] speculativeSummarizationEncryptionKey is empty, regenerating");
            n.speculativeSummarizationEncryptionKey = crypto.getRandomValues(new Uint8Array(32));
        }
    } catch (r) {
        // On deserialization error, regenerate key
        console.error("[composer] Error deserializing speculativeSummarizationEncryptionKey", r);
        n.speculativeSummarizationEncryptionKey = crypto.getRandomValues(new Uint8Array(32));
    }
}
```

### 3. BH Function (Base64 Decoder)

**Location**: Lines 12552-12586

The `BH` function is a custom base64 decoder that handles both standard and URL-safe base64:

```javascript
function BH(i) {
    // Standard base64 decoding implementation
    // Supports both + and - for position 62
    // Supports both / and _ for position 63
    // Returns Vs.wrap(s).slice(0, o) - wrapped buffer
}
```

### 4. yO Function (Base64 Encoder)

**Location**: Lines 12595-12616

The `yO` function encodes binary data to base64 for storage:

```javascript
function yO({buffer: i}, e = !0, t = !1) {
    // e: whether to add padding (=)
    // t: whether to use URL-safe alphabet
    const n = t ? m3a : f3a;  // f3a is standard, m3a is URL-safe
    // Returns base64 string
}
```

### 5. Key Serialization for Storage

**Location**: Line 267039

When saving composer state, the key is encoded:

```javascript
speculativeSummarizationEncryptionKey: Di ? yO(Vs.wrap(Di)) : void 0,
```

## Protobuf Schema

### StreamUnifiedChatRequest (Field 79)

**Location**: Lines 123471-123474, 330590-330593

```protobuf
message StreamUnifiedChatRequest {
    // ... other fields ...
    optional bytes speculative_summarization_encryption_key = 79;  // T: 12 = bytes
}
```

The field is:
- Field number: 79
- Type: `bytes` (T: 12 in protobuf-es)
- Optional field

### ConversationSummary Response

**Location**: Lines 122381-122422

```protobuf
message ConversationSummary {
    string summary = 1;
    string truncation_last_bubble_id_inclusive = 2;
    string client_should_start_sending_from_inclusive_bubble_id = 3;
    string previous_conversation_summary_bubble_id = 4;
    bool includes_tool_results = 5;
    string strategy = 6;
}
```

## Speculative Summarization Flow

### 1. Triggering Conditions

**Location**: Lines 490359-490401

Speculative summarization is triggered based on dynamic configuration:

```javascript
// Default configuration values
const config = {
    tokenUsageThresholdPercentage: 80,    // Trigger when usage >= 80%
    tolerancePercentage: 10,               // Skip if cached summary within 10% of current usage
    inflightMaxAgeMinutes: 5,              // Timeout for in-flight summarizations
    speculativeStreamTimeoutMinutes: 5     // Stream timeout
};
```

Configuration schema (Line 294994-294998):
```javascript
client_speculative_summarization_config: ls.object({
    tokenUsageThresholdPercentage: ls.number(),
    tolerancePercentage: ls.number(),
    inflightMaxAgeMinutes: ls.number(),
    speculativeStreamTimeoutMinutes: ls.number()
})
```

### 2. getSpeculativeSummary Method

**Location**: Lines 492000-492113

```javascript
async getSpeculativeSummary(composerId) {
    // 1. Check if already in flight (prevent duplicate requests)
    const inFlightTime = this._speculativeSummarizationInFlight.get(composerId);
    if (inFlightTime !== undefined) {
        const ageMinutes = (Date.now() - inFlightTime) / 60000;
        if (ageMinutes >= inflightMaxAgeMinutes) {
            // Stale entry - remove and continue
            this._speculativeSummarizationInFlight.delete(composerId);
        } else {
            return;  // Already in flight, skip
        }
    }

    // 2. Get encryption key from composer data
    const encryptionKey = composerData.speculativeSummarizationEncryptionKey;

    // 3. Build request with encryption key
    const request = await this.computeStreamUnifiedChatRequest(composerId, {
        // ... conversation data ...
        extra: {
            speculativeSummarizationEncryptionKey: encryptionKey
        }
    });

    // 4. Stream summaries from server
    for await (const summary of chatClient.streamSpeculativeSummaries(request, {signal})) {
        // Store cached summary on conversation map
        this._composerDataService.updateComposerDataSetStore(
            composerId,
            M => M("conversationMap", bubbleId, "cachedConversationSummary", summary)
        );
    }
}
```

### 3. Request Construction

**Location**: Lines 491970-491995

The encryption key is included in the request:

```javascript
{
    // ... other fields ...
    speculativeSummarizationEncryptionKey: d?.speculativeSummarizationEncryptionKey,
    // ... other fields ...
}
```

### 4. Server Communication

**Location**: Lines 466477-466481

The gRPC service definition:

```javascript
streamSpeculativeSummaries: {
    name: "StreamSpeculativeSummaries",
    I: mse,   // StreamUnifiedChatRequest
    O: cZ,    // ConversationSummary
    kind: Kt.ServerStreaming
}
```

## Summary Storage and Caching

### Cached Summary Structure

Summaries are cached at the bubble (message) level:

```javascript
// Stored on conversation map entries
conversationMap[bubbleId].cachedConversationSummary = {
    summary: string,
    truncationLastBubbleIdInclusive: string,
    clientShouldStartSendingFromInclusiveBubbleId: string,
    previousConversationSummaryBubbleId: string,
    includesToolResults: boolean,
    strategy: string
};
```

### Latest Conversation Summary

**Location**: Lines 490782-490785

```javascript
this._composerDataService.updateComposerDataSetStore(e, g => g("latestConversationSummary", {
    summary: f,  // ConversationSummary object
    lastBubbleId: s
}));
```

### hasNearbyCachedSummary Check

**Location**: Lines 297900-297918

Before triggering new summarization, checks if a cached summary exists within the tolerance:

```javascript
hasNearbyCachedSummary(composerId, currentUsagePercent, tolerancePercent) {
    // Iterates through conversation bubbles
    // Looks for cachedConversationSummary entries
    // Checks if their context usage is within tolerance of current usage
    if (Math.abs(currentUsagePercent - cachedUsagePercent) <= tolerancePercent) {
        return true;  // Can use cached summary
    }
    return false;
}
```

## Encryption Architecture Analysis

### Key Observations

1. **Client-Side Key Generation**: The 256-bit encryption key is generated entirely client-side using `crypto.getRandomValues()`.

2. **Server-Side Usage**: The key is sent to the server via the `speculative_summarization_encryption_key` protobuf field, suggesting:
   - Server may encrypt summaries before storage
   - Server uses the key to decrypt when retrieving
   - This is a form of client-controlled encryption

3. **Key Per Composer**: Each composer session has its own encryption key, providing conversation-level isolation.

4. **No Local Encryption**: The client code does not show local encryption/decryption of summaries. The key appears to be used solely server-side.

5. **Similar Pattern**: This mirrors the `context_bank_encryption_key` (field 43) pattern used for context bank encryption.

### Related Encryption Fields

The codebase contains several similar encryption key fields:

| Field Name | Field Number | Purpose |
|-----------|--------------|---------|
| `speculative_summarization_encryption_key` | 79 | Conversation summary encryption |
| `context_bank_encryption_key` | 43 | Context bank data encryption |
| `path_encryption_key` | - | File path encryption for privacy |

### EncryptedBlobStore (Reference Pattern)

**Location**: Lines 263050-263120

For local encryption, Cursor uses `EncryptedBlobStore` with AES-256-GCM:

```javascript
class EncryptedBlobStore {
    static ALGORITHM = "AES-GCM";
    static IV_LENGTH = 12;

    async getEncryptionKey() {
        const keyBytes = new TextEncoder().encode(this.encryptionKeyStr);
        const hash = await crypto.subtle.digest("SHA-256", keyBytes);
        return await crypto.subtle.importKey("raw", hash, {
            name: "AES-GCM",
            length: 256
        }, true, ["encrypt", "decrypt"]);
    }

    async encryptBlob(data) {
        const iv = crypto.getRandomValues(new Uint8Array(12));
        const encrypted = await crypto.subtle.encrypt({
            name: "AES-GCM",
            iv: iv
        }, await this.getEncryptionKey(), data);
        // Return: IV || ciphertext
        return new Uint8Array([...iv, ...new Uint8Array(encrypted)]);
    }
}
```

This shows the encryption pattern Cursor uses locally, likely similar to server-side implementation.

## Data Flow Diagram

```
[Client - Composer Creation]
    |
    v
crypto.getRandomValues(32 bytes) --> speculativeSummarizationEncryptionKey
    |
    v
[Stored in composer data]
    |
    |--> [On save] yO(Vs.wrap(key)) --> Base64 string --> localStorage
    |
    |--> [On restore] BH(base64String) --> Uint8Array
    |
    v
[Context usage >= 80%]
    |
    v
getSpeculativeSummary()
    |
    v
computeStreamUnifiedChatRequest({
    speculativeSummarizationEncryptionKey: key
})
    |
    v
[gRPC: StreamSpeculativeSummaries]
    |
    v
[Server: Generates & encrypts summaries using provided key]
    |
    v
[Stream: ConversationSummary objects]
    |
    v
[Cache on conversationMap[bubbleId].cachedConversationSummary]
```

## Open Questions / Further Investigation

1. **Server-Side Implementation**: How exactly does the server use the encryption key? Is it AES-GCM like the local blob store?

2. **Key Rotation**: No evidence of key rotation mechanism found. What happens if the key is compromised?

3. **Privacy Mode Interaction**: How does this interact with privacy mode settings?

4. **NAL (New Agent Loop) Exception**: NAL conversations skip summarization (Line 491549-491551). Why?

5. **Strategy Selection**: The `ConversationSummaryStrategy` supports both `plain_text_summary` and `arbitrary_summary_plus_tool_result_truncation`. What determines which is used?

## Source File References

- **Main file**: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
- **Key generation**: Line 215139
- **Key restoration**: Lines 266811-266818
- **Base64 functions**: Lines 12552-12616
- **Protobuf schema**: Lines 123471-123474, 330590-330593
- **Speculative summarization**: Lines 492000-492113
- **Triggering logic**: Lines 490359-490401
- **Config schema**: Lines 294994-294998
- **EncryptedBlobStore**: Lines 263050-263120
