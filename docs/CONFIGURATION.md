# Engram Configuration

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENGRAM_DATA_PATH` | `/data/memories` | Path to store memory files (set in Docker image) |
| `ENGRAM_EMBEDDING_MODEL` | `intfloat/e5-base-v2` | Embedding model for semantic search (v0.9.0) |

### Embedding Model Options

| Model | Dimensions | RAM | Notes |
|-------|------------|-----|-------|
| `intfloat/e5-base-v2` | 768 | ~1GB | Default, good balance |
| `intfloat/e5-large-v2` | 1024 | ~1.5GB | Better semantic quality |
| `intfloat/multilingual-e5-large` | 1024 | ~1.5GB | Multi-language support |

**Note:** Changing models triggers automatic FAISS index rebuild on startup.

## MemoryStore Constructor Options

```python
MemoryStore(
    path="./memories",                    # Memory storage path
    embedding_model="intfloat/e5-base-v2", # Embedding model
    enable_faiss=True,                    # Enable FAISS vector search
    auto_link_threshold=0.75,             # Similarity threshold for auto-linking
    auto_link_max=3,                      # Max auto-links per memory
    
    # Sleep Scheduler (automatic fade cycles)
    enable_sleep_scheduler=True,          # Enable/disable automatic fading
    sleep_interval_hours=24.0,            # Hours between fade cycles
    sleep_start_delay_minutes=5.0         # Minutes before first cycle
)
```

## Memory Fading Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `ENGRAM_DECAY_HALF_LIFE_DAYS` | 30 | Memory strength halves every N days without access |
| `ENGRAM_DORMANT_THRESHOLD` | 0.2 | Below this strength, memory becomes dormant |
| `ENGRAM_MIN_STRENGTH` | 0.01 | Minimum strength (never fully forgotten) |
| `ENGRAM_QUALITY_WEIGHT` | 0.4 | Weight of quality in strength calculation |
| `ENGRAM_RECALL_WEIGHT` | 0.3 | Weight of recall success in strength |
| `ENGRAM_ACCESS_WEIGHT` | 0.3 | Weight of access frequency in strength |

Example docker-compose override:
```yaml
environment:
  - ENGRAM_DECAY_HALF_LIFE_DAYS=14  # Faster decay
  - ENGRAM_DORMANT_THRESHOLD=0.3   # Higher threshold
```

## Docker Compose (Required Setup)

⚠️ **Volume mount is REQUIRED** to persist data across container restarts.

```yaml
services:
  engram:
    image: ghcr.io/compemperor/engram:latest
    ports:
      - "8765:8765"
    volumes:
      - ${HOME}/.openclaw/engram-data:/data/memories    # REQUIRED: persist memory data (keep outside git repos!)
    environment:
      # Optional: upgrade to better embeddings (v0.9.0)
      - ENGRAM_EMBEDDING_MODEL=intfloat/e5-large-v2
    restart: unless-stopped
```

**Without the volume mount**, all memories are lost when the container restarts!

The image already has `MEMORY_PATH=/data/memories` set. Just mount your host directory to `/data/memories`.

## API Configuration

The API runs on port `8765` by default. Change via:

```bash
python -m engram --host 0.0.0.0 --port 8765
```

## Sleep Scheduler Configuration (v0.10.0)

The sleep scheduler runs these phases automatically every 24h:

| Phase | Description | Setting |
|-------|-------------|---------|
| Fade | Mark unused memories dormant | Always enabled |
| Reflection | Synthesize insights | `auto_reflect_enabled` |
| Quality | Adjust quality scores | `auto_quality_enabled` |
| Compression | Merge similar memories | `compression_enabled` |
| Replay | Strengthen at-risk memories | `replay_enabled` |

Default limits:
- `compression_limit`: 5 groups per cycle
- `replay_limit`: 20 memories per cycle
