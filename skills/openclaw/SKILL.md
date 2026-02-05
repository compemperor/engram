# Engram - AI Agent Memory System

**Repository:** https://github.com/compemperor/engram  
**API Endpoint:** http://localhost:8765  
**Container:** engram (auto-restart)  

Self-improving memory system with episodic/semantic memory, active recall, and learning sessions.

**📚 For detailed usage guidance:** See [MEMORY-GUIDE.md](./MEMORY-GUIDE.md)

---

## 🔧 OpenClaw Setup

To use Engram as your memory system, replace the default workspace files:

**MEMORY.md** (replace entire file):
```markdown
# MEMORY.md

**All memory is in Engram.** This file exists only to tell you that.

## Startup
1. Search Engram: `curl http://localhost:8765/memory/search -X POST -d '{"query": "startup critical rules"}'`
2. Load context relevant to current task

## Engram API
- **Endpoint:** http://localhost:8765
- **Search:** POST /memory/search
- **Recall:** GET /memory/recall/{topic}
- **Store:** POST /memory/add (quality >= 8 only)

That's it. Everything else is in Engram.
```

**SOUL.md** (add to end or replace startup instruction):
```markdown
**FIRST ACTION EVERY SESSION:** Search Engram for "startup critical rules". No exceptions.
```

**Why:** OpenClaw loads MEMORY.md and SOUL.md each session. By pointing them to Engram, all memory is centralized and searchable.

---

## ✨ Key Features

**E5-base-v2 Embedding Model** - High-quality semantic search
- 768-dimensional embeddings for nuanced matching
- Finds "don't chase FOMO" when searching "avoid emotional trades"
- Automatic query/passage prefix handling

**Memory Fading** - Biologically-inspired forgetting
- Memories have strength scores (quality × recall × access)
- Unused memories fade to dormant (excluded from search, not deleted)
- Sleep scheduler runs consolidation automatically every 24h

**Temporal Weighting** - Recent and high-quality memories rank higher
- Exponential recency decay (30-day half-life)
- Quality boost based on source_quality (1-10)

**Context-Aware Retrieval** - Auto-expand related memories
- Follows knowledge graph relationships
- Configurable expansion depth (1-3 levels)

**Heuristic Quality Assessment (v0.8)** - Auto-evaluate memory quality
- GET /memory/quality/{id} to assess single memory
- POST /memory/quality/assess for batch assessment
- No LLM required - uses behavioral signals

**Reflection Phase (v0.7)** - Synthesize memories into insights
- POST /memory/reflect to consolidate topic memories
- Auto-runs during sleep cycle (every 24h)

**Configurable Embedding Model (v0.9)** - ENGRAM_EMBEDDING_MODEL env var
- Options: e5-base-v2 (default), e5-large-v2, multilingual-e5-large
- Creates "reflection" memory type linked to sources
- GET /memory/reflect/candidates to see what needs reflection

---

## Core Concepts

### Memory Types

**Episodic Memory** - Experiences and events with context
- "OVZON filled at 54.50 SEK on 2026-02-03"
- "Learning session on market intel lasted 15 minutes"
- "Deployment test completed at 11:15 UTC"

**Semantic Memory** - Facts, rules, and lessons
- "Adjust limit orders before market close"
- "Always verify sources before trusting"
- "Quality >= 8 saves automatically"

**When to use:**
- Events/experiences → `memory_type="episodic"`
- Facts/rules/lessons → `memory_type="semantic"`  (default)

### Quality Scale

**1-6:** Opinions, rumors, single unverified sources, social media  
**7:** Good source OR verified expert stating facts on-topic  
**8-9:** Multiple verified sources, tested personally, documented  
**10:** Official documentation, research papers, proven in production

**Critical rules:**
- Social media = MAX 6 (opinions), 7 (expert facts only)
- Before rating 8+: verify 2+ independent sources
- When uncertain: rate lower (6-7 is fine)

**⚠️ QUALITY 8 IS MINIMUM FOR STORAGE**
- If you can't rate a note 8+, DIG DEEPER
- Surface-level research = trash
- Keep searching until you find quality 8+ sources
- Consolidation will reject anything < 8 (as it should)

---

## API Reference

### Store Memory

```python
import requests

API = "http://localhost:8765"

# Add semantic memory (facts/rules)
requests.post(f"{API}/memory/add", json={
    "topic": "trading",
    "lesson": "Don't chase missed trades emotionally",
    "source_quality": 9,
    "understanding": 4.5  # optional, 1-5 scale
})

# Add episodic memory (events/experiences)
requests.post(f"{API}/memory/add", json={
    "topic": "deployment",
    "lesson": "Engram deployed successfully at 11:15 UTC",
    "source_quality": 8,
    "metadata": {"version": "0.2.0", "duration_min": 5}
})
```

### Search Memories

```python
# Semantic search with temporal weighting
r = requests.post(f"{API}/memory/search", json={
    "query": "market timing mistakes",
    "top_k": 5,
    "min_quality": 7,  # optional filter
    "use_temporal_weighting": True,  # ✨ NEW: boost recent + high-quality memories
    "auto_expand_context": False,  # ✨ NEW: auto-include related memories
    "expansion_depth": 1  # ✨ NEW: how deep to expand (1-3)
})

results = r.json()["results"]
for hit in results:
    print(f"{hit['score']:.2f}: {hit['memory']['lesson']}")

# Context expansion example (automatically includes related memories)
r = requests.post(f"{API}/memory/search", json={
    "query": "trading mistakes",
    "top_k": 1,
    "auto_expand_context": True,  # Enables knowledge graph expansion
    "expansion_depth": 1  # Pull related memories 1 hop away (1-3 max)
})
# Returns: top 1 match + its related memories via knowledge graph
# Example: 1 direct result → 2-3 total results with relationships included
```

### Recall by Topic

```python
# Get all memories for a specific topic
r = requests.get(f"{API}/memory/recall/trading", params={
    "min_quality": 7  # optional filter
})

memories = r.json()["memories"]
for memory in memories:
    print(f"- {memory['lesson']}")
```

### Related Memories (Knowledge Graph)

```python
# Find memories related to a specific memory (graph-based)
# First, get a memory ID from search or recall
r = requests.post(f"{API}/memory/search", json={
    "query": "position sizing"
})
memory_id = r.json()["results"][0]["memory"]["memory_id"]

# Then find related memories
r = requests.get(f"{API}/memory/related/{memory_id}")
related = r.json()["related"]

for mem in related:
    print(f"- {mem['lesson']}")
```

### Create Relationships (Knowledge Graph)

**⚡ Auto-Linking:**  
Engram automatically creates `related_to` relationships when storing memories! Uses semantic similarity (threshold: 0.75, max: 3 links per memory). Based on spreading activation theory from cognitive science.

```python
# Just add a memory - auto-linking happens automatically
requests.post(f"{API}/memory/add", json={
    "topic": "trading",
    "lesson": "OVZON loss taught me about FOMO",
    "source_quality": 9
})
# Auto-links to similar memories about trading/FOMO/mistakes

# Check what got linked
r = requests.get(f"{API}/memory/stats")
print(f"Graph nodes: {r.json()['knowledge_graph']['total_nodes']}")
print(f"Auto-linked relationships: {r.json()['knowledge_graph']['total_relationships']}")
```

**Manual relationships** (for specific connections):

```python
# Add a relationship between two memories
# Relationship types: caused_by, related_to, contradicts, supports, example_of, derived_from

# First, get memory IDs
r = requests.post(f"{API}/memory/search", json={"query": "bug fix"})
from_id = r.json()["results"][0]["memory"]["memory_id"]

r = requests.post(f"{API}/memory/search", json={"query": "debugging rule"})
to_id = r.json()["results"][0]["memory"]["memory_id"]

# Create relationship
requests.post(f"{API}/memory/relationship", json={
    "from_id": from_id,
    "to_id": to_id,
    "relation_type": "example_of",  # bug fix is example of debugging rule
    "confidence": 0.9,
    "metadata": {"context": "production bug"}
})

# Query relationships
r = requests.get(f"{API}/memory/related/{to_id}")
print(f"Found {r.json()['count']} related memories")
```

### Get Stats

```python
r = requests.get(f"{API}/memory/stats")
stats = r.json()

print(f"Total: {stats['total_memories']}")
print(f"Episodic: {stats['episodic_memories']}")
print(f"Semantic: {stats['semantic_memories']}")
print(f"Topics: {stats['topics']}")
```

### Active Recall

Engram can quiz you on memories to strengthen retention:

```python
# Get a recall challenge
r = requests.get(f"{API}/recall/challenge")
challenge = r.json()["challenge"]

print(challenge["question"])  # "What is the key lesson about X?"
print(challenge["difficulty"])  # "medium"

# After answering, submit your response
requests.post(f"{API}/recall/submit", json={
    "challenge_id": challenge["id"],
    "answer": "Your answer here",
    "confidence": 0.8  # 0-1 scale
})

# View recall stats
r = requests.get(f"{API}/recall/stats")
stats = r.json()["statistics"]
print(f"Success rate: {stats['success_rate']*100}%")
```

### Reflection Phase (v0.7)

Synthesize multiple memories into higher-level insights:

```python
# Generate reflection on a topic
r = requests.post(f"{API}/memory/reflect", json={
    "topic": "trading",          # Topic to reflect on
    "min_quality": 7,            # Optional quality filter
    "min_memories": 3,           # Minimum memories required
    "include_subtopics": True    # Include trading/risk, etc.
})
print(r.json()["synthesis"])

# List all reflections
r = requests.get(f"{API}/memory/reflections")

# See what topics need reflection
r = requests.get(f"{API}/memory/reflect/candidates")
print(r.json()["candidates"])  # ["trading", "projects", ...]
```

**Auto-reflection:** Sleep scheduler runs reflections every 24h on topics with 5+ memories that haven't been reflected in 7+ days.

---

## Learning Sessions

Structured learning with auto-consolidation and quality filtering.

### Start Session

```python
# Start a learning session
r = requests.post(f"{API}/learning/session/start", params={
    "topic": "market-intel",
    "duration_min": 15
})
session_id = r.json()["session_id"]
```

### Add Notes

**Notes with quality >= 8 automatically save to memory**

```python
# Add observation (quality < 8 = session notes only)
requests.post(f"{API}/learning/session/{session_id}/note", json={
    "content": "Found 5 tweets mentioning OVZON",
    "source_quality": 6  # Just observation, not saved
})

# Add insight (quality >= 8 = auto-saved to memory)
requests.post(f"{API}/learning/session/{session_id}/note", json={
    "content": "Risk management beats prediction accuracy",
    "source_quality": 9,  # High-quality insight, auto-saved!
    "source_url": "https://example.com/article"  # optional
})
```

### Verify Understanding

```python
# Add verification checkpoint
requests.post(f"{API}/learning/session/{session_id}/verify", json={
    "topic": "risk-management",
    "understanding": 4.5,  # 1-5 scale
    "sources_verified": True,
    "gaps": ["Need to understand position sizing formulas"],  # optional
    "applications": ["Apply 10/10/1 rule to portfolio"]  # optional
})
```

### Consolidate Session

```python
# Finish and consolidate learning session
r = requests.post(f"{API}/learning/session/{session_id}/consolidate")
summary = r.json()

print(f"Notes: {summary['summary']['notes_count']}")
print(f"Understanding: {summary['summary']['average_understanding']}/5")
print(f"Saved to memory: {summary['saved_to_memory']}")  # High-quality notes
```

### List Sessions

```python
r = requests.get(f"{API}/learning/sessions")
sessions = r.json()["sessions"]

for session in sessions:
    print(f"{session['topic']}: {session['status']}")
```

---

## Integration Patterns

### Before Tasks - Recall Lessons

```python
def recall_lessons(context: str, min_quality: int = 7) -> list:
    """Recall relevant lessons before starting work"""
    r = requests.post(f"{API}/memory/search", json={
        "query": context,
        "top_k": 5,
        "min_quality": min_quality
    })
    return [hit["memory"]["lesson"] for hit in r.json()["results"]]

# Example usage
lessons = recall_lessons("trading mistakes")
for lesson in lessons:
    print(f"Remember: {lesson}")
```

### During Work - Structured Learning

**⚠️ CRITICAL: ALWAYS use learning sessions for exploration/research!**
- Learning sessions = quality control (consolidation filters quality >= 8)
- Direct memory adds bypass filtering = noise accumulation
- If session endpoints fail → ABORT and inform user immediately

**⚠️ SHELL VARIABLE ISSUE:**
- Each `exec()` call = NEW shell session
- Variables don't persist between calls
- **SOLUTION:** Use helper script or store session_id in file

**Option 1: Use helper script (recommended for OpenClaw agents)**
```bash
# Helper script maintains session_id across exec() calls
./learning-session-helper.sh start "topic" "goal" 10
./learning-session-helper.sh note "content" 8
./learning-session-helper.sh verify "topic" 4.5
./learning-session-helper.sh consolidate
```

**Option 2: Python (for agents with persistent runtime)**
```python
def learn_with_structure(topic: str, duration_min: int = 30):
    """Run structured learning session"""
    
    # Start session (uses query params, NOT JSON body!)
    r = requests.post(f"{API}/learning/session/start", params={
        "topic": topic,
        "duration_min": duration_min
    })
    
    # Check for errors
    if r.status_code != 200:
        raise Exception(f"Learning session failed: {r.text}")
    
    session_id = r.json()["session_id"]
    
    # Your learning logic here...
    # Add notes as you discover things
    
    # Example: Log finding
    requests.post(f"{API}/learning/session/{session_id}/note", json={
        "content": "Discovery here",
        "source_quality": 8  # >= 8 auto-saves
    })
    
    # Verify understanding
    requests.post(f"{API}/learning/session/{session_id}/verify", json={
        "topic": "subtopic",
        "understanding": 4.0,
        "sources_verified": True
    })
    
    # Consolidate
    r = requests.post(f"{API}/learning/session/{session_id}/consolidate")
    return r.json()
```

### After Work - Store Insights

```python
def remember(topic: str, lesson: str, quality: int = 8):
    """Store important insight"""
    requests.post(f"{API}/memory/add", json={
        "topic": topic,
        "lesson": lesson,
        "source_quality": quality
    })

# Example
remember("debugging", "Check logs before adding prints", quality=9)
```

---

## Practical Workflows

### Trading Intel Sweep

```python
# 1. Recall past mistakes
past_mistakes = recall_lessons("trading mistakes timing")

# 2. Start learning session
session_id = start_session("market-intel-sweep", 15)

# 3. Research and log findings
for stock in watchlist:
    # ... do research ...
    log_note(session_id, f"OVZON: {finding}", quality=7)

# 4. Consolidate
summary = consolidate(session_id)

# 5. Store high-quality insights
if found_catalyst:
    remember("market-intel", f"OVZON catalyst: {reason}", quality=8)
```

### X/Twitter Learning

```python
# 1. Start learning session
session_id = start_session("X-learning-AI", 30)

# 2. Search and learn
tweets = search_x("AI agents")
for tweet in tweets:
    # Log observation (quality 6 = not saved)
    log_note(session_id, f"Tweet: {tweet}", quality=6)
    
    # If valuable insight (verify sources first!)
    if valuable and verified:
        log_note(session_id, insight, quality=8)  # Auto-saved!

# 3. Verify understanding
verify(session_id, "AI-agents", understanding=4.0, verified=True)

# 4. Consolidate (auto-saves quality >= 8)
summary = consolidate(session_id)
```

### Bug Investigation

```python
# 1. Recall similar bugs
similar = recall_lessons(f"bug {error_type}")

# 2. Start session
session_id = start_session(f"bug-{ticket_id}", 20)

# 3. Log investigation
log_note(session_id, "Root cause: X", quality=9)  # Auto-saved
log_note(session_id, "Fix: Y", quality=9)  # Auto-saved

# 4. Verify
verify(session_id, "debugging", understanding=4.5, verified=True)

# 5. Consolidate
consolidate(session_id)
```

---

## Container Management

```bash
# Check status
docker ps | grep engram

# View logs
docker logs engram -f

# Restart
docker restart engram

# Health check
curl http://localhost:8765/health
```

---

## User Policy

**Use learning sessions for ALL important tasks** (user request 2026-02-02)

**When to use learning sessions:**
- Important tasks
- Research and analysis
- Debugging complex issues
- Trading analysis
- Any work worth remembering

**Benefits:**
- Structured note-taking
- Auto-save high-quality insights (>= 8)
- Understanding verification
- Quality filtering
- Memory consolidation

---

## Best Practices

**Quality tracking:**
- Be honest with ratings
- Verify sources before 8+
- Expert facts = 7
- Multiple verified sources = 8+

**Topic organization:**
```python
# Good: Hierarchical and specific
"trading/mistakes"
"debugging/python"
"market-intel/OVZON"

# Avoid: Too generic
"notes"
"stuff"
```

**Before tasks:**
```python
# Always recall first
lessons = recall_lessons("task context")
```

**During learning:**
```python
# Use sessions for structure
session_id = start_session("topic", duration_min)
# Log notes as you learn
# Verify understanding
# Consolidate at end
```

**Memory types:**
```python
# Events = episodic
"Deployed at 11:15 UTC"

# Facts/rules = semantic (default)
"Always verify before deploying"
```

---

## Health & Troubleshooting

```bash
# Health check
curl http://localhost:8765/health

# Stats
curl http://localhost:8765/memory/stats | jq

# Container logs
docker logs engram --tail 50

# Rebuild FAISS index (if search broken)
curl -X POST http://localhost:8765/memory/rebuild-index

# Restart container
docker restart engram
```

---

## Interactive Documentation

**Full API docs:** http://localhost:8765/docs

Test all endpoints interactively in your browser.

---

## Summary

**Store memories:**
```python
POST /memory/add
{"topic": "X", "lesson": "Y", "source_quality": 8}
```

**Search & Recall:**
```python
# Semantic search (finds related concepts)
POST /memory/search
{"query": "X", "top_k": 5, "min_quality": 7}

# Get all by topic
GET /memory/recall/{topic}?min_quality=7
```

**Learning sessions:**
```python
POST /learning/session/start?topic=X&goal=Y&target_duration_min=10  # Uses QUERY PARAMS (not JSON body!)
POST /learning/session/{id}/note {"content": "X", "source_quality": 8}
POST /learning/session/{id}/verify {"understanding": 4.0}
POST /learning/session/{id}/consolidate
```

**Active recall:**
```python
GET /recall/challenge - Generate recall challenge (prioritizes due memories)
POST /recall/submit - Submit recall attempt (updates spaced repetition schedule)
GET /recall/due - Get memories due for review
GET /recall/stats - Get recall statistics
```

**Remember:** Quality >= 8 auto-saves. Use learning sessions for important work. Always recall lessons before tasks.
