# Engram - Aider Integration

Use Engram memory in Aider sessions.

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

## Example

After refactoring:
```python
save_lesson("python", "Use dataclasses instead of dicts for type safety")
```

Before similar work:
```python
lessons = get_lessons("python type safety")
```
