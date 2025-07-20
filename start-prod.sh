#!/bin/bash

# Start the application in production mode

echo "Starting application in production mode..."

# Start the FastAPI server
cd /Users/otsilekole/Desktop/Realitychecker
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Start the dashboard
cd /Users/otsilekole/Desktop/Realitychecker/dashboard
npm start &