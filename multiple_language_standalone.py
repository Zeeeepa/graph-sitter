#!/usr/bin/env python3
"""
Standalone Chinese to English Translation Tool for Python Codebases

This tool extracts Chinese characters from Python files and translates them to English
using the web-ui-python-sdk instead of AI API calls. It creates a translated version
of the entire codebase with cached translations stored in JSON format.

Requirements:
    pip install web-ui-python-sdk

System Requirements:
    - Python 3.7+
    - tkinter (usually comes with Python)
    - web-ui-python-sdk package
    - Active internet connection for translation API

Usage:
    python multiple_language_standalone.py                           # GUI directory selection
    python multiple_language_standalone.py /path/to/repo             # CLI directory specification
    python multiple_language_standalone.py --local /path/to/repo     # Local directory translation
    python multiple_language_standalone.py --url https://github.com/user/repo  # Clone and translate

File Structure Created:
    selected_repo/
    selected_repo_translated/
        _translate_cache.json    # Translation cache file
        [all translated files]   # Translated Python files

Features:
- Interactive directory selection via GUI
- Extract Chinese characters from Python files (functions, variables, strings, comments)
- Use web-ui-python-sdk with GLM-4.5V model for translations
- Cache translations in JSON format to avoid re-translation
- Apply translations to create translated codebase
- Handle both code identifiers (CamelCase) and string literals separately
- Batch processing with random batch sizes for efficiency
- Resume capability - run multiple times to improve coverage
- Skip blacklisted directories (.git, __pycache__, etc.)

Notes:
- The tool will create a GUI dialog to select the source directory (or use CLI path)
- Translations are cached in _translate_cache.json for reuse
- Failed translations can be retried by running the script again
- Manual editing of the cache file is supported for corrections
- Code identifiers are translated using CamelCase naming convention
- String literals and comments are translated naturally

Example:
    $ pip install web-ui-python-sdk
    $ python multiple_language_standalone.py /path/to/chinese/codebase
    
    # Creates:
    # /path/to/chinese/codebase_translated/
    # /path/to/chinese/codebase_translated/_translate_cache.json
    # /path/to/chinese/codebase_translated/[all translated .py files]
"""

import os
import json
import re
import shutil
import ast
import time
import random
import uuid
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import requests
from urllib.parse import urljoin


# ============================================================================
# Embedded Z.AI SDK - Essential components only
# ============================================================================

class ZAIError(Exception):
    """Base exception for Z.AI API errors."""
    pass


class ChatCompletionResponse:
    """Complete chat completion response."""
    def __init__(self, content: str, thinking: str = "", usage: Dict = None, 
                 message_id: str = "", done: bool = True):
        self.content = content
        self.thinking = thinking
        self.usage = usage or {}
        self.message_id = message_id
        self.done = done


class HTTPClient:
    """HTTP Client for Z.AI API requests."""
    
    def __init__(self, base_url: str, timeout: int, verbose: bool = False):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verbose = verbose
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a new session with default headers."""
        session = requests.Session()
        session.headers.update({
            "accept": "*/*",
            "accept-encoding": "gzip, deflate",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "pragma": "no-cache",
            "referer": "https://chat.z.ai/",
            "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
        })
        return session
    
    def set_auth_header(self, token: str):
        """Set authorization header."""
        self.session.headers["authorization"] = f"Bearer {token}"
    
    def update_headers(self, headers: Dict[str, str]):
        """Update session headers."""
        self.session.headers.update(headers)
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    stream: bool = False) -> requests.Response:
        """Make HTTP request to API."""
        url = urljoin(self.base_url, endpoint)
        
        try:
            timeout = (30, 60) if stream else self.timeout
            
            if stream:
                headers = dict(self.session.headers)
                headers.pop('accept-encoding', None)
                response = self.session.request(
                    method=method, url=url, json=data if data else None,
                    timeout=timeout, stream=stream, headers=headers
                )
            else:
                response = self.session.request(
                    method=method, url=url, json=data if data else None,
                    timeout=timeout, stream=stream
                )
            
            if self.verbose:
                print(f"[DEBUG] Request to {url}")
                print(f"[DEBUG] Status: {response.status_code}")
            
            response.raise_for_status()
            
            if response.cookies:
                self.session.cookies.update(response.cookies)
            
            return response
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.text
                    error_msg += f" - Response: {error_detail}"
                except:
                    pass
            raise ZAIError(error_msg)


class AuthManager:
    """Manages authentication for Z.AI API."""
    
    def __init__(self, http_client: HTTPClient):
        self.http_client = http_client
        self.token: Optional[str] = None
        self.auth_data: Optional[Dict] = None
    
    def get_guest_token(self) -> str:
        """Get a guest token from Z.AI auth endpoint."""
        try:
            response = self.http_client.make_request("GET", "/api/v1/auths/")
            auth_data = response.json()
            token = auth_data.get("token")
            
            if not token:
                raise ZAIError("No token found in auth response")
            
            self.auth_data = auth_data
            self.token = token
            return token
            
        except Exception as e:
            raise ZAIError(f"Failed to get guest token: {e}")
    
    def set_token(self, token: str):
        """Set authentication token."""
        self.token = token
        self.http_client.set_auth_header(token)
    
    def get_auth_data(self) -> Optional[Dict]:
        """Get stored authentication data."""
        return self.auth_data


class ZAIClient:
    """Z.AI API Client - Simplified version for translation."""
    
    def __init__(self, token: str = None, base_url: str = "https://chat.z.ai", 
                 timeout: int = 180, auto_auth: bool = True, verbose: bool = False):
        self.base_url = base_url
        self.timeout = timeout
        self.verbose = verbose
        
        self.http_client = HTTPClient(base_url, timeout, verbose=verbose)
        self.auth_manager = AuthManager(self.http_client)
        
        if not token and auto_auth:
            token = self.auth_manager.get_guest_token()
        
        if token:
            self.auth_manager.set_token(token)
    
    @property
    def token(self) -> Optional[str]:
        """Get current authentication token."""
        return self.auth_manager.token
    
    def simple_chat(self, message: str, model: str = "glm-4.5v", 
                   enable_thinking: bool = True, chat_title: str = "Simple Chat",
                   temperature: float = None, top_p: float = None,
                   max_tokens: int = None) -> ChatCompletionResponse:
        """Simple one-shot chat completion."""
        chat_id = str(uuid.uuid4())
        message_id = str(uuid.uuid4())
        timestamp = int(time.time())
        
        # Build chat creation payload
        chat_payload = {
            "chat": {
                "id": "",
                "title": chat_title,
                "models": [model],
                "params": {},
                "history": {
                    "messages": {
                        message_id: {
                            "id": message_id,
                            "parentId": None,
                            "childrenIds": [],
                            "role": "user",
                            "content": message,
                            "timestamp": timestamp,
                            "models": [model]
                        }
                    },
                    "currentId": message_id
                },
                "messages": [{
                    "id": message_id,
                    "parentId": None,
                    "childrenIds": [],
                    "role": "user",
                    "content": message,
                    "timestamp": timestamp,
                    "models": [model]
                }],
                "tags": [],
                "flags": [],
                "features": [
                    {"type": "mcp", "server": "vibe-coding", "status": "hidden"},
                    {"type": "mcp", "server": "ppt-maker", "status": "hidden"},
                    {"type": "mcp", "server": "image-search", "status": "hidden"}
                ],
                "mcp_servers": [],
                "enable_thinking": enable_thinking,
                "timestamp": int(time.time() * 1000)
            }
        }
        
        self.http_client.update_headers({"x-fe-version": "prod-fe-1.0.70"})
        
        try:
            # Create chat
            response = self.http_client.make_request("POST", "/api/v1/chats/new", chat_payload)
            chat_data = response.json()
            actual_chat_id = chat_data.get("id")
            
            if not actual_chat_id:
                raise ZAIError("Failed to create chat - no chat ID returned")
            
            # Get completion via streaming (simplified - just collect all content)
            completion_payload = {
                "model": model,
                "messages": [{"role": "user", "content": message}],
                "params": {},
                "features": {
                    "image_generation": False,
                    "web_search": False,
                    "auto_web_search": False,
                    "preview_mode": True,
                    "flags": [],
                    "features": [
                        {"type": "mcp", "server": "vibe-coding", "status": "hidden"},
                        {"type": "mcp", "server": "ppt-maker", "status": "hidden"},
                        {"type": "mcp", "server": "image-search", "status": "hidden"}
                    ],
                    "enable_thinking": enable_thinking
                },
                "variables": {
                    "{{USER_NAME}}": "Guest",
                    "{{USER_LOCATION}}": "Unknown",
                    "{{CURRENT_DATETIME}}": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
                "model_item": {
                    "id": model,
                    "name": model.upper(),
                    "owned_by": "openai",
                    "info": {
                        "id": model,
                        "params": {
                            "temperature": temperature if temperature is not None else 0.8,
                            "top_p": top_p if top_p is not None else 0.6,
                            "max_tokens": max_tokens if max_tokens is not None else 80000
                        }
                    }
                },
                "chat_id": actual_chat_id,
                "id": str(uuid.uuid4())
            }
            
            # Add optional parameters to params dict
            if temperature is not None:
                completion_payload["params"]["temperature"] = temperature
            if top_p is not None:
                completion_payload["params"]["top_p"] = top_p  
            if max_tokens is not None:
                completion_payload["params"]["max_tokens"] = max_tokens
            
            # Update referer header  
            original_referer = self.http_client.session.headers.get("referer")
            self.http_client.session.headers["referer"] = f"https://chat.z.ai/c/{actual_chat_id}"
            
            try:
                # Make streaming request and collect response
                response = self.http_client.make_request(
                    "POST", 
                    "/api/chat/completions", 
                    completion_payload,
                    stream=True
                )
                
                content = ""
                thinking = ""
                current_phase = None
                
                # Process streaming response  
                line_count = 0
                for line in response.iter_lines():
                    line_count += 1
                        
                    if line:
                        # Decode bytes to string if needed
                        if isinstance(line, bytes):
                            line = line.decode('utf-8')
                        line = line.strip()
                        if not line or line.startswith(":"):
                            continue
                            
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip():
                                try:
                                    data = json.loads(data_str)
                                    
                                    # Extract the actual data from the wrapper
                                    if 'data' in data and isinstance(data['data'], dict):
                                        actual_data = data['data']
                                        
                                        # Handle phase information
                                        if 'phase' in actual_data:
                                            current_phase = actual_data['phase']
                                        
                                        # Handle complete message content (first response with choices)
                                        if 'choices' in actual_data and len(actual_data['choices']) > 0:
                                            choice = actual_data['choices'][0]
                                            if 'message' in choice:
                                                message = choice['message']
                                                if 'content' in message:
                                                    msg_content = message['content']
                                                    # Remove box markers if present
                                                    msg_content = msg_content.replace('<|begin_of_box|>', '').replace('<|end_of_box|>', '')
                                                    content = msg_content  # Replace, don't append
                                                if 'reasoning_content' in message:
                                                    reasoning = message['reasoning_content']
                                                    thinking = reasoning  # Replace, don't append
                                        
                                        # Check for done signal
                                        if actual_data.get('done', False):
                                            break
                                        
                                except json.JSONDecodeError:
                                    continue
                    
                    # Add safety break for long streams
                    if line_count > 1000:
                        break
            
                return ChatCompletionResponse(
                    content=content.strip(),
                    thinking=thinking.strip(),
                    usage={},
                    message_id=str(uuid.uuid4()),
                    done=True
                )
            finally:
                # Restore original referer
                if original_referer:
                    self.http_client.session.headers["referer"] = original_referer
            
        except Exception as e:
            raise ZAIError(f"Simple chat failed: {e}")


# ============================================================================
# End of Embedded Z.AI SDK
# ============================================================================


class ChineseTranslator:
    """Main translator class that handles the entire translation workflow"""
    
    def __init__(self):
        self.blacklist = [
            'multi-language', '.git', 'private_upload', 'build', '.github', 
            '.vscode', '__pycache__', 'venv', '.env', 'node_modules', 'dist',
            '__pycache__', '.pyc', '_translated', '_translate_cache.json'
        ]
        self.client = None
        self.translation_cache = {}
        self.cache_file_path = None
        
    def init_client(self):
        """Initialize the embedded ZAI client"""
        try:
            # Initialize the embedded client
            self.client = ZAIClient(auto_auth=True, verbose=False)
            print(f"Successfully initialized ZAI client with token: {self.client.token[:20] if self.client.token else 'None'}...")
            return True
        except Exception as e:
            print(f"Error initializing ZAI client: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def clone_repository(self, url: str, target_dir: str = None) -> str:
        """Clone a repository from URL"""
        try:
            # Extract repository name from URL
            repo_name = url.rstrip('/').split('/')[-1]
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            
            # Use provided target directory or current directory
            if target_dir is None:
                target_dir = os.getcwd()
            
            clone_path = os.path.join(target_dir, repo_name)
            
            # Remove existing directory if it exists
            if os.path.exists(clone_path):
                print(f"Removing existing directory: {clone_path}")
                shutil.rmtree(clone_path)
            
            # Clone the repository
            print(f"Cloning repository from {url}...")
            result = subprocess.run(['git', 'clone', url, clone_path], 
                                 capture_output=True, text=True, check=True)
            
            print(f"Successfully cloned to: {clone_path}")
            return clone_path
            
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e}")
            print(f"Git output: {e.stderr}")
            return None
        except Exception as e:
            print(f"Unexpected error during cloning: {e}")
            return None
    
    def select_directory(self, cli_path: str = None) -> str:
        """Let user select a directory to translate"""
        if cli_path and os.path.isdir(cli_path):
            return cli_path
            
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        directory = filedialog.askdirectory(
            title="Select the codebase directory to translate"
        )
        
        root.destroy()
        return directory
    
    def contains_chinese(self, text: str) -> bool:
        """Check if text contains Chinese characters"""
        chinese_regex = re.compile(r'[\u4e00-\u9fff]+')
        return chinese_regex.search(text) is not None
    
    def extract_chinese_from_file(self, file_path: str) -> Tuple[List[str], List[str]]:
        """
        Extract Chinese characters from a Python file
        Returns tuple of (identifiers, string_literals)
        """
        identifiers = []
        string_literals = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST for identifiers
            try:
                root = ast.parse(content)
                for node in ast.walk(root):
                    # Function and class names
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        if self.contains_chinese(node.name):
                            identifiers.append(node.name)
                    
                    # Variable names
                    elif isinstance(node, ast.Name):
                        if self.contains_chinese(node.id):
                            identifiers.append(node.id)
                    
                    # Import names
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            if self.contains_chinese(alias.name):
                                identifiers.append(alias.name)
                    
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and self.contains_chinese(node.module):
                            identifiers.append(node.module)
                        for alias in node.names:
                            if self.contains_chinese(alias.name):
                                identifiers.append(alias.name)
                    
                    # String literals
                    elif isinstance(node, ast.Str):
                        if self.contains_chinese(node.s):
                            string_literals.append(node.s)
                    
                    # For Python 3.8+
                    elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                        if self.contains_chinese(node.value):
                            string_literals.append(node.value)
            
            except SyntaxError:
                print(f"Syntax error in file: {file_path}, skipping AST parsing")
            
            # Extract comments
            for line_no, line in enumerate(content.splitlines(), 1):
                comment_match = re.search(r'#.*$', line)
                if comment_match:
                    comment = comment_match.group(0)
                    if self.contains_chinese(comment):
                        string_literals.append(comment)
        
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
        
        return identifiers, string_literals
    
    def extract_chinese_from_directory(self, directory_path: str) -> Tuple[Set[str], Set[str]]:
        """
        Extract all Chinese characters from Python files in directory
        Returns tuple of (unique_identifiers, unique_string_literals)
        """
        all_identifiers = set()
        all_string_literals = set()
        
        print(f"Scanning directory: {directory_path}")
        
        for root, dirs, files in os.walk(directory_path):
            # Skip blacklisted directories
            dirs[:] = [d for d in dirs if not any(blacklisted in d for blacklisted in self.blacklist)]
            
            if any(blacklisted in root for blacklisted in self.blacklist):
                continue
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    print(f"Processing: {file_path}")
                    identifiers, string_literals = self.extract_chinese_from_file(file_path)
                    all_identifiers.update(identifiers)
                    all_string_literals.update(string_literals)
        
        print(f"Found {len(all_identifiers)} unique Chinese identifiers")
        print(f"Found {len(all_string_literals)} unique Chinese string literals")
        
        return all_identifiers, all_string_literals
    
    def load_cache(self, cache_file: str) -> Dict[str, str]:
        """Load translation cache from JSON file"""
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    # Filter out None values and ensure keys contain Chinese
                    return {k: v for k, v in cache.items() 
                           if v is not None and self.contains_chinese(k)}
            except Exception as e:
                print(f"Error loading cache: {e}")
        return {}
    
    def save_cache(self, cache_file: str, cache_data: Dict[str, str]):
        """Save translation cache to JSON file"""
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def translate_with_sdk(self, texts: List[str], is_identifier: bool = False) -> Dict[str, str]:
        """
        Translate texts using web-ui-python-sdk
        
        Args:
            texts: List of Chinese texts to translate
            is_identifier: True if translating code identifiers (use CamelCase)
        
        Returns:
            Dictionary mapping original text to translated text
        """
        if not texts:
            return {}
        
        if not self.client:
            print("Error: SDK client not initialized")
            return {}
        
        translations = {}
        
        # Split into batches to avoid overwhelming the API
        batch_size = random.randint(8, 16)  # Random batch size like original
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            print(f"Translating batch {i//batch_size + 1}: {len(batch)} items")
            
            try:
                if is_identifier:
                    # For identifiers, use CamelCase naming convention
                    prompt = f"""Translate the following Chinese programming identifiers to English using CamelCase naming convention.
Return only the translations in the same order, one per line.
Do not include explanations, numbers, or extra text.

Chinese identifiers to translate:
{json.dumps(batch, ensure_ascii=False)}"""
                else:
                    # For string literals and comments
                    prompt = f"""Translate the following Chinese text to English.
Return the translations in JSON format: {{"original_text": "translated_text"}}
Keep the same number of items and maintain the structure.

Chinese texts to translate:
{json.dumps(batch, ensure_ascii=False)}"""
                
                response = self.client.simple_chat(
                    message=prompt,
                    model="glm-4.5v",  # Use the recommended model
                    temperature=0.3    # Lower temperature for more consistent translation
                )
                
                if response and hasattr(response, 'content'):
                    result = response.content.strip()
                    
                    if is_identifier:
                        # Parse line-by-line results for identifiers
                        translated_lines = [line.strip() for line in result.split('\n') if line.strip()]
                        for orig, trans in zip(batch, translated_lines):
                            # Clean up the translation (remove quotes, extra characters)
                            clean_trans = re.sub(r'^["\']|["\']$', '', trans)
                            clean_trans = re.sub(r'[^a-zA-Z0-9_]', '', clean_trans)
                            if clean_trans:
                                translations[orig] = clean_trans
                            else:
                                translations[orig] = None
                    else:
                        # Parse JSON results for string literals
                        try:
                            json_result = json.loads(result)
                            # Ensure we only add string values
                            for key, value in json_result.items():
                                if isinstance(value, str):
                                    translations[key] = value
                                elif isinstance(value, list) and len(value) == 1 and isinstance(value[0], str):
                                    translations[key] = value[0]  # Take first item if it's a single-item list
                                else:
                                    translations[key] = None
                        except json.JSONDecodeError:
                            # Fallback: try to parse as simple mapping
                            for orig in batch:
                                translations[orig] = None
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error translating batch: {e}")
                # Mark all items in batch as failed
                for item in batch:
                    translations[item] = None
        
        return translations
    
    def get_missing_translations(self, all_texts: Set[str], cache: Dict[str, str]) -> List[str]:
        """Get list of texts that need translation"""
        missing = []
        for text in all_texts:
            if text not in cache or cache[text] is None:
                missing.append(text)
        return missing
    
    def translate_codebase(self, source_dir: str, target_dir: str):
        """Apply translations to create translated codebase"""
        print(f"Creating translated codebase at: {target_dir}")
        
        # Copy entire directory structure
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        
        def ignore_function(dir, files):
            ignored = []
            for item in files:
                if any(blacklisted in item for blacklisted in self.blacklist):
                    ignored.append(item)
            return ignored
        
        shutil.copytree(source_dir, target_dir, ignore=ignore_function)
        
        # Sort cache by length (longest first) for proper replacement
        sorted_cache = dict(sorted(self.translation_cache.items(), key=lambda x: -len(x[0])))
        
        # Apply translations to all Python files
        for root, dirs, files in os.walk(target_dir):
            # Skip blacklisted directories
            dirs[:] = [d for d in dirs if not any(blacklisted in d for blacklisted in self.blacklist)]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self.translate_file(file_path, sorted_cache)
    
    def translate_file(self, file_path: str, translation_cache: Dict[str, str]):
        """Apply translations to a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply translations
            for chinese_text, english_text in translation_cache.items():
                if english_text is None:
                    continue
                    
                # Ensure english_text is a string
                if not isinstance(english_text, str):
                    print(f"Warning: Translation for '{chinese_text}' is not a string: {type(english_text)}, skipping")
                    continue
                
                # Handle quotes in translations
                safe_translation = english_text
                if '"' in safe_translation:
                    safe_translation = safe_translation.replace('"', '`')
                if "'" in safe_translation:
                    safe_translation = safe_translation.replace("'", '`')
                
                content = content.replace(chinese_text, safe_translation)
            
            # Only write if content changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Translated: {file_path}")
        
        except Exception as e:
            print(f"Error translating file {file_path}: {e}")
    
    def run(self, cli_path: str = None):
        """Main execution function"""
        print("Chinese to English Translation Tool for Python Codebases")
        print("=" * 60)
        
        # Initialize SDK client
        if not self.init_client():
            return
        
        # Select source directory
        source_dir = self.select_directory(cli_path)
        if not source_dir:
            print("No directory selected. Exiting.")
            return
        
        print(f"Selected directory: {source_dir}")
        
        # Setup target directory and cache file
        source_path = Path(source_dir)
        target_dir = str(source_path.parent / f"{source_path.name}_translated")
        self.cache_file_path = os.path.join(target_dir, "_translate_cache.json")
        
        # Create target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)
        
        # Load existing cache
        self.translation_cache = self.load_cache(self.cache_file_path)
        print(f"Loaded {len(self.translation_cache)} cached translations")
        
        # Extract Chinese characters
        identifiers, string_literals = self.extract_chinese_from_directory(source_dir)
        
        # Get missing translations for identifiers
        missing_identifiers = self.get_missing_translations(identifiers, self.translation_cache)
        if missing_identifiers:
            print(f"\nTranslating {len(missing_identifiers)} code identifiers...")
            identifier_translations = self.translate_with_sdk(missing_identifiers, is_identifier=True)
            self.translation_cache.update(identifier_translations)
            self.save_cache(self.cache_file_path, self.translation_cache)
        
        # Get missing translations for string literals
        missing_literals = self.get_missing_translations(string_literals, self.translation_cache)
        if missing_literals:
            print(f"\nTranslating {len(missing_literals)} string literals...")
            literal_translations = self.translate_with_sdk(missing_literals, is_identifier=False)
            self.translation_cache.update(literal_translations)
            self.save_cache(self.cache_file_path, self.translation_cache)
        
        # Create translated codebase
        print(f"\nApplying translations...")
        self.translate_codebase(source_dir, target_dir)
        
        print(f"\n✓ Translation completed!")
        print(f"✓ Translated codebase: {target_dir}")
        print(f"✓ Translation cache: {self.cache_file_path}")
        print(f"✓ Total cached translations: {len(self.translation_cache)}")
        
        # Show statistics
        successful_translations = sum(1 for v in self.translation_cache.values() if v is not None)
        failed_translations = len(self.translation_cache) - successful_translations
        print(f"✓ Successful translations: {successful_translations}")
        if failed_translations > 0:
            print(f"⚠ Failed translations: {failed_translations}")
            print("  (You can run the script again to retry failed translations)")


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(
        description="Standalone Chinese to English Translation Tool for Python Codebases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # GUI directory selection
  python multiple_language_standalone.py
  
  # Local directory translation
  python multiple_language_standalone.py --local /path/to/repo
  python multiple_language_standalone.py /path/to/repo  # shorthand
  
  # Clone and translate from URL
  python multiple_language_standalone.py --url https://github.com/user/repo
  python multiple_language_standalone.py --url https://github.com/binary-husky/gpt_academic
        """)
    
    parser.add_argument('path', nargs='?', help='Directory path to translate (shorthand for --local)')
    parser.add_argument('--local', help='Local directory path to translate')  
    parser.add_argument('--url', help='Git repository URL to clone and translate')
    
    args = parser.parse_args()
    
    translator = ChineseTranslator()
    source_dir = None
    
    try:
        # Determine source directory
        if args.url:
            print("=" * 60)
            print("Chinese to English Translation Tool for Python Codebases") 
            print("=" * 60)
            source_dir = translator.clone_repository(args.url)
            if not source_dir:
                print("Failed to clone repository. Exiting.")
                return
        elif args.local:
            if not os.path.isdir(args.local):
                print(f"Error: '{args.local}' is not a valid directory")
                return
            source_dir = args.local
        elif args.path:
            if not os.path.isdir(args.path):
                print(f"Error: '{args.path}' is not a valid directory")
                return  
            source_dir = args.path
        
        # Run translation
        translator.run(source_dir)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()