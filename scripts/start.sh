#!/bin/bash
# Quick start script for Engram

set -e

echo "🧠 Starting Engram..."
echo ""

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "Running in Docker container"
    python -m engram
else
    # Check if dependencies are installed
    if ! python -c "import fastapi" 2>/dev/null; then
        echo "📦 Installing dependencies..."
        pip install -r requirements.txt
    fi
    
    echo "🚀 Starting Engram API..."
    echo "   API: http://localhost:8765"
    echo "   Docs: http://localhost:8765/docs"
    echo ""
    
    python -m engram
fi
