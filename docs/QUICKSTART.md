# Engram Quickstart 🧠

Get up and running with Engram in 5 minutes.

---

## Option 1: Docker (Recommended)

```bash
# Start with docker-compose
docker-compose up -d

# Or build and run manually
docker build -t engram .
docker run -d -p 8765:8765 -v ./memories:/data/memories engram
```

**API will be available at:** http://localhost:8765  
**Docs:** http://localhost:8765/docs

---

## Option 2: Local Python

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API
python -m engram

# Or use the start script
./scripts/start.sh
```

---

## Quick Test

```bash
# Check health
curl http://localhost:8765/health

# Add a lesson
curl -X POST http://localhost:8765/memory/add \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "trading",
    "lesson": "Don'\''t chase missed trades",
    "source_quality": 9,
    "understanding": 5.0
  }'

# Search
curl -X POST http://localhost:8765/memory/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "trading mistakes",
    "top_k": 5
  }'

# Recall topic
curl http://localhost:8765/memory/recall/trading
```

---

## Python Client Example

```python
from engram import MemoryStore

# Initialize
memory = MemoryStore(path="./memories")

# Add lesson
memory.add_lesson(
    topic="trading",
    lesson="Set limit orders 2h before close",
    source_quality=8,
    understanding=4.5
)

# Search
results = memory.search("trading strategies", top_k=5)

for result in results:
    print(f"{result.memory.lesson} (score: {result.score})")

# Recall
lessons = memory.recall("trading", min_quality=7)
```

---

## Learning Session Example

```python
from engram.learning import LearningSession

# Start session
session = LearningSession(
    topic="recursive self-improvement",
    duration_min=30
)

# Add notes
session.add_note(
    content="Key finding: RSI is now practice, not theory",
    source_url="https://recursive-workshop.github.io",
    source_quality=9
)

# Self-verification checkpoint
session.verify(
    topic="RSI frameworks",
    understanding=4.0,
    sources_verified=True,
    gaps=["Implementation details needed"],
    applications=["Could apply to my learning sessions"]
)

# Add insights
session.add_insight("Drift detection prevents knowledge degradation")

# Consolidate (v0.11.2+: saves to Engram memory, not file)
summary = session.consolidate()
print(f"Session {summary['session_id']}: {summary['insights_count']} insights")
```

---

## API Endpoints

### Memory
- `POST /memory/add` - Add lesson
- `POST /memory/search` - Semantic search
- `GET /memory/recall/{topic}` - Get all for topic
- `GET /memory/stats` - Statistics

### Quality (Mirror)
- `POST /mirror/evaluate` - Evaluate session quality
- `GET /mirror/drift` - Check drift metrics
- `GET /mirror/metrics` - Current metrics

### Learning
- `POST /learning/session/start` - Start session
- `POST /learning/session/{id}/note` - Add note
- `POST /learning/session/{id}/verify` - Verification checkpoint
- `POST /learning/session/{id}/consolidate` - Finalize

---

## Interactive API Docs

Visit **http://localhost:8765/docs** for interactive Swagger documentation.

You can test all endpoints directly from your browser!

---

## Next Steps

1. **Run the example:** `python examples/quickstart.py`
2. **Read the docs:** Check `/docs` directory
3. **Build your agent:** Integrate Engram into your AI agent
4. **Customize:** Adjust thresholds, add features

---

## Troubleshooting

**"Module not found":**
```bash
pip install -r requirements.txt
```

**"FAISS not available":**
- Install: `pip install faiss-cpu`
- Or disable FAISS: `MemoryStore(enable_faiss=False)`

**Docker issues:**
```bash
# Rebuild
docker-compose down
docker-compose up --build
```

---

**Questions?** Open an issue on GitHub!

🦀 Happy building!
