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

class CursorHTTP2Client(CursorProperProtobuf):
    def __init__(self):
        super().__init__()
    
    async def establish_session_http2(self, auth_token, session_id, client_key, cursor_checksum):
        """Call AvailableModels - this works with HTTP/1.1"""
        print("🔧 Establishing session (HTTP/1.1)...")
        
        url = f"{self.base_url}/aiserver.v1.AiService/AvailableModels"
        headers = {
            'accept-encoding': 'gzip',
            'authorization': f'Bearer {auth_token}',
            'connect-protocol-version': '1',
            'content-type': 'application/proto',  # Note: different content-type
            'user-agent': 'connect-es/1.6.1',
            'x-amzn-trace-id': f'Root={uuid.uuid4()}',
            'x-client-key': client_key,
            'x-cursor-checksum': cursor_checksum,
            'x-cursor-client-version': '1.1.3',
            'x-cursor-config-version': str(uuid.uuid4()),
            'x-cursor-timezone': 'Asia/Shanghai',
            'x-ghost-mode': 'true',
            'x-request-id': str(uuid.uuid4()),
            'x-session-id': session_id,
            'Host': 'api2.cursor.sh',
        }
        
        # Use HTTP/1.1 for AvailableModels (this works)
        async with httpx.AsyncClient(http2=False, timeout=10.0) as client:
            response = await client.post(url, headers=headers)
            print(f"Session: {response.status_code}")
            return response.status_code == 200
    
    async def send_chat_http2(self, messages, model, auth_token, session_id, client_key, cursor_checksum):
        """Send chat using HTTP/2 - THE KEY DIFFERENCE!"""
        print(f"🚀 Sending to {model} with HTTP/2...")
        
        cursor_body = self.generate_cursor_body_exact(messages, model)
        print(f"Body size: {len(cursor_body)} bytes")
        
        url = f"{self.base_url}/aiserver.v1.ChatService/StreamUnifiedChatWithTools"
        headers = {
            'authorization': f'Bearer {auth_token}',
            'connect-accept-encoding': 'gzip',
            'connect-protocol-version': '1',
            'content-type': 'application/connect+proto',  # ConnectRPC content type
            'user-agent': 'connect-es/1.6.1',
            'x-amzn-trace-id': f'Root={uuid.uuid4()}',
            'x-client-key': client_key,
            'x-cursor-checksum': cursor_checksum,
            'x-cursor-client-version': '1.1.3',
            'x-cursor-config-version': str(uuid.uuid4()),
            'x-cursor-timezone': 'Asia/Shanghai',
            'x-ghost-mode': 'true',
            'x-request-id': str(uuid.uuid4()),
            'x-session-id': session_id,
            'Host': 'api2.cursor.sh'
        }
        
        # 🎯 THE BREAKTHROUGH: Use HTTP/2 instead of HTTP/1.1!
        async with httpx.AsyncClient(http2=True, timeout=30.0) as client:
            try:
                print("📡 Using HTTP/2 protocol...")
                async with client.stream('POST', url, headers=headers, content=cursor_body) as response:
                    print(f"Status: {response.status_code}")
                    print(f"HTTP version: {response.http_version}")
                    
                    if response.status_code == 200:
                        print("🎉 SUCCESS! HTTP/2 works! Streaming response:")
                        full_text = ""
                        chunk_count = 0
                        
                        async for chunk in response.aiter_bytes():
                            chunk_count += 1
                            
                            # Try simple text extraction for now
                            try:
                                text = chunk.decode('utf-8', errors='ignore')
                                # Filter out noise but keep meaningful content
                                clean_text = ''.join(c for c in text if c.isprintable())
                                if clean_text and len(clean_text) > 3:
                                    full_text += clean_text
                                    print(clean_text, end='', flush=True)
                            except:
                                pass
                            
                            if len(full_text) > 1000 or chunk_count > 50:
                                break
                        
                        print(f"\n\n🎉 HTTP/2 SUCCESS! Got {chunk_count} chunks, {len(full_text)} chars!")
                        return full_text
                    else:
                        error = await response.aread()
                        print(f"❌ Error {response.status_code}: {error.decode('utf-8', errors='ignore')[:200]}")
                        
            except Exception as e:
                print(f"❌ Exception: {str(e)}")
        
        return None
    
    async def test_http2_breakthrough(self, prompt="Hello! Please respond with 'Hi from Cursor API!'", model="gpt-4"):
        """Test the HTTP/2 breakthrough"""
        if not self.token:
            print("❌ No token")
            return None
        
        # Process auth token
        auth_token = self.token
        if '::' in auth_token:
            auth_token = auth_token.split('::')[1]
        
        # Generate session data
        session_id = self.generate_session_id(auth_token)
        client_key = self.generate_hashed_64_hex(auth_token)
        cursor_checksum = self.generate_cursor_checksum(auth_token)
        
        print(f"🎯 HTTP/2 BREAKTHROUGH TEST")
        print(f"HTTP 464 = Incompatible Protocol = Need HTTP/2!")
        print("=" * 60)
        print(f"Session: {session_id}")
        print(f"Model: {model}")
        print(f"Prompt: {prompt}")
        
        # Step 1: Establish session with HTTP/1.1 (works)
        session_ok = await self.establish_session_http2(auth_token, session_id, client_key, cursor_checksum)
        if not session_ok:
            print("❌ Session failed")
            return None
        
        # Step 2: Send chat with HTTP/2 (THE BREAKTHROUGH!)
        messages = [{"role": "user", "content": prompt}]
        result = await self.send_chat_http2(
            messages, model, auth_token, session_id, client_key, cursor_checksum
        )
        
        return result
