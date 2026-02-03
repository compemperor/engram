"""
Engram FastAPI Server - REST API for memory, learning, and quality evaluation

Provides professional REST endpoints for all Engram functionality.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uvicorn
import os

from engram.memory.store_v2 import MemoryStoreV2 as MemoryStore
from engram.memory.types import SearchResult
from engram.mirror.evaluator import MirrorEvaluator
from engram.mirror.drift import DriftDetector
from engram.learning.session import LearningSession


# Pydantic models for request/response validation

class AddLessonRequest(BaseModel):
    topic: str = Field(..., description="Topic category")
    lesson: str = Field(..., description="The lesson/memory content")
    source_quality: Optional[int] = Field(None, ge=1, le=10, description="Source quality (1-10)")
    understanding: Optional[float] = Field(None, ge=1.0, le=5.0, description="Understanding score (1-5)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    top_k: int = Field(5, ge=1, le=50, description="Number of results")
    min_quality: Optional[int] = Field(None, ge=1, le=10, description="Minimum quality filter")
    topic_filter: Optional[str] = Field(None, description="Filter by specific topic")


class EvaluateSessionRequest(BaseModel):
    sources_verified: bool = Field(..., description="Were sources verified?")
    understanding_ratings: List[float] = Field(..., description="Understanding scores (1-5) per topic")
    topics: List[str] = Field(..., description="Topics covered")
    notes: Optional[str] = Field(None, description="Evaluation notes")


class LearningNoteRequest(BaseModel):
    content: str = Field(..., description="Note content")
    source_url: Optional[str] = Field(None, description="Source URL")
    source_quality: Optional[int] = Field(None, ge=1, le=10, description="Source quality (1-10)")


class VerificationRequest(BaseModel):
    topic: str = Field(..., description="Topic to verify")
    understanding: float = Field(..., ge=1.0, le=5.0, description="Understanding (1-5)")
    sources_verified: bool = Field(False, description="Sources verified?")
    gaps: Optional[List[str]] = Field(None, description="What's unclear")
    applications: Optional[List[str]] = Field(None, description="How to apply")


# Initialize FastAPI app
app = FastAPI(
    title="Engram API",
    description="Memory traces for AI agents - Self-improving memory system with knowledge graphs and active recall",
    version="0.2.3"
)

# Global state (initialized on startup)
memory_store: Optional[MemoryStore] = None
mirror_evaluator: Optional[MirrorEvaluator] = None
drift_detector: Optional[DriftDetector] = None
active_sessions: Dict[str, LearningSession] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize Engram components on startup"""
    global memory_store, mirror_evaluator, drift_detector
    
    # Use environment variable for data path, default to /data/memories for Docker
    data_path = os.getenv("ENGRAM_DATA_PATH", "/data/memories")
    
    memory_store = MemoryStore(path=data_path)
    mirror_evaluator = MirrorEvaluator(path=data_path)
    drift_detector = DriftDetector(path=data_path)
    
    print("✓ Engram API started")
    stats = memory_store.get_stats()
    print(f"  Memory: {stats.get('total_memories', 0)} memories")
    print(f"  FAISS: {'enabled' if memory_store.enable_faiss else 'disabled'}")


# Health & Info Endpoints

@app.get("/")
async def root():
    """API root - returns basic info"""
    return {
        "service": "Engram API",
        "version": "0.2.3",
        "description": "Memory traces for AI agents with knowledge graphs and active recall",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "memory_enabled": memory_store is not None,
        "mirror_enabled": mirror_evaluator is not None,
        "timestamp": memory_store.metadata.get("last_updated") if memory_store else None
    }


# Memory Endpoints

@app.post("/memory/add")
async def add_lesson(request: AddLessonRequest):
    """Add a new lesson/memory"""
    try:
        memory = memory_store.add_lesson(
            topic=request.topic,
            lesson=request.lesson,
            source_quality=request.source_quality,
            understanding=request.understanding,
            metadata=request.metadata
        )
        
        return {
            "status": "success",
            "memory": memory.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/search")
async def search_memory(request: SearchRequest):
    """Semantic search across memories"""
    try:
        results = memory_store.search(
            query=request.query,
            top_k=request.top_k,
            min_quality=request.min_quality,
            topic_filter=request.topic_filter
        )
        
        return {
            "query": request.query,
            "count": len(results),
            "results": [
                {
                    "memory": r.memory.to_dict(),
                    "score": r.score
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/recall/{topic}")
async def recall_topic(topic: str, min_quality: Optional[int] = None):
    """Recall all memories for a specific topic"""
    try:
        memories = memory_store.recall(topic=topic, min_quality=min_quality)
        
        return {
            "topic": topic,
            "count": len(memories),
            "memories": [m.to_dict() for m in memories]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/stats")
async def memory_stats():
    """Get memory statistics"""
    try:
        stats = memory_store.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/rebuild-index")
async def rebuild_index():
    """Rebuild FAISS index from scratch"""
    try:
        if not memory_store.enable_faiss:
            raise HTTPException(status_code=400, detail="FAISS not enabled")
        
        memory_store.rebuild_index()
        
        return {
            "status": "success",
            "message": "Index rebuilt successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mirror (Quality) Endpoints

@app.post("/mirror/evaluate")
async def evaluate_session(request: EvaluateSessionRequest):
    """Evaluate a learning session quality"""
    try:
        evaluation = mirror_evaluator.evaluate_session(
            sources_verified=request.sources_verified,
            understanding_ratings=request.understanding_ratings,
            topics=request.topics,
            notes=request.notes
        )
        
        return {
            "status": "success",
            "evaluation": evaluation.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mirror/drift")
async def check_drift(window: int = 10):
    """Check for drift in recent sessions"""
    try:
        alerts = drift_detector.check_drift(window=window)
        stability = drift_detector.get_stability_score(window=window)
        
        return {
            "stability_score": stability,
            "alerts": [
                {
                    "severity": a.severity,
                    "category": a.category,
                    "message": a.message,
                    "metric": a.metric,
                    "threshold": a.threshold
                }
                for a in alerts
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mirror/metrics")
async def mirror_metrics():
    """Get current mirror metrics"""
    try:
        drift_metrics = mirror_evaluator.get_drift_metrics()
        quality_trends = mirror_evaluator.get_quality_trends(last_n=10)
        
        return {
            "drift": drift_metrics,
            "quality": quality_trends
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Learning Session Endpoints

@app.post("/learning/session/start")
async def start_session(
    topic: str,
    duration_min: int = 30,
    session_id: Optional[str] = None
):
    """Start a new learning session"""
    try:
        if session_id is None:
            from datetime import datetime
            session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        if session_id in active_sessions:
            raise HTTPException(status_code=400, detail="Session already exists")
        
        # Use MEMORY_PATH from environment to ensure persistence
        memory_path = os.getenv("MEMORY_PATH", "/data/memories")
        output_dir = os.path.join(memory_path, "learning-sessions")
        
        session = LearningSession(
            topic=topic,
            duration_min=duration_min,
            output_dir=output_dir,
            enable_verification=True
        )
        
        active_sessions[session_id] = session
        
        return {
            "status": "success",
            "session_id": session_id,
            "topic": topic,
            "duration_min": duration_min
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/learning/session/{session_id}/note")
async def add_session_note(session_id: str, request: LearningNoteRequest):
    """Add a note to learning session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        session = active_sessions[session_id]
        session.add_note(
            content=request.content,
            source_url=request.source_url,
            source_quality=request.source_quality
        )
        
        return {
            "status": "success",
            "notes_count": len(session.notes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/learning/session/{session_id}/verify")
async def verify_session(session_id: str, request: VerificationRequest):
    """Add verification checkpoint to session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        session = active_sessions[session_id]
        checkpoint = session.verify(
            topic=request.topic,
            understanding=request.understanding,
            sources_verified=request.sources_verified,
            gaps=request.gaps,
            applications=request.applications
        )
        
        return {
            "status": "success",
            "checkpoint": {
                "topic": checkpoint.topic,
                "understanding": checkpoint.understanding,
                "sources_verified": checkpoint.sources_verified
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/learning/session/{session_id}/time-check")
async def session_time_check(session_id: str):
    """Check time status of learning session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        session = active_sessions[session_id]
        time_status = session.time_check()
        
        return {
            "status": "success",
            "time": time_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/learning/session/{session_id}/consolidate")
async def consolidate_session(session_id: str):
    """Consolidate and finalize learning session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        session = active_sessions[session_id]
        summary = session.consolidate()
        
        # Evaluate with mirror
        evaluation = mirror_evaluator.evaluate_session(
            sources_verified=session.all_sources_verified(),
            understanding_ratings=session.get_understanding_ratings(),
            topics=session.get_topics_covered()
        )
        
        # Save quality insights if consolidation recommended
        if evaluation.consolidate:
            for insight in session.insights:
                memory_store.add_lesson(
                    topic=session.topic,
                    lesson=insight,
                    source_quality=int(evaluation.source_quality),
                    understanding=evaluation.understanding
                )
        
        # Clean up
        del active_sessions[session_id]
        
        return {
            "status": "success",
            "summary": summary,
            "evaluation": evaluation.to_dict(),
            "saved_to_memory": evaluation.consolidate
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/learning/sessions")
async def list_sessions():
    """List active learning sessions"""
    return {
        "count": len(active_sessions),
        "sessions": [
            {
                "session_id": sid,
                "topic": session.topic,
                "notes_count": len(session.notes),
                "checkpoints_count": len(session.checkpoints)
            }
            for sid, session in active_sessions.items()
        ]
    }


# Enhanced Memory Endpoints (v0.2.0)

class AddLessonV2Request(BaseModel):
    topic: str = Field(..., description="Topic category")
    lesson: str = Field(..., description="The lesson/memory content")
    memory_type: str = Field("semantic", description="Memory type: episodic or semantic")
    source_quality: Optional[int] = Field(None, ge=1, le=10, description="Source quality (1-10)")
    understanding: Optional[float] = Field(None, ge=1.0, le=5.0, description="Understanding score (1-5)")
    entities: Optional[List[Dict]] = Field(None, description="Extracted entities")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


@app.post("/memory/add/v2")
async def add_lesson_v2(request: AddLessonV2Request):
    """Add memory with type classification (v0.2.0)"""
    try:
        memory = memory_store.add_lesson(
            topic=request.topic,
            lesson=request.lesson,
            memory_type=request.memory_type,
            source_quality=request.source_quality,
            understanding=request.understanding,
            entities=request.entities,
            metadata=request.metadata
        )
        
        return {
            "status": "success",
            "memory": memory.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/related/{memory_id}")
async def get_related_memories(
    memory_id: str,
    relation_type: Optional[str] = None,
    max_depth: int = 1
):
    """Get memories related via knowledge graph"""
    try:
        related = memory_store.get_related_memories(
            memory_id=memory_id,
            relation_type=relation_type,
            max_depth=max_depth
        )
        
        return {
            "memory_id": memory_id,
            "count": len(related),
            "related": [m.to_dict() for m in related]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recall/challenge")
async def generate_recall_challenge(memory_id: Optional[str] = None):
    """Generate active recall challenge"""
    try:
        # Get memories
        memories = memory_store._load_all_memories()
        
        if memory_id:
            # Specific memory
            memory = next((m for m in memories if m.memory_id == memory_id), None)
            if not memory:
                raise HTTPException(status_code=404, detail="Memory not found")
        else:
            # Random memory
            import random
            memory = random.choice(memories)
        
        challenge = memory_store.recall_system.generate_challenge(memory)
        
        return {
            "status": "success",
            "challenge": challenge.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recall/stats")
async def get_recall_stats(memory_id: Optional[str] = None):
    """Get recall statistics"""
    try:
        stats = memory_store.recall_system.get_statistics(memory_id)
        
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Main entry point
def main(host: str = "0.0.0.0", port: int = 8765, reload: bool = False):
    """Run Engram API server"""
    uvicorn.run(
        "engram.api:app",
        host=host,
        port=port,
        reload=reload
    )


if __name__ == "__main__":
    main()
