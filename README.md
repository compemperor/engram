# Engram 🧠

**Memory traces for AI agents**

Self-improving memory system with quality control, drift detection, and learning framework. Built for AI agents that need to learn, remember, and self-correct - with full privacy and zero API costs.

---

**🤖 For AI Agents:** See [Agent Integration](./docs/AGENT_INTEGRATION.md) for quick integration guide

📚 **Documentation:**
- [Memory Guide](./docs/MEMORY-GUIDE.md) - How to use memory efficiently ⭐
- [Quick Reference](./docs/QUICK-REF.md) - Fast lookup for agents
- [Agent Integration](./docs/AGENT_INTEGRATION.md) - API reference

---

## Why Engram?

**The Problem:** Current AI memory systems accumulate everything without filtering. Over time, they fill with noise, lose coherence, and can't distinguish valuable insights from garbage.

**What goes wrong:**
- ❌ **No quality control** - Garbage in = garbage retained forever
- ❌ **No drift detection** - System doesn't know when it's losing coherence
- ❌ **No consolidation** - Can't store everything, but also can't decide what to keep
- ❌ **Result:** Memory systems that get worse over time, not better

**Engram's Solution:**

✅ **Quality gates** - Only store verified, high-quality learnings  
✅ **Drift detection** - Monitors when memory patterns diverge from goals  
✅ **Dream consolidation** - Like human sleep, replays and strengthens valuable memories while filtering noise  
✅ **Self-correction** - Automatically adjusts when detecting issues  

**Result:** Memory that improves over time, not degrades.

---

## Features

🔒 **Privacy-First** - Local embeddings, no data leaves your machine  
🧠 **Smart Memory** - Semantic search with quality filtering  
🔁 **Self-Improving** - Quality evaluation and drift detection  
🧪 **Neuroscience-Inspired** - Dream consolidation, homeostatic regulation  
🔌 **Framework-Agnostic** - Works with any LLM  
📦 **All-in-One** - Single Docker container, FastAPI server  

---

## Quick Start

### Docker (Recommended)

```bash
docker run -d -p 8765:8765 -v ./memories:/data/memories ghcr.io/compemperor/engram:latest
```

### Local

```bash
git clone https://github.com/compemperor/engram.git
cd engram
pip install -r requirements.txt
python -m engram
```

**API:** http://localhost:8765  
**Docs:** http://localhost:8765/docs (interactive OpenAPI)

---

## Basic Usage

### Add Memory

```bash
curl -X POST http://localhost:8765/memory/add \
  -H "Content-Type: application/json" \
  -d '{"topic":"coding","lesson":"Always validate inputs","source_quality":9}'
```

### Search

```bash
curl -X POST http://localhost:8765/memory/search \
  -H "Content-Type: application/json" \
  -d '{"query":"best practices","top_k":5}'
```

### Python

```python
import requests

api = "http://localhost:8765"

# Store
requests.post(f"{api}/memory/add", json={
    "topic": "debugging",
    "lesson": "Check logs first",
    "source_quality": 9
})

# Search
r = requests.post(f"{api}/memory/search", json={
    "query": "debugging",
    "top_k": 5
})
print(r.json()["results"])
```

---

## Architecture

Three layers working together:

1. **Memory** - Local embeddings (sentence-transformers) + FAISS vector search
2. **Mirror** - Quality evaluation, drift detection, consolidation decisions
3. **Learning** - Structured sessions with self-verification checkpoints

**API Server:** FastAPI with 19 REST endpoints, OpenAPI docs

---

## Use Cases

- **AI Agents** - Persistent memory with quality control
- **Personal Knowledge** - Build your external brain
- **Research** - Track learnings with drift detection
- **Trading Bots** - Remember lessons, prevent mistakes
- **Chatbots** - Maintain context across sessions

---

## Documentation

- **[docs/AGENT_INTEGRATION.md](./docs/AGENT_INTEGRATION.md)** - Quick guide for AI agents
- **[docs/QUICKSTART.md](./docs/QUICKSTART.md)** - 5-minute tutorial
- **[docs/MEMORY-GUIDE.md](./docs/MEMORY-GUIDE.md)** - How to use memory efficiently
- **[/docs](http://localhost:8765/docs)** - Interactive API docs (when running)

---

## Technology

- **Python 3.11** - Core language
- **FastAPI + Pydantic** - REST API with validation
- **sentence-transformers** - Local embeddings (all-MiniLM-L6-v2)
- **FAISS** - Vector search (CPU-only)
- **Docker** - One-command deployment

---

## Inspired By

- [Butterfly RSI](https://github.com/ButterflyRSI/Butterfly-RSI) - Drift detection & dream consolidation
- ICLR 2026 Workshop - Recursive self-improvement research
- Neuroscience - Memory consolidation during sleep

---

## Roadmap

### v0.7.0+ (Future)

- Memory compression (hierarchical summaries)
- Memory replay (background consolidation)  
- Meta-learning analytics (optimize over time)
- Alternative vector DBs (Milvus, Qdrant)

### v0.6.1 ✅ (Released 2026-02-04)

**Sleep Scheduler** - Automatic memory consolidation
- Background scheduler runs fade cycles every 24 hours
- Like the brain during sleep - no manual cron needed
- Graceful startup (5 min delay) and shutdown
- New endpoint: `/memory/sleep/status`

### v0.6.0 ✅ (Released 2026-02-04)

**Memory Fading** - Biologically-inspired forgetting
- Strength score based on quality, recall success, access frequency
- Exponential decay (30-day half-life, configurable)
- Memories fade to "dormant" status (excluded from search, not deleted)
- Auto-boost on access - searching strengthens memories

### v0.5.0 ✅ (Released 2026-02-04)

**E5-base-v2 Embedding Model** - Significantly better semantic search
- Upgraded from `all-MiniLM-L6-v2` to `intfloat/e5-base-v2`
- 2x richer representations (768 vs 384 dimensions)
- Better semantic understanding and nuanced matching
- Auto-rebuild FAISS index on dimension mismatch

### v0.4.0 ✅ (Released 2026-02-04)

**Temporal Weighting & Context Expansion**
- Boost recent + high-quality memories in search
- Auto-expand related memories via knowledge graph

### v0.3.0 ✅ (Released 2026-02-03)

**Spaced Repetition** - Memory review scheduling based on Ebbinghaus forgetting curve

### v0.2.x ✅

**Foundation** - Episodic/semantic memory, knowledge graphs, active recall, learning sessions


## License

Apache 2.0
