# TASK-1: Cursor Agent API (api5.cursor.sh) Analysis

## Overview

The agent API endpoints at `api5.cursor.sh` are used for Cursor's Background Composer feature - the autonomous AI agent that runs in a remote VM to perform code editing tasks.

## Endpoint Mapping

### Production Endpoints

| Variable | URL | Purpose |
|----------|-----|---------|
| `u6t` | https://agent.api5.cursor.sh | Privacy mode agent (default) |
| `d6t` | https://agentn.api5.cursor.sh | Non-privacy mode agent (default) |
| `h6t` | https://agent-gcpp-uswest.api5.cursor.sh | Privacy mode agent (US West) |
| `f6t` | https://agentn-gcpp-uswest.api5.cursor.sh | Non-privacy mode agent (US West) |
| `qEl` | https://agent-gcpp-eucentral.api5.cursor.sh | Privacy mode agent (EU Central) |
| `JEl` | https://agentn-gcpp-eucentral.api5.cursor.sh | Non-privacy mode agent (EU Central) |

**Source:** Line 182746 in `beautified/workbench.desktop.main.js`

## Agent vs Agentn: Privacy Mode Distinction

The naming convention reveals the key difference:
- **`agent.*`** endpoints: Used when **Privacy Mode is ENABLED** (NO_STORAGE)
- **`agentn.*`** endpoints: Used when **Privacy Mode is DISABLED** (allows storage/training)

The "n" in "agentn" likely stands for "non-privacy" or "normal" mode.

### Privacy Mode Values (PrivacyMode enum)

From `aiserver.v1.PrivacyMode`:
```
PRIVACY_MODE_UNSPECIFIED = 0
PRIVACY_MODE_NO_STORAGE = 1      -> Uses agent.* (privacy pod)
PRIVACY_MODE_NO_TRAINING = 2
PRIVACY_MODE_USAGE_DATA_TRAINING_ALLOWED = 3
PRIVACY_MODE_USAGE_CODEBASE_TRAINING_ALLOWED = 4
```

When privacy mode is `NO_STORAGE`, the client connects to the `agent.*` endpoints which are designated as "privacy pods" that don't store user data.

## Geographic Endpoint Selection

The client stores two sets of URLs for each privacy setting:

```javascript
agentBackendUrlPrivacy: {
    default: "https://agent.api5.cursor.sh",       // u6t
    "us-west-1": "https://agent-gcpp-uswest.api5.cursor.sh"  // h6t
}
agentBackendUrlNonPrivacy: {
    default: "https://agentn.api5.cursor.sh",      // d6t
    "us-west-1": "https://agentn-gcpp-uswest.api5.cursor.sh" // f6t
}
```

The "gcpp" in endpoint names likely means "GCP Pod" - indicating these run on Google Cloud Platform in specific regions.

### Available Region Configurations

1. **Prod (default)** - Uses default endpoints with US West fallback
2. **Prod EU Central 1 Agent** - Explicitly uses EU Central endpoints only

The EU Central configuration (line 440568-440588) only has `default` key without regional fallbacks:
```javascript
agentBackendUrlPrivacy: { default: qEl }   // EU Central privacy
agentBackendUrlNonPrivacy: { default: JEl } // EU Central non-privacy
```

### getAgentBackendUrls Function (Line 440802)

```javascript
getAgentBackendUrls(e) {
    // Local development - both privacy and non-privacy use same endpoint
    return e.includes("localhost") || e.includes("lclhst.build") ? {
        privacy: { default: e, "us-west-1": e },
        nonPrivacy: { default: e, "us-west-1": e }
    } : e.includes(mB) || e.includes(hbe) ? {
        // Staging environments
        privacy: { default: e, "us-west-1": e },
        nonPrivacy: { default: e, "us-west-1": e }
    } : {
        // Production - separate privacy and non-privacy endpoints
        privacy: { default: u6t, "us-west-1": h6t },
        nonPrivacy: { default: d6t, "us-west-1": f6t }
    }
}
```

## gRPC Services on Agent Endpoints

### `agent.v1.AgentService` (PPs variable at line 555870)

Primary service for agent operations:
| Method | Kind | Description |
|--------|------|-------------|
| `Run` | BiDiStreaming | Main bidirectional stream for agent execution |
| `RunSSE` | ServerStreaming | Server-sent events variant |
| `RunPoll` | ServerStreaming | Polling variant for environments without WebSocket |
| `NameAgent` | Unary | Generate name for an agent session |
| `GetUsableModels` | Unary | Get list of models available for CLI |
| `GetDefaultModelForCli` | Unary | Get default model for CLI usage |
| `GetAllowedModelIntents` | Unary | Get allowed intents per model |

### `aiserver.v1.BackgroundComposerService` (Dyo variable at line 815696)

Full background composer management service:
| Method | Kind | Description |
|--------|------|-------------|
| `ListBackgroundComposers` | Unary | List all background composer instances |
| `AttachBackgroundComposer` | ServerStreaming | Attach to a running composer |
| `StreamInteractionUpdates` | ServerStreaming | Stream UI updates |
| `StreamInteractionUpdatesSSE` | ServerStreaming | SSE variant for updates |
| `StreamConversation` | ServerStreaming | Stream conversation messages |
| `GetLatestAgentConversationState` | Unary | Get current state |
| `GetBlobForAgentKV` | Unary | Get key-value blob data |
| `AttachBackgroundComposerLogs` | ServerStreaming | Stream logs |
| `StartBackgroundComposerFromSnapshot` | Unary | Start from saved state |
| `StartParallelAgentWorkflow` | Unary | Start parallel workflows |
| `StreamParallelAgentWorkflowStatus` | ServerStreaming | Stream parallel status |
| `MakePRBackgroundComposer` | Unary | Create PR from composer |
| `OpenPRBackgroundComposer` | Unary | Open PR in browser |
| `GetBackgroundComposerStatus` | Unary | Get status |
| `AddAsyncFollowupBackgroundComposer` | Unary | Add async followup |
| `GetCursorServerUrl` | Unary | Get server URL |
| `PauseBackgroundComposer` | Unary | Pause execution |
| `ResumeBackgroundComposer` | Unary | Resume execution |
| `ArchiveBackgroundComposer` | Unary | Archive composer |
| `GetBackgroundComposerInfo` | Unary | Get composer info |
| `GetBackgroundComposerRepositoryInfo` | Unary | Get repo info |
| `GetMachine` | Unary | Get VM machine info |
| `ListDetailedBackgroundComposers` | Unary | List with full details |

## Protobuf Message Structures

### agent.v1.AgentClientMessage (Line 142702)

The client-to-server message is a oneof with these message types:

| Field # | Name | Type | Description |
|---------|------|------|-------------|
| 1 | run_request | Uas | Initial run request |
| 2 | exec_client_message | wJ | Execution client message |
| 5 | exec_client_control_message | V4t | Execution control |
| 3 | kv_client_message | Jas | Key-value storage message |
| 4 | conversation_action | GR | Conversation action |
| 6 | interaction_response | HAr | Response to interaction query |
| 7 | client_heartbeat | Gfl | Heartbeat message |

### agent.v1.AgentServerMessage (Line 142771)

The server-to-client message is a oneof with these message types:

| Field # | Name | Type | Description |
|---------|------|------|-------------|
| 1 | interaction_update | g7 | UI/interaction update |
| 2 | exec_server_message | Hpe | Execution server message |
| 5 | exec_server_control_message | Gas | Execution control |
| 3 | conversation_checkpoint_update | U1 | Checkpoint update |
| 4 | kv_server_message | qfl | Key-value storage message |
| 7 | interaction_query | VAr | Query from server to client |

### agent.v1.NameAgentRequest (Line 142835)

Simple request to name an agent:
```protobuf
message NameAgentRequest {
    string user_message = 1; // User message to base name on
}
```

### agent.v1.NameAgentResponse (Line 142865)

```protobuf
message NameAgentResponse {
    string name = 1; // Generated agent name
}
```

### agent.v1.GetUsableModelsRequest (Line 142895)

```protobuf
message GetUsableModelsRequest {
    repeated string custom_model_ids = 1; // Optional custom model IDs to include
}
```

### agent.v1.GetUsableModelsResponse (Line 142925)

```protobuf
message GetUsableModelsResponse {
    repeated ModelInfo models = 1; // Available models
}
```

## Agent Client Service Architecture

### AgentClientService (Line 556920)

The `agentClientService` (GGt) is the main interface for running agent loops:

```javascript
var Pco = class extends Ve {
    constructor(e, t, n, s, r) {
        // Create backend client for AgentService
        this.backendClient = this.instantiationService.createInstance(aC, {
            service: PPs,  // agent.v1.AgentService
            headerInjector: async () => {
                // Inject filesync encryption header
                const l = await IZh(this.everythingProviderService),
                // Get retry interceptor config
                const d = this.experimentService.checkFeatureGate("retry_interceptor_enabled_for_streaming"),
                const h = this.experimentService.getDynamicConfig("retry_interceptor_params_config");
                return { ...l, ...g }
            }
        });
        // Wrap with mock support for testing
        this.client = new kro({
            async * run(l, d, h) {
                const f = await o.get(),
                    g = SZh(f, { injectTraceHeaders: !0 });
                for await (const p of g.run(l, d, h)) yield p
            }
        })
    }

    async run(e, t, n, s, r, o, a, l, d, h, f) {
        return this.client.run(e, t, n, s, r, o, a, l, d, h, f)
    }
}
```

### runAgentLoop Function (Line 940177)

The main agent execution loop:

```javascript
async * runAgentLoop(e, t) {
    // Extract parameters
    let { userText, richText, mode, selectedContext, requestContext,
          modelDetails, generationUUID, conversationId, messageId,
          abortController, onCheckpoint, resourceAccessor, bestOfNGroupId,
          tryUseBestOfNPromotion, headers, conversationState, onFirstToken, onHeader } = t;

    // Create conversation action manager
    let te = this.composerDataService.getComposerData(g)?.conversationActionManager;
    te || (te = new Cpt(g, w, this.instantiationService, f));

    // Build model config
    const ae = new SJ({
        modelId: h.modelName,
        maxMode: h.maxMode,
        credentials: this.convertModelDetailsToCredentials(h)
    });

    // Create user message action
    const pe = new GR({
        action: {
            case: "userMessageAction",
            value: new t3({
                userMessage: new sI({
                    text: r,
                    messageId: p ?? g,
                    selectedContext: l,
                    mode: a,
                    bestOfNGroupId: T,
                    tryUseBestOfNPromotion: D,
                    richText: o
                }),
                requestContext: d
            })
        }
    });

    // Run the agent client
    const ke = this.agentClientService.run(J, A, pe, ae, ce, E, Le, te, Re, [], Pe);

    // Yield streaming responses
    for await (const Ne of ne) {
        if (w.signal.aborted) break;
        Ne.response?.case === "streamUnifiedChatResponse" && (yield Ne.response.value)
    }
}
```

## Request/Response Flow

### Transport Architecture

1. **BackendClient (`aC` class)** - Creates service clients
   - Location: `out-build/vs/workbench/services/ai/browser/backendClient.js` (line 300276)
   - Uses `aiConnectRequestService` for transport

2. **ConnectRequestService (`otc` class)** - Manages transport providers
   - Location: `out-build/vs/workbench/services/ai/browser/connectRequestService.js` (line 300254)
   - Registers connect transport providers

3. **Transport Provider** - Handles actual HTTP/2 or gRPC-web calls
   - Uses Connect protocol from @bufbuild/connect
   - Headers injected for auth and experiment overrides

### Request Flow Diagram

```
User Action
    |
    v
ComposerAgentService.getAgentStreamResponse()
    |
    v
streamFromAgentBackend() -> builds request context
    |
    v
AgentService.runAgentLoop() / resume()
    |
    v
AgentClientService.run() -> BiDi streaming
    |
    v
BackendClient.get() -> creates Connect client
    |
    v
aiConnectRequestService.transport()
    |
    v
$streamAiConnect() (MainThread)
    |
    v
_proxy.$callAiConnectTransportProviderStream() (ExtHost)
    |
    v
HTTP/2 Request to agent.api5.cursor.sh or agentn.api5.cursor.sh
```

### Header Injection

Custom headers are added to each request (line 300298-300310):
- Standard auth headers (`Authorization: Bearer <token>`)
- `x-background-composer-env` for dev environments
- `X-Dev-Experiment-Overrides` for A/B testing
- Filesync encryption header (from EverythingProvider)
- Retry interceptor configuration

### Authentication Flow

1. `cursorAuthenticationService.getAccessToken()` retrieves the access token
2. Token is stored in `cursorAuth/accessToken` in storage
3. Bearer token is added as `Authorization` header
4. Token is refreshed via `refreshAccessToken()` if expired

```javascript
async getAuthenticationHeader() {
    const e = await this.getAccessToken();
    return { Authorization: `Bearer ${e}` }
}
```

## Service Name Maps

The code maintains two service name maps for routing:

1. **`Oyo` (SERVICE_NAME_MAP_AISERVER_V1)** - Contains aiserver.v1.* services (line 831611)
2. **`zsu` (SERVICE_NAME_MAP_AGENT_V1)** - Contains agent.v1.* services (line 808429):
   - `agent.v1.AgentService` (PPs)
   - `agent.v1.ControlService` (Vsu)
   - `agent.v1.ExecService` (Hsu)
   - `agent.v1.PrivateWorkerBridgeExternalService` (qsu)
   - `agent.v1.LifecycleService` (Jsu)
   - `agent.v1.PtyHostService` (Gsu)

## Backend Server Environments

Available server configurations (TN enum at line 440833):

| Environment | Port | Description |
|-------------|------|-------------|
| Prod | 1814 | Production servers |
| ProdEuCentral1Agent | 1813 | EU Central production |
| Staging | 1815 | Staging environment |
| StagingLocalWebsite | 1816 | Staging with local website |
| LocalExceptCppAndEmbeddings | 1817 | Local dev except Cpp |
| LocalExceptCPP | 1818 | Local dev |
| FullLocal | 1819 | Full local dev |
| LocalExceptEmbeddings | 1820 | Local except embeddings |
| DevStaging | 1821 | Dev staging |
| LocalExceptCppAndEmbeddingsStaging | 1822 | Local staging |

## Default Model Configuration

From line 182746-182781, the default models are configured based on date:

```javascript
// Special opus model during specific time window
HEl = new Date("2025-11-24T20:00:00Z"),
$El = new Date("2025-12-06T11:59:00Z"),
scs = Date.now() >= HEl.getTime() && Date.now() < $El.getTime()
    ? "claude-4.5-opus-high-thinking"
    : "default";

J1e = {
    composer: {
        defaultModel: scs,
        fallbackModels: [],
        bestOfNDefaultModels: ["composer-1", "claude-4.5-opus-high", "gpt-5.1-codex"]
    },
    cmdK: { defaultModel: "default", ... },
    backgroundComposer: { defaultModel: "default", ... },
    planExecution: { defaultModel: "default", ... },
    spec: { defaultModel: "default", ... },
    deepSearch: { defaultModel: "default", ... },
    quickAgent: { defaultModel: "default", ... }
}
```

## Response Types

Key response types indicating server state:
- `isOnPrivacyPod: boolean` - Whether running on privacy-enabled infrastructure
- `isGhostModeOn: boolean` - Whether ghost/ephemeral mode is active

## Privacy Mode and Cloud Agents

Cloud Agents (Background Agents) are NOT available in "Privacy Mode (Legacy)" which is the NO_STORAGE mode:

```javascript
// Line 1140760-1140786
title: "Cloud Agents Not Supported in Privacy Mode (Legacy)"
message: "Your team admin can switch to 'Privacy Mode' to use cloud agents."
// Throws: "Background agent not available in privacy mode with no storage"
```

Users must enable data storage to use Cloud Agents.

## Open Questions for Further Investigation

1. **How is the geographic endpoint selected at runtime?** The code stores both `default` and `us-west-1` options but the selection logic wasn't fully traced - likely based on latency or user settings.

2. **What triggers the switch between BiDi streaming (Run) vs ServerStreaming (RunSSE)?** Likely depends on client capabilities and network conditions.

3. **How does the checkpoint system work for resuming agent sessions?** See `conversationCheckpointUpdate` messages and the `resume()` method.

4. **What is the full schema for interaction_update messages?** These drive the UI updates during agent execution.

---

## Files Referenced

- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
  - Line 142702: AgentClientMessage protobuf
  - Line 142771: AgentServerMessage protobuf
  - Line 182746: Endpoint URL definitions
  - Line 300276: BackendClient class
  - Line 440802: getAgentBackendUrls function
  - Line 555870: AgentService definition (PPs)
  - Line 556920: AgentClientService (GGt)
  - Line 808429: SERVICE_NAME_MAP_AGENT_V1 (zsu)
  - Line 815696: BackgroundComposerService definition
  - Line 832123: $streamAiConnect transport handler
  - Line 940177: runAgentLoop function
