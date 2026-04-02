# Cursor 2.6.22 Reverse Engineering Findings

## Version Metadata

- Cursor version: `2.6.22`
- Commit: `c6285feaba0ad62603f7c22e72f0a170dc8415a0`
- VS Code base: `1.105.1`
- Build quality: `stable`

## Artifact Paths

- Source AppImage: `Cursor-2.6.22-x86_64.AppImage`
- Extracted root: `squashfs-root-2.6.22/`
- Core bundle snapshot: `reveng_2.6.22/original/`

## Core Files Captured

- `original/product.json`
- `original/main.js`
- `original/sharedProcessMain.js`
- `original/extensionHostProcess.js`
- `original/workbench.desktop.main.js`

## Initial Notes

- Track created by cloning the `2.3.41` workspace playbook and backlog model.
- `2.3.41` remains intact under `reveng_2.3.41/` for regression-style diffing.
- Detailed protocol/header/tool deltas are tracked as `TASK-303+`.

## Auth and Prompt Validation (2026-04-02)

- End-to-end prompt flow is working again in this workspace.
- `AvailableModels` and `StreamUnifiedChatWithTools` both return `200` with
  `2.6.22` header conventions.
- Working client profile includes:
  - `x-cursor-client-version: 2.6.22`
  - `x-cursor-client-os-version`
  - `x-cursor-config-version`
  - `x-request-id` + `x-amzn-trace-id`
  - `x-ghost-mode: false`
- OAuth refresh flow confirmed:
  - `POST https://api2.cursor.sh/oauth/token`
  - payload: `grant_type=refresh_token`, `client_id=<prod client id>`,
    `refresh_token=<stored refresh token>`
  - response includes `access_token`
- Implementation notes and command transcripts are in:
  `analysis/TASK-304-auth-models-chat.md`.

## Scope and Limitation Check (2026-04-01)

- `ask` workflow remains healthy after cleanup (`just test`, `just test-all`).
- `AvailableModels` preflight remains healthy (`Session: 200`).
- Experimental agent paths (`cursor_agent_client.py`, `cursor_bidi_client.py`)
  still connect and stream, but are not production-clean yet:
  - decoded output can include transport/protobuf noise;
  - only a subset of local tool handlers are implemented;
  - some server tool-call flows still abort when round-trip continuation is
    incomplete (`ERROR_USER_ABORTED_REQUEST` observed in agent loop).

## Open Questions

1. Which request header set changed between `2.3.41` and `2.6.22`?
2. Did ConnectRPC framing or gzip thresholds change?
3. Are agent tool enums and result schemas still backward-compatible?
4. Which protobuf field-level deltas are required for full agent parity?
