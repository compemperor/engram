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
    REFLECTION = "reflection"  # Synthesized insight from multiple memories
    REASONING = "reasoning"  # v0.14: Decision traces, tool calls, observations


class ActionType(str, Enum):
    """Types of actions in reasoning traces"""
    TOOL_CALL = "tool_call"  # Called a tool/function
    DECISION = "decision"  # Made a decision
    QUERY = "query"  # Searched/queried something
    REFLECTION = "reflection"  # Reflected on outcome


class TraceOutcome(str, Enum):
    """Outcome of a reasoning trace"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    PENDING = "pending"


class RelationType(str, Enum):
    """Types of relationships between memories"""
    CAUSED_BY = "caused_by"  # A caused B
    RELATED_TO = "related_to"  # A relates to B
    CONTRADICTS = "contradicts"  # A contradicts B
    SUPPORTS = "supports"  # A supports B
    EXAMPLE_OF = "example_of"  # A is example of B
    DERIVED_FROM = "derived_from"  # A derived from B
    SYNTHESIZED_FROM = "synthesized_from"  # A is a reflection synthesized from B


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


# ============================================================================
# v0.14: Reasoning Memory Types
# ============================================================================

@dataclass
class TraceAction:
    """Action taken in a reasoning trace"""
    type: ActionType  # tool_call, decision, query, reflection
    name: str  # Tool name, decision type, or query type
    args: Dict[str, Any] = field(default_factory=dict)  # Arguments/parameters
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['type'] = self.type.value
        return result


@dataclass
class ReasoningTrace:
    """
    v0.14: A single step in an agent's reasoning process.
    
    Captures the Thought-Action-Observation cycle for learning and debugging.
    Based on ReasoningBank and ExpeL research.
    """
    trace_id: str  # Unique identifier
    session_id: str  # Session this trace belongs to
    timestamp: str  # When this trace occurred
    sequence: int  # Order within session (0, 1, 2, ...)
    
    # The reasoning cycle
    thought: Optional[str] = None  # LLM's reasoning/plan
    action: Optional[TraceAction] = None  # Action taken
    observation: Optional[str] = None  # Result/feedback from action
    outcome: TraceOutcome = TraceOutcome.PENDING  # success/failure/partial
    
    # Metadata
    tokens_input: int = 0
    tokens_output: int = 0
    duration_ms: int = 0
    user_feedback: Optional[str] = None  # positive/negative/null
    
    # Distillation (Phase 3)
    distilled_pattern: Optional[str] = None  # Extracted insight
    related_traces: List[str] = field(default_factory=list)  # Related trace IDs
    
    # Skill extraction (Phase 4)
    skill_id: Optional[str] = None  # If this trace is part of a skill
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'trace_id': self.trace_id,
            'session_id': self.session_id,
            'timestamp': self.timestamp,
            'sequence': self.sequence,
            'thought': self.thought,
            'action': self.action.to_dict() if self.action else None,
            'observation': self.observation,
            'outcome': self.outcome.value,
            'tokens_input': self.tokens_input,
            'tokens_output': self.tokens_output,
            'duration_ms': self.duration_ms,
            'user_feedback': self.user_feedback,
            'distilled_pattern': self.distilled_pattern,
            'related_traces': self.related_traces,
            'skill_id': self.skill_id,
        }
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReasoningTrace':
        """Create ReasoningTrace from dictionary"""
        action_data = data.get('action')
        action = None
        if action_data:
            action = TraceAction(
                type=ActionType(action_data['type']),
                name=action_data['name'],
                args=action_data.get('args', {})
            )
        
        return cls(
            trace_id=data['trace_id'],
            session_id=data['session_id'],
            timestamp=data['timestamp'],
            sequence=data.get('sequence', 0),
            thought=data.get('thought'),
            action=action,
            observation=data.get('observation'),
            outcome=TraceOutcome(data.get('outcome', 'pending')),
            tokens_input=data.get('tokens_input', 0),
            tokens_output=data.get('tokens_output', 0),
            duration_ms=data.get('duration_ms', 0),
            user_feedback=data.get('user_feedback'),
            distilled_pattern=data.get('distilled_pattern'),
            related_traces=data.get('related_traces', []),
            skill_id=data.get('skill_id'),
        )


@dataclass
class Skill:
    """
    v0.14: A reusable skill extracted from successful trace sequences.
    
    Based on Voyager's skill library concept.
    """
    skill_id: str
    name: str  # Human-readable name
    description: str  # What this skill does
    
    # The skill definition
    trigger_pattern: str  # When to use this skill (query pattern)
    trace_sequence: List[str]  # Ordered trace IDs that form this skill
    success_rate: float = 0.0  # How often this skill succeeds
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_used: Optional[str] = None
    use_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Skill':
        return cls(**data)
