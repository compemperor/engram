"""
Basic tests for Engram memory system
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from engram.memory.store import MemoryStore


class TestMemoryStore:
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def memory_store(self, temp_dir):
        """Create memory store instance"""
        return MemoryStore(path=temp_dir, enable_faiss=False)
    
    def test_add_lesson(self, memory_store):
        """Test adding a lesson"""
        memory = memory_store.add_lesson(
            topic="test",
            lesson="This is a test lesson",
            source_quality=9,
            understanding=4.5
        )
        
        assert memory.topic == "test"
        assert memory.lesson == "This is a test lesson"
        assert memory.source_quality == 9
        assert memory.understanding == 4.5
    
    def test_recall(self, memory_store):
        """Test recalling memories by topic"""
        memory_store.add_lesson("trading", "Lesson 1")
        memory_store.add_lesson("trading", "Lesson 2")
        memory_store.add_lesson("learning", "Lesson 3")
        
        trading_memories = memory_store.recall("trading")
        
        assert len(trading_memories) == 2
        assert all(m.topic == "trading" for m in trading_memories)
    
    def test_stats(self, memory_store):
        """Test memory statistics"""
        memory_store.add_lesson("topic1", "Lesson 1")
        memory_store.add_lesson("topic2", "Lesson 2")
        
        stats = memory_store.get_stats()
        
        assert stats["total_memories"] == 2
        assert set(stats["topics"]) == {"topic1", "topic2"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
