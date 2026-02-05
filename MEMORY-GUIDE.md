# Engram Memory Utilization Guide

**For agents and skills: How to use Engram memory most efficiently**

---

## ⚠️ CRITICAL RULES (from user)

**1. Use Engram ONLY - NO manual markdown files**
- Learning sessions save automatically when quality >= 8
- If consolidation returns `consolidate: false` → STOP
- Do NOT manually save to bypass the filter
- That's trash that failed quality check - accept it

**2. Quality 8 is MINIMUM**
- If you can't rate a note 8+, DIG DEEPER
- Surface-level research = trash
- Quality 8 = 2+ verified sources, tested, proven
- Stuck at 6-7? Search more, verify harder, find better sources

**3. Use ENTIRE time span given**
- User says 10 minutes? Spend FULL 10 minutes
- Finish in 2 minutes? You didn't dig deep enough
- Fast ≠ thorough
- Keep researching until ALL notes are quality 8+

**4. Trust the consolidation filter**
- If it says no, it means your research was trash
- No manual saves to bypass
- Only exception: episodic events (trades, deployments)

---

## Quick Decision Tree

```
Need to remember something?
├─ Is it an event/experience? → memory/add (episodic)
├─ Is it a fact/rule/lesson? → memory/add (semantic)
└─ Not sure? → semantic (default)

Need to recall something?
├─ Know the exact topic? → /memory/recall/{topic}
├─ Fuzzy concept/question? → /memory/search
├─ Related to another memory? → /memory/related/{id}
└─ Want to test understanding? → /recall/challenge

Learning something new?
├─ Short (<5 min)? → Just add memories directly
├─ Medium (5-15 min)? → Learning session (auto-saves)
└─ Long (15+ min)? → Learning session + verify

Want to synthesize insights? → /memory/reflect ⭐ NEW
├─ Have 3+ memories on a topic? → Generate reflection
├─ Want meta-level understanding? → Reflection phase
└─ Periodic maintenance? → Reflect on major topics
```

---

## When to Use Each Endpoint

### 1. `/memory/add` - Store New Memory

**Use when:**
- You learned something worth keeping
- You want to document an event
- Quality >= 8 (2+ verified sources)
- Understanding is clear

**Don't use when:**
- Uncertain about info (search first!)
- Duplicate of existing memory (search first!)
- Quality < 7 (not worth storing)

**Example:**
```python
# Good: Verified, tested, worth remembering
requests.post(f"{API}/memory/add", json={
    "topic": "trading/risk",
    "lesson": "Kelly Criterion: f = (bp-q)/b. Use 0.25x-0.5x fractional.",
    "source_quality": 10,  # Tested in production
    "understanding": 5.0   # Fully understand
})

# Bad: Uncertain, single source, unverified
requests.post(f"{API}/memory/add", json={
    "topic": "trading",
    "lesson": "Someone on Reddit said OVZON will moon",  # ❌ Quality 3, don't store!
    "source_quality": 3
})
```

---

### 2. `/memory/search` - Semantic Search

**Use when:**
- You have a question or fuzzy concept
- You don't know the exact topic
- You want to find related memories
- You're exploring what you know about X

**Best for:**
- "What do I know about X?"
- "Have I learned anything related to Y?"
- "Show me mistakes I made with Z"

**Example:**
```python
# Fuzzy question
r = requests.post(f"{API}/memory/search", json={
    "query": "When should I avoid trading?",  # Natural language!
    "top_k": 5,
    "min_quality": 8  # Only high-quality memories
})

# Exploration
r = requests.post(f"{API}/memory/search", json={
    "query": "OVZON mistakes lessons learned",
    "top_k": 10
})
```

**Efficiency tip:** Always set `min_quality` to filter noise!

---

### 3. `/memory/recall/{topic}` - Get All Memories for Topic

**Use when:**
- You know the EXACT topic structure
- You want ALL memories (not just top 5)
- You're reviewing a specific category
- You're generating a summary/report

**Best for:**
- "Show me all trading lessons"
- "What have I learned about OVZON?"
- "List all deployment memories"

**Example:**
```python
# Get all trading memories
r = requests.get(f"{API}/memory/recall/trading", params={
    "min_quality": 7
})

# Get all OVZON intel
r = requests.get(f"{API}/memory/recall/market-intel/ovzon")
```

**Topic structure:**
- Use `/` for hierarchy: `trading/risk`, `intel/osint`
- Use `-` within words: `market-intel`, `bug-bounty`
- Lowercase, no spaces

**Efficiency tip:** If you're not sure of the exact topic, use `/memory/search` instead!

---

### 4. `/memory/related/{memory_id}` - Graph-Based Recall

**Use when:**
- You found a relevant memory and want more like it
- You're exploring knowledge connections
- You want to discover related concepts

**Best for:**
- "This memory is relevant, what else is connected?"
- "Find memories with similar entities/concepts"
- "Discover knowledge I didn't explicitly search for"

**Example:**
```python
# First, search to find a relevant memory
search = requests.post(f"{API}/memory/search", json={
    "query": "Kelly Criterion position sizing"
}).json()

memory_id = search["results"][0]["memory"]["memory_id"]

# Then find related memories
related = requests.get(f"{API}/memory/related/{memory_id}").json()

for mem in related["related"]:
    print(mem["lesson"])
```

**Efficiency tip:** Combine search → related for knowledge graph exploration!

---

### 5. `/recall/challenge` - Active Recall Testing

**Use when:**
- You want to test your understanding
- You're reviewing before applying knowledge
- You want to strengthen memory retention
- You have spare time (not urgent tasks)

**Don't use when:**
- You're in the middle of urgent work
- You need specific info NOW (use search instead!)
- You're just exploring (use search)

**Example:**
```python
# Get a challenge
challenge = requests.get(f"{API}/recall/challenge").json()["challenge"]

print(challenge["question"])
# "What is the key lesson about position sizing?"

# Submit answer
requests.post(f"{API}/recall/submit", json={
    "challenge_id": challenge["id"],
    "answer": "Use Kelly Criterion: f=(bp-q)/b, but fractional (0.25x-0.5x) in practice"
})
```

**Efficiency tip:** Do challenges during heartbeat idle time, not during active tasks!

---

### 6. Learning Sessions - Structured Learning

**Use when:**
- Learning something new (5+ minutes)
- Deep dive on a topic (10-20 sources)
- You want auto-save of high-quality notes
- You need verification/consolidation

**Workflow:**
```python
# 1. Start session
session = requests.post(f"{API}/learning/session/start", params={
    "topic": "docker-optimization",
    "duration_min": 10
}).json()

session_id = session["session_id"]

# 2. Add notes as you learn
requests.post(f"{API}/learning/session/{session_id}/note", json={
    "content": "Multi-stage builds reduce image size by 92%",
    "source_quality": 9,
    "source_url": "https://docs.docker.com/build/..."
})

# 3. Verify understanding (optional, every 5-10 notes)
requests.post(f"{API}/learning/session/{session_id}/verify", json={
    "topic": "docker-optimization",
    "understanding": 4.5,
    "sources_verified": true,
    "gaps": ["BuildKit SSH forwarding"],
    "applications": ["Apply to Engram image"]
})

# 4. Consolidate (auto-saves quality >= 8)
result = requests.post(f"{API}/learning/session/{session_id}/consolidate").json()

if result["evaluation"]["consolidate"]:
    print(f"Saved {len(result['saved_memories'])} memories!")
```

**When NOT to use:**
- Quick lookups (<2 min)
- Single fact storage (use `/memory/add` directly)
- Urgent tasks (overhead not worth it)

---

## Efficiency Best Practices

### 1. Search Before Storing (Avoid Duplicates)

```python
# ❌ BAD: Store without checking
requests.post(f"{API}/memory/add", json={
    "topic": "trading",
    "lesson": "Don't chase trades emotionally"
})

# ✅ GOOD: Check first
existing = requests.post(f"{API}/memory/search", json={
    "query": "emotional trading mistakes",
    "top_k": 3
}).json()

if not any("chase" in m["memory"]["lesson"] for m in existing["results"]):
    # Not duplicate, safe to store
    requests.post(f"{API}/memory/add", json=...)
```

### 2. Use min_quality to Filter Noise

```python
# ❌ BAD: Get all memories (including low-quality)
r = requests.post(f"{API}/memory/search", json={
    "query": "trading"
})

# ✅ GOOD: Only high-quality
r = requests.post(f"{API}/memory/search", json={
    "query": "trading",
    "min_quality": 8  # Verified, tested, proven
})
```

### 3. Topic Hierarchy for Organization

```python
# ❌ BAD: Flat structure
"trading"
"trading2"
"trading-kelly"
"ovzon"
"ovzon-sentiment"

# ✅ GOOD: Hierarchical
"trading/risk"
"trading/algorithms"
"trading/mistakes"
"market-intel/ovzon"
"market-intel/saab"
```

### 4. Batch Recall at Start, Not During Work

```python
# ✅ GOOD: Load context at session start
def init_session(task_context):
    """Load relevant memories once at start"""
    memories = requests.post(f"{API}/memory/search", json={
        "query": task_context,
        "top_k": 10,
        "min_quality": 7
    }).json()["results"]
    
    return memories  # Use throughout session

# ❌ BAD: Search every time you need something
# (wasteful, redundant API calls)
```

### 5. Learning Sessions for Deep Work Only

```python
# ✅ GOOD: 10+ minutes, 10+ sources, complex topic
start_learning_session("kubernetes-security", duration_min=15)

# ❌ BAD: 2 minutes, single fact
start_learning_session("what-is-docker", duration_min=2)
# ^ Just use /memory/add directly!
```

### 6. Use Related for Knowledge Graph Exploration

```python
# ✅ GOOD: Explore connections
def explore_knowledge(concept):
    # Search for entry point
    results = search_memory(concept, top_k=1)
    memory_id = results[0]["memory"]["memory_id"]
    
    # Find related
    related = requests.get(f"{API}/memory/related/{memory_id}").json()
    
    # Discover connected knowledge
    return related["related"]

# Example: "trading" → Kelly Criterion → risk management → stop-loss
```

---

## Common Patterns for Agents

### Pattern 1: Task Startup Recall

```python
def start_task(task_description):
    """Always recall relevant memories before starting work"""
    
    # 1. Search for related lessons
    lessons = requests.post(f"{API}/memory/search", json={
        "query": f"{task_description} mistakes lessons learned",
        "top_k": 5,
        "min_quality": 8
    }).json()["results"]
    
    # 2. Recall topic-specific memories
    topic = extract_topic(task_description)  # e.g., "trading" from "analyze OVZON"
    if topic:
        topic_memories = requests.get(
            f"{API}/memory/recall/{topic}",
            params={"min_quality": 7}
        ).json()["memories"]
    
    # 3. Work with combined context
    context = lessons + topic_memories
    return context
```

### Pattern 2: Learning + Application

```python
def learn_and_apply(topic, duration_min):
    """Deep learning session with immediate application"""
    
    # 1. Start learning session
    session = start_learning_session(topic, duration_min)
    
    # 2. Gather knowledge (add notes as you learn)
    for source in sources:
        add_note(session, source)
    
    # 3. Verify understanding
    verify_session(session, understanding=4.5)
    
    # 4. Consolidate (auto-saves quality >= 8)
    result = consolidate_session(session)
    
    # 5. Apply immediately (while fresh)
    if result["saved_memories"]:
        apply_knowledge(result["saved_memories"])
```

### Pattern 3: Mistake Capture

```python
def capture_mistake(context, what_happened, lesson):
    """Always document mistakes for future prevention"""
    
    requests.post(f"{API}/memory/add", json={
        "topic": f"mistakes/{context}",
        "lesson": f"MISTAKE: {what_happened}. LESSON: {lesson}",
        "source_quality": 10,  # Learned the hard way!
        "understanding": 5.0,
        "memory_type": "episodic"
    })
```

### Pattern 4: Heartbeat Memory Maintenance

```python
def heartbeat_memory_review():
    """Periodic memory consolidation (every few days)"""
    
    # 1. Get active recall challenge
    challenge = requests.get(f"{API}/recall/challenge").json()
    
    # 2. Review recent memories
    stats = requests.get(f"{API}/memory/stats").json()
    
    # 3. If memory count growing, consolidate topics
    if stats["total_memories"] > 50:
        # Review and merge similar memories
        pass
```

---

## Anti-Patterns (What NOT to Do)

### ❌ Storing Low-Quality Info
```python
# Don't store rumors, opinions, unverified claims
requests.post(f"{API}/memory/add", json={
    "lesson": "Reddit says OVZON will 10x",
    "source_quality": 3  # ❌ Don't store quality < 7!
})
```

### ❌ Searching Without Filters
```python
# Wasteful: Returns low-quality noise
requests.post(f"{API}/memory/search", json={
    "query": "trading"
    # ❌ No min_quality filter!
})
```

### ❌ Duplicating Memories
```python
# Check first, then store!
# ❌ Storing "Don't chase trades" 5 times
```

### ❌ Using Learning Sessions for Quick Facts
```python
# ❌ Overhead not worth it for single facts
start_learning_session("what-is-ssh", duration_min=1)

# ✅ Just store directly
requests.post(f"{API}/memory/add", json=...)
```

### ❌ Flat Topic Structure
```python
# ❌ Hard to organize
"trading1", "trading2", "trading3"

# ✅ Hierarchical
"trading/risk", "trading/algorithms", "trading/mistakes"
```

---

## Summary: Decision Matrix

| Need | Use | Why |
|------|-----|-----|
| Store fact/lesson | `/memory/add` | Direct, fast |
| Store event/experience | `/memory/add` (episodic) | Preserves context |
| Fuzzy search | `/memory/search` | Natural language |
| Get all from topic | `/memory/recall/{topic}` | Complete list |
| Find connections | `/memory/related/{id}` | Knowledge graph |
| Test understanding | `/recall/challenge` | Active recall |
| Deep learning (5+ min) | Learning session | Auto-save, structured |
| Quick fact (<2 min) | `/memory/add` directly | No overhead |

**Golden Rule:** Search before storing, filter by quality, organize by topic hierarchy.

---

**Last updated:** 2026-02-03  
**Engram version:** v0.2.1  
**Status:** Production guidelines
