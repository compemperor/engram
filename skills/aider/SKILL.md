# Engram - Aider Integration

Use Engram memory in Aider sessions.

## Why Learning Sessions? 🧠

**During coding:** You learn patterns, make mistakes, discover solutions.

**Without structure:** These insights get lost or diluted.

**With Engram sessions:**
1. **Start** - Begin a focused learning session on a topic
2. **Note** - Log what you learn (rate quality 1-10)
3. **Verify** - Self-check: Can I explain this? What would I do differently?
4. **Consolidate** - High-quality notes (>= 8) become permanent memories

**Why it works:**
- Quality threshold filters noise (only keep the good stuff)
- Verification forces you to articulate understanding
- Sessions give structure to organic learning
- Perfect for refactoring sprints, debugging marathons, learning new libraries

**When to use:**
- Refactoring a complex module
- Learning a new framework
- Debugging a challenging issue
- Code review insights

---

## Setup

```bash
# Start Engram
docker run -d -p 8765:8765 -v ./memories:/data/memories ghcr.io/compemperor/engram:latest
```

## Usage in .aider.conf.yml

```yaml
# Add custom commands
commands:
  remember: |
    import requests
    requests.post('http://localhost:8765/memory/add', json={
      'topic': '{topic}',
      'lesson': '{lesson}',
      'source_quality': 9
    })
  
  recall: |
    import requests
    r = requests.post('http://localhost:8765/memory/search', json={
      'query': '{query}',
      'top_k': 5
    })
    for hit in r.json()['results']:
      print(hit['memory']['lesson'])
```

## In Aider Session

```python
# In your project's aider_helper.py
import requests

ENGRAM = "http://localhost:8765"

def save_lesson(topic: str, lesson: str):
    """Save a coding lesson to Engram"""
    requests.post(f"{ENGRAM}/memory/add", json={
        "topic": topic,
        "lesson": lesson,
        "source_quality": 9
    })

def get_lessons(query: str):
    """Get relevant lessons from Engram"""
    r = requests.post(f"{ENGRAM}/memory/search", json={
        "query": query,
        "top_k": 5,
        "min_quality": 7
    })
    return [hit["memory"]["lesson"] for hit in r.json()["results"]]
```

## Learning Sessions

For deep learning cycles:

```python
import requests

def start_session(topic: str):
    r = requests.post(f"http://localhost:8765/learning/session/start?topic={topic}&duration_min=30")
    return r.json()["session_id"]

def log_note(session_id: str, content: str, quality: int = 8):
    requests.post(f"http://localhost:8765/learning/session/{session_id}/note", json={
        "content": content,
        "source_quality": quality  # >= 8 auto-saves to memory
    })

def finish_session(session_id: str):
    return requests.post(f"http://localhost:8765/learning/session/{session_id}/consolidate").json()

# Example
session_id = start_session("refactoring-patterns")
log_note(session_id, "Extract method refactoring reduces complexity", 9)
log_note(session_id, "Single responsibility principle applies to functions", 8)
summary = finish_session(session_id)
```

## Examples

After refactoring:
```python
save_lesson("python", "Use dataclasses instead of dicts for type safety")
```

Before similar work:
```python
lessons = get_lessons("python type safety")
```

## Workflow

**Before coding:**
```python
# Recall relevant patterns
lessons = get_lessons("refactoring patterns")
```

**During work:**
```python
# Track learning
session_id = start_session("api-refactoring")
log_note(session_id, "Separated concerns into layers", 9)
```

**After completion:**
```python
summary = finish_session(session_id)
# High-quality notes auto-saved!
```

## Health & Stats

```bash
# Health check
curl http://localhost:8765/health

# View stats
curl http://localhost:8765/memory/stats
```

## API Docs

http://localhost:8765/docs

## Notes

- Quality >= 8: Auto-saved to permanent memory
- Understanding 1-5 scale: 1=confused, 5=mastery
- Semantic search finds related concepts
- Sessions auto-consolidate insights

## Container Management

```bash
docker ps | grep engram        # Status
docker logs engram -f          # Logs
docker restart engram          # Restart
```
