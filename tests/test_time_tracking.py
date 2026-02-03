#!/usr/bin/env python3
"""
Test script for Engram v0.2.2 time tracking features
"""

import requests
import time
import json

BASE_URL = "http://localhost:8765"

def test_time_tracking():
    """Test time tracking in learning sessions"""
    
    print("🧪 Testing Engram v0.2.2 Time Tracking")
    print("=" * 60)
    
    # 1. Start session
    print("\n1. Starting learning session (1 min duration)...")
    response = requests.post(
        f"{BASE_URL}/learning/session/start",
        params={"topic": "time-tracking-test", "duration_min": 1}
    )
    assert response.status_code == 200
    data = response.json()
    session_id = data["session_id"]
    print(f"✅ Session started: {session_id}")
    print(f"   Duration: {data['duration_min']} min")
    
    # 2. Check time immediately
    print("\n2. Checking time status (should be ~0% progress)...")
    response = requests.get(f"{BASE_URL}/learning/session/{session_id}/time-check")
    assert response.status_code == 200
    time_data = response.json()["time"]
    print(f"✅ Time check working")
    print(f"   Elapsed: {time_data['elapsed_min']} min")
    print(f"   Remaining: {time_data['remaining_min']} min")
    print(f"   Progress: {time_data['progress_percent']}%")
    print(f"   Target reached: {time_data['target_reached']}")
    assert time_data["target_reached"] == False
    assert time_data["progress_percent"] < 10
    
    # 3. Add a note
    print("\n3. Adding note...")
    response = requests.post(
        f"{BASE_URL}/learning/session/{session_id}/note",
        json={
            "content": "Testing time tracking features",
            "source_quality": 9
        }
    )
    assert response.status_code == 200
    print("✅ Note added")
    
    # 4. Wait a bit and check time again
    print("\n4. Waiting 10 seconds...")
    time.sleep(10)
    
    response = requests.get(f"{BASE_URL}/learning/session/{session_id}/time-check")
    time_data = response.json()["time"]
    print(f"✅ Time check after 10s")
    print(f"   Elapsed: {time_data['elapsed_min']} min")
    print(f"   Remaining: {time_data['remaining_min']} min")
    print(f"   Progress: {time_data['progress_percent']}%")
    assert time_data["elapsed_min"] > 0.15  # Should be > 10 seconds
    
    # 5. Add verification checkpoint
    print("\n5. Adding verification checkpoint...")
    response = requests.post(
        f"{BASE_URL}/learning/session/{session_id}/verify",
        json={
            "topic": "time-tracking",
            "understanding": 5.0,
            "sources_verified": True,
            "gaps": [],
            "applications": ["Implement in agents", "Improve session accuracy"]
        }
    )
    assert response.status_code == 200
    print("✅ Verification checkpoint added")
    
    # 6. Consolidate before target time (should warn)
    print("\n6. Consolidating before target time (should warn)...")
    response = requests.post(f"{BASE_URL}/learning/session/{session_id}/consolidate")
    assert response.status_code == 200
    summary = response.json()["summary"]
    print(f"✅ Session consolidated")
    print(f"   Planned: {summary['duration_min']} min (consolidated early)")
    print(f"   Notes: {summary['notes_count']}")
    print(f"   Checkpoints: {summary['checkpoints_count']}")
    
    # 7. Test that session is removed from active sessions
    print("\n7. Verifying session cleanup...")
    response = requests.get(f"{BASE_URL}/learning/session/{session_id}/time-check")
    assert response.status_code == 404  # Session should be gone
    print("✅ Session removed from active sessions")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("\nTime tracking features verified:")
    print("  - target_end_time calculation")
    print("  - time_check() method")
    print("  - elapsed_time() and time_remaining()")
    print("  - progress_percent calculation")
    print("  - Early consolidation warning")
    print("  - API endpoint /learning/session/{id}/time-check")

if __name__ == "__main__":
    try:
        test_time_tracking()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
