# Engram - Cursor Integration

Memory system for Cursor IDE.

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
