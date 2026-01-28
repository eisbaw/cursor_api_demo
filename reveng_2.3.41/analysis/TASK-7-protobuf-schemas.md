# TASK-7: Protobuf Message Schemas Analysis

**Source:** `reveng_2.3.41/beautified/workbench.desktop.main.js`
**Analysis Date:** 2026-01-28 (Updated)
**Status:** Extended analysis with additional services and enums

## Overview

The Cursor IDE uses Protocol Buffers for communication with its AI server (`aiserver.v1.*` namespace). This document extracts the protobuf message schemas from the decompiled JavaScript.

### Scalar Type Reference

The `T` field in scalar types corresponds to protobuf scalar type numbers:
- `T: 1` = double
- `T: 3` = int64
- `T: 5` = int32
- `T: 8` = bool
- `T: 9` = string
- `T: 12` = bytes
- `T: 13` = uint32

---

## Priority Services

### 1. ChatService (`aiserver.v1.ChatService`)

**Location:** Line ~466427

```protobuf
service ChatService {
  // Main bidirectional streaming chat with tools
  rpc StreamUnifiedChatWithTools(stream StreamUnifiedChatWithToolsRequest)
      returns (stream StreamUnifiedChatResponse);  // BiDiStreaming

  // Server-streaming SSE variant
  rpc StreamUnifiedChatWithToolsSSE(BidiRequestId)
      returns (stream StreamUnifiedChatResponse);  // ServerStreaming

  // Polling variant for environments without streaming
  rpc StreamUnifiedChatWithToolsPoll(BidiPollRequest)
      returns (stream BidiPollResponse);  // ServerStreaming

  // Idempotent variants (same patterns)
  rpc StreamUnifiedChatWithToolsIdempotent(...);
  rpc StreamUnifiedChatWithToolsIdempotentSSE(...);
  rpc StreamUnifiedChatWithToolsIdempotentPoll(...);

  // Non-tool streaming
  rpc StreamUnifiedChat(StreamUnifiedChatRequest)
      returns (stream StreamUnifiedChatResponse);  // ServerStreaming

  // Summary operations
  rpc GetConversationSummary(StreamUnifiedChatRequest)
      returns (ConversationSummary);  // Unary
  rpc StreamSpeculativeSummaries(StreamUnifiedChatRequest)
      returns (stream ConversationSummary);

  // Warm/prefetch connections
  rpc WarmStreamUnifiedChatWithTools(StreamUnifiedChatRequest)
      returns (WarmStreamUnifiedChatWithToolsResponse);  // Unary

  // Prompt dry run
  rpc GetPromptDryRun(StreamUnifiedChatRequest) returns (...);

  // Full file Cmd+K
  rpc StreamFullFileCmdK(StreamUnifiedChatRequest)
      returns (stream StreamUnifiedChatResponse);
  rpc WarmFullFileCmdK(StreamUnifiedChatRequest) returns (...);
}
```

#### StreamUnifiedChatRequest (aiserver.v1.StreamUnifiedChatRequest)
**Location:** Line ~123020

```protobuf
message StreamUnifiedChatRequest {
  // Conversation history
  repeated ConversationMessage conversation = 1;
  repeated ConversationMessageHeaderOnly full_conversation_headers_only = 30;

  // File scanning options
  optional bool allow_long_file_scan = 2;
  optional bool can_handle_filenames_after_language_ids = 4;

  // Context
  ExplicitContext explicit_context = 3;
  ModelDetails model_details = 5;
  LinterErrors linter_errors = 6;
  repeated string documentation_identifiers = 7;
  optional string use_web = 8;
  repeated ComposerExternalLink external_links = 9;
  optional ConversationMessage project_context = 10;

  // File diffs and compression
  repeated FileDiff diffs_for_compressing_files = 11;
  optional bool compress_edits = 12;
  optional bool should_cache = 13;
  repeated LinterErrors multi_file_linter_errors = 14;

  // Current file info
  CurrentFileInfo current_file = 15;
  optional RecentEdits recent_edits = 16;
  optional bool use_reference_composer_diff_prompt = 17;
  repeated FileDiffHistory file_diff_histories = 18;
  optional bool use_new_compression_scheme = 19;
  repeated AdditionalRankedContext additional_ranked_context = 20;
  repeated ChatQuote quotes = 21;

  // Chat metadata
  bool is_chat = 22;
  string conversation_id = 23;
  string replying_to_request_id = 72;

  // Repository info
  RepositoryInfo repository_info = 24;
  bool repository_info_should_query_staging = 25;
  bool repository_info_should_query_prod = 39;
  optional QueryOnlyRepoAccess query_only_repo_access = 52;
  string repo_query_auth_token = 44;

  // Environment and agentic mode
  EnvironmentInfo environment_info = 26;
  bool is_agentic = 27;
  optional ConversationSummary conversation_summary = 28;
  repeated ClientSideToolV2 supported_tools = 29;

  // YOLO/Auto mode
  bool enable_yolo_mode = 31;
  string yolo_prompt = 32;

  // Unified chat options
  bool use_unified_chat_prompt = 33;
  repeated MCPTool mcp_tools = 34;
  optional bool use_full_inputs_context = 35;
  optional bool is_resume = 36;

  // Model fallback options
  optional bool allow_model_fallbacks = 37;
  optional int32 number_of_times_shown_fallback_model_warning = 38;

  // Context bank
  optional string context_bank_session_id = 40;
  optional int32 context_bank_version = 41;
  optional bytes context_bank_encryption_key = 43;

  // Headless/background mode
  bool is_headless = 45;
  bool is_background_composer = 68;
  optional string background_composer_id = 55;

  // Codebase results
  optional UsesCodebaseResults uses_codebase_results = 42;

  // Mode settings
  optional UnifiedMode unified_mode = 46;
  repeated ClientSideToolV2 tools_requiring_accepted_return = 47;
  optional bool should_disable_tools = 48;
  optional ThinkingLevel thinking_level = 49;
  optional bool should_use_chat_prompt = 50;
  optional bool uses_rules = 51;
  optional bool mode_uses_auto_apply = 53;
  optional string unified_mode_name = 54;
  optional bool use_generate_rules_prompt = 56;
  optional bool edit_tool_supports_search_and_replace = 57;

  // Project layout
  repeated ProjectLayout project_layouts = 58;
  optional string repository_name_if_unindexed = 59;
  optional double indexing_progress = 60;
  optional FullFileCmdKOptions full_file_cmd_k_options = 61;
  optional string indexing_phase_if_unindexed = 62;
  optional bool use_knowledge_base_prompt = 63;
  optional int32 indexing_num_files_if_unindexed = 64;
  optional bool supports_mermaid_diagrams = 65;
  optional SubagentInfo subagent_info = 66;

  // Git and dev mode
  bool supports_git_index = 67;
  bool force_is_not_dev = 69;
  optional bool disable_edit_file_timeout = 70;
  optional bool should_attach_linter_errors = 71;
  optional bool should_speculatively_route_gpt5 = 73;
  optional bool force_terminal_hanging_detection = 74;
  optional bool force_summarization = 75;

  // Search and spec mode
  optional bool is_quick_search_query = 76;
  optional bool is_spec_mode = 77;
  bool allow_server_side_semantic_search = 78;
  optional bytes speculative_summarization_encryption_key = 79;

  // Workspace
  repeated WorkspaceFolder workspace_folders = 81;
  optional bool does_readfile_support_images = 82;
  optional bool sandboxing_support_enabled = 83;
  optional string custom_planning_instructions = 84;
  optional bool enable_terminal_file_persistence = 85;
  optional string terminals_folder = 86;
  optional string agent_transcripts_folder = 93;
  optional string agent_notes_folder = 87;
  optional string agent_tools_folder = 88;

  // Plans and MCP
  optional CurrentPlan current_plan = 89;
  optional bool has_mcp_descriptors = 90;

  // Best-of-N sampling
  optional string best_of_n_group_id = 91;
  optional bool try_use_best_of_n_promotion = 92;
}
```

#### StreamUnifiedChatResponse (aiserver.v1.StreamUnifiedChatResponse)
**Location:** Line ~123966

```protobuf
message StreamUnifiedChatResponse {
  // Main text content
  string text = 1;
  optional string server_bubble_id = 22;

  // Debugging
  optional string debugging_only_chat_prompt = 2;
  optional int32 debugging_only_token_count = 3;

  // Citations and references
  DocumentCitation document_citation = 4;
  optional string filled_prompt = 5;
  optional bool is_big_file = 6;
  optional string intermediate_text = 7;
  optional bool is_using_slow_request = 10;
  optional ChunkIdentity chunk_identity = 8;
  optional DocsReference docs_reference = 9;
  optional WebCitation web_citation = 11;
  optional AIWebSearchResults ai_web_search_results = 33;

  // Status and tool calls
  optional StatusUpdates status_updates = 12;
  optional ToolCallV1 tool_call = 13;  // Legacy
  optional ToolCallV2 tool_call_v2 = 36;  // New format
  optional bool should_break_ai_message = 14;
  optional PartialToolCall partial_tool_call = 15;
  optional FinalToolResult final_tool_result = 16;

  // Links and navigation
  optional SymbolLink symbol_link = 17;
  optional FileLink file_link = 19;

  // Conversation summary
  optional ConversationSummary conversation_summary = 18;

  // Service status
  optional ServiceStatusUpdate service_status_update = 20;
  optional ViewableGitContext viewable_git_context = 21;

  // Context and code
  optional ContextPieceUpdate context_piece_update = 23;
  optional UsedCode used_code = 24;

  // Thinking/reasoning
  optional Thinking thinking = 25;
  optional ThinkingStyle thinking_style = 37;
  optional bool stop_using_dsv3_agentic_model = 26;

  // Usage tracking
  optional string usage_uuid = 27;
  optional ConversationSummaryStarter conversation_summary_starter = 28;
  optional SubagentReturn subagent_return = 29;
  optional ContextWindowStatus context_window_status = 30;

  // Image and parallel tool calls
  optional ImageDescription image_description = 31;
  optional bool parallel_tool_calls_complete = 32;

  // Feedback and debugging
  optional StarsFeedbackRequest stars_feedback_request = 34;
  optional string model_provider_request_json = 35;
}
```

---

### 2. AuthService (`aiserver.v1.AuthService`)

**Location:** Line ~814571

Authentication and session management service.

```protobuf
service AuthService {
  // Email operations
  rpc GetEmail(GetEmailRequest) returns (GetEmailResponse);  // Unary
  rpc EmailValid(EmailValidRequest) returns (EmailValidResponse);  // Unary

  // Update management
  rpc DownloadUpdate(DownloadUpdateRequest) returns (DownloadUpdateResponse);  // Unary

  // Privacy settings
  rpc MarkPrivacy(MarkPrivacyRequest) returns (MarkPrivacyResponse);  // Unary
  rpc SetPrivacyMode(SetPrivacyModeRequest) returns (SetPrivacyModeResponse);  // Unary

  // A/B testing
  rpc SwitchCmdKFraction(SwitchCmdKFractionRequest) returns (SwitchCmdKFractionResponse);  // Unary

  // Customer identification
  rpc GetCustomerId(GetCustomerIdRequest) returns (GetCustomerIdResponse);  // Unary

  // Session management
  rpc GetSessionToken(GetSessionTokenRequest) returns (GetSessionTokenResponse);  // Unary
  rpc CheckSessionToken(CheckSessionTokenRequest) returns (CheckSessionTokenResponse);  // Unary
  rpc ListActiveSessions(ListActiveSessionsRequest) returns (ListActiveSessionsResponse);  // Unary
  rpc RevokeSession(RevokeSessionRequest) returns (RevokeSessionResponse);  // Unary

  // JWT management
  rpc ListJwtPublicKeys(ListJwtPublicKeysRequest) returns (ListJwtPublicKeysResponse);  // Unary
}
```

---

### 3. DashboardService (`aiserver.v1.DashboardService`)

**Location:** Line ~718909

Team, billing, and account management service.

```protobuf
service DashboardService {
  // Team operations
  rpc GetTeams(GetTeamsRequest) returns (GetTeamsResponse);  // Unary
  rpc GetMe(GetMeRequest) returns (GetMeResponse);  // Unary
  rpc CreateTeam(CreateTeamRequest) returns (CreateTeamResponse);  // Unary
  rpc GetTeamMembers(GetTeamMembersRequest) returns (GetTeamMembersResponse);  // Unary
  rpc GetTeamUsage(GetTeamUsageRequest) returns (GetTeamUsageResponse);  // Unary
  rpc GetTeamIdForReactivation(GetTeamIdForReactivationRequest) returns (GetTeamIdForReactivationResponse);  // Unary

  // Invitations
  rpc SendTeamInvite(SendTeamInviteRequest) returns (SendTeamInviteResponse);  // Unary
  rpc GetTeamInviteLink(GetTeamInviteLinkRequest) returns (GetTeamInviteLinkResponse);  // Unary
  rpc AcceptInvite(AcceptInviteRequest) returns (AcceptInviteResponse);  // Unary

  // Member management
  rpc UpdateRole(UpdateRoleRequest) returns (UpdateRoleResponse);  // Unary
  rpc RemoveMember(RemoveMemberRequest) returns (RemoveMemberResponse);  // Unary
  rpc ChangeSeat(ChangeSeatRequest) returns (ChangeSeatResponse);  // Unary

  // Group management (SCIM)
  rpc GetDirectoryGroups(GetDirectoryGroupsRequest) returns (GetDirectoryGroupsResponse);  // Unary
  rpc UpdateDirectoryGroupSettings(UpdateDirectoryGroupSettingsRequest) returns (UpdateDirectoryGroupSettingsResponse);  // Unary
  rpc GetGroups(GetGroupsRequest) returns (GetGroupsResponse);  // Unary
  rpc GetGroupMembers(GetGroupMembersRequest) returns (GetGroupMembersResponse);  // Unary
  rpc CreateGroup(CreateGroupRequest) returns (CreateGroupResponse);  // Unary
  rpc UpdateGroup(UpdateGroupRequest) returns (UpdateGroupResponse);  // Unary
  rpc DeleteGroup(DeleteGroupRequest) returns (DeleteGroupResponse);  // Unary
  rpc AddGroupMembers(AddGroupMembersRequest) returns (AddGroupMembersResponse);  // Unary
  rpc RemoveGroupMembers(RemoveGroupMembersRequest) returns (RemoveGroupMembersResponse);  // Unary
  rpc BulkAssignGroupMembers(BulkAssignGroupMembersRequest) returns (BulkAssignGroupMembersResponse);  // Unary
  rpc PreviewAttachGroupToDirectory(PreviewAttachGroupToDirectoryRequest) returns (PreviewAttachGroupToDirectoryResponse);  // Unary
  rpc DetachGroupFromDirectory(DetachGroupFromDirectoryRequest) returns (DetachGroupFromDirectoryResponse);  // Unary
  rpc GetScimConflicts(GetScimConflictsRequest) returns (GetScimConflictsResponse);  // Unary

  // Billing and subscriptions
  rpc GetActivationCheckoutUrl(GetActivationCheckoutUrlRequest) returns (GetActivationCheckoutUrlResponse);  // Unary
  rpc GetTeamCustomerPortalUrl(GetTeamCustomerPortalUrlRequest) returns (GetTeamCustomerPortalUrlResponse);  // Unary
  rpc ChangeTeamSubscription(ChangeTeamSubscriptionRequest) returns (ChangeTeamSubscriptionResponse);  // Unary
  rpc GetMonthlyInvoice(GetMonthlyInvoiceRequest) returns (GetMonthlyInvoiceResponse);  // Unary
  rpc ListInvoiceCycles(ListInvoiceCyclesRequest) returns (ListInvoiceCyclesResponse);  // Unary
  rpc GetDailySpendByCategory(GetDailySpendByCategoryRequest) returns (GetDailySpendByCategoryResponse);  // Unary
  rpc GetPricingHistory(GetPricingHistoryRequest) returns (GetPricingHistoryResponse);  // Unary

  // Usage limits
  rpc GetHardLimit(GetHardLimitRequest) returns (GetHardLimitResponse);  // Unary
  rpc SetHardLimit(SetHardLimitRequest) returns (SetHardLimitResponse);  // Unary
  rpc EnableOnDemandSpend(EnableOnDemandSpendRequest) returns (EnableOnDemandSpendResponse);  // Unary
  rpc GetSignUpType(GetSignUpTypeRequest) returns (GetSignUpTypeResponse);  // Unary

  // GitHub integration
  rpc ConnectGithubCallback(ConnectGithubCallbackRequest) returns (ConnectGithubCallbackResponse);  // Unary
  rpc RegisterGithubCursorCode(RegisterGithubCursorCodeRequest) returns (RegisterGithubCursorCodeResponse);  // Unary
  rpc DisconnectGithub(DisconnectGithubRequest) returns (DisconnectGithubResponse);  // Unary

  // GitHub Enterprise
  rpc PrepareSetupGithubEnterpriseApp(PrepareSetupGithubEnterpriseAppRequest) returns (PrepareSetupGithubEnterpriseAppResponse);  // Unary
  rpc FinishSetupGithubEnterpriseApp(FinishSetupGithubEnterpriseAppRequest) returns (FinishSetupGithubEnterpriseAppResponse);  // Unary
  rpc ListGithubEnterpriseApps(ListGithubEnterpriseAppsRequest) returns (ListGithubEnterpriseAppsResponse);  // Unary
  rpc DeleteGithubEnterpriseApp(DeleteGithubEnterpriseAppRequest) returns (DeleteGithubEnterpriseAppResponse);  // Unary

  // GitLab Enterprise
  rpc SetupGitlabEnterpriseInstance(SetupGitlabEnterpriseInstanceRequest) returns (SetupGitlabEnterpriseInstanceResponse);  // Unary
  rpc ListGitlabEnterpriseInstances(ListGitlabEnterpriseInstancesRequest) returns (ListGitlabEnterpriseInstancesResponse);  // Unary
  rpc DeleteGitlabEnterpriseInstance(DeleteGitlabEnterpriseInstanceRequest) returns (DeleteGitlabEnterpriseInstanceResponse);  // Unary
  rpc SyncGitlabRepos(SyncGitlabReposRequest) returns (SyncGitlabReposResponse);  // Unary

  // Account management
  rpc DeleteAccount(DeleteAccountRequest) returns (DeleteAccountResponse);  // Unary

  // Background composer secrets
  rpc ListBackgroundComposerSecrets(...) returns (...);  // Unary
}
```

---

### 4. EnterpriseAdminService (`aiserver.v1.EnterpriseAdminService`)

**Location:** Line ~819142

Enterprise contract and pricing management.

```protobuf
service EnterpriseAdminService {
  // Manual contracts
  rpc GetManualEnterpriseContract(GetManualEnterpriseContractRequest)
      returns (GetManualEnterpriseContractResponse);  // Unary
  rpc ListManualEnterpriseContracts(ListManualEnterpriseContractsRequest)
      returns (ListManualEnterpriseContractsResponse);  // Unary
  rpc CreateManualEnterpriseContract(CreateManualEnterpriseContractRequest)
      returns (CreateManualEnterpriseContractResponse);  // Unary
  rpc UpsertManualEnterpriseContract(UpsertManualEnterpriseContractRequest)
      returns (UpsertManualEnterpriseContractResponse);  // Unary
  rpc DeleteManualEnterpriseContract(DeleteManualEnterpriseContractRequest)
      returns (DeleteManualEnterpriseContractResponse);  // Unary

  // Contract expansions
  rpc CreateContractExpansion(CreateContractExpansionRequest)
      returns (CreateContractExpansionResponse);  // Unary

  // Enterprise contracts
  rpc ListEnterpriseContracts(ListEnterpriseContractsRequest)
      returns (ListEnterpriseContractsResponse);  // Unary

  // Token-based pricing
  rpc EnableTokenBasedPricing(EnableTokenBasedPricingRequest)
      returns (EnableTokenBasedPricingResponse);  // Unary
  rpc StartTokenBasedTrial(StartTokenBasedTrialRequest)
      returns (StartTokenBasedTrialResponse);  // Unary

  // Status
  rpc GetEnterpriseStatus(GetEnterpriseStatusRequest)
      returns (GetEnterpriseStatusResponse);  // Unary
}
```

---

### 5. BidiService (`aiserver.v1.BidiService`)

**Location:** Line ~810613

For environments where bidirectional streaming is unavailable.

```protobuf
service BidiService {
  // Append data to a bidirectional stream
  rpc BidiAppend(BidiAppendRequest) returns (BidiAppendResponse);  // Unary
}
```

#### BidiRequestId (aiserver.v1.BidiRequestId)
**Location:** Line ~439115

```protobuf
message BidiRequestId {
  string request_id = 1;
}
```

#### BidiAppendRequest (aiserver.v1.BidiAppendRequest)
**Location:** Line ~439145

```protobuf
message BidiAppendRequest {
  string data = 1;
  BidiRequestId request_id = 2;
  int64 append_seqno = 3;
}
```

#### BidiPollRequest (aiserver.v1.BidiPollRequest)
**Location:** Line ~439210

```protobuf
message BidiPollRequest {
  BidiRequestId request_id = 1;
  optional bool start_request = 2;
}
```

#### BidiPollResponse (aiserver.v1.BidiPollResponse)
**Location:** Line ~439246

```protobuf
message BidiPollResponse {
  int64 seqno = 1;
  string data = 2;
  optional bool eof = 3;
}
```

---

### 6. VmDaemonService (`aiserver.v1.VmDaemonService`)

**Location:** Line ~831475

Service for VM-based agent execution environment.

```protobuf
service VmDaemonService {
  // Index management
  rpc SyncIndex(SyncIndexRequest) returns (SyncIndexResponse);  // Unary
  rpc CompileRepoIncludeExcludePatterns(CompileRepoIncludeExcludePatternsRequest)
      returns (CompileRepoIncludeExcludePatternsResponse);  // Unary

  // Lifecycle
  rpc Upgrade(UpgradeRequest) returns (UpgradeResponse);  // Unary
  rpc Ping(PingRequest) returns (PingResponse);  // Unary

  // Execution
  rpc Exec(ExecRequest) returns (ExecResponse);  // Unary
  rpc CallClientSideV2Tool(CallClientSideV2ToolRequest) returns (CallClientSideV2ToolResponse);  // Unary

  // File operations
  rpc ReadTextFile(ReadTextFileRequest) returns (ReadTextFileResponse);  // Unary
  rpc WriteTextFile(WriteTextFileRequest) returns (WriteTextFileResponse);  // Unary
  rpc GetFileStats(GetFileStatsRequest) returns (GetFileStatsResponse);  // Unary

  // Context
  rpc GetExplicitContext(GetExplicitContextRequest) returns (GetExplicitContextResponse);  // Unary
  rpc GetEnvironmentInfo(GetEnvironmentInfoRequest) returns (GetEnvironmentInfoResponse);  // Unary

  // Authentication
  rpc ProvideTemporaryAccessToken(ProvideTemporaryAccessTokenRequest)
      returns (ProvideTemporaryAccessTokenResponse);  // Unary
  rpc RefreshGitHubAccessToken(RefreshGitHubAccessTokenRequest)
      returns (RefreshGitHubAccessTokenResponse);  // Unary

  // Workspace
  rpc WarmCursorServer(WarmCursorServerRequest) returns (WarmCursorServerResponse);  // Unary
  rpc GetWorkspaceChangesHash(GetWorkspaceChangesHashRequest)
      returns (GetWorkspaceChangesHashResponse);  // Unary
  rpc GetDiff(GetDiffRequest) returns (DiffResult);  // Unary
  rpc GetLinterErrors(GetLinterErrorsRequest) returns (GetLinterErrorsResponse);  // Unary
  rpc GetLogs(GetLogsRequest) returns (GetLogsResponse);  // Unary

  // Extensions
  rpc InstallExtensions(InstallExtensionsRequest) returns (InstallExtensionsResponse);  // Unary

  // MCP
  rpc GetMcpTools(GetMcpToolsRequest) returns (GetMcpToolsResponse);  // Unary

  // Telemetry
  rpc TrackModel(TrackModelRequest) returns (TrackModelResponse);  // Unary
  rpc CallDiagnosticsExecutor(CallDiagnosticsExecutorRequest)
      returns (CallDiagnosticsExecutorResponse);  // Unary
}
```

---

### 7. TeamCreditsService (`aiserver.v1.TeamCreditsService`)

**Location:** Line ~828176

Team credits management.

```protobuf
service TeamCreditsService {
  rpc GetTeamCredits(GetTeamCreditsRequest) returns (GetTeamCreditsResponse);  // Unary
  rpc SetTeamCredits(SetTeamCreditsRequest) returns (SetTeamCreditsResponse);  // Unary
  rpc ClearTeamCredits(ClearTeamCreditsRequest) returns (ClearTeamCreditsResponse);  // Unary
}
```

---

### 8. UploadService (`aiserver.v1.UploadService`)

**Location:** Line ~829266

Documentation upload and management.

```protobuf
service UploadService {
  rpc UploadDocumentation(UploadDocumentationRequest) returns (UploadDocumentationResponse);  // Unary
  rpc UploadDocumentationStatus(UploadDocumentationStatusRequest) returns (UploadStatusResponse);  // Unary
  rpc MarkAsPublic(MarkAsPublicRequest) returns (UploadStatusResponse);  // Unary
  rpc UploadStatus(UploadStatusRequest) returns (UploadStatusResponse);  // Unary
  rpc GetPages(GetPagesRequest) returns (GetPagesResponse);  // Unary
  rpc GetDoc(GetDocRequest) returns (GetDocResponse);  // Unary
  rpc RescrapeDocs(RescrapeDocsRequest) returns (RescrapeDocsResponse);  // Unary
  rpc RescrapeDocsV2(RescrapeDocsV2Request) returns (RescrapeDocsResponse);  // Unary
  rpc UpsertAllDocs(UpsertAllDocsRequest) returns (UpsertAllDocsResponse);  // Unary
}
```

---

## Core Message Types

### ModelDetails (aiserver.v1.ModelDetails)
**Location:** Line ~91789

```protobuf
message ModelDetails {
  optional string model_name = 1;
  optional string api_key = 2;
  optional bool enable_ghost_mode = 3;
  optional AzureState azure_state = 4;
  optional bool enable_slow_pool = 5;
  optional string openai_api_base_url = 6;
  optional BedrockState bedrock_state = 7;
  optional bool max_mode = 8;
}
```

### RepositoryInfo (aiserver.v1.RepositoryInfo)
**Location:** Line ~101535

```protobuf
message RepositoryInfo {
  string relative_workspace_path = 1;
  repeated string remote_urls = 2;
  repeated string remote_names = 3;
  string repo_name = 4;
  string repo_owner = 5;
  bool is_tracked = 6;
  bool is_local = 7;
  optional int32 num_files = 8;
  optional double orthogonal_transform_seed = 9;
  optional EmbeddingModel preferred_embedding_model = 10;
  string workspace_uri = 11;
  optional DatabaseProvider preferred_db_provider = 12;
}
```

### EnvironmentInfo (aiserver.v1.EnvironmentInfo)
**Location:** Line ~90145

```protobuf
message EnvironmentInfo {
  optional string exthost_platform = 1;
  optional string exthost_arch = 2;
  optional string exthost_release = 3;
  optional string exthost_shell = 4;
  optional string local_timestamp = 5;
  repeated string workspace_uris = 6;
  optional string cursor_version = 7;
  optional bool is_remote = 8;
  optional string local_os_type = 9;
  optional string home_directory = 10;
  optional string local_timezone = 11;
}
```

### FileDiff (aiserver.v1.FileDiff)
**Location:** Line ~90571

```protobuf
message FileDiff {
  int32 added = 4;
  int32 removed = 5;
  string from = 1;
  string to = 2;
  repeated Chunk chunks = 3;
  optional string before_file_contents = 6;
  optional string after_file_contents = 7;

  message Chunk {
    string content = 1;
    repeated string lines = 2;
    int32 old_start = 3;
    int32 old_lines = 4;
    int32 new_start = 5;
    int32 new_lines = 6;
  }
}
```

### SimpleRange (aiserver.v1.SimpleRange)
**Location:** Line ~90690

```protobuf
message SimpleRange {
  int32 start_line_number = 1;
  int32 start_column = 2;
  int32 end_line_number_inclusive = 3;
  int32 end_column = 4;
}
```

---

## Key Enumerations

### PlanType (aiserver.v1.PlanType)
**Location:** Line ~829328

```protobuf
enum PlanType {
  PLAN_TYPE_UNSPECIFIED = 0;
  PLAN_TYPE_FREE = 1;
  PLAN_TYPE_FREE_TRIAL = 2;
  PLAN_TYPE_PRO = 3;
  PLAN_TYPE_PRO_STUDENT = 4;
  PLAN_TYPE_PRO_PLUS = 5;
  PLAN_TYPE_ULTRA = 6;
  PLAN_TYPE_TEAM = 7;
  PLAN_TYPE_ENTERPRISE = 8;
}
```

### ScenarioType (aiserver.v1.ScenarioType)
**Location:** Line ~829359

```protobuf
enum ScenarioType {
  SCENARIO_TYPE_UNSPECIFIED = 0;
  SCENARIO_TYPE_PLAN_LIMIT = 1;
  SCENARIO_TYPE_TIER_1_LIMIT = 2;
  SCENARIO_TYPE_TIER_2_LIMIT = 3;
  SCENARIO_TYPE_TIER_3_LIMIT = 4;
  SCENARIO_TYPE_ON_DEMAND_LIMIT = 5;
  SCENARIO_TYPE_TEAM_ON_DEMAND_LIMIT = 6;
  SCENARIO_TYPE_MONTHLY_LIMIT = 7;
  SCENARIO_TYPE_POOLED_LIMIT = 8;
}
```

### ChatRequestEventType (aiserver.v1.ChatRequestEventType)
**Location:** Line ~828202

```protobuf
enum ChatRequestEventType {
  CHAT_REQUEST_EVENT_TYPE_UNSPECIFIED = 0;
  CHAT_REQUEST_EVENT_TYPE_REQUEST_START = 1;
  CHAT_REQUEST_EVENT_TYPE_MODEL_PROVIDER_REQUEST_START = 2;
  CHAT_REQUEST_EVENT_TYPE_START_STREAMING = 3;
  CHAT_REQUEST_EVENT_TYPE_END_STREAMING = 4;
  CHAT_REQUEST_EVENT_TYPE_TOOL_CALL_START = 5;
  CHAT_REQUEST_EVENT_TYPE_TOOL_CALL_END = 6;
  CHAT_REQUEST_EVENT_TYPE_TOOL_CALL_STREAM_FINISHED = 8;
  CHAT_REQUEST_EVENT_TYPE_REQUEST_END = 7;
  CHAT_REQUEST_EVENT_TYPE_PARALLEL_TOOL_CALL_START = 9;
  CHAT_REQUEST_EVENT_TYPE_PARALLEL_TOOL_CALL_END = 10;
  CHAT_REQUEST_EVENT_TYPE_STREAM_STATE_CHANGE = 11;
}
```

### EvalRunStatus (aiserver.v1.EvalRunStatus)
**Location:** Line ~819210

```protobuf
enum EvalRunStatus {
  EVAL_RUN_STATUS_UNSPECIFIED = 0;
  EVAL_RUN_STATUS_PENDING = 1;
  EVAL_RUN_STATUS_BUILDING = 7;
  EVAL_RUN_STATUS_SUBMITTED = 6;
  EVAL_RUN_STATUS_RUNNING = 2;
  EVAL_RUN_STATUS_FINISHED = 3;
  EVAL_RUN_STATUS_FAILED = 4;
  EVAL_RUN_STATUS_KILLED = 5;
}
```

### SubAgent (aiserver.v1.SubAgent)
**Location:** Line ~814651

```protobuf
enum SubAgent {
  SUB_AGENT_UNSPECIFIED = 0;
  SUB_AGENT_TERMINAL_AGENT = 1;
  SUB_AGENT_WEB_AGENT = 2;
  SUB_AGENT_PROGRAMMER_AGENT = 3;
}
```

### SubagentType (aiserver.v1.SubagentType)
**Location:** Line ~121904

```protobuf
enum SubagentType {
  SUBAGENT_TYPE_UNSPECIFIED = 0;
  SUBAGENT_TYPE_BACKGROUND = 1;
  SUBAGENT_TYPE_INLINE = 2;
  // Additional values...
}
```

### LintSeverity (aiserver.v1.LintSeverity)
**Location:** Line ~89920

```protobuf
enum LintSeverity {
  LINT_SEVERITY_UNSPECIFIED = 0;
  LINT_SEVERITY_ERROR = 1;
  LINT_SEVERITY_WARNING = 2;
  LINT_SEVERITY_INFO = 3;
  LINT_SEVERITY_HINT = 4;
}
```

### EmbeddingModel (aiserver.v1.EmbeddingModel)
**Location:** Line ~89954

```protobuf
enum EmbeddingModel {
  EMBEDDING_MODEL_UNSPECIFIED = 0;
  EMBEDDING_MODEL_ADA = 1;
  EMBEDDING_MODEL_VOYAGE = 2;
  // Additional values...
}
```

### DatabaseProvider (aiserver.v1.DatabaseProvider)
**Location:** Line ~97709

```protobuf
enum DatabaseProvider {
  DATABASE_PROVIDER_UNSPECIFIED = 0;
  DATABASE_PROVIDER_QDRANT = 1;
  DATABASE_PROVIDER_POSTGRES = 2;
  DATABASE_PROVIDER_MILVUS = 3;
}
```

### UnifiedMode (aiserver.v1.StreamUnifiedChatRequest.UnifiedMode)
**Location:** Line ~123569

```protobuf
enum UnifiedMode {
  UNIFIED_MODE_UNSPECIFIED = 0;
  UNIFIED_MODE_NORMAL = 1;
  UNIFIED_MODE_AGENT = 2;
  UNIFIED_MODE_CMD_K = 3;
  UNIFIED_MODE_CUSTOM = 4;
  // Additional values...
}
```

### ThinkingLevel (aiserver.v1.StreamUnifiedChatRequest.ThinkingLevel)
**Location:** Line ~123592

```protobuf
enum ThinkingLevel {
  THINKING_LEVEL_UNSPECIFIED = 0;
  THINKING_LEVEL_MEDIUM = 1;
  THINKING_LEVEL_HIGH = 2;
}
```

---

## Tool Enumerations

### ClientSideToolV2 (aiserver.v1.ClientSideToolV2)
**Location:** Line ~104365

The newer tool enumeration used for agentic operations (55+ tools):

```protobuf
enum ClientSideToolV2 {
  UNSPECIFIED = 0;
  READ_SEMSEARCH_FILES = 1;
  RIPGREP_SEARCH = 3;
  READ_FILE = 5;
  LIST_DIR = 6;
  EDIT_FILE = 7;
  FILE_SEARCH = 8;
  SEMANTIC_SEARCH_FULL = 9;
  DELETE_FILE = 11;
  REAPPLY = 12;
  RUN_TERMINAL_COMMAND_V2 = 15;
  FETCH_RULES = 16;
  WEB_SEARCH = 18;
  MCP = 19;
  SEARCH_SYMBOLS = 23;
  BACKGROUND_COMPOSER_FOLLOWUP = 24;
  KNOWLEDGE_BASE = 25;
  FETCH_PULL_REQUEST = 26;
  DEEP_SEARCH = 27;
  CREATE_DIAGRAM = 28;
  FIX_LINTS = 29;
  READ_LINTS = 30;
  GO_TO_DEFINITION = 31;
  TASK = 32;
  AWAIT_TASK = 33;
  TODO_READ = 34;
  TODO_WRITE = 35;
  EDIT_FILE_V2 = 38;
  LIST_DIR_V2 = 39;
  READ_FILE_V2 = 40;
  RIPGREP_RAW_SEARCH = 41;
  GLOB_FILE_SEARCH = 42;
  CREATE_PLAN = 43;
  LIST_MCP_RESOURCES = 44;
  READ_MCP_RESOURCE = 45;
  READ_PROJECT = 46;
  UPDATE_PROJECT = 47;
  TASK_V2 = 48;
  CALL_MCP_TOOL = 49;
  APPLY_AGENT_DIFF = 50;
  ASK_QUESTION = 51;
  SWITCH_MODE = 52;
  GENERATE_IMAGE = 53;
  COMPUTER_USE = 54;
  WRITE_SHELL_STDIN = 55;
}
```

### BuiltinTool (aiserver.v1.BuiltinTool)
**Location:** Line ~104514

Legacy tool enumeration (20 tools):

```protobuf
enum BuiltinTool {
  UNSPECIFIED = 0;
  SEARCH = 1;
  READ_CHUNK = 2;
  GOTODEF = 3;
  EDIT = 4;
  UNDO_EDIT = 5;
  END = 6;
  NEW_FILE = 7;
  ADD_TEST = 8;
  RUN_TEST = 9;
  DELETE_TEST = 10;
  SAVE_FILE = 11;
  GET_TESTS = 12;
  GET_SYMBOLS = 13;
  SEMANTIC_SEARCH = 14;
  GET_PROJECT_STRUCTURE = 15;
  CREATE_RM_FILES = 16;
  RUN_TERMINAL_COMMANDS = 17;
  NEW_EDIT = 18;
  READ_WITH_LINTER = 19;
}
```

---

## All Discovered Services

### Core Services
| Service | Location | Description |
|---------|----------|-------------|
| `aiserver.v1.ChatService` | ~466427 | Main chat and streaming API |
| `aiserver.v1.BidiService` | ~810613 | Bidirectional stream emulation |
| `aiserver.v1.BackgroundComposerService` | ~815697 | Background agent workflows |
| `aiserver.v1.AiService` | ~439286 | General AI operations |
| `aiserver.v1.ReplayChatService` | ~466509 | Replay/debug chat sessions |

### Repository Services
| Service | Location | Description |
|---------|----------|-------------|
| `aiserver.v1.RepositoryService` | ~436912 | Repository indexing and sync |
| `aiserver.v1.GitIndexService` | ~437030 | Git index operations |
| `aiserver.v1.FastSearchService` | ~443228 | Fast codebase search |

### Completion Services
| Service | Location | Description |
|---------|----------|-------------|
| `aiserver.v1.CmdKService` | ~810703 | Cmd+K inline editing |
| `aiserver.v1.CppService` | ~300218 | C++ autocomplete (Copilot++) |
| `aiserver.v1.FastApplyService` | ~300077 | Fast code application |
| `aiserver.v1.CursorPredictionService` | ~817743 | Tab completion predictions |

### Authentication & Dashboard
| Service | Location | Description |
|---------|----------|-------------|
| `aiserver.v1.AuthService` | ~814571 | Authentication |
| `aiserver.v1.DashboardService` | ~718909 | User dashboard |

### Enterprise Services
| Service | Location | Description |
|---------|----------|-------------|
| `aiserver.v1.EnterpriseAdminService` | ~819142 | Enterprise admin |
| `aiserver.v1.TeamCreditsService` | ~828176 | Team credits management |

### VM and Remote Services
| Service | Location | Description |
|---------|----------|-------------|
| `aiserver.v1.VmDaemonService` | ~831475 | VM daemon operations |
| `aiserver.v1.AsyncPlatformService` | ~813450 | Async platform ops |

### Infrastructure Services
| Service | Location | Description |
|---------|----------|-------------|
| `aiserver.v1.FileSyncService` | ~810643 | File synchronization |
| `aiserver.v1.HealthService` | ~823788 | Health checks |
| `aiserver.v1.NetworkService` | ~824232 | Network diagnostics |
| `aiserver.v1.UploadService` | ~829266 | Documentation upload |

### Analytics & Metrics
| Service | Location | Description |
|---------|----------|-------------|
| `aiserver.v1.MetricsService` | ~478761 | Telemetry |
| `aiserver.v1.AnalyticsService` | ~811511 | Analytics |
| `aiserver.v1.TraceService` | ~478819 | Tracing |
| `aiserver.v1.ToolCallEventService` | ~478829 | Tool call events |
| `aiserver.v1.ChatRequestEventService` | ~478839 | Chat request events |
| `aiserver.v1.PerformanceEventService` | ~478789 | Performance events |
| `aiserver.v1.ProfilingService` | ~478799 | Profiling |
| `aiserver.v1.OnlineMetricsService` | ~824745 | Online metrics |
| `aiserver.v1.CiMetricsService` | ~817459 | CI metrics |
| `aiserver.v1.ClientLoggerService` | ~817610 | Client logging |

### Specialized Services
| Service | Location | Description |
|---------|----------|-------------|
| `aiserver.v1.MCPRegistryService` | ~449102 | MCP tool registry |
| `aiserver.v1.LinterService` | ~810745 | Linting operations |
| `aiserver.v1.AutopilotService` | ~815685 | Autopilot mode |
| `aiserver.v1.BugbotService` | ~810625 | Bug detection |
| `aiserver.v1.ReviewService` | ~825972 | Code review |
| `aiserver.v1.DebuggerService` | ~817980 | Debugging |
| `aiserver.v1.GitGraphService` | ~822164 | Git visualization |
| `aiserver.v1.DeeplinkService` | ~818304 | Deep linking |
| `aiserver.v1.ConversationsService` | ~500892 | Conversation management |
| `aiserver.v1.EvalTrackingService` | ~820999 | Evaluation tracking |

### Admin Services
| Service | Location | Description |
|---------|----------|-------------|
| `aiserver.v1.BugbotAdminService` | ~816346 | Bugbot admin |
| `aiserver.v1.ServerConfigService` | ~827949 | Server config |

### Miscellaneous
| Service | Location | Description |
|---------|----------|-------------|
| `aiserver.v1.AiProjectService` | ~809655 | AI project management |
| `aiserver.v1.ShadowWorkspaceService` | ~809709 | Shadow workspace |
| `aiserver.v1.AiBranchService` | ~810571 | AI branch management |
| `aiserver.v1.HallucinatedFunctionsService` | ~823657 | Hallucination detection |
| `aiserver.v1.InAppAdService` | ~824008 | In-app advertising |
| `aiserver.v1.MarketplaceService` | ~824110 | Marketplace |
| `aiserver.v1.RequestReplayService` | ~824949 | Request replay |
| `aiserver.v1.UsageSimulationService` | ~829890 | Usage simulation |
| `aiserver.v1.WebProfilingService` | ~478809 | Web profiling |

---

## Key Findings

1. **Streaming Architecture**: Cursor uses three streaming modes:
   - **BiDiStreaming**: Full bidirectional streaming (WebSocket-like)
   - **ServerStreaming**: Server-sent events (SSE)
   - **Polling**: For environments without streaming support

2. **Tool System Evolution**: Two tool systems exist:
   - **BuiltinTool**: Legacy (20 tools)
   - **ClientSideToolV2**: Modern (55+ tools) with versioned APIs

3. **Agent Architecture**: Background composers enable async processing with state management via blob IDs and offset keys for resumption.

4. **Enterprise Features**:
   - Team and enterprise billing management
   - SCIM group management
   - GitHub/GitLab Enterprise integration
   - Token-based pricing

5. **Plan Tiers**: Free, Free Trial, Pro, Pro Student, Pro Plus, Ultra, Team, Enterprise

6. **VM Daemon**: Support for remote VM-based agent execution with full file system access and MCP tool integration.

7. **Thinking Modes**: Support for different reasoning levels (unspecified, medium, high) for extended thinking.

---

## References

- Tool schemas: `TASK-26-tool-schemas.md`
- Agent schemas: `TASK-25-agent-v1-schemas.md`
- Agent state: `TASK-28-agent-state-schemas.md`
- Source: Line references are from `beautified/workbench.desktop.main.js`
