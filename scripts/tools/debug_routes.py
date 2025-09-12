#!/usr/bin/env python3
"""Debug script to check registered routes."""

from app.main import app

def debug_routes():
    """Print all registered routes."""
    print("Registered routes:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            print(f"  {route.methods} {route.path}")
        elif hasattr(route, 'path'):
            print(f"  {route.path}")

if __name__ == "__main__":
    debug_routes()