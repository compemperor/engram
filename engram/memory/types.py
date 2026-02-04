"""
Memory types and data structures

Defines episodic vs semantic memory and relationships
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from enum import Enum


class MemoryType(str, Enum):
    """Type of memory"""
    EPISODIC = "episodic"  # Personal experiences, events (when, where, what happened)
    SEMANTIC = "semantic"  # Facts, rules, concepts (general knowledge)


class RelationType(str, Enum):
    """Types of relationships between memories"""
    CAUSED_BY = "caused_by"  # A caused B
    RELATED_TO = "related_to"  # A relates to B
    CONTRADICTS = "contradicts"  # A contradicts B
    SUPPORTS = "supports"  # A supports B
    EXAMPLE_OF = "example_of"  # A is example of B
    DERIVED_FROM = "derived_from"  # A derived from B


@dataclass
class Entity:
    """Named entity in memory (person, stock, concept, etc.)"""
    name: str
    type: str  # person, stock, concept, event, etc.
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Relationship:
    """Relationship between two memories"""
    from_id: str  # Source memory ID
    to_id: str  # Target memory ID
    relation_type: RelationType
    confidence: float = 1.0  # 0-1, how confident in this relationship
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MemoryStatus(str, Enum):
    """Memory status for fading system"""
    ACTIVE = "active"  # Normal, included in searches
    DORMANT = "dormant"  # Faded below threshold, excluded from searches
    CONSOLIDATED = "consolidated"  # Merged into a summary


@dataclass
class Memory:
    """Enhanced memory entry with type, entities, and fading support"""
    topic: str
    lesson: str
    memory_type: MemoryType  # NEW: episodic or semantic
    timestamp: str
    memory_id: str  # NEW: unique identifier for relationships
    source_quality: Optional[int] = None  # 1-10 scale
    understanding: Optional[float] = None  # 1-5 scale
    entities: List[Entity] = field(default_factory=list)  # NEW: extracted entities
    metadata: Optional[Dict[str, Any]] = None
    recall_count: int = 0  # Track how many times recalled
    last_recalled: Optional[str] = None  # Last recall timestamp
    next_review: Optional[str] = None  # When to review next (spaced repetition)
    review_success_rate: float = 0.0  # Success rate for this memory (0-1)
    # v0.6.0: Fading system fields
    access_count: int = 0  # How many times retrieved in search
    last_accessed: Optional[str] = None  # Last search retrieval timestamp
    status: MemoryStatus = MemoryStatus.ACTIVE  # active, dormant, consolidated
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['memory_type'] = self.memory_type.value
        result['status'] = self.status.value if isinstance(self.status, MemoryStatus) else self.status
        return result


@dataclass
class SearchResult:
    """Search result with score"""
    memory: Memory
    score: float  # Similarity score (0-1, higher = better)
    relationships: List[Relationship] = field(default_factory=list)  # NEW: related memories


@dataclass
class RecallChallenge:
    """Active recall challenge"""
    memory_id: str
    question: str  # What to recall
    expected_topics: List[str]  # Expected answer topics
    difficulty: Literal["easy", "medium", "hard"]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RecallAttempt:
    """Result of recall attempt"""
    challenge_id: str
    memory_id: str
    success: bool  # Did they recall correctly?
    confidence: float  # 0-1, how confident were they
    time_taken_ms: int  # How long to recall
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
