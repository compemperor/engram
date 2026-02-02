# Engram - OpenClaw Integration

Memory system for OpenClaw agents.

## Quick Start

```bash
# Start Engram server
docker run -d -p 8765:8765 -v ~/.openclaw/workspace/memory:/data/memories ghcr.io/compemperor/engram:latest
```

## Usage

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

# Search memories
def recall(query: str, min_quality: int = 7):
    r = requests.post(f"{ENGRAM}/memory/search", json={
        "query": query,
        "top_k": 5,
        "min_quality": min_quality
    })
    return [hit["memory"]["lesson"] for hit in r.json()["results"]]

# Get all for topic
def get_topic(topic: str):
    r = requests.get(f"{ENGRAM}/memory/recall/{topic}")
    return [m["lesson"] for m in r.json()["memories"]]
```

## Example

```python
# After completing a task
remember("trading", "Don't chase missed trades", quality=9)

# Before starting similar task
lessons = recall("trading mistakes")
print("Relevant lessons:", lessons)
```

## API Docs

http://localhost:8765/docs
