#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor Chat protobuf implementation based on provided schema
"""

import struct
import uuid

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