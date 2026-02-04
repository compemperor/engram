#!/bin/bash
# Learning Session Helper - Maintains session_id across operations
# Usage: ./learning-session-helper.sh start|note|verify|consolidate

API="http://localhost:8765"
SESSION_FILE="/tmp/current-learning-session.txt"

case "$1" in
  start)
    topic="$2"
    goal="$3"
    duration="${4:-10}"
    
    # URL encode parameters
    topic_encoded=$(printf %s "$topic" | jq -sRr @uri)
    goal_encoded=$(printf %s "$goal" | jq -sRr @uri)
    
    response=$(curl -s -X POST "$API/learning/session/start?topic=$topic_encoded&goal=$goal_encoded&target_duration_min=$duration")
    session_id=$(echo "$response" | jq -r '.session_id')
    
    if [ "$session_id" = "null" ] || [ -z "$session_id" ]; then
      echo "ERROR: Failed to start session"
      echo "$response"
      exit 1
    fi
    
    echo "$session_id" > "$SESSION_FILE"
    echo "✓ Session started: $session_id"
    ;;
    
  note)
    session_id=$(cat "$SESSION_FILE" 2>/dev/null)
    if [ -z "$session_id" ]; then
      echo "ERROR: No active session. Run 'start' first."
      exit 1
    fi
    
    content="$2"
    quality="${3:-8}"
    
    response=$(curl -s -X POST "$API/learning/session/$session_id/note" \
      -H "Content-Type: application/json" \
      -d "{\"content\": \"$content\", \"quality\": $quality}")
    
    echo "$response" | jq -r '.status // "ERROR"'
    ;;
    
  verify)
    session_id=$(cat "$SESSION_FILE" 2>/dev/null)
    if [ -z "$session_id" ]; then
      echo "ERROR: No active session"
      exit 1
    fi
    
    topic="$2"
    understanding="${3:-4.0}"
    
    curl -s -X POST "$API/learning/session/$session_id/verify" \
      -H "Content-Type: application/json" \
      -d "{\"topic\": \"$topic\", \"understanding\": $understanding, \"sources_verified\": true}" | jq
    ;;
    
  consolidate)
    session_id=$(cat "$SESSION_FILE" 2>/dev/null)
    if [ -z "$session_id" ]; then
      echo "ERROR: No active session"
      exit 1
    fi
    
    curl -s -X POST "$API/learning/session/$session_id/consolidate" | jq
    rm -f "$SESSION_FILE"
    echo "✓ Session consolidated and closed"
    ;;
    
  *)
    echo "Usage: $0 {start|note|verify|consolidate} [args...]"
    exit 1
    ;;
esac
