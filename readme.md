# Cursor API Client (2.6.22)

Reverse-engineered Python client for Cursor IDE API focused on the `2.6.22`
protocol, auth flow, and streaming chat path.

## Quick Start

```bash
# End-to-end smoke test (auth + prompt)
nix-shell --run "just test"
```

## Workspace Artifacts

- AppImage: `Cursor-2.6.22-x86_64.AppImage`
- Extracted root: `squashfs-root-2.6.22/`
- Core snapshots: `reveng_2.6.22/original/`
- Pretty-printed bundles: `reveng_2.6.22/beautified/`
- Findings and deep dives: `reveng_2.6.22/FINDINGS.md`, `reveng_2.6.22/analysis/`

## Usage

```bash
# Simple query
./ask "Hello"

# Specify model explicitly (optional)
./ask -m <model-id> "Explain quantum computing"

# Live stream chunks as they arrive
./ask --stream "Explain quantum computing"

# Pipe input
echo "What is 2+2?" | ./ask
```

## Available Commands

```bash
just test       # Basic end-to-end prompt check
just demo       # End-to-end demo prompt
just stream-demo # End-to-end live streaming demo
just test-decoder # Decoder frame test
just test-all   # Run smoke + decoder + demo
just help       # Show all commands
```

## Verified Scope and Limits

Validated in this workspace (2026-04-01):

- `nix-shell --run "just test"` succeeds (auth + chat path via `ask`).
- `nix-shell --run "just test-all"` succeeds (smoke + decoder + demo).
- `AvailableModels` preflight returns `200` via `cursor_http2_client.py`.
- Experimental agent paths (`cursor_agent_client.py`, `cursor_bidi_client.py`)
  reach API and stream output, but decoding can include protocol noise.

Current limitations:

- Only a subset of `ClientSideToolV2` handlers are implemented locally.
- Many agent tools intentionally return `TODO`/not-implemented placeholders.
- `cursor_agent_client.py` (httpx path) cannot robustly continue server tool
  requests on the same stream and can end with `ERROR_USER_ABORTED_REQUEST`.
- `cursor_bidi_client.py` is still experimental for tool-call round-trips.

## Project Structure

```text
ask                         # CLI wrapper
cursor_http2_client.py      # HTTP/2 transport + streaming client
cursor_proper_protobuf.py   # Header/auth/checksum + protobuf request encoding
cursor_streaming_decoder.py # Response frame parser
cursor_auth_reader.py       # SQLite token reader
cursor_chat_proto.py        # Low-level protobuf encoder
reveng_2.6.22/              # Decompile/beautify/findings track
```

## Authentication

Reads tokens from Cursor SQLite storage:

- Linux: `~/.config/Cursor/User/globalStorage/state.vscdb`
- macOS: `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb`
- Windows: `%APPDATA%\Cursor\User\globalStorage\state.vscdb`

Primary keys:

- `cursorAuth/accessToken`
- `cursorAuth/refreshToken`
- `storage.serviceMachineId`

Refresh endpoint:

- `POST https://api2.cursor.sh/oauth/token`
- payload: `grant_type=refresh_token`, `client_id`, `refresh_token`

## API Details (2.6.22)

### Endpoints

- `https://api2.cursor.sh` - Primary API and OAuth token refresh
- `https://api3.cursor.sh` - Telemetry and related services
- `https://agent.api5.cursor.sh` - Agent API (privacy)
- `https://agentn.api5.cursor.sh` - Agent API (non-privacy)

### Required Header Profile

```text
Authorization: Bearer {token}
Content-Type: application/connect+proto
Connect-Protocol-Version: 1
x-cursor-client-version: {detected_client_version}
x-cursor-client-type: ide
x-cursor-client-os: {detected_os}
x-cursor-client-arch: {detected_arch}
x-cursor-client-os-version: {kernel_or_os_version}
x-cursor-client-device-type: desktop
x-cursor-checksum: {jyh_cipher_timestamp}{machine_id}[/mac_machine_id]
x-cursor-config-version: {uuid}
x-cursor-timezone: {iana_timezone}
x-ghost-mode: false
x-session-id: {uuid-v5-from-token}
x-request-id: {uuid}
x-amzn-trace-id: Root={same_request_id}
```

### Protocol

- Transport: HTTP/2 with ConnectRPC framing
- Encoding: Binary envelope `[type:1][len:4BE][payload]`
- Chat endpoint: `/aiserver.v1.ChatService/StreamUnifiedChatWithTools`
- Model list endpoint: `/aiserver.v1.AiService/AvailableModels`

## Reverse Engineering

Current decompilation and analysis is under `reveng_2.6.22/`.

- `original/` contains raw extracted core bundles
- `beautified/` contains formatted bundles for analysis
- `analysis/` contains task-oriented deep dives
- `FINDINGS.md` tracks confirmed behavior and deltas

Backlog planning and status lives in `backlog/tasks/`.

## Models

Model availability is dynamic and should be queried from:

- `POST /aiserver.v1.AiService/AvailableModels`

The `ask` CLI defaults to `default` unless `-m` is provided.
