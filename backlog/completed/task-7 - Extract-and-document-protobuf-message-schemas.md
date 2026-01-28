---
id: TASK-7
title: Extract and document protobuf message schemas
status: Done
assignee: []
created_date: '2026-01-27 13:40'
updated_date: '2026-01-28 07:17'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extract the protobuf message definitions from the decompiled JavaScript. There are over 500 aiserver.v1.* message types. Create .proto files or JSON schema documentation for the key messages used in Agent, Chat, and Background services. Focus on request/response pairs for the main services.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Extended analysis of protobuf message schemas from Cursor IDE 2.3.41 decompiled source.

## New Services Documented

1. **AuthService** - Authentication, session management, JWT handling
2. **DashboardService** - Team management, billing, GitHub/GitLab enterprise integration, SCIM groups
3. **EnterpriseAdminService** - Enterprise contracts, token-based pricing
4. **VmDaemonService** - VM-based agent execution environment
5. **TeamCreditsService** - Team credits management
6. **UploadService** - Documentation upload and management

## New Enumerations Documented

- **PlanType** - Free, Pro, Pro Plus, Ultra, Team, Enterprise tiers
- **ScenarioType** - Usage limit scenarios (plan, tier, on-demand)
- **ChatRequestEventType** - Telemetry event types for chat requests
- **EvalRunStatus** - Evaluation run lifecycle states
- **SubAgent** - Terminal, Web, and Programmer subagent types
- **LintSeverity** - Error, Warning, Info, Hint
- **EmbeddingModel** - Ada, Voyage embedding models
- **DatabaseProvider** - Qdrant, Postgres, Milvus

## Key Message Types Added

- **ModelDetails** - Model configuration with Azure/Bedrock state
- **RepositoryInfo** - Repository metadata and indexing config
- **EnvironmentInfo** - Client environment details
- **FileDiff** - Diff representation with chunks

## Analysis File Updated

`/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-7-protobuf-schemas.md`

## Total Services Discovered: 45+
<!-- SECTION:FINAL_SUMMARY:END -->
