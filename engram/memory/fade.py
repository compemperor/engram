"""
Memory Fading System - Biologically-inspired forgetting for Engram

Based on research:
- FadeMem (2026): Exponential decay modulated by relevance, access, time
- Ebbinghaus forgetting curve: R = exp(-t/S)
- Google Titans: Adaptive weight decay with surprise metrics

Memories fade but are never deleted - they become "dormant" and can be recovered.
"""

import math
import os
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass

from engram.memory.types import Memory


# Configuration - all configurable via environment variables
DECAY_HALF_LIFE_DAYS = float(os.getenv("ENGRAM_DECAY_HALF_LIFE_DAYS", "30"))
DORMANT_THRESHOLD = float(os.getenv("ENGRAM_DORMANT_THRESHOLD", "0.2"))
MIN_STRENGTH = float(os.getenv("ENGRAM_MIN_STRENGTH", "0.01"))
QUALITY_WEIGHT = float(os.getenv("ENGRAM_QUALITY_WEIGHT", "0.4"))
RECALL_WEIGHT = float(os.getenv("ENGRAM_RECALL_WEIGHT", "0.3"))
ACCESS_WEIGHT = float(os.getenv("ENGRAM_ACCESS_WEIGHT", "0.3"))


@dataclass
class FadeMetrics:
    """Metrics for memory fading decisions"""
    strength: float
    decay_factor: float
    days_since_access: float
    is_dormant: bool
    recommended_action: str  # "keep", "fade", "dormant", "consolidate"


def calculate_base_strength(memory: Memory) -> float:
    """
    Calculate base strength from memory attributes.
    
    Strength = weighted combination of:
    - Source quality (1-10 normalized to 0-1)
    - Recall success rate (0-1)
    - Access frequency (normalized)
    """
    # Quality component (0-1)
    quality = (memory.source_quality or 5) / 10.0
    
    # Recall success component (0-1)
    recall_success = memory.review_success_rate or 0.0
    
    # Access frequency component (0-1, logarithmic)
    # More accesses = higher strength, but diminishing returns
    access_count = getattr(memory, 'access_count', 0) or 0
    access_factor = min(1.0, math.log1p(access_count) / 5.0)  # log(1+x), max at ~148 accesses
    
    # Combine with weights
    base_strength = (
        QUALITY_WEIGHT * quality +
        RECALL_WEIGHT * recall_success +
        ACCESS_WEIGHT * access_factor
    )
    
    return max(MIN_STRENGTH, min(1.0, base_strength))


def calculate_decay(days_since_access: float) -> float:
    """
    Calculate decay factor using Ebbinghaus-inspired exponential decay.
    
    decay = exp(-t / half_life) where t = days since last access
    
    Returns value between 0 and 1 (1 = no decay, 0 = full decay)
    """
    if days_since_access <= 0:
        return 1.0
    
    # Exponential decay: R = exp(-t * ln(2) / half_life)
    decay_rate = math.log(2) / DECAY_HALF_LIFE_DAYS
    decay_factor = math.exp(-decay_rate * days_since_access)
    
    return max(MIN_STRENGTH, decay_factor)


def calculate_strength(memory: Memory, current_time: Optional[datetime] = None) -> float:
    """
    Calculate current memory strength after applying decay.
    
    Final strength = base_strength × decay_factor
    """
    if current_time is None:
        current_time = datetime.utcnow()
    
    base_strength = calculate_base_strength(memory)
    
    # Get last access time (use last_recalled, last_accessed, or timestamp)
    last_access_str = (
        getattr(memory, 'last_accessed', None) or 
        memory.last_recalled or 
        memory.timestamp
    )
    
    try:
        # Handle multiple datetime formats
        for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
            try:
                last_access = datetime.strptime(last_access_str, fmt)
                break
            except ValueError:
                continue
        else:
            last_access = current_time  # Fallback: no decay
    except Exception:
        last_access = current_time
    
    days_since_access = (current_time - last_access).total_seconds() / 86400
    decay_factor = calculate_decay(days_since_access)
    
    final_strength = base_strength * decay_factor
    return max(MIN_STRENGTH, min(1.0, final_strength))


def get_fade_metrics(memory: Memory, current_time: Optional[datetime] = None) -> FadeMetrics:
    """
    Get comprehensive fade metrics for a memory.
    """
    if current_time is None:
        current_time = datetime.utcnow()
    
    strength = calculate_strength(memory, current_time)
    base_strength = calculate_base_strength(memory)
    
    # Calculate days since access
    last_access_str = (
        getattr(memory, 'last_accessed', None) or 
        memory.last_recalled or 
        memory.timestamp
    )
    
    try:
        for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
            try:
                last_access = datetime.strptime(last_access_str, fmt)
                break
            except ValueError:
                continue
        else:
            last_access = current_time
    except Exception:
        last_access = current_time
    
    days_since_access = (current_time - last_access).total_seconds() / 86400
    decay_factor = calculate_decay(days_since_access)
    is_dormant = strength < DORMANT_THRESHOLD
    
    # Determine recommended action
    if strength >= 0.7:
        action = "keep"
    elif strength >= DORMANT_THRESHOLD:
        action = "fade"
    elif base_strength >= 0.5:  # High quality but decayed
        action = "consolidate"
    else:
        action = "dormant"
    
    return FadeMetrics(
        strength=strength,
        decay_factor=decay_factor,
        days_since_access=days_since_access,
        is_dormant=is_dormant,
        recommended_action=action
    )


def should_include_in_search(memory: Memory, include_dormant: bool = False) -> bool:
    """
    Determine if memory should be included in search results.
    
    By default, excludes dormant memories unless explicitly requested.
    """
    if include_dormant:
        return True
    
    # Check if memory has dormant status
    status = getattr(memory, 'status', 'active')
    if status == 'dormant':
        return False
    
    # Calculate current strength
    strength = calculate_strength(memory)
    return strength >= DORMANT_THRESHOLD


def boost_on_access(memory: Memory) -> Dict[str, Any]:
    """
    Boost memory strength when accessed (retrieved in search).
    
    Returns dict of fields to update on the memory.
    """
    access_count = getattr(memory, 'access_count', 0) or 0
    
    return {
        'access_count': access_count + 1,
        'last_accessed': datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    }


def find_consolidation_candidates(
    memories: List[Memory],
    similarity_threshold: float = 0.8,
    min_memories: int = 3
) -> List[List[Memory]]:
    """
    Find groups of similar fading memories that could be consolidated.
    
    Returns list of groups, where each group contains similar memories
    that could be merged into a summary.
    """
    # Get fading memories (strength below 0.5 but above dormant)
    fading = [
        m for m in memories 
        if DORMANT_THRESHOLD <= calculate_strength(m) < 0.5
    ]
    
    if len(fading) < min_memories:
        return []
    
    # Group by topic prefix (simple heuristic)
    topic_groups: Dict[str, List[Memory]] = {}
    for m in fading:
        # Use first part of topic as group key
        prefix = m.topic.split('/')[0] if '/' in m.topic else m.topic
        if prefix not in topic_groups:
            topic_groups[prefix] = []
        topic_groups[prefix].append(m)
    
    # Return groups with enough memories
    return [
        group for group in topic_groups.values() 
        if len(group) >= min_memories
    ]


def create_consolidation_summary(memories: List[Memory]) -> str:
    """
    Create a summary of multiple memories for consolidation.
    
    This would ideally use an LLM, but for now we create a simple summary.
    """
    topics = list(set(m.topic for m in memories))
    lessons = [m.lesson for m in memories]
    
    # Simple concatenation with dedup hints
    summary_parts = [
        f"Consolidated from {len(memories)} memories on: {', '.join(topics)}",
        "",
        "Key points:",
    ]
    
    for i, lesson in enumerate(lessons[:5], 1):  # Max 5 lessons
        # Truncate long lessons
        short = lesson[:200] + "..." if len(lesson) > 200 else lesson
        summary_parts.append(f"{i}. {short}")
    
    if len(lessons) > 5:
        summary_parts.append(f"... and {len(lessons) - 5} more")
    
    return "\n".join(summary_parts)
