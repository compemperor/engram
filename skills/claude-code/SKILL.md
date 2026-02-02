# Engram - Claude Code Integration

Memory system for Claude Code projects.

## Understanding Learning Sessions 🧠

**The Challenge:** AI agents learn during sessions but have no long-term memory between sessions.

**Engram's Solution:** Structured learning with quality control.

**How it works:**

1. **Session Start** - Define what you're learning about
2. **Progressive Notes** - Log observations with quality ratings (1-10)
   - 1-5: Low quality (scratch notes)
   - 6-7: Medium quality (useful reference)
   - 8-10: High quality (teach-worthy insights)
3. **Verification Checkpoints** - Self-assess understanding (1-5 scale)
   - 1-2: Confused, need to revisit
   - 3: Grasping it, but not confident
   - 4-5: Understand and can apply
4. **Consolidation** - Notes with quality >= 8 automatically become permanent memories

**Why this works for AI agents:**
- **Quality gates** prevent memory pollution (only keep the best)
- **Verification** forces articulation (the Feynman test)
- **Auto-save threshold** (>= 8) ensures high signal-to-noise ratio
- **Permanent storage** survives session restarts

**Use cases:**
- Multi-file refactoring (track decisions)
- Learning codebases (capture architecture insights)
- Debugging complex issues (remember what worked)
- API design (consolidate best practices)

---

## Setup

```bash
# Start Engram
docker run -d -p 8765:8765 -v ./memories:/data/memories ghcr.io/compemperor/engram:latest
```

## Python Client

Add `engram_client.py` to your project:

```python
"""Engram memory client for Claude Code"""
import requests
from typing import List, Optional

class EngramClient:
    def __init__(self, api_url: str = "http://localhost:8765"):
        self.api = api_url
    
    def remember(self, topic: str, lesson: str, quality: int = 8) -> dict:
        """Store a coding lesson"""
        response = requests.post(
            f"{self.api}/memory/add",
            json={
                "topic": topic,
                "lesson": lesson,
                "source_quality": quality,
                "understanding": 4.0
            }
        )
        return response.json()
    
    def recall(self, query: str, min_quality: int = 7) -> List[str]:
        """Search for relevant lessons"""
        response = requests.post(
            f"{self.api}/memory/search",
            json={
                "query": query,
                "top_k": 5,
                "min_quality": min_quality
            }
        )
        results = response.json()["results"]
        return [r["memory"]["lesson"] for r in results]
    
    def get_topic(self, topic: str, min_quality: int = 7) -> List[str]:
        """Get all lessons for a topic"""
        response = requests.get(
            f"{self.api}/memory/recall/{topic}",
            params={"min_quality": min_quality}
        )
        memories = response.json()["memories"]
        return [m["lesson"] for m in memories]

# Global instance
engram = EngramClient()
```

## Usage

```python
from engram_client import engram

# After solving a problem
engram.remember(
    "fastapi",
    "Use BackgroundTasks for async operations that don't need to block response",
    quality=9
)

# Before tackling similar problem
lessons = engram.recall("fastapi async patterns")
print("Relevant techniques:", lessons)

# Get all lessons for a topic
api_patterns = engram.get_topic("fastapi")
```

## Learning Sessions

For structured deep learning:

```python
class EngramClient:
    # ... (previous methods) ...
    
    def start_session(self, topic: str, duration_min: int = 30):
        """Start a learning session"""
        response = requests.post(
            f"{self.api}/learning/session/start",
            params={"topic": topic, "duration_min": duration_min}
        )
        return response.json()["session_id"]
    
    def log_note(self, session_id: str, content: str, quality: int = 8):
        """Log a learning note (quality >= 8 auto-saves to memory)"""
        response = requests.post(
            f"{self.api}/learning/session/{session_id}/note",
            json={"content": content, "source_quality": quality}
        )
        return response.json()
    
    def verify_understanding(self, session_id: str, topic: str, understanding: float, applications: list):
        """Add verification checkpoint"""
        response = requests.post(
            f"{self.api}/learning/session/{session_id}/verify",
            json={
                "topic": topic,
                "understanding": understanding,
                "sources_verified": True,
                "applications": applications
            }
        )
        return response.json()
    
    def consolidate_session(self, session_id: str):
        """Consolidate and save high-quality insights"""
        response = requests.post(
            f"{self.api}/learning/session/{session_id}/consolidate"
        )
        return response.json()

# Usage
session_id = engram.start_session("api-design", duration_min=20)
engram.log_note(session_id, "REST endpoints should be noun-based", quality=9)
engram.log_note(session_id, "Use HTTP status codes correctly", quality=8)
engram.verify_understanding(session_id, "api-design", 4.5, ["Apply to new endpoints"])
summary = engram.consolidate_session(session_id)
print(f"Saved {summary['summary']['insights_count']} insights")
```

## Project Structure

```
your-project/
├── engram_client.py    # Memory client (with sessions!)
├── main.py             # Your code
└── .env                # ENGRAM_API=http://localhost:8765
```

## Best Practices

**After each significant change:**
```python
engram.remember("architecture", "Separated concerns into layers", quality=8)
```

**Before refactoring:**
```python
lessons = engram.recall("refactoring patterns")
```

**When debugging:**
```python
bugs = engram.recall("common bugs in [your context]")
```

## With Environment Variable

```python
import os
from engram_client import EngramClient

engram = EngramClient(api_url=os.getenv("ENGRAM_API", "http://localhost:8765"))
```
