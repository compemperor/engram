"""
LearningSession - Structured learning with self-verification

Implements the learning-loop framework:
1. Exploration (gather information)
2. Deep dive (focus on key areas)
3. Self-verification (check understanding)
4. Consolidation (save quality learnings)
"""

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
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
        output_dir: str = "./memories/learning-sessions",
        enable_verification: bool = True
    ):
        """
        Initialize learning session.
        
        Args:
            topic: Main topic to learn about
            duration_min: Planned duration in minutes
            output_dir: Directory to save session files
            enable_verification: Enable self-verification checkpoints
        """
        self.topic = topic
        self.duration_min = duration_min
        self.enable_verification = enable_verification
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Session data
        self.notes: List[LearningNote] = []
        self.checkpoints: List[VerificationCheckpoint] = []
        self.insights: List[str] = []
        self.start_time = datetime.now()
        
        # Calculate target end time for time awareness
        from datetime import timedelta
        self.target_end_time = self.start_time + timedelta(minutes=duration_min)
        
        # Generate session file name
        timestamp = self.start_time.strftime("%Y-%m-%d-%H%M%S")
        safe_topic = "".join(c if c.isalnum() or c in " -" else "" for c in topic)
        safe_topic = safe_topic.replace(" ", "-")[:50]
        self.session_file = self.output_dir / f"{timestamp}-{safe_topic}.md"
    
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
        
        Returns:
            Dict with session summary and metrics
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
            "duration_min": round(duration, 1),
            "notes_count": len(self.notes),
            "checkpoints_count": len(self.checkpoints),
            "insights_count": len(self.insights),
            "verified_sources": verified_sources,
            "average_understanding": round(avg_understanding, 2),
            "session_file": str(self.session_file),
            "timestamp": self.start_time.isoformat()
        }
        
        # Save session file
        self._save_session_file(summary)
        
        return summary
    
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
    
    def _save_session_file(self, summary: Dict[str, Any]):
        """Save session to markdown file"""
        content = f"""# Learning Session - {self.start_time.strftime("%Y-%m-%d %H:%M")}

**Topic:** {self.topic}  
**Duration:** {summary['duration_min']} min  
**Goal:** Deep understanding with self-verification  

---

## Progressive Notes

"""
        
        for note in self.notes:
            content += f"### {note.timestamp}\n\n"
            content += f"{note.content}\n\n"
            if note.source_url:
                content += f"**Source:** {note.source_url}\n"
            if note.source_quality:
                content += f"**Quality:** {note.source_quality}/10\n"
            content += "\n"
        
        content += "---\n\n## Self-Verification Checkpoints\n\n"
        
        for checkpoint in self.checkpoints:
            content += f"### {checkpoint.timestamp} - {checkpoint.topic}\n\n"
            content += f"**Understanding:** {checkpoint.understanding}/5\n"
            content += f"**Sources Verified:** {'✅' if checkpoint.sources_verified else '❌'}\n\n"
            
            if checkpoint.gaps:
                content += "**Gaps:**\n"
                for gap in checkpoint.gaps:
                    content += f"- {gap}\n"
                content += "\n"
            
            if checkpoint.applications:
                content += "**Applications:**\n"
                for app in checkpoint.applications:
                    content += f"- {app}\n"
                content += "\n"
        
        if self.insights:
            content += "---\n\n## Key Insights\n\n"
            for i, insight in enumerate(self.insights, 1):
                content += f"{i}. {insight}\n"
        
        content += f"""
---

## Summary

**Topics Covered:** {len(self.checkpoints)}  
**Average Understanding:** {summary['average_understanding']}/5  
**Verified Sources:** {summary['verified_sources']}/{len(self.notes)}  
**Key Insights:** {summary['insights_count']}  

**Session Duration:** {summary['duration_min']} min  
**Status:** {'✅ Complete' if self.checkpoints else '⏳ In Progress'}

🦀 Learning session complete!
"""
        
        with open(self.session_file, "w") as f:
            f.write(content)
