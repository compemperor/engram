# Engram 🧠

**Memory traces for AI agents**

Self-improving memory system with quality control, drift detection, and learning framework. Built for AI agents that need to learn, remember, and self-correct - with full privacy and zero API costs.

## Features

🔒 **Privacy-First** - Local embeddings, no data leaves your machine  
🧠 **Smart Memory** - Semantic search with quality filtering  
🔁 **Self-Improving** - Quality evaluation and drift detection  
🧪 **Neuroscience-Inspired** - Dream consolidation, homeostatic regulation  
🔌 **Framework-Agnostic** - Works with any LLM  
📦 **All-in-One** - Single Docker container, FastAPI server  

## Quick Start

```bash
# Docker (recommended)
docker run -d -p 8765:8765 -v ./memories:/data/memories compemperor/engram:latest

# Or run locally
pip install -r requirements.txt
python -m engram.api
```

## API Endpoints

### Memory Operations
- `POST /memory/add` - Add lesson/memory
- `POST /memory/search` - Semantic search
- `GET /memory/recall/{topic}` - Get all memories for topic
- `GET /memory/stats` - Memory statistics

### Learning Sessions
- `POST /learning/session/start` - Start learning session
- `POST /learning/session/explore` - Explore sources
- `POST /learning/session/verify` - Self-verification checkpoint
- `POST /learning/session/consolidate` - Consolidate & save quality learnings

### Quality & Drift
- `POST /mirror/evaluate` - Evaluate session quality
- `GET /mirror/drift` - Check drift metrics
- `POST /mirror/consolidate` - Quality-filtered consolidation

### Health
- `GET /health` - Service health check
- `GET /` - API documentation (OpenAPI/Swagger)

## Architecture

```
┌─────────────────────────────┐
│   FastAPI Server            │  <- REST API, OpenAPI docs
├─────────────────────────────┤
│   Mirror (Quality Layer)    │  <- Self-evaluation, drift detection
├─────────────────────────────┤
│   Learning (Sessions)       │  <- Structured learning with verification
├─────────────────────────────┤
│   Memory (Storage + Search) │  <- FAISS, embeddings, recall
└─────────────────────────────┘
```

## Use Cases

- **AI Agents** - Give your agent persistent memory with quality control
- **Personal Knowledge Base** - Build your external brain
- **Research Assistants** - Track learnings over time with drift detection
- **Trading Bots** - Remember lessons, prevent repeating mistakes
- **Chatbots** - Maintain context and personality across sessions

## Inspired By

- [Butterfly RSI](https://github.com/ButterflyRSI/Butterfly-RSI) - Drift detection & dream consolidation
- ICLR 2026 Workshop - Recursive self-improvement research
- Neuroscience - Memory consolidation during sleep

## License

Apache 2.0

---

**Status:** 🚧 In Development  
**Author:** compemperor, Clawdy  
**Built:** 2026-02-02
