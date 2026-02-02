"""
Engram Quickstart Example

Demonstrates basic usage of Engram's memory and quality evaluation.
"""

from engram import MemoryStore, MirrorEvaluator

# Initialize memory store
print("🧠 Initializing Engram...")
memory = MemoryStore(path="./example-memories")

# Add some lessons
print("\n📝 Adding lessons...")
memory.add_lesson(
    topic="trading",
    lesson="Don't chase missed trades - fresh opportunities > emotional attachment",
    source_quality=9,
    understanding=5.0
)

memory.add_lesson(
    topic="trading",
    lesson="Set limit orders 2h before close if conviction is high",
    source_quality=8,
    understanding=4.5
)

memory.add_lesson(
    topic="learning",
    lesson="Deep understanding (1-3 topics) > surface-level (10 topics)",
    source_quality=9,
    understanding=5.0
)

# Search
print("\n🔍 Searching for 'trading mistakes'...")
results = memory.search("trading mistakes", top_k=2)

for i, result in enumerate(results, 1):
    print(f"\n{i}. Score: {result.score:.3f}")
    print(f"   Topic: {result.memory.topic}")
    print(f"   Lesson: {result.memory.lesson}")
    print(f"   Quality: {result.memory.source_quality}/10")

# Recall specific topic
print("\n💭 Recalling all 'trading' lessons...")
trading_lessons = memory.recall("trading", min_quality=8)

for lesson in trading_lessons:
    print(f"- {lesson.lesson}")

# Quality evaluation
print("\n🔍 Evaluating session quality...")
evaluator = MirrorEvaluator(path="./example-memories")

evaluation = evaluator.evaluate_session(
    sources_verified=True,
    understanding_ratings=[4.5, 5.0],
    topics=["trading", "learning"],
    notes="High-quality session with verified sources"
)

print(f"Source Quality: {evaluation.source_quality}/10")
print(f"Understanding: {evaluation.understanding}/5")
print(f"Drift Score: {evaluation.drift_score:.2f}")
print(f"Consolidate? {'✅ Yes' if evaluation.consolidate else '❌ No'}")

# Stats
print("\n📊 Memory stats:")
stats = memory.get_stats()
print(f"Total memories: {stats['total_memories']}")
print(f"Topics: {', '.join(stats['topics'])}")
print(f"FAISS enabled: {stats['faiss_enabled']}")

print("\n✅ Quickstart complete!")
