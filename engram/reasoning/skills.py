"""
SkillExtractor - Extract reusable skills from successful trace sequences

Phase 4 of v0.14: Skill library concept from Voyager.
"""

import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime

from engram.memory.types import ReasoningTrace, Skill, TraceOutcome


class SkillExtractor:
    """
    Extracts reusable skills from successful trace sequences.
    
    Based on Voyager's skill library:
    - Skills are temporally extended, interpretable, composable
    - Successful sequences become reusable
    - Compounds agent abilities over time
    """
    
    def __init__(self, reasoning_store=None):
        self.store = reasoning_store
    
    def _generate_skill_id(self, name: str) -> str:
        """Generate unique skill ID"""
        content = f"{name}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def extract_skill_from_session(
        self,
        session_id: str,
        name: str,
        description: str,
        trigger_pattern: str,
        min_success_rate: float = 0.7
    ) -> Optional[Skill]:
        """
        Extract a skill from a successful session.
        
        Only creates skill if session success rate meets threshold.
        """
        if not self.store:
            return None
        
        traces = self.store.get_session_traces(session_id)
        if not traces:
            return None
        
        # Calculate success rate
        successes = sum(1 for t in traces if t.outcome == TraceOutcome.SUCCESS)
        success_rate = successes / len(traces) if traces else 0
        
        if success_rate < min_success_rate:
            return None
        
        # Create skill
        skill = Skill(
            skill_id=self._generate_skill_id(name),
            name=name,
            description=description,
            trigger_pattern=trigger_pattern,
            trace_sequence=[t.trace_id for t in traces],
            success_rate=success_rate,
            created_at=datetime.utcnow().isoformat()
        )
        
        # Store the skill
        self.store.add_skill(skill)
        
        # Update traces with skill_id
        for trace in traces:
            self.store.update_trace(trace.trace_id, skill_id=skill.skill_id)
        
        return skill
    
    def find_skill_for_task(
        self,
        task_description: str,
        min_success_rate: float = 0.5
    ) -> Optional[Skill]:
        """
        Find a skill that matches a task description.
        
        TODO: Implement embedding-based matching.
        For now, uses simple text matching.
        """
        if not self.store:
            return None
        
        skills = self.store.get_skills()
        task_lower = task_description.lower()
        
        for skill in skills:
            if skill.success_rate < min_success_rate:
                continue
            
            # Simple pattern matching
            if skill.trigger_pattern.lower() in task_lower:
                return skill
            
            # Check name and description
            if (task_lower in skill.name.lower() or 
                task_lower in skill.description.lower()):
                return skill
        
        return None
    
    def get_skill_traces(self, skill: Skill) -> List[ReasoningTrace]:
        """Get all traces that form a skill"""
        if not self.store:
            return []
        
        traces = []
        for trace_id in skill.trace_sequence:
            trace = self.store.get_trace(trace_id)
            if trace:
                traces.append(trace)
        
        return traces
    
    def update_skill_usage(self, skill_id: str) -> Optional[Skill]:
        """Update skill usage statistics after it's used"""
        # TODO: Implement skill update in store
        pass
    
    def suggest_skill_extraction(
        self,
        min_traces: int = 5,
        min_success_rate: float = 0.8
    ) -> List[Dict[str, Any]]:
        """
        Suggest sessions that could be extracted as skills.
        
        Returns sessions with high success rates that aren't yet skills.
        """
        if not self.store:
            return []
        
        suggestions = []
        stats = self.store.get_stats()
        
        # Get traces grouped by session
        if not self.store.traces_file.exists():
            return []
        
        import json
        sessions = {}
        with open(self.store.traces_file, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    sid = data.get('session_id')
                    if sid not in sessions:
                        sessions[sid] = {"traces": 0, "successes": 0, "has_skill": False}
                    sessions[sid]["traces"] += 1
                    if data.get('outcome') == 'success':
                        sessions[sid]["successes"] += 1
                    if data.get('skill_id'):
                        sessions[sid]["has_skill"] = True
        
        # Filter and rank
        for session_id, info in sessions.items():
            if info["has_skill"]:
                continue
            if info["traces"] < min_traces:
                continue
            
            success_rate = info["successes"] / info["traces"]
            if success_rate >= min_success_rate:
                suggestions.append({
                    "session_id": session_id,
                    "trace_count": info["traces"],
                    "success_rate": success_rate
                })
        
        # Sort by success rate
        suggestions.sort(key=lambda x: x["success_rate"], reverse=True)
        
        return suggestions[:10]
