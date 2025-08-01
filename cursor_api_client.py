#!/usr/bin/env python3
"""
Minimal Cursor API Client
Demonstrates how to communicate with Cursor's backend API using gRPC-web protocol
Updated for Cursor 1.3.7 with Protocol Buffer support
"""

import json
import asyncio
import aiohttp
import base64
from typing import Dict, Optional, List, AsyncIterator
import struct

from constants import CURSOR_EMBEDDED_AI_KEY

class CursorAPIClient:
    """Minimal client for Cursor's gRPC-web API"""
    
    def __init__(self, bearer_token: Optional[str] = None):
        """
        Initialize the client
        
        Args:
            bearer_token: Your Cursor authentication token
        """
        # API endpoints
        self.base_url = "https://api2.cursor.sh"
        self.marketplace_url = "https://marketplace.cursorapi.com/_apis/public/gallery"

        # squashfs-root-1.3/usr/share/cursor/resources/app/out/main.beautified.js
        #   Cw = "https://80ec2259ebfad12d8aa2afe6eb4f6dd5@metrics.cursor.sh/4508016051945472"
        # squashfs-root-1.3/usr/share/cursor/resources/app/out/vs/workbench/workbench.desktop.main.beautified.js
        #   fio = "https://80ec2259ebfad12d8aa2afe6eb4f6dd5@metrics.cursor.sh/4508016051945472", 
        self.metrics_url = "https://metrics.cursor.sh/4508016051945472"

        # This is 
        #   Yqi = "KbZUR41cY7W6zRSdpSUJ7I7mLYBKOCmB"
        # in squashfs-root-1.3/usr/share/cursor/resources/app/out/vs/workbench/workbench.desktop.main.js 
        self.app_key = "KbZUR41cY7W6zRSdpSUJ7I7mLYBKOCmB"

        # This seems to be used by many vscode extensions
        self.embedded_ai_key = CURSOR_EMBEDDED_AI_KEY
        
        # Headers
        self.headers = {
            "Content-Type": "application/grpc-web+proto",
            "X-Grpc-Web": "1",
            "Accept": "application/grpc-web+proto",
            "User-Agent": "Cursor/1.3.7",
            "Origin": "https://cursor.sh",
        }
        
        if bearer_token:
            self.headers["Authorization"] = f"Bearer {bearer_token}"
    
    def _encode_length_delimited(self, data: bytes) -> bytes:
        """Encode data with length prefix for gRPC-web"""
        # gRPC-web uses a 5-byte header: 1 byte for compressed flag + 4 bytes for length
        length = len(data)
        # 0x00 = not compressed
        header = struct.pack('>BI', 0x00, length)
        return header + data
    
    def _decode_grpc_web_response(self, data: bytes) -> List[bytes]:
        """Decode gRPC-web response into individual messages"""
        messages = []
        offset = 0
        
        while offset < len(data):
            if offset + 5 > len(data):
                break
                
            # Read 5-byte header
            compressed = data[offset]
            length = struct.unpack('>I', data[offset + 1:offset + 5])[0]
            offset += 5
            
            if offset + length > len(data):
                break
                
            # Extract message
            message = data[offset:offset + length]
            messages.append(message)
            offset += length
            
        return messages
    
    async def stream_chat(self, prompt: str, model: str = "claude-3.5-sonnet") -> AsyncIterator[str]:
        """
        Send a chat prompt and stream the response
        
        Args:
            prompt: The prompt to send
            model: The model to use (default: claude-3.5-sonnet)
            
        Yields:
            Response chunks as they arrive
        """
        # Uses aiserver.v1 Protocol Buffers
        # Message types include:
        # - aiserver.v1.UsageEventDetails (Chat, Composer, CmdK, etc.)
        # - aiserver.v1.DocumentationQueryRequest/Response
        
        # For now, let's demonstrate the connection pattern
        # In 1.3.7, the main submit function is submitChatMaybeAbortCurrent
        endpoint = f"{self.base_url}/aiserver.v1.CmdKService/StreamCmdK"
        
        # In a real implementation, you'd encode the request using protobuf
        # This is a placeholder showing the structure
        request_data = {
            "prompt": prompt,
            "modelDetails": {
                "model": model,
                "provider": "anthropic"
            },
            "contextItems": [],
            "options": {}
        }
        
        # Note: This is simplified - actual encoding requires protobuf
        request_bytes = json.dumps(request_data).encode('utf-8')
        encoded_request = self._encode_length_delimited(request_bytes)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint,
                data=encoded_request,
                headers=self.headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API error: {response.status} - {error_text}")
                
                # Stream the response
                async for chunk in response.content.iter_any():
                    if chunk:
                        messages = self._decode_grpc_web_response(chunk)
                        for message in messages:
                            # In real implementation, decode protobuf here
                            # For now, just yield the raw message
                            yield f"Received message: {len(message)} bytes"

    async def simple_chat(self, prompt: str) -> str:
        """
        Send a chat prompt and get the complete response
        
        Args:
            prompt: The prompt to send
            
        Returns:
            The complete response
        """
        response_parts = []
        async for chunk in self.stream_chat(prompt):
            response_parts.append(chunk)
        return "\n".join(response_parts)


# Example usage
async def main():
    """Example of how to use the client"""
    
    # Note: You need to get your bearer token from Cursor
    # 1. Open Cursor
    # 2. Open Developer Tools (Cmd+Option+I on Mac)
    # 3. Go to Network tab
    # 4. Send a prompt in Cursor
    # 5. Look for requests to api2.cursor.sh
    # 6. Copy the Authorization header value (without "Bearer ")
    
    bearer_token = "YOUR_BEARER_TOKEN_HERE"
    
    # Create client
    client = CursorAPIClient(bearer_token=bearer_token)
    
    # Example 1: Stream a response
    print("Streaming response:")
    async for chunk in client.stream_chat("Hello, how are you?"):
        print(chunk)
    
    # Example 2: Get complete response
    print("\nComplete response:")
    response = await client.simple_chat("What is Python?")
    print(response)


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())


"""
IMPORTANT NOTES:

1. This is a simplified demonstration. A full implementation requires:
   - Proper protobuf definitions from Cursor's proto files
   - Correct message encoding/decoding
   - Handling of streaming responses
   - Error handling and retries

2. The actual protocol in Cursor 1.3.7:
   - Uses extensive Protocol Buffers (aiserver.v1.*)
   - Implements gRPC-web streaming with WebSocket/SSE
   - Includes sophisticated service architecture patterns
   - Handles usage event tracking (Chat, Composer, CmdK, etc.)
   - Native components: Rust file service, WebAssembly tokenization

3. For a production client, you would need:
   - The protobuf definitions (.proto files)
   - A protobuf compiler to generate Python classes
   - Proper gRPC-web client implementation
   - Session management and authentication flow
"""
