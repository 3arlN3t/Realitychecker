#!/bin/bash

# Reality Checker WhatsApp Bot Startup Script
# This script sets up the Python path and starts the server

echo "🚀 Starting Reality Checker WhatsApp Bot..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Project root: $SCRIPT_DIR"

# Set PYTHONPATH to include the project root
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
echo "🐍 Python path: $PYTHONPATH"

# Check if .env file exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "⚠️  Warning: .env file not found. Make sure environment variables are set."
fi

# Check if app directory exists
if [ ! -d "$SCRIPT_DIR/app" ]; then
    echo "❌ Error: app directory not found!"
    exit 1
fi

# Start the server
echo "🌐 Starting server on http://localhost:8000"
cd "$SCRIPT_DIR"

# Try to start with uvicorn
if command -v uvicorn &> /dev/null; then
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app
else
    echo "❌ Error: uvicorn not found. Install it with: pip install uvicorn"
    exit 1
fi