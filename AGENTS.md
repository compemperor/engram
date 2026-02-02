# For AI Agents 🤖

Quick integration guide for AI agents (Claude Code, Cursor, Aider, etc.)

---

## Quick Start

```bash
# Start Engram server
docker run -d -p 8765:8765 -v ./memories:/data/memories compemperor/engram
```

**API:** http://localhost:8765  
**Docs:** http://localhost:8765/docs

---

## Basic Usage

### Store a Memory

```bash
curl -X POST http://localhost:8765/memory/add \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "coding",
    "lesson": "Always validate API inputs with Pydantic",
    "source_quality": 9
  }'
```

### Search Memories

```bash
curl -X POST http://localhost:8765/memory/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "API best practices",
    "top_k": 5,
    "min_quality": 7
  }'
```

### Recall Topic

```bash
curl http://localhost:8765/memory/recall/coding?min_quality=7
```

---

## Python Integration

```python
import requests

ENGRAM = "http://localhost:8765"

# Store lesson
def remember(topic: str, lesson: str, quality: int = 8):
    requests.post(f"{ENGRAM}/memory/add", json={
        "topic": topic,
        "lesson": lesson,
        "source_quality": quality
    })

# Search
def recall(query: str):
    r = requests.post(f"{ENGRAM}/memory/search", json={
        "query": query,
        "top_k": 5,
        "min_quality": 7
    })
    return [hit["memory"]["lesson"] for hit in r.json()["results"]]

# Usage in your agent
remember("debugging", "Check logs first, then add breakpoints", quality=9)
lessons = recall("debugging techniques")
```

---

## Learning Sessions

For complex learning tasks:

```python
import requests

ENGRAM = "http://localhost:8765"
session_id = "learning-20260202"

# 1. Start session
requests.post(f"{ENGRAM}/learning/session/start", params={
    "topic": "fastapi-patterns",
    "duration_min": 30,
    "session_id": session_id
})

# 2. Add notes as you learn
requests.post(f"{ENGRAM}/learning/session/{session_id}/note", json={
    "content": "Dependency injection makes testing easier",
    "source_url": "https://fastapi.tiangolo.com/tutorial/dependencies/",
    "source_quality": 9
})

# 3. Verify understanding
requests.post(f"{ENGRAM}/learning/session/{session_id}/verify", json={
    "topic": "dependency-injection",
    "understanding": 4.0,
    "sources_verified": True,
    "applications": ["Can refactor current API"]
})

# 4. Consolidate (auto-saves high-quality insights)
requests.post(f"{ENGRAM}/learning/session/{session_id}/consolidate")
```

---

## Best Practices

**Quality Tracking:**
- 9-10: Verified from official docs
- 7-8: Reliable source, tested
- 5-6: Uncertain, needs verification
- 1-4: Low confidence

**Topic Organization:**
```python
# Good: Hierarchical and specific
"python/optimization"
"fastapi/dependency-injection"
"debugging/python"

# Avoid: Too generic
"coding"
"tips"
```

**Before Tasks:**
```python
# Recall relevant lessons first
lessons = recall("error handling in Python")
# Use lessons in your work
```

---

## Environment Variable

```bash
export ENGRAM_API="http://localhost:8765"
```

---

## Interactive Docs

Visit **http://localhost:8765/docs** to test all endpoints in your browser.

---

**More examples:** Check `/examples/quickstart.py`
