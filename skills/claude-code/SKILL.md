# Engram - Claude Code Integration

Memory system for Claude Code projects.

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

## Project Structure

```
your-project/
├── engram_client.py    # Memory client
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
