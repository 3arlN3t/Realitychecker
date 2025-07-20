#!/usr/bin/env python3
"""
Startup script for Reality Checker WhatsApp Bot.

This script properly sets up the Python path and starts the FastAPI server.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the Reality Checker server with proper Python path setup."""
    
    # Get the project root directory (where this script is located)
    project_root = Path(__file__).parent.absolute()
    
    # Add project root to Python path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Set PYTHONPATH environment variable
    current_pythonpath = os.environ.get('PYTHONPATH', '')
    if current_pythonpath:
        os.environ['PYTHONPATH'] = f"{project_root}:{current_pythonpath}"
    else:
        os.environ['PYTHONPATH'] = str(project_root)
    
    print(f"🚀 Starting Reality Checker WhatsApp Bot...")
    print(f"📁 Project root: {project_root}")
    print(f"🐍 Python path: {os.environ['PYTHONPATH']}")
    
    # Check if required files exist
    app_main = project_root / "app" / "main.py"
    if not app_main.exists():
        print(f"❌ Error: {app_main} not found!")
        sys.exit(1)
    
    env_file = project_root / ".env"
    if not env_file.exists():
        print(f"⚠️  Warning: {env_file} not found. Make sure environment variables are set.")
    
    # Start the server using uvicorn
    try:
        import uvicorn
        
        # Run the server
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=[str(project_root / "app")],
            log_level="info"
        )
        
    except ImportError:
        print("❌ Error: uvicorn not installed. Install it with: pip install uvicorn")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()