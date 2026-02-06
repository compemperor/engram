"""
TraceDistiller - Extract patterns from reasoning traces

Phase 3 of v0.14: Distillation of raw traces into reusable patterns.
Based on ReasoningBank's distillation approach.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from engram.memory.types import ReasoningTrace, TraceOutcome


class TraceDistiller:
    """
    Distills reasoning traces into high-level patterns.
    
    Key concepts from ReasoningBank:
    - Learn from both success AND failure
    - Failures close to success (hard negatives) are most valuable
    - Distilled patterns are more generalizable than raw traces
    """
    
    def __init__(self, reasoning_store=None):
        self.store = reasoning_store
    
    def distill_session(
        self,
        session_id: str,
        min_traces: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Distill a session's traces into a pattern.
        
        Returns a pattern dict with:
        - summary: High-level description
        - key_decisions: Important decision points
        - success_factors: What led to success
        - failure_factors: What led to failure
        - lesson: Generalized insight
        """
        if not self.store:
            return None
        
        traces = self.store.get_session_traces(session_id)
        if len(traces) < min_traces:
            return None
        
        # Analyze outcome distribution
        outcomes = {"success": 0, "failure": 0, "partial": 0}
        for t in traces:
            outcomes[t.outcome.value] = outcomes.get(t.outcome.value, 0) + 1
        
        # Determine overall session outcome
        if outcomes["success"] > outcomes["failure"]:
            session_outcome = "success"
        elif outcomes["failure"] > outcomes["success"]:
            session_outcome = "failure"
        else:
            session_outcome = "mixed"
        
        # Extract key actions
        tool_calls = [t for t in traces if t.action and t.action.type.value == "tool_call"]
        decisions = [t for t in traces if t.action and t.action.type.value == "decision"]
        
        # Build pattern
        pattern = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "trace_count": len(traces),
            "session_outcome": session_outcome,
            "outcomes": outcomes,
            "tool_calls": [
                {"name": t.action.name, "outcome": t.outcome.value}
                for t in tool_calls
            ],
            "key_decisions": [
                {"thought": t.thought, "outcome": t.outcome.value}
                for t in decisions[:5]  # Limit to top 5
            ],
            "summary": self._generate_summary(traces, session_outcome),
            "lesson": self._extract_lesson(traces, session_outcome)
        }
        
        return pattern
    
    def _generate_summary(
        self,
        traces: List[ReasoningTrace],
        outcome: str
    ) -> str:
        """Generate a summary of the session"""
        tool_names = set()
        for t in traces:
            if t.action and t.action.name:
                tool_names.add(t.action.name)
        
        return f"Session with {len(traces)} steps, {len(tool_names)} unique tools, outcome: {outcome}"
    
    def _extract_lesson(
        self,
        traces: List[ReasoningTrace],
        outcome: str
    ) -> str:
        """Extract a generalized lesson from the session"""
        # Find the last trace with an observation (usually the conclusion)
        for t in reversed(traces):
            if t.observation and t.outcome.value in ["success", "failure"]:
                if t.outcome.value == "success":
                    return f"Successful approach: {t.observation[:200]}"
                else:
                    return f"Failed approach - avoid: {t.observation[:200]}"
        
        return f"Session completed with {outcome} outcome"
    
    def find_similar_patterns(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find patterns similar to a query.
        
        TODO: Implement embedding-based similarity search.
        For now, returns empty list (stub for Phase 3).
        """
        return []
    
    def distill_failure_to_hard_negative(
        self,
        trace: ReasoningTrace
    ) -> Optional[Dict[str, Any]]:
        """
        Convert a failure trace into a hard negative example.
        
        Hard negatives are failures that are close to success -
        they help sharpen decision boundaries.
        
        Based on "Co-Evolving Agents" research.
        """
        if trace.outcome != TraceOutcome.FAILURE:
            return None
        
        return {
            "trace_id": trace.trace_id,
            "type": "hard_negative",
            "what_failed": trace.observation,
            "context": trace.thought,
            "suggested_fix": None,  # Could be filled by LLM analysis
            "timestamp": datetime.utcnow().isoformat()
        }
