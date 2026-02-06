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
🎯 **Intent-Aware Retrieval** - Auto-adjusts search based on query intent (v0.13)  
🔁 **Self-Improving** - Quality evaluation and drift detection  
🧪 **Neuroscience-Inspired** - Dream consolidation, homeostatic regulation  
📚 **Active Learning** - Tracks knowledge gaps, suggests what to learn (v0.11)  
🎭 **Episodic Memory** - Store experiences, not just facts (v0.11)  
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

1. **Memory** - Local embeddings (E5) + FAISS vector search
2. **Mirror** - Quality evaluation, drift detection, consolidation
3. **Learning** - Structured sessions with self-verification

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

- **Python 3.11** - Core runtime
- **FastAPI** - REST API with OpenAPI docs
- **E5-base-v2** - Local embeddings (768-dim, high-quality semantic search)
- **FAISS** - Vector similarity search
- **Docker** - Single container deployment

---

## Inspired By

**Memory & Forgetting**
- [Ebbinghaus Forgetting Curve](https://en.wikipedia.org/wiki/Forgetting_curve) - Exponential memory decay model
- [FadeMem (2026)](https://arxiv.org/abs/2504.08000) - Adaptive memory fading for LLMs (45% storage reduction)
- [Google Titans](https://arxiv.org/abs/2501.00663) - Adaptive weight decay with surprise metrics

**Learning & Recall**
- [Spaced Repetition](https://en.wikipedia.org/wiki/Spaced_repetition) - Optimal review scheduling
- [Spreading Activation Theory](https://en.wikipedia.org/wiki/Spreading_activation) - Knowledge graph auto-linking

**Retrieval**
- [SimpleMem (2026)](https://arxiv.org/abs/2601.02553) - Intent-aware retrieval planning, 26% F1 improvement

**Embeddings**
- [E5-base-v2](https://huggingface.co/intfloat/e5-base-v2) - High-quality text embeddings

**Projects**
- [Butterfly RSI](https://github.com/ButterflyRSI/Butterfly-RSI) - Drift detection & dream consolidation
- ICLR 2026 Workshop - Recursive self-improvement research

---

## Roadmap

### Future

- Alternative vector DBs (Milvus, Qdrant)

### Current Features

- **Intent-Aware Retrieval** ⭐ NEW (v0.13) - Auto-adjusts search params based on query intent
- **Memory Compression & Replay** - Consolidate similar memories, strengthen via replay
- **Heuristic Quality Assessment** - Auto-runs during sleep cycle - Auto-evaluate memory quality without LLM (usage patterns)
- **Reflection Phase** - Synthesize memories into higher-level insights (inspired by Generative Agents)
- **Auto-Reflection** - Sleep scheduler automatically reflects on topics every 24h
- **Memory Fading** - Biologically-inspired forgetting with sleep scheduler
- **E5-base-v2 Embeddings** - High-quality semantic search
- **Temporal Weighting** - Boost recent + high-quality memories
- **Context Expansion** - Auto-expand related memories via knowledge graph
- **Spaced Repetition** - Memory review scheduling
- **Episodic/Semantic Memory** - Separate experiences from facts
- **Knowledge Graphs** - Memory relationships and auto-linking
- **Learning Sessions** - Structured learning with quality filtering

See [GitHub Releases](https://github.com/compemperor/engram/releases) for detailed changelog.


## License

Apache 2.0
