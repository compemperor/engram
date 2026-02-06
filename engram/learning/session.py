"""
LearningSession - Structured learning with self-verification

Implements the learning-loop framework:
1. Exploration (gather information)
2. Deep dive (focus on key areas)
3. Self-verification (check understanding)
4. Consolidation (save quality learnings)

v0.11.2: Removed markdown file output - sessions stored in Engram memory system
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class VerificationCheckpoint:
    """Self-verification checkpoint"""
    topic: str
    understanding: float  # 1-5 scale
    sources_verified: bool
    gaps: List[str]  # What's still unclear
    applications: List[str]  # How would I use this
    timestamp: str


@dataclass
class LearningNote:
    """Progressive learning note"""
    content: str
    timestamp: str
    source_url: Optional[str] = None
    source_quality: Optional[int] = None  # 1-10 if evaluated


class LearningSession:
    """
    Structured learning session with self-verification.
    
    Usage:
        session = LearningSession(topic="recursive self-improvement")
        session.add_note("Key finding: ...")
        session.verify(topic="RSI", understanding=4, ...)
        insights = session.consolidate()
    """
    
    def __init__(
        self,
        topic: str,
        duration_min: int = 30,
        enable_verification: bool = True
    ):
        """
        Initialize learning session.
        
        Args:
            topic: Main topic to learn about
            duration_min: Planned duration in minutes
            enable_verification: Enable self-verification checkpoints
        """
        self.topic = topic
        self.duration_min = duration_min
        self.enable_verification = enable_verification
        
        # Session data
        self.notes: List[LearningNote] = []
        self.checkpoints: List[VerificationCheckpoint] = []
        self.insights: List[str] = []
        self.start_time = datetime.now()
        
        # Calculate target end time for time awareness
        from datetime import timedelta
        self.target_end_time = self.start_time + timedelta(minutes=duration_min)
        
        # Generate session ID
        self.session_id = self.start_time.strftime("%Y%m%d-%H%M%S")
    
    def add_note(
        self,
        content: str,
        source_url: Optional[str] = None,
        source_quality: Optional[int] = None
    ):
        """
        Add a progressive learning note.
        
        Args:
            content: The note content
            source_url: Optional source URL
            source_quality: Optional quality rating (1-10)
        """
        note = LearningNote(
            content=content,
            timestamp=datetime.now().strftime("%H:%M"),
            source_url=source_url,
            source_quality=source_quality
        )
        self.notes.append(note)
    
    def verify(
        self,
        topic: str,
        understanding: float,
        sources_verified: bool = False,
        gaps: Optional[List[str]] = None,
        applications: Optional[List[str]] = None
    ) -> VerificationCheckpoint:
        """
        Add self-verification checkpoint.
        
        Args:
            topic: Topic being verified
            understanding: Understanding rating (1-5)
            sources_verified: Were sources verified against primary sources?
            gaps: List of things still unclear
            applications: List of how you'd apply this knowledge
        
        Returns:
            VerificationCheckpoint object
        """
        checkpoint = VerificationCheckpoint(
            topic=topic,
            understanding=understanding,
            sources_verified=sources_verified,
            gaps=gaps or [],
            applications=applications or [],
            timestamp=datetime.now().strftime("%H:%M")
        )
        self.checkpoints.append(checkpoint)
        return checkpoint
    
    def add_insight(self, insight: str):
        """
        Add a key insight.
        
        Args:
            insight: The insight text
        """
        self.insights.append(insight)
    
    def consolidate(self) -> Dict[str, Any]:
        """
        Consolidate session and generate summary.
        
        Converts high-quality notes to insights automatically.
        Returns structured data for storage in Engram memory system.
        
        Returns:
            Dict with session summary, metrics, and data for memory storage
        """
        duration = self.elapsed_time()
        
        # Warn if consolidating before target time (but still allow it)
        if not self.is_target_time_reached():
            remaining = self.time_remaining()
            print(f"⚠️  Warning: Consolidating {remaining:.1f} min before target end time")
            print(f"    Planned: {self.duration_min} min | Actual: {duration:.1f} min")
        
        # Auto-convert high-quality notes to insights
        for note in self.notes:
            if note.source_quality and note.source_quality >= 8:
                # High-quality note becomes an insight
                if note.content not in self.insights:
                    self.insights.append(note.content)
        
        # Calculate quality metrics
        verified_sources = sum(1 for note in self.notes if note.source_quality and note.source_quality >= 7)
        avg_understanding = (
            sum(c.understanding for c in self.checkpoints) / len(self.checkpoints)
            if self.checkpoints else 0.0
        )
        
        summary = {
            "topic": self.topic,
            "session_id": self.session_id,
            "duration_min": round(duration, 1),
            "notes_count": len(self.notes),
            "checkpoints_count": len(self.checkpoints),
            "insights_count": len(self.insights),
            "verified_sources": verified_sources,
            "average_understanding": round(avg_understanding, 2),
            "timestamp": self.start_time.isoformat()
        }
        
        return summary
    
    def get_notes_for_storage(self) -> List[Dict[str, Any]]:
        """
        Get notes formatted for memory storage.
        
        Returns:
            List of note dicts ready for memory system
        """
        return [
            {
                "content": note.content,
                "timestamp": note.timestamp,
                "source_url": note.source_url,
                "source_quality": note.source_quality
            }
            for note in self.notes
        ]
    
    def get_checkpoints_for_storage(self) -> List[Dict[str, Any]]:
        """
        Get checkpoints formatted for memory storage.
        
        Returns:
            List of checkpoint dicts
        """
        return [asdict(checkpoint) for checkpoint in self.checkpoints]
    
    def get_topics_covered(self) -> List[str]:
        """Get list of topics from checkpoints"""
        return [c.topic for c in self.checkpoints]
    
    def get_understanding_ratings(self) -> List[float]:
        """Get understanding ratings from checkpoints"""
        return [c.understanding for c in self.checkpoints]
    
    def all_sources_verified(self) -> bool:
        """Check if all sources were verified"""
        if not self.checkpoints:
            return False
        return all(c.sources_verified for c in self.checkpoints)
    
    def time_remaining(self) -> float:
        """
        Get time remaining until target end time (in minutes).
        
        Returns:
            Minutes remaining (negative if past target)
        """
        now = datetime.now()
        remaining_seconds = (self.target_end_time - now).total_seconds()
        return remaining_seconds / 60
    
    def elapsed_time(self) -> float:
        """
        Get elapsed time since session start (in minutes).
        
        Returns:
            Minutes elapsed
        """
        now = datetime.now()
        elapsed_seconds = (now - self.start_time).total_seconds()
        return elapsed_seconds / 60
    
    def is_target_time_reached(self) -> bool:
        """
        Check if target end time has been reached.
        
        Returns:
            True if current time >= target_end_time
        """
        return datetime.now() >= self.target_end_time
    
    def time_check(self) -> Dict[str, Any]:
        """
        Get current time status for the session.
        
        Returns:
            Dict with time metrics
        """
        now = datetime.now()
        elapsed = self.elapsed_time()
        remaining = self.time_remaining()
        progress_pct = (elapsed / self.duration_min) * 100 if self.duration_min > 0 else 0
        
        return {
            "start_time": self.start_time.isoformat(),
            "target_end_time": self.target_end_time.isoformat(),
            "current_time": now.isoformat(),
            "planned_duration_min": self.duration_min,
            "elapsed_min": round(elapsed, 2),
            "remaining_min": round(remaining, 2),
            "progress_percent": round(progress_pct, 1),
            "target_reached": self.is_target_time_reached()
        }
