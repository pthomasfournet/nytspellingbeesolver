#!/bin/bash
# Start web server - ensures only one instance runs

echo "🔍 Checking for existing server instances..."

# Kill any existing uvicorn processes (force kill with -9)
pkill -9 -f "uvicorn web_server:app" 2>/dev/null && echo "✓ Stopped existing server" || echo "✓ No existing server found"

# Also check for anything on port 8000
if lsof -i:8000 -t >/dev/null 2>&1; then
    echo "⚠️  Port 8000 still in use, force killing..."
    kill -9 $(lsof -i:8000 -t) 2>/dev/null
fi

# Wait for port to be released
sleep 2

# Start fresh server
echo "🚀 Starting web server..."
python3 -m uvicorn web_server:app --host 0.0.0.0 --port 8000 --reload

# Note: Script runs in foreground so you can Ctrl+C to stop
