# TASK-90: Bedrock Model ID Regional Prefix System

## Executive Summary

Cursor IDE transforms AWS Bedrock model IDs based on the user's configured AWS region. Models are stored internally with a `us.` prefix (US standard), and the client dynamically replaces this prefix with region-appropriate alternatives (`apac.`, `eu.`, `ca.`) when the user selects a non-US region.

This is an AWS Bedrock standard, not a Cursor-specific convention. AWS Bedrock uses cross-region inference (CRI) prefixes to route requests to the appropriate regional model deployment.

## Regional Prefix Mapping

### Region-to-Prefix Logic

```javascript
// File: workbench.desktop.main.js
// Line: 894673-894675 (regionalBedrockId function)
regionalBedrockId(e) {
    const t = this._reactiveStorageService.applicationUserPersistentStorage.bedrockState?.region || "";
    return !t || t.startsWith("us-") ? e
         : t.startsWith("ap-") ? e.replace("us.", "apac.")
         : t.startsWith("eu-") ? e.replace("us.", "eu.")
         : t.startsWith("ca-") ? e.replace("us.", "ca.")
         : e
}
```

### Mapping Table

| User Region Prefix | Model ID Prefix | Example Regions |
|-------------------|-----------------|-----------------|
| `us-` (or empty)  | `us.`           | us-east-1, us-east-2, us-west-1, us-west-2 |
| `ap-`             | `apac.`         | ap-northeast-1, ap-southeast-1, ap-southeast-2 |
| `eu-`             | `eu.`           | eu-west-1, eu-west-2, eu-central-1 |
| `ca-`             | `ca.`           | ca-central-1 |

### Fallback Behavior

If the region does not match any known prefix pattern, the model ID is returned unchanged (with `us.` prefix). This means:
- Empty region: defaults to `us.` prefix
- Unknown region prefix (e.g., `af-`, `sa-`, `me-`): keeps `us.` prefix
- The system does not error on unsupported regions; it silently falls back to US routing

## Supported Bedrock Models

The hardcoded list of Bedrock models supported for automatic prefix transformation:

```javascript
// Line: 290762
JQl = [
    "us.anthropic.claude-sonnet-4-20250514-v1:0",
    "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "us.anthropic.claude-3-5-haiku-20241022-v1:0",
    "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "us.anthropic.claude-opus-4-20250514-v1:0",
    "us.anthropic.claude-opus-4-1-20250805-v1:0",
    "us.anthropic.claude-opus-4-5-20251101-v1:0"
]
```

### Model Analysis

| Model Name | Base Model | Release Date | Version |
|------------|------------|--------------|---------|
| claude-sonnet-4-20250514 | Sonnet 4 | 2025-05-14 | v1:0 |
| claude-sonnet-4-5-20250929 | Sonnet 4.5 | 2025-09-29 | v1:0 |
| claude-3-5-haiku-20241022 | 3.5 Haiku | 2024-10-22 | v1:0 |
| claude-haiku-4-5-20251001 | Haiku 4.5 | 2025-10-01 | v1:0 |
| claude-opus-4-20250514 | Opus 4 | 2025-05-14 | v1:0 |
| claude-opus-4-1-20250805 | Opus 4.1 | 2025-08-05 | v1:0 |
| claude-opus-4-5-20251101 | Opus 4.5 | 2025-11-01 | v1:0 |

## Model ID Transformation Flow

### 1. Default Models Refresh

When fetching available models from the server, the client transforms model IDs:

```javascript
// Line: 894688-894695
const s = this._reactiveStorageService.applicationUserPersistentStorage.bedrockState?.region;
s && !s.startsWith("us-") && (n = n.map(P => (P.name || "").startsWith("us.anthropic.") ? {
    ...P,
    name: this.regionalBedrockId(P.name || ""),
    serverModelName: this.regionalBedrockId(P.serverModelName || ""),
    clientDisplayName: this.regionalBedrockId(P.clientDisplayName || ""),
    inputboxShortModelName: this.regionalBedrockId(P.inputboxShortModelName || "")
} : P))
```

**Flow:**
1. Server returns models with `us.anthropic.*` prefixes
2. If user region is non-US, all `us.anthropic.*` models are transformed
3. Four model identifier fields are updated:
   - `name`: Primary model identifier
   - `serverModelName`: Name sent to backend/Bedrock
   - `clientDisplayName`: Name shown in UI
   - `inputboxShortModelName`: Abbreviated name in input box

### 2. Bedrock Toggle Enable/Disable

When toggling Bedrock on or off, models are added/removed with correct regional prefix:

```javascript
// Line: 910567-910574
Rt(xt => {
    const $t = Je();  // current toggle state
    if (xt !== $t)
        for (const si of JQl) {  // iterate hardcoded models
            let ti = si;
            const bi = Xe.reactiveStorageService.applicationUserPersistentStorage.bedrockState?.region || "";

            // Transform prefix based on region
            bi.startsWith("ap-") ? ti = si.replace("us.", "apac.")
            : bi.startsWith("eu-") ? ti = si.replace("us.", "eu.")
            : bi.startsWith("ca-") && (ti = si.replace("us.", "ca."))

            // Add or remove model based on toggle state
            $t ? (Xe.aiSettingsService.addUserAddedModel(ti), Xe.aiSettingsService.enableModel(ti))
                : (Xe.aiSettingsService.removeModel(si), Xe.aiSettingsService.removeModel(ti))
        }
    return $t
}, Je());
```

**Important:** When removing models, both the original `us.` prefix AND the regional prefix are removed to clean up any variant.

### 3. Model Selection in UI

The default test model also uses the regional prefix:

```javascript
// Line: 910577
const [bt, tt] = Be(
    Xe.reactiveStorageService.applicationUserPersistentStorage.bedrockState?.testModel
    ?? "us.anthropic.claude-sonnet-4-20250514-v1:0"
);
```

## Bedrock State Storage

The `bedrockState` object in persistent storage tracks the user's Bedrock configuration:

```javascript
// Stored in applicationUserPersistentStorage.bedrockState
{
    accessKey: string,     // AWS Access Key ID or "iam" for IAM role auth
    secretKey: string,     // AWS Secret Access Key or "iam" for IAM role auth
    region: string,        // AWS region (e.g., "us-east-1", "eu-west-1")
    useBedrock: boolean,   // Toggle state
    sessionToken: string,  // Optional STS session token
    testModel: string      // Last tested model ID
}
```

## AWS Bedrock Cross-Region Inference

### How It Works

AWS Bedrock's Cross-Region Inference (CRI) allows a single model inference profile to route requests across multiple AWS regions. The regional prefix determines the inference profile used:

| Prefix | Inference Profile | Typical Regions |
|--------|-------------------|-----------------|
| `us.`  | US inference profile | us-east-1, us-west-2 |
| `eu.`  | EU inference profile | eu-west-1, eu-central-1 |
| `apac.`| APAC inference profile | ap-northeast-1, ap-southeast-2 |
| `ca.`  | Canada inference profile | ca-central-1 |

### Why This Matters

1. **Data Residency**: Enterprise customers may need requests processed in specific regions for compliance (GDPR, data sovereignty)
2. **Latency**: Regional prefixes route to geographically closer deployments
3. **Availability**: CRI provides automatic failover within a regional profile

## Credential Flow Integration

When Bedrock credentials are sent to the AI server:

```javascript
// Line: 940426-940433
e.bedrockState?.useBedrock === !0 ? {
    case: "bedrockCredentials",
    value: new Bas({  // BedrockCredentials protobuf message
        accessKey: e.bedrockState.accessKey,
        secretKey: e.bedrockState.secretKey,
        region: e.bedrockState.region,        // <-- User's region
        sessionToken: e.bedrockState.sessionToken
    })
}
```

The `region` field is passed to the server along with credentials. The server uses this region to:
1. Construct the Bedrock endpoint URL (`bedrock-runtime.{region}.amazonaws.com`)
2. Apply appropriate model ID prefix if needed on the server side

## Test Credentials API

Users can validate their Bedrock credentials before enabling:

```javascript
// Line: 895192-895202
async testBedrockCredentials(accessKey, secretKey, region, modelName) {
    const response = await this.aiClient().testBedrockCredentials({
        accessKey: accessKey,
        secretKey: secretKey,
        region: region,     // <-- Test region
        modelName: modelName  // <-- Model ID (with regional prefix)
    });
    return {
        valid: response.success,
        error: response.error
    }
}
```

## UI Implementation

The settings UI shows a region input field:

```javascript
// Line: 910643-910654
{
    placeholder: "e.g. us-east-1",
    onInput: $t => {
        Xe.reactiveStorageService.setApplicationUserPersistentStorage("bedrockState", {
            ...Xe.reactiveStorageService.applicationUserPersistentStorage.bedrockState,
            region: $t.currentTarget.value  // Free-form text input
        })
    },
    value: Xe.reactiveStorageService.applicationUserPersistentStorage.bedrockState?.region ?? "",
    spellcheck: !1
}
```

**Note:** The region is a free-form text input, not a dropdown. Users must enter valid AWS region codes manually.

## Enterprise IAM Role Default Region

When enterprise IAM role authentication is detected, a default region is set:

```javascript
// Line: 1098122-1098127
this._reactiveStorageService.setApplicationUserPersistentStorage("bedrockState", {
    useBedrock: !1,
    region: "us-east-2",  // <-- Default for IAM role auth
    ...this._reactiveStorageService.applicationUserPersistentStorage.bedrockState,
    accessKey: "iam",
    secretKey: "iam"
})
```

The default region `us-east-2` (Ohio) is used for enterprise IAM role setups, but can be overridden by existing `bedrockState.region` via the spread operator.

## Gaps and Limitations

### 1. Incomplete Regional Coverage

Only four region prefixes are supported:
- Supported: `us-`, `ap-`, `eu-`, `ca-`
- **Not supported:**
  - `me-` (Middle East)
  - `af-` (Africa - Cape Town)
  - `sa-` (South America)

Unsupported regions silently fall back to `us.` prefix, which may not work if Bedrock is not deployed there.

### 2. No Region Validation

The UI accepts any string as a region. Invalid regions like `xx-invalid-1` are accepted and will fail at API call time.

### 3. Hardcoded Model List

The `JQl` array is hardcoded and does not automatically update when AWS adds new Bedrock models. New Claude models require a Cursor update.

### 4. No Cross-Region Fallback

If a model is unavailable in the user's region, there's no automatic fallback to another region.

## File References

| Component | Line Numbers | Description |
|-----------|--------------|-------------|
| `regionalBedrockId()` | 894673-894676 | Core prefix transformation function |
| `JQl` (model list) | 290762 | Hardcoded Bedrock model IDs |
| Model refresh transform | 894688-894695 | Transform models on refresh |
| Toggle handler | 910567-910574 | Add/remove models on toggle |
| Default test model | 910577 | Default model ID for testing |
| BedrockCredentials proto | 141286-141331 | Protobuf message definition |
| Test credentials | 895192-895202 | Credential validation API |
| Settings UI | 910643-910654 | Region input field |
| IAM role default | 1098122-1098127 | Default region for enterprise |

## Conclusion

The Bedrock regional prefix system is a straightforward string replacement mechanism that transforms `us.` prefixes to regional equivalents (`apac.`, `eu.`, `ca.`) based on the first few characters of the user's AWS region setting. This aligns with AWS Bedrock's Cross-Region Inference (CRI) model naming convention.

The implementation is robust for common use cases but has gaps around validation, regional coverage, and error handling for edge cases.
