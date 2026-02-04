"""
MemoryStore - Enhanced with episodic/semantic, knowledge graphs, and active recall

Main memory storage and retrieval system for Engram.
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
from engram.memory.types import Memory, SearchResult, MemoryType, MemoryStatus, Entity
from engram.memory.graph import KnowledgeGraph
from engram.memory.recall import ActiveRecallSystem
from engram.memory.fade import (
    calculate_strength, should_include_in_search, boost_on_access,
    get_fade_metrics, find_consolidation_candidates, DORMANT_THRESHOLD
)


class MemoryStore:
    """
    Enhanced memory store with:
    - Episodic vs Semantic separation
    - Knowledge graphs (relationships)
    - Active recall system
    """
    
    def __init__(
        self,
        path: str = "./memories",
        embedding_model: str = "intfloat/e5-base-v2",  # v0.5.0: Upgraded from all-MiniLM-L6-v2 for better semantic search
        enable_faiss: bool = True,
        auto_link_threshold: float = 0.75,
        auto_link_max: int = 3
    ):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        
        # Storage files
        self.lessons_file = self.path / "lessons.jsonl"
        self.index_file = self.path / "memory.faiss"
        self.metadata_file = self.path / "metadata.json"
        
        # Auto-linking config
        self.auto_link_threshold = auto_link_threshold
        self.auto_link_max = auto_link_max
        
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
            embedding = self.embedder.encode(lesson, is_query=False)  # Document/passage
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
    
    def update_memory(self, memory: Memory) -> None:
        """
        Update an existing memory in storage
        
        Args:
            memory: Updated memory object
        """
        # Load all memories
        memories = self._load_all_memories()
        
        # Find and replace the memory
        updated = False
        for i, m in enumerate(memories):
            if m.memory_id == memory.memory_id:
                memories[i] = memory
                updated = True
                break
        
        if not updated:
            raise ValueError(f"Memory {memory.memory_id} not found")
        
        # Rewrite JSONL file
        with open(self.lessons_file, "w") as f:
            for m in memories:
                f.write(json.dumps(m.to_dict()) + "\n")
    
    # v0.6.0: Fading system methods
    def _boost_memory_access(self, memory_id: str) -> None:
        """Boost a memory's access count and timestamp when retrieved."""
        all_memories = self._load_all_memories()
        updated = False
        
        for memory in all_memories:
            if memory.memory_id == memory_id:
                memory.access_count = getattr(memory, 'access_count', 0) + 1
                memory.last_accessed = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
                updated = True
                break
        
        if updated:
            self._save_all_memories(all_memories)
    
    def get_memory_strength(self, memory_id: str) -> Optional[float]:
        """Get the current strength of a memory after decay."""
        all_memories = self._load_all_memories()
        for memory in all_memories:
            if memory.memory_id == memory_id:
                return calculate_strength(memory)
        return None
    
    def get_fade_status(self) -> Dict[str, Any]:
        """Get fading status across all memories."""
        all_memories = self._load_all_memories()
        
        active = []
        fading = []
        dormant = []
        
        for memory in all_memories:
            metrics = get_fade_metrics(memory)
            entry = {
                "memory_id": memory.memory_id,
                "topic": memory.topic,
                "strength": metrics.strength,
                "days_since_access": metrics.days_since_access,
                "action": metrics.recommended_action
            }
            
            if metrics.is_dormant:
                dormant.append(entry)
            elif metrics.strength < 0.5:
                fading.append(entry)
            else:
                active.append(entry)
        
        return {
            "total": len(all_memories),
            "active_count": len(active),
            "fading_count": len(fading),
            "dormant_count": len(dormant),
            "dormant_threshold": DORMANT_THRESHOLD,
            "active": active[:10],  # Sample
            "fading": fading[:10],
            "dormant": dormant[:10]
        }
    
    def apply_fade_cycle(self) -> Dict[str, Any]:
        """
        Run a fade cycle: update memory statuses based on current strength.
        
        This should be called periodically (e.g., daily) to update statuses.
        """
        all_memories = self._load_all_memories()
        
        newly_dormant = []
        reactivated = []
        
        for memory in all_memories:
            metrics = get_fade_metrics(memory)
            current_status = getattr(memory, 'status', MemoryStatus.ACTIVE)
            
            # Handle string status from JSON
            if isinstance(current_status, str):
                current_status = MemoryStatus(current_status) if current_status in ['active', 'dormant', 'consolidated'] else MemoryStatus.ACTIVE
            
            if metrics.is_dormant and current_status == MemoryStatus.ACTIVE:
                memory.status = MemoryStatus.DORMANT
                newly_dormant.append(memory.memory_id)
            elif not metrics.is_dormant and current_status == MemoryStatus.DORMANT:
                memory.status = MemoryStatus.ACTIVE
                reactivated.append(memory.memory_id)
        
        if newly_dormant or reactivated:
            self._save_all_memories(all_memories)
        
        return {
            "newly_dormant": newly_dormant,
            "reactivated": reactivated,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _calculate_temporal_score(
        self,
        memory: Memory,
        base_similarity: float,
        recency_weight: float = 0.3,
        quality_weight: float = 0.2
    ) -> float:
        """
        Calculate temporal-weighted score combining:
        - Base similarity (semantic match)
        - Recency (newer = higher)
        - Quality (source_quality boost)
        
        Formula: score = similarity * (1 + recency_factor + quality_factor)
        """
        # Parse timestamp
        try:
            timestamp = datetime.strptime(memory.timestamp, "%Y-%m-%d %H:%M")
            days_ago = (datetime.now() - timestamp).days
            
            # Exponential decay: newer memories get higher boost
            # Max boost at day 0: recency_weight
            # Half-life: 30 days
            recency_factor = recency_weight * (0.5 ** (days_ago / 30.0))
        except:
            recency_factor = 0.0
        
        # Quality boost (normalized to 0-1, then scaled)
        if memory.source_quality:
            quality_factor = quality_weight * (memory.source_quality / 10.0)
        else:
            quality_factor = 0.0
        
        # Combined score
        final_score = base_similarity * (1.0 + recency_factor + quality_factor)
        
        return final_score
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        min_quality: Optional[int] = None,
        memory_type: Optional[str] = None,  # Filter by type
        topic_filter: Optional[str] = None,
        include_relationships: bool = False,  # Include related memories
        use_temporal_weighting: bool = True,  # NEW: temporal weighting
        auto_expand_context: bool = True,  # NEW: auto-expand related memories (v0.4.1: enabled by default)
        expansion_depth: int = 1,  # NEW: how deep to expand
        include_dormant: bool = False  # v0.6.0: include dormant memories
    ) -> List[SearchResult]:
        """
        Enhanced search with:
        - Type filtering
        - Temporal weighting (recency + importance)
        - Context-aware retrieval (auto-expand related memories)
        """
        
        if not self.enable_faiss:
            return []
        
        # Get all memories (don't filter yet - FAISS indices must match)
        all_memories = self._load_all_memories()
        
        if not all_memories:
            return []
        
        # Encode query
        query_embedding = self.embedder.encode(query, is_query=True)  # Query prefix for E5
        query_2d = query_embedding.reshape(1, -1)
        
        # Search FAISS (search ALL, then filter)
        k = min(top_k * 5, len(all_memories))  # Get more candidates for filtering
        distances, indices = self.index.search(query_2d, k)
        
        # Build results with temporal weighting
        results = []
        seen_ids = set()  # Track unique memories
        
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx >= len(all_memories):
                continue
            
            memory = all_memories[idx]
            
            # Apply filters AFTER retrieval
            if memory_type:
                mem_type_str = str(memory.memory_type.value if hasattr(memory.memory_type, 'value') else memory.memory_type)
                if mem_type_str != str(memory_type):
                    continue
            
            if min_quality and (not memory.source_quality or memory.source_quality < min_quality):
                continue
            
            if topic_filter and memory.topic != topic_filter:
                continue
            
            # v0.6.0: Filter dormant memories unless explicitly requested
            if not include_dormant and not should_include_in_search(memory, include_dormant):
                continue
            
            if memory.memory_id in seen_ids:
                continue
            seen_ids.add(memory.memory_id)
            
            # v0.6.0: Boost memory on access (updates access_count and last_accessed)
            self._boost_memory_access(memory.memory_id)
            
            # Base similarity score
            base_similarity = float(1 / (1 + dist))
            
            # Apply temporal weighting if enabled
            if use_temporal_weighting:
                score = self._calculate_temporal_score(memory, base_similarity)
            else:
                score = base_similarity
            
            # Get relationships if requested
            relationships = []
            if include_relationships:
                relationships = self.knowledge_graph.get_related(memory.memory_id)
            
            results.append(SearchResult(
                memory=memory,
                score=score,
                relationships=relationships
            ))
            
            # Stop once we have enough filtered results
            if len(results) >= top_k:
                break
        
        # Sort by final score (temporal-weighted or base)
        results.sort(key=lambda x: x.score, reverse=True)
        
        # Take top K
        top_results = results[:top_k]
        
        # Context-aware expansion: auto-include related memories
        if auto_expand_context and top_results:
            expanded_results = []
            expansion_seen_ids = set()  # Separate tracking for expansion to avoid blocking related memories
            all_memories_dict = {m.memory_id: m for m in all_memories}
            
            for result in top_results:
                # Add the primary result
                expanded_results.append(result)
                expansion_seen_ids.add(result.memory.memory_id)
                
                # Get related memories through knowledge graph
                related_ids = self.knowledge_graph.get_connected_memories(
                    result.memory.memory_id,
                    max_depth=expansion_depth
                )
                
                # Add related memories as lower-scored results
                for related_id in related_ids:
                    if related_id not in expansion_seen_ids and related_id in all_memories_dict:
                        related_memory = all_memories_dict[related_id]
                        expansion_seen_ids.add(related_id)
                        
                        # Related memories get 70% of the parent's score
                        related_score = result.score * 0.7
                        
                        relationships = self.knowledge_graph.get_related(related_id)
                        
                        expanded_results.append(SearchResult(
                            memory=related_memory,
                            score=related_score,
                            relationships=relationships
                        ))
            
            return expanded_results
        
        return top_results
    
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
        dimension = self.embedder.dimension  # Get dimension from model
        
        if self.index_file.exists():
            try:
                self.index = faiss.read_index(str(self.index_file))
                # Verify dimension matches
                if self.index.d != dimension:
                    print(f"⚠️  FAISS index dimension mismatch: {self.index.d} != {dimension}")
                    print("   Rebuilding index with correct dimensions...")
                    self.index = faiss.IndexFlatL2(dimension)
                    self._rebuild_index()
            except Exception as e:
                print(f"⚠️  Error loading FAISS index: {e}")
                print("   Creating new index...")
                self.index = faiss.IndexFlatL2(dimension)
        else:
            self.index = faiss.IndexFlatL2(dimension)
    
    def _rebuild_index(self):
        """Rebuild FAISS index from JSONL memories"""
        memories = self._load_all_memories()
        print(f"   Re-embedding {len(memories)} memories...")
        
        for i, memory in enumerate(memories):
            if i % 10 == 0 and i > 0:
                print(f"   Progress: {i}/{len(memories)}")
            
            embedding = self.embedder.encode(memory.lesson, is_query=False)
            embedding_2d = embedding.reshape(1, -1)
            self.index.add(embedding_2d)
        
        # Save rebuilt index
        faiss.write_index(self.index, str(self.index_file))
        print(f"✓ Index rebuilt: {len(memories)} memories indexed")
    
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
                    if "next_review" not in data:
                        data["next_review"] = None
                    if "review_success_rate" not in data:
                        data["review_success_rate"] = 0.0
                    
                    # v0.6.0: Set defaults for fade fields
                    if "access_count" not in data:
                        data["access_count"] = 0
                    if "last_accessed" not in data:
                        data["last_accessed"] = None
                    if "status" not in data:
                        data["status"] = MemoryStatus.ACTIVE
                    elif isinstance(data["status"], str):
                        # Convert string to enum
                        data["status"] = MemoryStatus(data["status"]) if data["status"] in ['active', 'dormant', 'consolidated'] else MemoryStatus.ACTIVE
                    
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
