"""
Memory Scheduler - Background maintenance like sleep consolidation

Runs periodic fade cycles automatically, mimicking how the brain
consolidates and forgets during sleep.
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class MemoryScheduler:
    """
    Background scheduler for memory maintenance.
    
    Runs fade cycles periodically (default: every 24 hours).
    Like sleep - the system "rests" and consolidates memories.
    """
    
    def __init__(
        self,
        fade_callback: Callable,
        interval_hours: float = 24.0,
        start_delay_minutes: float = 5.0  # Wait before first run
    ):
        self.fade_callback = fade_callback
        self.interval_seconds = interval_hours * 3600
        self.start_delay_seconds = start_delay_minutes * 60
        
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_run: Optional[datetime] = None
        self._next_run: Optional[datetime] = None
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
        """Execute the fade cycle."""
        start_time = datetime.utcnow()
        logger.info(f"🌙 Memory sleep cycle starting at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            result = self.fade_callback()
            self._last_run = datetime.utcnow()
            
            newly_dormant = result.get('newly_dormant', [])
            reactivated = result.get('reactivated', [])
            
            duration = (self._last_run - start_time).total_seconds()
            
            logger.info(
                f"🌙 Memory sleep cycle complete in {duration:.1f}s: "
                f"{len(newly_dormant)} faded to dormant, {len(reactivated)} reactivated"
            )
        except Exception as e:
            logger.error(f"🌙 Memory sleep cycle failed: {e}")
            raise
    
    def get_status(self) -> dict:
        """Get scheduler status."""
        return {
            "running": self._running,
            "interval_hours": self.interval_seconds / 3600,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "next_run": self._next_run.isoformat() if self._next_run else None
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
