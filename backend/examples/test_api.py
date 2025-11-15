#!/usr/bin/env python3
"""
Writer Assistant API Test Script

This script reads JSON example files and sends requests to the Writer Assistant backend,
supporting both regular endpoints and streaming endpoints (SSE).

Usage:
    python test_api.py <json_file> [--base-url BASE_URL] [--timeout TIMEOUT]

Examples:
    python test_api.py health/health-check.json
    python test_api.py tokens/token-count-request.json --base-url http://localhost:8000
    python test_api.py ai-generation/generate-chapter-request.json --timeout 60
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class APITester:
    """Test client for Writer Assistant API endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 60):
        """
        Initialize the API tester.
        
        Args:
            base_url: Base URL of the Writer Assistant API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def load_example_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load and parse a JSON example file.
        
        Args:
            file_path: Path to the JSON example file
            
        Returns:
            Parsed JSON data
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Example file not found: {file_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in {file_path}: {e}")
    
    def is_streaming_endpoint(self, endpoint: str) -> bool:
        """
        Determine if an endpoint uses Server-Sent Events (SSE) streaming.
        
        Args:
            endpoint: The endpoint path
            
        Returns:
            True if the endpoint uses streaming, False otherwise
        """
        streaming_endpoints = [
            '/api/v1/generate-chapter',
            '/api/v1/modify-chapter',
            '/api/v1/character-feedback',
            '/api/v1/rater-feedback',
            '/api/v1/editor-review',
            '/api/v1/flesh-out',
            '/api/v1/generate-character-details',
            '/api/v1/regenerate-bio',
            '/api/v1/generate-chapter-outlines',
            '/api/v1/chat/llm'
        ]
        return any(endpoint.endswith(streaming_ep) for streaming_ep in streaming_endpoints)
    
    def send_regular_request(self, method: str, url: str, headers: Dict[str, str], 
                           body: Optional[Dict[str, Any]]) -> requests.Response:
        """
        Send a regular HTTP request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL for the request
            headers: Request headers
            body: Request body (for POST requests)
            
        Returns:
            Response object
        """
        print(f"🌐 Sending {method} request to: {url}")
        print(f"📋 Headers: {json.dumps(headers, indent=2)}")
        
        if body:
            print(f"📦 Request body: {json.dumps(body, indent=2)}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=body if body else None,
                timeout=self.timeout
            )
            return response
        except requests.exceptions.Timeout:
            print(f"⏰ Request timed out after {self.timeout} seconds")
            sys.exit(1)
        except requests.exceptions.ConnectionError:
            print(f"🔌 Connection error - is the server running at {self.base_url}?")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            sys.exit(1)
    
    def send_streaming_request(self, method: str, url: str, headers: Dict[str, str], 
                             body: Optional[Dict[str, Any]]) -> None:
        """
        Send a streaming request and handle Server-Sent Events.
        
        Args:
            method: HTTP method (should be POST for streaming endpoints)
            url: Full URL for the request
            headers: Request headers
            body: Request body
        """
        print(f"🌊 Sending streaming {method} request to: {url}")
        print(f"📋 Headers: {json.dumps(headers, indent=2)}")
        
        if body:
            print(f"📦 Request body: {json.dumps(body, indent=2)}")
        
        # Add Accept header for SSE
        streaming_headers = headers.copy()
        streaming_headers['Accept'] = 'text/event-stream'
        streaming_headers['Cache-Control'] = 'no-cache'
        
        try:
            print("\n🔄 Streaming response:")
            print("=" * 60)
            
            response = self.session.request(
                method=method,
                url=url,
                headers=streaming_headers,
                json=body if body else None,
                stream=True,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                return
            
            # Process Server-Sent Events
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith('data: '):
                        data = line[6:]  # Remove 'data: ' prefix
                        try:
                            event_data = json.loads(data)
                            self._print_streaming_event(event_data)
                        except json.JSONDecodeError:
                            print(f"📄 Raw data: {data}")
                    elif line.startswith('event: '):
                        event_type = line[7:]  # Remove 'event: ' prefix
                        print(f"🎯 Event type: {event_type}")
                    elif line.strip() == '':
                        continue  # Empty line separates events
                    else:
                        print(f"📝 SSE line: {line}")
            
            print("=" * 60)
            print("✅ Streaming completed")
            
        except requests.exceptions.Timeout:
            print(f"⏰ Streaming request timed out after {self.timeout} seconds")
            sys.exit(1)
        except requests.exceptions.ConnectionError:
            print(f"🔌 Connection error - is the server running at {self.base_url}?")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"❌ Streaming request failed: {e}")
            sys.exit(1)
    
    def _print_streaming_event(self, event_data: Dict[str, Any]) -> None:
        """
        Pretty print a streaming event.
        
        Args:
            event_data: Parsed event data
        """
        event_type = event_data.get('type', 'unknown')
        
        if event_type == 'status':
            phase = event_data.get('phase', 'unknown')
            message = event_data.get('message', '')
            progress = event_data.get('progress', 0)
            print(f"📊 Status [{phase}]: {message} ({progress}%)")
        
        elif event_type == 'result':
            print("🎉 Result received:")
            result_data = event_data.get('data', {})
            
            # Handle different result types
            if 'chapterText' in result_data:
                word_count = result_data.get('wordCount', 0)
                print(f"📖 Generated chapter ({word_count} words):")
                print("─" * 40)
                chapter_text = result_data['chapterText']
                # Show first 500 characters
                if len(chapter_text) > 500:
                    print(f"{chapter_text[:500]}...")
                    print(f"[... truncated, full text is {len(chapter_text)} characters]")
                else:
                    print(chapter_text)
                print("─" * 40)
            
            elif 'modifiedChapterText' in result_data:
                word_count = result_data.get('wordCount', 0)
                print(f"✏️ Modified chapter ({word_count} words):")
                modifications = result_data.get('modifications_applied', [])
                if modifications:
                    print("🔧 Modifications applied:")
                    for mod in modifications:
                        print(f"  • {mod}")
                print("─" * 40)
                chapter_text = result_data['modifiedChapterText']
                # Show first 500 characters
                if len(chapter_text) > 500:
                    print(f"{chapter_text[:500]}...")
                    print(f"[... truncated, full text is {len(chapter_text)} characters]")
                else:
                    print(chapter_text)
                print("─" * 40)
            
            elif 'feedback' in result_data:
                print("💭 Character feedback:")
                feedback = result_data['feedback']
                for category, items in feedback.items():
                    if items:
                        print(f"  {category.replace('_', ' ').title()}:")
                        for item in items[:3]:  # Show first 3 items
                            print(f"    • {item}")
                        if len(items) > 3:
                            print(f"    ... and {len(items) - 3} more")
            
            elif 'message' in result_data:
                message = result_data['message']
                print(f"💬 Chat response:")
                print("─" * 40)
                if isinstance(message, dict):
                    content = message.get('content', str(message))
                else:
                    content = str(message)
                print(content)
                print("─" * 40)
            
            else:
                print(f"📄 Result data: {json.dumps(result_data, indent=2)}")
        
        elif event_type == 'error':
            error_msg = event_data.get('message', 'Unknown error')
            print(f"❌ Error: {error_msg}")
        
        else:
            print(f"📦 Event [{event_type}]: {json.dumps(event_data, indent=2)}")
    
    def test_endpoint(self, example_file: str) -> None:
        """
        Test an API endpoint using an example file.
        
        Args:
            example_file: Path to the JSON example file
        """
        print(f"🧪 Testing API endpoint with: {example_file}")
        print("=" * 80)
        
        try:
            # Load the example file
            example_data = self.load_example_file(example_file)
            
            # Extract request information
            request_info = example_data.get('request', {})
            method = request_info.get('method', 'GET')
            endpoint_url = request_info.get('url', '')
            headers = request_info.get('headers', {})
            body = request_info.get('body')
            
            # Handle special case for health endpoints that might not have full URL
            if not endpoint_url.startswith('/'):
                endpoint_url = f"/api/v1/{endpoint_url}"
            
            # Construct full URL
            full_url = f"{self.base_url}{endpoint_url}"
            
            # Determine if this is a streaming endpoint
            is_streaming = self.is_streaming_endpoint(endpoint_url)
            
            print(f"📍 Endpoint: {example_data.get('endpoint', 'Unknown')}")
            print(f"📝 Description: {example_data.get('description', 'No description')}")
            print(f"🌊 Streaming: {'Yes' if is_streaming else 'No'}")
            print()
            
            # Send the request
            start_time = time.time()
            
            if is_streaming:
                self.send_streaming_request(method, full_url, headers, body)
            else:
                response = self.send_regular_request(method, full_url, headers, body)
                
                # Print response
                elapsed_time = time.time() - start_time
                print(f"\n📨 Response received in {elapsed_time:.2f}s:")
                print(f"🔢 Status Code: {response.status_code}")
                print(f"📋 Headers: {dict(response.headers)}")
                
                try:
                    response_json = response.json()
                    print(f"📄 Response Body: {json.dumps(response_json, indent=2)}")
                except json.JSONDecodeError:
                    print(f"📄 Response Body (text): {response.text}")
            
            elapsed_time = time.time() - start_time
            print(f"\n⏱️ Total time: {elapsed_time:.2f}s")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            sys.exit(1)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Test Writer Assistant API endpoints using JSON example files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_api.py health/health-check.json
  python test_api.py tokens/token-count-request.json --base-url http://localhost:8000
  python test_api.py ai-generation/generate-chapter-request.json --timeout 60
        """
    )
    
    parser.add_argument(
        'json_file',
        help='Path to the JSON example file to test'
    )
    
    parser.add_argument(
        '--base-url',
        default='http://localhost:8000',
        help='Base URL of the Writer Assistant API (default: http://localhost:8000)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        help='Request timeout in seconds (default: 60)'
    )
    
    args = parser.parse_args()
    
    # Create API tester and run the test
    tester = APITester(base_url=args.base_url, timeout=args.timeout)
    tester.test_endpoint(args.json_file)


if __name__ == '__main__':
    main()
