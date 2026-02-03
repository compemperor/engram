# Engram - Local Memory & Learning System

Self-improving memory system with quality control, drift detection, and learning framework.

## Learning Philosophy 🧠

**The Problem:** Just storing everything creates noise. You need structure to learn effectively.

**Engram's Approach:**
1. **Exploration** - Gather information, take notes
2. **Quality Assessment** - Rate what you learned (1-10)
3. **Verification** - Self-check: Do I actually understand this? (1-5 scale)
4. **Consolidation** - Keep only high-quality learnings (quality >= 8)

**Why Verification Matters:**
- Forces you to articulate understanding
- Identifies gaps before moving on
- Like the Feynman Technique - if you can't explain it, you don't know it

**Why Quality Thresholds:**
- Quality < 8: Useful notes but not permanent memory
- Quality >= 8: High-quality insight → auto-saved to permanent memory
- Understanding < 3: Need to study more
- Understanding >= 4: Ready to apply

**The Flow:**
```
Start Session → Add Notes (quality rating) → Verify Understanding
→ Consolidate (quality >= 8 becomes permanent memory)
```

**Result:** Only verified, high-quality learnings persist. No noise.

---

## ⚠️ Quality Rules (KEEP IT SIMPLE!)

**Rating Scale:**
- **1-6:** Single source, unverified, social media (opinions/rumors)
- **7:** One good source OR verified expert stating facts
- **8+:** TWO+ independent sources, verified

**BEFORE rating 8+:**
- [ ] Did I check 2+ independent sources?
- [ ] Is this verified fact, not speculation?
- [ ] Am I being honest, or inflating to save?

**Social media rules:**
- Random users/opinions = MAX 6
- **Verified experts on-topic stating facts = 7** (can trust single source)
- Check: Is author expert in this field? Are they stating facts or opinions?

**Deep dive:** Don't trust first result. Check multiple sources. Verify claims.

**When uncertain:** Rate lower. Quality 6-7 is fine, verify later.

---

## Quick Reference

**API endpoint:** http://localhost:8765  
**Container:** engram (auto-restart)  
**Memory path:** ~/.openclaw/workspace/memory/

## Core Functions

### Store a Lesson
```python
import requests

def remember(topic: str, lesson: str, quality: int = 8):
    """Store a lesson in Engram"""
    r = requests.post("http://localhost:8765/memory/add", json={
        "topic": topic,
        "lesson": lesson,
        "source_quality": quality,
        "understanding": 4.0  # 1-5 scale
    })
    return r.json()

# Example
remember("trading", "Don't chase missed trades emotionally", quality=9)
```

### Search Memories
```python
def recall(query: str, min_quality: int = 7, top_k: int = 5):
    """Search memories semantically"""
    r = requests.post("http://localhost:8765/memory/search", json={
        "query": query,
        "top_k": top_k,
        "min_quality": min_quality
    })
    results = r.json()["results"]
    return [hit["memory"]["lesson"] for hit in results]

# Example
lessons = recall("trading mistakes")
```

### Get All for Topic
```python
def get_topic(topic: str):
    """Get all memories for a specific topic"""
    r = requests.get(f"http://localhost:8765/memory/recall/{topic}")
    return [m["lesson"] for m in r.json()["memories"]]

# Example
trading_lessons = get_topic("trading")
```

### Evaluate Quality
```python
def evaluate(text: str):
    """Evaluate quality of text before storing"""
    r = requests.post("http://localhost:8765/mirror/evaluate", json={
        "text": text
    })
    result = r.json()
    return result["quality"], result["should_store"]

# Example
quality, should_store = evaluate("This is a test lesson")
if should_store:
    remember("testing", "This is a test lesson", quality=int(quality * 10))
```

## Learning Sessions

### Start a Learning Session
```python
def start_learning(topic: str, duration_min: int = 30):
    """Start a structured learning session"""
    r = requests.post(
        f"http://localhost:8765/learning/session/start?topic={topic}&duration_min={duration_min}"
    )
    return r.json()["session_id"]

# Example
session_id = start_learning("market-intel", duration_min=15)
```

### Add Learning Notes
```python
def log_note(session_id: str, content: str, source_quality: int = 7, source_url: str = None):
    """Log a learning note (quality >= 8 auto-saved to memory)"""
    r = requests.post(
        f"http://localhost:8765/learning/session/{session_id}/note",
        json={
            "content": content,
            "source_quality": source_quality,  # 1-10 (>= 8 becomes insight)
            "source_url": source_url  # optional
        }
    )
    return r.json()

# Example
log_note(session_id, "Found OVZON mentioned in 5 defense tweets", source_quality=8)
log_note(session_id, "Risk management beats prediction accuracy", source_quality=9)
```

### Verify Understanding
```python
def verify_learning(session_id: str, topic: str, understanding: float, applications: list = None):
    """Add verification checkpoint"""
    r = requests.post(
        f"http://localhost:8765/learning/session/{session_id}/verify",
        json={
            "topic": topic,
            "understanding": understanding,  # 1-5
            "sources_verified": True,
            "applications": applications or []
        }
    )
    return r.json()

# Example
verify_learning(session_id, "market-analysis", 4.5, 
    applications=["Apply sentiment to trading decisions", "Use LSTM for prediction"])
```

### Consolidate Session
```python
def consolidate_session(session_id: str):
    """Complete and consolidate learning session"""
    r = requests.post(f"http://localhost:8765/learning/session/{session_id}/consolidate")
    result = r.json()
    return result

# Example
summary = consolidate_session(session_id)
print(f"Notes: {summary['summary']['notes_count']}")
print(f"Understanding: {summary['summary']['average_understanding']}")
print(f"Saved to memory: {summary['saved_to_memory']}")
```

## Workflow

**Before a task:**
```python
# 1. Recall relevant lessons
lessons = recall("task context")
for lesson in lessons:
    print(f"Remember: {lesson}")
```

**During work:**
```python
# 2. Start learning session
session_id = start_learning("topic", "what you're trying to learn")

# 3. Log observations and insights
log_learning(session_id, "observation", "Found X...", 3.0)
log_learning(session_id, "insight", "This means Y...", 4.0)
```

**After completion:**
```python
# 4. Complete session (auto-consolidates)
summary = finish_learning(session_id)

# 5. Store high-quality lessons
if summary["avg_understanding"] >= 3.0:
    remember("topic", "Key lesson learned", quality=8)
```

## Integration with Tasks

### Trading Intel Sweep
```python
# Before sweep
past_mistakes = recall("trading mistakes")
market_insights = recall("market analysis")

# During sweep
session_id = start_learning("market-intel", "Find best swing trade opportunities")
# ... do research ...
log_learning(session_id, "observation", "OVZON up 5% on news X", 3.5)

# After sweep
summary = finish_learning(session_id)
if found_opportunity:
    remember("market-intel", f"OVZON catalyst: {reason}", quality=8)
```

### X/Twitter Learning
```python
# Start learning session
session_id = start_learning("X", "AI trends and news")

# Search and learn
tweets = search_x("AI agents")
for tweet in tweets:
    quality, should_store = evaluate(tweet)
    if should_store:
        log_learning(session_id, "observation", tweet, quality)

# Complete and consolidate
summary = finish_learning(session_id)
```

## Health Check
```bash
curl http://localhost:8765/health
# {"status":"healthy","memory_enabled":true}
```

## Stats
```bash
curl http://localhost:8765/memory/stats
# {"total_memories":42,"topics":["trading","X","AI"],...}
```

## API Docs
http://localhost:8765/docs

## Notes

- **Quality threshold:** Store only 7+ quality lessons
- **Understanding scale:** 1=confused, 3=grasp, 5=mastery
- **Semantic search:** Uses embeddings, finds related concepts
- **Auto-consolidation:** Learning sessions auto-filter and strengthen memories
- **Drift detection:** Monitors memory coherence over time

## Container Management

```bash
# Check status
docker ps | grep engram

# View logs
docker logs engram -f

# Restart
docker restart engram

# Stop
docker stop engram
```

---

## v0.2.0 Features ✨

**Episodic vs Semantic:**
```python
# Episodic (experience/event)
remember_experience("trading", "OVZON filled at 54.50", quality=9, memory_type="episodic")

# Semantic (fact/rule)
remember_rule("trading", "Adjust limit 2h before close", quality=9, memory_type="semantic")
```

**Knowledge Graphs:**
```python
# Get related memories
related = get_related_memories(memory_id="abc123", max_depth=2)
```

**Active Recall:**
```python
# Generate challenge (prioritizes due memories)
challenge = generate_recall_challenge(memory_id="abc123")

# Submit recall attempt (updates spaced repetition schedule)
submit_recall(memory_id="abc123", answer="my answer", confidence=0.9)

# Check memories due for review
due = get_due_reviews()

# Get stats
stats = get_recall_stats(memory_id="abc123")
```

