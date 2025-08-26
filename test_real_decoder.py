#!/usr/bin/env python3
"""Test the streaming decoder with actual protobuf message"""

import sys
import os
import struct

# Add cursor-grpc to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'cursor-grpc'))

from cursor_streaming_decoder import CursorStreamDecoder
from server_full_pb2 import StreamUnifiedChatResponseWithTools, StreamUnifiedChatResponse

def create_real_test_frame():
    """Create a proper protobuf message frame"""
    # Create inner message
    inner_response = StreamUnifiedChatResponse()
    inner_response.text = "Hello from properly decoded Cursor API!"
    
    # Create outer message  
    outer_response = StreamUnifiedChatResponseWithTools()
    outer_response.stream_unified_chat_response.CopyFrom(inner_response)
    
    # Serialize to bytes
    protobuf_data = outer_response.SerializeToString()
    
    # Create frame: msg_type=0 (protobuf), msg_len, msg_data
    msg_type = 0
    msg_len = len(protobuf_data)
    frame = struct.pack('>BI', msg_type, msg_len) + protobuf_data
    
    print(f"Created frame: type={msg_type}, len={msg_len}, data={protobuf_data[:20].hex()}...")
    
    return frame

def test_real_decoder():
    print("Testing Cursor Stream Decoder with real protobuf...")
    
    try:
        decoder = CursorStreamDecoder()
        test_frame = create_real_test_frame()
        
        messages = decoder.feed_data(test_frame)
        print(f"✅ Decoded {len(messages)} messages:")
        for msg in messages:
            print(f"  [{msg.msg_type.upper()}] {msg.content}")
            
        return len(messages) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_real_decoder()
    if success:
        print("\n🎉 Decoder test PASSED!")
    else:
        print("\n❌ Decoder test FAILED!")
        sys.exit(1)