# Engram Skills

Integration guides for different AI agent frameworks and IDEs.

## Available Skills

### [OpenClaw](openclaw/)
Integration for OpenClaw agent framework. Python wrapper with simple API.

### [Aider](aider/)
Use Engram in Aider AI coding sessions. Configuration and helper functions.

### [Cursor](cursor/)
Cursor IDE integration with VS Code custom commands and helper script.

### [Claude Code](claude-code/)
Python client for Claude Code projects. Full OOP client with examples.

## Quick Start

1. **Start Engram server:**
   ```bash
   docker run -d -p 8765:8765 -v ./memories:/data/memories ghcr.io/compemperor/engram:latest
   ```

2. **Choose your framework** and follow the SKILL.md guide in that directory

3. **Basic pattern:**
   - Store lessons after solving problems
   - Query for lessons before tackling similar tasks
   - Build up a knowledge base over time

## Creating New Skills

To add integration for a new framework:

1. Create `skills/your-framework/SKILL.md`
2. Include:
   - Setup instructions
   - Basic usage code
   - Practical examples
   - Best practices
3. Submit a PR!

## Generic Integration

All skills use the same REST API:

```bash
# Store
curl -X POST http://localhost:8765/memory/add \
  -H "Content-Type: application/json" \
  -d '{"topic":"topic","lesson":"lesson","source_quality":9}'

# Search  
curl -X POST http://localhost:8765/memory/search \
  -H "Content-Type: application/json" \
  -d '{"query":"search terms","top_k":5}'

# Recall topic
curl http://localhost:8765/memory/recall/topic
```

**API docs:** http://localhost:8765/docs (when running)

## Philosophy

**Learn as you code:**
- Store lessons immediately (while context is fresh)
- Query before similar work (avoid repeating mistakes)
- Quality over quantity (rate your lessons)

**Good lessons:**
- Specific and actionable
- Include context (what/why/when)
- Verified from experience

**Bad lessons:**
- Too generic ("write good code")
- No context
- Unverified assumptions

## Contributing

Have a skill for another framework? PRs welcome!

1. Fork the repo
2. Add your skill in `skills/your-framework/`
3. Follow the existing structure
4. Submit PR

---

**Need help?** Open an issue or check the main [README](../README.md)
