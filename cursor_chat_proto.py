#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor Chat protobuf implementation based on provided schema

Related analysis documents:
- TASK-26-tool-schemas.md: Tool parameter and result schemas
- TASK-7-protobuf-schemas.md: General protobuf message structures
- TASK-110-tool-enum-mapping.md: ClientSideToolV2 enum values
- TASK-126-toolv2-params.md: Detailed tool parameter field numbers

Wire format reference:
- Wire type 0: Varint (int32, int64, uint32, uint64, sint32, sint64, bool, enum)
- Wire type 1: 64-bit (fixed64, sfixed64, double)
- Wire type 2: Length-delimited (string, bytes, embedded messages, packed repeated fields)
- Wire type 5: 32-bit (fixed32, sfixed32, float)
"""

import struct
import uuid
from typing import Dict, List, Tuple, Any, Optional


class ProtobufDecoder:
    """Decode protobuf wire format messages
    
    Used to parse streaming responses from Cursor API.
    See TASK-7-protobuf-schemas.md for schema documentation.
    """
    
    @staticmethod
    def decode_varint(data: bytes, pos: int) -> Tuple[int, int]:
        """Decode a varint, return (value, new_position)"""
        result = 0
        shift = 0
        while pos < len(data):
            b = data[pos]
            result |= (b & 0x7F) << shift
            pos += 1
            if not (b & 0x80):
                break
            shift += 7
        return result, pos
    
    @staticmethod
    def decode_field(data: bytes, pos: int) -> Tuple[int, int, Any, int]:
        """Decode a single field, return (field_num, wire_type, value, new_position)"""
        if pos >= len(data):
            return None, None, None, pos
        
        tag, pos = ProtobufDecoder.decode_varint(data, pos)
        field_num = tag >> 3
        wire_type = tag & 0x07
        
        if wire_type == 0:  # Varint
            value, pos = ProtobufDecoder.decode_varint(data, pos)
        elif wire_type == 1:  # Fixed64
            value = struct.unpack('<Q', data[pos:pos+8])[0]
            pos += 8
        elif wire_type == 2:  # Length-delimited
            length, pos = ProtobufDecoder.decode_varint(data, pos)
            value = data[pos:pos+length]
            pos += length
        elif wire_type == 5:  # Fixed32
            value = struct.unpack('<I', data[pos:pos+4])[0]
            pos += 4
        else:
            value = None
        
        return field_num, wire_type, value, pos
    
    @staticmethod
    def decode_message(data: bytes) -> Dict[int, List[Any]]:
        """Decode all fields in a message, return dict of field_num -> [values]"""
        fields = {}
        pos = 0
        while pos < len(data):
            field_num, wire_type, value, pos = ProtobufDecoder.decode_field(data, pos)
            if field_num is None:
                break
            if field_num not in fields:
                fields[field_num] = []
            fields[field_num].append((wire_type, value))
        return fields
    
    @staticmethod
    def get_string(fields: Dict, field_num: int) -> Optional[str]:
        """Extract string field value"""
        if field_num in fields:
            for wire_type, value in fields[field_num]:
                if wire_type == 2 and isinstance(value, bytes):
                    try:
                        return value.decode('utf-8')
                    except:
                        pass
        return None
    
    @staticmethod
    def get_int(fields: Dict, field_num: int) -> Optional[int]:
        """Extract integer field value"""
        if field_num in fields:
            for wire_type, value in fields[field_num]:
                if wire_type == 0:
                    return value
        return None
    
    @staticmethod
    def get_bytes(fields: Dict, field_num: int) -> Optional[bytes]:
        """Extract bytes/nested message field value"""
        if field_num in fields:
            for wire_type, value in fields[field_num]:
                if wire_type == 2:
                    return value
        return None


class ToolCallDecoder:
    """Decode ClientSideToolV2Call messages from stream
    
    Based on TASK-26-tool-schemas.md:
    message ClientSideToolV2Call {
      ClientSideToolV2 tool = 1;
      string tool_call_id = 3;
      string name = 9;
      string raw_args = 10;
      // params oneof at various field numbers
    }
    """
    
    # Field numbers from TASK-26-tool-schemas.md
    FIELD_TOOL = 1
    FIELD_TOOL_CALL_ID = 3
    FIELD_NAME = 9
    FIELD_RAW_ARGS = 10
    
    @staticmethod
    def parse_frame(data: bytes) -> Tuple[Optional[bytes], bytes]:
        """Parse ConnectRPC frame: [flag:1][length:4][payload]
        Returns (payload, remaining_data)"""
        if len(data) < 5:
            return None, data
        
        flag = data[0]
        length = struct.unpack('>I', data[1:5])[0]
        
        if len(data) < 5 + length:
            return None, data
        
        payload = data[5:5+length]
        remaining = data[5+length:]
        return payload, remaining
    
    @staticmethod
    def find_tool_calls(data: bytes) -> List[Dict]:
        """Find tool calls in protobuf data by looking for known field patterns
        
        Returns list of dicts with: tool, tool_call_id, name, raw_args
        """
        tool_calls = []
        
        # Try to decode as protobuf
        try:
            fields = ProtobufDecoder.decode_message(data)
        except:
            return []
        
        # Look for nested messages that might contain tool calls
        # The response is a StreamUnifiedChatResponse which contains
        # various nested messages including tool calls
        
        # Try each length-delimited field as a potential tool call container
        for field_num, values in fields.items():
            for wire_type, value in values:
                if wire_type == 2 and isinstance(value, bytes) and len(value) > 10:
                    # Try to decode as nested message
                    try:
                        nested = ProtobufDecoder.decode_message(value)
                        tool_call = ToolCallDecoder._extract_tool_call(nested)
                        if tool_call:
                            tool_calls.append(tool_call)
                        
                        # Also check nested messages within
                        for nf, nv in nested.items():
                            for nwt, nval in nv:
                                if nwt == 2 and isinstance(nval, bytes) and len(nval) > 10:
                                    try:
                                        deep = ProtobufDecoder.decode_message(nval)
                                        tool_call = ToolCallDecoder._extract_tool_call(deep)
                                        if tool_call:
                                            tool_calls.append(tool_call)
                                    except:
                                        pass
                    except:
                        pass
        
        return tool_calls
    
    @staticmethod
    def _extract_tool_call(fields: Dict) -> Optional[Dict]:
        """Extract tool call from decoded fields"""
        tool = ProtobufDecoder.get_int(fields, ToolCallDecoder.FIELD_TOOL)
        tool_call_id = ProtobufDecoder.get_string(fields, ToolCallDecoder.FIELD_TOOL_CALL_ID)
        name = ProtobufDecoder.get_string(fields, ToolCallDecoder.FIELD_NAME)
        raw_args = ProtobufDecoder.get_string(fields, ToolCallDecoder.FIELD_RAW_ARGS)
        
        # Valid tool call needs at least tool enum and tool_call_id
        if tool is not None and tool > 0 and tool_call_id:
            return {
                'tool': tool,
                'tool_call_id': tool_call_id,
                'name': name or '',
                'raw_args': raw_args or '',
            }
        return None


class ProtobufEncoder:
    @staticmethod
    def encode_varint(value):
        """Encode an integer as a varint"""
        result = b''
        while value >= 0x80:
            result += bytes([value & 0x7F | 0x80])
            value >>= 7
        result += bytes([value & 0x7F])
        return result
    
    @staticmethod
    def encode_field(field_num, wire_type, value):
        """Encode a protobuf field"""
        tag = (field_num << 3) | wire_type
        result = ProtobufEncoder.encode_varint(tag)
        
        if wire_type == 0:  # Varint
            result += ProtobufEncoder.encode_varint(value)
        elif wire_type == 2:  # Length-delimited
            if isinstance(value, str):
                value = value.encode('utf-8')
            result += ProtobufEncoder.encode_varint(len(value)) + value
        elif wire_type == 1:  # Fixed64
            result += struct.pack('<Q', value)
            
        return result

class CursorChatMessage:
    """
    ChatMessage protobuf implementation based on schema:
    
    message ChatMessage {
      repeated UserMessage messages = 2;
      Instructions instructions = 4;
      string projectPath = 5;
      Model model = 7;
      string requestId = 9;
      string summary = 11;
      string conversationId = 15;
    }
    """
    
    @staticmethod
    def create_user_message(content, role=1, message_id=None):
        """
        Create a UserMessage:
        string content = 1;
        int32 role = 2;
        string message_id = 13;
        """
        if not message_id:
            message_id = str(uuid.uuid4())
            
        msg = b''
        msg += ProtobufEncoder.encode_field(1, 2, content)  # content (string)
        msg += ProtobufEncoder.encode_field(2, 0, role)     # role (int32) - 1=user, 2=assistant
        msg += ProtobufEncoder.encode_field(13, 2, message_id)  # message_id (string)
        return msg
    
    @staticmethod
    def create_instructions(instruction):
        """
        Create Instructions message:
        string instruction = 1;
        """
        if not instruction:
            return b''
        return ProtobufEncoder.encode_field(1, 2, instruction)
    
    @staticmethod
    def create_model(name, empty=""):
        """
        Create Model message:
        string name = 1;
        string empty = 4;
        """
        msg = b''
        msg += ProtobufEncoder.encode_field(1, 2, name)
        if empty:
            msg += ProtobufEncoder.encode_field(4, 2, empty)
        return msg
    
    @staticmethod
    def create_chat_message(messages, model="claude-3.5-sonnet", instructions=None, 
                          project_path="", request_id=None, summary="", 
                          conversation_id=None):
        """
        Create complete ChatMessage
        """
        if not request_id:
            request_id = str(uuid.uuid4())
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            
        chat_msg = b''
        
        # Field 2: repeated UserMessage messages
        for msg in messages:
            if isinstance(msg, dict):
                # Create UserMessage from dict
                user_msg = CursorChatMessage.create_user_message(
                    msg.get('content', ''),
                    1 if msg.get('role', 'user') == 'user' else 2,
                    msg.get('message_id')
                )
                chat_msg += ProtobufEncoder.encode_field(2, 2, user_msg)
            else:
                # Assume it's already encoded
                chat_msg += ProtobufEncoder.encode_field(2, 2, msg)
        
        # Field 4: Instructions (optional)
        if instructions:
            instr_msg = CursorChatMessage.create_instructions(instructions)
            chat_msg += ProtobufEncoder.encode_field(4, 2, instr_msg)
        
        # Field 5: projectPath (string)
        if project_path:
            chat_msg += ProtobufEncoder.encode_field(5, 2, project_path)
        
        # Field 7: Model
        model_msg = CursorChatMessage.create_model(model)
        chat_msg += ProtobufEncoder.encode_field(7, 2, model_msg)
        
        # Field 9: requestId (string)
        chat_msg += ProtobufEncoder.encode_field(9, 2, request_id)
        
        # Field 11: summary (string)
        if summary:
            chat_msg += ProtobufEncoder.encode_field(11, 2, summary)
        
        # Field 15: conversationId (string)
        chat_msg += ProtobufEncoder.encode_field(15, 2, conversation_id)
        
        return chat_msg
    
    @staticmethod
    def create_simple_chat_request(prompt, model="claude-3.5-sonnet"):
        """
        Create a simple chat request with just a user message
        """
        messages = [{'content': prompt, 'role': 'user'}]
        return CursorChatMessage.create_chat_message(messages, model)
    
    @staticmethod
    def create_hex_envelope(protobuf_data):
        """
        Create envelope with hex-encoded length (like in the JS code)
        Format: [magic:1][hex_length:8][data]
        """
        magic = 0x00  # No compression
        length_hex = f"{len(protobuf_data):08x}"  # 8 hex chars
        
        envelope = bytes([magic]) + length_hex.encode('ascii') + protobuf_data
        return envelope
    
    @staticmethod
    def create_binary_envelope(protobuf_data):
        """
        Create envelope with binary length
        Format: [magic:1][length:4][data]
        """
        magic = 0x00
        length = struct.pack('>I', len(protobuf_data))
        return bytes([magic]) + length + protobuf_data