#!/usr/bin/env python3
"""
Simple test server to verify routes work
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.main import app
import uvicorn

if __name__ == "__main__":
    print("Starting test server on port 8001...")
    print("Routes loaded:")
    for route in app.routes:
        if hasattr(route, 'path') and 'agents' in route.path:
            methods = getattr(route, 'methods', set())
            print(f"  {methods} {route.path}")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
