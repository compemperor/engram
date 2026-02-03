"""
MemoryStore v2 - Enhanced with episodic/semantic, knowledge graphs, and active recall

Backwards compatible with v1 storage format
"""

import json
import hashlib
from dataclasses import asdict
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
from engram.memory.types import Memory, SearchResult, MemoryType, Entity
from engram.memory.graph import KnowledgeGraph
from engram.memory.recall import ActiveRecallSystem


class MemoryStoreV2:
    """
    Enhanced memory store with:
    - Episodic vs Semantic separation
    - Knowledge graphs (relationships)
    - Active recall system
    """
    
    def __init__(
        self,
        path: str = "./memories",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        enable_faiss: bool = True
    ):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        
        # Storage files
        self.lessons_file = self.path / "lessons.jsonl"
        self.index_file = self.path / "memory.faiss"
        self.metadata_file = self.path / "metadata.json"
        
        # Initialize subsystems
        self.embedder = EmbeddingEngine(model_name=embedding_model)
        self.knowledge_graph = KnowledgeGraph(self.path)
        self.recall_system = ActiveRecallSystem(self.path)
        
        # Initialize FAISS
        self.enable_faiss = enable_faiss and FAISS_AVAILABLE
        if self.enable_faiss:
            self._load_or_create_index()
        
        # Load metadata
        self.metadata = self._load_metadata()
    
    def add_lesson(
        self,
        topic: str,
        lesson: str,
        memory_type: str = "semantic",  # "episodic" or "semantic"
        source_quality: Optional[int] = None,
        understanding: Optional[float] = None,
        entities: Optional[List[Dict]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """Add memory with type classification"""
        
        # Generate unique ID for memory
        memory_id = hashlib.md5(
            f"{topic}-{lesson[:50]}-{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Parse entities if provided
        entity_objects = []
        if entities:
            entity_objects = [Entity(**e) for e in entities]
        
        memory = Memory(
            topic=topic,
            lesson=lesson,
            memory_type=MemoryType(memory_type),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            memory_id=memory_id,
            source_quality=source_quality,
            understanding=understanding,
            entities=entity_objects,
            metadata=metadata or {}
        )
        
        # Save to JSONL
        with open(self.lessons_file, "a") as f:
            f.write(json.dumps(memory.to_dict()) + "\n")
        
        # Add to FAISS index
        if self.enable_faiss:
            embedding = self.embedder.encode(lesson)
            embedding_2d = embedding.reshape(1, -1)
            self.index.add(embedding_2d)
            faiss.write_index(self.index, str(self.index_file))
        
        # Update metadata
        self.metadata["total_memories"] = self.metadata.get("total_memories", 0) + 1
        topics_set = set(self.metadata.get("topics", []))
        topics_set.add(topic)
        self.metadata["topics"] = list(topics_set)
        self.metadata["last_updated"] = datetime.now().isoformat()
        self._save_metadata()
        
        return memory
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        min_quality: Optional[int] = None,
        memory_type: Optional[str] = None,  # NEW: filter by type
        topic_filter: Optional[str] = None,
        include_relationships: bool = False  # NEW: include related memories
    ) -> List[SearchResult]:
        """Enhanced search with type filtering and relationships"""
        
        if not self.enable_faiss:
            return []
        
        # Get all memories
        memories = self._load_all_memories()
        
        if not memories:
            return []
        
        # Filter by type if specified
        if memory_type:
            memories = [
                m for m in memories
                if str(m.memory_type.value if hasattr(m.memory_type, 'value') else m.memory_type) == str(memory_type)
            ]
        
        # Filter by quality
        if min_quality:
            memories = [
                m for m in memories
                if m.source_quality and m.source_quality >= min_quality
            ]
        
        # Filter by topic
        if topic_filter:
            memories = [m for m in memories if m.topic == topic_filter]
        
        if not memories:
            return []
        
        # Encode query
        query_embedding = self.embedder.encode(query)
        query_2d = query_embedding.reshape(1, -1)
        
        # Search FAISS
        k = min(top_k * 2, len(memories))  # Get more for filtering
        distances, indices = self.index.search(query_2d, k)
        
        # Build results
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx >= len(memories):
                continue
            
            memory = memories[idx]
            similarity = float(1 / (1 + dist))  # Convert distance to similarity
            
            # Get relationships if requested
            relationships = []
            if include_relationships:
                relationships = self.knowledge_graph.get_related(memory.memory_id)
            
            results.append(SearchResult(
                memory=memory,
                score=similarity,
                relationships=relationships
            ))
        
        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:top_k]
    
    def recall(
        self,
        topic: str,
        min_quality: Optional[int] = None,
        memory_type: Optional[str] = None
    ) -> List[Memory]:
        """Recall all memories for a specific topic"""
        memories = self._load_all_memories()
        
        # Filter by topic
        memories = [m for m in memories if m.topic == topic]
        
        # Filter by quality if specified
        if min_quality:
            memories = [
                m for m in memories
                if m.source_quality and m.source_quality >= min_quality
            ]
        
        # Filter by type if specified
        if memory_type:
            memories = [
                m for m in memories
                if str(m.memory_type.value if hasattr(m.memory_type, 'value') else m.memory_type) == str(memory_type)
            ]
        
        return memories
    
    def get_related_memories(
        self,
        memory_id: str,
        relation_type: Optional[str] = None,
        max_depth: int = 1
    ) -> List[Memory]:
        """Get memories related to this one via knowledge graph"""
        
        # Get connected memory IDs
        if relation_type:
            from engram.memory.types import RelationType
            rel_type = RelationType(relation_type)
        else:
            rel_type = None
        
        connected_ids = self.knowledge_graph.get_connected_memories(
            memory_id,
            relation_type=rel_type,
            max_depth=max_depth
        )
        
        # Load all memories
        all_memories = self._load_all_memories()
        
        # Filter to connected ones
        return [m for m in all_memories if m.memory_id in connected_ids]
    
    def add_relationship(
        self,
        from_id: str,
        to_id: str,
        relation_type: str,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add a relationship between two memories"""
        from engram.memory.types import Relationship, RelationType
        
        # Validate memory IDs exist
        all_memories = self._load_all_memories()
        memory_ids = {m.memory_id for m in all_memories}
        
        if from_id not in memory_ids:
            raise ValueError(f"Memory ID not found: {from_id}")
        if to_id not in memory_ids:
            raise ValueError(f"Memory ID not found: {to_id}")
        
        # Create relationship
        relationship = Relationship(
            from_id=from_id,
            to_id=to_id,
            relation_type=RelationType(relation_type),
            confidence=confidence,
            metadata=metadata
        )
        
        # Add to graph
        self.knowledge_graph.add_relationship(relationship)
        self.knowledge_graph.save()
        
        return relationship.to_dict()
    
    def _load_or_create_index(self):
        """Load or create FAISS index"""
        dimension = 384  # all-MiniLM-L6-v2 dimension
        
        if self.index_file.exists():
            self.index = faiss.read_index(str(self.index_file))
        else:
            self.index = faiss.IndexFlatL2(dimension)
    
    def _load_all_memories(self) -> List[Memory]:
        """Load all memories from JSONL"""
        if not self.lessons_file.exists():
            return []
        
        memories = []
        with open(self.lessons_file, "r") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    
                    # Handle old format (no memory_type)
                    if "memory_type" not in data:
                        data["memory_type"] = "semantic"  # Default for old memories
                    
                    # Ensure memory_type is MemoryType enum
                    if isinstance(data["memory_type"], str):
                        data["memory_type"] = MemoryType(data["memory_type"])
                    
                    if "memory_id" not in data:
                        # Generate ID for old memories
                        data["memory_id"] = hashlib.md5(
                            f"{data['topic']}-{data['lesson'][:50]}".encode()
                        ).hexdigest()[:16]
                    
                    # Parse entities if present
                    if "entities" in data and data["entities"]:
                        data["entities"] = [Entity(**e) for e in data["entities"]]
                    else:
                        data["entities"] = []
                    
                    # Set defaults for recall fields
                    if "recall_count" not in data:
                        data["recall_count"] = 0
                    if "last_recalled" not in data:
                        data["last_recalled"] = None
                    
                    memories.append(Memory(**data))
                except Exception as e:
                    print(f"Warning: Could not parse memory: {e}")
                    continue
        
        return memories
    
    def _load_metadata(self) -> Dict:
        """Load metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Save metadata"""
        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f, indent=2)
    
    def get_stats(self) -> Dict:
        """Get comprehensive statistics"""
        memories = self._load_all_memories()
        
        episodic_count = sum(1 for m in memories if m.memory_type == MemoryType.EPISODIC)
        semantic_count = sum(1 for m in memories if m.memory_type == MemoryType.SEMANTIC)
        
        graph_stats = self.knowledge_graph.get_stats()
        recall_stats = self.recall_system.get_statistics()
        
        return {
            **self.metadata,
            "episodic_memories": episodic_count,
            "semantic_memories": semantic_count,
            "knowledge_graph": graph_stats,
            "recall_stats": recall_stats
        }
