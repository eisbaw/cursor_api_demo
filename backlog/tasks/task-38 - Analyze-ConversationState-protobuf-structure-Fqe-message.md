---
id: TASK-38
title: Analyze ConversationState protobuf structure (Fqe message)
status: Done
assignee: []
created_date: '2026-01-27 14:47'
updated_date: '2026-01-28 07:15'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete: ConversationState Protobuf Structure

### Key Findings

**Dual Message Types Identified:**
1. `ConversationState` (agent.v1.ConversationState) - Legacy format with direct message embedding
2. `ConversationStateStructure` (agent.v1.ConversationStateStructure) - Fqe class, uses blob-based storage for NAL

**Fqe (ConversationStateStructure) Fields:**
- `turns_old` (field 2): Deprecated bytes array
- `root_prompt_messages_json` (field 1): Bytes array for system prompts
- `turns` (field 8): Serialized turn data as bytes
- `todos` (field 3): Serialized todo items
- `pending_tool_calls` (field 4): String array
- `token_details` (field 5): ConversationTokenDetails message
- `summary` (field 6): Optional bytes
- `plan` (field 7): Optional bytes
- `previous_workspace_uris` (field 9): String array
- `mode` (field 10): AgentMode enum
- `file_states` / `file_states_v2` (fields 12, 15): File content tracking
- `turn_timings` (field 14): StepTiming array
- `subagent_states` (field 16): Map of SubagentPersistedState
- `self_summary_count` (field 17): uint32
- `read_paths` (field 18): String array

**CloudAgentState Wrapper:**
- Wraps Fqe for cloud background agents
- Contains PR metadata (pr_body, pr_url, branch_name)
- Tracks git state (starting_commit, base_branch, commits)
- Includes grind mode configuration
- Stream resumption via `last_interaction_update_offset_key`

**State Persistence Architecture:**
- CloudAgentStorageService handles save/load
- Blob stores per composer with caching
- Metadata versioning for migrations
- Async write queues for durability

**Checkpoint System:**
- CheckpointHandler manages state snapshots
- Transcript writer for conversation logging
- Cloud transfer extracts state + blobs

### Related Types Documented:
- ConversationTurn (oneof: AgentConversationTurn, ShellConversationTurn)
- ConversationStep (oneof: AssistantMessage, ToolCall, ThinkingMessage)
- TodoItem with TodoStatus enum
- AgentMode enum (AGENT, ASK, PLAN, DEBUG, TRIAGE)
- FileState/FileStateStructure
- StepTiming for performance tracking
- SubagentPersistedState for nested agents

### Output
Analysis written to `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-38-conversation-state.md`
<!-- SECTION:FINAL_SUMMARY:END -->
