#!/usr/bin/env python3
"""
Cursor Authentication Token Reader
Reads the stored authentication tokens from Cursor's local storage
Updated for Cursor 1.3.7 with embedded AI key support
"""

import os
import json
import sqlite3
import platform
from pathlib import Path
from typing import Optional, Dict

from constants import CURSOR_EMBEDDED_AI_KEY


class CursorAuthReader:
    """Read Cursor's stored authentication tokens"""
    
    def __init__(self):
        self.cursor_data_path = self._find_cursor_data_path()
        self.storage_path = None
        if self.cursor_data_path:
            # Try different possible storage locations
            # Prefer SQLite database over JSON
            possible_paths = [
                self.cursor_data_path / "globalStorage" / "state.vscdb",
                self.cursor_data_path / "storage" / "state.vscdb",
                self.cursor_data_path / "state.vscdb",
                self.cursor_data_path / "globalStorage" / "storage.json",
            ]
            for path in possible_paths:
                if path.exists():
                    self.storage_path = path
                    break
    
    def _find_cursor_data_path(self) -> Optional[Path]:
        """Find Cursor's user data directory based on the platform"""
        system = platform.system()
        home = Path.home()
        
        if system == "Linux":
            # Linux paths
            paths = [
                home / ".config" / "Cursor" / "User",
                home / ".config" / "cursor" / "User",
                home / ".cursor" / "User",
            ]
        elif system == "Darwin":  # macOS
            paths = [
                home / "Library" / "Application Support" / "Cursor" / "User",
                home / "Library" / "Application Support" / "cursor" / "User",
            ]
        elif system == "Windows":
            paths = [
                home / "AppData" / "Roaming" / "Cursor" / "User",
                home / "AppData" / "Roaming" / "cursor" / "User",
            ]
        else:
            print(f"Unsupported platform: {system}")
            return None
        
        # Check which path exists
        for path in paths:
            if path.exists():
                return path
                
        # Also check for globalStorage directly
        for base_path in paths:
            parent = base_path.parent
            if parent.exists():
                return parent
        
        return None
    
    def read_json_storage(self) -> Optional[Dict]:
        """Read storage from JSON file"""
        if not self.storage_path or self.storage_path.suffix != '.json':
            return None
            
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading JSON storage: {e}")
            return None
    
    def read_sqlite_storage(self) -> Optional[Dict]:
        """Read storage from SQLite database"""
        if not self.storage_path or self.storage_path.suffix != '.vscdb':
            return None
            
        try:
            conn = sqlite3.connect(str(self.storage_path))
            cursor = conn.cursor()
            
            # Try different table names that might store the data
            tables = ['ItemTable', 'cursorDiskKV']
            storage_data = {}
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT key, value FROM {table}")
                    for key, value in cursor.fetchall():
                        if key and isinstance(key, str) and key.startswith('cursorAuth/'):
                            # Value might be bytes or string
                            if isinstance(value, bytes):
                                value = value.decode('utf-8')
                            # Try to parse as JSON, otherwise use as string
                            try:
                                storage_data[key] = json.loads(value)
                            except:
                                storage_data[key] = value
                except sqlite3.Error as e:
                    continue
            
            conn.close()
            return storage_data
        except Exception as e:
            print(f"Error reading SQLite storage: {e}")
            return None
    
    def get_auth_tokens(self) -> Dict[str, Optional[str]]:
        """Get all authentication tokens"""
        tokens = {
            'access_token': None,
            'refresh_token': None,
            'openai_key': None,
            'claude_key': None,
            'google_key': None,
            'email': None,
            'stripe_customer_id': None,
            'membership_type': None,
            'embedded_ai_key': CURSOR_EMBEDDED_AI_KEY,
        }
        
        if not self.storage_path:
            print("Could not find Cursor storage path")
            return tokens
        
        print(f"Found storage at: {self.storage_path}")
        
        # Try reading based on file type
        if self.storage_path.suffix == '.json':
            storage_data = self.read_json_storage()
        else:
            storage_data = self.read_sqlite_storage()
        
        if not storage_data:
            print("Could not read storage data")
            return tokens
        
        # Extract tokens
        key_mappings = {
            'cursorAuth/accessToken': 'access_token',
            'cursorAuth/refreshToken': 'refresh_token',
            'cursorAuth/openAIKey': 'openai_key',
            'cursorAuth/claudeKey': 'claude_key',
            'cursorAuth/googleKey': 'google_key',
            'cursorAuth/cachedEmail': 'email',
            'cursorAuth/stripeCustomerId': 'stripe_customer_id',
            'cursorAuth/stripeMembershipType': 'membership_type',
        }
        
        for storage_key, token_key in key_mappings.items():
            if storage_key in storage_data:
                tokens[token_key] = storage_data[storage_key]
        
        return tokens
    
    def get_bearer_token(self) -> Optional[str]:
        """Get just the bearer token for API access"""
        tokens = self.get_auth_tokens()
        return tokens.get('access_token')
    
    def get_embedded_ai_key(self) -> str:
        """Get the embedded AI key used in Cursor 1.3.7+"""
        return CURSOR_EMBEDDED_AI_KEY


def main():
    """Main function to demonstrate usage"""
    reader = CursorAuthReader()
    
    if not reader.cursor_data_path:
        print("Error: Could not find Cursor data directory")
        print("\nPossible locations:")
        print("  Linux: ~/.config/Cursor/User")
        print("  macOS: ~/Library/Application Support/Cursor/User")
        print("  Windows: %APPDATA%\\Cursor\\User")
        return
    
    print(f"Found Cursor data at: {reader.cursor_data_path}")
    
    # Get all tokens
    tokens = reader.get_auth_tokens()
    
    print("\nAuthentication Status:")
    print(f"  Email: {tokens['email'] or 'Not found'}")
    print(f"  Access Token: {'Found' if tokens['access_token'] else 'Not found'}")
    print(f"  Refresh Token: {'Found' if tokens['refresh_token'] else 'Not found'}")
    print(f"  Membership: {tokens['membership_type'] or 'Unknown'}")
    print(f"  Embedded AI Key: Available")
    
    if tokens['access_token']:
        print(f"\nBearer Token (first 20 chars): {tokens['access_token'][:20]}...")
        print("\nFor API usage:")
        print(f"   bearer_token = '{tokens['access_token']}'")
    else:
        print("\nNo access token found. Make sure you're logged into Cursor.")
    
    # Show API keys if present
    print("\nAPI Keys:")
    for key_name in ['openai_key', 'claude_key', 'google_key']:
        if tokens[key_name]:
            print(f"  {key_name}: {'Found' if tokens[key_name] else 'Not found'}")


if __name__ == "__main__":
    main()