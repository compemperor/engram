"""
Memory Scheduler - Background maintenance like sleep consolidation

Runs periodic fade cycles and auto-reflections automatically, mimicking how the brain
consolidates and forgets during sleep.
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable, List, Dict, Any

logger = logging.getLogger(__name__)


class MemoryScheduler:
    """
    Background scheduler for memory maintenance.
    
    Runs fade cycles and auto-reflections periodically (default: every 24 hours).
    Like sleep - the system "rests" and consolidates memories.
    """
    
    def __init__(
        self,
        fade_callback: Callable,
        interval_hours: float = 24.0,
        start_delay_minutes: float = 5.0,  # Wait before first run
        # v0.7.1: Auto-reflection settings
        reflect_callback: Optional[Callable] = None,
        get_reflection_candidates_callback: Optional[Callable] = None,
        enable_auto_reflect: bool = True,
        reflect_min_memories: int = 5,
        reflect_min_days_since_last: int = 7,
        # v0.8.1: Auto quality assessment settings
        quality_assess_callback: Optional[Callable] = None,
        quality_apply_callback: Optional[Callable] = None,
        enable_auto_quality: bool = True,
        quality_assess_limit: int = 15,
        quality_min_confidence: float = 0.8
    ):
        self.fade_callback = fade_callback
        self.reflect_callback = reflect_callback
        self.get_reflection_candidates_callback = get_reflection_candidates_callback
        self.interval_seconds = interval_hours * 3600
        self.start_delay_seconds = start_delay_minutes * 60
        
        # Auto-reflection settings
        self.enable_auto_reflect = enable_auto_reflect
        self.reflect_min_memories = reflect_min_memories
        self.reflect_min_days_since_last = reflect_min_days_since_last
        
        # v0.8.1: Auto quality assessment settings
        self.quality_assess_callback = quality_assess_callback
        self.quality_apply_callback = quality_apply_callback
        self.enable_auto_quality = enable_auto_quality
        self.quality_assess_limit = quality_assess_limit
        self.quality_min_confidence = quality_min_confidence
        
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_run: Optional[datetime] = None
        self._next_run: Optional[datetime] = None
        self._last_reflection_run: Optional[datetime] = None
        self._last_quality_run: Optional[datetime] = None
        self._running = False
    
    def start(self) -> None:
        """Start the background scheduler."""
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        self._stop_event.clear()
        self._running = True
        self._next_run = datetime.utcnow() + timedelta(seconds=self.start_delay_seconds)
        
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        logger.info(f"Memory scheduler started. First fade cycle in {self.start_delay_seconds/60:.1f} minutes")
    
    def stop(self) -> None:
        """Stop the background scheduler."""
        if not self._running:
            return
        
        self._stop_event.set()
        self._running = False
        
        if self._thread:
            self._thread.join(timeout=5.0)
        
        logger.info("Memory scheduler stopped")
    
    def _run_loop(self) -> None:
        """Main scheduler loop."""
        # Initial delay
        if self._stop_event.wait(self.start_delay_seconds):
            return  # Stopped during initial delay
        
        while not self._stop_event.is_set():
            try:
                self._run_fade_cycle()
            except Exception as e:
                logger.error(f"Fade cycle failed: {e}")
            
            # Update next run time
            self._next_run = datetime.utcnow() + timedelta(seconds=self.interval_seconds)
            
            # Wait for next interval (or stop signal)
            if self._stop_event.wait(self.interval_seconds):
                break
    
    def _run_fade_cycle(self) -> None:
        """Execute the fade cycle and auto-reflections."""
        start_time = datetime.utcnow()
        logger.info(f"🌙 Memory sleep cycle starting at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Phase 1: Fade cycle
        try:
            result = self.fade_callback()
            self._last_run = datetime.utcnow()
            
            newly_dormant = result.get('newly_dormant', [])
            reactivated = result.get('reactivated', [])
            
            logger.info(
                f"🌙 Fade phase complete: "
                f"{len(newly_dormant)} faded to dormant, {len(reactivated)} reactivated"
            )
        except Exception as e:
            logger.error(f"🌙 Fade cycle failed: {e}")
            raise
        
        # Phase 2: Auto-reflection (v0.7.1)
        reflections_created = []
        if self.enable_auto_reflect and self.reflect_callback and self.get_reflection_candidates_callback:
            try:
                reflections_created = self._run_auto_reflections()
            except Exception as e:
                logger.error(f"🌙 Auto-reflection failed: {e}")
                # Don't raise - fade cycle succeeded, reflection is optional
        
        # Phase 3: Auto quality assessment (v0.8.1)
        quality_result = {"upgraded": [], "downgraded": [], "archived": []}
        if self.enable_auto_quality and self.quality_assess_callback and self.quality_apply_callback:
            try:
                quality_result = self._run_auto_quality_assessment()
            except Exception as e:
                logger.error(f"🌙 Auto quality assessment failed: {e}")
                # Don't raise - earlier phases succeeded
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        quality_changes = len(quality_result.get("upgraded", [])) + len(quality_result.get("downgraded", [])) + len(quality_result.get("archived", []))
        
        logger.info(
            f"🌙 Memory sleep cycle complete in {duration:.1f}s: "
            f"{len(newly_dormant)} dormant, {len(reactivated)} reactivated, "
            f"{len(reflections_created)} reflections, {quality_changes} quality adjustments"
        )
    
    def _run_auto_reflections(self) -> List[str]:
        """
        Automatically generate reflections for topics that need them.
        
        Returns list of topics that were reflected on.
        """
        # Get candidate topics (5+ memories, no recent reflection)
        candidates = self.get_reflection_candidates_callback(
            min_memories=self.reflect_min_memories,
            min_days_since_last=self.reflect_min_days_since_last
        )
        
        if not candidates:
            logger.info("🌙 No topics need reflection")
            return []
        
        logger.info(f"🌙 Auto-reflecting on {len(candidates)} topics: {candidates[:5]}...")
        
        reflected_topics = []
        for topic in candidates[:3]:  # Max 3 reflections per cycle to avoid overload
            try:
                result = self.reflect_callback(
                    topic=topic,
                    min_quality=7,
                    min_memories=self.reflect_min_memories,
                    include_subtopics=False  # Only reflect on exact topic, not subtopics
                )
                reflected_topics.append(topic)
                logger.info(f"🌙 Reflected on '{topic}': {result.get('source_count', 0)} memories synthesized")
            except ValueError as e:
                # Not enough memories - skip
                logger.debug(f"🌙 Skipped '{topic}': {e}")
            except Exception as e:
                logger.warning(f"🌙 Failed to reflect on '{topic}': {e}")
        
        self._last_reflection_run = datetime.utcnow()
        return reflected_topics
    
    def _run_auto_quality_assessment(self) -> Dict[str, List[str]]:
        """
        Automatically assess and adjust memory quality.
        
        Returns dict with upgraded, downgraded, archived memory IDs.
        """
        logger.info(f"🌙 Running quality assessment on up to {self.quality_assess_limit} memories...")
        
        # Assess memories (prioritizes those with usage data)
        assessments = self.quality_assess_callback(
            limit=self.quality_assess_limit,
            include_duplicates=True
        )
        
        if not assessments:
            logger.info("🌙 No memories to assess")
            return {"upgraded": [], "downgraded": [], "archived": []}
        
        # Apply adjustments (only high confidence)
        result = self.quality_apply_callback(
            assessments,
            auto_apply=True,
            min_confidence=self.quality_min_confidence
        )
        
        upgraded = result.get("upgraded", [])
        downgraded = result.get("downgraded", [])
        archived = result.get("archived", [])
        skipped = result.get("skipped", [])
        
        if upgraded or downgraded or archived:
            logger.info(
                f"🌙 Quality adjustments applied: "
                f"{len(upgraded)} upgraded, {len(downgraded)} downgraded, "
                f"{len(archived)} archived, {len(skipped)} skipped (low confidence)"
            )
        else:
            logger.info(f"🌙 Quality assessment: no changes needed ({len(skipped)} skipped)")
        
        self._last_quality_run = datetime.utcnow()
        return result
    
    def get_status(self) -> dict:
        """Get scheduler status."""
        return {
            "running": self._running,
            "interval_hours": self.interval_seconds / 3600,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "next_run": self._next_run.isoformat() if self._next_run else None,
            # v0.7.1: Auto-reflection status
            "auto_reflect_enabled": self.enable_auto_reflect,
            "reflect_min_memories": self.reflect_min_memories,
            "reflect_min_days_since_last": self.reflect_min_days_since_last,
            "last_reflection_run": self._last_reflection_run.isoformat() if self._last_reflection_run else None,
            # v0.8.1: Auto quality assessment status
            "auto_quality_enabled": self.enable_auto_quality,
            "quality_assess_limit": self.quality_assess_limit,
            "quality_min_confidence": self.quality_min_confidence,
            "last_quality_run": self._last_quality_run.isoformat() if self._last_quality_run else None
        }
    
    def trigger_now(self) -> dict:
        """Trigger a fade cycle immediately (manual override)."""
        if not self._running:
            raise RuntimeError("Scheduler not running")
        
        self._run_fade_cycle()
        return {
            "status": "triggered",
            "last_run": self._last_run.isoformat() if self._last_run else None
        }
