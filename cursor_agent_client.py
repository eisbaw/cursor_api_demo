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


# ClientSideToolV2 enum values (from TASK-110)
class ClientSideToolV2:
    UNSPECIFIED = 0
    READ_SEMSEARCH_FILES = 1
    RIPGREP_SEARCH = 3
    READ_FILE = 5
    LIST_DIR = 6
    EDIT_FILE = 7
    FILE_SEARCH = 8
    SEMANTIC_SEARCH_FULL = 9
    DELETE_FILE = 11
    REAPPLY = 12
    RUN_TERMINAL_COMMAND_V2 = 15
    FETCH_RULES = 16
    WEB_SEARCH = 18
    MCP = 19
    SEARCH_SYMBOLS = 23
    GO_TO_DEFINITION = 31
    EDIT_FILE_V2 = 38
    LIST_DIR_V2 = 39
    READ_FILE_V2 = 40
    RIPGREP_RAW_SEARCH = 41
    GLOB_FILE_SEARCH = 42


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
            # ListDirResult - encode entries
            entries_str = json.dumps(data.get('entries', []))
            msg += ProtobufEncoder.encode_field(1, 2, entries_str)
            
        elif tool == ClientSideToolV2.RIPGREP_SEARCH:
            # RipgrepSearchResult - encode matches
            matches_str = json.dumps(data.get('matches', []))
            msg += ProtobufEncoder.encode_field(1, 2, matches_str)
            
        elif tool == ClientSideToolV2.RUN_TERMINAL_COMMAND_V2:
            # RunTerminalCommandV2Result
            if 'stdout' in data:
                msg += ProtobufEncoder.encode_field(1, 2, data['stdout'])
            if 'stderr' in data:
                msg += ProtobufEncoder.encode_field(2, 2, data['stderr'])
            if 'exit_code' in data:
                msg += ProtobufEncoder.encode_field(3, 0, data['exit_code'])
                
        elif tool == ClientSideToolV2.EDIT_FILE:
            # EditFileResult
            if data.get('is_applied'):
                msg += ProtobufEncoder.encode_field(2, 0, 1)  # is_applied = true
        
        return msg
    
    def _get_result_field_number(self, tool: int) -> int:
        """Get the field number for tool result in ClientSideToolV2Result"""
        # Based on TASK-126-toolv2-params.md
        result_field_map = {
            ClientSideToolV2.READ_FILE: 6,
            ClientSideToolV2.LIST_DIR: 9,
            ClientSideToolV2.RIPGREP_SEARCH: 4,
            ClientSideToolV2.RUN_TERMINAL_COMMAND_V2: 21,
            ClientSideToolV2.EDIT_FILE: 11,
            ClientSideToolV2.FILE_SEARCH: 10,
            ClientSideToolV2.GLOB_FILE_SEARCH: 51,
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
                    # Map name to enum
                    name_to_enum = {
                        'list_dir': ClientSideToolV2.LIST_DIR,
                        'read_file': ClientSideToolV2.READ_FILE,
                        'grep_search': ClientSideToolV2.RIPGREP_SEARCH,
                        'edit_file': ClientSideToolV2.EDIT_FILE,
                        'run_terminal_command': ClientSideToolV2.RUN_TERMINAL_COMMAND_V2,
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
