"""
Knowledge Graph for memory relationships

Stores and queries relationships between memories
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Set
from collections import defaultdict

from engram.memory.types import Relationship, RelationType


class KnowledgeGraph:
    """
    Graph structure for memory relationships
    
    Stores relationships as adjacency lists:
    - Forward: memory_id -> [outgoing relationships]
    - Backward: memory_id -> [incoming relationships]
    """
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.graph_file = storage_path / "knowledge_graph.json"
        
        # Adjacency lists
        self.forward: Dict[str, List[Relationship]] = defaultdict(list)
        self.backward: Dict[str, List[Relationship]] = defaultdict(list)
        
        self.load()
    
    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship between memories"""
        # Add to forward index (from -> to)
        self.forward[relationship.from_id].append(relationship)
        
        # Add to backward index (to -> from)
        self.backward[relationship.to_id].append(relationship)
    
    def get_related(
        self,
        memory_id: str,
        relation_type: Optional[RelationType] = None,
        direction: str = "both"  # "outgoing", "incoming", or "both"
    ) -> List[Relationship]:
        """
        Get all relationships for a memory
        
        Args:
            memory_id: The memory to query
            relation_type: Filter by relationship type (optional)
            direction: Which direction to search
        
        Returns:
            List of relationships
        """
        results = []
        
        if direction in ["outgoing", "both"]:
            results.extend(self.forward.get(memory_id, []))
        
        if direction in ["incoming", "both"]:
            results.extend(self.backward.get(memory_id, []))
        
        # Filter by type if specified
        if relation_type:
            results = [r for r in results if r.relation_type == relation_type]
        
        return results
    
    def get_connected_memories(
        self,
        memory_id: str,
        relation_type: Optional[RelationType] = None,
        max_depth: int = 2
    ) -> Set[str]:
        """
        Get all memory IDs connected to this one (BFS)
        
        Args:
            memory_id: Starting memory
            relation_type: Filter by relationship type
            max_depth: Maximum depth to traverse
        
        Returns:
            Set of connected memory IDs
        """
        visited = set()
        queue = [(memory_id, 0)]  # (id, depth)
        
        while queue:
            current_id, depth = queue.pop(0)
            
            if current_id in visited or depth > max_depth:
                continue
            
            visited.add(current_id)
            
            # Get all related memories
            relationships = self.get_related(current_id, relation_type)
            
            for rel in relationships:
                # Add both endpoints
                next_id = rel.to_id if rel.from_id == current_id else rel.from_id
                if next_id not in visited:
                    queue.append((next_id, depth + 1))
        
        visited.discard(memory_id)  # Remove self
        return visited
    
    def save(self) -> None:
        """Save graph to disk"""
        data = {
            "forward": {
                k: [r.to_dict() for r in v]
                for k, v in self.forward.items()
            },
            "backward": {
                k: [r.to_dict() for r in v]
                for k, v in self.backward.items()
            }
        }
        
        self.graph_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.graph_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self) -> None:
        """Load graph from disk"""
        if not self.graph_file.exists():
            return
        
        try:
            with open(self.graph_file, 'r') as f:
                data = json.load(f)
            
            # Reconstruct forward index
            for memory_id, rels in data.get("forward", {}).items():
                self.forward[memory_id] = [
                    Relationship(**r) for r in rels
                ]
            
            # Reconstruct backward index
            for memory_id, rels in data.get("backward", {}).items():
                self.backward[memory_id] = [
                    Relationship(**r) for r in rels
                ]
        
        except Exception as e:
            print(f"Warning: Could not load knowledge graph: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get graph statistics"""
        total_relationships = sum(len(rels) for rels in self.forward.values())
        
        return {
            "total_nodes": len(set(self.forward.keys()) | set(self.backward.keys())),
            "total_relationships": total_relationships,
            "forward_edges": len(self.forward),
            "backward_edges": len(self.backward)
        }
