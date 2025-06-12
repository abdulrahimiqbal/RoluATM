#!/usr/bin/env python3
"""
Simple HTTP server for RoluATM Kiosk App
Serves the built React app on localhost:3000
"""

import os
import sys
import http.server
import socketserver
from pathlib import Path

# Configuration
PORT = 3000
DIST_DIR = "/home/rahiim/RoluATM/kiosk-app/dist"

class KioskHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for the kiosk app"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIST_DIR, **kwargs)
    
    def end_headers(self):
        # Add CORS headers for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def log_message(self, format, *args):
        # Simple logging
        print(f"[{self.address_string()}] {format % args}")

def main():
    """Start the kiosk HTTP server"""
    
    # Check if dist directory exists
    if not os.path.exists(DIST_DIR):
        print(f"❌ Error: Dist directory not found: {DIST_DIR}")
        print("Please build the kiosk app first with: npm run build")
        sys.exit(1)
    
    # Check if index.html exists
    index_file = os.path.join(DIST_DIR, "index.html")
    if not os.path.exists(index_file):
        print(f"❌ Error: index.html not found: {index_file}")
        sys.exit(1)
    
    print(f"🚀 Starting RoluATM Kiosk Server...")
    print(f"📁 Serving directory: {DIST_DIR}")
    print(f"🌐 Server URL: http://localhost:{PORT}")
    print(f"🔄 Press Ctrl+C to stop")
    
    try:
        with socketserver.TCPServer(("", PORT), KioskHTTPRequestHandler) as httpd:
            print(f"✅ Server started successfully on port {PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"❌ Error: Port {PORT} is already in use")
            print("Please stop any existing server or use a different port")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 