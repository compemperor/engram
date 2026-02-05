"""
Memory Compression - Consolidate similar memories into compact representations

Inspired by how the brain consolidates memories during sleep:
- Near-duplicate detection via embedding similarity
- Merge related memories into comprehensive summaries
- Archive originals, keep links for provenance
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class CompressionCandidate:
    """A group of memories that could be compressed together."""
    primary_id: str  # The "best" memory to keep
    merge_ids: List[str]  # Memories to merge into primary
    similarity_scores: List[float]  # Similarity of each merge candidate
    topic: str
    combined_lesson: str  # Merged content
    reason: str  # Why these were grouped


@dataclass
class CompressionResult:
    """Result of a compression operation."""
    compressed_count: int
    archived_count: int
    candidates: List[CompressionCandidate]
    skipped: List[str]  # Memory IDs skipped (too unique)
    

class MemoryCompressor:
    """
    Compresses similar memories to reduce redundancy.
    
    Strategies:
    1. Near-duplicate merging (similarity > 0.9)
    2. Topic consolidation (same topic, related content)
    3. Temporal compression (multiple memories about same event)
    """
    
    def __init__(
        self,
        similarity_threshold: float = 0.88,  # High threshold for safety
        min_quality_to_keep: int = 7,
        max_merge_group: int = 5
    ):
        self.similarity_threshold = similarity_threshold
        self.min_quality_to_keep = min_quality_to_keep
        self.max_merge_group = max_merge_group
    
    def find_compression_candidates(
        self,
        memories: List[Any],
        embeddings: Dict[str, Any],
        limit: int = 10
    ) -> List[CompressionCandidate]:
        """
        Find groups of memories that could be compressed.
        
        Args:
            memories: List of Memory objects
            embeddings: Dict of memory_id -> embedding vector
            limit: Max candidates to return
            
        Returns:
            List of CompressionCandidate groups
        """
        import numpy as np
        
        if not embeddings or len(memories) < 2:
            return []
        
        candidates = []
        processed_ids = set()
        
        # Group by topic first for efficiency
        topic_groups: Dict[str, List[Any]] = {}
        for m in memories:
            if m.memory_id in processed_ids:
                continue
            # Skip reflections
            memory_type = getattr(m, 'memory_type', None)
            if memory_type:
                type_val = memory_type.value if hasattr(memory_type, 'value') else str(memory_type)
                if type_val == "reflection":
                    continue
            
            topic = m.topic.split('/')[0] if '/' in m.topic else m.topic
            if topic not in topic_groups:
                topic_groups[topic] = []
            topic_groups[topic].append(m)
        
        for topic, group in topic_groups.items():
            if len(group) < 2:
                continue
            
            # Find similar pairs within topic
            for i, m1 in enumerate(group):
                if m1.memory_id in processed_ids:
                    continue
                if m1.memory_id not in embeddings:
                    continue
                
                merge_candidates = []
                
                for j, m2 in enumerate(group[i+1:], i+1):
                    if m2.memory_id in processed_ids:
                        continue
                    if m2.memory_id not in embeddings:
                        continue
                    
                    # Calculate cosine similarity
                    sim = self._cosine_similarity(
                        embeddings[m1.memory_id],
                        embeddings[m2.memory_id]
                    )
                    
                    if sim >= self.similarity_threshold:
                        merge_candidates.append((m2, sim))
                
                if merge_candidates:
                    # Sort by similarity, take top N
                    merge_candidates.sort(key=lambda x: x[1], reverse=True)
                    merge_candidates = merge_candidates[:self.max_merge_group - 1]
                    
                    # Determine primary (highest quality, or most recent)
                    all_memories = [m1] + [mc[0] for mc in merge_candidates]
                    primary = max(all_memories, key=lambda m: (
                        getattr(m, 'source_quality', 5),
                        getattr(m, 'access_count', 0),
                        getattr(m, 'created_at', '') or ''
                    ))
                    
                    merge_ids = [m.memory_id for m in all_memories if m.memory_id != primary.memory_id]
                    
                    # Combine lessons
                    combined = self._combine_lessons(all_memories)
                    
                    candidate = CompressionCandidate(
                        primary_id=primary.memory_id,
                        merge_ids=merge_ids,
                        similarity_scores=[mc[1] for mc in merge_candidates],
                        topic=topic,
                        combined_lesson=combined,
                        reason=f"High similarity ({merge_candidates[0][1]:.2f}+) within topic '{topic}'"
                    )
                    candidates.append(candidate)
                    
                    # Mark as processed
                    processed_ids.add(primary.memory_id)
                    for mid in merge_ids:
                        processed_ids.add(mid)
                    
                    if len(candidates) >= limit:
                        return candidates
        
        return candidates
    
    def _cosine_similarity(self, v1, v2) -> float:
        """Calculate cosine similarity between two vectors."""
        import numpy as np
        v1 = np.array(v1)
        v2 = np.array(v2)
        dot = np.dot(v1, v2)
        norm = np.linalg.norm(v1) * np.linalg.norm(v2)
        return float(dot / norm) if norm > 0 else 0.0
    
    def _combine_lessons(self, memories: List[Any]) -> str:
        """Combine multiple memory lessons into one comprehensive lesson."""
        # Sort by quality/recency
        sorted_mems = sorted(memories, key=lambda m: (
            getattr(m, 'source_quality', 5),
            getattr(m, 'created_at', '') or ''
        ), reverse=True)
        
        # Start with highest quality
        primary = sorted_mems[0]
        combined = primary.lesson
        
        # Add unique insights from others
        seen_phrases = set(combined.lower().split())
        additions = []
        
        for m in sorted_mems[1:]:
            # Find phrases in this lesson not in combined
            words = m.lesson.lower().split()
            unique_ratio = sum(1 for w in words if w not in seen_phrases) / max(len(words), 1)
            
            if unique_ratio > 0.3:  # Has significant unique content
                additions.append(m.lesson)
                seen_phrases.update(words)
        
        if additions:
            combined = combined.rstrip('.') + ". Additional context: " + " | ".join(additions[:2])
        
        return combined[:2000]  # Limit length


class MemoryReplayer:
    """
    Replays memories during sleep to strengthen retention.
    
    Mimics hippocampal replay during sleep - strengthens important
    memories by simulating retrieval without explicit recall.
    """
    
    def __init__(
        self,
        replay_boost: float = 0.1,  # Strength boost per replay
        max_replays_per_cycle: int = 20,
        prioritize_decaying: bool = True
    ):
        self.replay_boost = replay_boost
        self.max_replays_per_cycle = max_replays_per_cycle
        self.prioritize_decaying = prioritize_decaying
    
    def select_for_replay(
        self,
        memories: List[Any],
        limit: Optional[int] = None
    ) -> List[Any]:
        """
        Select memories for replay based on importance and decay risk.
        
        Priority:
        1. High quality memories at risk of decay
        2. Recently accessed but not frequently
        3. Well-connected memories (high relationship count)
        """
        limit = limit or self.max_replays_per_cycle
        
        scored = []
        now = datetime.utcnow()
        
        for m in memories:
            # Skip reflections
            memory_type = getattr(m, 'memory_type', None)
            if memory_type:
                type_val = memory_type.value if hasattr(memory_type, 'value') else str(memory_type)
                if type_val == "reflection":
                    continue
            
            # Skip dormant
            status = getattr(m, 'status', None)
            if status:
                status_val = status.value if hasattr(status, 'value') else str(status)
                if status_val == "dormant":
                    continue
            
            quality = getattr(m, 'source_quality', 5)
            strength = getattr(m, 'strength', 1.0)
            access_count = getattr(m, 'access_count', 0)
            
            # Calculate days since last access
            last_access = getattr(m, 'last_accessed', None) or getattr(m, 'created_at', None)
            if isinstance(last_access, str):
                try:
                    last_access = datetime.fromisoformat(last_access.replace('Z', '+00:00'))
                    days_since = (now - last_access.replace(tzinfo=None)).days
                except:
                    days_since = 0
            else:
                days_since = 0
            
            # Score: prioritize high quality at decay risk
            score = 0.0
            
            # Quality factor (higher = more worth saving)
            score += quality * 0.3
            
            # Decay risk (lower strength + more days = higher priority)
            if self.prioritize_decaying:
                decay_risk = (1 - strength) * min(days_since / 30, 1.0)
                score += decay_risk * 0.4
            
            # Inverse access (less accessed = needs replay more)
            access_factor = 1.0 / (1 + access_count * 0.1)
            score += access_factor * 0.3
            
            scored.append((score, m))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return [m for _, m in scored[:limit]]
    
    def replay_memory(self, memory: Any) -> Dict[str, Any]:
        """
        Replay a single memory (boost its strength/access).
        
        Returns dict of changes to apply.
        """
        current_strength = getattr(memory, 'strength', 1.0)
        current_access = getattr(memory, 'access_count', 0)
        
        # Boost strength (capped at 1.0)
        new_strength = min(1.0, current_strength + self.replay_boost)
        
        return {
            "memory_id": memory.memory_id,
            "old_strength": current_strength,
            "new_strength": new_strength,
            "access_count": current_access + 1,
            "replayed_at": datetime.utcnow().isoformat()
        }
