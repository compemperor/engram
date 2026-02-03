"""
Active Recall System

Generates challenges and tracks recall performance with spaced repetition
"""

import json
import random
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import hashlib

from engram.memory.types import RecallChallenge, RecallAttempt, Memory


class ActiveRecallSystem:
    """
    Manages active recall challenges and tracks performance
    
    Features:
    - Generate challenges from memories
    - Track recall attempts
    - Calculate difficulty based on past performance
    - Schedule reviews
    """
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.challenges_file = storage_path / "recall_challenges.json"
        self.attempts_file = storage_path / "recall_attempts.json"
        
        self.challenges: Dict[str, RecallChallenge] = {}
        self.attempts: List[RecallAttempt] = []
        
        self.load()
    
    def generate_challenge(self, memory: Memory) -> RecallChallenge:
        """
        Generate a recall challenge from a memory
        
        Args:
            memory: Memory to generate challenge from
        
        Returns:
            RecallChallenge
        """
        # Generate challenge ID from memory ID + timestamp
        challenge_id = hashlib.md5(
            f"{memory.memory_id}-{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Determine difficulty based on past recalls
        success_rate = self._get_success_rate(memory.memory_id)
        
        if success_rate >= 0.8:
            difficulty = "hard"  # Good recall, make it harder
        elif success_rate >= 0.5:
            difficulty = "medium"
        else:
            difficulty = "easy"  # Poor recall, make it easier
        
        # Generate question based on memory type
        memory_type_str = memory.memory_type.value if hasattr(memory.memory_type, 'value') else memory.memory_type
        
        if memory_type_str == "episodic":
            # For experiences: "What happened with X?"
            question = f"What did you learn from your experience with {memory.topic}?"
        else:
            # For facts: "What is the rule about X?"
            question = f"What is the key lesson about {memory.topic}?"
        
        challenge = RecallChallenge(
            memory_id=memory.memory_id,
            question=question,
            expected_topics=[memory.topic],
            difficulty=difficulty
        )
        
        self.challenges[challenge_id] = challenge
        return challenge
    
    def record_attempt(
        self,
        challenge_id: str,
        memory_id: str,
        success: bool,
        confidence: float,
        time_taken_ms: int
    ) -> RecallAttempt:
        """
        Record a recall attempt
        
        Args:
            challenge_id: ID of the challenge
            memory_id: ID of the memory being recalled
            success: Whether recall was successful
            confidence: 0-1 confidence rating
            time_taken_ms: Time taken in milliseconds
        
        Returns:
            RecallAttempt
        """
        attempt = RecallAttempt(
            challenge_id=challenge_id,
            memory_id=memory_id,
            success=success,
            confidence=confidence,
            time_taken_ms=time_taken_ms
        )
        
        self.attempts.append(attempt)
        return attempt
    
    def get_due_for_review(
        self,
        memories: List[Memory],
        count: int = 5
    ) -> List[Memory]:
        """
        Get memories due for review (spaced repetition)
        
        Args:
            memories: All available memories
            count: Number to return
        
        Returns:
            List of memories needing review
        """
        # Calculate priority for each memory
        priorities = []
        
        for memory in memories:
            # Skip if never recalled
            if memory.recall_count == 0:
                priority = 1.0  # High priority for new memories
            else:
                # Lower priority for recently recalled, high success rate
                success_rate = self._get_success_rate(memory.memory_id)
                recency = self._get_recency_score(memory.last_recalled)
                
                # Priority = (1 - success_rate) * recency_score
                priority = (1 - success_rate) * recency
            
            priorities.append((priority, memory))
        
        # Sort by priority (highest first)
        priorities.sort(key=lambda x: x[0], reverse=True)
        
        # Return top N
        return [m for _, m in priorities[:count]]
    
    def get_statistics(self, memory_id: Optional[str] = None) -> Dict:
        """
        Get recall statistics
        
        Args:
            memory_id: If provided, stats for specific memory
        
        Returns:
            Dictionary of statistics
        """
        if memory_id:
            attempts = [a for a in self.attempts if a.memory_id == memory_id]
        else:
            attempts = self.attempts
        
        if not attempts:
            return {
                "total_attempts": 0,
                "success_rate": 0.0,
                "avg_confidence": 0.0,
                "avg_time_ms": 0
            }
        
        successes = sum(1 for a in attempts if a.success)
        total_confidence = sum(a.confidence for a in attempts)
        total_time = sum(a.time_taken_ms for a in attempts)
        
        return {
            "total_attempts": len(attempts),
            "success_rate": successes / len(attempts),
            "avg_confidence": total_confidence / len(attempts),
            "avg_time_ms": total_time // len(attempts)
        }
    
    def _get_success_rate(self, memory_id: str) -> float:
        """Calculate success rate for a memory (last 5 attempts)"""
        recent_attempts = [
            a for a in self.attempts
            if a.memory_id == memory_id
        ][-5:]  # Last 5
        
        if not recent_attempts:
            return 0.5  # Default: unknown
        
        successes = sum(1 for a in recent_attempts if a.success)
        return successes / len(recent_attempts)
    
    def _get_recency_score(self, last_recalled: Optional[str]) -> float:
        """Calculate recency score (0-1, 1 = needs review)"""
        if not last_recalled:
            return 1.0  # Never recalled = needs review
        
        try:
            last_dt = datetime.fromisoformat(last_recalled)
            hours_since = (datetime.utcnow() - last_dt).total_seconds() / 3600
            
            # Spaced repetition intervals (simplified)
            if hours_since < 24:
                return 0.1  # Very recent
            elif hours_since < 72:  # 3 days
                return 0.3
            elif hours_since < 168:  # 1 week
                return 0.6
            else:
                return 1.0  # Old, needs review
        
        except:
            return 0.5  # Default if parse fails
    
    def calculate_next_review(
        self,
        memory: Memory,
        success: bool
    ) -> datetime:
        """
        Calculate next review date using spaced repetition (Ebbinghaus curve)
        
        Args:
            memory: Memory being reviewed
            success: Whether recall was successful
        
        Returns:
            Next review datetime
        """
        # Get current interval
        if memory.next_review:
            try:
                next_review_dt = datetime.fromisoformat(memory.next_review)
                last_recalled_dt = datetime.fromisoformat(memory.last_recalled) if memory.last_recalled else datetime.utcnow()
                current_interval_days = (next_review_dt - last_recalled_dt).days
            except:
                current_interval_days = 1  # Default
        else:
            current_interval_days = 1  # First review
        
        # Calculate new interval based on success
        if success:
            # Success: increase interval (× 2.5)
            new_interval_days = max(1, int(current_interval_days * 2.5))
        else:
            # Failure: decrease interval (× 0.5)
            new_interval_days = max(1, int(current_interval_days * 0.5))
        
        # Cap at 60 days
        new_interval_days = min(new_interval_days, 60)
        
        # Calculate next review date
        return datetime.utcnow() + timedelta(days=new_interval_days)
    
    def get_memories_due(
        self,
        memories: List[Memory]
    ) -> List[Memory]:
        """
        Get memories that are due for review right now
        
        Args:
            memories: All available memories
        
        Returns:
            List of memories due for review (next_review < now)
        """
        now = datetime.utcnow()
        due = []
        
        for memory in memories:
            # Include if never reviewed
            if memory.next_review is None:
                due.append(memory)
                continue
            
            # Include if next_review is in the past
            try:
                next_review_dt = datetime.fromisoformat(memory.next_review)
                if next_review_dt <= now:
                    due.append(memory)
            except:
                # If parse fails, include it
                due.append(memory)
        
        return due
    
    def save(self) -> None:
        """Save challenges and attempts to disk"""
        # Save challenges
        challenges_data = {
            cid: c.to_dict() for cid, c in self.challenges.items()
        }
        
        with open(self.challenges_file, 'w') as f:
            json.dump(challenges_data, f, indent=2)
        
        # Save attempts
        attempts_data = [a.to_dict() for a in self.attempts]
        
        with open(self.attempts_file, 'w') as f:
            json.dump(attempts_data, f, indent=2)
    
    def load(self) -> None:
        """Load challenges and attempts from disk"""
        # Load challenges
        if self.challenges_file.exists():
            try:
                with open(self.challenges_file, 'r') as f:
                    data = json.load(f)
                
                self.challenges = {
                    cid: RecallChallenge(**c)
                    for cid, c in data.items()
                }
            except Exception as e:
                print(f"Warning: Could not load challenges: {e}")
        
        # Load attempts
        if self.attempts_file.exists():
            try:
                with open(self.attempts_file, 'r') as f:
                    data = json.load(f)
                
                self.attempts = [RecallAttempt(**a) for a in data]
            except Exception as e:
                print(f"Warning: Could not load attempts: {e}")
