"""
DriftDetector - Monitor and detect drift from goals/persona

Inspired by Butterfly RSI's stability monitoring.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class DriftAlert:
    """Drift detection alert"""
    severity: str  # "low", "medium", "high"
    category: str  # "topic", "quality", "understanding"
    message: str
    metric: float  # The drift metric value
    threshold: float  # The threshold that was exceeded


class DriftDetector:
    """
    Monitors learning patterns and alerts on drift.
    
    Detects:
    - Topic drift (learning unrelated things)
    - Quality drift (accepting low-quality sources)
    - Understanding drift (declining comprehension)
    """
    
    def __init__(
        self,
        path: str = "./memories",
        topic_drift_threshold: float = 0.7,
        quality_threshold: float = 6.0,
        understanding_threshold: float = 3.0
    ):
        """
        Initialize drift detector.
        
        Args:
            path: Directory for storing drift data
            topic_drift_threshold: Max topic diversity before alerting (0-1)
            quality_threshold: Min quality score before alerting (0-10)
            understanding_threshold: Min understanding before alerting (0-5)
        """
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        
        self.topic_drift_threshold = topic_drift_threshold
        self.quality_threshold = quality_threshold
        self.understanding_threshold = understanding_threshold
        
        self.metrics_file = self.path / "mirror-metrics.jsonl"
    
    def check_drift(self, window: int = 10) -> List[DriftAlert]:
        """
        Check for drift in recent sessions.
        
        Args:
            window: Number of recent sessions to analyze
        
        Returns:
            List of DriftAlert objects
        """
        metrics = self._load_recent_metrics(window)
        
        if len(metrics) < 3:
            return []  # Not enough data
        
        alerts = []
        
        # Check quality drift
        recent_quality = [m.get("source_quality", 0) for m in metrics[-3:]]
        avg_quality = sum(recent_quality) / len(recent_quality)
        
        if avg_quality < self.quality_threshold:
            alerts.append(DriftAlert(
                severity="high" if avg_quality < 5 else "medium",
                category="quality",
                message=f"Quality declining: recent average {avg_quality:.1f}/10",
                metric=avg_quality,
                threshold=self.quality_threshold
            ))
        
        # Check understanding drift
        recent_understanding = [m.get("understanding", 0) for m in metrics[-3:]]
        avg_understanding = sum(recent_understanding) / len(recent_understanding)
        
        if avg_understanding < self.understanding_threshold:
            alerts.append(DriftAlert(
                severity="high" if avg_understanding < 2 else "medium",
                category="understanding",
                message=f"Understanding declining: recent average {avg_understanding:.1f}/5",
                metric=avg_understanding,
                threshold=self.understanding_threshold
            ))
        
        # Check topic drift
        # TODO: Implement topic coherence checking
        # Would need persona/goal definitions
        
        return alerts
    
    def get_stability_score(self, window: int = 10) -> float:
        """
        Calculate overall stability score (0-1, higher = more stable).
        
        Args:
            window: Number of recent sessions to analyze
        
        Returns:
            Stability score 0-1
        """
        metrics = self._load_recent_metrics(window)
        
        if not metrics:
            return 1.0  # No data = assume stable
        
        # Quality stability
        qualities = [m.get("source_quality", 5) for m in metrics]
        quality_std = self._std_dev(qualities)
        quality_score = max(0, 1 - (quality_std / 10))  # Normalize
        
        # Understanding stability
        understandings = [m.get("understanding", 2.5) for m in metrics]
        understanding_std = self._std_dev(understandings)
        understanding_score = max(0, 1 - (understanding_std / 5))  # Normalize
        
        # Combined score
        return (quality_score + understanding_score) / 2
    
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
    
    def _std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
