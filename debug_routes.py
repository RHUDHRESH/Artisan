#!/usr/bin/env python3
"""
Debug script to test the backend routes directly
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.main import app

def list_routes():
    print("=== Available Routes ===")
    for route in app.routes:
        if hasattr(route, 'path'):
            methods = getattr(route, 'methods', set())
            print(f"{methods} {route.path}")

def test_agent_routes():
    agent_routes = [r for r in app.routes if hasattr(r, 'path') and 'agents' in r.path]
    print(f"\n=== Agent Routes Found: {len(agent_routes)} ===")
    for route in agent_routes:
        methods = getattr(route, 'methods', set())
        print(f"{methods} {route.path}")

if __name__ == "__main__":
    list_routes()
    test_agent_routes()
