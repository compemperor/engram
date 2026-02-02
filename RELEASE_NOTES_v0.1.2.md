# Release Notes - v0.1.2

**Release Date:** 2026-02-02  
**Type:** Bug Fix + Documentation Update

---

## 🐛 Bug Fix: Session Consolidation

**Issue:** Learning session consolidation was not saving insights to permanent memory storage.

**Root Cause:** The `consolidate()` method was not converting high-quality notes to insights before evaluation.

**Fix:**
- Notes with `source_quality >= 8` now automatically convert to insights during consolidation
- Insights are properly saved to memory via `memory_store.add_lesson()` when `evaluation.consolidate == true`
- Session workflow now fully functional from start to permanent storage

**Impact:** Learning sessions are now a fully working feature - high-quality observations automatically become permanent memories.

---

## 📝 Documentation Updates

**Updated:**
- `skills/openclaw/SKILL.md` - Fixed all API parameters and examples
- Function signatures corrected (query params vs JSON body)
- Added note about quality >= 8 auto-save behavior
- Removed incorrect `log_learning` and `finish_learning` functions
- Added correct `log_note`, `verify_learning`, and `consolidate_session` functions

**API Version:** Bumped to 0.1.2 in FastAPI app

---

## 🧪 Testing

**Validated:**
- ✅ Session creation (`/learning/session/start`)
- ✅ Note logging (`/learning/session/{id}/note`)
- ✅ Verification checkpoints (`/learning/session/{id}/verify`)
- ✅ Consolidation with memory save (`/learning/session/{id}/consolidate`)
- ✅ High-quality notes (quality >= 8) auto-saved to memory
- ✅ End-to-end workflow tested successfully

---

## 🔄 Workflow

**Before v0.1.2:**
```python
# Consolidation reported success but didn't save to memory ❌
consolidate_session(session_id)
# Had to manually call memory.add() separately
```

**After v0.1.2:**
```python
# High-quality notes automatically saved during consolidation ✅
log_note(session_id, "Key insight", source_quality=9)
consolidate_session(session_id)
# Insight is now in permanent memory!
```

---

## 📦 Docker Images

**Available:**
- `ghcr.io/compemperor/engram:latest` (v0.1.2)
- `ghcr.io/compemperor/engram:0.1.2` (tagged)

**Size:** ~8.3GB

---

## 🚀 Migration

**No breaking changes!**

Existing users can simply pull the new image:

```bash
docker pull ghcr.io/compemperor/engram:latest
docker restart engram
```

All existing memories and data remain compatible.

---

## 📊 Files Changed

- `engram/learning/session.py` - Auto-convert high-quality notes to insights
- `engram/api.py` - Version bump to 0.1.2
- `skills/openclaw/SKILL.md` - Corrected documentation

**Lines changed:** ~30 additions, ~20 modifications

---

## 🙏 Credits

Bug discovered and reported during live testing session.  
Fixed within 30 minutes of discovery.  
Full workflow validated before release.

---

## 🔗 Links

**Repository:** https://github.com/compemperor/engram  
**Docker Images:** https://github.com/compemperor?tab=packages  
**Documentation:** [README.md](README.md) | [AGENTS.md](AGENTS.md) | [QUICKSTART.md](QUICKSTART.md)

---

**For issues or questions:** Open an issue on GitHub

🦀 **Engram v0.1.2 - Learning sessions now fully functional!**
