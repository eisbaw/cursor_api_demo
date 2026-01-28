# TASK-104: ExaSearch and ExaFetch Tool Schemas Analysis

## Executive Summary

Cursor IDE integrates with Exa AI (exa.ai) for advanced web search capabilities through two complementary tools:
- **ExaSearch** - Semantic web search with configurable search types
- **ExaFetch** - Full content retrieval for search results

Both tools are defined in the `agent.v1` protobuf namespace, indicating they are server-side agent tools requiring user approval before execution.

## Source Locations

**Primary Protobuf Definitions:**
- ExaSearch: `out-build/proto/agent/v1/exa_search_tool_pb.js` (line 136314)
- ExaFetch: `out-build/proto/agent/v1/exa_fetch_tool_pb.js` (line 136705)

**TypeScript Definitions (duplicate bundle):**
- ExaSearch: `src/proto/agent/v1/exa_search_tool_pb.ts` (line 240416)
- ExaFetch: `src/proto/agent/v1/exa_fetch_tool_pb.ts` (line 240807)

**Tool Registration:**
- `agent.v1.ToolCall` oneof (line 139348): fields 26 (exa_search) and 27 (exa_fetch)

---

## ExaSearch Tool Schemas

### agent.v1.ExaSearchArgs

The primary input schema for Exa search requests.

```protobuf
message ExaSearchArgs {
  string query = 1;           // Search query string
  string type = 2;            // Search type (auto, neural, keyword, fast, deep)
  int32 num_results = 3;      // Number of results to return
  string tool_call_id = 4;    // Correlation ID for tool call tracking
}
```

**Field Details:**

| Field | Number | Wire Type | Description | Default |
|-------|--------|-----------|-------------|---------|
| query | 1 | T:9 (string) | The search query to execute | "" |
| type | 2 | T:9 (string) | Search mode selector | "" |
| num_results | 3 | T:5 (int32) | Maximum results to return | 0 |
| tool_call_id | 4 | T:9 (string) | Unique ID to correlate request/response | "" |

**Type Parameter Values (from Exa AI API):**

| Value | Description | Latency |
|-------|-------------|---------|
| `auto` | Default balanced mode | ~1000ms |
| `neural` | Embeddings-based semantic search | Medium |
| `keyword` | Traditional keyword matching | Fast |
| `fast` | Streamlined for real-time apps | <350ms |
| `deep` | Agentic search with query expansion | ~3.5s |

### agent.v1.ExaSearchResult

Response container using oneof pattern for success/error/rejected states.

```protobuf
message ExaSearchResult {
  oneof result {
    ExaSearchSuccess success = 1;
    ExaSearchError error = 2;
    ExaSearchRejected rejected = 3;
  }
}
```

### agent.v1.ExaSearchSuccess

Successful search response containing references.

```protobuf
message ExaSearchSuccess {
  repeated ExaSearchReference references = 1;
}
```

### agent.v1.ExaSearchReference

Individual search result entry.

```protobuf
message ExaSearchReference {
  string title = 1;           // Page title
  string url = 2;             // Full URL
  string text = 3;            // Snippet/excerpt text
  string published_date = 4;  // Publication date (ISO format)
}
```

**Field Details:**

| Field | Number | Wire Type | Description |
|-------|--------|-----------|-------------|
| title | 1 | T:9 (string) | Title of the web page |
| url | 2 | T:9 (string) | Full URL to the resource |
| text | 3 | T:9 (string) | Text snippet/excerpt |
| published_date | 4 | T:9 (string) | Publication date string |

### agent.v1.ExaSearchError

Error response with message.

```protobuf
message ExaSearchError {
  string error = 1;  // Error message describing failure
}
```

### agent.v1.ExaSearchRejected

Rejection response (typically from user denial).

```protobuf
message ExaSearchRejected {
  string reason = 1;  // Reason for rejection
}
```

### agent.v1.ExaSearchToolCall

Complete tool call wrapper combining args and result.

```protobuf
message ExaSearchToolCall {
  ExaSearchArgs args = 1;
  ExaSearchResult result = 2;
}
```

### agent.v1.ExaSearchRequestQuery

User approval request query.

```protobuf
message ExaSearchRequestQuery {
  ExaSearchArgs args = 1;  // Arguments requiring approval
}
```

### agent.v1.ExaSearchRequestResponse

User approval response with oneof for approval/rejection.

```protobuf
message ExaSearchRequestResponse {
  oneof result {
    Approved approved = 1;
    Rejected rejected = 2;
  }

  message Approved {}  // Empty - just indicates approval

  message Rejected {
    string reason = 1;  // Why user rejected
  }
}
```

---

## ExaFetch Tool Schemas

### agent.v1.ExaFetchArgs

Input schema for fetching full content from search results.

```protobuf
message ExaFetchArgs {
  repeated string ids = 1;    // IDs of search results to fetch
  string tool_call_id = 2;    // Correlation ID
}
```

**Field Details:**

| Field | Number | Wire Type | Description | Default |
|-------|--------|-----------|-------------|---------|
| ids | 1 | T:9 (string), repeated | Array of search result IDs to fetch | [] |
| tool_call_id | 2 | T:9 (string) | Correlation ID | "" |

**Note:** IDs reference specific search results from a prior ExaSearch call, enabling the two-phase search-then-fetch pattern.

### agent.v1.ExaFetchResult

Response container using oneof pattern.

```protobuf
message ExaFetchResult {
  oneof result {
    ExaFetchSuccess success = 1;
    ExaFetchError error = 2;
    ExaFetchRejected rejected = 3;
  }
}
```

### agent.v1.ExaFetchSuccess

Successful fetch response containing full content.

```protobuf
message ExaFetchSuccess {
  repeated ExaFetchContent contents = 1;
}
```

### agent.v1.ExaFetchContent

Full content for a fetched document.

```protobuf
message ExaFetchContent {
  string title = 1;           // Page title
  string url = 2;             // Source URL
  string text = 3;            // Full page text content
  string published_date = 4;  // Publication date
}
```

**Field Details:**

| Field | Number | Wire Type | Description |
|-------|--------|-----------|-------------|
| title | 1 | T:9 (string) | Document title |
| url | 2 | T:9 (string) | Source URL |
| text | 3 | T:9 (string) | Full extracted text content |
| published_date | 4 | T:9 (string) | Publication date string |

### agent.v1.ExaFetchError

```protobuf
message ExaFetchError {
  string error = 1;  // Error message
}
```

### agent.v1.ExaFetchRejected

```protobuf
message ExaFetchRejected {
  string reason = 1;  // Rejection reason
}
```

### agent.v1.ExaFetchToolCall

```protobuf
message ExaFetchToolCall {
  ExaFetchArgs args = 1;
  ExaFetchResult result = 2;
}
```

### agent.v1.ExaFetchRequestQuery

```protobuf
message ExaFetchRequestQuery {
  ExaFetchArgs args = 1;
}
```

### agent.v1.ExaFetchRequestResponse

```protobuf
message ExaFetchRequestResponse {
  oneof result {
    Approved approved = 1;
    Rejected rejected = 2;
  }

  message Approved {}

  message Rejected {
    string reason = 1;
  }
}
```

---

## Tool Integration in agent.v1.ToolCall

Both Exa tools are registered in the main `ToolCall` oneof (line 139348):

```javascript
// agent.v1.ToolCall fields (excerpt)
{
  no: 26,
  name: "exa_search_tool_call",
  kind: "message",
  T: sfl,  // ExaSearchToolCall
  oneof: "tool"
}, {
  no: 27,
  name: "exa_fetch_tool_call",
  kind: "message",
  T: mfl,  // ExaFetchToolCall
  oneof: "tool"
}
```

**Full ToolCall Context (neighboring tools):**

| Field No | Tool Name | Description |
|----------|-----------|-------------|
| 24 | fetch_tool_call | Generic URL fetch |
| 25 | switch_mode_tool_call | Mode switching |
| **26** | **exa_search_tool_call** | **Exa AI semantic search** |
| **27** | **exa_fetch_tool_call** | **Exa AI content fetch** |
| 28 | generate_image_tool_call | Image generation |
| 29 | record_screen_tool_call | Screen recording |

---

## Interaction Flow

### Request/Response Cycle (from lines 465475-465605)

**1. Search Request Query Conversion:**
```javascript
case "exaSearchRequestQuery":
    return {
        type: "exa-search-request",
        args: i.query.value.args  // ExaSearchArgs
    };
```

**2. User Approval Flow:**
- UI presents search request for approval
- User approves or rejects
- Response created:

```javascript
case "exa-search-request":
    return s.approved ? {
        case: "approved",
        value: new ExaSearchRequestResponse.Approved()
    } : {
        case: "rejected",
        value: new ExaSearchRequestResponse.Rejected({ reason: s.reason })
    };
```

**3. CLI Auto-Approval (line 465670):**
```javascript
case "exa-search-request":
    return { approved: !0 };  // Auto-approve in CLI mode
case "exa-fetch-request":
    return { approved: !0 };  // Auto-approve in CLI mode
```

---

## Comparison: Exa AI vs WebSearch

Cursor has two web search implementations:

| Feature | ExaSearch (agent.v1) | WebSearch (aiserver.v1) |
|---------|---------------------|------------------------|
| Namespace | agent.v1 | aiserver.v1 |
| Tool enum | Field 26 in ToolCall | CLIENT_SIDE_TOOL_V2_WEB_SEARCH (18) |
| Type parameter | Yes (5 modes) | No |
| num_results | Yes | No |
| Two-phase | Yes (search + fetch) | No |
| User approval | Required | Required |
| Published date | Yes | No |
| ID-based fetch | Yes | No |
| Result streaming | No | Yes (WebSearchStream) |

**WebSearchParams Schema (for comparison):**
```protobuf
// aiserver.v1.WebSearchParams (line 112797)
message WebSearchParams {
  string search_term = 1;  // Simple search term only
}

// aiserver.v1.WebSearchResult
message WebSearchResult {
  repeated WebReference references = 1;
  optional bool is_final = 2;
  optional bool rejected = 3;
}

// aiserver.v1.WebSearchResult.WebReference
message WebReference {
  string title = 1;
  string url = 2;
  string chunk = 3;  // Note: "chunk" not "text"
}
```

---

## Protobuf Wire Type Reference

| T Value | Protobuf Type | Description |
|---------|---------------|-------------|
| 5 | int32 | 32-bit signed integer |
| 8 | bool | Boolean |
| 9 | string | UTF-8 string |

---

## Key Observations

1. **Two-Phase Design:** ExaSearch returns snippets; ExaFetch retrieves full content using IDs from search results

2. **User Approval Required:** Both tools have RequestQuery/RequestResponse patterns requiring explicit user approval (except in CLI mode)

3. **Semantic Search Support:** The `type` field supports multiple search modes (auto, neural, keyword, fast, deep)

4. **ID-Based Retrieval:** ExaFetch uses IDs from ExaSearchReference results, not URLs directly

5. **Published Date Tracking:** Both tools include publication date in results (not present in generic WebSearch)

6. **Duplicate Definitions:** Same schemas appear in both compiled JS (out-build) and TypeScript (src) bundles at lines 136k and 240k

7. **Agent-Side Execution:** Being in `agent.v1` namespace indicates server-side agent execution rather than client-side tool

---

## JSON Schema Representation

### ExaSearchArgs (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "agent.v1.ExaSearchArgs",
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search query string"
    },
    "type": {
      "type": "string",
      "enum": ["", "auto", "neural", "keyword", "fast", "deep"],
      "description": "Search mode"
    },
    "numResults": {
      "type": "integer",
      "format": "int32",
      "description": "Number of results to return"
    },
    "toolCallId": {
      "type": "string",
      "description": "Correlation ID"
    }
  },
  "required": ["query"]
}
```

### ExaFetchArgs (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "agent.v1.ExaFetchArgs",
  "type": "object",
  "properties": {
    "ids": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "IDs from ExaSearchReference results"
    },
    "toolCallId": {
      "type": "string",
      "description": "Correlation ID"
    }
  },
  "required": ["ids"]
}
```

---

## Related Analysis Files

- TASK-104-exa-tools.md - Initial Exa tools analysis
- TASK-124-exasearch-params.md - Deep dive on type parameter values
- TASK-26-tool-schemas.md - General tool schema patterns
- TASK-110-tool-enum-mapping.md - Tool type relationships
- TASK-112-tool-approval.md - Approval flow patterns

---

## Analysis Metadata

- **Source Version:** Cursor IDE 2.3.41
- **Source File:** `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
- **Analysis Date:** 2026-01-28
- **Key Line References:** 136314-136702 (ExaSearch), 136705-137085 (ExaFetch), 139478-139488 (ToolCall registration)
