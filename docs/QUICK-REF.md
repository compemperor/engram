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

┌─ Need SYNTHESIS? (v0.7) ────────────────────────────────┐
│ • Consolidate topic?  → POST /memory/reflect            │
│ • List insights?      → GET /memory/reflections         │
│ • What needs reflect? → GET /memory/reflect/candidates  │
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

# Reflect on topic (v0.7)
curl -X POST http://localhost:8765/memory/reflect \
  -H "Content-Type: application/json" \
  -d '{"topic": "trading", "min_quality": 7}'

# List reflections
curl http://localhost:8765/memory/reflections

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



### Quality Assessment (v0.8)

Evaluate memory quality using heuristics:
```python
# Assess single memory
r = requests.get(f"{API}/memory/quality/{memory_id}")

# Batch assess
r = requests.post(f"{API}/memory/quality/assess?limit=10")

# Apply adjustments
r = requests.post(f"{API}/memory/quality/apply?auto_apply=true")
```


### Embedding Model (v0.9)

Configure via environment variable:
```yaml
environment:
  - ENGRAM_EMBEDDING_MODEL=intfloat/e5-large-v2
```

Options:
- `intfloat/e5-base-v2` (768 dims, default)
- `intfloat/e5-large-v2` (1024 dims, better quality)
- `intfloat/multilingual-e5-large` (1024 dims, multi-language)

### Compression & Replay (v0.10)

```python
# Find compression candidates
r = requests.get(f"{API}/memory/compression/candidates?limit=5")

# Apply compression
r = requests.post(f"{API}/memory/compression/apply?auto_apply=true")

# Get replay candidates
r = requests.get(f"{API}/memory/replay/candidates?limit=10")

# Replay memories
r = requests.post(f"{API}/memory/replay?limit=20")
```
