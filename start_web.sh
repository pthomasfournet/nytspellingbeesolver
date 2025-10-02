#!/bin/bash
# Start web server - ensures only one instance runs

echo "🔍 Checking for existing server instances..."

# Kill any existing uvicorn processes
pkill -f "uvicorn web_server:app" 2>/dev/null && echo "✓ Stopped existing server" || echo "✓ No existing server found"

# Wait a moment for processes to clean up
sleep 1

# Start fresh server
echo "🚀 Starting web server..."
python3 -m uvicorn web_server:app --host 0.0.0.0 --port 8000 --reload

# Note: Script runs in foreground so you can Ctrl+C to stop
