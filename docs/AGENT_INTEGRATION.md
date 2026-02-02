# Agent Integration Guide 🤖

How to integrate Engram with AI agents (Claude Code, OpenCode, LangChain, etc.)

---

## Overview

Engram provides three integration methods:

1. **REST API** - Universal, works with any agent/framework
2. **Python Library** - Direct import for Python agents
3. **CLI** - Command-line for shell-based agents

---

## Method 1: REST API (Universal)

**Best for:** Any agent framework, language-agnostic

### Start Engram Server

```bash
# Docker (recommended)
docker run -d -p 8765:8765 -v ./memories:/data/memories ghcr.io/compemperor/engram:latest

# Or local
python -m engram
```

### Basic Operations

```bash
# Add memory
curl -X POST http://localhost:8765/memory/add \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "coding",
    "lesson": "Always validate API inputs with Pydantic",
    "source_quality": 9,
    "understanding": 5.0
  }'

# Search memories
curl -X POST http://localhost:8765/memory/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "API best practices",
    "top_k": 5,
    "min_quality": 7
  }'

# Recall topic
curl http://localhost:8765/memory/recall/coding?min_quality=7
```

### Learning Session

```bash
# Start session
curl -X POST "http://localhost:8765/learning/session/start?topic=python-optimization&duration_min=30"

# Add note
curl -X POST http://localhost:8765/learning/session/20260202-203000/note \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Use list comprehensions instead of loops for 2-3x speedup",
    "source_url": "https://docs.python.org/3/tutorial/datastructures.html",
    "source_quality": 9
  }'

# Verify understanding
curl -X POST http://localhost:8765/learning/session/20260202-203000/verify \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "python-optimization",
    "understanding": 4.5,
    "sources_verified": true,
    "gaps": ["Need to benchmark actual performance"],
    "applications": ["Can optimize data processing scripts"]
  }'

# Consolidate
curl -X POST http://localhost:8765/learning/session/20260202-203000/consolidate
```

---

## Method 2: Python Library

**Best for:** Python-based agents (Claude Code, OpenCode with Python)

### Installation

```bash
pip install engram
# Or from source
cd engram && pip install -e .
```

### Usage

```python
from engram import MemoryStore, MirrorEvaluator, LearningSession

# Initialize
memory = MemoryStore(path="./agent-memories")

# Store lessons
memory.add_lesson(
    topic="debugging",
    lesson="Check logs first, then add print statements",
    source_quality=8,
    understanding=5.0
)

# Search
results = memory.search("debugging techniques", top_k=5, min_quality=7)
for result in results:
    print(f"[{result.score:.2f}] {result.memory.lesson}")

# Recall all lessons for topic
lessons = memory.recall("debugging", min_quality=7)

# Quality evaluation
evaluator = MirrorEvaluator(path="./agent-memories")
evaluation = evaluator.evaluate_session(
    sources_verified=True,
    understanding_ratings=[4.5, 5.0],
    topics=["debugging", "testing"]
)

if evaluation.consolidate:
    print("High quality - saving to long-term memory")
```

### Learning Session

```python
from engram.learning import LearningSession

# Create session
session = LearningSession(
    topic="fastapi-best-practices",
    duration_min=30,
    output_dir="./agent-memories/sessions"
)

# Take notes
session.add_note(
    content="Use dependency injection for database connections",
    source_url="https://fastapi.tiangolo.com/tutorial/dependencies/",
    source_quality=9
)

# Self-verification
session.verify(
    topic="fastapi-patterns",
    understanding=4.0,
    sources_verified=True,
    gaps=["Need to understand Depends() better"],
    applications=["Can refactor current API"]
)

# Add insights
session.add_insight("Dependency injection makes testing easier")

# Consolidate
summary = session.consolidate()
print(f"Session saved to: {summary['session_file']}")
```

---

## Method 3: CLI Wrapper

**Best for:** Shell-based agents, scripts

### Create CLI Helper

```bash
# ~/.local/bin/engram-memory

#!/bin/bash
# Engram CLI wrapper for agents

ENGRAM_API="${ENGRAM_API:-http://localhost:8765}"

case "$1" in
  add)
    curl -X POST "$ENGRAM_API/memory/add" \
      -H "Content-Type: application/json" \
      -d "{\"topic\":\"$2\",\"lesson\":\"$3\",\"source_quality\":${4:-7}}"
    ;;
  search)
    curl -X POST "$ENGRAM_API/memory/search" \
      -H "Content-Type: application/json" \
      -d "{\"query\":\"$2\",\"top_k\":${3:-5}}" | jq -r '.results[].memory.lesson'
    ;;
  recall)
    curl "$ENGRAM_API/memory/recall/$2?min_quality=${3:-7}" | jq -r '.memories[].lesson'
    ;;
  *)
    echo "Usage: engram-memory {add|search|recall} ..."
    exit 1
    ;;
esac
```

```bash
chmod +x ~/.local/bin/engram-memory

# Usage
engram-memory add "coding" "Use type hints for better IDE support" 9
engram-memory search "python best practices" 5
engram-memory recall "coding" 7
```

---

## Integration Examples

### Claude Code (Anthropic)

```python
# In your Claude Code project

from engram import MemoryStore

class ClaudeCodeMemory:
    def __init__(self):
        self.memory = MemoryStore(path="./claude-memories")
    
    def remember(self, topic: str, lesson: str, quality: int = 8):
        """Store a lesson learned during coding"""
        self.memory.add_lesson(topic, lesson, source_quality=quality)
    
    def recall_lessons(self, query: str) -> list:
        """Search for relevant lessons"""
        results = self.memory.search(query, top_k=5, min_quality=7)
        return [r.memory.lesson for r in results]
    
    def recall_topic(self, topic: str) -> list:
        """Get all lessons for a topic"""
        memories = self.memory.recall(topic, min_quality=7)
        return [m.lesson for m in memories]

# Usage in Claude Code
memory = ClaudeCodeMemory()

# After completing a task
memory.remember("fastapi", "Use lifespan events for startup/shutdown", quality=9)

# Before starting similar task
lessons = memory.recall_lessons("fastapi best practices")
print("Relevant lessons:", lessons)
```

### OpenCode Integration

```python
# opencode_engram.py

import requests
from typing import List, Dict

class OpenCodeEngram:
    """Engram integration for OpenCode"""
    
    def __init__(self, api_url: str = "http://localhost:8765"):
        self.api = api_url
    
    def store_lesson(self, topic: str, lesson: str, quality: int = 8):
        """Store coding lesson"""
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
    
    def search_lessons(self, query: str, min_quality: int = 7) -> List[str]:
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
    
    def get_topic_lessons(self, topic: str) -> List[str]:
        """Get all lessons for topic"""
        response = requests.get(f"{self.api}/memory/recall/{topic}")
        memories = response.json()["memories"]
        return [m["lesson"] for m in memories]

# Usage
engram = OpenCodeEngram()

# After solving a problem
engram.store_lesson(
    "debugging",
    "Use Python debugger (pdb) instead of print statements for complex issues",
    quality=9
)

# Before tackling similar problem
lessons = engram.search_lessons("debugging python")
print("Relevant techniques:", lessons)
```

### LangChain Integration

```python
from langchain.memory import BaseMemory
from engram import MemoryStore

class EngramMemory(BaseMemory):
    """LangChain memory backed by Engram"""
    
    def __init__(self, topic: str = "conversation", path: str = "./memories"):
        self.topic = topic
        self.memory = MemoryStore(path=path)
    
    @property
    def memory_variables(self) -> List[str]:
        return ["history"]
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load relevant memories"""
        query = inputs.get("input", "")
        results = self.memory.search(query, top_k=5, min_quality=7)
        history = "\n".join([r.memory.lesson for r in results])
        return {"history": history}
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]):
        """Save interaction to memory"""
        lesson = f"{inputs.get('input', '')}: {outputs.get('output', '')}"
        self.memory.add_lesson(
            topic=self.topic,
            lesson=lesson,
            source_quality=7,
            understanding=4.0
        )

# Usage with LangChain
from langchain.chains import ConversationChain

memory = EngramMemory(topic="coding-chat")
chain = ConversationChain(memory=memory, llm=llm)
```

---

## Best Practices for Agents

### 1. Quality Tracking

Always track source quality when storing lessons:

```python
# High quality (verified sources, deep understanding)
memory.add_lesson(topic, lesson, source_quality=9, understanding=5.0)

# Medium quality (unverified but seems correct)
memory.add_lesson(topic, lesson, source_quality=7, understanding=3.5)

# Low quality (uncertain, needs verification)
memory.add_lesson(topic, lesson, source_quality=5, understanding=2.0)
```

### 2. Topic Organization

Use consistent topic naming:

```python
# Good: Hierarchical, specific
"python/optimization"
"fastapi/dependency-injection"
"debugging/python"

# Avoid: Too generic
"coding"
"programming"
"tips"
```

### 3. Regular Recall

Before starting tasks, recall relevant lessons:

```python
# Search semantically
lessons = memory.search("handling API errors in Python", top_k=5)

# Or recall specific topic
lessons = memory.recall("error-handling", min_quality=7)

# Use lessons in prompt/context
context = "\n".join([f"- {l.lesson}" for l in lessons])
```

### 4. Learning Sessions

For complex learning, use structured sessions:

```python
session = LearningSession(topic="topic", duration_min=30)

# Progressive learning
session.add_note("Finding 1...")
session.add_note("Finding 2...")

# Self-verification
session.verify(topic="subtopic", understanding=4.0, sources_verified=True)

# Consolidate
session.consolidate()  # Auto-saves high-quality insights
```

### 5. Drift Monitoring

Periodically check for drift:

```bash
curl http://localhost:8765/mirror/drift
```

If drift detected, review recent learnings and refocus.

---

## Environment Variables

```bash
# API URL
export ENGRAM_API="http://localhost:8765"

# Memory path (for Python library)
export ENGRAM_MEMORY_PATH="./agent-memories"

# Quality thresholds
export ENGRAM_MIN_QUALITY="7"
export ENGRAM_MIN_UNDERSTANDING="3.0"
```

---

## Docker Integration

### For Agent Containers

```yaml
# docker-compose.yml
services:
  engram:
    image: compemperor/engram:latest
    ports:
      - "8765:8765"
    volumes:
      - ./memories:/data/memories
  
  my-agent:
    image: my-agent:latest
    environment:
      - ENGRAM_API=http://engram:8765
    depends_on:
      - engram
```

### Shared Memory Volume

```bash
# Multiple agents sharing same memory
docker run -d --name engram \
  -p 8765:8765 \
  -v agent-memories:/data/memories \
  compemperor/engram

docker run -d --name agent1 \
  -e ENGRAM_API=http://engram:8765 \
  -v agent-memories:/data/memories:ro \
  my-agent:latest

docker run -d --name agent2 \
  -e ENGRAM_API=http://engram:8765 \
  -v agent-memories:/data/memories:ro \
  my-agent:latest
```

---

## Monitoring & Health

### Health Check

```bash
# API health
curl http://localhost:8765/health

# Stats
curl http://localhost:8765/memory/stats

# Quality metrics
curl http://localhost:8765/mirror/metrics
```

### Integration Test

```python
import requests

def test_engram_integration():
    """Test Engram is accessible"""
    api = "http://localhost:8765"
    
    # Health check
    health = requests.get(f"{api}/health")
    assert health.status_code == 200
    
    # Add test lesson
    response = requests.post(
        f"{api}/memory/add",
        json={"topic": "test", "lesson": "Test lesson", "source_quality": 9}
    )
    assert response.status_code == 200
    
    # Search
    results = requests.post(
        f"{api}/memory/search",
        json={"query": "test", "top_k": 1}
    )
    assert results.status_code == 200
    assert len(results.json()["results"]) > 0
    
    print("✅ Engram integration working!")

if __name__ == "__main__":
    test_engram_integration()
```

---

## Troubleshooting

**Connection refused:**
```bash
# Check if Engram is running
curl http://localhost:8765/health

# Start if not running
docker-compose up -d engram
```

**Out of memory:**
```bash
# Check memory stats
curl http://localhost:8765/memory/stats

# Rebuild index if needed
curl -X POST http://localhost:8765/memory/rebuild-index
```

**Slow searches:**
- Enable FAISS (check requirements.txt includes faiss-cpu)
- Reduce top_k parameter
- Add quality filters (min_quality=7)

---

## Example: Agent Skill File

For OpenClaw or similar agent frameworks:

```python
# ~/.openclaw/skills/engram-client/SKILL.md

"""
Engram Memory Client Skill

Provides memory persistence for the agent across sessions.
"""

import requests
from typing import List, Dict

ENGRAM_API = "http://localhost:8765"

def remember(topic: str, lesson: str, quality: int = 8):
    """Store a lesson learned"""
    requests.post(
        f"{ENGRAM_API}/memory/add",
        json={"topic": topic, "lesson": lesson, "source_quality": quality}
    )

def recall(query: str, min_quality: int = 7) -> List[str]:
    """Search for relevant lessons"""
    response = requests.post(
        f"{ENGRAM_API}/memory/search",
        json={"query": query, "top_k": 5, "min_quality": min_quality}
    )
    return [r["memory"]["lesson"] for r in response.json()["results"]]

def get_topic(topic: str) -> List[str]:
    """Get all lessons for topic"""
    response = requests.get(f"{ENGRAM_API}/memory/recall/{topic}")
    return [m["lesson"] for m in response.json()["memories"]]
```

---

## Summary

**Universal Access:** REST API works with any language/framework  
**Python Native:** Direct import for Python agents  
**CLI Friendly:** Shell wrappers for script-based agents  
**Docker Ready:** Easy integration in containerized environments  
**Quality Focused:** Built-in quality control and drift detection  

**Next:** Check the [API documentation](http://localhost:8765/docs) for all endpoints!

---

**Questions?** Open an issue on GitHub or check the main README.

🤖 **Happy agent building!**
