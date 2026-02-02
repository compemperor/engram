# Engram - Cursor Integration

Memory system for Cursor IDE.

## Learning Flow 🧠

**Traditional problem:** Code, learn something, forget it next week.

**Engram solution:** Structured learning with quality gates.

**The Cycle:**
```
Code Session → Discoveries → Rate Quality (1-10) → Self-Verify (1-5)
→ Consolidation → Permanent Memory (if quality >= 8)
```

**Why quality thresholds?**
- Not every observation is worth remembering
- Quality >= 8 means "I'd teach this to someone else"
- Understanding >= 4 means "I can apply this right now"

**Why verification?**
- Prevents false confidence
- Identifies what you actually need to review
- Like explaining code in a PR review - if you can't explain it clearly, you don't fully get it

**Perfect for:**
- Deep debugging sessions
- Learning new patterns
- Architecture decisions
- Performance optimization insights

---

## Setup

```bash
# Start Engram
docker run -d -p 8765:8765 -v ./memories:/data/memories ghcr.io/compemperor/engram:latest
```

## VS Code Extension (Optional)

Create `.vscode/settings.json`:

```json
{
  "cursor.customCommands": {
    "Remember": {
      "command": "curl -X POST http://localhost:8765/memory/add -H 'Content-Type: application/json' -d '{\"topic\":\"${topic}\",\"lesson\":\"${lesson}\",\"source_quality\":9}'"
    },
    "Recall": {
      "command": "curl -X POST http://localhost:8765/memory/search -H 'Content-Type: application/json' -d '{\"query\":\"${query}\",\"top_k\":5}'"
    }
  }
}
```

## Helper Script

Create `engram_helper.py` in your project:

```python
#!/usr/bin/env python3
"""
Engram helper for Cursor IDE
Usage: python engram_helper.py remember "topic" "lesson"
       python engram_helper.py recall "query"
"""
import sys
import requests

ENGRAM = "http://localhost:8765"

def remember(topic: str, lesson: str):
    r = requests.post(f"{ENGRAM}/memory/add", json={
        "topic": topic,
        "lesson": lesson,
        "source_quality": 9
    })
    print(f"✓ Saved to {topic}")

def recall(query: str):
    r = requests.post(f"{ENGRAM}/memory/search", json={
        "query": query,
        "top_k": 5,
        "min_quality": 7
    })
    for hit in r.json()["results"]:
        print(f"• {hit['memory']['lesson']}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    action = sys.argv[1]
    if action == "remember" and len(sys.argv) == 4:
        remember(sys.argv[2], sys.argv[3])
    elif action == "recall":
        recall(sys.argv[2])
```

## Learning Sessions

Add to engram_helper.py for deep learning:

```python
def start_session(topic: str):
    r = requests.post(f"http://localhost:8765/learning/session/start?topic={topic}&duration_min=30")
    return r.json()["session_id"]

def log_note(session_id: str, content: str, quality: int = 8):
    requests.post(f"http://localhost:8765/learning/session/{session_id}/note", json={
        "content": content,
        "source_quality": quality  # >= 8 auto-saves
    })

def finish_session(session_id: str):
    return requests.post(f"http://localhost:8765/learning/session/{session_id}/consolidate").json()
```

## Usage in Cursor

After fixing a bug:
```bash
python engram_helper.py remember "debugging" "Check null pointers before dereferencing"
```

Before debugging:
```bash
python engram_helper.py recall "debugging techniques"
```

## Cursor Composer

Add to your Cursor Composer context:

> Before each coding task, query Engram for relevant lessons: `curl http://localhost:8765/memory/search -d '{"query":"current task description"}'`

## Workflow

**Before task:**
```python
# Check for relevant lessons
lessons = recall("debugging techniques")
```

**During work:**
```python
# Track discoveries
session_id = start_session("debugging")
log_note(session_id, "Found null pointer issue", quality=9)
```

**After task:**
```python
# Consolidate learnings
summary = finish_session(session_id)
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

---

## ⚠️ Quality Rating Policy

**Before rating sources, read:** `QUALITY_RATING_POLICY.md` in Engram repo

**Quick rules:**
- Social media = MAX 6
- Quality 8+ needs 2+ independent sources
- Use CRAAP test for evaluation
- Be conservative with ratings

See full policy for details.
