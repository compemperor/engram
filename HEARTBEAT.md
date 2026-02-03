# HEARTBEAT.md

## Idle Time Activities (Check 2-3x per day)

### 1. Active Recall Challenge (Daily)
Run memory recall to strengthen retention:
```bash
curl http://localhost:8765/recall/challenge
# Answer the question internally
# Track if I got it right
```

### 2. Memory Stats Review (Daily)
Check memory health:
```bash
curl http://localhost:8765/memory/stats
curl http://localhost:8765/recall/stats
```

### 3. Periodic Checks (Rotate through day)
- **Morning (08:00-10:00):** Weather, calendar for today
- **Midday (12:00-14:00):** Check mentions on X (if implemented)
- **Afternoon (15:00-17:00):** Market close summary (if trading day)
- **Evening (18:00-20:00):** Review daily notes, update MEMORY.md

### 4. Background Maintenance (Once daily)
- Run recall challenges to test retention
- Check Engram memory stats
- Commit changes to skills/config files

### 5. Proactive Work (When quiet)
- Read through learning session files
- Consolidate insights into MEMORY.md
- Organize workspace files
- Update documentation

## Rules
- Late night (23:00-08:00): Stay quiet unless urgent
- If nothing needs attention: Reply HEARTBEAT_OK
- If something needs attention: Report it (don't assume user knows)
- Run recall challenges to test understanding
- Track recall success rate
