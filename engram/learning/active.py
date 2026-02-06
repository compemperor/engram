"""
Active Learning Module

Tracks knowledge gaps and suggests what to learn next.

Features:
- Tracks searches with poor results (gaps)
- Tracks failed recall challenges (weak areas)
- Prioritizes learning suggestions
- Maintains "to-learn" queue
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
import json
import os
from pathlib import Path


@dataclass
class KnowledgeGap:
    """Represents a gap in knowledge"""
    query: str  # What was searched for
    category: str  # Gap type: search_miss, recall_fail, low_score, user_request
    detected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    search_results_count: int = 0
    best_score: float = 0.0
    frequency: int = 1  # How many times this gap was hit
    priority: float = 0.5  # 0-1, higher = more urgent
    related_topics: List[str] = field(default_factory=list)
    resolved: bool = False
    resolved_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LearningPriority:
    """A prioritized learning suggestion"""
    topic: str
    reason: str
    priority: float  # 0-1
    gaps: List[str]  # Related gap queries
    suggested_sources: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ActiveLearningTracker:
    """Tracks knowledge gaps and generates learning priorities"""
    
    def __init__(self, data_dir: str = "/data"):
        self.data_dir = Path(data_dir)
        self.gaps_file = self.data_dir / "active_learning" / "gaps.json"
        self.gaps_file.parent.mkdir(parents=True, exist_ok=True)
        self.gaps: Dict[str, KnowledgeGap] = {}
        self._load()
    
    def _load(self):
        """Load gaps from disk"""
        if self.gaps_file.exists():
            try:
                with open(self.gaps_file, "r") as f:
                    data = json.load(f)
                    for key, gap_data in data.items():
                        self.gaps[key] = KnowledgeGap(**gap_data)
            except Exception as e:
                print(f"[ActiveLearning] Failed to load gaps: {e}")
    
    def _save(self):
        """Persist gaps to disk"""
        try:
            with open(self.gaps_file, "w") as f:
                json.dump({k: v.to_dict() for k, v in self.gaps.items()}, f, indent=2)
        except Exception as e:
            print(f"[ActiveLearning] Failed to save gaps: {e}")
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for deduplication"""
        return query.lower().strip()
    
    def track_search_gap(
        self,
        query: str,
        results_count: int,
        best_score: float,
        threshold_count: int = 3,
        threshold_score: float = 0.5
    ):
        """
        Track a search that returned poor results.
        
        Args:
            query: Search query
            results_count: Number of results returned
            best_score: Score of best result
            threshold_count: Minimum acceptable results
            threshold_score: Minimum acceptable score
        """
        # Only track if below thresholds
        if results_count >= threshold_count and best_score >= threshold_score:
            return
        
        key = self._normalize_query(query)
        
        if key in self.gaps:
            # Increment frequency for existing gap
            gap = self.gaps[key]
            gap.frequency += 1
            gap.priority = min(1.0, gap.priority + 0.1)  # Increase priority
            if results_count < gap.search_results_count:
                gap.search_results_count = results_count
            if best_score > gap.best_score:
                gap.best_score = best_score
        else:
            # Create new gap
            category = "search_miss" if results_count == 0 else "low_score"
            self.gaps[key] = KnowledgeGap(
                query=query,
                category=category,
                search_results_count=results_count,
                best_score=best_score,
                priority=0.5 if results_count > 0 else 0.7
            )
        
        self._save()
    
    def track_recall_failure(
        self,
        topic: str,
        memory_id: str,
        confidence: float
    ):
        """Track a failed recall challenge"""
        key = f"recall:{topic}"
        
        if key in self.gaps:
            gap = self.gaps[key]
            gap.frequency += 1
            gap.priority = min(1.0, gap.priority + 0.15)
        else:
            self.gaps[key] = KnowledgeGap(
                query=f"Recall failed: {topic}",
                category="recall_fail",
                priority=0.6,
                related_topics=[topic]
            )
        
        self._save()
    
    def track_user_request(self, topic: str, context: str = ""):
        """User explicitly requested to learn something"""
        key = f"user:{self._normalize_query(topic)}"
        
        self.gaps[key] = KnowledgeGap(
            query=topic,
            category="user_request",
            priority=0.9,  # User requests are high priority
            related_topics=[topic] if topic else []
        )
        
        self._save()
    
    def resolve_gap(self, query: str):
        """Mark a gap as resolved"""
        key = self._normalize_query(query)
        if key in self.gaps:
            self.gaps[key].resolved = True
            self.gaps[key].resolved_at = datetime.utcnow().isoformat()
            self._save()
    
    def get_gaps(
        self,
        include_resolved: bool = False,
        min_priority: float = 0.0,
        limit: int = 20
    ) -> List[KnowledgeGap]:
        """Get knowledge gaps sorted by priority"""
        gaps = list(self.gaps.values())
        
        if not include_resolved:
            gaps = [g for g in gaps if not g.resolved]
        
        gaps = [g for g in gaps if g.priority >= min_priority]
        gaps.sort(key=lambda g: (-g.priority, -g.frequency))
        
        return gaps[:limit]
    
    def get_learning_suggestions(self, limit: int = 5) -> List[LearningPriority]:
        """Generate prioritized learning suggestions"""
        gaps = self.get_gaps(limit=50)
        
        # Group by category and theme
        topic_scores: Dict[str, float] = {}
        topic_gaps: Dict[str, List[str]] = {}
        
        for gap in gaps:
            # Extract topic from query (simple heuristic)
            words = gap.query.lower().split()
            topic = words[0] if words else "general"
            
            # For recall failures, use the related topic
            if gap.category == "recall_fail" and gap.related_topics:
                topic = gap.related_topics[0].split("/")[0]
            
            if topic not in topic_scores:
                topic_scores[topic] = 0.0
                topic_gaps[topic] = []
            
            topic_scores[topic] += gap.priority * gap.frequency
            topic_gaps[topic].append(gap.query)
        
        # Create suggestions
        suggestions = []
        for topic, score in sorted(topic_scores.items(), key=lambda x: -x[1]):
            reason = self._generate_reason(topic, topic_gaps[topic])
            suggestions.append(LearningPriority(
                topic=topic,
                reason=reason,
                priority=min(1.0, score / 10),  # Normalize
                gaps=topic_gaps[topic][:5]
            ))
        
        return suggestions[:limit]
    
    def _generate_reason(self, topic: str, gaps: List[str]) -> str:
        """Generate a human-readable reason for learning suggestion"""
        if len(gaps) == 1:
            return f"Knowledge gap detected: {gaps[0]}"
        else:
            return f"{len(gaps)} knowledge gaps in {topic} area"
    
    def stats(self) -> Dict[str, Any]:
        """Get statistics about knowledge gaps"""
        all_gaps = list(self.gaps.values())
        active = [g for g in all_gaps if not g.resolved]
        
        by_category = {}
        for gap in active:
            by_category[gap.category] = by_category.get(gap.category, 0) + 1
        
        return {
            "total_gaps": len(all_gaps),
            "active_gaps": len(active),
            "resolved_gaps": len(all_gaps) - len(active),
            "by_category": by_category,
            "avg_priority": sum(g.priority for g in active) / len(active) if active else 0,
            "most_frequent": sorted(active, key=lambda g: -g.frequency)[:3] if active else []
        }


# Global instance
_tracker: Optional[ActiveLearningTracker] = None


def get_tracker(data_dir: str = "/data") -> ActiveLearningTracker:
    """Get or create the active learning tracker"""
    global _tracker
    if _tracker is None:
        _tracker = ActiveLearningTracker(data_dir)
    return _tracker
