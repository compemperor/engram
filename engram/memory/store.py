"""
MemoryStore - Enhanced with episodic/semantic, knowledge graphs, and active recall

Main memory storage and retrieval system for Engram.
"""

import json
import hashlib
from dataclasses import asdict
from datetime import datetime, timedelta
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
from engram.memory.scheduler import MemoryScheduler
from engram.memory.intent import get_intent_classifier, IntentClassification, QueryIntent


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
        auto_link_max: int = 3,
        # v0.6.1: Sleep scheduler settings
        enable_sleep_scheduler: bool = True,
        sleep_interval_hours: float = 24.0,
        sleep_start_delay_minutes: float = 5.0
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
        
        # v0.6.1: Initialize sleep scheduler (background fade cycles)
        # v0.7.1: Added auto-reflection during sleep
        # v0.8.1: Added auto quality assessment during sleep
        # v0.10.0: Added compression and replay during sleep
        self.scheduler: Optional[MemoryScheduler] = None
        if enable_sleep_scheduler:
            self.scheduler = MemoryScheduler(
                fade_callback=self.apply_fade_cycle,
                interval_hours=sleep_interval_hours,
                start_delay_minutes=sleep_start_delay_minutes,
                # v0.7.1: Auto-reflection callbacks
                reflect_callback=self.reflect,
                get_reflection_candidates_callback=self.get_reflection_candidates,
                enable_auto_reflect=True,
                reflect_min_memories=5,
                reflect_min_days_since_last=7,
                # v0.8.1: Auto quality assessment callbacks
                quality_assess_callback=self.assess_quality,
                quality_apply_callback=self.apply_quality_adjustments,
                enable_auto_quality=True,
                quality_assess_limit=15,
                quality_min_confidence=0.8,
                # v0.10.0: Compression and replay callbacks
                compression_candidates_callback=self.find_compression_candidates,
                compression_apply_callback=self.compress_memories,
                replay_callback=self.replay_memories,
                enable_compression=True,
                enable_replay=True,
                compression_limit=5,
                replay_limit=20
            )
            self.scheduler.start()
    
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
    
    def _save_all_memories(self, memories: List[Memory]) -> None:
        """Save all memories to JSONL file."""
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
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get the sleep scheduler status."""
        if self.scheduler is None:
            return {"enabled": False, "status": "disabled"}
        
        status = self.scheduler.get_status()
        return {"enabled": True, **status}
    
    def shutdown(self) -> None:
        """Shutdown the memory store gracefully (stops scheduler)."""
        if self.scheduler:
            self.scheduler.stop()
    
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
        include_dormant: bool = False,  # v0.6.0: include dormant memories
        intent_aware: bool = True  # v0.13.0: intent-aware retrieval
    ) -> tuple[List[SearchResult], Optional[IntentClassification]]:
        """
        Enhanced search with:
        - Type filtering
        - Temporal weighting (recency + importance)
        - Context-aware retrieval (auto-expand related memories)
        - Intent-aware retrieval (v0.13.0): classifies query intent and adjusts params
        
        Returns: (results, intent_classification) where classification is None if intent_aware=False
        """
        intent_classification = None
        
        # v0.13.0: Intent-aware parameter adjustment
        if intent_aware:
            classifier = get_intent_classifier()
            user_params = {
                'top_k': top_k if top_k != 5 else None,  # Only if user changed from default
                'min_quality': min_quality,
                'use_temporal_weighting': use_temporal_weighting if not use_temporal_weighting else None,
                'auto_expand_context': auto_expand_context if not auto_expand_context else None,
                'expansion_depth': expansion_depth if expansion_depth != 1 else None,
                'include_dormant': include_dormant if include_dormant else None,
            }
            adjusted_params, intent_classification = classifier.get_adjusted_params(query, user_params)
            
            # Apply adjusted params (only if not explicitly set by user)
            if top_k == 5 and 'top_k' in adjusted_params:
                top_k = adjusted_params['top_k']
            if min_quality is None and 'min_quality' in adjusted_params:
                min_quality = adjusted_params.get('min_quality')
            if use_temporal_weighting and 'use_temporal_weighting' in adjusted_params:
                use_temporal_weighting = adjusted_params['use_temporal_weighting']
            if auto_expand_context and 'auto_expand_context' in adjusted_params:
                auto_expand_context = adjusted_params['auto_expand_context']
            if expansion_depth == 1 and 'expansion_depth' in adjusted_params:
                expansion_depth = adjusted_params['expansion_depth']
            if not include_dormant and 'include_dormant' in adjusted_params:
                include_dormant = adjusted_params['include_dormant']
        
        if not self.enable_faiss:
            return [], intent_classification
        
        # Get all memories (don't filter yet - FAISS indices must match)
        all_memories = self._load_all_memories()
        
        if not all_memories:
            return [], intent_classification
        
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
            
            return expanded_results, intent_classification
        
        return top_results, intent_classification
    
    def recall(
        self,
        topic: str,
        min_quality: Optional[int] = None,
        memory_type: Optional[str] = None,
        include_archived: bool = False
    ) -> List[Memory]:
        """Recall all memories for a specific topic"""
        memories = self._load_all_memories()
        
        # Filter out archived (dormant) memories unless explicitly requested
        if not include_archived:
            memories = [
                m for m in memories
                if getattr(m, 'status', MemoryStatus.ACTIVE) != MemoryStatus.DORMANT
                and str(getattr(m, 'status', 'active')) != 'dormant'
            ]
        
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
        
        # Calculate actual counts from loaded memories (not metadata)
        total_count = len(memories)
        episodic_count = sum(1 for m in memories if m.memory_type == MemoryType.EPISODIC)
        semantic_count = sum(1 for m in memories if m.memory_type == MemoryType.SEMANTIC)
        reflection_count = sum(1 for m in memories if m.memory_type == MemoryType.REFLECTION)
        actual_topics = list(set(m.topic for m in memories))
        
        graph_stats = self.knowledge_graph.get_stats()
        recall_stats = self.recall_system.get_statistics()
        
        # Return actual counts, not metadata (which can drift)
        return {
            "total_memories": total_count,
            "topics": actual_topics,
            "last_updated": self.metadata.get("last_updated"),
            "episodic_memories": episodic_count,
            "semantic_memories": semantic_count,
            "reflection_memories": reflection_count,
            "knowledge_graph": graph_stats,
            "recall_stats": recall_stats
        }
    
    def sync_metadata(self) -> Dict:
        """
        Recalculate and sync metadata with actual memory state.
        Fixes drift between metadata counts and actual stored memories.
        
        Returns:
            Dict with before/after counts
        """
        memories = self._load_all_memories()
        
        before = {
            "total": self.metadata.get("total_memories", 0),
            "topics": len(self.metadata.get("topics", []))
        }
        
        # Recalculate from actual data
        actual_topics = list(set(m.topic for m in memories))
        
        self.metadata["total_memories"] = len(memories)
        self.metadata["topics"] = actual_topics
        self.metadata["last_updated"] = datetime.now().isoformat()
        self._save_metadata()
        
        after = {
            "total": len(memories),
            "topics": len(actual_topics)
        }
        
        return {"before": before, "after": after, "synced": True}
    
    def archive_memory(self, memory_id: str) -> Dict:
        """
        Archive a memory by setting its status to DORMANT.
        Archived memories are excluded from searches but remain in storage.
        
        Args:
            memory_id: ID of the memory to archive
            
        Returns:
            Dict with status and archived memory info
        """
        memories = self._load_all_memories()
        
        for memory in memories:
            if memory.memory_id == memory_id:
                old_status = memory.status
                memory.status = MemoryStatus.DORMANT
                self._save_all_memories(memories)
                
                return {
                    "archived": True,
                    "memory_id": memory_id,
                    "topic": memory.topic,
                    "old_status": str(old_status.value) if hasattr(old_status, 'value') else str(old_status),
                    "new_status": "dormant"
                }
        
        raise ValueError(f"Memory {memory_id} not found")
    
    def list_archived(self) -> List[Dict]:
        """
        List all archived (dormant) memories.
        
        Returns:
            List of archived memory summaries
        """
        memories = self._load_all_memories()
        archived = []
        
        for memory in memories:
            status = getattr(memory, 'status', MemoryStatus.ACTIVE)
            if hasattr(status, 'value'):
                status_str = status.value
            else:
                status_str = str(status)
            
            if status_str == 'dormant':
                archived.append({
                    "memory_id": memory.memory_id,
                    "topic": memory.topic,
                    "lesson": memory.lesson[:100] + "..." if len(memory.lesson) > 100 else memory.lesson,
                    "timestamp": memory.timestamp
                })
        
        return archived
    
    # v0.7.0: Reflection Phase - Synthesize memories into higher-level insights
    
    def reflect(
        self,
        topic: str,
        min_quality: Optional[int] = None,
        min_memories: int = 3,
        include_subtopics: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a reflection by synthesizing memories on a topic.
        
        Inspired by Generative Agents (Park et al.): creates higher-level insights
        from accumulated memories.
        
        Args:
            topic: Topic to reflect on (e.g., 'trading' or 'trading/risk')
            min_quality: Minimum source quality filter
            min_memories: Minimum memories required for reflection
            include_subtopics: Include memories from subtopics
            
        Returns:
            Dict with reflection memory and synthesis metadata
        """
        from engram.memory.types import RelationType
        from collections import defaultdict
        
        # Gather memories matching the topic
        all_memories = self._load_all_memories()
        
        # Filter by topic (exact match or subtopic)
        if include_subtopics:
            matching_memories = [
                m for m in all_memories
                if m.topic == topic or m.topic.startswith(f"{topic}/")
            ]
        else:
            matching_memories = [m for m in all_memories if m.topic == topic]
        
        # Exclude existing reflections (don't reflect on reflections)
        matching_memories = [
            m for m in matching_memories 
            if m.memory_type != MemoryType.REFLECTION
        ]
        
        # Filter by quality
        if min_quality:
            matching_memories = [
                m for m in matching_memories
                if m.source_quality and m.source_quality >= min_quality
            ]
        
        # Check minimum threshold
        if len(matching_memories) < min_memories:
            raise ValueError(
                f"Not enough memories for reflection: {len(matching_memories)} found, "
                f"{min_memories} required. Topic: '{topic}'"
            )
        
        # Group memories by subtopic
        subtopic_groups = defaultdict(list)
        for m in matching_memories:
            subtopic_groups[m.topic].append(m)
        
        # Calculate statistics
        avg_quality = sum(m.source_quality or 5 for m in matching_memories) / len(matching_memories)
        total_memories = len(matching_memories)
        
        # Extract common themes/patterns from lessons
        themes = self._extract_themes(matching_memories)
        
        # Generate synthesis
        synthesis = self._generate_synthesis(
            topic=topic,
            subtopic_groups=dict(subtopic_groups),
            themes=themes,
            avg_quality=avg_quality,
            total_memories=total_memories
        )
        
        # Create reflection memory
        reflection = self.add_lesson(
            topic=f"{topic}/reflection",
            lesson=synthesis,
            memory_type="reflection",
            source_quality=min(10, int(avg_quality) + 1),  # Quality bump for synthesis
            metadata={
                "reflection_type": "synthesis",
                "source_topic": topic,
                "source_count": total_memories,
                "subtopics": list(subtopic_groups.keys()),
                "themes": themes[:5],  # Top 5 themes
                "avg_source_quality": round(avg_quality, 2)
            }
        )
        
        # Link reflection to source memories
        source_ids = []
        for m in matching_memories:
            try:
                self.add_relationship(
                    from_id=reflection.memory_id,
                    to_id=m.memory_id,
                    relation_type="synthesized_from",
                    confidence=0.9
                )
                source_ids.append(m.memory_id)
            except Exception:
                pass  # Skip if relationship already exists
        
        return {
            "reflection": reflection.to_dict(),
            "synthesis": synthesis,
            "source_count": total_memories,
            "subtopics": list(subtopic_groups.keys()),
            "themes": themes[:5],
            "avg_quality": round(avg_quality, 2),
            "source_memory_ids": source_ids
        }
    
    def _extract_themes(self, memories: List[Memory]) -> List[str]:
        """
        Extract common themes from a set of memories.
        Uses simple word frequency analysis.
        """
        from collections import Counter
        import re
        
        # Common words to ignore
        stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
            'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
            'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above',
            'below', 'between', 'under', 'again', 'further', 'then', 'once', 'here',
            'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
            'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or',
            'because', 'until', 'while', 'this', 'that', 'these', 'those', 'i', 'you',
            'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who', 'whom'
        }
        
        # Extract words from all lessons
        word_counts = Counter()
        for memory in memories:
            words = re.findall(r'\b[a-zA-Z]{3,}\b', memory.lesson.lower())
            for word in words:
                if word not in stopwords:
                    word_counts[word] += 1
        
        # Return top themes (words appearing in multiple memories)
        themes = [word for word, count in word_counts.most_common(20) if count >= 2]
        return themes
    
    def _generate_synthesis(
        self,
        topic: str,
        subtopic_groups: Dict[str, List[Memory]],
        themes: List[str],
        avg_quality: float,
        total_memories: int
    ) -> str:
        """
        Generate a synthesis text from grouped memories.
        
        Creates a structured summary without requiring an LLM.
        """
        lines = []
        
        # Header
        lines.append(f"REFLECTION on '{topic}' ({total_memories} memories, avg quality {avg_quality:.1f}/10)")
        lines.append("")
        
        # Themes
        if themes:
            lines.append(f"KEY THEMES: {', '.join(themes[:7])}")
            lines.append("")
        
        # Summarize each subtopic
        for subtopic, memories in sorted(subtopic_groups.items()):
            if len(memories) == 1:
                # Single memory - just quote it
                lines.append(f"• [{subtopic}]: {memories[0].lesson[:200]}")
            else:
                # Multiple memories - summarize
                lines.append(f"• [{subtopic}] ({len(memories)} insights):")
                
                # Show top 3 by quality
                sorted_mems = sorted(
                    memories,
                    key=lambda m: m.source_quality or 5,
                    reverse=True
                )[:3]
                
                for m in sorted_mems:
                    quality_str = f"[Q{m.source_quality}]" if m.source_quality else ""
                    lines.append(f"  - {quality_str} {m.lesson[:150]}")
        
        lines.append("")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        return "\n".join(lines)
    
    def get_reflections(self, topic: Optional[str] = None) -> List[Memory]:
        """
        Get all reflection memories, optionally filtered by topic.
        
        Args:
            topic: Optional topic filter (matches source_topic in metadata)
            
        Returns:
            List of reflection memories
        """
        all_memories = self._load_all_memories()
        
        # Filter to reflections only
        reflections = [
            m for m in all_memories
            if m.memory_type == MemoryType.REFLECTION
        ]
        
        # Filter by topic if specified
        if topic:
            reflections = [
                m for m in reflections
                if m.metadata and m.metadata.get("source_topic") == topic
            ]
        
        # Sort by timestamp (newest first)
        reflections.sort(key=lambda m: m.timestamp, reverse=True)
        
        return reflections
    
    def get_reflection_candidates(
        self,
        min_memories: int = 5,
        min_days_since_last: int = 7
    ) -> List[str]:
        """
        Get topics that are good candidates for auto-reflection.
        
        A topic is a candidate if:
        1. It has at least min_memories non-reflection memories
        2. It hasn't been reflected on in the last min_days_since_last days
        
        Args:
            min_memories: Minimum memories required for reflection
            min_days_since_last: Minimum days since last reflection on this topic
            
        Returns:
            List of topic strings that need reflection
        """
        from collections import defaultdict
        
        all_memories = self._load_all_memories()
        
        # Count memories per base topic (first part before /)
        topic_counts = defaultdict(int)
        for m in all_memories:
            if m.memory_type != MemoryType.REFLECTION:
                # Get base topic (e.g., "trading" from "trading/risk")
                base_topic = m.topic.split('/')[0]
                topic_counts[base_topic] += 1
        
        # Get existing reflections and their timestamps
        reflection_times = {}
        for m in all_memories:
            if m.memory_type == MemoryType.REFLECTION:
                source_topic = m.metadata.get("source_topic") if m.metadata else None
                if source_topic:
                    base_topic = source_topic.split('/')[0]
                    try:
                        ts = datetime.strptime(m.timestamp, "%Y-%m-%d %H:%M")
                        if base_topic not in reflection_times or ts > reflection_times[base_topic]:
                            reflection_times[base_topic] = ts
                    except:
                        pass
        
        # Find candidates
        candidates = []
        now = datetime.now()
        min_age = timedelta(days=min_days_since_last)
        
        for topic, count in topic_counts.items():
            if count < min_memories:
                continue
            
            # Check if reflected recently
            last_reflection = reflection_times.get(topic)
            if last_reflection:
                age = now - last_reflection
                if age < min_age:
                    continue  # Too recent
            
            candidates.append(topic)
        
        # Sort by memory count (most memories first)
        candidates.sort(key=lambda t: topic_counts[t], reverse=True)
        
        return candidates
    
    # v0.8.0: Heuristic-based Quality Assessment
    
    def assess_quality(
        self,
        memory_id: Optional[str] = None,
        limit: int = 10,
        include_duplicates: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Assess memory quality using heuristics (no LLM required).
        
        Args:
            memory_id: Specific memory to assess (if None, assess batch)
            limit: Maximum memories to assess in batch mode
            include_duplicates: Include duplicate detection (slower)
            
        Returns:
            List of quality assessments
        """
        from engram.memory.quality import QualityAssessor, assess_memories_batch
        
        all_memories = self._load_all_memories()
        
        # Build embeddings dict for duplicate detection
        embeddings = None
        if include_duplicates and self.enable_faiss:
            embeddings = self._get_all_embeddings()
        
        if memory_id:
            # Assess single memory
            memory = next((m for m in all_memories if m.memory_id == memory_id), None)
            if not memory:
                raise ValueError(f"Memory not found: {memory_id}")
            
            assessor = QualityAssessor(self.knowledge_graph, self.recall_system)
            assessment = assessor.assess_memory(memory, all_memories, embeddings)
            return [assessment.to_dict()]
        else:
            # Batch assessment - prioritize memories with usage data
            scored_memories = []
            for m in all_memories:
                # Skip reflections
                if m.memory_type == MemoryType.REFLECTION:
                    continue
                
                # Prioritize memories with some activity
                score = (
                    getattr(m, 'access_count', 0) * 2 +
                    getattr(m, 'recall_count', 0) * 3
                )
                scored_memories.append((score, m))
            
            # Sort by activity (most active first for assessment)
            scored_memories.sort(key=lambda x: x[0], reverse=True)
            memories_to_assess = [m for _, m in scored_memories[:limit]]
            
            assessments = assess_memories_batch(
                memories_to_assess,
                self.knowledge_graph,
                self.recall_system,
                embeddings,
                limit
            )
            
            return [a.to_dict() for a in assessments]
    
    def apply_quality_adjustments(
        self,
        assessments: List[Dict[str, Any]],
        auto_apply: bool = False,
        min_confidence: float = 0.7
    ) -> Dict[str, Any]:
        """
        Apply quality adjustments based on assessments.
        
        Args:
            assessments: List of quality assessments
            auto_apply: If True, automatically update qualities
            min_confidence: Minimum confidence to apply changes
            
        Returns:
            Summary of changes made
        """
        all_memories = self._load_all_memories()
        memory_dict = {m.memory_id: m for m in all_memories}
        
        upgraded = []
        downgraded = []
        archived = []
        skipped = []
        
        for assessment in assessments:
            memory_id = assessment["memory_id"]
            confidence = assessment["confidence"]
            action = assessment["suggested_action"]
            assessed = assessment["assessed_quality"]
            
            if confidence < min_confidence:
                skipped.append(memory_id)
                continue
            
            if memory_id not in memory_dict:
                continue
            
            memory = memory_dict[memory_id]
            original = memory.source_quality or 5
            
            if auto_apply:
                if action == "upgrade":
                    memory.source_quality = min(10, int(assessed))
                    upgraded.append(memory_id)
                elif action == "downgrade":
                    memory.source_quality = max(1, int(assessed))
                    downgraded.append(memory_id)
                elif action == "archive":
                    memory.status = MemoryStatus.DORMANT
                    archived.append(memory_id)
            else:
                # Just track what would be changed
                if action == "upgrade":
                    upgraded.append(memory_id)
                elif action == "downgrade":
                    downgraded.append(memory_id)
                elif action == "archive":
                    archived.append(memory_id)
        
        if auto_apply and (upgraded or downgraded or archived):
            self._save_all_memories(all_memories)
        
        return {
            "auto_applied": auto_apply,
            "upgraded": upgraded,
            "downgraded": downgraded,
            "archived": archived,
            "skipped": skipped,
            "total_assessed": len(assessments)
        }
    
    def _get_all_embeddings(self) -> Dict[str, Any]:
        """Get embeddings for all memories (for duplicate detection)."""
        if not self.enable_faiss:
            return {}
        
        try:
            import numpy as np
            
            all_memories = self._load_all_memories()
            embeddings = {}
            
            # Rebuild embeddings from FAISS index
            # Note: This assumes index order matches memory order
            for i, memory in enumerate(all_memories):
                if i < self.index.ntotal:
                    embeddings[memory.memory_id] = self.index.reconstruct(i)
            
            return embeddings
        except Exception:
            return {}
    
    # v0.10.0: Memory Compression and Replay
    
    def find_compression_candidates(
        self,
        limit: int = 10,
        similarity_threshold: float = 0.88
    ) -> List[Dict[str, Any]]:
        """
        Find groups of similar memories that could be compressed.
        
        Args:
            limit: Max candidate groups to return
            similarity_threshold: Minimum similarity to consider for merging
            
        Returns:
            List of compression candidates with merge suggestions
        """
        from engram.memory.compression import MemoryCompressor
        
        all_memories = self._load_all_memories()
        embeddings = self._get_all_embeddings()
        
        compressor = MemoryCompressor(similarity_threshold=similarity_threshold)
        candidates = compressor.find_compression_candidates(all_memories, embeddings, limit)
        
        return [
            {
                "primary_id": c.primary_id,
                "merge_ids": c.merge_ids,
                "similarity_scores": c.similarity_scores,
                "topic": c.topic,
                "combined_lesson": c.combined_lesson,
                "reason": c.reason
            }
            for c in candidates
        ]
    
    def compress_memories(
        self,
        candidates: List[Dict[str, Any]],
        auto_apply: bool = False
    ) -> Dict[str, Any]:
        """
        Compress memory groups by merging into primary and archiving others.
        
        Args:
            candidates: List of compression candidates from find_compression_candidates
            auto_apply: If True, actually perform the compression
            
        Returns:
            Summary of compression results
        """
        all_memories = self._load_all_memories()
        memory_dict = {m.memory_id: m for m in all_memories}
        
        compressed = []
        archived = []
        
        for candidate in candidates:
            primary_id = candidate["primary_id"]
            merge_ids = candidate["merge_ids"]
            combined_lesson = candidate["combined_lesson"]
            
            if primary_id not in memory_dict:
                continue
            
            primary = memory_dict[primary_id]
            
            if auto_apply:
                # Update primary with combined lesson
                primary.lesson = combined_lesson
                
                # Boost quality (compression = curation = value)
                if primary.source_quality:
                    primary.source_quality = min(10, primary.source_quality + 1)
                
                # Archive merged memories
                for merge_id in merge_ids:
                    if merge_id in memory_dict:
                        memory_dict[merge_id].status = MemoryStatus.DORMANT
                        # Add link to primary
                        if hasattr(memory_dict[merge_id], 'metadata') and memory_dict[merge_id].metadata:
                            memory_dict[merge_id].metadata['compressed_into'] = primary_id
                        archived.append(merge_id)
                
                compressed.append(primary_id)
        
        if auto_apply and (compressed or archived):
            self._save_all_memories(all_memories)
        
        return {
            "auto_applied": auto_apply,
            "compressed": compressed,
            "archived": archived,
            "total_candidates": len(candidates)
        }
    
    def select_for_replay(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Select memories for replay (strengthening during sleep).
        
        Prioritizes high-quality memories at risk of decay.
        
        Args:
            limit: Max memories to select
            
        Returns:
            List of memories selected for replay
        """
        from engram.memory.compression import MemoryReplayer
        
        all_memories = self._load_all_memories()
        replayer = MemoryReplayer(max_replays_per_cycle=limit)
        selected = replayer.select_for_replay(all_memories, limit)
        
        return [
            {
                "memory_id": m.memory_id,
                "topic": m.topic,
                "quality": getattr(m, 'source_quality', 5),
                "strength": getattr(m, 'strength', 1.0),
                "access_count": getattr(m, 'access_count', 0)
            }
            for m in selected
        ]
    
    def replay_memories(
        self,
        memory_ids: Optional[List[str]] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Replay memories to strengthen retention.
        
        Args:
            memory_ids: Specific memories to replay (if None, auto-select)
            limit: Max memories to replay
            
        Returns:
            Summary of replay results
        """
        from engram.memory.compression import MemoryReplayer
        
        all_memories = self._load_all_memories()
        memory_dict = {m.memory_id: m for m in all_memories}
        
        replayer = MemoryReplayer(max_replays_per_cycle=limit)
        
        # Select memories to replay
        if memory_ids:
            to_replay = [memory_dict[mid] for mid in memory_ids if mid in memory_dict]
        else:
            to_replay = replayer.select_for_replay(all_memories, limit)
        
        replayed = []
        for memory in to_replay:
            changes = replayer.replay_memory(memory)
            
            # Apply changes
            memory.strength = changes["new_strength"]
            memory.access_count = changes["access_count"]
            memory.last_accessed = datetime.utcnow().isoformat()
            
            replayed.append({
                "memory_id": memory.memory_id,
                "topic": memory.topic,
                "strength_boost": changes["new_strength"] - changes["old_strength"]
            })
        
        if replayed:
            self._save_all_memories(all_memories)
        
        return {
            "replayed_count": len(replayed),
            "replayed": replayed
        }
