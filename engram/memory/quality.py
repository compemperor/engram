"""
Heuristic-based Quality Assessment - v0.8.0

Automatically evaluates memory quality using behavioral signals:
- Recall success rate (spaced repetition results)
- Access frequency (how often retrieved)
- Relationship density (knowledge graph connections)
- Age resilience (old + still accessed = valuable)
- Duplicate detection (embedding similarity)

No LLM required - uses patterns from actual usage.
Inspired by how the brain strengthens memories through use.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import math


@dataclass
class QualityAssessment:
    """Result of heuristic quality assessment"""
    memory_id: str
    original_quality: Optional[int]
    assessed_quality: float  # 1-10 scale
    confidence: float  # 0-1, how confident in assessment
    
    # Component scores (0-1 scale)
    recall_score: float  # Based on spaced repetition success
    access_score: float  # Based on retrieval frequency
    relationship_score: float  # Based on knowledge graph density
    age_resilience_score: float  # Old + still used = valuable
    
    # Flags
    is_duplicate: bool
    duplicate_of: Optional[str]  # Memory ID if duplicate
    suggested_action: str  # "keep", "upgrade", "downgrade", "merge", "archive"
    reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "original_quality": self.original_quality,
            "assessed_quality": round(self.assessed_quality, 2),
            "confidence": round(self.confidence, 2),
            "components": {
                "recall": round(self.recall_score, 2),
                "access": round(self.access_score, 2),
                "relationships": round(self.relationship_score, 2),
                "age_resilience": round(self.age_resilience_score, 2)
            },
            "is_duplicate": self.is_duplicate,
            "duplicate_of": self.duplicate_of,
            "suggested_action": self.suggested_action,
            "reasoning": self.reasoning
        }


class QualityAssessor:
    """
    Heuristic-based quality assessment system.
    
    Evaluates memories based on usage patterns, not LLM judgment.
    """
    
    # Weights for combining component scores
    WEIGHTS = {
        "recall": 0.35,      # Spaced repetition is strongest signal
        "access": 0.25,      # Frequent access = useful
        "relationships": 0.20,  # Well-connected = important
        "age_resilience": 0.20  # Stood test of time
    }
    
    # Thresholds
    DUPLICATE_SIMILARITY_THRESHOLD = 0.92  # Cosine similarity for duplicate detection
    MIN_ACCESSES_FOR_CONFIDENCE = 3  # Need this many accesses for high confidence
    MIN_RECALLS_FOR_CONFIDENCE = 2  # Need this many recall attempts for high confidence
    
    def __init__(self, knowledge_graph=None, recall_system=None):
        self.knowledge_graph = knowledge_graph
        self.recall_system = recall_system
    
    def assess_memory(
        self,
        memory,
        all_memories: List = None,
        embeddings: Dict[str, Any] = None
    ) -> QualityAssessment:
        """
        Assess quality of a single memory using heuristics.
        
        Args:
            memory: Memory object to assess
            all_memories: List of all memories (for duplicate detection)
            embeddings: Dict of memory_id -> embedding (for similarity)
        """
        # Calculate component scores
        recall_score = self._calculate_recall_score(memory)
        access_score = self._calculate_access_score(memory)
        relationship_score = self._calculate_relationship_score(memory)
        age_resilience_score = self._calculate_age_resilience_score(memory)
        
        # Check for duplicates
        is_duplicate, duplicate_of = self._check_duplicate(
            memory, all_memories, embeddings
        )
        
        # Calculate weighted quality score
        weighted_score = (
            self.WEIGHTS["recall"] * recall_score +
            self.WEIGHTS["access"] * access_score +
            self.WEIGHTS["relationships"] * relationship_score +
            self.WEIGHTS["age_resilience"] * age_resilience_score
        )
        
        # Scale to 1-10
        assessed_quality = 1 + (weighted_score * 9)
        
        # Calculate confidence based on data availability
        confidence = self._calculate_confidence(memory)
        
        # Determine suggested action
        action, reasoning = self._determine_action(
            memory, assessed_quality, confidence, is_duplicate, duplicate_of
        )
        
        return QualityAssessment(
            memory_id=memory.memory_id,
            original_quality=memory.source_quality,
            assessed_quality=assessed_quality,
            confidence=confidence,
            recall_score=recall_score,
            access_score=access_score,
            relationship_score=relationship_score,
            age_resilience_score=age_resilience_score,
            is_duplicate=is_duplicate,
            duplicate_of=duplicate_of,
            suggested_action=action,
            reasoning=reasoning
        )
    
    def _calculate_recall_score(self, memory) -> float:
        """
        Score based on spaced repetition performance.
        
        High success rate = valuable memory worth keeping.
        """
        recall_count = getattr(memory, 'recall_count', 0)
        success_rate = getattr(memory, 'review_success_rate', 0.0)
        
        if recall_count == 0:
            return 0.5  # Neutral - no data yet
        
        # Weight by number of attempts (more attempts = more confident)
        attempt_weight = min(1.0, recall_count / 5)
        
        # Success rate directly maps to score
        return success_rate * attempt_weight + 0.5 * (1 - attempt_weight)
    
    def _calculate_access_score(self, memory) -> float:
        """
        Score based on how often memory is retrieved.
        
        Frequently accessed = useful for tasks.
        """
        access_count = getattr(memory, 'access_count', 0)
        
        if access_count == 0:
            return 0.3  # Low - never used
        
        # Logarithmic scaling (diminishing returns)
        # 1 access = 0.4, 5 accesses = 0.7, 20+ = ~1.0
        return min(1.0, 0.3 + 0.7 * (math.log(access_count + 1) / math.log(25)))
    
    def _calculate_relationship_score(self, memory) -> float:
        """
        Score based on knowledge graph connections.
        
        Well-connected memories are more central/important.
        """
        if not self.knowledge_graph:
            return 0.5  # Neutral - no graph available
        
        # Count relationships
        relationships = self.knowledge_graph.get_related(memory.memory_id)
        rel_count = len(relationships) if relationships else 0
        
        if rel_count == 0:
            return 0.3  # Low - isolated memory
        
        # Scale: 1 rel = 0.5, 3 rels = 0.7, 5+ = ~1.0
        return min(1.0, 0.3 + 0.7 * (rel_count / 5))
    
    def _calculate_age_resilience_score(self, memory) -> float:
        """
        Score based on age combined with continued access.
        
        Old memories that are still accessed are proven valuable.
        """
        try:
            created = datetime.strptime(memory.timestamp, "%Y-%m-%d %H:%M")
            age_days = (datetime.now() - created).days
        except:
            return 0.5  # Neutral - can't parse timestamp
        
        access_count = getattr(memory, 'access_count', 0)
        last_accessed = getattr(memory, 'last_accessed', None)
        
        if age_days < 7:
            return 0.5  # Too new to judge
        
        # Old + still accessed = high score
        # Old + never accessed = low score
        if access_count == 0:
            # Decay based on age
            return max(0.1, 0.5 - (age_days / 60) * 0.4)
        
        # Calculate recency of last access
        if last_accessed:
            try:
                last_access_dt = datetime.strptime(last_accessed, "%Y-%m-%d %H:%M")
                days_since_access = (datetime.now() - last_access_dt).days
                
                # Recent access of old memory = very valuable
                if age_days > 30 and days_since_access < 7:
                    return 0.9
                elif age_days > 14 and days_since_access < 14:
                    return 0.7
            except:
                pass
        
        # Default: moderate score for accessed memories
        return 0.6
    
    def _check_duplicate(
        self,
        memory,
        all_memories: List,
        embeddings: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if memory is a duplicate of another using embedding similarity.
        """
        if not all_memories or not embeddings:
            return False, None
        
        if memory.memory_id not in embeddings:
            return False, None
        
        try:
            import numpy as np
            
            target_emb = embeddings[memory.memory_id]
            
            for other in all_memories:
                if other.memory_id == memory.memory_id:
                    continue
                
                if other.memory_id not in embeddings:
                    continue
                
                other_emb = embeddings[other.memory_id]
                
                # Cosine similarity
                similarity = np.dot(target_emb, other_emb) / (
                    np.linalg.norm(target_emb) * np.linalg.norm(other_emb)
                )
                
                if similarity >= self.DUPLICATE_SIMILARITY_THRESHOLD:
                    # Prefer keeping older or higher quality memory
                    if (other.source_quality or 5) >= (memory.source_quality or 5):
                        return True, other.memory_id
            
            return False, None
        except Exception:
            return False, None
    
    def _calculate_confidence(self, memory) -> float:
        """
        Calculate confidence in the assessment based on data availability.
        """
        confidence = 0.3  # Base confidence
        
        # More data = higher confidence
        access_count = getattr(memory, 'access_count', 0)
        recall_count = getattr(memory, 'recall_count', 0)
        
        if access_count >= self.MIN_ACCESSES_FOR_CONFIDENCE:
            confidence += 0.3
        elif access_count > 0:
            confidence += 0.15
        
        if recall_count >= self.MIN_RECALLS_FOR_CONFIDENCE:
            confidence += 0.3
        elif recall_count > 0:
            confidence += 0.15
        
        # Has relationships = more context
        if self.knowledge_graph:
            rels = self.knowledge_graph.get_related(memory.memory_id)
            if rels and len(rels) > 0:
                confidence += 0.1
        
        return min(1.0, confidence)
    
    def _determine_action(
        self,
        memory,
        assessed_quality: float,
        confidence: float,
        is_duplicate: bool,
        duplicate_of: Optional[str]
    ) -> Tuple[str, str]:
        """
        Determine recommended action based on assessment.
        """
        original = memory.source_quality or 5
        
        if is_duplicate:
            return "merge", f"Duplicate of {duplicate_of}. Consider merging or archiving."
        
        # Only suggest changes if confidence is reasonable
        if confidence < 0.5:
            return "keep", "Insufficient data for confident assessment. Keep as-is."
        
        diff = assessed_quality - original
        
        if diff >= 2:
            return "upgrade", f"Usage patterns suggest higher value (assessed {assessed_quality:.1f} vs original {original})"
        elif diff <= -2:
            return "downgrade", f"Low usage suggests lower value (assessed {assessed_quality:.1f} vs original {original})"
        elif assessed_quality < 4 and confidence >= 0.7:
            return "archive", f"Consistently low value (assessed {assessed_quality:.1f}). Consider archiving."
        else:
            return "keep", f"Quality assessment ({assessed_quality:.1f}) aligns with original ({original})"


def assess_memories_batch(
    memories: List,
    knowledge_graph=None,
    recall_system=None,
    embeddings: Dict[str, Any] = None,
    limit: int = 10
) -> List[QualityAssessment]:
    """
    Assess quality of multiple memories.
    
    Args:
        memories: List of Memory objects
        knowledge_graph: KnowledgeGraph instance
        recall_system: ActiveRecallSystem instance
        embeddings: Dict of memory_id -> embedding
        limit: Maximum memories to assess
    
    Returns:
        List of QualityAssessment objects
    """
    assessor = QualityAssessor(knowledge_graph, recall_system)
    
    assessments = []
    for memory in memories[:limit]:
        assessment = assessor.assess_memory(memory, memories, embeddings)
        assessments.append(assessment)
    
    return assessments
