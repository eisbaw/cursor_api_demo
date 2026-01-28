# TASK-69: Cursor Capability Types and Membership Tiers

Analysis of capability types and their mapping to subscription tiers in Cursor IDE authorization system.

## Source
- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`

---

## Membership Types (PlanType)

The core membership enum is defined as `aiserver.v1.PlanType`:

```javascript
// Line 829327
i[i.UNSPECIFIED = 0] = "UNSPECIFIED"
i[i.FREE = 1] = "FREE"
i[i.FREE_TRIAL = 2] = "FREE_TRIAL"
i[i.PRO = 3] = "PRO"
i[i.PRO_STUDENT = 4] = "PRO_STUDENT"
i[i.PRO_PLUS = 5] = "PRO_PLUS"
i[i.ULTRA = 6] = "ULTRA"
i[i.TEAM = 7] = "TEAM"
i[i.ENTERPRISE = 8] = "ENTERPRISE"
```

### Internal Membership Variable (`aa`)

The client uses the `aa` object for membership type checks:
```javascript
// Line 268990
aa.FREE = "free"
aa.PRO = "pro"
aa.PRO_PLUS = "pro_plus"
aa.ENTERPRISE = "enterprise"
aa.FREE_TRIAL = "free_trial"
aa.ULTRA = "ultra"
```

---

## Pricing Matrix

| Tier | Monthly Price | Included Amount | Description |
|------|--------------|-----------------|-------------|
| FREE | $0/mo | $0 | Free tier |
| FREE_TRIAL | $0/mo | $20 equivalent | Pro Trial |
| PRO | $20/mo | $20 | Standard paid tier |
| PRO_PLUS | $60/mo | $70 | "Unlock 3x more usage on Agent & more" |
| ULTRA | $200/mo | $400 | Highest individual tier |
| ENTERPRISE | Team pricing | Variable | Team/org features |

Source: Lines 912059-912103

---

## Spend Limit Options by Tier

Available spend limit options differ by membership:

```javascript
// Line 704802-704805
ndo = {
    [aa.PRO]: [20, 50, 100],
    [aa.PRO_PLUS]: [40, 80, 150],
    [aa.ULTRA]: [50, 150, 300]
}
```

---

## ComposerCapabilityType Enum

The full list of composer capabilities (`aiserver.v1.ComposerCapabilityRequest.ComposerCapabilityType`):

| Value | Name | Description |
|-------|------|-------------|
| 0 | UNSPECIFIED | Default |
| 1 | LOOP_ON_LINTS | Lint iteration capability |
| 2 | LOOP_ON_TESTS | Test iteration capability |
| 3 | MEGA_PLANNER | Large-scale planning |
| 4 | LOOP_ON_COMMAND | Command iteration |
| 5 | TOOL_CALL | Tool calling capability |
| 6 | DIFF_REVIEW | Diff review capability |
| 7 | CONTEXT_PICKING | Context selection |
| 8 | EDIT_TRAIL | Edit history tracking |
| 9 | AUTO_CONTEXT | Automatic context |
| 10 | CONTEXT_PLANNER | Context planning |
| 11 | DIFF_HISTORY | Diff history |
| 12 | REMEMBER_THIS | Memory capability |
| 13 | DECOMPOSER | Task decomposition |
| 14 | USES_CODEBASE | Codebase access |
| 15 | TOOL_FORMER | Tool formation/calling |
| 16 | CURSOR_RULES | Cursor rules support |
| 17 | TOKEN_COUNTER | Token counting |
| 18 | USAGE_DATA | Usage tracking |
| 19 | CHIMES | Notification sounds |
| 20 | CODE_DECAY_TRACKER | Code decay tracking |
| 21 | BACKGROUND_COMPOSER | Background processing |
| 22 | SUMMARIZATION | Conversation summarization |
| 23 | AI_CODE_TRACKING | AI code tracking |
| 24 | QUEUING | Request queuing |
| 25 | MEMORIES | Memory persistence |
| 26 | RCP_LOGS | RCP logging |
| 27 | KNOWLEDGE_FETCH | Knowledge base fetching |
| 28 | SLACK_INTEGRATION | Slack integration |
| 29 | SUB_COMPOSER | Sub-composer support |
| 30 | THINKING | Extended thinking mode |
| 31 | CONTEXT_WINDOW | Context window management |
| 32 | ONLINE_METRICS | Online metrics |
| 33 | NOTIFICATIONS | Notification system |
| 34 | SPEC | Spec mode |

Source: Lines 117858-117963

---

## Tool Types

```javascript
// Line 117965
i[i.UNSPECIFIED = 0] = "UNSPECIFIED"
i[i.ADD_FILE_TO_CONTEXT = 1] = "ADD_FILE_TO_CONTEXT"
i[i.ITERATE = 3] = "ITERATE"
i[i.REMOVE_FILE_FROM_CONTEXT = 4] = "REMOVE_FILE_FROM_CONTEXT"
i[i.SEMANTIC_SEARCH_CODEBASE = 5] = "SEMANTIC_SEARCH_CODEBASE"
```

---

## Agent Modes

```javascript
// Line 139077
i[i.UNSPECIFIED = 0] = "UNSPECIFIED"
i[i.AGENT = 1] = "AGENT"
i[i.ASK = 2] = "ASK"
i[i.PLAN = 3] = "PLAN"
i[i.DEBUG = 4] = "DEBUG"
i[i.TRIAGE = 5] = "TRIAGE"
```

---

## Rate Limiting Scenario Types

Different limit scenarios (`aiserver.v1.ScenarioType`):

```javascript
// Line 829358
i[i.UNSPECIFIED = 0] = "UNSPECIFIED"
i[i.PLAN_LIMIT = 1] = "PLAN_LIMIT"
i[i.TIER_1_LIMIT = 2] = "TIER_1_LIMIT"
i[i.TIER_2_LIMIT = 3] = "TIER_2_LIMIT"
i[i.TIER_3_LIMIT = 4] = "TIER_3_LIMIT"
i[i.ON_DEMAND_LIMIT = 5] = "ON_DEMAND_LIMIT"
i[i.TEAM_ON_DEMAND_LIMIT = 6] = "TEAM_ON_DEMAND_LIMIT"
i[i.MONTHLY_LIMIT = 7] = "MONTHLY_LIMIT"
i[i.POOLED_LIMIT = 8] = "POOLED_LIMIT"
```

---

## Error Codes Related to Tier Restrictions

```javascript
// Lines 92721-92763
"ERROR_FREE_USER_RATE_LIMIT_EXCEEDED"
"ERROR_PRO_USER_RATE_LIMIT_EXCEEDED"
"ERROR_FREE_USER_USAGE_LIMIT"
"ERROR_PRO_USER_USAGE_LIMIT"
"ERROR_PRO_USER_ONLY"  // Feature only available to Pro users
```

Error handling shows tier-gated features:
```javascript
// Line 705073-705103
case fu.PRO_USER_ONLY:
case "ERROR_PRO_USER_ONLY":
    return mt?.details?.title ?? "Request Allowed for Pro Users Only"
    // ...
    mt += "This feature is only available for Pro users. Please upgrade your account."
```

---

## CPP (Cursor Predict/Pro) Tier Gating

The CPP (predictive coding) feature has tier-based gating:

```javascript
// Line 268919-268924
function V$l(i) {
    return i === aa.ULTRA || i === aa.PRO || i === aa.PRO_PLUS || i === aa.ENTERPRISE || i === aa.FREE_TRIAL
}

function zyh(i, e, t) {
    return i === void 0 || i.isOn === !1 ? !1 : !(e === !1 || t === !1 && !i.shouldLetUserEnableCppEvenIfNotPro)
}
```

Key insight: CPP requires:
- Being authenticated AND
- Having PRO, PRO_PLUS, ULTRA, ENTERPRISE, or FREE_TRIAL tier
- OR having `shouldLetUserEnableCppEvenIfNotPro` flag set

---

## BugBot Usage Tiers

BugBot has its own tier system (`aiserver.v1.BugbotUsageTier`):

```javascript
// Line 269151
i[i.UNSPECIFIED = 0] = "UNSPECIFIED"
i[i.FREE_TIER = 1] = "FREE_TIER"
i[i.TRIAL = 2] = "TRIAL"
i[i.PAID = 3] = "PAID"
```

BugBot is gated by feature gates:
- `editor_bugbot` - Main gate
- `editor_bugbot_composer_upsell` - Upsell prompts
- `bugbot_editor_markers` - Editor markers

---

## Privacy Mode Options

Privacy modes (`aiserver.v1.PrivacyMode`):

```javascript
// Line 269165
i[i.UNSPECIFIED = 0] = "UNSPECIFIED"
i[i.NO_STORAGE = 1] = "NO_STORAGE"
i[i.NO_TRAINING = 2] = "NO_TRAINING"
i[i.USAGE_DATA_TRAINING_ALLOWED = 3] = "USAGE_DATA_TRAINING_ALLOWED"
i[i.USAGE_CODEBASE_TRAINING_ALLOWED = 4] = "USAGE_CODEBASE_TRAINING_ALLOWED"
```

Enterprise users have additional privacy controls:
- `privacyModeForced` - Enforced by team admin
- Ghost mode header: `x-ghost-mode`

---

## Tier Checking Patterns

Common patterns for tier checking in the codebase:

### Check for Paid Plan
```javascript
// Line 268920
return i === aa.ULTRA || i === aa.PRO || i === aa.PRO_PLUS || i === aa.ENTERPRISE || i === aa.FREE_TRIAL
```

### Check for Enterprise
```javascript
// Lines 704821, 718883, etc.
i.cursorAuthenticationService.membershipType() === aa.ENTERPRISE
```

### Check for Trial Status
```javascript
// Line 370350
return s() === aa.FREE_TRIAL || s() === aa.FREE || s() === aa.PRO_PLUS && o() === "trialing" || s() === aa.PRO && o() === "trialing"
```

---

## Feature Gates Related to Tiers

Key feature gates that may relate to tier functionality:

| Gate Name | Description |
|-----------|-------------|
| `editor_bugbot` | BugBot feature access |
| `editor_bugbot_composer_upsell` | BugBot upsell prompts |
| `use_usage_limit_policy_experiment` | Usage limit enforcement |
| `spec_mode` | Spec mode availability |
| `quick_search_ux` | Quick search UX |
| `mcp_discovery` | MCP discovery feature |
| `enable_agent_web_search` | Agent web search |

---

## Upgrade Flow

Upgrade paths defined in client:

```javascript
// Line 912094-912107
switch (n()) {
    case aa.FREE:
    case aa.FREE_TRIAL:
    case aa.PRO:
        return { tier: "pro_plus", name: "Get Pro+", ... };
    case aa.PRO_PLUS:
        return { tier: "ultra", name: "Get Ultra", ... };
}
```

Upgrade endpoint: `api/auth/checkoutDeepControl?tier={tier}`

---

## Slow Request Handling

The `is_using_slow_request` field indicates degraded service for non-premium tiers:

```javascript
// Line 124017, 169658, 331132, 539349
name: "is_using_slow_request"
```

Error message for slow requests:
```javascript
// Line 451161
case fu.PRO_USER_USAGE_LIMIT:
    return "We're currently recieving a large number of slow requests and could not queue yours..."
```

---

## Open Questions

1. What specific capabilities are restricted at each tier level?
2. How does the `ScenarioType` tier system map to membership tiers?
3. What is the exact relationship between BugBot tiers and membership tiers?
4. How are feature gates used to progressively enable features per tier?

---

## Suggested Follow-up Tasks

1. **TASK-XXX**: Deep-dive into CPP (Cursor Predict) tier gating logic
2. **TASK-XXX**: Map feature gates to specific membership tiers
3. **TASK-XXX**: Document the complete upgrade flow and checkout process
4. **TASK-XXX**: Analyze rate limiting implementation per tier
5. **TASK-XXX**: Investigate BugBot licensing and tier relationship

---

## References

- Line 268990: `aa` membership constants
- Line 829327: `PlanType` protobuf enum
- Lines 117858-117963: `ComposerCapabilityType` enum
- Lines 704802-704805: Spend limit options per tier
- Lines 912059-912103: Pricing and upgrade options
