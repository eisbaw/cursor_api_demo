---
id: TASK-46
title: Analyze NAL (Native Agent Layer) vs Regular Backend streaming paths in Cursor
status: Done
assignee: []
created_date: '2026-01-27 14:48'
updated_date: '2026-01-28 07:02'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyzed NAL (Native Agent Layer) vs Regular Backend streaming paths in Cursor IDE 2.3.41.

## Key Findings

1. **Two Distinct Streaming Architectures**:
   - **NAL Path**: Uses `AgentService/Run` with BiDi streaming, enabled via `isNAL: true` flag
   - **Regular Path**: Uses `AiServerService/StreamComposer` with server streaming

2. **Path Selection Triggers**:
   - Background composer attachment automatically enables NAL
   - `worktree_nal_only` feature gate forces NAL for worktree sessions
   - New conversations in worktrees get NAL when gate is enabled

3. **Technical Differences**:
   - NAL uses `conversationState.fileStatesV2` for file tracking
   - Regular path uses `codeBlockData` for file tracking
   - NAL has 5-second heartbeats and built-in stall detection
   - Different abort controller handling (NAL streams not auto-aborted)

4. **HTTP Transport Modes**:
   - HTTP/2 (default): Full BiDi support
   - HTTP/1.1: SSE fallback mode
   - HTTP/1.0: Maximum compatibility mode
   - Controlled via `cursor.general.disableHttp2` and `cursor.general.disableHttp1SSE`

5. **Fallback Pattern**: Every BiDi method has SSE equivalent (e.g., `StreamBidi` -> `StreamBidiSSE`)

Analysis documented in `/reveng_2.3.41/analysis/TASK-46-nal-streaming.md`
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Documented NAL (Native Agent Layer) vs Regular Backend streaming paths in Cursor 2.3.41:

- NAL uses bidirectional streaming via AgentService/Run
- Regular path uses server streaming via AiServerService/StreamComposer
- Path selection controlled by `isNAL` flag on composer data
- Feature gates like `worktree_nal_only` influence path selection
- Both paths support SSE fallback for HTTP/1.1 environments
- NAL has dedicated stall detection and heartbeat mechanisms

Full analysis at: `/reveng_2.3.41/analysis/TASK-46-nal-streaming.md`
<!-- SECTION:FINAL_SUMMARY:END -->
