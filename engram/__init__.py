"""
Engram - Memory traces for AI agents

Self-improving memory system with quality control, drift detection,
and learning framework.
"""

__version__ = "0.11.3"
__author__ = "compemperor, Clawdy"
__license__ = "Apache 2.0"

from engram.memory.store import MemoryStore
from engram.mirror.evaluator import MirrorEvaluator
from engram.learning.session import LearningSession

__all__ = [
    "MemoryStore",
    "MirrorEvaluator", 
    "LearningSession",
]
