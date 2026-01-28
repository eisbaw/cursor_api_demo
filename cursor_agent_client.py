#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor Agent Client with Tool Calling Support

This client implements Agent mode communication with Cursor's API.
Based on reverse engineering analysis of Cursor IDE 2.3.41.

Status:
- [WORKING] Agent mode request encoding (unified_mode=AGENT, is_agentic=true)
- [WORKING] supported_tools field with ClientSideToolV2 enum values
- [WORKING] Tool call detection from server responses
- [WORKING] Local tool execution (read_file, list_dir, grep_search, etc.)
- [WORKING] Tool result encoding (ClientSideToolV2Result)
- [LIMITED] Bidirectional streaming (httpx doesn't support writing after initial request)

To send tool results back, the client needs true HTTP/2 bidirectional streaming.
Options for future improvement:
1. Use grpclib/grpcio for proper gRPC bidirectional streaming
2. Implement with h2 library directly for raw HTTP/2 control
3. Use SSE + BidiAppend fallback (if server supports it)

References:
- TASK-7-protobuf-schemas.md: StreamUnifiedChatRequest schema
- TASK-110-tool-enum-mapping.md: ClientSideToolV2 enum values
- TASK-126-toolv2-params.md: Tool parameter schemas
- TASK-52-toolcall-schema.md: Tool call/result flow
- TASK-2-bidiservice.md: Bidirectional streaming protocol
- TASK-43-sse-poll-fallback.md: SSE/BidiAppend fallback
"""

import asyncio
import httpx
import uuid
import hashlib
import gzip
import time
import os
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from cursor_auth_reader import CursorAuthReader
from cursor_chat_proto import ProtobufEncoder


# ClientSideToolV2 enum values (from TASK-110-tool-enum-mapping.md)
class ClientSideToolV2:
    """All 44 ClientSideToolV2 tools from aiserver.v1"""
    UNSPECIFIED = 0
    READ_SEMSEARCH_FILES = 1       # Semantic search file retrieval
    RIPGREP_SEARCH = 3             # Regex search with ripgrep
    READ_FILE = 5                  # Read file contents
    LIST_DIR = 6                   # List directory contents
    EDIT_FILE = 7                  # Edit file (legacy)
    FILE_SEARCH = 8                # Fuzzy file name search
    SEMANTIC_SEARCH_FULL = 9       # Full semantic search
    DELETE_FILE = 11               # Delete file
    REAPPLY = 12                   # Re-apply previous edit
    RUN_TERMINAL_COMMAND_V2 = 15   # Execute terminal command
    FETCH_RULES = 16               # Fetch cursor rules
    WEB_SEARCH = 18                # Search the web
    MCP = 19                       # Call MCP tool (legacy)
    SEARCH_SYMBOLS = 23            # Search code symbols
    BACKGROUND_COMPOSER_FOLLOWUP = 24  # Followup with background agent
    KNOWLEDGE_BASE = 25            # Query knowledge base
    FETCH_PULL_REQUEST = 26        # Fetch PR information
    DEEP_SEARCH = 27               # Deep codebase search
    CREATE_DIAGRAM = 28            # Create Mermaid diagram
    FIX_LINTS = 29                 # Auto-fix lint errors
    READ_LINTS = 30                # Read lint errors
    GO_TO_DEFINITION = 31          # Go to symbol definition
    TASK = 32                      # Create subagent task
    AWAIT_TASK = 33                # Wait for task completion
    TODO_READ = 34                 # Read todo list
    TODO_WRITE = 35                # Write todo list
    EDIT_FILE_V2 = 38              # Edit file (new)
    LIST_DIR_V2 = 39               # List directory (tree)
    READ_FILE_V2 = 40              # Read file (new)
    RIPGREP_RAW_SEARCH = 41        # Raw ripgrep search
    GLOB_FILE_SEARCH = 42          # Glob pattern file search
    CREATE_PLAN = 43               # Create execution plan
    LIST_MCP_RESOURCES = 44        # List MCP resources
    READ_MCP_RESOURCE = 45         # Read MCP resource
    READ_PROJECT = 46              # Read project info
    UPDATE_PROJECT = 47            # Update project info
    TASK_V2 = 48                   # Create task (new)
    CALL_MCP_TOOL = 49             # Call MCP tool (new)
    APPLY_AGENT_DIFF = 50          # Apply agent-generated diff
    ASK_QUESTION = 51              # Ask user a question
    SWITCH_MODE = 52               # Switch agent mode
    GENERATE_IMAGE = 53            # Generate image
    COMPUTER_USE = 54              # Computer automation
    WRITE_SHELL_STDIN = 55         # Write to shell stdin


# UnifiedMode enum values (from TASK-7)
class UnifiedMode:
    UNSPECIFIED = 0
    NORMAL = 1  # Ask mode
    AGENT = 2   # Agent mode
    CMD_K = 3
    CUSTOM = 4


@dataclass
class ToolCall:
    """Parsed tool call from server"""
    tool: int
    tool_call_id: str
    name: str
    raw_args: str
    params: Dict[str, Any]


@dataclass
class ToolResult:
    """Tool execution result"""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None


class ToolExecutor:
    """Executes tools locally and returns results"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root).resolve()
    
    def execute(self, tool_call: ToolCall) -> ToolResult:
        """Execute a tool call and return result"""
        tool = tool_call.tool
        params = tool_call.params
        
        try:
            if tool == ClientSideToolV2.READ_FILE:
                return self._read_file(params)
            elif tool == ClientSideToolV2.LIST_DIR:
                return self._list_dir(params)
            elif tool == ClientSideToolV2.RIPGREP_SEARCH:
                return self._grep_search(params)
            elif tool == ClientSideToolV2.RUN_TERMINAL_COMMAND_V2:
                return self._run_terminal(params)
            elif tool == ClientSideToolV2.EDIT_FILE:
                return self._edit_file(params)
            elif tool == ClientSideToolV2.FILE_SEARCH:
                return self._file_search(params)
            elif tool == ClientSideToolV2.GLOB_FILE_SEARCH:
                return self._glob_file_search(params)
            # V2 versions - delegate to V1 implementations
            elif tool == ClientSideToolV2.READ_FILE_V2:
                return self._read_file_v2(params)
            elif tool == ClientSideToolV2.LIST_DIR_V2:
                return self._list_dir_v2(params)
            elif tool == ClientSideToolV2.EDIT_FILE_V2:
                return self._edit_file_v2(params)
            elif tool == ClientSideToolV2.RIPGREP_RAW_SEARCH:
                return self._ripgrep_raw_search(params)
            # Stub implementations with TODOs
            elif tool == ClientSideToolV2.DELETE_FILE:
                return self._delete_file(params)
            elif tool == ClientSideToolV2.REAPPLY:
                return self._reapply(params)
            elif tool == ClientSideToolV2.SEMANTIC_SEARCH_FULL:
                return self._semantic_search_full(params)
            elif tool == ClientSideToolV2.READ_SEMSEARCH_FILES:
                return self._read_semsearch_files(params)
            elif tool == ClientSideToolV2.FETCH_RULES:
                return self._fetch_rules(params)
            elif tool == ClientSideToolV2.WEB_SEARCH:
                return self._web_search(params)
            elif tool == ClientSideToolV2.MCP:
                return self._mcp(params)
            elif tool == ClientSideToolV2.SEARCH_SYMBOLS:
                return self._search_symbols(params)
            elif tool == ClientSideToolV2.GO_TO_DEFINITION:
                return self._go_to_definition(params)
            elif tool == ClientSideToolV2.BACKGROUND_COMPOSER_FOLLOWUP:
                return self._background_composer_followup(params)
            elif tool == ClientSideToolV2.KNOWLEDGE_BASE:
                return self._knowledge_base(params)
            elif tool == ClientSideToolV2.FETCH_PULL_REQUEST:
                return self._fetch_pull_request(params)
            elif tool == ClientSideToolV2.DEEP_SEARCH:
                return self._deep_search(params)
            elif tool == ClientSideToolV2.CREATE_DIAGRAM:
                return self._create_diagram(params)
            elif tool == ClientSideToolV2.FIX_LINTS:
                return self._fix_lints(params)
            elif tool == ClientSideToolV2.READ_LINTS:
                return self._read_lints(params)
            elif tool == ClientSideToolV2.TASK:
                return self._task(params)
            elif tool == ClientSideToolV2.AWAIT_TASK:
                return self._await_task(params)
            elif tool == ClientSideToolV2.TODO_READ:
                return self._todo_read(params)
            elif tool == ClientSideToolV2.TODO_WRITE:
                return self._todo_write(params)
            elif tool == ClientSideToolV2.CREATE_PLAN:
                return self._create_plan(params)
            elif tool == ClientSideToolV2.LIST_MCP_RESOURCES:
                return self._list_mcp_resources(params)
            elif tool == ClientSideToolV2.READ_MCP_RESOURCE:
                return self._read_mcp_resource(params)
            elif tool == ClientSideToolV2.READ_PROJECT:
                return self._read_project(params)
            elif tool == ClientSideToolV2.UPDATE_PROJECT:
                return self._update_project(params)
            elif tool == ClientSideToolV2.TASK_V2:
                return self._task_v2(params)
            elif tool == ClientSideToolV2.CALL_MCP_TOOL:
                return self._call_mcp_tool(params)
            elif tool == ClientSideToolV2.APPLY_AGENT_DIFF:
                return self._apply_agent_diff(params)
            elif tool == ClientSideToolV2.ASK_QUESTION:
                return self._ask_question(params)
            elif tool == ClientSideToolV2.SWITCH_MODE:
                return self._switch_mode(params)
            elif tool == ClientSideToolV2.GENERATE_IMAGE:
                return self._generate_image(params)
            elif tool == ClientSideToolV2.COMPUTER_USE:
                return self._computer_use(params)
            elif tool == ClientSideToolV2.WRITE_SHELL_STDIN:
                return self._write_shell_stdin(params)
            else:
                return ToolResult(
                    success=False,
                    data={},
                    error=f"Unsupported tool: {tool}"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                error=str(e)
            )
    
    def _read_file(self, params: Dict) -> ToolResult:
        """Execute read_file tool"""
        path = params.get('relative_workspace_path', '')
        start_line = params.get('start_line_one_indexed', 1)
        end_line = params.get('end_line_one_indexed_inclusive')
        
        full_path = self.workspace_root / path
        
        if not full_path.exists():
            return ToolResult(False, {}, f"File not found: {path}")
        
        if not full_path.is_file():
            return ToolResult(False, {}, f"Not a file: {path}")
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            
            # Apply line range
            start_idx = max(0, start_line - 1)
            end_idx = end_line if end_line else total_lines
            
            selected_lines = lines[start_idx:end_idx]
            contents = ''.join(selected_lines)
            
            return ToolResult(
                success=True,
                data={
                    'contents': contents,
                    'relative_workspace_path': path,
                    'start_line_one_indexed': start_idx + 1,
                    'end_line_one_indexed_inclusive': min(end_idx, total_lines),
                    'total_lines': total_lines,
                }
            )
        except Exception as e:
            return ToolResult(False, {}, str(e))
    
    def _list_dir(self, params: Dict) -> ToolResult:
        """Execute list_dir tool"""
        dir_path = params.get('directory_path', '.')
        
        full_path = self.workspace_root / dir_path
        
        if not full_path.exists():
            return ToolResult(False, {}, f"Directory not found: {dir_path}")
        
        if not full_path.is_dir():
            return ToolResult(False, {}, f"Not a directory: {dir_path}")
        
        try:
            entries = []
            for entry in sorted(full_path.iterdir()):
                if entry.name.startswith('.'):
                    continue  # Skip hidden files
                entries.append({
                    'name': entry.name,
                    'is_directory': entry.is_dir(),
                    'size': entry.stat().st_size if entry.is_file() else 0,
                })
            
            return ToolResult(
                success=True,
                data={
                    'entries': entries,
                    'directory_path': dir_path,
                }
            )
        except Exception as e:
            return ToolResult(False, {}, str(e))
    
    def _grep_search(self, params: Dict) -> ToolResult:
        """Execute ripgrep search tool"""
        pattern = params.get('pattern', '')
        # Try to get pattern from pattern_info if available
        if not pattern and 'pattern_info' in params:
            pattern = params['pattern_info'].get('pattern', '')
        
        if not pattern:
            return ToolResult(False, {}, "No search pattern provided")
        
        try:
            # Try ripgrep first
            cmd = ['rg', '--json', '-m', '50', pattern, str(self.workspace_root)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            matches = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get('type') == 'match':
                        match_data = data.get('data', {})
                        matches.append({
                            'path': match_data.get('path', {}).get('text', ''),
                            'line_number': match_data.get('line_number', 0),
                            'line_content': match_data.get('lines', {}).get('text', '').strip(),
                        })
                except json.JSONDecodeError:
                    continue
            
            return ToolResult(
                success=True,
                data={
                    'matches': matches,
                    'pattern': pattern,
                    'total_matches': len(matches),
                }
            )
        except FileNotFoundError:
            # Fallback to grep if rg not available
            return ToolResult(False, {}, "ripgrep not available")
        except Exception as e:
            return ToolResult(False, {}, str(e))
    
    def _run_terminal(self, params: Dict) -> ToolResult:
        """Execute terminal command tool"""
        command = params.get('command', '')
        cwd = params.get('cwd', str(self.workspace_root))
        
        if not command:
            return ToolResult(False, {}, "No command provided")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return ToolResult(
                success=True,
                data={
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'exit_code': result.returncode,
                }
            )
        except subprocess.TimeoutExpired:
            return ToolResult(False, {}, "Command timed out")
        except Exception as e:
            return ToolResult(False, {}, str(e))
    
    def _edit_file(self, params: Dict) -> ToolResult:
        """Execute edit_file tool"""
        path = params.get('relative_workspace_path', '')
        old_string = params.get('old_string', '')
        new_string = params.get('new_string', '')
        
        full_path = self.workspace_root / path
        
        if not old_string or new_string is None:
            return ToolResult(False, {}, "old_string and new_string required")
        
        try:
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if old_string not in content:
                    return ToolResult(False, {}, f"old_string not found in {path}")
                
                new_content = content.replace(old_string, new_string, 1)
                
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                return ToolResult(
                    success=True,
                    data={
                        'is_applied': True,
                        'relative_workspace_path': path,
                    }
                )
            else:
                # Create new file
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(new_string)
                
                return ToolResult(
                    success=True,
                    data={
                        'is_applied': True,
                        'relative_workspace_path': path,
                    }
                )
        except Exception as e:
            return ToolResult(False, {}, str(e))
    
    def _file_search(self, params: Dict) -> ToolResult:
        """Execute file_search tool - find files by name pattern"""
        query = params.get('query', '')
        
        if not query:
            return ToolResult(False, {}, "No query provided")
        
        try:
            # Use find or fd to search for files
            files = []
            for path in self.workspace_root.rglob(f'*{query}*'):
                if path.is_file() and not any(p.startswith('.') for p in path.parts):
                    rel_path = str(path.relative_to(self.workspace_root))
                    files.append({'uri': rel_path})
                    if len(files) >= 50:  # Limit results
                        break
            
            return ToolResult(
                success=True,
                data={
                    'files': files,
                    'num_results': len(files),
                    'limit_hit': len(files) >= 50,
                }
            )
        except Exception as e:
            return ToolResult(False, {}, str(e))
    
    def _glob_file_search(self, params: Dict) -> ToolResult:
        """Execute glob_file_search tool - find files by glob pattern"""
        pattern = params.get('pattern', params.get('glob_pattern', ''))
        
        if not pattern:
            return ToolResult(False, {}, "No pattern provided")
        
        try:
            files = []
            for path in self.workspace_root.glob(pattern):
                if path.is_file():
                    rel_path = str(path.relative_to(self.workspace_root))
                    files.append({'uri': rel_path})
                    if len(files) >= 100:
                        break
            
            return ToolResult(
                success=True,
                data={
                    'files': files,
                    'num_results': len(files),
                    'limit_hit': len(files) >= 100,
                }
            )
        except Exception as e:
            return ToolResult(False, {}, str(e))
    
    # =========================================================================
    # V2 Tool Implementations (delegate to V1 where applicable)
    # See TASK-110-tool-enum-mapping.md for version evolution
    # =========================================================================
    
    def _read_file_v2(self, params: Dict) -> ToolResult:
        """Read file V2 - uses character-based offsets
        See TASK-26-tool-schemas.md ReadFileV2Params/Result"""
        # V2 uses: target_file, offset (line), limit (lines), chars_limit
        # Delegate to V1 implementation with parameter mapping
        v1_params = {
            'relative_workspace_path': params.get('target_file', ''),
            'start_line_one_indexed': params.get('offset', 0) + 1 if params.get('offset') else None,
            'end_line_one_indexed_inclusive': (params.get('offset', 0) + params.get('limit', 100)) if params.get('limit') else None,
        }
        return self._read_file(v1_params)
    
    def _list_dir_v2(self, params: Dict) -> ToolResult:
        """List directory V2 - returns tree structure
        See TASK-26-tool-schemas.md ListDirV2Params/Result"""
        # TODO: Implement recursive tree structure with depth parameter
        # V2 Result uses DirectoryTreeNode with nested children
        # For now, delegate to V1
        v1_params = {'directory_path': params.get('target_directory', '.')}
        return self._list_dir(v1_params)
    
    def _edit_file_v2(self, params: Dict) -> ToolResult:
        """Edit file V2 - streaming edit support
        See TASK-26-tool-schemas.md EditFileV2Params/Result"""
        # TODO: Implement streaming edit with contents_after_edit
        # V2 supports: streaming_content, diff, result_for_model
        v1_params = {
            'relative_workspace_path': params.get('relative_workspace_path', ''),
            'new_string': params.get('contents_after_edit', ''),
        }
        return self._edit_file(v1_params)
    
    def _ripgrep_raw_search(self, params: Dict) -> ToolResult:
        """Raw ripgrep search - direct rg access
        See TASK-26-tool-schemas.md RipgrepRawSearchParams"""
        # Params: pattern, path, ignore_globs, case_sensitive, max_results
        pattern = params.get('pattern', '')
        path = params.get('path', str(self.workspace_root))
        
        if not pattern:
            return ToolResult(False, {}, "No pattern provided")
        
        try:
            cmd = ['rg', '--json']
            if params.get('case_sensitive') is False:
                cmd.append('-i')
            if params.get('max_results'):
                cmd.extend(['-m', str(params['max_results'])])
            for glob in params.get('ignore_globs', []):
                cmd.extend(['--glob', f'!{glob}'])
            cmd.extend([pattern, path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return ToolResult(success=True, data={'output': result.stdout, 'matches': []})
        except Exception as e:
            return ToolResult(False, {}, str(e))
    
    # =========================================================================
    # Stub Implementations - TODO: Full implementation needed
    # Reference: TASK-26-tool-schemas.md for param/result schemas
    # Reference: TASK-110-tool-enum-mapping.md for tool descriptions
    # =========================================================================
    
    def _delete_file(self, params: Dict) -> ToolResult:
        """Delete file tool
        See TASK-26-tool-schemas.md DeleteFileParams/Result
        TODO: Implement with safety checks and user confirmation"""
        # Params: relative_workspace_path
        # Result: rejected, file_non_existent, file_deleted_successfully
        path = params.get('relative_workspace_path', '')
        full_path = self.workspace_root / path
        
        if not full_path.exists():
            return ToolResult(success=True, data={'file_non_existent': True, 'file_deleted_successfully': False})
        
        # TODO: Add confirmation mechanism - for now, actually delete
        try:
            full_path.unlink()
            return ToolResult(success=True, data={'file_deleted_successfully': True})
        except Exception as e:
            return ToolResult(False, {}, str(e))
    
    def _reapply(self, params: Dict) -> ToolResult:
        """Re-apply previous edit
        See TASK-26-tool-schemas.md ReapplyParams/Result
        TODO: Track edit history for reapplication"""
        # Params: (none documented)
        # Result: (success indicator)
        return ToolResult(False, {}, "TODO: Reapply requires edit history tracking. See TASK-26-tool-schemas.md")
    
    def _semantic_search_full(self, params: Dict) -> ToolResult:
        """Full semantic search using embeddings
        See TASK-26-tool-schemas.md SemanticSearchFullParams/Result
        TODO: Requires embedding model integration"""
        # Params: query, include_pattern, exclude_pattern, top_k
        # Result: code_results, all_files, missing_files, knowledge_results
        query = params.get('query', '')
        return ToolResult(False, {}, f"TODO: Semantic search requires embeddings. Query: {query}. See TASK-26-tool-schemas.md")
    
    def _read_semsearch_files(self, params: Dict) -> ToolResult:
        """Read semantically searched files
        See TASK-26-tool-schemas.md ReadSemsearchFilesParams/Result
        TODO: Integrate with semantic search results"""
        return ToolResult(False, {}, "TODO: Requires semantic search integration. See TASK-26-tool-schemas.md")
    
    def _fetch_rules(self, params: Dict) -> ToolResult:
        """Fetch cursor rules from .cursorrules files
        See TASK-26-tool-schemas.md FetchRulesParams/Result
        TODO: Parse .cursorrules and cursor.rules files"""
        # Look for .cursorrules in workspace
        rules_files = ['.cursorrules', 'cursor.rules', '.cursor/rules']
        rules_content = []
        
        for rf in rules_files:
            rules_path = self.workspace_root / rf
            if rules_path.exists():
                try:
                    rules_content.append(rules_path.read_text())
                except:
                    pass
        
        return ToolResult(success=True, data={'rules': rules_content, 'count': len(rules_content)})
    
    def _web_search(self, params: Dict) -> ToolResult:
        """Web search tool
        See TASK-26-tool-schemas.md WebSearchParams/Result
        TODO: Integrate with external search API (Exa, Tavily, etc.)
        See TASK-104-exa-tools.md for Exa integration details"""
        # Params: search_term
        # Result: references [{title, url, chunk}], is_final, rejected
        search_term = params.get('search_term', '')
        return ToolResult(False, {}, f"TODO: Web search requires API integration. Query: {search_term}. See TASK-104-exa-tools.md")
    
    def _mcp(self, params: Dict) -> ToolResult:
        """Legacy MCP tool call
        See TASK-27-mcp-tool-schemas.md for MCP protocol details
        TODO: Implement MCP client connection"""
        # Params: tools [{name, description, parameters, server_name}]
        # Result: selected_tool, result
        return ToolResult(False, {}, "TODO: MCP requires protocol implementation. See TASK-27-mcp-tool-schemas.md")
    
    def _search_symbols(self, params: Dict) -> ToolResult:
        """Search code symbols (functions, classes, etc.)
        See TASK-26-tool-schemas.md SearchSymbolsParams/Result
        TODO: Integrate with LSP or ctags for symbol extraction"""
        # Params: query
        # Result: matches [{name, uri, range, secondary_text, score}]
        query = params.get('query', '')
        
        # Basic implementation using ripgrep for function/class definitions
        try:
            # Search for common definition patterns
            pattern = f'(def |class |function |const |let |var |interface |type ){query}'
            cmd = ['rg', '-n', '--json', '-m', '20', pattern, str(self.workspace_root)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            matches = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get('type') == 'match':
                        match_data = data.get('data', {})
                        matches.append({
                            'name': query,
                            'uri': match_data.get('path', {}).get('text', ''),
                            'line_number': match_data.get('line_number', 0),
                        })
                except:
                    pass
            
            return ToolResult(success=True, data={'matches': matches})
        except Exception as e:
            return ToolResult(False, {}, str(e))
    
    def _go_to_definition(self, params: Dict) -> ToolResult:
        """Go to symbol definition
        See TASK-26-tool-schemas.md GotodefParams/Result
        TODO: Integrate with LSP for accurate go-to-definition"""
        # Params: uri, position
        # Result: definitions [{uri, range}]
        return ToolResult(False, {}, "TODO: Go-to-definition requires LSP integration. See TASK-26-tool-schemas.md")
    
    def _background_composer_followup(self, params: Dict) -> ToolResult:
        """Followup with background agent
        See TASK-26-tool-schemas.md BackgroundComposerFollowupParams/Result
        TODO: Implement background agent communication"""
        return ToolResult(False, {}, "TODO: Background composer requires agent orchestration. See TASK-26-tool-schemas.md")
    
    def _knowledge_base(self, params: Dict) -> ToolResult:
        """Query knowledge base
        See TASK-26-tool-schemas.md KnowledgeBaseParams/Result
        TODO: Implement knowledge base integration"""
        return ToolResult(False, {}, "TODO: Knowledge base not implemented. See TASK-26-tool-schemas.md")
    
    def _fetch_pull_request(self, params: Dict) -> ToolResult:
        """Fetch PR information from GitHub/GitLab
        See TASK-26-tool-schemas.md FetchPullRequestParams/Result
        TODO: Integrate with GitHub/GitLab APIs"""
        # Params: pr_url or pr_number
        return ToolResult(False, {}, "TODO: Fetch PR requires git provider API. See TASK-26-tool-schemas.md")
    
    def _deep_search(self, params: Dict) -> ToolResult:
        """Deep codebase search
        See TASK-26-tool-schemas.md DeepSearchParams/Result
        TODO: Implement multi-pass deep search with semantic understanding"""
        query = params.get('query', '')
        return ToolResult(False, {}, f"TODO: Deep search requires semantic + structural analysis. Query: {query}")
    
    def _create_diagram(self, params: Dict) -> ToolResult:
        """Create Mermaid diagram
        See TASK-26-tool-schemas.md CreateDiagramParams/Result
        TODO: Generate Mermaid syntax from code analysis"""
        # Result: diagram_content (Mermaid syntax)
        return ToolResult(False, {}, "TODO: Diagram creation requires code structure analysis. See TASK-26-tool-schemas.md")
    
    def _fix_lints(self, params: Dict) -> ToolResult:
        """Auto-fix lint errors
        See TASK-26-tool-schemas.md FixLintsParams/Result
        TODO: Integrate with linters (ESLint, Pylint, etc.)"""
        return ToolResult(False, {}, "TODO: Fix lints requires linter integration. See TASK-26-tool-schemas.md")
    
    def _read_lints(self, params: Dict) -> ToolResult:
        """Read lint errors for current file/workspace
        See TASK-26-tool-schemas.md ReadLintsParams/Result
        TODO: Run linters and parse output"""
        return ToolResult(False, {}, "TODO: Read lints requires linter integration. See TASK-26-tool-schemas.md")
    
    def _task(self, params: Dict) -> ToolResult:
        """Create subagent task
        See TASK-26-tool-schemas.md TaskParams/Result
        TODO: Spawn subagent for parallel task execution"""
        # Params: task_description, task_title, async, allowed_write_directories
        # Result: CompletedTaskResult or AsyncTaskResult
        description = params.get('task_description', '')
        return ToolResult(False, {}, f"TODO: Task requires subagent spawning. Task: {description}")
    
    def _await_task(self, params: Dict) -> ToolResult:
        """Wait for task completion
        See TASK-26-tool-schemas.md AwaitTaskParams/Result
        TODO: Implement task tracking and await mechanism"""
        task_id = params.get('task_id', '')
        return ToolResult(False, {}, f"TODO: Await task requires task tracking. Task ID: {task_id}")
    
    def _todo_read(self, params: Dict) -> ToolResult:
        """Read current todo list
        See TASK-26-tool-schemas.md TodoReadParams/Result"""
        # For now, return empty todo list
        # TODO: Implement persistent todo storage
        return ToolResult(success=True, data={'todos': []})
    
    def _todo_write(self, params: Dict) -> ToolResult:
        """Write/update todo list
        See TASK-26-tool-schemas.md TodoWriteParams/Result"""
        # Params: todos [{content, status, id, dependencies}], merge
        # Result: success, ready_task_ids, final_todos
        # TODO: Implement persistent todo storage
        todos = params.get('todos', [])
        return ToolResult(success=True, data={
            'success': True,
            'final_todos': todos,
            'was_merge': params.get('merge', False),
        })
    
    def _create_plan(self, params: Dict) -> ToolResult:
        """Create execution plan
        See TASK-26-tool-schemas.md CreatePlanParams/Result
        TODO: Generate structured execution plan"""
        return ToolResult(False, {}, "TODO: Plan creation requires planning engine. See TASK-26-tool-schemas.md")
    
    def _list_mcp_resources(self, params: Dict) -> ToolResult:
        """List available MCP resources
        See TASK-27-mcp-tool-schemas.md
        TODO: Query MCP servers for available resources"""
        return ToolResult(False, {}, "TODO: MCP resource listing requires MCP client. See TASK-27-mcp-tool-schemas.md")
    
    def _read_mcp_resource(self, params: Dict) -> ToolResult:
        """Read specific MCP resource
        See TASK-27-mcp-tool-schemas.md
        TODO: Fetch resource from MCP server"""
        uri = params.get('uri', '')
        return ToolResult(False, {}, f"TODO: MCP resource read requires MCP client. URI: {uri}")
    
    def _read_project(self, params: Dict) -> ToolResult:
        """Read project configuration
        See TASK-26-tool-schemas.md ReadProjectParams/Result
        TODO: Parse project config files (package.json, pyproject.toml, etc.)"""
        # Try to read common project files
        project_files = ['package.json', 'pyproject.toml', 'Cargo.toml', 'go.mod']
        project_info = {}
        
        for pf in project_files:
            path = self.workspace_root / pf
            if path.exists():
                try:
                    project_info[pf] = path.read_text()[:1000]  # First 1000 chars
                except:
                    pass
        
        return ToolResult(success=True, data={'project_files': project_info})
    
    def _update_project(self, params: Dict) -> ToolResult:
        """Update project configuration
        See TASK-26-tool-schemas.md UpdateProjectParams/Result
        TODO: Implement project config updates"""
        return ToolResult(False, {}, "TODO: Project update requires config modification. See TASK-26-tool-schemas.md")
    
    def _task_v2(self, params: Dict) -> ToolResult:
        """Create task V2 - improved subagent spawning
        See TASK-26-tool-schemas.md TaskV2Params/Result
        TODO: Implement V2 task creation with subagent_type"""
        # Params: description, prompt, subagent_type, model
        # Result: agent_id, is_background
        description = params.get('description', '')
        return ToolResult(False, {}, f"TODO: Task V2 requires subagent orchestration. Task: {description}")
    
    def _call_mcp_tool(self, params: Dict) -> ToolResult:
        """Call MCP tool (new API)
        See TASK-27-mcp-tool-schemas.md
        TODO: Implement MCP tool invocation"""
        tool_name = params.get('tool_name', '')
        server_name = params.get('server_name', '')
        return ToolResult(False, {}, f"TODO: MCP tool call requires MCP client. Tool: {tool_name}@{server_name}")
    
    def _apply_agent_diff(self, params: Dict) -> ToolResult:
        """Apply agent-generated diff
        See TASK-26-tool-schemas.md ApplyAgentDiffParams/Result
        TODO: Parse and apply unified diff format"""
        return ToolResult(False, {}, "TODO: Agent diff requires diff parsing/application. See TASK-26-tool-schemas.md")
    
    def _ask_question(self, params: Dict) -> ToolResult:
        """Ask user a question (interactive)
        See TASK-26-tool-schemas.md AskQuestionParams/Result
        TODO: Implement user interaction mechanism"""
        question = params.get('question', '')
        # In CLI context, we could prompt stdin
        return ToolResult(success=True, data={'answer': f'[User interaction not implemented. Question: {question}]'})
    
    def _switch_mode(self, params: Dict) -> ToolResult:
        """Switch agent mode
        See TASK-26-tool-schemas.md SwitchModeParams/Result
        TODO: Implement mode switching logic"""
        target_mode = params.get('target_mode', '')
        return ToolResult(False, {}, f"TODO: Mode switching requires mode manager. Target: {target_mode}")
    
    def _generate_image(self, params: Dict) -> ToolResult:
        """Generate image
        See TASK-26-tool-schemas.md GenerateImageArgs/Result
        TODO: Integrate with image generation API"""
        prompt = params.get('prompt', '')
        return ToolResult(False, {}, f"TODO: Image generation requires API. Prompt: {prompt}")
    
    def _computer_use(self, params: Dict) -> ToolResult:
        """Computer automation (mouse/keyboard control)
        See TASK-26-tool-schemas.md ComputerUseParams/Result
        TODO: Implement computer automation (security-sensitive)"""
        # Params: actions [{type, coordinates, text, key}]
        return ToolResult(False, {}, "TODO: Computer use requires automation framework. See TASK-26-tool-schemas.md")
    
    def _write_shell_stdin(self, params: Dict) -> ToolResult:
        """Write to shell stdin
        See TASK-26-tool-schemas.md WriteShellStdinParams/Result
        TODO: Implement stdin writing for interactive shells"""
        # Params: terminal_instance_id, content
        content = params.get('content', '')
        return ToolResult(False, {}, f"TODO: Shell stdin requires terminal tracking. Content: {content[:50]}...")


class CursorAgentClient:
    """Cursor Agent Client with tool calling support"""
    
    # Default tools to support in agent mode
    DEFAULT_TOOLS = [
        ClientSideToolV2.READ_FILE,
        ClientSideToolV2.LIST_DIR,
        ClientSideToolV2.RIPGREP_SEARCH,
        ClientSideToolV2.RUN_TERMINAL_COMMAND_V2,
        ClientSideToolV2.EDIT_FILE,
        ClientSideToolV2.FILE_SEARCH,
        ClientSideToolV2.GLOB_FILE_SEARCH,
    ]
    
    def __init__(self, workspace_root: str = "."):
        self.auth_reader = CursorAuthReader()
        self.token = self.auth_reader.get_bearer_token()
        self.base_url = "https://api2.cursor.sh"
        self.tool_executor = ToolExecutor(workspace_root)
        self.workspace_root = Path(workspace_root).resolve()
        
    def generate_hashed_64_hex(self, input_str: str, salt: str = '') -> str:
        """Generate SHA-256 hash"""
        hash_obj = hashlib.sha256()
        hash_obj.update((input_str + salt).encode('utf-8'))
        return hash_obj.hexdigest()
    
    def generate_session_id(self, auth_token: str) -> str:
        """Generate session ID using UUID v5"""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, auth_token))
    
    def get_machine_id(self) -> Optional[str]:
        """Get machine ID from Cursor storage"""
        import sqlite3
        db_path = self.auth_reader.storage_path
        if not db_path:
            return None
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM ItemTable WHERE key = 'storage.serviceMachineId'")
            row = cursor.fetchone()
            conn.close()
            if row:
                val = row[0]
                if isinstance(val, bytes):
                    val = val.decode('utf-8')
                return val
        except:
            pass
        return None
    
    def generate_cursor_checksum(self, token: str) -> str:
        """Generate checksum (Jyh cipher)"""
        machine_id = self.get_machine_id()
        if not machine_id:
            machine_id = self.generate_hashed_64_hex(token, 'machineId')
        
        timestamp = int(time.time() * 1000 // 1000000)
        
        byte_array = bytearray([
            (timestamp >> 40) & 255,
            (timestamp >> 32) & 255,
            (timestamp >> 24) & 255,
            (timestamp >> 16) & 255,
            (timestamp >> 8) & 255,
            timestamp & 255,
        ])
        
        # Obfuscate (Jyh cipher)
        t = 165
        for i in range(len(byte_array)):
            byte_array[i] = ((byte_array[i] ^ t) + (i % 256)) & 255
            t = byte_array[i]
        
        # URL-safe base64
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        encoded = ""
        for i in range(0, len(byte_array), 3):
            a = byte_array[i]
            b = byte_array[i + 1] if i + 1 < len(byte_array) else 0
            c = byte_array[i + 2] if i + 2 < len(byte_array) else 0
            encoded += alphabet[a >> 2]
            encoded += alphabet[((a & 3) << 4) | (b >> 4)]
            if i + 1 < len(byte_array):
                encoded += alphabet[((b & 15) << 2) | (c >> 6)]
            if i + 2 < len(byte_array):
                encoded += alphabet[c & 63]
        
        return f"{encoded}{machine_id}"
    
    def encode_message(self, content: str, role: int, message_id: str, chat_mode_enum: int = None) -> bytes:
        """Encode a conversation message"""
        msg = b''
        msg += ProtobufEncoder.encode_field(1, 2, content)
        msg += ProtobufEncoder.encode_field(2, 0, role)
        msg += ProtobufEncoder.encode_field(13, 2, message_id)
        if chat_mode_enum is not None:
            msg += ProtobufEncoder.encode_field(47, 0, chat_mode_enum)
        return msg
    
    def encode_instruction(self, instruction_text: str) -> bytes:
        """Encode instruction"""
        msg = b''
        if instruction_text:
            msg += ProtobufEncoder.encode_field(1, 2, instruction_text)
        return msg
    
    def encode_model(self, model_name: str) -> bytes:
        """Encode model"""
        msg = b''
        msg += ProtobufEncoder.encode_field(1, 2, model_name)
        msg += ProtobufEncoder.encode_field(4, 2, b'')
        return msg
    
    def encode_cursor_setting(self) -> bytes:
        """Encode CursorSetting"""
        msg = b''
        msg += ProtobufEncoder.encode_field(1, 2, "cursor\\aisettings")
        msg += ProtobufEncoder.encode_field(3, 2, b'')
        unknown6_msg = b''
        unknown6_msg += ProtobufEncoder.encode_field(1, 2, b'')
        unknown6_msg += ProtobufEncoder.encode_field(2, 2, b'')
        msg += ProtobufEncoder.encode_field(6, 2, unknown6_msg)
        msg += ProtobufEncoder.encode_field(8, 0, 1)
        msg += ProtobufEncoder.encode_field(9, 0, 1)
        return msg
    
    def encode_metadata(self) -> bytes:
        """Encode Metadata"""
        msg = b''
        msg += ProtobufEncoder.encode_field(1, 2, "linux")
        msg += ProtobufEncoder.encode_field(2, 2, "x64")
        msg += ProtobufEncoder.encode_field(3, 2, "6.13.0")
        msg += ProtobufEncoder.encode_field(4, 2, "/usr/bin/python3")
        from datetime import datetime
        msg += ProtobufEncoder.encode_field(5, 2, datetime.now().isoformat())
        return msg
    
    def encode_message_id(self, message_id: str, role: int, summary_id: str = None) -> bytes:
        """Encode MessageId"""
        msg = b''
        msg += ProtobufEncoder.encode_field(1, 2, message_id)
        if summary_id:
            msg += ProtobufEncoder.encode_field(2, 2, summary_id)
        msg += ProtobufEncoder.encode_field(3, 0, role)
        return msg
    
    def encode_agent_request(self, messages: List[Dict], model_name: str, 
                            supported_tools: List[int] = None) -> bytes:
        """Encode Agent mode request with supported_tools"""
        if supported_tools is None:
            supported_tools = self.DEFAULT_TOOLS
        
        msg = b''
        
        # Format messages
        formatted_messages = []
        message_ids = []
        
        for user_msg in messages:
            if user_msg['role'] == 'user':
                msg_id = str(uuid.uuid4())
                formatted_messages.append({
                    'content': user_msg['content'],
                    'role': 1,  # user
                    'messageId': msg_id,
                    'chatModeEnum': 2  # Agent mode
                })
                message_ids.append({
                    'messageId': msg_id,
                    'role': 1
                })
        
        # repeated Message messages = 1;
        for formatted_msg in formatted_messages:
            message_bytes = self.encode_message(
                formatted_msg['content'],
                formatted_msg['role'],
                formatted_msg['messageId'],
                formatted_msg.get('chatModeEnum')
            )
            msg += ProtobufEncoder.encode_field(1, 2, message_bytes)
        
        # int32 unknown2 = 2; // 1
        msg += ProtobufEncoder.encode_field(2, 0, 1)
        
        # Instruction instruction = 3;
        instruction_bytes = self.encode_instruction("")
        msg += ProtobufEncoder.encode_field(3, 2, instruction_bytes)
        
        # int32 unknown4 = 4; // 1
        msg += ProtobufEncoder.encode_field(4, 0, 1)
        
        # Model model = 5;
        model_bytes = self.encode_model(model_name)
        msg += ProtobufEncoder.encode_field(5, 2, model_bytes)
        
        # string webTool = 8;
        msg += ProtobufEncoder.encode_field(8, 2, "")
        
        # int32 unknown13 = 13;
        msg += ProtobufEncoder.encode_field(13, 0, 1)
        
        # CursorSetting cursorSetting = 15;
        cursor_setting_bytes = self.encode_cursor_setting()
        msg += ProtobufEncoder.encode_field(15, 2, cursor_setting_bytes)
        
        # int32 unknown19 = 19; // 1
        msg += ProtobufEncoder.encode_field(19, 0, 1)
        
        # string conversationId = 23;
        msg += ProtobufEncoder.encode_field(23, 2, str(uuid.uuid4()))
        
        # Metadata metadata = 26;
        metadata_bytes = self.encode_metadata()
        msg += ProtobufEncoder.encode_field(26, 2, metadata_bytes)
        
        # bool is_agentic = 27; (field 27 in StreamUnifiedChatRequest)
        msg += ProtobufEncoder.encode_field(27, 0, 1)  # true
        
        # repeated ClientSideToolV2 supported_tools = 29;
        for tool in supported_tools:
            msg += ProtobufEncoder.encode_field(29, 0, tool)
        
        # repeated MessageId messageIds = 30;
        for msg_id_data in message_ids:
            message_id_bytes = self.encode_message_id(
                msg_id_data['messageId'],
                msg_id_data['role']
            )
            msg += ProtobufEncoder.encode_field(30, 2, message_id_bytes)
        
        # int32 largeContext = 35; // 0
        msg += ProtobufEncoder.encode_field(35, 0, 0)
        
        # int32 unknown38 = 38; // 0
        msg += ProtobufEncoder.encode_field(38, 0, 0)
        
        # int32 chatModeEnum = 46; // 2 for Agent mode
        msg += ProtobufEncoder.encode_field(46, 0, 2)
        
        # string unknown47 = 47;
        msg += ProtobufEncoder.encode_field(47, 2, "")
        
        # int32 unknown48 = 48; // 0
        msg += ProtobufEncoder.encode_field(48, 0, 0)
        
        # int32 unknown49 = 49; // 0
        msg += ProtobufEncoder.encode_field(49, 0, 0)
        
        # int32 unknown51 = 51; // 0
        msg += ProtobufEncoder.encode_field(51, 0, 0)
        
        # int32 unknown53 = 53; // 1
        msg += ProtobufEncoder.encode_field(53, 0, 1)
        
        # string chatMode = 54; // "agent"
        msg += ProtobufEncoder.encode_field(54, 2, "agent")
        
        return msg
    
    def encode_stream_unified_chat_request(self, messages: List[Dict], model_name: str) -> bytes:
        """Encode StreamUnifiedChatWithToolsRequest for agent mode"""
        msg = b''
        
        # Request request = 1;
        request_bytes = self.encode_agent_request(messages, model_name)
        msg += ProtobufEncoder.encode_field(1, 2, request_bytes)
        
        return msg
    
    def encode_tool_result(self, tool: int, tool_call_id: str, result: ToolResult) -> bytes:
        """Encode ClientSideToolV2Result"""
        msg = b''
        
        # ClientSideToolV2 tool = 1;
        msg += ProtobufEncoder.encode_field(1, 0, tool)
        
        # string tool_call_id = 35;
        msg += ProtobufEncoder.encode_field(35, 2, tool_call_id)
        
        if result.success:
            # Encode result based on tool type
            result_bytes = self._encode_tool_specific_result(tool, result.data)
            if result_bytes:
                # The field number depends on the tool type
                field_num = self._get_result_field_number(tool)
                msg += ProtobufEncoder.encode_field(field_num, 2, result_bytes)
        else:
            # ToolResultError error = 8;
            error_bytes = ProtobufEncoder.encode_field(1, 2, result.error or "Unknown error")
            msg += ProtobufEncoder.encode_field(8, 2, error_bytes)
        
        return msg
    
    def _encode_tool_specific_result(self, tool: int, data: Dict) -> bytes:
        """Encode tool-specific result data"""
        msg = b''
        
        if tool == ClientSideToolV2.READ_FILE:
            # ReadFileResult
            if 'contents' in data:
                msg += ProtobufEncoder.encode_field(1, 2, data['contents'])
            if 'relative_workspace_path' in data:
                msg += ProtobufEncoder.encode_field(9, 2, data['relative_workspace_path'])
            if 'total_lines' in data:
                msg += ProtobufEncoder.encode_field(12, 0, data['total_lines'])
                
        elif tool == ClientSideToolV2.LIST_DIR:
            # ListDirResult: repeated File files = 1; string directory_relative_workspace_path = 2;
            entries = data.get('entries', [])
            for entry in entries:
                # File message: name=1(string), is_directory=2(bool), size=3(int64)
                file_msg = b''
                file_msg += ProtobufEncoder.encode_field(1, 2, entry.get('name', ''))
                file_msg += ProtobufEncoder.encode_field(2, 0, 1 if entry.get('is_directory') else 0)
                if entry.get('size'):
                    file_msg += ProtobufEncoder.encode_field(3, 0, entry['size'])
                msg += ProtobufEncoder.encode_field(1, 2, file_msg)
            # directory_relative_workspace_path = 2
            if 'directory_path' in data:
                msg += ProtobufEncoder.encode_field(2, 2, data['directory_path'])
            
        elif tool == ClientSideToolV2.RIPGREP_SEARCH:
            # RipgrepSearchResult: internal=1(RipgrepSearchResultInternal)
            # RipgrepSearchResultInternal: results=1(repeated IFileMatch), exit=2(enum)
            # IFileMatch: resource=1(string), results=2(repeated ITextSearchResult)
            # ITextSearchResult: match=1(ITextSearchMatch oneof)
            # ITextSearchMatch: range_locations=2(repeated), preview_text=3(string)
            internal_msg = b''
            
            # Group matches by file path
            matches = data.get('matches', [])
            files_dict = {}
            for match in matches:
                if isinstance(match, dict):
                    path = match.get('path', '')
                    if path:
                        if path not in files_dict:
                            files_dict[path] = []
                        files_dict[path].append(match)
            
            # Encode each file's matches as IFileMatch
            for file_path, file_matches in files_dict.items():
                file_match_msg = b''
                # resource = 1 (file path)
                file_match_msg += ProtobufEncoder.encode_field(1, 2, file_path)
                
                # results = 2 (repeated ITextSearchResult)
                for match in file_matches:
                    line_content = match.get('line_content', '')
                    line_number = match.get('line_number', 0)
                    
                    # ITextSearchMatch: preview_text=3
                    text_search_match = b''
                    text_search_match += ProtobufEncoder.encode_field(3, 2, line_content)
                    
                    # Optionally add range_locations for line number
                    if line_number:
                        # ISearchRangeSetPairing: source=1(Range)
                        # Range: startLineNumber=1, startColumn=2, endLineNumber=3, endColumn=4
                        range_msg = b''
                        range_msg += ProtobufEncoder.encode_field(1, 0, line_number)  # startLineNumber
                        range_msg += ProtobufEncoder.encode_field(2, 0, 1)  # startColumn
                        range_msg += ProtobufEncoder.encode_field(3, 0, line_number)  # endLineNumber
                        range_msg += ProtobufEncoder.encode_field(4, 0, len(line_content) + 1)  # endColumn
                        pairing = ProtobufEncoder.encode_field(1, 2, range_msg)  # source
                        text_search_match += ProtobufEncoder.encode_field(2, 2, pairing)
                    
                    # ITextSearchResult: match=1 (oneof field)
                    text_search_result = ProtobufEncoder.encode_field(1, 2, text_search_match)
                    file_match_msg += ProtobufEncoder.encode_field(2, 2, text_search_result)
                
                internal_msg += ProtobufEncoder.encode_field(1, 2, file_match_msg)
            
            # exit = NORMAL (1)
            internal_msg += ProtobufEncoder.encode_field(2, 0, 1)
            
            # Wrap in RipgrepSearchResult.internal
            msg += ProtobufEncoder.encode_field(1, 2, internal_msg)
            
        elif tool == ClientSideToolV2.RUN_TERMINAL_COMMAND_V2:
            # RunTerminalCommandV2Result: output=1(string), exit_code=2(int32), rejected=3(bool)
            # Combine stdout and stderr into output
            output = data.get('stdout', '') or data.get('output', '')
            if data.get('stderr'):
                output += '\n' + data['stderr']
            if output:
                msg += ProtobufEncoder.encode_field(1, 2, output)
            if 'exit_code' in data:
                msg += ProtobufEncoder.encode_field(2, 0, data['exit_code'])
                
        elif tool == ClientSideToolV2.EDIT_FILE:
            # EditFileResult: is_applied=2(bool)
            if data.get('is_applied'):
                msg += ProtobufEncoder.encode_field(2, 0, 1)  # is_applied = true
        
        elif tool == ClientSideToolV2.FILE_SEARCH:
            # ToolCallFileSearchResult: files=1(repeated File), limit_hit=2(bool), num_results=3(int32)
            # File: uri=1(string)
            files = data.get('files', [])
            for f in files:
                file_msg = ProtobufEncoder.encode_field(1, 2, f.get('uri', ''))
                msg += ProtobufEncoder.encode_field(1, 2, file_msg)
            if data.get('limit_hit'):
                msg += ProtobufEncoder.encode_field(2, 0, 1)
            msg += ProtobufEncoder.encode_field(3, 0, data.get('num_results', len(files)))
        
        elif tool == ClientSideToolV2.GLOB_FILE_SEARCH:
            # GlobFileSearchResult - same structure as FileSearchResult
            files = data.get('files', [])
            for f in files:
                file_msg = ProtobufEncoder.encode_field(1, 2, f.get('uri', ''))
                msg += ProtobufEncoder.encode_field(1, 2, file_msg)
            if data.get('limit_hit'):
                msg += ProtobufEncoder.encode_field(2, 0, 1)
            msg += ProtobufEncoder.encode_field(3, 0, data.get('num_results', len(files)))
        
        return msg
    
    def _get_result_field_number(self, tool: int) -> int:
        """Get the field number for tool result in ClientSideToolV2Result
        Based on TASK-26-tool-schemas.md ClientSideToolV2Result oneof result {}"""
        result_field_map = {
            # Core file operations
            ClientSideToolV2.READ_SEMSEARCH_FILES: 2,     # read_semsearch_files_result
            ClientSideToolV2.RIPGREP_SEARCH: 4,           # ripgrep_search_result
            ClientSideToolV2.READ_FILE: 6,                # read_file_result
            ClientSideToolV2.LIST_DIR: 9,                 # list_dir_result
            ClientSideToolV2.EDIT_FILE: 10,               # edit_file_result
            ClientSideToolV2.FILE_SEARCH: 11,             # file_search_result
            ClientSideToolV2.SEMANTIC_SEARCH_FULL: 18,    # semantic_search_full_result
            ClientSideToolV2.DELETE_FILE: 20,             # delete_file_result
            ClientSideToolV2.REAPPLY: 21,                 # reapply_result
            ClientSideToolV2.RUN_TERMINAL_COMMAND_V2: 24, # run_terminal_command_v2_result
            ClientSideToolV2.FETCH_RULES: 25,             # fetch_rules_result
            ClientSideToolV2.WEB_SEARCH: 27,              # web_search_result
            ClientSideToolV2.MCP: 28,                     # mcp_result
            ClientSideToolV2.SEARCH_SYMBOLS: 32,          # search_symbols_result
            ClientSideToolV2.BACKGROUND_COMPOSER_FOLLOWUP: 33,  # background_composer_followup_result
            ClientSideToolV2.KNOWLEDGE_BASE: 34,          # knowledge_base_result
            ClientSideToolV2.FETCH_PULL_REQUEST: 36,      # fetch_pull_request_result
            ClientSideToolV2.DEEP_SEARCH: 37,             # deep_search_result
            ClientSideToolV2.CREATE_DIAGRAM: 38,          # create_diagram_result
            ClientSideToolV2.FIX_LINTS: 39,               # fix_lints_result
            ClientSideToolV2.READ_LINTS: 40,              # read_lints_result
            ClientSideToolV2.GO_TO_DEFINITION: 41,        # gotodef_result
            ClientSideToolV2.TASK: 42,                    # task_result
            ClientSideToolV2.AWAIT_TASK: 43,              # await_task_result
            ClientSideToolV2.TODO_READ: 44,               # todo_read_result
            ClientSideToolV2.TODO_WRITE: 45,              # todo_write_result
            # V2 versions
            ClientSideToolV2.EDIT_FILE_V2: 51,            # edit_file_v2_result
            ClientSideToolV2.LIST_DIR_V2: 52,             # list_dir_v2_result
            ClientSideToolV2.READ_FILE_V2: 53,            # read_file_v2_result
            ClientSideToolV2.RIPGREP_RAW_SEARCH: 54,      # ripgrep_raw_search_result
            ClientSideToolV2.GLOB_FILE_SEARCH: 55,        # glob_file_search_result
            ClientSideToolV2.CREATE_PLAN: 56,             # create_plan_result
            ClientSideToolV2.LIST_MCP_RESOURCES: 57,      # list_mcp_resources_result
            ClientSideToolV2.READ_MCP_RESOURCE: 58,       # read_mcp_resource_result
            ClientSideToolV2.READ_PROJECT: 59,            # read_project_result
            ClientSideToolV2.UPDATE_PROJECT: 60,          # update_project_result
            ClientSideToolV2.TASK_V2: 61,                 # task_v2_result
            ClientSideToolV2.CALL_MCP_TOOL: 62,           # call_mcp_tool_result
            ClientSideToolV2.APPLY_AGENT_DIFF: 63,        # apply_agent_diff_result
            ClientSideToolV2.ASK_QUESTION: 64,            # ask_question_result
            ClientSideToolV2.SWITCH_MODE: 65,             # switch_mode_result
            ClientSideToolV2.COMPUTER_USE: 66,            # computer_use_result
            ClientSideToolV2.GENERATE_IMAGE: 67,          # generate_image_result
            ClientSideToolV2.WRITE_SHELL_STDIN: 68,       # write_shell_stdin_result
        }
        return result_field_map.get(tool, 2)  # Default to field 2
    
    def generate_request_body(self, messages: List[Dict], model_name: str) -> bytes:
        """Generate request body with proper framing"""
        buffer = self.encode_stream_unified_chat_request(messages, model_name)
        
        magic_number = 0x00
        if len(messages) >= 3:
            buffer = gzip.compress(buffer)
            magic_number = 0x01
        
        length_hex = format(len(buffer), '08x')
        length_bytes = bytes.fromhex(length_hex)
        
        return bytes([magic_number]) + length_bytes + buffer
    
    def parse_tool_call_from_chunk(self, chunk: bytes) -> Optional[ToolCall]:
        """Parse tool call from response chunk"""
        try:
            text = chunk.decode('utf-8', errors='ignore')
            
            # Look for tool call patterns in the response
            # Pattern 1: JSON in text (magic byte 2 or 3)
            if chunk and len(chunk) > 5 and chunk[0] in (2, 3):
                try:
                    if chunk[0] == 3:
                        data = gzip.decompress(chunk[5:])
                    else:
                        data = chunk[5:]
                    json_data = json.loads(data.decode('utf-8'))
                    if 'tool' in json_data or 'name' in json_data:
                        return ToolCall(
                            tool=json_data.get('tool', 0),
                            tool_call_id=json_data.get('tool_call_id', ''),
                            name=json_data.get('name', ''),
                            raw_args=json_data.get('raw_args', ''),
                            params=json.loads(json_data.get('raw_args', '{}')) if json_data.get('raw_args') else {}
                        )
                except:
                    pass
            
            # Pattern 2: Look for tool markers in text
            # Tool calls often appear as: toolu_bdrk_... or similar IDs
            import re
            
            # Match tool call ID pattern
            tool_id_match = re.search(r'(toolu_[a-zA-Z0-9_]+)', text)
            if tool_id_match:
                tool_call_id = tool_id_match.group(1)
                
                # Try to find the tool name
                tool_name = None
                for name in ['list_dir', 'read_file', 'grep_search', 'edit_file', 'run_terminal_command']:
                    if name in text.lower():
                        tool_name = name
                        break
                
                if tool_name:
                    # Map name to enum - see TASK-110-tool-enum-mapping.md
                    name_to_enum = {
                        # Core file operations
                        'list_dir': ClientSideToolV2.LIST_DIR,
                        'read_file': ClientSideToolV2.READ_FILE,
                        'edit_file': ClientSideToolV2.EDIT_FILE,
                        'delete_file': ClientSideToolV2.DELETE_FILE,
                        'file_search': ClientSideToolV2.FILE_SEARCH,
                        'glob_file_search': ClientSideToolV2.GLOB_FILE_SEARCH,
                        # Search
                        'grep_search': ClientSideToolV2.RIPGREP_SEARCH,
                        'ripgrep_search': ClientSideToolV2.RIPGREP_SEARCH,
                        'codebase_search': ClientSideToolV2.SEMANTIC_SEARCH_FULL,
                        'search_symbols': ClientSideToolV2.SEARCH_SYMBOLS,
                        'deep_search': ClientSideToolV2.DEEP_SEARCH,
                        # Terminal
                        'run_terminal_command': ClientSideToolV2.RUN_TERMINAL_COMMAND_V2,
                        'run_terminal_cmd': ClientSideToolV2.RUN_TERMINAL_COMMAND_V2,
                        # Web/external
                        'web_search': ClientSideToolV2.WEB_SEARCH,
                        'fetch_rules': ClientSideToolV2.FETCH_RULES,
                        'fetch_pull_request': ClientSideToolV2.FETCH_PULL_REQUEST,
                        # MCP
                        'mcp': ClientSideToolV2.MCP,
                        'call_mcp_tool': ClientSideToolV2.CALL_MCP_TOOL,
                        # Task/Agent
                        'task': ClientSideToolV2.TASK,
                        'todo_read': ClientSideToolV2.TODO_READ,
                        'todo_write': ClientSideToolV2.TODO_WRITE,
                        # Misc
                        'reapply': ClientSideToolV2.REAPPLY,
                        'go_to_definition': ClientSideToolV2.GO_TO_DEFINITION,
                        'gotodef': ClientSideToolV2.GO_TO_DEFINITION,
                        'create_diagram': ClientSideToolV2.CREATE_DIAGRAM,
                        'fix_lints': ClientSideToolV2.FIX_LINTS,
                        'read_lints': ClientSideToolV2.READ_LINTS,
                        # V2 versions
                        'list_dir_v2': ClientSideToolV2.LIST_DIR_V2,
                        'read_file_v2': ClientSideToolV2.READ_FILE_V2,
                        'edit_file_v2': ClientSideToolV2.EDIT_FILE_V2,
                    }
                    
                    # Try to extract JSON params
                    params = {}
                    json_match = re.search(r'\{[^{}]+\}', text)
                    if json_match:
                        try:
                            params = json.loads(json_match.group())
                        except:
                            pass
                    
                    return ToolCall(
                        tool=name_to_enum.get(tool_name, 0),
                        tool_call_id=tool_call_id,
                        name=tool_name,
                        raw_args=json_match.group() if json_match else '',
                        params=params
                    )
            
            return None
        except:
            return None
    
    def get_headers(self, auth_token: str, session_id: str, client_key: str, 
                   cursor_checksum: str) -> Dict[str, str]:
        """Get HTTP headers for requests"""
        return {
            'authorization': f'Bearer {auth_token}',
            'connect-accept-encoding': 'gzip',
            'connect-protocol-version': '1',
            'content-type': 'application/connect+proto',
            'user-agent': 'connect-es/1.6.1',
            'x-amzn-trace-id': f'Root={uuid.uuid4()}',
            'x-client-key': client_key,
            'x-cursor-checksum': cursor_checksum,
            'x-cursor-client-version': '2.3.41',
            'x-cursor-client-type': 'ide',
            'x-cursor-client-os': 'linux',
            'x-cursor-client-arch': 'x64',
            'x-cursor-client-device-type': 'desktop',
            'x-cursor-config-version': str(uuid.uuid4()),
            'x-cursor-timezone': 'Europe/Copenhagen',
            'x-ghost-mode': 'true',
            'x-request-id': str(uuid.uuid4()),
            'x-session-id': session_id,
            'Host': 'api2.cursor.sh'
        }
    
    def encode_tool_result_request(self, tool: int, tool_call_id: str, result: ToolResult) -> bytes:
        """Encode StreamUnifiedChatRequestWithTools with tool result (field 2)"""
        msg = b''
        
        # ClientSideToolV2Result client_side_tool_v2_result = 2;
        result_bytes = self.encode_tool_result(tool, tool_call_id, result)
        msg += ProtobufEncoder.encode_field(2, 2, result_bytes)
        
        return msg
    
    def frame_message(self, data: bytes, compress: bool = False) -> bytes:
        """Frame a message with magic byte and length"""
        if compress:
            data = gzip.compress(data)
            magic = 0x01
        else:
            magic = 0x00
        
        length_hex = format(len(data), '08x')
        length_bytes = bytes.fromhex(length_hex)
        
        return bytes([magic]) + length_bytes + data
    
    async def send_bidi_append(self, client: httpx.AsyncClient, request_id: str, 
                               seqno: int, data: bytes, headers: Dict[str, str],
                               verbose: bool = False) -> bool:
        """Send tool result via BidiAppend (SSE fallback)"""
        url = f"{self.base_url}/aiserver.v1.BidiService/BidiAppend"
        
        # Encode BidiAppendRequest
        msg = b''
        # string data = 1; (contains serialized StreamUnifiedChatRequestWithTools as JSON string)
        import base64
        # According to analysis: data is JSON string, not binary
        data_as_json = base64.b64encode(data).decode()  # For binary, base64 encode
        msg += ProtobufEncoder.encode_field(1, 2, data_as_json)
        # BidiRequestId request_id = 2;
        request_id_msg = ProtobufEncoder.encode_field(1, 2, request_id)
        msg += ProtobufEncoder.encode_field(2, 2, request_id_msg)
        # int64 append_seqno = 3;
        msg += ProtobufEncoder.encode_field(3, 0, seqno)
        
        framed = self.frame_message(msg)
        
        try:
            response = await client.post(url, headers=headers, content=framed)
            if verbose:
                print(f"[BidiAppend status: {response.status_code}]")
                if response.status_code != 200:
                    body = response.read()
                    print(f"[BidiAppend response: {body[:200]}]")
            return response.status_code == 200
        except Exception as e:
            if verbose:
                print(f"[BidiAppend error: {e}]")
            return False
    
    async def run_agent_loop(self, prompt: str, model: str = "claude-4-sonnet",
                            max_tool_calls: int = 10, verbose: bool = False) -> str:
        """Run agent using a conversation loop - new request for each tool result"""
        if not self.token:
            print("Error: No authentication token")
            return ""
        
        auth_token = self.token
        if '::' in auth_token:
            auth_token = auth_token.split('::')[1]
        
        session_id = self.generate_session_id(auth_token)
        client_key = self.generate_hashed_64_hex(auth_token)
        cursor_checksum = self.generate_cursor_checksum(auth_token)
        
        if verbose:
            print(f"Agent mode (loop) with model: {model}")
            print(f"Workspace: {self.workspace_root}")
            print("=" * 50)
        
        messages = [{"role": "user", "content": prompt}]
        conversation_id = str(uuid.uuid4())
        
        url = f"{self.base_url}/aiserver.v1.ChatService/StreamUnifiedChatWithTools"
        full_response = ""
        tool_calls_executed = 0
        
        async with httpx.AsyncClient(http2=True, timeout=120.0) as client:
            while tool_calls_executed < max_tool_calls:
                headers = self.get_headers(auth_token, session_id, client_key, cursor_checksum)
                headers['x-conversation-id'] = conversation_id
                
                cursor_body = self.generate_request_body(messages, model)
                
                if verbose and tool_calls_executed > 0:
                    print(f"\n[Continuing conversation with tool result...]")
                
                try:
                    pending_tool_call = None
                    turn_response = ""
                    
                    async with client.stream('POST', url, headers=headers, content=cursor_body) as response:
                        if verbose and tool_calls_executed == 0:
                            print(f"Status: {response.status_code}")
                        
                        if response.status_code != 200:
                            error = await response.aread()
                            print(f"Error: {error.decode('utf-8', errors='ignore')[:500]}")
                            break
                        
                        async for chunk in response.aiter_bytes():
                            # Extract text
                            try:
                                text = chunk.decode('utf-8', errors='ignore')
                                printable = ''.join(c for c in text if c.isprintable() or c in '\n\r\t')
                                if printable and len(printable) > 2:
                                    turn_response += printable
                                    print(printable, end='', flush=True)
                            except:
                                pass
                            
                            # Check for tool call
                            tool_call = self.parse_tool_call_from_chunk(chunk)
                            if tool_call:
                                pending_tool_call = tool_call
                    
                    full_response += turn_response
                    
                    # If there's a pending tool call, execute it and add result to messages
                    if pending_tool_call:
                        if verbose:
                            print(f"\n[Tool: {pending_tool_call.name}]")
                        
                        result = self.tool_executor.execute(pending_tool_call)
                        tool_calls_executed += 1
                        
                        if verbose:
                            status = 'success' if result.success else result.error
                            print(f"[Result: {status}]")
                        
                        # Add assistant message with tool call and user message with tool result
                        messages.append({
                            "role": "assistant",
                            "content": turn_response,
                            "tool_calls": [{
                                "id": pending_tool_call.tool_call_id,
                                "type": "function",
                                "function": {
                                    "name": pending_tool_call.name,
                                    "arguments": pending_tool_call.raw_args
                                }
                            }]
                        })
                        messages.append({
                            "role": "tool",
                            "tool_call_id": pending_tool_call.tool_call_id,
                            "content": json.dumps(result.data) if result.success else f"Error: {result.error}"
                        })
                    else:
                        # No tool call, we're done
                        break
                    
                except Exception as e:
                    print(f"Error: {e}")
                    import traceback
                    traceback.print_exc()
                    break
            
            print()
            return full_response
    
    async def run_agent(self, prompt: str, model: str = "claude-4-sonnet",
                       max_tool_calls: int = 10, verbose: bool = False,
                       execute_tools: bool = True) -> str:
        """Run agent with tool calling support
        
        Args:
            prompt: The user prompt
            model: Model name (default: claude-4-sonnet)
            max_tool_calls: Maximum tool calls to detect
            verbose: Print verbose output
            execute_tools: Execute detected tools locally (can't send results back yet)
        
        Note: httpx doesn't support true HTTP/2 bidirectional streaming,
        so tool results can't be sent back to the server on the same connection.
        Tools are executed locally for demonstration purposes.
        """
        if not self.token:
            print("Error: No authentication token")
            return ""
        
        auth_token = self.token
        if '::' in auth_token:
            auth_token = auth_token.split('::')[1]
        
        session_id = self.generate_session_id(auth_token)
        client_key = self.generate_hashed_64_hex(auth_token)
        cursor_checksum = self.generate_cursor_checksum(auth_token)
        
        if verbose:
            print(f"Agent mode with model: {model}")
            print(f"Workspace: {self.workspace_root}")
            print(f"Supported tools: {len(self.DEFAULT_TOOLS)}")
            print("=" * 50)
        
        messages = [{"role": "user", "content": prompt}]
        
        url = f"{self.base_url}/aiserver.v1.ChatService/StreamUnifiedChatWithTools"
        headers = self.get_headers(auth_token, session_id, client_key, cursor_checksum)
        
        cursor_body = self.generate_request_body(messages, model)
        
        full_response = ""
        tool_calls_detected = []
        tool_results = []
        
        async with httpx.AsyncClient(http2=True, timeout=120.0) as client:
            try:
                async with client.stream('POST', url, headers=headers, content=cursor_body) as response:
                    if verbose:
                        print(f"Status: {response.status_code}")
                    
                    if response.status_code != 200:
                        error = await response.aread()
                        print(f"Error: {error.decode('utf-8', errors='ignore')[:500]}")
                        return ""
                    
                    async for chunk in response.aiter_bytes():
                        try:
                            text = chunk.decode('utf-8', errors='ignore')
                            printable = ''.join(c for c in text if c.isprintable() or c in '\n\r\t')
                            if printable and len(printable) > 2:
                                full_response += printable
                                print(printable, end='', flush=True)
                        except:
                            pass
                        
                        # Detect tool calls
                        tool_call = self.parse_tool_call_from_chunk(chunk)
                        if tool_call and len(tool_calls_detected) < max_tool_calls:
                            # Skip if we already have this tool call
                            if any(tc.tool_call_id == tool_call.tool_call_id for tc in tool_calls_detected):
                                continue
                            
                            tool_calls_detected.append(tool_call)
                            
                            if execute_tools:
                                if verbose:
                                    print(f"\n[Tool: {tool_call.name} ({tool_call.tool_call_id[:16]}...)]")
                                
                                result = self.tool_executor.execute(tool_call)
                                tool_results.append((tool_call, result))
                                
                                if verbose:
                                    status = 'success' if result.success else f'error: {result.error}'
                                    print(f"[Local execution: {status}]")
                                    if result.success and result.data:
                                        # Show brief preview of result
                                        data_str = json.dumps(result.data, indent=2)[:200]
                                        print(f"[Result preview: {data_str}...]")
                
                print()
                
                if tool_calls_detected:
                    print(f"\n--- Tool Call Summary ---")
                    print(f"Detected {len(tool_calls_detected)} tool call(s)")
                    for i, (tc, res) in enumerate(tool_results, 1):
                        status = 'OK' if res.success else f'ERR: {res.error}'
                        print(f"  {i}. {tc.name}: {status}")
                    print(f"\nNote: Tool results executed locally (bidi streaming not supported)")
                
                return full_response
                
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
                return ""


async def main():
    import sys
    
    # Parse arguments
    model = "claude-4-sonnet"
    prompt = "List the files in the current directory"
    verbose = False
    max_tools = 10
    execute_tools = True
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '-m' and i + 1 < len(args):
            model = args[i + 1]
            i += 2
        elif args[i] == '-v':
            verbose = True
            i += 1
        elif args[i] == '-t' and i + 1 < len(args):
            max_tools = int(args[i + 1])
            i += 2
        elif args[i] == '--no-exec':
            execute_tools = False
            i += 1
        elif args[i] == '--help':
            print("Usage: cursor_agent_client.py [-m model] [-v] [-t N] [--no-exec] [prompt]")
            print("  -m model   Model to use (default: claude-4-sonnet)")
            print("  -v         Verbose output")
            print("  -t N       Maximum tool calls to detect (default: 10)")
            print("  --no-exec  Don't execute tools locally (detection only)")
            print("  prompt     The prompt to send (default: 'List files')")
            print()
            print("Note: This client demonstrates agent mode with tool detection.")
            print("Tool results are executed locally but can't be sent back to server")
            print("(requires true HTTP/2 bidi streaming which httpx doesn't support).")
            return
        else:
            prompt = args[i]
            i += 1
    
    client = CursorAgentClient(workspace_root=".")
    result = await client.run_agent(
        prompt, model=model, max_tool_calls=max_tools, 
        verbose=verbose, execute_tools=execute_tools
    )
    
    if not result:
        print("No response received")


if __name__ == "__main__":
    asyncio.run(main())
