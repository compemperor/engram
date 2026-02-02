# Engram 🧠

**Memory traces for AI agents**

Self-improving memory system with quality control, drift detection, and learning framework. Built for AI agents that need to learn, remember, and self-correct - with full privacy and zero API costs.

---

**🤖 For AI Agents:** See [AGENTS.md](AGENTS.md) for quick integration guide

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

- **[AGENTS.md](AGENTS.md)** - Quick guide for AI agents
- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute tutorial
- **[examples/](examples/)** - Code examples
- **[/docs](http://localhost:8765/docs)** - Interactive API docs (when running)

---

## Technology

- **Python 3.11** - Core language
- **FastAPI + Pydantic** - REST API with validation
- **sentence-transformers** - Local embeddings (all-MiniLM-L6-v2)
- **FAISS** - Vector search (CPU-only)
- **Docker** - One-command deployment

**Note:** Inspired by Butterfly RSI's concepts (drift detection, dream consolidation), but built from scratch with our own implementation.

---

## Inspired By

- [Butterfly RSI](https://github.com/ButterflyRSI/Butterfly-RSI) - Drift detection & dream consolidation
- ICLR 2026 Workshop - Recursive self-improvement research
- Neuroscience - Memory consolidation during sleep

---

## License

Apache 2.0
