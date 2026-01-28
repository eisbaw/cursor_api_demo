#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor Bidirectional Streaming Client using h2

True HTTP/2 bidirectional streaming implementation for Cursor's agent API.
This allows sending tool results back on the same stream.

Based on reverse engineering analysis of Cursor IDE 2.3.41.
"""

import asyncio
import ssl
import socket
import struct
import json
import uuid
import hashlib
import time
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Callable
from dataclasses import dataclass

import h2.connection
import h2.events
import h2.config

from cursor_auth_reader import CursorAuthReader
from cursor_chat_proto import ProtobufEncoder


# Import from agent client
from cursor_agent_client import (
    ClientSideToolV2, UnifiedMode, ToolCall, ToolResult, ToolExecutor,
    CursorAgentClient
)


@dataclass
class StreamState:
    """State for a single HTTP/2 stream"""
    stream_id: int
    headers_sent: bool = False
    headers_received: bool = False
    body_buffer: bytes = b''
    response_headers: Dict[str, str] = None
    ended: bool = False


class CursorBidiClient:
    """HTTP/2 bidirectional streaming client for Cursor API"""
    
    BASE_URL = "api2.cursor.sh"
    PORT = 443
    
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
        self.workspace_root = Path(workspace_root).resolve()
        self.auth_reader = CursorAuthReader()
        self.token = self.auth_reader.get_bearer_token()
        
        # Get machine ID from storage
        try:
            storage_data = self.auth_reader.read_sqlite_storage()
            self.machine_id = storage_data.get('storage.serviceMachineId')
        except:
            self.machine_id = None
        
        self.tool_executor = ToolExecutor(str(self.workspace_root))
        
        # Use agent client's encoding methods
        self._encoder = CursorAgentClient(workspace_root=str(self.workspace_root))
        
        # HTTP/2 connection state
        self.conn: Optional[h2.connection.H2Connection] = None
        self.sock: Optional[ssl.SSLSocket] = None
        self.streams: Dict[int, StreamState] = {}
        
    def generate_hashed_64_hex(self, token: str, seed: str = "clientKey") -> str:
        """Generate a 64-char hex hash using agent client's algorithm"""
        return self._encoder.generate_hashed_64_hex(token, seed)
    
    def generate_session_id(self, token: str) -> str:
        """Generate session ID from token using agent client's algorithm"""
        return self._encoder.generate_session_id(token)
    
    def generate_cursor_checksum(self, token: str) -> str:
        """Generate x-cursor-checksum header value using agent client's algorithm"""
        # Use the proven algorithm from CursorAgentClient
        return self._encoder.generate_cursor_checksum(token)
    
    def get_headers(self, auth_token: str) -> List[Tuple[str, str]]:
        """Get HTTP/2 headers for the request"""
        session_id = self.generate_session_id(auth_token)
        client_key = self.generate_hashed_64_hex(auth_token)
        checksum = self.generate_cursor_checksum(auth_token)
        
        # Match the headers from the working httpx client exactly
        return [
            (":method", "POST"),
            (":path", "/aiserver.v1.ChatService/StreamUnifiedChatWithTools"),
            (":authority", self.BASE_URL),
            (":scheme", "https"),
            ("authorization", f"Bearer {auth_token}"),
            ("connect-accept-encoding", "gzip"),
            ("connect-protocol-version", "1"),
            ("content-type", "application/connect+proto"),
            ("user-agent", "connect-es/1.6.1"),
            ("x-amzn-trace-id", f"Root={uuid.uuid4()}"),
            ("x-client-key", client_key),
            ("x-cursor-checksum", checksum),
            ("x-cursor-client-version", "2.3.41"),
            ("x-cursor-client-type", "ide"),
            ("x-cursor-client-os", "linux"),
            ("x-cursor-client-arch", "x64"),
            ("x-cursor-client-device-type", "desktop"),
            ("x-cursor-config-version", str(uuid.uuid4())),
            ("x-cursor-timezone", "Europe/Copenhagen"),
            ("x-ghost-mode", "true"),
            ("x-request-id", str(uuid.uuid4())),
            ("x-session-id", session_id),
        ]
    
    def frame_message(self, data: bytes, compress: bool = False) -> bytes:
        """Frame a message with ConnectRPC envelope"""
        flags = 0x01 if compress else 0x00
        length = len(data)
        return struct.pack('>BI', flags, length) + data
    
    def parse_frames(self, data: bytes) -> List[Tuple[bool, bytes]]:
        """Parse ConnectRPC framed messages from data"""
        frames = []
        offset = 0
        while offset + 5 <= len(data):
            flags = data[offset]
            length = struct.unpack('>I', data[offset+1:offset+5])[0]
            if offset + 5 + length > len(data):
                break
            payload = data[offset+5:offset+5+length]
            compressed = bool(flags & 0x01)
            frames.append((compressed, payload))
            offset += 5 + length
        return frames
    
    def encode_agent_request(self, messages: List[Dict], model: str) -> bytes:
        """Encode the initial agent request using agent client's encoding
        
        Note: This returns FRAMED data (magic byte + length + payload)
        """
        # Use the proven encoding from CursorAgentClient
        # generate_request_body already includes framing
        return self._encoder.generate_request_body(messages, model)
    
    def encode_tool_result(self, tool: int, tool_call_id: str, result: ToolResult) -> bytes:
        """Encode ClientSideToolV2Result using agent client's encoding"""
        # Use the proven encoding from CursorAgentClient
        return self._encoder.encode_tool_result(tool, tool_call_id, result)
    
    def encode_tool_result_message(self, tool: int, tool_call_id: str, result: ToolResult) -> bytes:
        """Encode StreamUnifiedChatRequestWithTools containing tool result"""
        msg = b''
        # Field 2: client_side_tool_v2_result
        result_bytes = self.encode_tool_result(tool, tool_call_id, result)
        msg += ProtobufEncoder.encode_field(2, 2, result_bytes)
        return msg
    
    def parse_tool_call(self, data: bytes) -> Optional[ToolCall]:
        """Parse tool call from response data - only returns when we have params"""
        try:
            text = data.decode('utf-8', errors='ignore')
            
            # Look for tool call ID pattern
            import re
            # Pattern: toolu_bdrk_ followed by exactly 26 alphanumeric chars
            tool_id_match = re.search(r'(toolu_bdrk_[a-zA-Z0-9]{26})', text)
            if not tool_id_match:
                tool_id_match = re.search(r'(toolu_[a-zA-Z0-9_]{20,32})', text)
            if not tool_id_match:
                return None
            
            tool_call_id = tool_id_match.group(1)
            
            # Find tool name - comprehensive mapping from TASK-110-tool-enum-mapping.md
            tool_name = None
            name_to_enum = {
                # Core file operations
                'list_dir': ClientSideToolV2.LIST_DIR,
                'read_file': ClientSideToolV2.READ_FILE,
                'edit_file': ClientSideToolV2.EDIT_FILE,
                'delete_file': ClientSideToolV2.DELETE_FILE,
                'file_search': ClientSideToolV2.FILE_SEARCH,
                'glob_file_search': ClientSideToolV2.GLOB_FILE_SEARCH,
                # Search operations
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
                'list_mcp_resources': ClientSideToolV2.LIST_MCP_RESOURCES,
                'read_mcp_resource': ClientSideToolV2.READ_MCP_RESOURCE,
                # Task/Agent
                'task': ClientSideToolV2.TASK,
                'await_task': ClientSideToolV2.AWAIT_TASK,
                'todo_read': ClientSideToolV2.TODO_READ,
                'todo_write': ClientSideToolV2.TODO_WRITE,
                'create_plan': ClientSideToolV2.CREATE_PLAN,
                # Misc
                'reapply': ClientSideToolV2.REAPPLY,
                'go_to_definition': ClientSideToolV2.GO_TO_DEFINITION,
                'gotodef': ClientSideToolV2.GO_TO_DEFINITION,
                'create_diagram': ClientSideToolV2.CREATE_DIAGRAM,
                'fix_lints': ClientSideToolV2.FIX_LINTS,
                'read_lints': ClientSideToolV2.READ_LINTS,
                'ask_question': ClientSideToolV2.ASK_QUESTION,
                'switch_mode': ClientSideToolV2.SWITCH_MODE,
                'generate_image': ClientSideToolV2.GENERATE_IMAGE,
                'computer_use': ClientSideToolV2.COMPUTER_USE,
                # V2 versions
                'list_dir_v2': ClientSideToolV2.LIST_DIR_V2,
                'read_file_v2': ClientSideToolV2.READ_FILE_V2,
                'edit_file_v2': ClientSideToolV2.EDIT_FILE_V2,
            }
            
            for name in name_to_enum:
                if re.search(rf'\b{name}\b', text, re.IGNORECASE):
                    tool_name = name
                    break
            
            if not tool_name:
                return None
            
            # Extract JSON params - REQUIRED for most tools
            params = {}
            # Look for complete JSON object with at least one key-value pair
            json_match = re.search(r'\{[^{}]*"[a-z_]+":\s*[^{}]+\}', text, re.IGNORECASE)
            if json_match:
                try:
                    params = json.loads(json_match.group())
                except:
                    pass
            
            # Tools that can work without params (list_dir with default path)
            tools_needing_params = {
                'file_search', 'grep_search', 'ripgrep_search', 'read_file', 
                'edit_file', 'run_terminal_command', 'run_terminal_cmd', 'glob_file_search',
                'web_search', 'codebase_search', 'deep_search', 'search_symbols',
                'delete_file', 'todo_write', 'create_plan', 'call_mcp_tool',
            }
            
            if tool_name in tools_needing_params and not params:
                return None  # Wait for params to arrive
            
            return ToolCall(
                tool=name_to_enum[tool_name],
                tool_call_id=tool_call_id,
                name=tool_name,
                raw_args=json_match.group() if json_match else '',
                params=params
            )
        except:
            return None
    
    def connect(self) -> bool:
        """Establish TLS connection and HTTP/2 handshake"""
        try:
            # Create SSL context
            ctx = ssl.create_default_context()
            ctx.set_alpn_protocols(['h2'])
            
            # Connect
            raw_sock = socket.create_connection((self.BASE_URL, self.PORT), timeout=30)
            self.sock = ctx.wrap_socket(raw_sock, server_hostname=self.BASE_URL)
            
            # Verify ALPN
            negotiated = self.sock.selected_alpn_protocol()
            if negotiated != 'h2':
                print(f"ALPN negotiation failed: {negotiated}")
                return False
            
            # Initialize HTTP/2 connection
            config = h2.config.H2Configuration(client_side=True)
            self.conn = h2.connection.H2Connection(config=config)
            self.conn.initiate_connection()
            self.sock.sendall(self.conn.data_to_send())
            
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def send_headers(self, stream_id: int, headers: List[Tuple[str, str]], end_stream: bool = False):
        """Send HTTP/2 headers on a stream"""
        self.conn.send_headers(stream_id, headers, end_stream=end_stream)
        self.sock.sendall(self.conn.data_to_send())
        
        if stream_id not in self.streams:
            self.streams[stream_id] = StreamState(stream_id=stream_id)
        self.streams[stream_id].headers_sent = True
    
    def send_data(self, stream_id: int, data: bytes, end_stream: bool = False):
        """Send HTTP/2 data on a stream"""
        # Check flow control window
        window = self.conn.local_flow_control_window(stream_id)
        if window < len(data):
            # Need to send in chunks
            while data:
                chunk_size = min(len(data), window, 16384)
                if chunk_size == 0:
                    break
                self.conn.send_data(stream_id, data[:chunk_size], end_stream=(end_stream and chunk_size >= len(data)))
                self.sock.sendall(self.conn.data_to_send())
                data = data[chunk_size:]
                window = self.conn.local_flow_control_window(stream_id)
        else:
            self.conn.send_data(stream_id, data, end_stream=end_stream)
            self.sock.sendall(self.conn.data_to_send())
    
    def receive_events(self, timeout: float = 1.0) -> List[h2.events.Event]:
        """Receive and process HTTP/2 events"""
        events = []
        self.sock.settimeout(timeout)
        try:
            data = self.sock.recv(65535)
            if data:
                new_events = self.conn.receive_data(data)
                events.extend(new_events)
                
                # Handle window updates
                for event in new_events:
                    if isinstance(event, h2.events.WindowUpdated):
                        pass  # Flow control handled automatically
                    elif isinstance(event, h2.events.DataReceived):
                        stream_id = event.stream_id
                        if stream_id in self.streams:
                            self.streams[stream_id].body_buffer += event.data
                        # Acknowledge received data
                        self.conn.acknowledge_received_data(len(event.data), stream_id)
                    elif isinstance(event, h2.events.ResponseReceived):
                        stream_id = event.stream_id
                        if stream_id in self.streams:
                            self.streams[stream_id].headers_received = True
                            self.streams[stream_id].response_headers = dict(event.headers)
                    elif isinstance(event, h2.events.StreamEnded):
                        stream_id = event.stream_id
                        if stream_id in self.streams:
                            self.streams[stream_id].ended = True
                
                # Send any pending data (window updates, etc.)
                self.sock.sendall(self.conn.data_to_send())
                
        except socket.timeout:
            pass
        except Exception as e:
            print(f"Receive error: {e}")
        
        return events
    
    def close(self):
        """Close the connection"""
        if self.conn:
            self.conn.close_connection()
            if self.sock:
                try:
                    self.sock.sendall(self.conn.data_to_send())
                except:
                    pass
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
    
    def run_agent(self, prompt: str, model: str = "claude-4-sonnet",
                  max_tool_calls: int = 10, verbose: bool = False) -> str:
        """Run agent with bidirectional streaming"""
        if not self.token:
            print("Error: No authentication token")
            return ""
        
        # Extract token after :: if present (e.g., "id::token" format)
        auth_token = self.token
        if '::' in auth_token:
            auth_token = auth_token.split('::')[1]
        
        if verbose:
            print(f"Agent mode (bidi) with model: {model}")
            print(f"Workspace: {self.workspace_root}")
            print(f"Token: {auth_token[:20]}..." if len(auth_token) > 20 else f"Token: {auth_token}")
            print("=" * 50)
        
        # Connect
        if not self.connect():
            return ""
        
        try:
            # Get next stream ID (client uses odd numbers)
            stream_id = self.conn.get_next_available_stream_id()
            
            # Send headers
            headers = self.get_headers(auth_token)
            
            if verbose:
                print("Headers being sent:")
                for k, v in headers:
                    if 'auth' in k.lower():
                        print(f"  {k}: {v[:30]}...")
                    else:
                        print(f"  {k}: {v}")
            
            self.send_headers(stream_id, headers)
            
            if verbose:
                print(f"Stream {stream_id} opened")
            
            # Send initial request (already framed by encode_agent_request)
            messages = [{"role": "user", "content": prompt}]
            framed_request = self.encode_agent_request(messages, model)
            self.send_data(stream_id, framed_request)
            
            if verbose:
                print(f"Initial request sent ({len(framed_request)} bytes)")
            
            # Main loop
            full_response = ""
            tool_calls_seen = set()
            tool_calls_executed = 0
            last_activity = time.time()
            timeout = 60.0
            
            while time.time() - last_activity < timeout:
                # Receive events
                events = self.receive_events(timeout=0.5)
                
                if events:
                    last_activity = time.time()
                
                # Check stream state
                if stream_id in self.streams:
                    state = self.streams[stream_id]
                    
                    # Process received data
                    if state.body_buffer:
                        data = state.body_buffer
                        state.body_buffer = b''
                        
                        # Extract text content
                        try:
                            text = data.decode('utf-8', errors='ignore')
                            printable = ''.join(c for c in text if c.isprintable() or c in '\n\r\t')
                            if printable and len(printable) > 2:
                                full_response += printable
                                print(printable, end='', flush=True)
                        except:
                            pass
                        
                        # Check for tool calls
                        tool_call = self.parse_tool_call(data)
                        if tool_call and tool_call.tool_call_id not in tool_calls_seen:
                            tool_calls_seen.add(tool_call.tool_call_id)
                            
                            if tool_calls_executed < max_tool_calls:
                                if verbose:
                                    print(f"\n[Tool: {tool_call.name}]")
                                
                                # Execute tool
                                result = self.tool_executor.execute(tool_call)
                                tool_calls_executed += 1
                                
                                if verbose:
                                    status = 'success' if result.success else result.error
                                    print(f"[Result: {status}]")
                                
                                # Send tool result back on the same stream!
                                result_data = self.encode_tool_result_message(
                                    tool_call.tool, tool_call.tool_call_id, result
                                )
                                framed_result = self.frame_message(result_data)
                                
                                if verbose:
                                    print(f"[Sending tool result ({len(framed_result)} bytes)]")
                                
                                # Small delay to let server finish sending tool call details
                                time.sleep(0.2)
                                
                                self.send_data(stream_id, framed_result)
                                
                                if verbose:
                                    print(f"[Sent tool result]")
                    
                    # Check if stream ended
                    if state.ended:
                        if verbose:
                            print("\n[Stream ended]")
                        break
            
            print()
            
            if tool_calls_executed > 0:
                print(f"\n--- Executed {tool_calls_executed} tool call(s) ---")
            
            return full_response
            
        finally:
            self.close()


async def main():
    import sys
    
    model = "claude-4-sonnet"
    prompt = "List the files in the current directory"
    verbose = False
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '-m' and i + 1 < len(args):
            model = args[i + 1]
            i += 2
        elif args[i] == '-v':
            verbose = True
            i += 1
        elif args[i] == '--help':
            print("Usage: cursor_bidi_client.py [-m model] [-v] [prompt]")
            print("  -m model   Model to use (default: claude-4-sonnet)")
            print("  -v         Verbose output")
            print("  prompt     The prompt to send")
            print()
            print("This client uses true HTTP/2 bidirectional streaming")
            print("to send tool results back on the same connection.")
            return
        else:
            prompt = args[i]
            i += 1
    
    client = CursorBidiClient(workspace_root=".")
    result = client.run_agent(prompt, model=model, verbose=verbose)
    
    if not result:
        print("No response received")


if __name__ == "__main__":
    asyncio.run(main())
