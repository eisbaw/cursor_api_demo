---
id: TASK-1
title: Reverse engineer api5.cursor.sh Agent API
status: Done
assignee: []
created_date: '2026-01-27 13:37'
updated_date: '2026-01-28 07:04'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate the new agent endpoints at api5.cursor.sh including agent.api5.cursor.sh and agentn.api5.cursor.sh. Understand the difference between "agent" and "agentn" services. Map the geographic endpoints (gcpp-eucentral, gcpp-uswest). Trace the client code that calls these endpoints.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Document api5.cursor.sh endpoint mapping
- [x] #2 Identify agent vs agentn distinction
- [x] #3 Map geographic routing endpoints
- [x] #4 Document gRPC service definitions
- [x] #5 Trace request/response flow
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Comprehensive analysis of the Cursor IDE agent API at api5.cursor.sh completed. Key findings:

### Endpoint Architecture
- **6 production endpoints** across 3 geographic regions (default, US West, EU Central)
- **Privacy mode distinction**: `agent.*` endpoints for privacy mode (no storage), `agentn.*` for non-privacy mode
- The "n" in "agentn" indicates "non-privacy" or "normal" storage mode

### gRPC Service Definitions
- **agent.v1.AgentService** - Primary BiDi streaming service with Run, RunSSE, RunPoll, NameAgent, GetUsableModels methods
- **aiserver.v1.BackgroundComposerService** - Full background composer management (20+ methods)
- **6 additional agent.v1 services**: ControlService, ExecService, PrivateWorkerBridgeExternalService, LifecycleService, PtyHostService

### Protobuf Message Structures
- **AgentClientMessage** - oneof with 7 message types (run_request, exec_client_message, kv_client_message, conversation_action, interaction_response, client_heartbeat, exec_client_control_message)
- **AgentServerMessage** - oneof with 6 message types (interaction_update, exec_server_message, conversation_checkpoint_update, kv_server_message, interaction_query, exec_server_control_message)

### Client Architecture
- **AgentClientService** wraps BackendClient for agent operations
- **runAgentLoop** function orchestrates the full request flow
- **Transport** uses @bufbuild/connect protocol with HTTP/2

### Authentication
- Bearer token via Authorization header
- Token stored in cursorAuth/accessToken storage
- Automatic refresh via refreshAccessToken()

### Limitations
- Cloud Agents not available in "Privacy Mode (Legacy)" with NO_STORAGE setting
- Users must enable data storage to use Cloud Agents

### Files
- Analysis written to: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-1-agent-api.md`
<!-- SECTION:FINAL_SUMMARY:END -->
