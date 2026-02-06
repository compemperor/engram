"""
MirrorEvaluator - Quality evaluation for learning sessions and memories

Inspired by Butterfly RSI's self-correction principles.

v0.12.0: Goal-aligned drift calculation using semantic similarity
"""

import json
import numpy as np
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from engram.memory.store import MemoryStore


@dataclass
class QualityEvaluation:
    """Quality evaluation result"""
    source_quality: float  # 0-10 scale
    understanding: float  # 0-5 scale
    drift_score: float  # 0-1 scale (0 = no drift, 1 = max drift)
    verified: bool  # Were sources verified?
    consolidate: bool  # Should this be saved to long-term memory?
    timestamp: str
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MirrorEvaluator:
    """
    Quality control system for memories and learning sessions.
    
    Features:
    - Source quality scoring
    - Understanding depth evaluation
    - Goal-aligned drift detection (v0.12.0)
    - Consolidation decision making
    """
    
    def __init__(
        self,
        path: str = "./memories",
        quality_threshold: float = 7.0,
        understanding_threshold: float = 3.0,
        memory_store: Optional["MemoryStore"] = None
    ):
        """
        Initialize evaluator.
        
        Args:
            path: Directory for storing evaluation metrics
            quality_threshold: Minimum quality score for consolidation (0-10)
            understanding_threshold: Minimum understanding score (0-5)
            memory_store: Optional MemoryStore for goal-aligned drift calculation
        """
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        
        self.metrics_file = self.path / "mirror-metrics.jsonl"
        self.state_file = self.path / "mirror-state.json"
        
        self.quality_threshold = quality_threshold
        self.understanding_threshold = understanding_threshold
        self.memory_store = memory_store
        
        # Cache for goal embeddings
        self._goals_embedding: Optional[np.ndarray] = None
        self._goals_cache_time: Optional[datetime] = None
        
        # Load state
        self.state = self._load_state()
    
    def set_memory_store(self, memory_store: "MemoryStore"):
        """Set memory store reference (for late binding)"""
        self.memory_store = memory_store
    
    def evaluate_session(
        self,
        sources_verified: bool,
        understanding_ratings: List[float],
        topics: List[str],
        content: Optional[str] = None,
        notes: Optional[str] = None
    ) -> QualityEvaluation:
        """
        Evaluate a learning session.
        
        Args:
            sources_verified: Were all sources verified against primary sources?
            understanding_ratings: List of understanding scores (1-5) per topic
            topics: List of topics covered
            content: Optional content for goal-aligned drift calculation
            notes: Optional evaluation notes
        
        Returns:
            QualityEvaluation object
        """
        # Source quality scoring
        source_quality = 9.0 if sources_verified else 5.0
        
        # Understanding depth (average of ratings)
        understanding = sum(understanding_ratings) / len(understanding_ratings) if understanding_ratings else 0.0
        
        # Goal-aligned drift calculation
        drift_score = self._calculate_drift(topics, content)
        
        # Consolidation decision
        # Note: drift_score NOT checked for learning sessions - exploration is expected
        consolidate = (
            source_quality >= self.quality_threshold and
            understanding >= self.understanding_threshold
        )
        
        evaluation = QualityEvaluation(
            source_quality=source_quality,
            understanding=understanding,
            drift_score=drift_score,
            verified=sources_verified,
            consolidate=consolidate,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            notes=notes
        )
        
        # Save metrics
        self._save_metric(evaluation)
        
        # Update state
        self._update_state(evaluation, topics)
        
        return evaluation
    
    def evaluate_memory(
        self,
        topic: str,
        lesson: str,
        source_verified: bool = False,
        understanding: Optional[float] = None
    ) -> QualityEvaluation:
        """
        Evaluate a single memory before storage.
        
        Args:
            topic: Memory topic
            lesson: The lesson content
            source_verified: Was source verified?
            understanding: Understanding score (1-5)
        
        Returns:
            QualityEvaluation object
        """
        source_quality = 9.0 if source_verified else 6.0
        understanding_score = understanding if understanding else 3.0
        
        # Goal-aligned drift using lesson content
        drift_score = self._calculate_drift([topic], lesson)
        
        consolidate = (
            source_quality >= self.quality_threshold and
            understanding_score >= self.understanding_threshold
        )
        
        evaluation = QualityEvaluation(
            source_quality=source_quality,
            understanding=understanding_score,
            drift_score=drift_score,
            verified=source_verified,
            consolidate=consolidate,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        
        self._save_metric(evaluation)
        self._update_state(evaluation, [topic])
        
        return evaluation
    
    def get_drift_metrics(self) -> Dict[str, Any]:
        """Get current drift metrics"""
        return {
            "recent_topics": self.state.get("recent_topics", []),
            "average_quality": self.state.get("average_quality", 0.0),
            "average_understanding": self.state.get("average_understanding", 0.0),
            "total_evaluations": self.state.get("total_evaluations", 0),
            "goal_aligned": self.memory_store is not None,
            "last_updated": self.state.get("last_updated")
        }
    
    def get_quality_trends(self, last_n: int = 10) -> Dict[str, Any]:
        """Get quality trends from recent evaluations"""
        metrics = self._load_recent_metrics(last_n)
        
        if not metrics:
            return {
                "count": 0,
                "average_quality": 0.0,
                "average_understanding": 0.0,
                "trend": "no_data"
            }
        
        qualities = [m["source_quality"] for m in metrics]
        understandings = [m["understanding"] for m in metrics]
        
        # Simple trend detection
        if len(qualities) >= 2:
            recent_avg = sum(qualities[-3:]) / min(3, len(qualities))
            older_avg = sum(qualities[:-3]) / max(1, len(qualities) - 3) if len(qualities) > 3 else recent_avg
            
            if recent_avg > older_avg + 1:
                trend = "improving"
            elif recent_avg < older_avg - 1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "count": len(metrics),
            "average_quality": sum(qualities) / len(qualities),
            "average_understanding": sum(understandings) / len(understandings),
            "trend": trend,
            "recent_scores": qualities[-5:]
        }
    
    # Private methods
    
    def _get_goals_embedding(self) -> Optional[np.ndarray]:
        """
        Get cached goals embedding, refreshing if needed.
        
        Searches for identity/goals and identity/interests in memory,
        combines them, and caches the embedding.
        """
        if self.memory_store is None:
            return None
        
        # Check cache (refresh every 5 minutes)
        now = datetime.now()
        if (self._goals_embedding is not None and 
            self._goals_cache_time is not None and
            (now - self._goals_cache_time).total_seconds() < 300):
            return self._goals_embedding
        
        try:
            # Search for goals and interests
            goals_text = []
            
            # Try to recall identity/goals
            goals = self.memory_store.recall("identity/goals")
            for mem in goals[:5]:  # Limit to 5
                goals_text.append(mem.lesson)
            
            # Try to recall identity/interests
            interests = self.memory_store.recall("identity/interests")
            for mem in interests[:5]:  # Limit to 5
                goals_text.append(mem.lesson)
            
            # Try to recall user/preferences
            prefs = self.memory_store.recall("user/preferences")
            for mem in prefs[:3]:  # Limit to 3
                goals_text.append(mem.lesson)
            
            if not goals_text:
                # No goals found - can't calculate goal-aligned drift
                return None
            
            # Combine and embed
            combined_goals = " ".join(goals_text)
            self._goals_embedding = self.memory_store.embedder.encode(
                combined_goals, 
                is_query=False
            )
            self._goals_cache_time = now
            
            return self._goals_embedding
            
        except Exception as e:
            print(f"[MirrorEvaluator] Error getting goals embedding: {e}")
            return None
    
    def _calculate_drift(self, topics: List[str], content: Optional[str] = None) -> float:
        """
        Calculate drift using goal alignment.
        
        v0.12.0: Uses semantic similarity between content and stored goals.
        If no goals are stored or no memory_store, falls back to topic diversity.
        
        Args:
            topics: List of topics being evaluated
            content: Optional content to compare against goals
        
        Returns:
            Drift score 0-1 (0 = perfectly aligned, 1 = completely off-topic)
        """
        # Try goal-aligned drift first
        if content and self.memory_store is not None:
            goals_embedding = self._get_goals_embedding()
            
            if goals_embedding is not None:
                try:
                    # Embed the content
                    content_embedding = self.memory_store.embedder.encode(
                        content,
                        is_query=False
                    )
                    
                    # Calculate cosine similarity
                    similarity = self._cosine_similarity(content_embedding, goals_embedding)
                    
                    # Convert to drift (high similarity = low drift)
                    drift = 1.0 - similarity
                    
                    # Clamp to 0-1
                    return max(0.0, min(1.0, drift))
                    
                except Exception as e:
                    print(f"[MirrorEvaluator] Error calculating goal drift: {e}")
                    # Fall through to topic-based drift
        
        # Fallback: topic diversity-based drift
        recent_topics = self.state.get("recent_topics", [])
        
        if not recent_topics:
            return 0.0
        
        unique_topics = set(recent_topics[-10:] + topics)
        diversity = len(unique_topics) / 10
        
        return min(diversity, 1.0)
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        a = a.flatten()
        b = b.flatten()
        
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    def _save_metric(self, evaluation: QualityEvaluation):
        """Append evaluation to metrics file"""
        with open(self.metrics_file, "a") as f:
            f.write(json.dumps(evaluation.to_dict()) + "\n")
    
    def _update_state(self, evaluation: QualityEvaluation, topics: List[str]):
        """Update running state"""
        # Add topics
        recent_topics = self.state.get("recent_topics", [])
        recent_topics.extend(topics)
        self.state["recent_topics"] = recent_topics[-20:]  # Keep last 20
        
        # Update averages
        total = self.state.get("total_evaluations", 0)
        avg_quality = self.state.get("average_quality", 0.0)
        avg_understanding = self.state.get("average_understanding", 0.0)
        
        # Running average
        self.state["average_quality"] = (avg_quality * total + evaluation.source_quality) / (total + 1)
        self.state["average_understanding"] = (avg_understanding * total + evaluation.understanding) / (total + 1)
        self.state["total_evaluations"] = total + 1
        self.state["last_updated"] = datetime.now().isoformat()
        
        self._save_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Load state file"""
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                return json.load(f)
        return {}
    
    def _save_state(self):
        """Save state file"""
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)
    
    def _load_recent_metrics(self, n: int) -> List[Dict[str, Any]]:
        """Load last N metrics"""
        if not self.metrics_file.exists():
            return []
        
        metrics = []
        with open(self.metrics_file, "r") as f:
            for line in f:
                if line.strip():
                    metrics.append(json.loads(line))
        
        return metrics[-n:]
