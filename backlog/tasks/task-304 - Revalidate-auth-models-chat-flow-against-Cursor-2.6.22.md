---
id: TASK-304
title: Revalidate auth models chat flow against Cursor 2.6.22
status: Done
assignee: []
created_date: '2026-04-02 10:31'
updated_date: '2026-04-02 10:54'
labels:
  - validation
  - auth
  - chat
  - version-2.6.22
dependencies:
  - TASK-302
  - TASK-303
references:
  - cursor_http2_client.py
  - cursor_proper_protobuf.py
  - reveng_2.6.22/analysis/
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Repeat the same smoke path used for the `2.3.41` implementation on `2.6.22`:
token load, session establishment, model listing, and minimal chat streaming.
Capture any status-code or schema failures and map them to concrete deltas.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Token + machine ID loading confirmed with current Cursor storage
- [x] #2 AvailableModels request tested against 2.6.22 assumptions
- [x] #3 StreamUnifiedChatWithTools request tested with 2.6.22 assumptions
- [x] #4 Failures categorized as auth, headers, schema, or transport drift
- [x] #5 Findings documented in `reveng_2.6.22/analysis/TASK-304-*.md`
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Validated auth/session/chat path for Cursor `2.6.22`.

- Updated client header profile to `2.6.22` conventions.
- Added OAuth refresh-token fallback against `/oauth/token`.
- Fixed SQLite token reads under active Cursor DB lock (`immutable=1`).
- Confirmed end-to-end prompt flow:
  - `./ask "Reply with exactly smoke-ok"` -> `smoke-ok`
  - `just test` and `just demo` both successful.

Detailed notes in `reveng_2.6.22/analysis/TASK-304-auth-models-chat.md`.
<!-- SECTION:FINAL_SUMMARY:END -->
