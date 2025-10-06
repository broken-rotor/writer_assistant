"""
Minimal FastAPI application for Writer Assistant
Run with: python simple_main.py
"""
import asyncio
import json
import os
from typing import List, Dict, Any
from datetime import datetime
import uuid

# Simple in-memory storage for development
stories_storage = {}

class Story:
    def __init__(self, title: str, genre: str, description: str = ""):
        self.id = str(uuid.uuid4())
        self.title = title
        self.genre = genre
        self.description = description
        self.user_id = "default_user"
        self.current_phase = "outline_development"
        self.status = "draft"
        self.outline = None
        self.chapters = []
        self.characters = []
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
        self.progress = {
            "outline_approved": False,
            "chapters_completed": 0,
            "total_chapters_planned": 0,
            "overall_progress": 0.0
        }

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "genre": self.genre,
            "description": self.description,
            "user_id": self.user_id,
            "current_phase": self.current_phase,
            "status": self.status,
            "outline": self.outline,
            "chapters": self.chapters,
            "characters": self.characters,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "progress": self.progress
        }

# Simple HTTP server without external dependencies
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json

class WriterAssistantHandler(BaseHTTPRequestHandler):
    def _send_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        response = {
            "success": True,
            "data": data,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0"
            }
        }
        self.wfile.write(json.dumps(response, indent=2).encode())

    def _send_error(self, message, status_code=400):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response = {
            "success": False,
            "error": message,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0"
            }
        }
        self.wfile.write(json.dumps(response, indent=2).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/':
            self._send_response({"message": "Writer Assistant API", "version": "1.0.0"})
        elif self.path == '/health':
            self._send_response({"status": "healthy"})
        elif self.path == '/api/v1/stories/':
            stories_list = [story.to_dict() for story in stories_storage.values()]
            self._send_response(stories_list)
        elif self.path.startswith('/api/v1/stories/') and len(self.path.split('/')) == 5:
            story_id = self.path.split('/')[-1]
            if story_id in stories_storage:
                self._send_response(stories_storage[story_id].to_dict())
            else:
                self._send_error("Story not found", 404)
        else:
            self._send_error("Not found", 404)

    def do_POST(self):
        if self.path == '/api/v1/stories/':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                story = Story(
                    title=data.get('title', 'Untitled'),
                    genre=data.get('genre', 'general'),
                    description=data.get('description', '')
                )
                stories_storage[story.id] = story
                self._send_response(story.to_dict())
            except Exception as e:
                self._send_error(f"Invalid data: {str(e)}")
        else:
            self._send_error("Not found", 404)

    def do_DELETE(self):
        if self.path.startswith('/api/v1/stories/') and len(self.path.split('/')) == 5:
            story_id = self.path.split('/')[-1]
            if story_id in stories_storage:
                del stories_storage[story_id]
                self._send_response({"message": "Story deleted successfully"})
            else:
                self._send_error("Story not found", 404)
        else:
            self._send_error("Not found", 404)

def run_server():
    server_address = ('localhost', 8000)
    httpd = HTTPServer(server_address, WriterAssistantHandler)
    print(f"Writer Assistant API server running on http://{server_address[0]}:{server_address[1]}")
    print("Endpoints available:")
    print("  GET  /                     - API info")
    print("  GET  /health               - Health check")
    print("  GET  /api/v1/stories/      - List all stories")
    print("  POST /api/v1/stories/      - Create new story")
    print("  GET  /api/v1/stories/{id}  - Get specific story")
    print("  DELETE /api/v1/stories/{id} - Delete story")
    print("\nPress Ctrl+C to stop the server")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down the server...")
        httpd.shutdown()

if __name__ == '__main__':
    run_server()