# TASK-124: ExaSearch Type Parameter Values Analysis

## Overview

This analysis investigates the `type` field in `ExaSearchArgs` and how it maps to Exa AI's search modes. The ExaSearch tool is Cursor's integration with Exa AI's web search API, offering different search strategies for optimal results.

## Source Location

**Primary Definition:** `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
- Lines 136314-136348: `ExaSearchArgs` protobuf definition
- Lines 240416-240462: Duplicate definition (different bundle)

## ExaSearchArgs Schema

```javascript
// agent.v1.ExaSearchArgs (line 136318)
constructor(e) {
    super(),
    this.query = "",       // Field 1: Search query string
    this.type = "",        // Field 2: Search type parameter
    this.numResults = 0,   // Field 3: Number of results to return
    this.toolCallId = ""   // Field 4: Correlation ID for tool call
}
```

The `type` field is defined as:
- **Field number:** 2
- **Type:** string (T: 9 in protobuf wire type)
- **Default value:** empty string `""`

## Exa AI Type Parameter Values

Based on Exa AI's current API documentation, the `type` parameter supports the following values:

### Primary Search Types

| Value | Description | Latency | Use Case |
|-------|-------------|---------|----------|
| `auto` | Default. Intelligently combines multiple search methods | ~1000ms P50 | General purpose, balanced performance |
| `neural` | Uses embeddings-based semantic model | Medium | Complex semantic queries |
| `fast` | Streamlined neural and reranking models | <350ms P50 | Real-time apps, voice agents, high-volume workflows |
| `deep` | Agentic search with query expansion | ~3.5s P50 | Highest quality results, research tasks |
| `keyword` | Traditional keyword-based search | Fast | Exact matches, specific terms |

### Observations from Cursor Codebase

1. **Internal Search Type Enum (line 268942):**
   ```javascript
   i.keyword = "keyword", i.vector = "vector"
   ```
   This internal enum in `reactiveStorageTypes.js` suggests Cursor may use:
   - `keyword` - Traditional keyword search
   - `vector` - Vector/semantic search (likely maps to `neural`)

2. **No Hardcoded Type Values Found:**
   The beautified source does not show explicit type values being set in ExaSearch calls. This suggests:
   - Type may be determined server-side
   - Type may come from user preferences or settings
   - Default (`auto`) may be used when not specified

3. **Comparison with WebSearch:**
   - WebSearch (`aiserver.v1`) does not have a type parameter
   - ExaSearch (`agent.v1`) has explicit type field for search strategy selection

## Search Type Behavior

### `auto` (Default)
- Balanced performance without manual tuning
- Reranker model adapts to query type
- Recommended for most use cases

### `neural`
- Semantic understanding of queries
- Better for complex or natural language queries
- Example: "how to implement authentication in React"

### `fast`
- 30% faster than other options
- Best for:
  - Single-step factual queries
  - Low-latency QA datasets
  - Real-time applications (voice agents, autocomplete)
  - High-volume agentic workflows

### `deep`
- Highest quality search results
- Uses iterative search/process/search strategy
- Best for research and comprehensive information gathering
- Higher latency tradeoff for quality

### `keyword`
- Traditional keyword matching
- Best for exact term searches
- Lower semantic understanding

## ExaSearch vs WebSearch Comparison

| Feature | ExaSearch (agent.v1) | WebSearch (aiserver.v1) |
|---------|---------------------|------------------------|
| Type parameter | Yes (search mode) | No |
| Search modes | neural, keyword, auto, fast, deep | Single mode |
| num_results | Configurable | Not in schema |
| Two-phase (search + fetch) | Yes | No |
| User approval required | Yes | Yes |
| Published date in results | Yes | No |
| ID-based content fetch | Yes (ExaFetch) | No |

## Request/Response Flow

From code analysis (lines 465475-465584):

1. **Request Query:**
   ```javascript
   case "exaSearchRequestQuery":
       return {
           type: "exa-search-request",
           args: i.query.value.args  // Contains query, type, numResults
       }
   ```

2. **User Approval:**
   - UI prompts user to approve/reject the search
   - Approval returns `ExaSearchRequestResponse.Approved`
   - Rejection returns `ExaSearchRequestResponse.Rejected` with reason

3. **Search Execution:**
   - If approved, search executes with specified type
   - Returns `ExaSearchSuccess` with references or `ExaSearchError`

4. **Content Fetch (Optional):**
   - User can fetch full content using IDs from search results
   - Uses `ExaFetch` tool with separate approval flow

## Default Behavior Analysis

The code at line 465670-465672 shows CLI fallback behavior:
```javascript
case "exa-search-request":
    return { approved: !0 }  // Auto-approve in CLI mode
```

This indicates:
- In interactive UI mode, user approval is required
- In CLI mode, searches are auto-approved
- Type parameter is passed through from the args

## Key Findings

1. **Type Field is String:** Unlike an enum, this allows flexibility for future Exa API changes
2. **Default is Empty:** When not specified, likely falls back to `auto` on server side
3. **Internal Mapping:** Cursor's internal `keyword`/`vector` enum may map to Exa's types
4. **Server-Side Decision:** Type selection logic may be determined by Cursor's server, not client
5. **No UI Selector Found:** No evidence of user-facing UI to select search type

## Recommendations for Emulation

When implementing ExaSearch:

1. **Default to `auto`:** Use `"auto"` or empty string for balanced results
2. **Support all types:** Allow `neural`, `keyword`, `fast`, `deep` for flexibility
3. **Set reasonable num_results:** Default appears to be 0 (server decides), but can be specified
4. **Handle approval flow:** Implement user confirmation for searches
5. **Support two-phase:** Implement both search (snippets) and fetch (full content)

## Related Analysis

- TASK-104: Exa AI Integration Tool Schemas (general structure)
- TASK-110: Tool Enum Mapping (tool type relationships)
- TASK-112: Tool Approval Flow (approval patterns)

## References

- [Exa AI Search API Documentation](https://docs.exa.ai/reference/search)
- [Exa API 2.0 Blog Post](https://exa.ai/blog/exa-api-2-0)
- [Exa AI Search Types Overview](https://docs.litellm.ai/docs/search/exa_ai)

## Follow-up Investigation

1. **Trace type value propagation:** How does type get set from user intent to API call?
2. **Analyze server-side logic:** How does Cursor's server select type if not specified?
3. **Research num_results defaults:** What values are typical for different contexts?
