"""
MirrorEvaluator - Quality evaluation for learning sessions and memories

Inspired by Butterfly RSI's self-correction principles.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List


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
    - Drift detection from goals/persona
    - Consolidation decision making
    """
    
    def __init__(
        self,
        path: str = "./memories",
        quality_threshold: float = 7.0,
        understanding_threshold: float = 3.0
    ):
        """
        Initialize evaluator.
        
        Args:
            path: Directory for storing evaluation metrics
            quality_threshold: Minimum quality score for consolidation (0-10)
            understanding_threshold: Minimum understanding score (0-5)
        """
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        
        self.metrics_file = self.path / "mirror-metrics.jsonl"
        self.state_file = self.path / "mirror-state.json"
        
        self.quality_threshold = quality_threshold
        self.understanding_threshold = understanding_threshold
        
        # Load state
        self.state = self._load_state()
    
    def evaluate_session(
        self,
        sources_verified: bool,
        understanding_ratings: List[float],
        topics: List[str],
        notes: Optional[str] = None
    ) -> QualityEvaluation:
        """
        Evaluate a learning session.
        
        Args:
            sources_verified: Were all sources verified against primary sources?
            understanding_ratings: List of understanding scores (1-5) per topic
            topics: List of topics covered
            notes: Optional evaluation notes
        
        Returns:
            QualityEvaluation object
        """
        # Source quality scoring
        source_quality = 9.0 if sources_verified else 5.0
        
        # Understanding depth (average of ratings)
        understanding = sum(understanding_ratings) / len(understanding_ratings) if understanding_ratings else 0.0
        
        # Drift calculation (placeholder - can be enhanced)
        drift_score = self._calculate_drift(topics)
        
        # Consolidation decision
        consolidate = (
            source_quality >= self.quality_threshold and
            understanding >= self.understanding_threshold and
            drift_score < 0.3  # Low drift
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
        drift_score = self._calculate_drift([topic])
        
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
    
    def _calculate_drift(self, topics: List[str]) -> float:
        """
        Calculate drift from recent topics.
        
        Placeholder implementation - can be enhanced with:
        - Persona alignment checking
        - Goal divergence detection
        - Topic diversity metrics
        """
        recent_topics = self.state.get("recent_topics", [])
        
        if not recent_topics:
            return 0.0
        
        # Simple diversity-based drift
        # More diverse topics = higher drift
        unique_topics = set(recent_topics[-10:] + topics)
        diversity = len(unique_topics) / 10  # Normalize to 0-1
        
        return min(diversity, 1.0)
    
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
