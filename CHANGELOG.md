# Changelog

All notable changes to Engram will be documented in this file.

## [0.11.0] - 2026-02-06

### Added
- **Active Learning Module** - Tracks knowledge gaps and suggests what to learn
  - `GET /learning/gaps` - View knowledge gaps (poor searches, failed recalls)
  - `GET /learning/suggest` - Get prioritized learning suggestions
  - `POST /learning/request` - Add topic to learning queue (high priority)
  - `POST /learning/resolve` - Mark gap as resolved
  - `GET /learning/stats` - Learning progress statistics
- **Episodic Memory Support** - Store experiences with `memory_type: "episodic"`
- Search now automatically tracks poor results as knowledge gaps
- Recall failures now tracked for active learning

### Changed
- Search endpoint now integrates with active learning tracker

## [0.10.3] - 2026-02-05

### Added
- Semantic similarity for recall validation (cosine similarity >= 0.75)
- Knowledge graph relationships
- Memory fading system (active/dormant/consolidated states)
- Spaced repetition with configurable intervals

## [0.10.0] - 2026-02-04

### Added
- Learning sessions with quality gates
- Mirror evaluator for drift detection
- Temporal weighting for search results
- Context expansion via knowledge graph

## [0.9.0] - 2026-02-03

### Added
- Configurable embedding models (e5-base, e5-large, multilingual)
- Docker support with health checks
- REST API with FastAPI

## [0.1.0] - 2026-02-01

### Added
- Initial release
- Basic semantic memory storage
- Vector similarity search
- Topic-based recall
