# Cursor API Client

Reverse-engineered Python client for Cursor IDE API (version 2.3.41).

## Quick Start

```bash
nix-shell
just demo
```

## Usage

```bash
# Simple query
./ask "Hello"

# Specify model
./ask -m claude-4.5-opus-high-thinking "Explain quantum computing"

# Pipe input
echo "What is 2+2?" | ./ask
```

## Available Commands

```
just demo       # Claude 4.5 Opus demo
just demo2      # Coding example
just test       # Basic test (gpt-4)
just models     # List available models
just help       # Show all commands
```

## Project Structure

```
ask                         # CLI wrapper
cursor_http2_client.py      # HTTP/2 client (main entry point)
cursor_proper_protobuf.py   # Protobuf encoding + checksum generation
cursor_streaming_decoder.py # Response frame parser
cursor_auth_reader.py       # SQLite token reader
cursor_chat_proto.py        # Low-level protobuf encoder
```

## Authentication

Reads tokens from Cursor's SQLite storage:
- Linux: `~/.config/Cursor/User/globalStorage/state.vscdb`
- macOS: `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb`
- Windows: `%APPDATA%\Cursor\User\globalStorage\state.vscdb`

Keys: `cursorAuth/accessToken`, `storage.serviceMachineId`

## API Details

### Endpoints
- `https://api2.cursor.sh` - Primary API
- `https://api3.cursor.sh` - Telemetry
- `https://agent.api5.cursor.sh` - Agent API (privacy mode)
- `https://agentn.api5.cursor.sh` - Agent API (non-privacy)

### Required Headers
```
Authorization: Bearer {token}
Content-Type: application/connect+proto
Connect-Protocol-Version: 1
x-cursor-client-version: 2.3.41
x-cursor-client-type: ide
x-cursor-client-os: linux
x-cursor-client-arch: x86_64
x-cursor-client-device-type: desktop
x-cursor-checksum: {jyh_cipher_timestamp}{machine_id}
x-ghost-mode: true
```

### Protocol
- Transport: HTTP/2 with ConnectRPC (gRPC-Web variant)
- Encoding: Binary protobuf with envelope `[type:1][len:4BE][payload]`
- Chat endpoint: `/aiserver.v1.ChatService/StreamUnifiedChatWithTools`

### Checksum Algorithm (Jyh Cipher)
```python
timestamp = int(time.time() * 1000 // 1000000)
bytes = [timestamp >> 40, timestamp >> 32, timestamp >> 24,
         timestamp >> 16, timestamp >> 8, timestamp & 255]
key = 165
for i in range(6):
    bytes[i] = ((bytes[i] ^ key) + i) % 256
    key = bytes[i]
checksum = base64_urlsafe(bytes) + machine_id
```

## Reverse Engineering

Analysis of Cursor 2.3.41 in `reveng_2.3.41/`:
- `analysis/` - 128 task analysis documents
- `original/` - Source files (workbench.desktop.main.js, etc.)
- `FINDINGS.md` - API endpoints, gRPC services, headers

Task backlog in `backlog/tasks/` (293 pending, 8 completed).

## Models

Available models include:
- `claude-4.5-opus-high-thinking`
- `claude-4.5-opus-high`
- `claude-4.5-sonnet-thinking`
- `claude-4-sonnet`
- `gpt-4o`
- `gpt-5.1-codex`
- `default` (server picks)
