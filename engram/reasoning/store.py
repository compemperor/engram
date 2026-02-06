"""
ReasoningStore - Storage and retrieval for reasoning traces

Phase 1 of v0.14: Basic trace storage with JSONL backend.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

from engram.memory.types import (
    ReasoningTrace, TraceAction, ActionType, TraceOutcome, Skill
)


class ReasoningStore:
    """
    Stores and retrieves reasoning traces.
    
    Uses JSONL format for append-only storage, similar to MemoryStore.
    """
    
    def __init__(self, path: str = "./memories"):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        
        # Storage files
        self.traces_file = self.path / "reasoning_traces.jsonl"
        self.skills_file = self.path / "skills.jsonl"
        self.metadata_file = self.path / "reasoning_metadata.json"
        
        # Load metadata
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load or create reasoning metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {
            "total_traces": 0,
            "total_skills": 0,
            "sessions": {},  # session_id -> {trace_count, last_trace}
            "created_at": datetime.utcnow().isoformat()
        }
    
    def _save_metadata(self):
        """Save metadata to file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _generate_trace_id(self, session_id: str, sequence: int) -> str:
        """Generate unique trace ID"""
        content = f"{session_id}:{sequence}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _generate_skill_id(self, name: str) -> str:
        """Generate unique skill ID"""
        content = f"{name}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    # =========================================================================
    # Phase 1: Basic Trace Storage
    # =========================================================================
    
    def add_trace(
        self,
        session_id: str,
        thought: Optional[str] = None,
        action_type: Optional[str] = None,
        action_name: Optional[str] = None,
        action_args: Optional[Dict[str, Any]] = None,
        observation: Optional[str] = None,
        outcome: str = "pending",
        tokens_input: int = 0,
        tokens_output: int = 0,
        duration_ms: int = 0,
        user_feedback: Optional[str] = None
    ) -> ReasoningTrace:
        """
        Add a new reasoning trace.
        
        Returns the created trace with generated ID.
        """
        # Get sequence number for this session
        session_info = self.metadata.get("sessions", {}).get(session_id, {"trace_count": 0})
        sequence = session_info.get("trace_count", 0)
        
        # Generate trace ID
        trace_id = self._generate_trace_id(session_id, sequence)
        
        # Create action if provided
        action = None
        if action_type and action_name:
            action = TraceAction(
                type=ActionType(action_type),
                name=action_name,
                args=action_args or {}
            )
        
        # Create trace
        trace = ReasoningTrace(
            trace_id=trace_id,
            session_id=session_id,
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            sequence=sequence,
            thought=thought,
            action=action,
            observation=observation,
            outcome=TraceOutcome(outcome),
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            duration_ms=duration_ms,
            user_feedback=user_feedback
        )
        
        # Append to JSONL file
        with open(self.traces_file, 'a') as f:
            f.write(json.dumps(trace.to_dict()) + '\n')
        
        # Update metadata
        self.metadata["total_traces"] = self.metadata.get("total_traces", 0) + 1
        if session_id not in self.metadata.get("sessions", {}):
            self.metadata["sessions"] = self.metadata.get("sessions", {})
            self.metadata["sessions"][session_id] = {"trace_count": 0, "first_trace": trace_id}
        self.metadata["sessions"][session_id]["trace_count"] = sequence + 1
        self.metadata["sessions"][session_id]["last_trace"] = trace_id
        self._save_metadata()
        
        return trace
    
    def get_trace(self, trace_id: str) -> Optional[ReasoningTrace]:
        """Get a specific trace by ID"""
        if not self.traces_file.exists():
            return None
        
        with open(self.traces_file, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if data.get('trace_id') == trace_id:
                        return ReasoningTrace.from_dict(data)
        return None
    
    def get_session_traces(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[ReasoningTrace]:
        """Get all traces for a session, ordered by sequence"""
        if not self.traces_file.exists():
            return []
        
        traces = []
        with open(self.traces_file, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if data.get('session_id') == session_id:
                        traces.append(ReasoningTrace.from_dict(data))
        
        # Sort by sequence
        traces.sort(key=lambda t: t.sequence)
        
        if limit:
            traces = traces[:limit]
        
        return traces
    
    def get_recent_traces(
        self,
        limit: int = 50,
        outcome_filter: Optional[str] = None
    ) -> List[ReasoningTrace]:
        """Get most recent traces across all sessions"""
        if not self.traces_file.exists():
            return []
        
        traces = []
        with open(self.traces_file, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if outcome_filter and data.get('outcome') != outcome_filter:
                        continue
                    traces.append(ReasoningTrace.from_dict(data))
        
        # Sort by timestamp descending
        traces.sort(key=lambda t: t.timestamp, reverse=True)
        
        return traces[:limit]
    
    def update_trace(
        self,
        trace_id: str,
        observation: Optional[str] = None,
        outcome: Optional[str] = None,
        user_feedback: Optional[str] = None,
        distilled_pattern: Optional[str] = None,
        skill_id: Optional[str] = None
    ) -> Optional[ReasoningTrace]:
        """
        Update an existing trace (e.g., add observation after action completes).
        
        Rewrites the JSONL file with updated trace.
        """
        if not self.traces_file.exists():
            return None
        
        traces = []
        updated_trace = None
        
        with open(self.traces_file, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if data.get('trace_id') == trace_id:
                        # Update fields
                        if observation is not None:
                            data['observation'] = observation
                        if outcome is not None:
                            data['outcome'] = outcome
                        if user_feedback is not None:
                            data['user_feedback'] = user_feedback
                        if distilled_pattern is not None:
                            data['distilled_pattern'] = distilled_pattern
                        if skill_id is not None:
                            data['skill_id'] = skill_id
                        updated_trace = ReasoningTrace.from_dict(data)
                    traces.append(data)
        
        # Rewrite file
        with open(self.traces_file, 'w') as f:
            for data in traces:
                f.write(json.dumps(data) + '\n')
        
        return updated_trace
    
    def search_traces(
        self,
        query: str,
        limit: int = 10,
        outcome_filter: Optional[str] = None,
        action_type_filter: Optional[str] = None
    ) -> List[ReasoningTrace]:
        """
        Simple text search across traces.
        
        Searches thought, observation, and action name fields.
        TODO: Add embedding-based search in Phase 3.
        """
        if not self.traces_file.exists():
            return []
        
        query_lower = query.lower()
        matches = []
        
        with open(self.traces_file, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    
                    # Apply filters
                    if outcome_filter and data.get('outcome') != outcome_filter:
                        continue
                    if action_type_filter:
                        action = data.get('action')
                        if not action or action.get('type') != action_type_filter:
                            continue
                    
                    # Text search
                    searchable = ' '.join([
                        data.get('thought') or '',
                        data.get('observation') or '',
                        data.get('action', {}).get('name', '') if data.get('action') else ''
                    ]).lower()
                    
                    if query_lower in searchable:
                        matches.append(ReasoningTrace.from_dict(data))
        
        return matches[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get reasoning memory statistics"""
        # Recalculate from actual data
        total_traces = 0
        sessions = {}
        outcomes = {"success": 0, "failure": 0, "partial": 0, "pending": 0}
        action_types = {}
        
        if self.traces_file.exists():
            with open(self.traces_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        total_traces += 1
                        
                        session_id = data.get('session_id')
                        if session_id not in sessions:
                            sessions[session_id] = 0
                        sessions[session_id] += 1
                        
                        outcome = data.get('outcome', 'pending')
                        outcomes[outcome] = outcomes.get(outcome, 0) + 1
                        
                        action = data.get('action')
                        if action:
                            atype = action.get('type', 'unknown')
                            action_types[atype] = action_types.get(atype, 0) + 1
        
        return {
            "total_traces": total_traces,
            "total_sessions": len(sessions),
            "outcomes": outcomes,
            "action_types": action_types,
            "total_skills": self.metadata.get("total_skills", 0)
        }
    
    # =========================================================================
    # Phase 4: Skill Storage (stub for now)
    # =========================================================================
    
    def add_skill(self, skill: Skill) -> Skill:
        """Add a skill to storage"""
        with open(self.skills_file, 'a') as f:
            f.write(json.dumps(skill.to_dict()) + '\n')
        
        self.metadata["total_skills"] = self.metadata.get("total_skills", 0) + 1
        self._save_metadata()
        
        return skill
    
    def get_skills(self, limit: int = 50) -> List[Skill]:
        """Get all skills"""
        if not self.skills_file.exists():
            return []
        
        skills = []
        with open(self.skills_file, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    skills.append(Skill.from_dict(data))
        
        return skills[:limit]
