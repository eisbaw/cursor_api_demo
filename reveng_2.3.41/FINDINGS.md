# Cursor 2.3.41 Reverse Engineering Findings

## API Endpoints

### Primary APIs
- `https://api2.cursor.sh` - Main API (same as v1.3)
- `https://api3.cursor.sh` - Telemetry/CmdK
- `https://api4.cursor.sh` - C++ analysis

### NEW: Agent APIs (api5.cursor.sh)
- `https://agent.api5.cursor.sh` - Agent service
- `https://agentn.api5.cursor.sh` - Agent N service
- `https://agent-gcpp-eucentral.api5.cursor.sh` - EU Central region
- `https://agent-gcpp-uswest.api5.cursor.sh` - US West region
- `https://agentn-gcpp-eucentral.api5.cursor.sh` - Agent N EU
- `https://agentn-gcpp-uswest.api5.cursor.sh` - Agent N US West

### Other
- `https://repo42.cursor.sh` - Repository service
- `https://staging.cursor.sh` - Staging
- `https://dev-staging.cursor.sh` - Dev staging

## HTTP Headers

### Known (from v1.3)
- `x-cursor-checksum`
- `x-cursor-client-version`

### NEW Headers
- `x-cursor-canary` - Canary/beta features
- `x-cursor-client-arch` - Architecture (x64, arm64)
- `x-cursor-client-device-type` - Device type
- `x-cursor-client-os` - Operating system
- `x-cursor-client-os-version` - OS version
- `x-cursor-client-type` - Client type
- `x-cursor-config-version` - Config version
- `x-cursor-log` - Logging flag
- `x-cursor-server-region` - Server region selection
- `x-cursor-timezone` - Client timezone

## gRPC Services (59 total)

### Core Services (existed in v1.3)
- `aiserver.v1.AiService` - AI completions
- `aiserver.v1.AuthService` - Authentication
- `aiserver.v1.ChatService` - Chat/conversation
- `aiserver.v1.CmdKService` - Cmd+K inline edits

### NEW Services
- `aiserver.v1.AutopilotService` - Autopilot/agent mode
- `aiserver.v1.BackgroundComposerService` - Background agent tasks
- `aiserver.v1.BidiService` - Bidirectional streaming
- `aiserver.v1.MCPRegistryService` - MCP server registry
- `aiserver.v1.VmDaemonService` - VM/sandbox daemon
- `aiserver.v1.ConversationsService` - Conversation management
- `aiserver.v1.FastApplyService` - Fast code application
- `aiserver.v1.FastSearchService` - Fast search
- `aiserver.v1.FileSyncService` - File synchronization
- `aiserver.v1.GitGraphService` - Git graph operations
- `aiserver.v1.GitIndexService` - Git index operations
- `aiserver.v1.LinterService` - Linting service
- `aiserver.v1.ReviewService` - Code review
- `aiserver.v1.ShadowWorkspaceService` - Shadow workspace
- `aiserver.v1.ToolCallEventService` - Tool call events
- `aiserver.v1.CursorPredictionService` - Cursor predictions
- `aiserver.v1.AiBranchService` - AI branch management
- `aiserver.v1.AiProjectService` - AI project management
- `aiserver.v1.AsyncPlatformService` - Async platform ops
- `aiserver.v1.BugbotService` - Bug detection
- `aiserver.v1.DebuggerService` - Debugging
- `aiserver.v1.HallucinatedFunctionsService` - Hallucination detection?
- `aiserver.v1.RepositoryService` - Repository operations
- `aiserver.v1.UploadService` - File uploads
- `aiserver.v1.TraceService` - Tracing/telemetry

### Admin/Enterprise Services
- `aiserver.v1.EnterpriseAdminService`
- `aiserver.v1.DashboardService`
- `aiserver.v1.TeamCreditsService`
- `aiserver.v1.CreateTeamService`
- `aiserver.v1.DeleteTeamService`
- `aiserver.v1.ListTeamService`

## Key Observations

1. **Agent Architecture**: Major shift to agent-based architecture with dedicated api5.cursor.sh endpoints
2. **Geographic Distribution**: Explicit region support (EU Central, US West)
3. **MCP Integration**: Native MCP (Model Context Protocol) support via MCPRegistryService
4. **Background Processing**: BackgroundComposerService suggests async agent work
5. **Bidirectional Streaming**: BidiService indicates real-time bidirectional communication
6. **Shadow Workspace**: ShadowWorkspaceService for safe code modifications
7. **VM Sandboxing**: VmDaemonService suggests sandboxed execution environment
