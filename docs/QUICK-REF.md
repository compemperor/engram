# Engram Quick Reference

**For agents:** Fast lookup of endpoints and when to use them.

## Decision Tree

```
┌─ Need to STORE? ────────────────────────────────────────┐
│ • Quality < 7?        → Don't store (noise)             │
│ • Quick fact?         → POST /memory/add                │
│ • Deep learning?      → POST /learning/session/start    │
│ • Event/experience?   → POST /memory/add (episodic)     │
└─────────────────────────────────────────────────────────┘

┌─ Need to RECALL? ───────────────────────────────────────┐
│ • Fuzzy concept?      → POST /memory/search             │
│ • Exact topic?        → GET /memory/recall/{topic}      │
│ • Related to X?       → GET /memory/related/{id}        │
│ • Test yourself?      → GET /recall/challenge           │
└─────────────────────────────────────────────────────────┘
```

## Common Commands

```bash
# Search memories
curl -X POST http://localhost:8765/memory/search \
  -H "Content-Type: application/json" \
  -d '{"query": "trading mistakes", "top_k": 5, "min_quality": 8}'

# Store memory
curl -X POST http://localhost:8765/memory/add \
  -H "Content-Type: application/json" \
  -d '{"topic": "trading/risk", "lesson": "Never risk >2%", "source_quality": 10}'

# Recall by topic
curl http://localhost:8765/memory/recall/trading?min_quality=7

# Get related memories
curl http://localhost:8765/memory/related/{memory_id}

# Stats
curl http://localhost:8765/memory/stats
```

## Quality Scale

- **1-6:** Don't store (opinions, rumors, unverified)
- **7:** Good source OR expert facts
- **8-9:** 2+ verified sources, tested personally
- **10:** Official docs, research papers, proven in production

## Topic Naming

```
✅ Good:
  trading/risk
  trading/algorithms
  market-intel/ovzon
  tools/osint
  
❌ Bad:
  trading1
  trading2
  ovzon-stuff
```

## Python Helper

```python
API = "http://localhost:8765"

def store_lesson(topic, lesson, quality=9):
    """Store a verified lesson"""
    requests.post(f"{API}/memory/add", json={
        "topic": topic,
        "lesson": lesson,
        "source_quality": quality
    })

def recall_context(query, min_quality=8):
    """Get relevant context for a task"""
    r = requests.post(f"{API}/memory/search", json={
        "query": query,
        "top_k": 5,
        "min_quality": min_quality
    })
    return r.json()["results"]
```

## Best Practices

1. **Search before storing** (avoid duplicates)
2. **Filter by quality** (`min_quality: 8` for critical tasks)
3. **Use hierarchy** (`topic/subtopic`, not flat)
4. **Batch recall at start** (not during work)
5. **Learning sessions for deep work** (5+ min, 10+ sources)

**Full guide:** [MEMORY-GUIDE.md](./MEMORY-GUIDE.md)

