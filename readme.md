# Cursor API Reference Documentation

## Demo

```
❯ nix-shell --run 'echo who are you | uv run ./ask -m claude-4-sonnet' | fmt
I'm Claude, an AI coding assistant powered by Claude Sonnet 4, operating
within Cursor. I'm here to help you#! with your coding tasks through pair
programming.My main role is to:- Help you write, debug, and improve code-
Answer programming questions- Assist with code reviews and refactoring-
Provide guidance on best practices and solutions can see information about
your current coding environment, including open files, cursor position,
edit history, and linter errors when relevant designed to follow
```


## Errata
There is still something to debug:

```
❯ nix-shell --run 'echo who are you | uv run ./ask -m claude-4-opus' | fmt
4{"error":{"code":"resource_exhausted","message":"Error","details":[{"type":"aiserver.v1.ErrorDetails","debug":{"error":"ERROR_GPT_4_VISION_PREVIEW_RATE_LIMIT","details":{"title":"Model
not allowed","detail":"Claude 4 Opus and Claude 4 Opus Thinking are
only available with Max mode. Upgrade to version 0.50.0 to use these
models."},"isExpected":true},"value":"CBw...
```

Protobuf schemas are still to be obtained from the extracted squashfs AppImage.


## Overview
This document provides a clean, comprehensive reference for the Cursor IDE API based on reverse engineering of version 1.3.7.


## Method
Here is a rough outline:

1. Download Linux AppImage.
2. Ask claude to make a PRD: Extract AppImage, beautify all javascript files, look for endpoints, auth, tokens and keys.
3. Run cursor via ltrace -p for specific PIDs only - namely those that send traffic as reported by netstat -antpu.
4. Ask claude to implement a minimal chat client in python.

In practice this takes some hours.


## API Endpoints

### Base URLs
- **Primary API**: `https://api2.cursor.sh`
- **Secondary API**: `https://api3.cursor.sh` (Telemetry & CmdK)
- **Geo API**: `https://api4.cursor.sh` (C++ analysis)
- **Repository Service**: `https://repo42.cursor.sh`
- **Authentication**: `prod.authentication.cursor.sh`
- **Marketplace**: `https://marketplace.cursorapi.com`

### Main Services

#### 1. Authentication Service (`aiserver.v1.AuthService`)
- `/aiserver.v1.AuthService/GetEmail` - Get user email
  - Method: POST
  - Protocol: ConnectRPC (JSON)
  - Response: `{"email":"user@example.com","signUpType":"SIGN_UP_TYPE_AUTH_0"}`

#### 2. AI Service (`aiserver.v1.AiService`)
- `/aiserver.v1.AiService/AvailableModels` - List available models
  - Method: POST
  - Protocol: HTTP/1.1 + `application/proto`
  - Response: List of 23+ models including claude-3.5-sonnet, gpt-4, cursor-small

#### 3. Chat Service (`aiserver.v1.ChatService`)
- `/aiserver.v1.ChatService/StreamUnifiedChatWithTools` - Main chat endpoint
  - Method: POST
  - Protocol: HTTP/2 + `application/connect+proto` (CRITICAL: Requires HTTP/2)
  - Type: Bidirectional streaming
  - Used for: AI conversations with tool integration

#### 4. CmdK Service (`aiserver.v1.CmdKService`)
- `/aiserver.v1.CmdKService/StreamCmdK` - Command palette AI
  - Method: POST
  - Protocol: gRPC-Web
  - Used for: Cmd+K functionality

## Authentication

### Token Storage
Authentication tokens are stored in SQLite database:
- **Linux**: `~/.config/Cursor/User/globalStorage/state.vscdb`
- **macOS**: `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb`
- **Windows**: `%APPDATA%\Cursor\User\globalStorage\state.vscdb`

### Token Keys
- `cursorAuth/accessToken` - Bearer token
- `cursorAuth/refreshToken` - Refresh token
- `cursorAuth/cachedEmail` - User email
- `cursorAuth/stripeMembershipType` - Subscription type

### Required Headers
```
Authorization: Bearer {token}
Content-Type: application/connect+proto
Connect-Protocol-Version: 1
x-cursor-client-version: 0.48.7
x-cursor-checksum: {checksum}
x-client-key: {sha256_hash_of_token}
x-session-id: {uuid_v5_of_token}
```

## Protocol Details

### Transport Protocols
1. **ConnectRPC** - Modern gRPC-Web variant
   - Content-Type: `application/connect+proto`
   - Header: `Connect-Protocol-Version: 1`
   - Binary envelope format with compression

2. **HTTP Version Requirements**
   - AvailableModels: HTTP/1.1
   - StreamUnifiedChatWithTools: HTTP/2 (returns 464 error with HTTP/1.1)

### Message Encoding

#### Binary Envelope Format
```
[Magic Number: 1 byte] [Length: 4 bytes BE] [Protobuf Payload: N bytes]
```
- Magic: 0x00 (uncompressed) or 0x01 (gzip compressed)
- Length: Big-endian 32-bit integer
- Payload: Protocol buffer message

### Session Management
1. Generate session credentials from auth token
2. Call AvailableModels to establish session (HTTP/1.1)
3. Send chat requests (HTTP/2)

## Protobuf Schemas

### StreamUnifiedChatWithToolsRequest
```protobuf
message StreamUnifiedChatWithToolsRequest {
  message Request {
    repeated Message messages = 1;
    Model model = 5;
    string conversationId = 23;
    Metadata metadata = 26;
    repeated MessageId messageIds = 30;
    string chatMode = 54;  // "Ask"
  }
  Request request = 1;
}
```

### Key Message Types
- `Message` - Chat messages with role, content, messageId
- `Model` - Model specification (name, provider)
- `Metadata` - Client metadata (OS, version, timestamps)
- `CursorSetting` - Configuration settings
- `MessageId` - Message tracking

### Usage Event Types
- `UsageEventDetails_Chat` - Standard chat
- `UsageEventDetails_Composer` - Code composer
- `UsageEventDetails_CmdK` - Command palette
- `UsageEventDetails_TerminalCmdK` - Terminal commands
- `UsageEventDetails_FastApply` - Quick code applications

## JavaScript File References

### Core Implementation Files
- **Main Workbench**: `workbench.desktop.main.js` (20.9MB)
  - Contains: `composerChatService`, `submitChatMaybeAbortCurrent`
  - Location: Line ~108 for main submit function
  - Protobuf schemas embedded throughout

- **Beautified Version**: `workbench.desktop.main.pretty.js`
  - Service definitions at various line offsets
  - CmdKService at line ~207898
  - Protocol buffer message definitions

### Key Functions
- `submitChatMaybeAbortCurrent(e, t, n, s)` - Main chat submission
  - e: composer ID
  - t: text/prompt content
  - n: options object
  - s: span context

- `streamUnifiedChatWithTools` - Streaming chat handler
- `computeStreamUnifiedChatRequest` - Request builder
- `warmSubmitChat` - Pre-warm chat system

## Working Implementation Example

```python
# 1. Extract auth token
auth_token = get_bearer_token_from_sqlite()

# 2. Generate session
session_id = uuid.uuid5(uuid.NAMESPACE_DNS, auth_token)
client_key = hashlib.sha256(auth_token.encode()).hexdigest()

# 3. Establish session (HTTP/1.1)
async with httpx.AsyncClient(http2=False) as client:
    response = await client.post(
        "https://api2.cursor.sh/aiserver.v1.AiService/AvailableModels",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/proto",
            "x-cursor-client-version": "0.48.7"
        }
    )

# 4. Send chat (HTTP/2)
async with httpx.AsyncClient(http2=True) as client:
    response = await client.post(
        "https://api2.cursor.sh/aiserver.v1.ChatService/StreamUnifiedChatWithTools",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/connect+proto",
            "x-client-key": client_key,
            "x-session-id": str(session_id)
        },
        content=encoded_protobuf
    )
```

## Key Discoveries

1. **HTTP/2 Requirement**: StreamUnifiedChatWithTools requires HTTP/2, returns 464 "Incompatible Protocol" with HTTP/1.1
2. **Dual Protocol**: Different endpoints use different HTTP versions
3. **Session Sequence**: Must call AvailableModels before chat endpoints
4. **ConnectRPC**: Uses Connect protocol, not standard gRPC-Web
5. **Binary Encoding**: Messages use binary envelope with optional compression

## Application Keys
- **Production**: `KbZUR41cY7W6zRSdpSUJ7I7mLYBKOCmB`
- **Dev/Staging**: `OzaBXLClY5CAGxNzUhQ2vlknpi07tGuE`
- **Embedded AI**: `0c6ae279ed8443289764825290e4f9e2-1a736e7c-1324-4338-be46-fc2a58ae4d14-7255`

Note: These are application-level keys used by all Cursor installations, not user authentication.
