# Migration Plan: Consolidating to Engram

This document outlines how to migrate from scattered tools to the unified Engram project.

---

## Current State (Before Migration)

### Private Repo: openclaw-skills

**Scattered components:**
```
openclaw-skills/
├── clawdy-memory/          # Memory API (FastAPI)
│   ├── setup.sh
│   ├── memory-api.py
│   ├── build-index.py
│   └── SKILL.md
├── learning-loop/          # Learning framework
│   ├── scripts/learn.sh
│   └── SKILL.md
└── (other skills...)
```

**Issues:**
- Tied to OpenClaw structure
- Not reusable by others
- No unified packaging
- Duplicate functionality

---

## New State (After Migration)

### Public Repo: engram

**Unified project:**
```
engram/                     # Standalone, pip installable
├── engram/                 # Core package
│   ├── memory/            # Refactored clawdy-memory
│   ├── mirror/            # New quality control
│   └── learning/          # Refactored learning-loop
├── integrations/
│   └── openclaw/          # OpenClaw-specific wrapper
└── (docs, tests, etc.)
```

**Benefits:**
- Framework-agnostic
- Public, reusable
- Professional packaging
- No duplication

---

## Migration Steps

### Step 1: Push Engram to GitHub ✅

```bash
cd ~/.openclaw/workspace/engram

# Initialize repo
git init
git add .
git commit -m "Initial commit: Engram v0.1.0

Unified memory system combining:
- Memory storage (clawdy-memory refactored)
- Quality control (MirrorLoop implemented)  
- Learning framework (learning-loop refactored)

Features:
- FastAPI REST API
- Local embeddings (sentence-transformers)
- FAISS vector search
- Quality evaluation + drift detection
- Docker containerization
- Pip installable

Apache 2.0 license"

# Add remote (you need to create repo on GitHub first)
git remote add origin git@github.com:compemperor/engram.git

# Push
git push -u origin main
```

### Step 2: Update openclaw-skills Repo

**Option A: Deprecate old skills** (Recommended)

```bash
cd ~/.openclaw/workspace/skills

# Create deprecation notices
cat > clawdy-memory/DEPRECATED.md << 'EOF'
# DEPRECATED

This skill has been consolidated into **Engram**.

**New repo:** https://github.com/compemperor/engram

**Migration:**
```bash
# Stop old service
docker stop clawdy-memory

# Use Engram instead
docker run -d -p 8765:8765 compemperor/engram
```

**OpenClaw integration:** See `engram/integrations/openclaw/`
EOF

cat > learning-loop/DEPRECATED.md << 'EOF'
# DEPRECATED

This skill has been consolidated into **Engram**.

**New repo:** https://github.com/compemperor/engram

**Usage:**
```python
from engram.learning import LearningSession

session = LearningSession(topic="...", duration_min=30)
# ... (see Engram docs)
```

**API endpoint:** `POST /learning/session/start`
EOF

# Commit deprecation notices
git add clawdy-memory/DEPRECATED.md learning-loop/DEPRECATED.md
git commit -m "Deprecate clawdy-memory and learning-loop

Consolidated into Engram: https://github.com/compemperor/engram"
git push
```

**Option B: Keep as OpenClaw-specific wrappers**

```bash
cd ~/.openclaw/workspace/skills

# Rewrite skills as thin wrappers around Engram
cat > clawdy-memory/SKILL.md << 'EOF'
# Clawdy Memory - OpenClaw Wrapper for Engram

**Note:** This is now a thin wrapper around [Engram](https://github.com/compemperor/engram).

## Setup

```bash
# Start Engram server
docker run -d -p 8765:8765 compemperor/engram
```

## Usage

```bash
# Add lesson
curl -X POST localhost:8765/memory/add \
  -d '{"topic":"...", "lesson":"..."}'
```

**Full docs:** https://github.com/compemperor/engram
EOF

git add clawdy-memory/SKILL.md
git commit -m "Convert clawdy-memory to Engram wrapper"
git push
```

### Step 3: Create OpenClaw Integration in Engram

```bash
cd ~/.openclaw/workspace/engram

# Create OpenClaw integration
mkdir -p integrations/openclaw
cat > integrations/openclaw/SKILL.md << 'EOF'
# Engram - OpenClaw Integration

Memory system for OpenClaw agents.

## Setup

```bash
# Option 1: Docker (recommended)
docker run -d -p 8765:8765 -v ~/.openclaw/workspace/memory:/data/memories compemperor/engram

# Option 2: Local
pip install engram
python -m engram
```

## Usage from OpenClaw

```python
# In your agent code
import requests

ENGRAM_API = "http://localhost:8765"

# Store lesson
requests.post(f"{ENGRAM_API}/memory/add", json={
    "topic": "trading",
    "lesson": "Don't chase missed trades",
    "source_quality": 9
})

# Search
response = requests.post(f"{ENGRAM_API}/memory/search", json={
    "query": "trading mistakes",
    "top_k": 5
})
```

**Full API docs:** http://localhost:8765/docs
EOF

# Add skill wrapper script
cat > integrations/openclaw/wrapper.py << 'EOF'
"""
OpenClaw wrapper for Engram

Usage in OpenClaw skills:
    from engram_wrapper import memory, recall, search
"""

import requests
import os

ENGRAM_API = os.getenv("ENGRAM_API", "http://localhost:8765")

def memory(topic: str, lesson: str, quality: int = 8):
    """Store a memory"""
    response = requests.post(
        f"{ENGRAM_API}/memory/add",
        json={"topic": topic, "lesson": lesson, "source_quality": quality}
    )
    return response.json()

def search(query: str, top_k: int = 5, min_quality: int = 7):
    """Search memories"""
    response = requests.post(
        f"{ENGRAM_API}/memory/search",
        json={"query": query, "top_k": top_k, "min_quality": min_quality}
    )
    return [r["memory"]["lesson"] for r in response.json()["results"]]

def recall(topic: str, min_quality: int = 7):
    """Recall all memories for topic"""
    response = requests.get(
        f"{ENGRAM_API}/memory/recall/{topic}",
        params={"min_quality": min_quality}
    )
    return [m["lesson"] for m in response.json()["memories"]]
EOF

git add integrations/openclaw/
git commit -m "Add OpenClaw integration wrapper"
git push
```

### Step 4: Update Your Local OpenClaw Setup

```bash
# Stop old services
docker stop clawdy-memory 2>/dev/null || true

# Start Engram
cd ~/.openclaw/workspace/engram
docker-compose up -d

# Update any scripts/cron that used old endpoints
# Old: http://localhost:8765/* (clawdy-memory)
# New: http://localhost:8765/* (engram - same endpoints!)

# Port is the same, so most things should just work!
```

### Step 5: Update Cron Jobs (If Needed)

Your existing cron jobs should work as-is since we kept the same endpoints!

```bash
# Check current cron jobs
cron list

# Update if needed (port is same, but just in case)
# market-intel-sweep job should still work
```

---

## Endpoint Mapping

**Good news:** Engram maintains backward compatibility!

| Old (clawdy-memory) | New (Engram) | Status |
|---------------------|--------------|---------|
| POST /add-lesson | POST /memory/add | ✅ Similar |
| POST /search | POST /memory/search | ✅ Compatible |
| GET /recall/{topic} | GET /memory/recall/{topic} | ✅ Same |
| GET /stats | GET /memory/stats | ✅ Same |
| POST /build-index | POST /memory/rebuild-index | ✅ Same |

**Small changes:**
- Request body slightly different (but more standard)
- Response format slightly different (but more complete)

**Migration helper script:**

```python
# migrate_cron.py - Update cron job payloads

import json

# Old format
old_payload = {
    "topic": "trading",
    "lesson": "Don't chase trades"
}

# New format (minimal change!)
new_payload = {
    "topic": "trading",
    "lesson": "Don't chase trades",
    "source_quality": 8  # Optional but recommended
}

# Search - no change needed!
search_payload = {
    "query": "trading mistakes",
    "top_k": 5
}
```

---

## Testing Migration

### Test Script

```bash
# test_migration.sh

#!/bin/bash
set -e

ENGRAM_API="http://localhost:8765"

echo "🧪 Testing Engram migration..."

# 1. Health check
echo "1. Health check..."
curl -s $ENGRAM_API/health | jq .

# 2. Add lesson
echo "2. Adding test lesson..."
curl -s -X POST $ENGRAM_API/memory/add \
  -H "Content-Type: application/json" \
  -d '{"topic":"test","lesson":"Migration test","source_quality":9}' | jq .

# 3. Search
echo "3. Searching..."
curl -s -X POST $ENGRAM_API/memory/search \
  -H "Content-Type: application/json" \
  -d '{"query":"test","top_k":1}' | jq .

# 4. Recall
echo "4. Recalling..."
curl -s $ENGRAM_API/memory/recall/test | jq .

# 5. Stats
echo "5. Stats..."
curl -s $ENGRAM_API/memory/stats | jq .

echo "✅ Migration test complete!"
```

```bash
chmod +x test_migration.sh
./test_migration.sh
```

---

## Cleanup Checklist

- [ ] **Push Engram to GitHub**
  ```bash
  cd ~/.openclaw/workspace/engram
  git init && git add . && git commit -m "Initial commit"
  git remote add origin git@github.com:compemperor/engram.git
  git push -u origin main
  ```

- [ ] **Deprecate old skills in openclaw-skills**
  ```bash
  cd ~/.openclaw/workspace/skills
  # Add DEPRECATED.md to clawdy-memory/ and learning-loop/
  git add . && git commit -m "Deprecate: consolidated into Engram"
  git push
  ```

- [ ] **Stop old services**
  ```bash
  docker stop clawdy-memory
  docker rm clawdy-memory
  ```

- [ ] **Start Engram**
  ```bash
  cd ~/.openclaw/workspace/engram
  docker-compose up -d
  ```

- [ ] **Test migration**
  ```bash
  ./test_migration.sh
  ```

- [ ] **Update documentation**
  - Update TOOLS.md to point to Engram
  - Update any skill READMEs that referenced old tools

- [ ] **Verify cron jobs still work**
  ```bash
  # Check market-intel-sweep, morning-briefing, etc.
  # Should work without changes (same port, compatible endpoints)
  ```

---

## Rollback Plan (If Needed)

If something breaks:

```bash
# Stop Engram
cd ~/.openclaw/workspace/engram
docker-compose down

# Restart old clawdy-memory
docker start clawdy-memory

# Or rebuild from skills repo
cd ~/.openclaw/workspace/skills/clawdy-memory
docker build -t clawdy-memory .
docker run -d -p 8765:8765 clawdy-memory
```

---

## Communication Plan

### Update TOOLS.md

```markdown
## Memory System

**Status:** ✅ Migrated to Engram (2026-02-02)

**Old:** clawdy-memory (deprecated)  
**New:** [Engram](https://github.com/compemperor/engram)

**Running:** http://localhost:8765 (Docker)

**Usage:**
```bash
# Add memory
curl -X POST localhost:8765/memory/add \
  -d '{"topic":"...", "lesson":"...", "source_quality":9}'

# Search
curl -X POST localhost:8765/memory/search \
  -d '{"query":"...", "top_k":5}'
```

**Docs:** http://localhost:8765/docs
```

### Commit Message Template

```
Migrate to Engram: unified memory system

Consolidated:
- clawdy-memory → engram/memory/
- MirrorLoop → engram/mirror/
- learning-loop → engram/learning/

Benefits:
- Public, reusable by community
- Professional packaging (pip install)
- Docker containerization
- Framework-agnostic
- Better documentation

Old skills deprecated but maintained for compatibility.

New repo: https://github.com/compemperor/engram
```

---

## Timeline

**Immediate (Today):**
1. ✅ Engram code complete
2. ⬜ Test locally
3. ⬜ Push to GitHub
4. ⬜ Deprecate old skills

**This Week:**
1. ⬜ Docker Hub publish
2. ⬜ Update all documentation
3. ⬜ Verify cron jobs work
4. ⬜ PyPI publish (optional)

**This Month:**
1. ⬜ Community feedback
2. ⬜ Improvements based on usage
3. ⬜ Additional integrations

---

## FAQ

**Q: Will my existing cron jobs break?**  
A: No! We kept the same port (8765) and compatible endpoints.

**Q: What happens to my existing memories?**  
A: Mount the same volume: `-v ~/.openclaw/workspace/memory:/data/memories`

**Q: Can I use both old and new at the same time?**  
A: No - they use the same port. Choose one.

**Q: What if I need OpenClaw-specific features?**  
A: Use `integrations/openclaw/` wrapper in Engram repo.

**Q: Should I delete old skill code?**  
A: No - deprecate it (add DEPRECATED.md) but keep for reference.

---

## Summary

**Migration strategy:** Deprecate scattered tools, consolidate into Engram

**Steps:**
1. Push Engram to public GitHub repo
2. Deprecate old skills in private repo
3. Stop old Docker containers
4. Start Engram container
5. Test migration
6. Update docs

**Impact:** Minimal - same port, compatible API, better features

**Timeline:** 1-2 hours for full migration

---

**Ready to migrate?** Follow the checklist above!

🦀 **One unified codebase, better for everyone!**
