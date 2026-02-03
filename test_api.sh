#!/bin/bash
# Engram API Test Suite - Verifies all endpoints work correctly

set -e

API="${ENGRAM_API:-http://localhost:8765}"

echo "=== Engram API Test Suite ==="
echo "Testing: $API"
echo

# Helper function
test_endpoint() {
    echo "✓ $1"
}

# 1. Health check
test_endpoint "Health check"
curl -sf "$API/health" > /dev/null

# 2. Add semantic memory
test_endpoint "Add semantic memory"
curl -sf -X POST "$API/memory/add" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "test",
    "lesson": "API test - semantic memory",
    "source_quality": 8
  }' > /dev/null

# 3. Add episodic memory
test_endpoint "Add episodic memory"
curl -sf -X POST "$API/memory/add" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "test",
    "lesson": "API test executed successfully",
    "source_quality": 9,
    "metadata": {"test": true, "timestamp": "now"}
  }' > /dev/null

# 4. Get stats
test_endpoint "Get memory stats"
curl -sf "$API/memory/stats" > /dev/null

# 5. Active recall challenge
test_endpoint "Active recall challenge"
curl -sf "$API/recall/challenge" > /dev/null

# 6. Recall stats
test_endpoint "Recall stats"
curl -sf "$API/recall/stats" > /dev/null

# 7. Start learning session (POST with query params)
test_endpoint "Start learning session"
SESSION=$(curl -sf -X POST "$API/learning/session/start?topic=api-test&duration_min=5" | jq -r '.session_id')

if [ -z "$SESSION" ] || [ "$SESSION" = "null" ]; then
    echo "❌ ERROR: Failed to create session"
    exit 1
fi

# 8. Add learning note
test_endpoint "Add learning note"
curl -sf -X POST "$API/learning/session/$SESSION/note" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test note with quality 9",
    "source_quality": 9
  }' > /dev/null

# 9. Add verification
test_endpoint "Add verification checkpoint"
curl -sf -X POST "$API/learning/session/$SESSION/verify" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "api-testing",
    "understanding": 4.5,
    "sources_verified": true,
    "applications": ["Verify deployment"]
  }' > /dev/null

# 10. List sessions
test_endpoint "List active sessions"
curl -sf "$API/learning/sessions" > /dev/null

# 11. Consolidate session
test_endpoint "Consolidate session"
curl -sf -X POST "$API/learning/session/$SESSION/consolidate" > /dev/null

# 12. Verify cleanup
test_endpoint "Verify session cleanup"
COUNT=$(curl -sf "$API/learning/sessions" | jq '.count')
if [ "$COUNT" != "0" ]; then
    echo "❌ ERROR: Session not cleaned up (count=$COUNT)"
    exit 1
fi

echo
echo "=== ✅ All tests passed! ==="
echo
echo "Memory stats:"
curl -sf "$API/memory/stats" | jq -c '{
  total: .total_memories,
  episodic: .episodic_memories,
  semantic: .semantic_memories,
  topics: .topics
}'
