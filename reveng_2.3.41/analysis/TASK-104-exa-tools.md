# TASK-104: Exa AI Integration Tool Schemas

## Overview

Cursor IDE integrates with Exa AI (exa.ai) for web search capabilities. Two main tools exist:
- **ExaSearch** - Performs web searches via Exa AI's semantic search
- **ExaFetch** - Fetches full content from search results

Both are defined in the `agent.v1` protobuf namespace, indicating server-side agent integration.

## Source Files

Proto definitions are in:
- `out-build/proto/agent/v1/exa_search_tool_pb.js` (line 136314)
- `out-build/proto/agent/v1/exa_fetch_tool_pb.js` (line 136705)

## ExaSearch Tool

### ExaSearchArgs
**Type:** `agent.v1.ExaSearchArgs`

| Field | No | Type | Description |
|-------|-----|------|-------------|
| query | 1 | string (T:9) | Search query string |
| type | 2 | string (T:9) | Search type (semantic, keyword, etc.) |
| num_results | 3 | int32 (T:5) | Number of results to return |
| tool_call_id | 4 | string (T:9) | ID to correlate tool call with response |

### ExaSearchResult
**Type:** `agent.v1.ExaSearchResult`

Oneof result field containing:
- `success` -> ExaSearchSuccess
- `error` -> ExaSearchError
- `rejected` -> ExaSearchRejected

### ExaSearchSuccess
**Type:** `agent.v1.ExaSearchSuccess`

| Field | No | Type | Description |
|-------|-----|------|-------------|
| references | 1 | repeated ExaSearchReference | Array of search results |

### ExaSearchReference
**Type:** `agent.v1.ExaSearchReference`

| Field | No | Type | Description |
|-------|-----|------|-------------|
| title | 1 | string (T:9) | Page title |
| url | 2 | string (T:9) | URL of the result |
| text | 3 | string (T:9) | Snippet/excerpt text |
| published_date | 4 | string (T:9) | Publication date |

### ExaSearchError
**Type:** `agent.v1.ExaSearchError`

| Field | No | Type | Description |
|-------|-----|------|-------------|
| error | 1 | string (T:9) | Error message |

### ExaSearchRejected
**Type:** `agent.v1.ExaSearchRejected`

| Field | No | Type | Description |
|-------|-----|------|-------------|
| reason | 1 | string (T:9) | Rejection reason (user denied, policy, etc.) |

### ExaSearchToolCall
**Type:** `agent.v1.ExaSearchToolCall`

Wrapper combining args and result:

| Field | No | Type | Description |
|-------|-----|------|-------------|
| args | 1 | ExaSearchArgs | The search arguments |
| result | 2 | ExaSearchResult | The search result |

### ExaSearchRequestQuery
**Type:** `agent.v1.ExaSearchRequestQuery`

User approval query:

| Field | No | Type | Description |
|-------|-----|------|-------------|
| args | 1 | ExaSearchArgs | Arguments to approve/reject |

### ExaSearchRequestResponse
**Type:** `agent.v1.ExaSearchRequestResponse`

Oneof result:
- `approved` -> ExaSearchRequestResponse.Approved (empty message)
- `rejected` -> ExaSearchRequestResponse.Rejected

#### ExaSearchRequestResponse.Rejected
| Field | No | Type | Description |
|-------|-----|------|-------------|
| reason | 1 | string (T:9) | Why user rejected |

---

## ExaFetch Tool

### ExaFetchArgs
**Type:** `agent.v1.ExaFetchArgs`

| Field | No | Type | Description |
|-------|-----|------|-------------|
| ids | 1 | repeated string (T:9) | IDs of search results to fetch |
| tool_call_id | 2 | string (T:9) | Correlation ID |

### ExaFetchResult
**Type:** `agent.v1.ExaFetchResult`

Oneof result field containing:
- `success` -> ExaFetchSuccess
- `error` -> ExaFetchError
- `rejected` -> ExaFetchRejected

### ExaFetchSuccess
**Type:** `agent.v1.ExaFetchSuccess`

| Field | No | Type | Description |
|-------|-----|------|-------------|
| contents | 1 | repeated ExaFetchContent | Full content items |

### ExaFetchContent
**Type:** `agent.v1.ExaFetchContent`

| Field | No | Type | Description |
|-------|-----|------|-------------|
| title | 1 | string (T:9) | Page title |
| url | 2 | string (T:9) | Source URL |
| text | 3 | string (T:9) | Full page text content |
| published_date | 4 | string (T:9) | Publication date |

### ExaFetchError
**Type:** `agent.v1.ExaFetchError`

| Field | No | Type | Description |
|-------|-----|------|-------------|
| error | 1 | string (T:9) | Error message |

### ExaFetchRejected
**Type:** `agent.v1.ExaFetchRejected`

| Field | No | Type | Description |
|-------|-----|------|-------------|
| reason | 1 | string (T:9) | Rejection reason |

### ExaFetchToolCall
**Type:** `agent.v1.ExaFetchToolCall`

| Field | No | Type | Description |
|-------|-----|------|-------------|
| args | 1 | ExaFetchArgs | Fetch arguments |
| result | 2 | ExaFetchResult | Fetch result |

### ExaFetchRequestQuery / ExaFetchRequestResponse
Same pattern as ExaSearch for user approval flow.

---

## Comparison: Exa AI vs WebSearch

Two different web search implementations exist:

### WebSearch (aiserver.v1)
- **Namespace:** `aiserver.v1`
- **Tool enum:** `CLIENT_SIDE_TOOL_V2_WEB_SEARCH` (no: 18)
- **Schema:** `WebSearchParams`, `WebSearchResult`, `WebSearchStream`
- **Simpler structure:** Just search_term as input
- **Result:** references with title, url, chunk fields
- **Has streaming support** via WebSearchStream

### Exa AI (agent.v1)
- **Namespace:** `agent.v1`
- **Richer parameters:** query, type, num_results
- **Two-phase:** Search first, then fetch full content
- **Has published_date** in results
- **Requires user approval** via RequestQuery/RequestResponse flow
- **IDs reference system** allowing fetch by ID

---

## Interaction Flow

Based on code at line 465475-465605:

1. Agent sends `exaSearchRequestQuery` with search args
2. UI converts to `exa-search-request` type for user prompt
3. User approves/rejects
4. Response is `exaSearchRequestResponse` with approved or rejected+reason
5. If approved, search executes and returns ExaSearchSuccess with references
6. Agent may then send `exaFetchRequestQuery` with IDs from results
7. Same approval flow for fetch
8. If approved, ExaFetchSuccess returns full content

---

## Key Observations

1. **Exa AI integration is newer** - In agent.v1 namespace vs aiserver.v1 for generic WebSearch
2. **Two-phase design** - Search returns snippets, Fetch retrieves full content
3. **User approval required** - Both tools have RequestQuery/RequestResponse patterns
4. **Semantic search support** - The "type" field suggests different search modes
5. **ID-based content retrieval** - Fetch uses IDs from search results, not URLs
6. **Duplicate definitions** - Same schemas appear at lines 136k and 240k (likely different bundles)

---

## Protobuf Field Type Reference

| T Value | Type |
|---------|------|
| 5 | int32 |
| 8 | bool |
| 9 | string |

---

## Related Analysis

- TASK-26: Tool schemas (general tool patterns)
- TASK-27: MCP tool schemas
- TASK-25: Agent v1 schemas

## Follow-up Tasks

1. Investigate how ExaSearch "type" parameter values map to Exa AI search types
2. Trace the approval UI flow for web search tools
3. Analyze rate limiting or quota management for Exa API calls
