# TASK-116: Experiment Service and Feature Gates System Analysis

## Overview

Cursor IDE 2.3.41 implements a sophisticated experiment/feature gating system powered by **Statsig**, a third-party feature flagging and A/B testing platform. The system supports three types of configurations:

1. **Feature Gates** (boolean flags)
2. **Experiments** (A/B tests with multiple parameters)
3. **Dynamic Configs** (server-configurable JSON objects)

## Architecture

### ExperimentService (Core Implementation)

**Location:** `out-build/vs/workbench/services/experiment/browser/experimentService.js` (line 295926)

**Service ID:** `yc = on("experimentService")`

The ExperimentService is the central interface for all experiment/feature gate checks. It wraps the Statsig SDK and provides:

- Synchronous gate checking (`checkFeatureGate`)
- Experiment parameter retrieval (`getExperimentParam`, `getExperimentGroup`)
- Dynamic config retrieval (`getDynamicConfigParam`)
- Override management for development/testing
- Bootstrap caching for fast startup

### Key Storage Keys

```javascript
FEATURE_FLAG_OVERRIDES_STORAGE_KEY = "workbench.experiments.featureFlagOverrides"
EXPERIMENT_OVERRIDES_STORAGE_KEY = "workbench.experiments.experimentOverrides"
DYNAMIC_CONFIG_OVERRIDES_STORAGE_KEY = "workbench.experiments.dynamicConfigOverrides"
STATSIG_BOOTSTRAP_STORAGE_KEY = "workbench.experiments.statsigBootstrap"
```

## Statsig Integration

### Client Initialization

```javascript
this._statsig = new StatsigClient(
    this.productService.statsigClientKey ?? "",
    user,
    {
        dataAdapter: dataAdapter,
        loggingEnabled: hasProxyUrl ? "always" : "disabled",
        disableStorage: true,
        logEventCompressionMode: "Forced",
        networkConfig: {
            api: statsigLogEventProxyUrl,
            // Only /rgstr (logging) endpoint uses network
            // All other traffic is blocked
            networkOverrideFunc: ...
        }
    }
)
```

### Bootstrap Flow

1. **Cache Initialization:** On startup, loads cached bootstrap data from `STATSIG_BOOTSTRAP_STORAGE_KEY`
2. **Server Refresh:** Polls `bootstrapStatsig` gRPC endpoint for fresh configuration
3. **User Context:** Includes `userID` (auth ID), `operatingSystem`, and `ignoreDevStatus`
4. **Polling:** Continues polling at configurable intervals (default ~5 seconds, min 1 second)

```javascript
async _refreshBootstrapFromServer(trigger = "poll") {
    const response = await backend.bootstrapStatsig({
        ignoreDevStatus: ignoreDevStatus,
        operatingSystem: clientOS
    });
    this.experimentService.refreshStatsigConfig(response.config, user, trigger);
}
```

## Gate Evaluation Logic

### checkFeatureGate(gateName)

Priority order:
1. **Override Check:** If `_canUseOverrides()` and gate has override, return override value
2. **Uninitialized Fallback:** If Statsig not ready or disabled, return `Pke[gateName]?.default ?? false`
3. **Statsig Evaluation:** Call `this._statsig.checkGate(gateName)`
4. **Error Fallback:** On error, return default value

### Override Eligibility (_canUseOverrides)

```javascript
_canUseOverrides() {
    // Allow overrides in:
    // 1. Test mode (enableSmokeTestDriver)
    // 2. Non-production builds (!isBuilt || isExtensionDevelopment)
    // 3. When isDevUser context key is true
    return this._isTestMode ||
           !(this.environmentService.isBuilt && !this.environmentService.isExtensionDevelopment) ||
           !!this.contextKeyService.getContextKeyValue("isDevUser");
}
```

## Feature Gate Configuration (Pke)

**Location:** `out-build/vs/platform/experiments/common/experimentConfig.gen.js` (line 293382)

Each gate is defined with:
- `client: boolean` - Whether it's evaluated on client vs server
- `default: boolean` - Fallback value when Statsig is unavailable

### Complete Feature Gate List (Extracted from Pke)

#### AI/Agent Features
| Gate Name | Client | Default | Description |
|-----------|--------|---------|-------------|
| `enable_agent_web_search` | true | true | Web search capability in agent |
| `enable_git_status_in_system_prompt` | true | false | Git status in system prompt |
| `mcp_discovery` | true | true | MCP server discovery |
| `mcp_allowlists` | true | false | MCP allowlist feature |
| `mcp_file_system` | true | false | MCP filesystem access |
| `mcp_embedded_resources` | true | false | MCP embedded resources |
| `spec_mode` | true | false | Spec/planning mode |
| `ide_nal` | true | false | IDE new agent loop |
| `quick_agent` | true | false | Quick agent feature |
| `nal_task_tool` | true | false | NAL task tool |
| `nal_async_task_tool` | true | false | NAL async task tool |
| `auto_resume` | true | false | Auto-resume conversations |

#### Model/Inference Features
| Gate Name | Client | Default | Description |
|-----------|--------|---------|-------------|
| `gpt_52_model_enabled` | false | true | GPT 5.2 model availability |
| `gpt_52_model_default_on` | false | true | GPT 5.2 as default |
| `gpt_51_codex_max_model_enabled` | false | true | GPT 5.1 Codex Max |
| `gemini3_default_on` | false | false | Gemini 3 as default |
| `gemini3_flash_default_on` | false | true | Gemini 3 Flash as default |
| `claude45_opus_default_on` | false | true | Claude 4.5 Opus as default |
| `reveal_model_behind_auto` | false | false | Show model behind "auto" |

#### Bugbot/Review Features
| Gate Name | Client | Default | Description |
|-----------|--------|---------|-------------|
| `editor_bugbot` | true | false | Editor bugbot feature |
| `editor_bugbot_deep_review_enabled` | true | true | Deep review capability |
| `bugbot_autorun_killswitch` | true | false | Kill switch for autorun |
| `bugbot_enable_severity` | false | false | Severity classification |
| `bugbot_editor_autorun_on_composer_finish` | true | false | Autorun after composer |

#### Cloud Agent Features
| Gate Name | Client | Default | Description |
|-----------|--------|---------|-------------|
| `cloud_agent_new_conversation_stream` | true | true | New conversation streaming |
| `cloud_agent_computer_use` | false | false | Computer use capability |
| `cloud_agent_private_workers` | false | false | Private worker support |
| `enable_cloud_agent_test_changes_checkbox` | true | false | Test changes UI |

#### Sandbox/Security Features
| Gate Name | Client | Default | Description |
|-----------|--------|---------|-------------|
| `sandbox_force_disable_linux` | true | false | Disable sandbox on Linux |
| `sandbox_force_disable_win32` | true | false | Disable sandbox on Windows |
| `composer1_sandboxing` | false | false | Composer sandboxing |
| `playwright_autorun` | true | false | Playwright auto-execution |

#### UI/UX Features
| Gate Name | Client | Default | Description |
|-----------|--------|---------|-------------|
| `force_to_agent_layout` | true | false | Force agent layout |
| `prevent_switch_layout` | true | true | Prevent layout switching |
| `hide_titlebar_default` | true | false | Hide titlebar by default |
| `color_token_in_markdown` | true | true | Color tokens in markdown |
| `fast_checkpoints` | true | true | Fast checkpoint system |
| `new_file_ux` | true | true | New file UX |

#### Networking/Performance
| Gate Name | Client | Default | Description |
|-----------|--------|---------|-------------|
| `http2_disable_pings` | true | false | Disable HTTP/2 pings |
| `retry_interceptor_disabled` | true | true | Disable retry interceptor |
| `retry_interceptor_enabled_for_streaming` | true | true | Retries for streaming |
| `use_brotli_compression` | true | true | Brotli compression |
| `client_database_wal` | true | true | WAL mode for client DB |

## Experiments Configuration (UZ)

A/B testing experiments with parameters and fallback values.

### Key Experiments

#### `sonnet45_to_opus45`
- Tests migration from Claude Sonnet to Opus
- Parameters: `enabled: boolean`

#### `individual_plan_limits`
- Tests usage limit variations
- Groups: `control`, `lower_auto`, `lower_both`
- Parameters: `auto_limit`, `api_limit`

#### `improved_ide_team_limit_ux`
- Tests team limit UX variations
- Groups: `control`, `group1`, `group2`

#### `cursor_extensions_isolation_v2`
- Extension isolation feature
- Parameters: `enabled: boolean`

#### `bugbot_different_validators_ab`
- Tests different bugbot validator configurations
- Groups include variations of Gemini and validator usage

## Dynamic Configs (Yue)

Server-configurable objects that can be updated without client releases.

### Key Dynamic Configs

#### `editor_bugbot_config`
```javascript
{
    model: "claude-4-5-sonnet-20250929",
    iterations: 0,
    agentic_iterations: 1,
    agentic_model: "claude-4.5-haiku",
    context_lines: 10
}
```

#### `opus45_config`
```javascript
{
    dropdownPosition: "after-composer",
    defaultOnModels: ["claude-4.5-opus-high-thinking"]
}
```

#### `parallel_agent_ensemble_config`
```javascript
{
    models: ["gpt-5.1-codex-high", "claude-4.5-sonnet-thinking", ...],
    gatherTimeoutMs: 300000,
    gatherMinSuccessPercentage: 0.5,
    gatherMinSuccessCount: null
}
```

#### `tool_limits_config`
- Controls limits for file search, file read, and directory listing
- Parameters: `fileSearchToolMaxResults`, `readFileV2ToolMaxFileSizeInBytes`, etc.

#### `tools_concurrency_config`
```javascript
{
    tools: {
        RIPGREP_RAW_SEARCH: { ttl: 10000, maxConcurrent: 5 },
        RIPGREP_SEARCH: { ttl: 10000, maxConcurrent: 5 }
    },
    defaultTtl: 10000,
    defaultMaxConcurrent: 999999
}
```

#### `client_version_config`
```javascript
{
    minAllowedClientVersion: "1.3.0",
    minSupportedClientVersion: "1.5.0"
}
```

## Usage Patterns

### Direct Gate Check
```javascript
if (experimentService.checkFeatureGate("mcp_allowlists")) {
    // Feature-gated code path
}
```

### Reactive Gate Property
```javascript
const gateProperty = experimentService.getFeatureGateProperty("mcp_allowlists");
this._register(gateProperty.onChange(value => {
    // React to gate changes
}));
```

### Dynamic Config Access
```javascript
const maxResults = experimentService.getDynamicConfigParam(
    "tool_limits_config",
    "fileSearchToolMaxResults"
);
```

### Experiment Parameter
```javascript
const enabled = experimentService.getExperimentParam(
    "playwright_suggestion",
    "enabled"
);
```

## Developer Tools

### Feature Flag Override UI
**Command:** `workbench.action.manageFeatureFlagOverrides` (Developer: Manage Feature Flag Overrides)

Available only when:
- Development build OR
- `isDevUser` context key is true (set by server config)

Allows toggling individual feature gates for testing.

### Test Mode Support

When `enableSmokeTestDriver` is set:
- Statsig is completely disabled
- Uses default values from `Pke`
- Accepts base64-encoded JSON for test flags via `testFeatureFlags` environment variable
- Accepts base64-encoded JSON for test configs via `testDynamicConfigs`

## Header Propagation

Override values are propagated to the server via headers:
```javascript
getOverridesForHeader() {
    // Returns JSON with:
    // - featureFlags: { gateName: boolean }
    // - experiments: { experimentName: { params } }
    // - dynamicConfigs: { configName: { params } }
    // Limited to 32768 characters
}
```

## Metrics

The service emits extensive metrics:
- `experimentService.blocking_time` - Initialization blocking time
- `experimentService.bootstrap.source` - Bootstrap data source (cache/network)
- `experimentService.gate_check_error` - Gate evaluation errors
- `experimentService.override_gate_check` - Override usage
- `experimentService.server_refresh_time` - Server poll latency
- `experimentService.time_to_initialized_ms` - Time to full initialization

## Security Considerations

1. **Server Authority:** Production builds respect server-side `isDevDoNotUseForSecretThingsBecauseCanBeSpoofedByUsers` flag
2. **Override Restrictions:** Overrides blocked in production unless server explicitly allows
3. **Gate Hash:** SHA-256 hash of enabled gates tracked for debugging
4. **Event Logging:** Statsig event logging goes through proxy URL only

## gRPC Integration

Bootstrap data is fetched via gRPC:
```javascript
bootstrapStatsig: {
    name: "BootstrapStatsig",
    I: BootstrapStatsigRequest,
    O: BootstrapStatsigResponse,
    kind: Unary
}
```

The response contains a full Statsig configuration JSON that is parsed and used to hydrate the client.

## Implications for Reverse Engineering

1. **Feature Discovery:** The complete list of feature gates reveals unreleased/testing features
2. **Server Control:** Many features are server-gated, meaning they require backend enablement
3. **A/B Testing:** User assignment to experiment groups affects available features
4. **Override Path:** Development overrides provide a way to test features locally
5. **Model Configuration:** Dynamic configs control which AI models are used

## Notable Upcoming/Hidden Features

Based on feature gates with `default: false`:
- `agent_projects` - Project management in agent
- `parallel_agent_workflow` - Parallel agent execution
- `enable_skills` - Skill system
- `rules_v2` - New rules system
- `shared_chats` - Chat sharing functionality
- `cloud_agent_computer_use` - Computer use API
- `artifacts_review_changes_tab` - Artifacts tab in review

## References

- Line 293382: `experimentConfig.gen.js` - Feature gate definitions
- Line 295926: `experimentService.js` - Core service implementation
- Line 973679: Bootstrap refresh logic
- Line 811525: gRPC `bootstrapStatsig` method definition
