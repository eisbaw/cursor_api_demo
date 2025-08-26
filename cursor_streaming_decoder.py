#!/usr/bin/env python3
"""
Proper Cursor streaming response decoder based on Rust cursor-api implementation.
Handles frame-based protobuf messages with compression support.
"""

import struct
import gzip
import json
from typing import List, Optional, Generator, Tuple
import sys
import os

# Add cursor-grpc to path for protobuf imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'cursor-grpc'))

try:
    from server_full_pb2 import StreamUnifiedChatResponseWithTools
except ImportError as e:
    print(f"Failed to import protobuf classes: {e}", file=sys.stderr)
    print("Make sure cursor-grpc submodule is initialized and protobuf files are generated", file=sys.stderr)
    sys.exit(1)


class StreamMessage:
    """Represents a parsed streaming message."""
    
    def __init__(self, msg_type: str, content: str):
        self.msg_type = msg_type
        self.content = content
    
    def __repr__(self):
        return f"StreamMessage(type={self.msg_type}, content={repr(self.content[:100])}{'...' if len(self.content) > 100 else ''})"


class CursorStreamDecoder:
    """
    Decodes Cursor streaming responses using proper frame-based protobuf parsing.
    Based on cursor-api/src/core/stream/decoder.rs implementation.
    """
    
    def __init__(self):
        self.buffer = bytearray()
    
    def feed_data(self, data: bytes) -> List[StreamMessage]:
        """
        Feed incoming data and return parsed messages.
        Frame format: [msg_type:1byte][msg_len:4bytes_big_endian][msg_data:msg_len_bytes]
        """
        if not data:
            return []
        
        self.buffer.extend(data)
        messages = []
        
        while len(self.buffer) >= 5:  # Minimum frame header size
            # Parse frame header
            msg_type = self.buffer[0]
            msg_len = struct.unpack('>I', self.buffer[1:5])[0]  # Big endian uint32
            
            # Check if we have the complete message
            if len(self.buffer) < 5 + msg_len:
                break  # Wait for more data
            
            # Extract message data
            msg_data = bytes(self.buffer[5:5 + msg_len])
            self.buffer = self.buffer[5 + msg_len:]  # Remove processed data
            
            # Process message based on type
            if msg_len == 0:
                continue  # Skip empty messages
            
            message = self._process_message(msg_type, msg_data)
            if message:
                messages.append(message)
        
        return messages
    
    def _process_message(self, msg_type: int, msg_data: bytes) -> Optional[StreamMessage]:
        """Process a single message based on its type."""
        try:
            if msg_type == 0:
                # Raw protobuf message
                return self._handle_protobuf_message(msg_data)
            elif msg_type == 1:
                # Gzip compressed protobuf message
                try:
                    decompressed = gzip.decompress(msg_data)
                    return self._handle_protobuf_message(decompressed)
                except Exception as e:
                    print(f"Failed to decompress gzip protobuf: {e}", file=sys.stderr)
                    return None
            elif msg_type == 2:
                # Raw JSON message
                return self._handle_json_message(msg_data)
            elif msg_type == 3:
                # Gzip compressed JSON message
                try:
                    decompressed = gzip.decompress(msg_data)
                    return self._handle_json_message(decompressed)
                except Exception as e:
                    print(f"Failed to decompress gzip JSON: {e}", file=sys.stderr)
                    return None
            else:
                print(f"Unknown message type: {msg_type}", file=sys.stderr)
                return None
        except Exception as e:
            print(f"Error processing message type {msg_type}: {e}", file=sys.stderr)
            return None
    
    def _handle_protobuf_message(self, msg_data: bytes) -> Optional[StreamMessage]:
        """Handle protobuf message data."""
        try:
            response = StreamUnifiedChatResponseWithTools()
            response.ParseFromString(msg_data)
            
            # Extract nested StreamUnifiedChatResponse
            if response.HasField('stream_unified_chat_response'):
                chat_response = response.stream_unified_chat_response
                
                if chat_response.text:
                    return StreamMessage("content", chat_response.text)
                elif hasattr(chat_response, 'filled_prompt') and chat_response.filled_prompt:
                    return StreamMessage("debug", chat_response.filled_prompt)
                elif hasattr(chat_response, 'thinking') and chat_response.thinking:
                    return StreamMessage("thinking", str(chat_response.thinking))
                elif hasattr(chat_response, 'web_citation') and chat_response.web_citation:
                    return StreamMessage("web_reference", str(chat_response.web_citation))
            
            elif response.HasField('client_side_tool_v2_call'):
                return StreamMessage("tool_call", str(response.client_side_tool_v2_call))
            
            # If no recognized content, return None
            return None
            
        except Exception as e:
            print(f"Failed to parse protobuf message: {e}", file=sys.stderr)
            return None
    
    def _handle_json_message(self, msg_data: bytes) -> Optional[StreamMessage]:
        """Handle JSON message data."""
        try:
            if len(msg_data) == 2:
                return StreamMessage("stream_end", "")
            
            text = msg_data.decode('utf-8', errors='ignore')
            try:
                parsed = json.loads(text)
                if 'error' in parsed:
                    return StreamMessage("error", json.dumps(parsed))
            except json.JSONDecodeError:
                pass
            
            return StreamMessage("json", text)
            
        except Exception as e:
            print(f"Failed to handle JSON message: {e}", file=sys.stderr)
            return None


def decode_cursor_response(response_data: bytes) -> Generator[StreamMessage, None, None]:
    """
    Decode a complete Cursor streaming response.
    Yields StreamMessage objects as they're parsed.
    """
    decoder = CursorStreamDecoder()
    messages = decoder.feed_data(response_data)
    for message in messages:
        yield message


if __name__ == "__main__":
    # Test with sample data or stdin
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'rb') as f:
            data = f.read()
    else:
        data = sys.stdin.buffer.read()
    
    print("Decoding Cursor streaming response...")
    print("=" * 50)
    
    for message in decode_cursor_response(data):
        print(f"[{message.msg_type.upper()}] {message.content}")
        
        if message.msg_type == "stream_end":
            break