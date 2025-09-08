#!/usr/bin/env bash
set -euo pipefail

PORT=${1:-8000}

if ! command -v ngrok >/dev/null 2>&1; then
  echo "ngrok is not installed. Install from https://ngrok.com/download and ensure it's in your PATH." >&2
  exit 1
fi

echo "Starting ngrok tunnel for http://localhost:${PORT} ..."
echo "Press Ctrl+C to stop."

# Run ngrok in the foreground so logs stream to the console
ngrok http ${PORT}

# Usage:
#   ./scripts/ngrok_expose.sh            # defaults to port 8000
#   ./scripts/ngrok_expose.sh 8000       # explicit port
# After start, copy the https URL and set Twilio webhook to:
#   https://<your-ngrok-subdomain>.ngrok.io/webhook/whatsapp
