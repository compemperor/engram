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

# Store memory (semantic - default)
curl -X POST http://localhost:8765/memory/add \
  -H "Content-Type: application/json" \
  -d '{"topic": "trading/risk", "lesson": "Never risk >2%", "source_quality": 10}'

# Store episodic memory (experiences/events)
curl -X POST http://localhost:8765/memory/add \
  -H "Content-Type: application/json" \
  -d '{"topic": "episodes/2026-02-06", "lesson": "User frustrated with repeated mistakes", "memory_type": "episodic", "source_quality": 9}'

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

# Sync metadata (fix count drift)
curl -X POST http://localhost:8765/memory/sync

# Archive a memory
curl -X POST http://localhost:8765/memory/archive/{memory_id}

# List archived memories
curl http://localhost:8765/memory/archived
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

### Active Learning (v0.11)

Track knowledge gaps and get learning suggestions:

```python
# View knowledge gaps (poor searches, failed recalls)
r = requests.get(f"{API}/learning/gaps")

# Get prioritized learning suggestions
r = requests.get(f"{API}/learning/suggest?limit=5")

# Request to learn a topic (high priority)
r = requests.post(f"{API}/learning/request?topic=quantum+computing")

# Mark gap as resolved
r = requests.post(f"{API}/learning/resolve?query=quantum+computing")

# Learning stats
r = requests.get(f"{API}/learning/stats")
```

Gaps are auto-tracked when:
- Search returns <3 results or score <0.5
- Recall challenge fails

### Goal-Aligned Drift (v0.12)

Drift measures how aligned your content is with your goals.

**Setup:** Store your goals in memory:
```bash
curl -X POST http://localhost:8765/memory/add \
  -H "Content-Type: application/json" \
  -d '{"topic": "identity/goals", "lesson": "Build AI agents, learn trading, improve Engram"}'

curl -X POST http://localhost:8765/memory/add \
  -H "Content-Type: application/json" \
  -d '{"topic": "identity/interests", "lesson": "Machine learning, cryptocurrency, Swedish stocks"}'
```

**How it works:**
- Embeds your content and compares to goals embedding
- Low drift (< 0.3) = content aligns with goals
- High drift (> 0.5) = content is off-topic

**Check drift metrics:**
```bash
curl http://localhost:8765/mirror/metrics
# Returns: goal_aligned: true/false, drift scores, etc.
```

Learning sessions ignore drift (exploration is expected).
Regular `/memory/add` uses drift in quality gate.

### Intent-Aware Retrieval (v0.13)

Search automatically adjusts parameters based on query intent.

**Intent Types:**
| Intent | Detected by | Adjustments |
|--------|-------------|-------------|
| `fact_lookup` | "what is", "define", short queries | top_k=3, min_quality=7, no temporal weighting |
| `procedural` | "how to", "workflow", "steps" | min_quality=8, temporal_weighting=false |
| `temporal` | "recent", "latest", "when" | temporal_boost=2x, top_k=5 |
| `exploration` | "explore", "research", "learn" | top_k=10, include_dormant=true, depth=2 |
| `recall` | "what did I learn", "remember" | top_k=5, context_expansion=true |
| `relationship` | "related to", "similar", "connected" | top_k=7, depth=2, include_dormant=true |

**Example Response:**
```json
{
  "query": "how to deploy engram",
  "intent": {
    "primary": "procedural",
    "confidence": 0.8,
    "secondary": null,
    "adjusted_params": {"min_quality": 8, "use_temporal_weighting": false}
  },
  "results": [...]
}
```

**Disable intent-aware retrieval:**
```bash
curl -X POST http://localhost:8765/memory/search \
  -H "Content-Type: application/json" \
  -d '{"query": "some query", "intent_aware": false}'
```

User-specified params always override intent adjustments.

### Reasoning Memory (v0.14)

Store and learn from decision traces, tool calls, and outcomes.

**Add a trace:**
```bash
curl -X POST http://localhost:8765/reasoning/trace \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my-session",
    "thought": "I need to search for X",
    "action_type": "tool_call",
    "action_name": "memory_search",
    "action_args": {"query": "X"},
    "observation": "Found 3 results",
    "outcome": "success"
  }'
```

**Get session traces:**
```bash
curl http://localhost:8765/reasoning/session/my-session
```

**Search traces:**
```bash
curl -X POST "http://localhost:8765/reasoning/search?query=deploy&outcome=failure"
```

**Distill session into pattern:**
```bash
curl -X POST http://localhost:8765/reasoning/distill/my-session
# Returns: summary, key_decisions, lesson learned
```

**Extract skill from successful session:**
```bash
curl -X POST http://localhost:8765/reasoning/skill/extract \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my-session",
    "name": "release-workflow",
    "description": "Execute release cycle",
    "trigger_pattern": "release",
    "min_success_rate": 0.8
  }'
```

**Find skill for task:**
```bash
curl -X POST "http://localhost:8765/reasoning/skill/find?task=how%20to%20release"
```

**Stats:**
```bash
curl http://localhost:8765/reasoning/stats
# Returns: total_traces, outcomes, action_types, total_skills
```

Based on ReasoningBank, ExpeL, and Voyager research.
OpenClaw hook available: `reasoning-trace` (captures tool calls automatically).
