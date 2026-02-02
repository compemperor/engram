"""
MemoryStore - Core memory storage and retrieval system

Handles:
- Episodic memory storage (topic + lesson + metadata)
- Semantic search via FAISS + embeddings
- Quality filtering
- Statistics tracking
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from engram.memory.embeddings import EmbeddingEngine


@dataclass
class Memory:
    """Single memory entry"""
    topic: str
    lesson: str
    timestamp: str
    source_quality: Optional[int] = None  # 1-10 scale
    understanding: Optional[float] = None  # 1-5 scale
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SearchResult:
    """Search result with score"""
    memory: Memory
    score: float  # Similarity score (0-1, higher = better)


class MemoryStore:
    """
    Main memory storage and retrieval system.
    
    Features:
    - Local embeddings (all-MiniLM-L6-v2)
    - FAISS vector search
    - Quality filtering
    - Topic-based recall
    """
    
    def __init__(
        self,
        path: str = "./memories",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        enable_faiss: bool = True
    ):
        """
        Initialize memory store.
        
        Args:
            path: Directory for memory storage
            embedding_model: Sentence-transformers model name
            enable_faiss: Use FAISS for vector search (requires faiss-cpu)
        """
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        
        self.lessons_file = self.path / "lessons.jsonl"
        self.index_file = self.path / "memory.faiss"
        self.metadata_file = self.path / "metadata.json"
        
        # Initialize embedding engine
        self.embedder = EmbeddingEngine(model_name=embedding_model)
        
        # Initialize FAISS if available
        self.enable_faiss = enable_faiss and FAISS_AVAILABLE
        if self.enable_faiss:
            self._load_or_create_index()
        
        # Load metadata
        self.metadata = self._load_metadata()
    
    def add_lesson(
        self,
        topic: str,
        lesson: str,
        source_quality: Optional[int] = None,
        understanding: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """
        Add a new lesson/memory.
        
        Args:
            topic: Topic category
            lesson: The actual learning/lesson
            source_quality: Quality score 1-10 (optional)
            understanding: Understanding score 1-5 (optional)
            metadata: Additional metadata (optional)
        
        Returns:
            Memory object
        """
        memory = Memory(
            topic=topic,
            lesson=lesson,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            source_quality=source_quality,
            understanding=understanding,
            metadata=metadata or {}
        )
        
        # Append to JSONL
        with open(self.lessons_file, "a") as f:
            f.write(json.dumps(memory.to_dict()) + "\n")
        
        # Add to FAISS index if enabled
        if self.enable_faiss:
            embedding = self.embedder.encode(lesson)
            # Reshape for FAISS
            embedding_2d = embedding.reshape(1, -1)
            self.index.add(embedding_2d)
            
            # Save index
            faiss.write_index(self.index, str(self.index_file))
        
        # Update metadata
        self.metadata["total_memories"] = self.metadata.get("total_memories", 0) + 1
        self.metadata["topics"] = list(set(self.metadata.get("topics", []) + [topic]))
        self.metadata["last_updated"] = datetime.now().isoformat()
        self._save_metadata()
        
        return memory
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        min_quality: Optional[int] = None,
        topic_filter: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Semantic search across memories.
        
        Args:
            query: Search query
            top_k: Number of results to return
            min_quality: Minimum source quality (1-10)
            topic_filter: Filter by specific topic
        
        Returns:
            List of SearchResult objects
        """
        if not self.enable_faiss:
            # Fallback to text matching if FAISS not available
            return self._search_text(query, top_k, min_quality, topic_filter)
        
        # Encode query
        query_embedding = self.embedder.encode(query).reshape(1, -1)
        
        # Search FAISS
        distances, indices = self.index.search(query_embedding, top_k * 2)  # Get extra for filtering
        
        # Load all memories
        memories = list(self._iter_memories())
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= len(memories):
                continue
                
            memory = memories[idx]
            
            # Apply filters
            if min_quality and (memory.source_quality is None or memory.source_quality < min_quality):
                continue
            if topic_filter and memory.topic != topic_filter:
                continue
            
            # Convert distance to similarity score (0-1, higher = better)
            # FAISS L2 distance: lower = more similar
            # Convert to similarity: 1 / (1 + distance)
            score = 1.0 / (1.0 + dist)
            
            results.append(SearchResult(memory=memory, score=score))
            
            if len(results) >= top_k:
                break
        
        return results
    
    def recall(
        self,
        topic: str,
        min_quality: Optional[int] = None
    ) -> List[Memory]:
        """
        Recall all memories for a specific topic.
        
        Args:
            topic: Topic to recall
            min_quality: Minimum source quality filter
        
        Returns:
            List of Memory objects
        """
        memories = []
        for memory in self._iter_memories():
            if memory.topic == topic:
                if min_quality is None or (memory.source_quality and memory.source_quality >= min_quality):
                    memories.append(memory)
        return memories
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            "total_memories": self.metadata.get("total_memories", 0),
            "topics": self.metadata.get("topics", []),
            "last_updated": self.metadata.get("last_updated"),
            "faiss_enabled": self.enable_faiss,
            "embedding_model": self.embedder.model_name
        }
    
    def rebuild_index(self):
        """Rebuild FAISS index from scratch"""
        if not self.enable_faiss:
            raise RuntimeError("FAISS not enabled")
        
        print("Rebuilding FAISS index...")
        
        # Load all memories
        memories = list(self._iter_memories())
        
        if not memories:
            print("No memories to index")
            return
        
        # Encode all lessons
        lessons = [m.lesson for m in memories]
        embeddings = []
        
        for lesson in lessons:
            emb = self.embedder.encode(lesson)
            embeddings.append(emb)
        
        embeddings = np.array(embeddings)
        
        # Create new index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)
        
        # Save
        faiss.write_index(self.index, str(self.index_file))
        
        print(f"✓ Indexed {len(memories)} memories")
    
    # Private methods
    
    def _iter_memories(self):
        """Iterate over all memories in JSONL file"""
        if not self.lessons_file.exists():
            return
        
        with open(self.lessons_file, "r") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    yield Memory(**data)
    
    def _search_text(
        self,
        query: str,
        top_k: int,
        min_quality: Optional[int],
        topic_filter: Optional[str]
    ) -> List[SearchResult]:
        """Fallback text-based search (when FAISS not available)"""
        query_lower = query.lower()
        results = []
        
        for memory in self._iter_memories():
            # Apply filters
            if min_quality and (memory.source_quality is None or memory.source_quality < min_quality):
                continue
            if topic_filter and memory.topic != topic_filter:
                continue
            
            # Simple text matching
            lesson_lower = memory.lesson.lower()
            if query_lower in lesson_lower:
                # Score based on position and length
                pos = lesson_lower.index(query_lower)
                score = 1.0 / (1.0 + pos / len(lesson_lower))
                results.append(SearchResult(memory=memory, score=score))
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def _load_or_create_index(self):
        """Load existing FAISS index or create new one"""
        if self.index_file.exists():
            self.index = faiss.read_index(str(self.index_file))
        else:
            # Create empty index (will be populated when memories are added)
            dimension = 384  # all-MiniLM-L6-v2 dimension
            self.index = faiss.IndexFlatL2(dimension)
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata file"""
        if self.metadata_file.exists():
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Save metadata file"""
        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f, indent=2)
