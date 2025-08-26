# Cursor API Reference Documentation

## Demo

```bash
# Simple usage
❯ ./ask "Hello! Please respond with: I am working perfectly!"
I am working perfectly!

# Quantum computing demo with Claude Sonnet 4
❯ just demo
Quantum computing is a revolutionary computational paradigm that leverages quantum mechanical phenomena like superposition and entanglement to process information in ways that classical computers cannot, allowing quantum bits (qubits) to exist in multiple states simultaneously rather than just the binary 0 or 1 states of classical bits. This enables quantum computers to potentially solve certain complex problems exponentially faster than classical computers, particularly in areas like cryptography, optimization, and scientific simulation, though current quantum computers are still in early development stages and face significant challenges with error rates and maintaining quantum coherence.

# Available justfile commands
❯ just help
Available commands:
  test       - Basic functionality test
  demo       - Quantum computing demo with Claude Sonnet 4
  code-demo  - Coding example with Claude Sonnet 4
  models     - Show available models
  test-all   - Run all tests
  clean      - Clean up generated files
```

## Status: FIXED ✅

**Previous Issue**: Fragmented/garbled output from streaming responses  
**Root Cause**: Incorrect response parsing using regex instead of proper protobuf decoding  
**Solution**: Implemented frame-based protobuf parser based on cursor-api Rust implementation  

The streaming decoder now properly handles:
- Frame format: `[msg_type:1byte][msg_len:4bytes_big_endian][protobuf_data]`
- Message types: 0=protobuf, 1=gzip+protobuf, 2=json, 3=gzip+json
- Nested protobuf structure: `StreamUnifiedChatResponseWithTools.stream_unified_chat_response.text`

**Result**: Clean, properly formatted responses with no fragmentation.


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

## Working Implementation

### Quick Start
```bash
# Enter nix shell for dependencies
nix-shell

# Simple test
./ask "Hello!"

# Use specific model
./ask -m claude-4-sonnet "Explain quantum computing"

# Run demos
just demo      # Quantum computing explanation
just test-all  # All tests
```

### Python Implementation Example
```python
from cursor_streaming_decoder import CursorStreamDecoder
from cursor_http2_client import CursorHTTP2Client

# Initialize client (auto-reads auth from SQLite)
client = CursorHTTP2Client()

# Send chat with proper streaming decode
response = await client.test_http2_breakthrough(
    prompt="Explain quantum computing", 
    model="claude-4-sonnet"
)
print(response)  # Clean, formatted output
```

### Key Implementation Details
```python
# Proper streaming decoder handles frame format
decoder = CursorStreamDecoder()
messages = decoder.feed_data(chunk)

for message in messages:
    if message.msg_type == "content":
        print(message.content)  # Clean text, no fragmentation
```

## Key Discoveries

1. **HTTP/2 Requirement**: StreamUnifiedChatWithTools requires HTTP/2, returns 464 "Incompatible Protocol" with HTTP/1.1
2. **Dual Protocol**: Different endpoints use different HTTP versions
3. **Session Sequence**: Must call AvailableModels before chat endpoints
4. **ConnectRPC**: Uses Connect protocol, not standard gRPC-Web
5. **Binary Encoding**: Messages use binary envelope with optional compression
6. **Frame-Based Parsing**: Streaming responses require proper frame decoding, not text extraction
7. **Protobuf Structure**: Nested `StreamUnifiedChatResponseWithTools` → `StreamUnifiedChatResponse` → `text` field
8. **Compression Support**: Handles gzip compression (msg_type=1,3) and JSON fallback (msg_type=2,3)

## Application Keys
- **Production**: `KbZUR41cY7W6zRSdpSUJ7I7mLYBKOCmB`
- **Dev/Staging**: `OzaBXLClY5CAGxNzUhQ2vlknpi07tGuE`
- **Embedded AI**: `0c6ae279ed8443289764825290e4f9e2-1a736e7c-1324-4338-be46-fc2a58ae4d14-7255`

Note: These are application-level keys used by all Cursor installations, not user authentication.
