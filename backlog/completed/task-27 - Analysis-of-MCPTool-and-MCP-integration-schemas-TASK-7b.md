---
id: TASK-27
title: Analysis of MCPTool and MCP integration schemas (TASK-7b)
status: Done
assignee: []
created_date: '2026-01-27 14:10'
updated_date: '2026-01-28 07:24'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Completed comprehensive analysis of MCP (Model Context Protocol) tool integration schemas in Cursor IDE 2.3.41.

## Key Findings

### Protobuf Schemas Documented
- **aiserver.v1 namespace**: MCPParams, MCPParams.Tool, MCPResult, MCPStream, CallMcpToolParams, CallMcpToolResult, MCPInstructions, MCPControls, AllowedMCPServer, AllowedMCPConfiguration, ListMcpResourcesParams, ListMcpResourcesResult, MCPKnownServerInfo, MCPServerRegistration, MCPRegistryService
- **agent.v1 namespace**: McpToolCall, McpArgs, McpResult, McpSuccess, McpError, McpRejected, McpPermissionDenied, McpTextContent, McpImageContent, McpToolDefinition, McpTools, McpInstructions, McpDescriptor, McpToolDescriptor, McpFileSystemOptions, ListMcpResourcesExecArgs, ListMcpResourcesExecResult, ReadMcpResourceExecArgs

### Tool Types
- `CLIENT_SIDE_TOOL_V2_MCP` (19) - Legacy MCP with MCPParams/MCPResult
- `CLIENT_SIDE_TOOL_V2_CALL_MCP_TOOL` (49) - Direct tool call with CallMcpToolParams/CallMcpToolResult
- `CLIENT_SIDE_TOOL_V2_LIST_MCP_RESOURCES` (44) - List MCP resources
- `CLIENT_SIDE_TOOL_V2_READ_MCP_RESOURCE` (45) - Read MCP resource

### Features Discovered
- Elicitation system for interactive server prompts
- Lease elicitation for long-running operations
- Human review integration (MCPToolReviewModel, MCPToolHumanReviewOption)
- MCPRegistryService for server discovery via domain matching
- Enterprise/team controls via MCPControls
- Hooks integration (beforeMCPExecution, afterMCPExecution)
- Server types: stdio and streamableHttp (with OAuth support)
- Recovery mechanism with consecutive failure tracking

### Output
Full analysis written to: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-27-mcp-tool-schemas.md`
<!-- SECTION:FINAL_SUMMARY:END -->
