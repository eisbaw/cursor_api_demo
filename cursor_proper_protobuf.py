#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor client with proper protobuf implementation matching the exact JavaScript schema
"""

import asyncio
import httpx
import uuid
import hashlib
import struct
import gzip
import time
import base64
import json
import os
import platform
import sys
from urllib.parse import urlparse
from cursor_auth_reader import CursorAuthReader
from cursor_chat_proto import ProtobufEncoder

DEFAULT_BACKEND_URL = "https://api2.cursor.sh"
DEFAULT_CURSOR_VERSION = "2.6.22"
DEFAULT_AUTH_CLIENT_ID = "KbZUR41cY7W6zRSdpSUJ7I7mLYBKOCmB"
TOKEN_REFRESH_SKEW_SECONDS = 120

class CursorProperProtobuf:
    def __init__(self):
        self.auth_reader = CursorAuthReader()
        self.token = self.auth_reader.get_bearer_token()
        self.base_url = os.environ.get("CURSOR_BACKEND_URL", DEFAULT_BACKEND_URL).rstrip("/")
        self.base_host = self._extract_host(self.base_url)
        self.cursor_version = self._load_cursor_version()
        self.auth_client_id = os.environ.get("CURSOR_AUTH_CLIENT_ID", DEFAULT_AUTH_CLIENT_ID)
        self.client_os = self._normalize_os(platform.system())
        self.client_arch = self._normalize_arch(platform.machine())
        self.client_os_version = platform.release() or "unknown"
        self.client_timezone = self._detect_timezone()
        self.ghost_mode = self._env_bool("CURSOR_GHOST_MODE", False)
        self.new_onboarding_completed = self._env_bool("CURSOR_NEW_ONBOARDING_COMPLETED", False)

    def _env_bool(self, key, default):
        value = os.environ.get(key)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}

    def _extract_host(self, base_url):
        try:
            parsed = urlparse(base_url if "://" in base_url else f"https://{base_url}")
            if parsed.netloc:
                return parsed.netloc
            if parsed.path:
                return parsed.path
        except Exception:
            pass
        return "api2.cursor.sh"

    def _normalize_os(self, system):
        normalized = {
            "linux": "linux",
            "darwin": "darwin",
            "windows": "win32",
        }
        lowered = system.lower()
        return normalized.get(lowered, lowered or "linux")

    def _normalize_arch(self, arch):
        lowered = arch.lower()
        if lowered in ("x86_64", "amd64"):
            return "x64"
        if lowered in ("aarch64", "arm64"):
            return "arm64"
        return lowered

    def _detect_timezone(self):
        tz_env = os.environ.get("TZ")
        if tz_env:
            return tz_env

        timezone_file = "/etc/timezone"
        try:
            with open(timezone_file, "r", encoding="utf-8") as f:
                tz_name = f.read().strip()
            if tz_name:
                return tz_name
        except Exception:
            pass

        try:
            localtime_target = os.path.realpath("/etc/localtime")
            marker = "/zoneinfo/"
            if marker in localtime_target:
                return localtime_target.split(marker, 1)[1]
        except Exception:
            pass

        # Last-resort fallback when no IANA zone can be discovered.
        return "UTC"

    def _version_key(self, version):
        parts = []
        for part in version.split("."):
            if part.isdigit():
                parts.append(int(part))
                continue
            digits = "".join(ch for ch in part if ch.isdigit())
            parts.append(int(digits) if digits else 0)
        return tuple(parts)

    def _discover_product_json_paths(self):
        base_dir = os.path.dirname(__file__)
        discovered = []
        try:
            entries = os.listdir(base_dir)
        except Exception:
            return discovered

        for entry in entries:
            entry_path = os.path.join(base_dir, entry)
            if not os.path.isdir(entry_path):
                continue

            if entry.startswith("reveng_"):
                discovered.append(
                    os.path.join(entry_path, "original", "product.json")
                )

            if entry.startswith("squashfs-root"):
                discovered.append(
                    os.path.join(
                        entry_path,
                        "usr",
                        "share",
                        "cursor",
                        "resources",
                        "app",
                        "product.json",
                    )
                )

        # Keep deterministic ordering for stable behavior.
        return sorted(set(discovered))

    def _load_cursor_version(self):
        """
        Resolve the active Cursor version from available product.json files.
        Falls back to DEFAULT_CURSOR_VERSION when unavailable.
        """
        env_version = os.environ.get("CURSOR_CLIENT_VERSION")
        if env_version:
            return env_version

        product_paths = self._discover_product_json_paths()
        best_version = None
        for path in product_paths:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                version = data.get("version")
                if isinstance(version, str) and version:
                    if best_version is None or self._version_key(version) > self._version_key(best_version):
                        best_version = version
            except Exception:
                continue
        if best_version:
            return best_version
        return DEFAULT_CURSOR_VERSION

    def _decode_jwt_exp(self, token):
        try:
            payload = token.split(".")[1]
            payload += "=" * (-len(payload) % 4)
            data = json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
            return int(data["exp"])
        except Exception:
            return None

    def _token_needs_refresh(self, token):
        exp = self._decode_jwt_exp(token)
        if exp is None:
            return False
        return exp - int(time.time()) < TOKEN_REFRESH_SKEW_SECONDS

    def refresh_access_token(self):
        """
        Refresh OAuth access token using stored refresh token.
        Cursor 2.6.22 uses POST {backendUrl}/oauth/token with grant_type refresh_token.
        """
        tokens = self.auth_reader.get_auth_tokens()
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            return None

        payload = {
            "grant_type": "refresh_token",
            "client_id": self.auth_client_id,
            "refresh_token": refresh_token,
        }
        try:
            response = httpx.post(
                f"{self.base_url}/oauth/token",
                json=payload,
                timeout=20.0,
            )
            if response.status_code != 200:
                return None
            data = response.json()
            new_access_token = data.get("access_token")
            if isinstance(new_access_token, str) and new_access_token:
                self.token = new_access_token
                return new_access_token
        except Exception:
            return None
        return None

    def get_active_token(self, force_refresh=False):
        token = self.token
        if not token:
            token = self.auth_reader.get_bearer_token()
            self.token = token
        if not token:
            return None
        if force_refresh or self._token_needs_refresh(token):
            refreshed = self.refresh_access_token()
            if refreshed:
                return refreshed
        return token

    def build_common_headers(self, auth_token, session_id, client_key, cursor_checksum):
        request_id = str(uuid.uuid4())
        return {
            "authorization": f"Bearer {auth_token}",
            "connect-protocol-version": "1",
            "user-agent": "connect-es/1.6.1",
            "x-amzn-trace-id": f"Root={request_id}",
            "x-client-key": client_key,
            "x-cursor-checksum": cursor_checksum,
            "x-cursor-client-version": self.cursor_version,
            "x-cursor-client-type": "ide",
            "x-cursor-client-os": self.client_os,
            "x-cursor-client-arch": self.client_arch,
            "x-cursor-client-os-version": self.client_os_version,
            "x-cursor-client-device-type": "desktop",
            "x-cursor-config-version": str(uuid.uuid4()),
            "x-cursor-timezone": self.client_timezone,
            "x-ghost-mode": "true" if self.ghost_mode else "false",
            "x-new-onboarding-completed": "true" if self.new_onboarding_completed else "false",
            "x-request-id": request_id,
            "x-session-id": session_id,
            "host": self.base_host,
        }
        
    def generate_hashed_64_hex(self, input_str, salt=''):
        """Generate SHA-256 hash like JS generateHashed64Hex"""
        hash_obj = hashlib.sha256()
        hash_obj.update((input_str + salt).encode('utf-8'))
        return hash_obj.hexdigest()
    
    def generate_session_id(self, auth_token):
        """Generate sessionid using UUID v5 with DNS namespace like JS"""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, auth_token))
    
    def get_machine_id(self):
        """Get machine ID from Cursor storage"""
        import sqlite3
        db_path = self.auth_reader.storage_path
        if not db_path:
            return None
        try:
            db_uri = f"file:{db_path}?mode=ro&immutable=1"
            conn = sqlite3.connect(db_uri, uri=True, timeout=10.0)
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
    
    def generate_cursor_checksum(self, token):
        """Generate checksum like JS generateCursorChecksum"""
        # Use real machine ID from storage
        machine_id = self.get_machine_id()
        if not machine_id:
            machine_id = self.generate_hashed_64_hex(token, 'machineId')
        
        timestamp = int(time.time() * 1000 // 1000000)  # Math.floor(Date.now() / 1e6)
        
        # Create byte array like JS
        byte_array = bytearray([
            (timestamp >> 40) & 255,
            (timestamp >> 32) & 255,
            (timestamp >> 24) & 255,
            (timestamp >> 16) & 255,
            (timestamp >> 8) & 255,
            timestamp & 255,
        ])
        
        # Obfuscate like JS (Jyh cipher)
        t = 165
        for i in range(len(byte_array)):
            byte_array[i] = ((byte_array[i] ^ t) + (i % 256)) & 255
            t = byte_array[i]
        
        # URL-safe base64 without padding
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
    
    def encode_message(self, content, role, message_id, chat_mode_enum=None):
        """Encode Message using exact schema"""
        msg = b''
        
        # string content = 1;
        msg += ProtobufEncoder.encode_field(1, 2, content)
        
        # int32 role = 2;
        msg += ProtobufEncoder.encode_field(2, 0, role)
        
        # string messageId = 13;
        msg += ProtobufEncoder.encode_field(13, 2, message_id)
        
        # int32 chatModeEnum = 47; // only for user message
        if chat_mode_enum is not None:
            msg += ProtobufEncoder.encode_field(47, 0, chat_mode_enum)
        
        return msg
    
    def encode_instruction(self, instruction_text):
        """Encode Instruction"""
        msg = b''
        
        # string instruction = 1;
        if instruction_text:
            msg += ProtobufEncoder.encode_field(1, 2, instruction_text)
        
        return msg
    
    def encode_model(self, model_name):
        """Encode Model"""
        msg = b''
        
        # string name = 1;
        msg += ProtobufEncoder.encode_field(1, 2, model_name)
        
        # bytes empty = 4;
        msg += ProtobufEncoder.encode_field(4, 2, b'')
        
        return msg
    
    def encode_cursor_setting(self):
        """Encode CursorSetting"""
        msg = b''
        
        # string name = 1;
        msg += ProtobufEncoder.encode_field(1, 2, "cursor\\aisettings")
        
        # bytes unknown3 = 3;
        msg += ProtobufEncoder.encode_field(3, 2, b'')
        
        # Unknown6 unknown6 = 6;
        unknown6_msg = b''
        unknown6_msg += ProtobufEncoder.encode_field(1, 2, b'')  # bytes unknown1 = 1;
        unknown6_msg += ProtobufEncoder.encode_field(2, 2, b'')  # bytes unknown2 = 2;
        msg += ProtobufEncoder.encode_field(6, 2, unknown6_msg)
        
        # int32 unknown8 = 8;
        msg += ProtobufEncoder.encode_field(8, 0, 1)
        
        # int32 unknown9 = 9;
        msg += ProtobufEncoder.encode_field(9, 0, 1)
        
        return msg
    
    def encode_metadata(self):
        """Encode Metadata"""
        msg = b''
        
        # string os = 1;
        msg += ProtobufEncoder.encode_field(1, 2, self.client_os)
        
        # string arch = 2;
        msg += ProtobufEncoder.encode_field(2, 2, self.client_arch)
        
        # string version = 3;
        msg += ProtobufEncoder.encode_field(3, 2, self.client_os_version)
        
        # string path = 4;
        msg += ProtobufEncoder.encode_field(4, 2, sys.executable or "python3")
        
        # string timestamp = 5;
        from datetime import datetime
        msg += ProtobufEncoder.encode_field(5, 2, datetime.now().isoformat())
        
        return msg
    
    def encode_message_id(self, message_id, role, summary_id=None):
        """Encode MessageId"""
        msg = b''
        
        # string messageId = 1;
        msg += ProtobufEncoder.encode_field(1, 2, message_id)
        
        # string summaryId = 2;
        if summary_id:
            msg += ProtobufEncoder.encode_field(2, 2, summary_id)
        
        # int32 role = 3;
        msg += ProtobufEncoder.encode_field(3, 0, role)
        
        return msg
    
    def encode_request(self, messages, model_name):
        """Encode Request using exact schema"""
        msg = b''
        
        # Format messages
        formatted_messages = []
        message_ids = []
        
        for i, user_msg in enumerate(messages):
            if user_msg['role'] == 'user':
                msg_id = str(uuid.uuid4())
                formatted_messages.append({
                    'content': user_msg['content'],
                    'role': 1,  # user
                    'messageId': msg_id,
                    'chatModeEnum': 1  # ask mode
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
        
        # int32 unknown27 = 27; // 0
        msg += ProtobufEncoder.encode_field(27, 0, 0)
        
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
        
        # int32 chatModeEnum = 46; // 1
        msg += ProtobufEncoder.encode_field(46, 0, 1)
        
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
        
        # string chatMode = 54;
        msg += ProtobufEncoder.encode_field(54, 2, "Ask")
        
        return msg
    
    def encode_stream_unified_chat_request(self, messages, model_name):
        """Encode StreamUnifiedChatWithToolsRequest"""
        msg = b''
        
        # Request request = 1;
        request_bytes = self.encode_request(messages, model_name)
        msg += ProtobufEncoder.encode_field(1, 2, request_bytes)
        
        return msg
    
    def generate_cursor_body_exact(self, messages, model_name):
        """Generate body exactly like JS generateCursorBody"""
        
        # Encode the protobuf message
        buffer = self.encode_stream_unified_chat_request(messages, model_name)
        
        # Apply compression logic from JS
        magic_number = 0x00
        if len(messages) >= 3:
            buffer = gzip.compress(buffer)
            magic_number = 0x01
        
        # Create final body like JS: magic_number + length (hex) + buffer
        length_hex = format(len(buffer), '08x')
        length_bytes = bytes.fromhex(length_hex)
        
        final_body = bytes([magic_number]) + length_bytes + buffer
        return final_body
    
    async def establish_session(self, auth_token, session_id, client_key, cursor_checksum):
        """Call AvailableModels first to establish session"""
        print("Establishing session...")
        
        url = f"{self.base_url}/aiserver.v1.AiService/AvailableModels"
        headers = self.build_common_headers(auth_token, session_id, client_key, cursor_checksum)
        headers["accept-encoding"] = "gzip"
        headers["content-type"] = "application/proto"
        
        async with httpx.AsyncClient(http2=False, timeout=10.0) as client:
            response = await client.post(url, headers=headers)
            if response.status_code == 401:
                refreshed = self.refresh_access_token()
                if refreshed and refreshed != auth_token:
                    headers["authorization"] = f"Bearer {refreshed}"
                    response = await client.post(url, headers=headers)
            print(f"Session: {response.status_code}")
            return response.status_code == 200
    
    async def send_chat_with_proper_protobuf(self, messages, model, auth_token, session_id, client_key, cursor_checksum):
        """Send chat with proper protobuf encoding"""
        print(f"Sending to {model} with proper protobuf...")
        
        # Generate proper protobuf body
        cursor_body = self.generate_cursor_body_exact(messages, model)
        print(f"Body size: {len(cursor_body)} bytes")
        
        url = f"{self.base_url}/aiserver.v1.ChatService/StreamUnifiedChatWithTools"
        headers = self.build_common_headers(auth_token, session_id, client_key, cursor_checksum)
        headers["connect-accept-encoding"] = "gzip"
        headers["content-type"] = "application/connect+proto"
        
        async with httpx.AsyncClient(http2=True, timeout=30.0) as client:
            try:
                async with client.stream('POST', url, headers=headers, content=cursor_body) as response:
                    if response.status_code == 401:
                        refreshed = self.refresh_access_token()
                        if refreshed and refreshed != auth_token:
                            headers["authorization"] = f"Bearer {refreshed}"
                            async with client.stream('POST', url, headers=headers, content=cursor_body) as retry_response:
                                response = retry_response
                                print(f"Status: {response.status_code}")
                                if response.status_code != 200:
                                    error = await response.aread()
                                    print(f"Error {response.status_code}: {error.decode('utf-8', errors='ignore')[:100]}")
                                    return None
                                print("SUCCESS: Streaming response:")
                                full_text = ""
                                chunk_count = 0
                                async for chunk in response.aiter_bytes():
                                    chunk_count += 1
                                    try:
                                        text = chunk.decode('utf-8', errors='ignore')
                                        if text and len(text) > 3:
                                            full_text += text
                                            print(text, end='', flush=True)
                                    except Exception:
                                        pass
                                    if len(full_text) > 1000 or chunk_count > 30:
                                        break
                                print(f"\n\nGot {chunk_count} chunks, {len(full_text)} chars total.")
                                return full_text
                    print(f"Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        print("SUCCESS: Streaming response:")
                        full_text = ""
                        chunk_count = 0
                        
                        async for chunk in response.aiter_bytes():
                            chunk_count += 1
                            
                            # Try simple text extraction
                            try:
                                text = chunk.decode('utf-8', errors='ignore')
                                if text and len(text) > 3:
                                    full_text += text
                                    print(text, end='', flush=True)
                            except Exception:
                                pass
                            
                            if len(full_text) > 1000 or chunk_count > 30:
                                break
                        
                        print(f"\n\nGot {chunk_count} chunks, {len(full_text)} chars total.")
                        return full_text
                    else:
                        error = await response.aread()
                        print(f"Error {response.status_code}: {error.decode('utf-8', errors='ignore')[:100]}")
                        
            except Exception as e:
                print(f"Exception: {str(e)}")
        
        return None
    
    async def test_proper_protobuf(self, prompt="Hello! Just say 'hi' back.", model="default"):
        """Test with proper protobuf implementation"""
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
        
        print(f"Protobuf Test")
        print(f"Using exact JavaScript protobuf schema")
        print("=" * 50)
        print(f"Session: {session_id}")
        print(f"Client Key: {client_key[:32]}...")
        
        # Establish session first
        session_ok = await self.establish_session(auth_token, session_id, client_key, cursor_checksum)
        if not session_ok:
            print("Error: Session failed")
            return None
        
        # Send chat with proper protobuf
        messages = [{"role": "user", "content": prompt}]
        result = await self.send_chat_with_proper_protobuf(
            messages, model, auth_token, session_id, client_key, cursor_checksum
        )
        
        return result

async def main():
    client = CursorProperProtobuf()
    
    result = await client.test_proper_protobuf(
        "Hello! Please just respond with 'Hi there!'",
        "default"
    )
    
    if result and len(result.strip()) > 10:
        print(f"\nSUCCESS: Got AI response.")
        print(f"Response: {result[:300]}...")
    else:
        print(f"\nNo response received.")

if __name__ == "__main__":
    asyncio.run(main())
