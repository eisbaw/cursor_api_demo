# TASK-304: Auth, Models, and Chat Revalidation (2.6.22)

## Objective

Re-run the same minimal auth/session/chat workflow used in `2.3.41` and
validate required protocol updates for `2.6.22`.

## Key Findings

1. `AvailableModels` succeeds with `2.6.22` header profile and returns `200`.
2. `StreamUnifiedChatWithTools` succeeds with HTTP/2 and returns decoded text.
3. End-to-end CLI prompt path is restored (`ask`, `just test`, `just demo`).
4. Previous failures were caused by stale header/version assumptions, not token
   absence.

## Required 2.6.22 Header Surface (Observed Working)

- `x-cursor-client-version: <detected product version>` (2.6.22 here)
- `x-cursor-client-type: ide`
- `x-cursor-client-os: <detected os>` (`linux` here)
- `x-cursor-client-arch: <detected arch>` (`x64` here)
- `x-cursor-client-os-version: <kernel-release>`
- `x-cursor-client-device-type: desktop`
- `x-cursor-config-version: <uuid>`
- `x-cursor-checksum: <jyh-timestamp><machine-id>[/<mac-machine-id>]`
- `x-session-id: <uuid-v5-from-token>`
- `x-request-id` and `x-amzn-trace-id: Root=<request-id>`
- `x-ghost-mode: false`

## OAuth Refresh Flow (Observed in 2.6.22 bundle)

- Endpoint: `POST https://api2.cursor.sh/oauth/token`
- Payload fields:
  - `grant_type=refresh_token`
  - `client_id=KbZUR41cY7W6zRSdpSUJ7I7mLYBKOCmB`
  - `refresh_token=<cursorAuth/refreshToken>`
- Response includes `access_token`, `id_token`, `shouldLogout`.

## Validation Commands and Outcomes

- `nix-shell --run "./ask 'Reply with exactly smoke-ok'"` -> `smoke-ok`
- `nix-shell --run "just test"` -> `I am working perfectly!`
- `nix-shell --run "just demo"` -> successful 2-sentence response

## Code Updates Applied

- `cursor_auth_reader.py`
  - SQLite reads switched to `mode=ro&immutable=1` to avoid lock failures.
- `cursor_proper_protobuf.py`
  - Version-aware header builder for `2.6.22`.
  - OAuth refresh-token fallback support.
  - Updated defaults and session/chat request headers.
- `cursor_http2_client.py`
  - Uses shared `2.6.22` header profile and refresh fallback.
- `ask`
  - Default model switched to `default` for safer cross-account execution.

## Scope Check After Consolidation (2026-04-01)

- `ask` and `just test-all` remain green after cleanup.
- `AvailableModels` preflight still returns `200`.
- Agent clients are still experimental:
  - stream transport/auth path works;
  - many `ClientSideToolV2` handlers remain intentionally stubbed;
  - httpx agent loop can fail with `ERROR_USER_ABORTED_REQUEST` when tool
    result continuation is expected.
