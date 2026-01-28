# TASK-100: Partner Data Sharing and Third-Party Model Privacy Analysis

Analysis of how Cursor IDE handles partner data sharing, third-party model provider interactions, and the privacy implications for user code and prompts when using non-Cursor models.

## Executive Summary

Cursor IDE routes AI requests through different model providers (OpenAI, Anthropic/Claude, Google/Gemini, AWS Bedrock) based on the selected model. The privacy mode system has granular controls, but **the critical finding is that "partnerDataShare" flag determines whether prompts and telemetry are shared with third-party model providers** even when "Privacy Mode" is enabled.

**Key Privacy Implications:**
1. Privacy Mode does NOT automatically protect against third-party model provider data sharing
2. The `partnerDataShare` flag is fetched from server and can be enabled even for privacy-mode users
3. User-selected models explicitly route data to their respective providers (OpenAI, Anthropic, Google, AWS)
4. The BYOK (Bring Your Own Key) feature sends data directly to third-party APIs

## The partnerDataShare Flag

### Definition

**Source**: Line 282876 in `workbench.desktop.main.js`

```javascript
// GetUserPrivacyModeResponse includes partnerDataShare
class GetUserPrivacyModeResponse {
  constructor(e) {
    this.privacyMode = wh.UNSPECIFIED;
    this.hoursRemainingInGracePeriod = 0;
    this.isEnforcedByTeam = false;
    this.isNotMigratedToServerSourceOfTruth = false;
    this.partnerDataShare = false;   // <-- KEY FLAG
    this.hasAcknowledgedGracePeriodDisclaimer = false;
    v.util.initPartial(e, this);
  }
}
```

### Storage Key

**Source**: Line 290762 in `workbench.desktop.main.js`

```javascript
Dps = "cursorai/donotchange/partnerDataShare"
```

### Where It's Used

**Source**: Line 1097822 in `workbench.desktop.main.js`

```javascript
this.partnerDataShare = () => this.storageService.get(Dps, -1) === "true";

this.fetchUserPrivacyMode = async ee => {
  // ...fetch from server
  pe = ne.partnerDataShare;  // Server returns this flag
}
```

### UI Disclosure

**Source**: Line 1138292 in `workbench.desktop.main.js`

When `partnerDataShare` is true, the onboarding UI displays:

```javascript
// When partnerDataShare is enabled
"Prompts and limited telemetry may also be shared with model providers
when you explicitly select their models."
```

**Source**: Line 905821 in `workbench.desktop.main.js`

In settings, the same warning appears in the Share Data option:
```javascript
U(xe, {
  get when() {
    return P()  // P = partnerDataShare flag
  },
  children: ". Prompts and limited telemetry may also be shared with
             model providers when you explicitly select their models"
})
```

## Third-Party Model Provider Categorization

### Model Provider Detection Functions

**Source**: Line 290767 in `workbench.desktop.main.js`

```javascript
// Claude/Anthropic model detection
Pps = ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"];
l7r = i => Pps.includes(i) || i.startsWith("claude-");

// Google/Gemini model detection
Lps = ["gemini-1.5-flash", "gemini-1.5-flash-8b"];
qQl = ["gemini-1.5-preview"];  // Excluded Gemini models
c7r = i => Lps.includes(i) || i.startsWith("gemini-") && !qQl.includes(i);

// AWS Bedrock regional model names
JQl = [
  "us.anthropic.claude-sonnet-4-20250514-v1:0",
  "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "us.anthropic.claude-3-5-haiku-20241022-v1:0",
  "us.anthropic.claude-haiku-4-5-20251001-v1:0",
  "us.anthropic.claude-opus-4-20250514-v1:0",
  "us.anthropic.claude-opus-4-1-20250805-v1:0",
  "us.anthropic.claude-opus-4-5-20251101-v1:0"
];
```

### API Key Routing Logic

**Source**: Line 299559-299560 in `workbench.desktop.main.js`

```javascript
getUseApiKeyForModel(e) {
  // If Claude model and user has Claude key enabled
  if (l7r(e) && this.reactiveStorageService.applicationUserPersistentStorage.useClaudeKey) {
    return this.reactiveStorageService.applicationUserPersistentStorage.useClaudeKey;
  }

  // If Google/Gemini model and user has Google key enabled
  if (c7r(e) && this.reactiveStorageService.applicationUserPersistentStorage.useGoogleKey) {
    return true;
  }

  // Default to OpenAI key
  return this.getUseOpenAIKey();
}
```

### API Key Resolution

**Source**: Line 1097721-1097722 in `workbench.desktop.main.js`

```javascript
getApiKeyForModel(e) {
  // Return appropriate API key based on model type
  if (l7r(e) && this._reactiveStorageService.applicationUserPersistentStorage.useClaudeKey) {
    return this.claudeKey();
  }
  if (c7r(e) && this._reactiveStorageService.applicationUserPersistentStorage.useGoogleKey) {
    return this.googleKey();
  }
  return this.openAIKey();
}
```

## BYOK (Bring Your Own Key) System

### Overview

The BYOK feature allows users to use their own API keys for third-party model providers, which means:
1. **Data flows directly to the third-party provider's API**
2. **Cursor does not intermediate the request** (for billing models)
3. **Third-party provider policies apply directly**

### BYOK Settings UI

**Source**: Line 1097223 in `workbench.desktop.main.js`

```javascript
// BYOK settings panel
RPm = be(`<div class=settings__item>
  <div class=settings__item_title>Bring-your-own-key</div>
  <div class=settings__item_description>
    If you'd like, you can put in your OpenAI api key to use Cursor at-cost.
  </div>
  <div class=openai-settings-container>
    <div class=openai-area>
      <input placeholder="Enter your OpenAI API Key">
      <button class=cursor-settings-submit-button>Update
`)
```

### BYOK Disabled by Admin

**Source**: Line 277065 in `workbench.desktop.main.js`

Team admins can disable BYOK:

```javascript
{
  no: 17,
  name: "byok_disabled",
  kind: "scalar",
  T: 8  // boolean
}
```

**Source**: Line 290782 in `workbench.desktop.main.js`

Default admin settings include:
```javascript
Mps = {
  allowedModels: [],
  blockedModels: [],
  dotCursorProtection: false,
  browserFeatures: false,
  browserOriginAllowlist: [],
  allowedMcpConfiguration: undefined,
  byokDisabled: false,  // Default: BYOK is allowed
  // ...
}
```

## AWS Bedrock Integration

### Bedrock State Storage

**Source**: Line 91733 in `workbench.desktop.main.js`

```javascript
class BedrockState {
  constructor(e) {
    this.accessKey = "";
    this.secretKey = "";
    this.region = "";
    this.useBedrock = false;
    this.sessionToken = "";
    v.util.initPartial(e, this);
  }
  // typeName = "aiserver.v1.BedrockState"
}
```

### Bedrock Model Name Regionalization

**Source**: Line 894673-894694 in `workbench.desktop.main.js`

```javascript
regionalBedrockId(e) {
  const t = this._reactiveStorageService.applicationUserPersistentStorage.bedrockState?.region || "";
  // Prepend region to bedrock model ID
}

// Models are transformed to include region:
{
  name: this.regionalBedrockId(P.name || ""),
  serverModelName: this.regionalBedrockId(P.serverModelName || ""),
  clientDisplayName: this.regionalBedrockId(P.clientDisplayName || ""),
  inputboxShortModelName: this.regionalBedrockId(P.inputboxShortModelName || "")
}
```

### Bedrock IAM Role Validation

**Source**: Line 278987 in `workbench.desktop.main.js`

```javascript
class ValidateBedrockIamRoleRequest {
  constructor(e) {
    this.teamId = 0;
    this.bedrockIamRole = "";
    this.region = "";
    this.modelId = "";
  }
  // typeName = "aiserver.v1.ValidateBedrockIamRoleRequest"
}
```

## Privacy Mode Interaction with Third-Party Data

### Privacy Mode Levels Recap

```javascript
wh = {
  UNSPECIFIED: 0,
  NO_STORAGE: 1,         // Most restrictive
  NO_TRAINING: 2,        // No training but storage allowed
  USAGE_DATA_TRAINING_ALLOWED: 3,
  USAGE_CODEBASE_TRAINING_ALLOWED: 4  // Least restrictive
}
```

### Critical Insight: Privacy Mode Does NOT Block Third-Party Sharing

The `partnerDataShare` flag operates **independently** of the privacy mode setting:

**Source**: Line 1138287-1138294 in `workbench.desktop.main.js`

```javascript
// In onboarding, shown regardless of privacy mode choice:
return [jPu(), " After one day of use, Cursor stores and learns from
your prompts, codebase, edit history, and other usage data to improve
the product.", U(xe, {
  get when() {
    return l()  // l = partnerDataShare condition
  },
  get children() {
    return [" ", "Prompts and limited telemetry may also be shared
    with model providers when you explicitly select their models."]
  }
})]
```

### What Privacy Mode Actually Protects

Based on the analysis, Privacy Mode controls:

| Setting | NO_STORAGE | NO_TRAINING | DATA_SHARING |
|---------|------------|-------------|--------------|
| Code storage by Cursor | NO | YES | YES |
| Training by Cursor | NO | NO | YES |
| Background Agent | NO | YES | YES |
| **Third-party model sharing** | **Via partnerDataShare** | **Via partnerDataShare** | **Via partnerDataShare** |

### The Model Provider Request JSON

**Source**: Line 124185 in `workbench.desktop.main.js`

Requests include a `model_provider_request_json` field:

```javascript
{
  no: 35,
  name: "model_provider_request_json",
  kind: "scalar",
  T: 9,  // string
  opt: true
}
```

This field can be downloaded for debugging:

**Source**: Line 744939-744975 in `workbench.desktop.main.js`

```javascript
d = () => po(() => {
  if (i.message.modelProviderRequestJson) return i.message.modelProviderRequestJson;
  // ... search conversation for request JSON
});

h = () => {
  const M = d();
  if (!M) {
    e.notificationService.notify({
      message: "No request content available",
      severity: Qs.Info
    });
    return
  }
  // Download as JSON file
  const B = new Blob([M], { type: "application/json" });
  J.download = `request-${D()||"content"}.json`;
  // ...
}
```

## Data Sharing Discount

**Source**: Line 272502 in `workbench.desktop.main.js`

There's a `data_sharing_discount_eligible` field suggesting pricing incentives for data sharing:

```javascript
{
  no: 22,
  name: "data_sharing_discount_eligible",
  kind: "scalar",
  T: 8  // boolean
}
```

## Grace Period System

### One Day Protection

**Source**: Line 905711 in `workbench.desktop.main.js`

New users have a grace period:

```javascript
Czf = be("<div><span><strong>Data Sharing is paused for your first day
of usage.</strong> Sharing will activate in <!> hour<!>.")
```

**Source**: Line 1138199 in `workbench.desktop.main.js`

```javascript
jPu = be("<b>Data sharing is off the first day.")
```

### Grace Period Acknowledgment

**Source**: Line 1138226-1138239 in `workbench.desktop.main.js`

```javascript
n() && (async () => {
  await (await e.aiService.aiClient()).acknowledgeGracePeriodDisclaimer({})
})().catch(() => {
  // Retry logic with 300 second delays
  setTimeout(() => {
    // retry
  }, 300 * 1e3)
})
```

## Privacy Claims Analysis

### Onboarding Privacy Mode Description

**Source**: Line 1138426 in `workbench.desktop.main.js`

```javascript
subtitle: "I do not want to enable data sharing.",
description: "With Privacy Mode enabled, none of your questions or code
will ever be stored or learned from by us or any third-party."
```

**Source**: Line 1138562 in `workbench.desktop.main.js`

```javascript
description: "If you enable Privacy Mode, none of your questions or code
will ever be stored by us or any third-party."
```

### Discrepancy Identified

The UI claims "none of your questions or code will ever be stored...by any third-party" but:

1. When using BYOK, requests go directly to third-party APIs (OpenAI, Anthropic, Google)
2. Third-party providers have their own data retention policies
3. The `partnerDataShare` flag indicates telemetry is shared with model providers

**This creates a potential discrepancy between the privacy mode claim and actual behavior when:**
- User selects a third-party model explicitly
- User uses BYOK with their own API key
- `partnerDataShare` is enabled server-side

## Default Models and Providers

### Default Model Configuration

**Source**: Line 182750 in `workbench.desktop.main.js`

```javascript
{
  bestOfNDefaultModels: ["composer-1", "claude-4.5-opus-high", "gpt-5.1-codex"]
}
```

**Source**: Line 711400 in `workbench.desktop.main.js`

```javascript
var Pcf = ["composer-1", "claude-4.5-opus-high", "gpt-5.1-codex"];
```

### Model Provider Categories

Based on the codebase analysis:

| Provider | Models | BYOK Support |
|----------|--------|--------------|
| OpenAI | gpt-4o-mini, gpt-*, o1-*, o3-* | Yes (openAIKey) |
| Anthropic | claude-* | Yes (claudeKey) |
| Google | gemini-* | Yes (googleKey) |
| AWS Bedrock | us.anthropic.* | Yes (bedrockState) |
| Cursor | composer-*, auto-*, default | N/A (native) |

## Metrics and Telemetry Collection

### Model Provider Telemetry Events

**Source**: Line 828210 in `workbench.desktop.main.js`

```javascript
name: "CHAT_REQUEST_EVENT_TYPE_MODEL_PROVIDER_REQUEST_START"
```

### Privacy Mode Metrics Tags

**Source**: Line 893842 (from TASK-76 analysis)

```javascript
tags.push(`privacy_mode:${this._privacyModeEnabled}`);
```

## Summary of Privacy Implications

### What Is Protected by Privacy Mode (NO_STORAGE)

1. Code is not stored by Cursor servers
2. Prompts are not stored by Cursor servers
3. No training on user data by Cursor
4. Background Agent is disabled

### What Is NOT Protected

1. **When using BYOK**: Data flows directly to third-party APIs
2. **When partnerDataShare is true**: Limited telemetry shared with providers
3. **When explicitly selecting third-party models**: Prompts sent to that provider
4. **Third-party provider retention policies**: Outside Cursor's control

### Recommendations for Investigation

1. **Traffic analysis**: Capture requests when using different models to verify data flow
2. **Server-side partnerDataShare logic**: Understand when server sets this flag
3. **BYOK request interception**: Verify whether BYOK bypasses Cursor servers entirely
4. **Third-party provider agreements**: Review Cursor's agreements with OpenAI, Anthropic, Google

## Related Tasks

- TASK-76: Privacy Mode System (detailed privacy mode mechanics)
- TASK-78: AWS Bedrock Integration (Bedrock-specific data flow)

## Code References

| Feature | Location in workbench.desktop.main.js |
|---------|--------------------------------------|
| partnerDataShare definition | Line 282876 |
| partnerDataShare storage key | Line 290762 (Dps) |
| Model provider detection | Lines 290767 (l7r, c7r functions) |
| BYOK API key routing | Lines 299559-299560 |
| Privacy mode UI claims | Lines 1138426, 1138562 |
| Grace period disclosure | Lines 905711, 1138199 |
| Data sharing UI options | Lines 905773-905842 |
| Model provider request JSON | Line 124185 |
| Bedrock state | Line 91733 |
| BYOK disabled by admin | Line 277065 |
