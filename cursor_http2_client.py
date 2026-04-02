#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor client using HTTP/2 - the breakthrough discovery!
HTTP 464 "Incompatible Protocol" means we need HTTP/2, not HTTP/1.1
"""

import asyncio
import httpx
import uuid
import hashlib
import time
import base64
from cursor_auth_reader import CursorAuthReader
from cursor_proper_protobuf import CursorProperProtobuf
from cursor_streaming_decoder import CursorStreamDecoder

class CursorHTTP2Client(CursorProperProtobuf):
    def __init__(self):
        super().__init__()
    
    async def establish_session_http2(self, auth_token, session_id, client_key, cursor_checksum):
        """Call AvailableModels - this works with HTTP/1.1"""
        print("Establishing session (HTTP/1.1)...")

        url = f"{self.base_url}/aiserver.v1.AiService/AvailableModels"
        headers = self.build_common_headers(auth_token, session_id, client_key, cursor_checksum)
        headers["accept-encoding"] = "gzip"
        headers["content-type"] = "application/proto"
        
        # Use HTTP/1.1 for AvailableModels (this works)
        async with httpx.AsyncClient(http2=False, timeout=10.0) as client:
            response = await client.post(url, headers=headers)
            if response.status_code == 401:
                refreshed = self.refresh_access_token()
                if refreshed and refreshed != auth_token:
                    headers["authorization"] = f"Bearer {refreshed}"
                    response = await client.post(url, headers=headers)
            print(f"Session: {response.status_code}")
            return response.status_code == 200
    
    async def send_chat_http2(self, messages, model, auth_token, session_id, client_key, cursor_checksum):
        """Send chat using HTTP/2 - THE KEY DIFFERENCE!"""
        print(f"Sending to {model} with HTTP/2...")

        cursor_body = self.generate_cursor_body_exact(messages, model)
        print(f"Body size: {len(cursor_body)} bytes")
        
        url = f"{self.base_url}/aiserver.v1.ChatService/StreamUnifiedChatWithTools"
        headers = self.build_common_headers(auth_token, session_id, client_key, cursor_checksum)
        headers["connect-accept-encoding"] = "gzip"
        headers["content-type"] = "application/connect+proto"
        
        # Use HTTP/2 instead of HTTP/1.1
        async with httpx.AsyncClient(http2=True, timeout=30.0) as client:
            try:
                print("Using HTTP/2 protocol...")
                async with client.stream('POST', url, headers=headers, content=cursor_body) as response:
                    if response.status_code == 401:
                        refreshed = self.refresh_access_token()
                        if refreshed and refreshed != auth_token:
                            headers["authorization"] = f"Bearer {refreshed}"
                            async with client.stream('POST', url, headers=headers, content=cursor_body) as retry_response:
                                response = retry_response
                                print(f"Status: {response.status_code}")
                                print(f"HTTP version: {response.http_version}")
                                if response.status_code != 200:
                                    error = await response.aread()
                                    print(f"Error {response.status_code}: {error.decode('utf-8', errors='ignore')[:200]}")
                                    return None
                                print("SUCCESS: HTTP/2 works. Streaming response:")
                                decoder = CursorStreamDecoder()
                                collected_content = []
                                chunk_count = 0
                                async for chunk in response.aiter_bytes():
                                    chunk_count += 1
                                    messages = decoder.feed_data(chunk)
                                    for message in messages:
                                        print(f"[{message.msg_type.upper()}] {message.content[:100]}{'...' if len(message.content) > 100 else ''}")
                                        if message.msg_type == "content":
                                            collected_content.append(message.content)
                                        elif message.msg_type == "stream_end":
                                            print("Stream ended")
                                            break
                                    if chunk_count > 100:
                                        print("Warning: stopping after 100 chunks")
                                        break
                                if collected_content:
                                    result = ''.join(collected_content)
                                    print(f"\nSUCCESS: Properly decoded streaming response:")
                                    print(f"Total content length: {len(result)} characters")
                                    return result
                                return "No content received"
                    print(f"Status: {response.status_code}")
                    print(f"HTTP version: {response.http_version}")
                    
                    if response.status_code == 200:
                        print("SUCCESS: HTTP/2 works. Streaming response:")
                        
                        # Use the proper streaming decoder based on Rust cursor-api
                        decoder = CursorStreamDecoder()
                        collected_content = []
                        chunk_count = 0
                        
                        async for chunk in response.aiter_bytes():
                            chunk_count += 1
                            
                            # Feed chunk to decoder and get parsed messages
                            messages = decoder.feed_data(chunk)
                            for message in messages:
                                print(f"[{message.msg_type.upper()}] {message.content[:100]}{'...' if len(message.content) > 100 else ''}")
                                
                                if message.msg_type == "content":
                                    collected_content.append(message.content)
                                elif message.msg_type == "stream_end":
                                    print("Stream ended")
                                    break
                            
                            # Safety limit
                            if chunk_count > 100:
                                print("Warning: stopping after 100 chunks")
                                break
                        
                        if collected_content:
                            result = ''.join(collected_content)
                            print(f"\nSUCCESS: Properly decoded streaming response:")
                            print(f"Total content length: {len(result)} characters")
                            return result
                        else:
                            return "No content received"
                    else:
                        error = await response.aread()
                        print(f"Error {response.status_code}: {error.decode('utf-8', errors='ignore')[:200]}")
                        
            except Exception as e:
                print(f"Exception: {str(e)}")
        
        return None
    
    async def test_http2_breakthrough(self, prompt="Hello! Please respond with 'Hi from Cursor API!'", model="default"):
        """Test the HTTP/2 breakthrough"""
        auth_token = self.get_active_token()
        if not auth_token:
            print("Error: No token")
            return None
        
        # Process auth token
        if '::' in auth_token:
            auth_token = auth_token.split('::')[1]
        
        # Generate session data
        session_id = self.generate_session_id(auth_token)
        client_key = self.generate_hashed_64_hex(auth_token)
        cursor_checksum = self.generate_cursor_checksum(auth_token)
        
        print(f"HTTP/2 Test")
        print(f"HTTP 464 = Incompatible Protocol = Need HTTP/2!")
        print("=" * 60)
        print(f"Session: {session_id}")
        print(f"Model: {model}")
        print(f"Prompt: {prompt}")
        
        # Step 1: Establish session with HTTP/1.1 (works)
        session_ok = await self.establish_session_http2(auth_token, session_id, client_key, cursor_checksum)
        if not session_ok:
            print("Error: Session failed")
            return None
        
        # Step 2: Send chat with HTTP/2 (THE BREAKTHROUGH!)
        messages = [{"role": "user", "content": prompt}]
        result = await self.send_chat_http2(
            messages, model, auth_token, session_id, client_key, cursor_checksum
        )
        
        return result
