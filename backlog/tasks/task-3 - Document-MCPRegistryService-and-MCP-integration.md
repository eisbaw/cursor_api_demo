---
id: TASK-3
title: Document MCPRegistryService and MCP integration
status: Done
assignee: []
created_date: '2026-01-27 13:38'
updated_date: '2026-01-28 07:03'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate aiserver.v1.MCPRegistryService which handles Model Context Protocol (MCP) server registration. Understand how Cursor discovers and connects to MCP servers, the registration protocol, and how tool calls are routed to MCP servers. This is important for understanding Cursor's extensibility model.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Comprehensive analysis of MCPRegistryService and MCP integration in Cursor IDE 2.3.41.

### Key Findings

**MCPRegistryService gRPC Service:**
- Service: `aiserver.v1.MCPRegistryService` with single `GetKnownServers` method
- Returns list of `MCPServerRegistration` objects with domain-to-server mappings
- Used for MCP server discovery when visiting URLs

**MCPService Architecture:**
- Central service managing all MCP server operations (service ID: `mcpService`)
- 21 injected dependencies including storage, file system, analytics, experiments
- Uses SolidJS-style reactive signals for state management
- Aggregates servers from 5 sources: default, user config, project config, extensions, providers

**Server Configuration:**
- File locations: `~/.cursor/mcp.json` (user), `.cursor/mcp.json` (project)
- Two server types: `stdio` (command-based) and `streamableHttp` (network-based)
- Full JSON schema validation with support for `enabledTools`, `envFile`, OAuth config

**MCP Client Architecture:**
- Three client types: EverythingProviderClient, MCPProviderClient, RecoveryWrapperClient
- Self-healing recovery mechanism with 3 retry attempts
- 11 internal commands for MCP operations (callTool, createClient, listOfferings, etc.)

**Tool Discovery and Routing:**
- Tools cached by server ID with reactive updates
- MCP index file system writes tool/resource/prompt JSON files when feature enabled
- Tool calls routed based on availability across all enabled servers

**Extension API:**
- `$registerMCPServer` / `$unregisterMCPServer` for extension-based registration
- MCP Provider Service allows direct provider registration with feature gates
- Supports both stdio and HTTP/SSE server types

**Security Features:**
- Project-managed servers require explicit user approval
- Approval tracked by config hash (invalidated on config change)
- Elicitation system for tool user input during execution
- Allowlist management for automatic tool approval

### Files Analyzed
- `workbench.desktop.main.js` lines 446845-449200 (MCP service implementations)
- Lines 832669-832809 (Extension API handlers)
- Various protobuf message type definitions

### Output
Analysis written to `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-3-mcp-registry.md`
<!-- SECTION:FINAL_SUMMARY:END -->
