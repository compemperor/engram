"""
Intent-Aware Retrieval for Engram v0.13.0

Classifies query intent and adjusts retrieval parameters for better results.
Based on SimpleMem research: 26% F1 improvement with intent-aware retrieval.
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Tuple


class QueryIntent(Enum):
    """Types of query intents"""
    FACT_LOOKUP = "fact_lookup"      # Direct question, specific answer expected
    EXPLORATION = "exploration"       # Broad discovery, learning, research
    TEMPORAL = "temporal"             # Time-related queries (recent, history, when)
    PROCEDURAL = "procedural"         # How-to, workflow, rules, steps
    RECALL = "recall"                 # Memory recall, what did I learn about X
    RELATIONSHIP = "relationship"     # Connections, related concepts


@dataclass
class IntentClassification:
    """Result of intent classification"""
    primary_intent: QueryIntent
    confidence: float
    secondary_intent: Optional[QueryIntent] = None
    suggested_params: dict = None
    
    def __post_init__(self):
        if self.suggested_params is None:
            self.suggested_params = {}


class IntentClassifier:
    """
    Classifies query intent using pattern matching and keyword analysis.
    
    Future enhancement: Could use embeddings for semantic intent detection.
    """
    
    # Pattern definitions for each intent type
    INTENT_PATTERNS = {
        QueryIntent.FACT_LOOKUP: [
            r"^what is\b",
            r"^who is\b",
            r"^where is\b",
            r"^define\b",
            r"^tell me about\b",
            r"\bmeaning of\b",
            r"^explain\b",
        ],
        QueryIntent.TEMPORAL: [
            r"\brecent(ly)?\b",
            r"\blast\s+(week|month|day|time)\b",
            r"\bwhen did\b",
            r"\bhistory of\b",
            r"\btimeline\b",
            r"\btoday\b",
            r"\byesterday\b",
            r"\bthis week\b",
            r"\bprevious(ly)?\b",
            r"\blatest\b",
            r"\bnew(est)?\b",
        ],
        QueryIntent.PROCEDURAL: [
            r"^how (do|to|can)\b",
            r"\bsteps to\b",
            r"\bworkflow\b",
            r"\bprocess\b",
            r"\brules? for\b",
            r"\bprocedure\b",
            r"\bchecklist\b",
            r"\brelease cycle\b",
            r"\bbest practice\b",
        ],
        QueryIntent.RECALL: [
            r"\bwhat did (i|we) learn\b",
            r"\bremember\b",
            r"\brecall\b",
            r"\bwhat do (i|you) know\b",
            r"\bprevious(ly)? (learned|discussed|covered)\b",
            r"\bmy (notes|memories|learnings)\b",
        ],
        QueryIntent.RELATIONSHIP: [
            r"\brelated to\b",
            r"\bconnect(ed|ion)?\b",
            r"\bsimilar to\b",
            r"\blike\b",
            r"\bassociat(ed|ion)\b",
            r"\blink(ed|s)?\b",
        ],
        QueryIntent.EXPLORATION: [
            r"\bexplore\b",
            r"\bdiscover\b",
            r"\blearn about\b",
            r"\bresearch\b",
            r"\bfind out\b",
            r"\binvestigate\b",
            r"\bwhat (else|more)\b",
            r"\bbroader\b",
            r"\bdeeper\b",
        ],
    }
    
    # Keywords that boost specific intents
    INTENT_KEYWORDS = {
        QueryIntent.FACT_LOOKUP: ["definition", "meaning", "what", "who", "where"],
        QueryIntent.TEMPORAL: ["recent", "latest", "new", "old", "history", "when", "date", "time"],
        QueryIntent.PROCEDURAL: ["how", "steps", "workflow", "process", "rule", "guide", "tutorial"],
        QueryIntent.RECALL: ["remember", "learned", "know", "recall", "memory"],
        QueryIntent.RELATIONSHIP: ["related", "similar", "connection", "link", "associate"],
        QueryIntent.EXPLORATION: ["explore", "discover", "research", "find", "investigate"],
    }
    
    # Default search parameters for each intent
    INTENT_PARAMS = {
        QueryIntent.FACT_LOOKUP: {
            "top_k": 3,
            "min_quality": 7,
            "use_temporal_weighting": False,  # Facts don't decay
            "auto_expand_context": False,     # Precise results
            "include_dormant": False,
        },
        QueryIntent.EXPLORATION: {
            "top_k": 10,
            "min_quality": 5,
            "use_temporal_weighting": True,
            "auto_expand_context": True,
            "expansion_depth": 2,             # Broader expansion
            "include_dormant": True,          # Include archived memories
        },
        QueryIntent.TEMPORAL: {
            "top_k": 5,
            "min_quality": None,
            "use_temporal_weighting": True,   # Heavy temporal boost
            "auto_expand_context": False,
            "include_dormant": False,
            "_temporal_boost": 2.0,           # Extra boost for recency
        },
        QueryIntent.PROCEDURAL: {
            "top_k": 5,
            "min_quality": 8,                 # High quality for procedures
            "use_temporal_weighting": False,  # Procedures don't decay
            "auto_expand_context": True,
            "expansion_depth": 1,
            "include_dormant": False,
            "_topic_hints": ["workflow", "rules", "startup", "critical"],
        },
        QueryIntent.RECALL: {
            "top_k": 5,
            "min_quality": 6,
            "use_temporal_weighting": True,
            "auto_expand_context": True,
            "expansion_depth": 1,
            "include_dormant": False,
        },
        QueryIntent.RELATIONSHIP: {
            "top_k": 7,
            "min_quality": 5,
            "use_temporal_weighting": True,
            "auto_expand_context": True,
            "expansion_depth": 2,             # Deep relationship expansion
            "include_dormant": True,
        },
    }
    
    def classify(self, query: str) -> IntentClassification:
        """
        Classify the intent of a search query.
        
        Returns IntentClassification with primary intent, confidence, and suggested params.
        """
        query_lower = query.lower().strip()
        
        # Score each intent
        scores = {intent: 0.0 for intent in QueryIntent}
        
        # Pattern matching (highest weight)
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    scores[intent] += 3.0
        
        # Keyword matching (medium weight)
        query_words = set(query_lower.split())
        for intent, keywords in self.INTENT_KEYWORDS.items():
            matches = query_words.intersection(set(keywords))
            scores[intent] += len(matches) * 1.0
        
        # Query length heuristics
        word_count = len(query_lower.split())
        if word_count <= 3:
            # Short queries tend to be fact lookups
            scores[QueryIntent.FACT_LOOKUP] += 0.5
        elif word_count >= 8:
            # Longer queries tend to be exploration
            scores[QueryIntent.EXPLORATION] += 0.5
        
        # Question word detection
        if query_lower.startswith(("how", "why")):
            scores[QueryIntent.PROCEDURAL] += 1.0
        elif query_lower.startswith(("what", "who", "where")):
            scores[QueryIntent.FACT_LOOKUP] += 1.0
        elif query_lower.startswith("when"):
            scores[QueryIntent.TEMPORAL] += 2.0
        
        # Get primary and secondary intents
        sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary_intent = sorted_intents[0][0]
        primary_score = sorted_intents[0][1]
        
        secondary_intent = None
        if len(sorted_intents) > 1 and sorted_intents[1][1] > 0:
            secondary_intent = sorted_intents[1][0]
        
        # Calculate confidence (normalize to 0-1)
        max_possible_score = 10.0  # Approximate max
        confidence = min(primary_score / max_possible_score, 1.0)
        
        # Default to fact_lookup if no strong signal
        if primary_score == 0:
            primary_intent = QueryIntent.FACT_LOOKUP
            confidence = 0.3
        
        # Get suggested parameters
        suggested_params = self.INTENT_PARAMS.get(primary_intent, {}).copy()
        
        # Merge secondary intent params with lower weight
        if secondary_intent and confidence < 0.7:
            secondary_params = self.INTENT_PARAMS.get(secondary_intent, {})
            for key, value in secondary_params.items():
                if key not in suggested_params:
                    suggested_params[key] = value
        
        return IntentClassification(
            primary_intent=primary_intent,
            confidence=confidence,
            secondary_intent=secondary_intent,
            suggested_params=suggested_params
        )
    
    def get_adjusted_params(
        self,
        query: str,
        user_params: dict
    ) -> Tuple[dict, IntentClassification]:
        """
        Classify query and return adjusted search parameters.
        
        User-specified params take precedence over intent-suggested params.
        
        Returns: (adjusted_params, classification)
        """
        classification = self.classify(query)
        
        # Start with intent-suggested params
        adjusted = classification.suggested_params.copy()
        
        # User params override intent params
        for key, value in user_params.items():
            if value is not None:  # Only override if explicitly set
                adjusted[key] = value
        
        return adjusted, classification


# Singleton for easy access
_classifier = None

def get_intent_classifier() -> IntentClassifier:
    """Get or create the intent classifier singleton."""
    global _classifier
    if _classifier is None:
        _classifier = IntentClassifier()
    return _classifier


def classify_query(query: str) -> IntentClassification:
    """Convenience function to classify a query."""
    return get_intent_classifier().classify(query)
