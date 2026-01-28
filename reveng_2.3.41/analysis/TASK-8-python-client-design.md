# TASK-8: Python Client Design for Cursor 2.3.41 Agent API

## Executive Summary

This document outlines the design for an updated Python client to work with Cursor 2.3.41's API. The existing `cursor_http2_client.py` works with the older API but now encounters `resource_exhausted` errors. The new version introduces significant changes including agent-focused endpoints (api5.cursor.sh), bidirectional streaming, and new header requirements.

## Current State Analysis

### Existing Client Files

1. **`cursor_http2_client.py`** - Main HTTP/2 client
   - Uses `httpx` with `http2=True`
   - Targets `api2.cursor.sh`
   - Calls `StreamUnifiedChatWithTools` endpoint
   - Headers: `x-cursor-checksum`, `x-cursor-client-version`, `x-cursor-timezone`, `x-ghost-mode`, etc.
   - Problem: Gets `resource_exhausted` errors

2. **`cursor_streaming_decoder.py`** - Protobuf streaming decoder
   - Frame-based decoder: `[msg_type:1byte][msg_len:4bytes_big_endian][msg_data]`
   - Handles raw protobuf (type 0), gzip protobuf (type 1), raw JSON (type 2), gzip JSON (type 3)
   - Uses `StreamUnifiedChatResponseWithTools` protobuf

3. **`cursor_proper_protobuf.py`** - Protobuf encoder
   - Manual protobuf encoding for request messages
   - Implements checksum generation, session ID generation

4. **`cursor_auth_reader.py`** - Authentication token reader
   - Reads from SQLite storage (`state.vscdb`)
   - Extracts access_token, refresh_token, etc.

### Key Findings from 2.3.41 Decompilation

#### New API Endpoints (api5.cursor.sh)
```
https://agent.api5.cursor.sh           - Agent service
https://agentn.api5.cursor.sh          - Agent N service
https://agent-gcpp-eucentral.api5.cursor.sh  - EU Central region
https://agent-gcpp-uswest.api5.cursor.sh     - US West region
```

#### New HTTP Headers Required
| Header | Purpose | Example |
|--------|---------|---------|
| `x-cursor-client-arch` | CPU architecture | `x64`, `arm64` |
| `x-cursor-client-os` | Operating system | `linux`, `darwin`, `win32` |
| `x-cursor-client-os-version` | OS version | `6.13.0` |
| `x-cursor-client-device-type` | Device type | `desktop` |
| `x-cursor-client-type` | Client type | `ide` |
| `x-cursor-canary` | Canary features | `true`/`false` |
| `x-cursor-config-version` | Config version | UUID |
| `x-cursor-server-region` | Server region | `eu-central`, `us-west` |
| `x-new-onboarding-completed` | Onboarding flag | `true`/`false` |

#### New gRPC Services
- **`aiserver.v1.BidiService`** - Bidirectional streaming
  - Method: `BidiAppend` (Unary)
  - Request: `BidiAppendRequest` {data: string, request_id: ?, append_seqno: int64}
  - Response: `BidiAppendResponse` {}

- **`aiserver.v1.BackgroundComposerService`** - Background agent tasks
- **`aiserver.v1.AutopilotService`** - Autopilot/agent mode
- **`aiserver.v1.MCPRegistryService`** - MCP server registry

#### ChatService Streaming Modes
The `aiserver.v1.ChatService` now supports multiple streaming modes:
| Method | Type | Purpose |
|--------|------|---------|
| `StreamUnifiedChatWithTools` | BiDiStreaming | Standard bidirectional |
| `StreamUnifiedChatWithToolsSSE` | ServerStreaming | SSE fallback |
| `StreamUnifiedChatWithToolsPoll` | ServerStreaming | Polling fallback |
| `StreamUnifiedChatWithToolsIdempotent` | BiDiStreaming | Idempotent version |
| `StreamUnifiedChatWithToolsIdempotentSSE` | ServerStreaming | Idempotent SSE |
| `WarmStreamUnifiedChatWithTools` | Unary | Connection warming |

#### Error Codes
```python
ERROR_RESOURCE_EXHAUSTED = 41  # The error we're seeing
ERROR_AUTH_TOKEN_NOT_FOUND = 11
ERROR_FREE_USER_USAGE_LIMIT = 40
ERROR_PRO_USER_USAGE_LIMIT = 12
ERROR_TIMEOUT = 5
```

## Proposed Design

### Architecture Overview

```
cursor_client/
    __init__.py
    auth.py           # Authentication handling
    client.py         # Main client class
    endpoints.py      # Endpoint definitions
    headers.py        # Header generation
    streaming.py      # Streaming handlers
    protobuf/
        encoder.py    # Request encoding
        decoder.py    # Response decoding
        messages.py   # Message types
    services/
        chat.py       # ChatService
        bidi.py       # BidiService
        agent.py      # Agent services
    errors.py         # Error handling
    config.py         # Configuration
```

### Core Classes

#### 1. CursorClientConfig
```python
@dataclass
class CursorClientConfig:
    """Configuration for Cursor API client."""

    # API endpoints
    api_base: str = "https://api2.cursor.sh"
    agent_api_base: str = "https://agent.api5.cursor.sh"

    # Client metadata
    client_version: str = "2.3.41"
    client_type: str = "ide"
    device_type: str = "desktop"

    # Platform info (auto-detected)
    os: str = field(default_factory=lambda: platform.system().lower())
    arch: str = field(default_factory=lambda: platform.machine())
    os_version: str = field(default_factory=lambda: platform.release())
    timezone: str = field(default_factory=lambda: time.tzname[0])

    # Connection settings
    http2_enabled: bool = True
    timeout: float = 30.0
    max_retries: int = 3

    # Feature flags
    ghost_mode: bool = True
    canary: bool = False
    server_region: Optional[str] = None  # None = auto-select
```

#### 2. HeaderBuilder
```python
class HeaderBuilder:
    """Builds headers for Cursor API requests."""

    def __init__(self, config: CursorClientConfig, auth: CursorAuth):
        self.config = config
        self.auth = auth

    def build_base_headers(self) -> Dict[str, str]:
        """Build standard headers for all requests."""
        return {
            "authorization": f"Bearer {self.auth.access_token}",
            "connect-protocol-version": "1",
            "content-type": "application/connect+proto",
            "user-agent": f"connect-es/1.6.1",
            "x-cursor-client-version": self.config.client_version,
            "x-cursor-client-type": self.config.client_type,
            "x-cursor-client-device-type": self.config.device_type,
            "x-cursor-client-os": self.config.os,
            "x-cursor-client-arch": self.config.arch,
            "x-cursor-client-os-version": self.config.os_version,
            "x-cursor-timezone": self.config.timezone,
            "x-ghost-mode": str(self.config.ghost_mode).lower(),
        }

    def build_request_headers(self, request_id: Optional[str] = None) -> Dict[str, str]:
        """Build headers for a specific request."""
        headers = self.build_base_headers()

        req_id = request_id or str(uuid.uuid4())
        headers.update({
            "x-request-id": req_id,
            "x-amzn-trace-id": f"Root={req_id}",
            "x-session-id": self._generate_session_id(),
            "x-client-key": self._generate_client_key(),
            "x-cursor-checksum": self._generate_checksum(),
            "x-cursor-config-version": str(uuid.uuid4()),
        })

        if self.config.canary:
            headers["x-cursor-canary"] = "true"

        if self.config.server_region:
            headers["x-cursor-server-region"] = self.config.server_region

        return headers
```

#### 3. CursorStreamingClient (Main Interface)
```python
class CursorStreamingClient:
    """Main client for Cursor 2.3.41 API with streaming support."""

    def __init__(self, config: Optional[CursorClientConfig] = None):
        self.config = config or CursorClientConfig()
        self.auth = CursorAuth()
        self.headers = HeaderBuilder(self.config, self.auth)
        self._http_client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._http_client = httpx.AsyncClient(
            http2=self.config.http2_enabled,
            timeout=self.config.timeout,
        )
        return self

    async def __aexit__(self, *args):
        if self._http_client:
            await self._http_client.aclose()

    # --- Chat Methods ---

    async def chat_stream(
        self,
        messages: List[ChatMessage],
        model: str = "claude-4-sonnet",
        mode: StreamMode = StreamMode.BIDI,
    ) -> AsyncIterator[StreamResponse]:
        """Stream a chat conversation."""
        ...

    async def chat_complete(
        self,
        messages: List[ChatMessage],
        model: str = "claude-4-sonnet",
    ) -> ChatResponse:
        """Complete a chat (non-streaming)."""
        ...

    # --- Agent Methods ---

    async def agent_stream(
        self,
        task: str,
        context: Optional[AgentContext] = None,
    ) -> AsyncIterator[AgentResponse]:
        """Stream an agent task execution."""
        ...

    # --- Utility Methods ---

    async def warm_connection(self) -> bool:
        """Warm the connection pool."""
        ...

    async def get_available_models(self) -> List[ModelInfo]:
        """Get list of available models."""
        ...
```

#### 4. BidiStreamHandler
```python
class BidiStreamHandler:
    """Handles bidirectional streaming for Cursor API."""

    def __init__(self, client: httpx.AsyncClient, headers: Dict[str, str]):
        self.client = client
        self.headers = headers
        self.decoder = CursorStreamDecoder()
        self._append_seqno = 0

    async def stream_request(
        self,
        endpoint: str,
        initial_request: bytes,
    ) -> AsyncIterator[StreamMessage]:
        """
        Perform bidirectional streaming.

        Note: httpx doesn't support true bidirectional streaming.
        For full bidi support, consider using grpclib or h2.
        """
        # Current approach: server-streaming with initial request
        async with self.client.stream(
            "POST",
            endpoint,
            headers=self.headers,
            content=initial_request,
        ) as response:
            async for chunk in response.aiter_bytes():
                for message in self.decoder.feed_data(chunk):
                    yield message

    async def append_data(
        self,
        request_id: str,
        data: str,
    ) -> bool:
        """
        Append data to an existing stream via BidiService.

        This is used for follow-up requests in a conversation.
        """
        request = BidiAppendRequest(
            data=data,
            request_id=request_id,
            append_seqno=self._append_seqno,
        )
        self._append_seqno += 1
        ...
```

#### 5. ErrorHandler
```python
class CursorAPIError(Exception):
    """Base exception for Cursor API errors."""

    def __init__(self, code: int, message: str, details: Optional[dict] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"[{code}] {message}")


class ResourceExhaustedError(CursorAPIError):
    """Raised when API returns resource_exhausted (429/code 41)."""

    def __init__(self, details: Optional[dict] = None):
        super().__init__(
            code=41,
            message="Resource exhausted - rate limited or quota exceeded",
            details=details,
        )
        self.retry_after = details.get("retry_after") if details else None
        self.is_retryable = details.get("is_retryable", True) if details else True


class ErrorHandler:
    """Handles error responses from Cursor API."""

    ERROR_MAP = {
        41: ResourceExhaustedError,
        11: AuthTokenNotFoundError,
        40: FreeUserUsageLimitError,
        12: ProUserUsageLimitError,
        5: TimeoutError,
    }

    @classmethod
    def handle_error(cls, response: StreamMessage) -> CursorAPIError:
        """Convert error response to appropriate exception."""
        ...

    @classmethod
    def should_retry(cls, error: CursorAPIError) -> bool:
        """Determine if request should be retried."""
        ...
```

### Streaming Modes Strategy

The client should support fallback between streaming modes:

```
1. Try: StreamUnifiedChatWithTools (BiDi over HTTP/2)
   |
   v (if fails with HTTP/2 error)
2. Try: StreamUnifiedChatWithToolsSSE (Server-Sent Events)
   |
   v (if SSE not supported)
3. Try: StreamUnifiedChatWithToolsPoll (Polling)
```

### Configuration for HTTP/2 Fallback

From the decompiled code, there's a setting `cursor.general.disableHttp2`. The client should respect this and have similar fallback logic:

```python
class TransportSelector:
    """Selects appropriate transport based on availability."""

    async def select_transport(self) -> TransportType:
        """Test connections and select best transport."""
        if await self._test_http2():
            return TransportType.HTTP2_BIDI
        elif await self._test_sse():
            return TransportType.HTTP1_SSE
        else:
            return TransportType.HTTP1_POLL
```

## Changes Required to Existing Code

### 1. cursor_http2_client.py
- Update to use new header format (add all new x-cursor-* headers)
- Update client version to `2.3.41`
- Add region selection support
- Add fallback streaming modes
- Improve error handling for resource_exhausted

### 2. cursor_streaming_decoder.py
- Add support for new message types from updated protobuf
- Add `BidiAppendResponse` handling
- Add tool call response handling

### 3. cursor_proper_protobuf.py
- Update field numbers for 2.3.41 schema changes
- Add new request types (BidiAppendRequest, etc.)
- Update model names (claude-4-sonnet, composer-1, etc.)

### 4. cursor_auth_reader.py
- No major changes needed (authentication flow unchanged)

## Open Questions / Needs Investigation

1. **BidiService Usage Pattern**: How exactly is `BidiAppend` used in conjunction with `StreamUnifiedChatWithTools`? Is it for follow-up messages in the same stream?

2. **Agent API Endpoints**: The api5.cursor.sh endpoints are new. Need to capture actual traffic to understand:
   - When agent.api5.cursor.sh is used vs api2.cursor.sh
   - What requests go to regional endpoints

3. **Checksum Algorithm**: The checksum generation has multiple variants. Need to verify exact algorithm for 2.3.41.

4. **Resource Exhausted Root Cause**: Is this a rate limit, quota, or protocol mismatch issue? Need to analyze error response details.

5. **HTTP/2 Settings**: What specific HTTP/2 settings does Cursor use? (frame size, concurrent streams, etc.)

## Implementation Plan

### Phase 1: Core Client
1. Create configuration dataclass
2. Implement header builder with all new headers
3. Update auth reader if needed
4. Basic unary request support

### Phase 2: Streaming
1. Implement server-streaming support
2. Add SSE fallback
3. Implement polling fallback
4. Add stream decoder improvements

### Phase 3: Bidirectional
1. Investigate BidiService usage pattern
2. Implement BidiAppend support
3. Add session management for multi-turn

### Phase 4: Error Handling & Resilience
1. Implement comprehensive error handling
2. Add automatic retry with backoff
3. Add transport fallback logic
4. Add connection pooling

## Dependencies

```
httpx[http2]>=0.25.0  # HTTP/2 support
protobuf>=4.25.0      # Protobuf serialization
grpclib>=0.4.0        # Optional: true bidi support
```

## References

- Decompiled source: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
- FINDINGS.md: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/FINDINGS.md`
- Existing protobuf definitions: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/cursor-grpc/`
