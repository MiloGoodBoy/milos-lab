# Auto-Cleaner Skill

## Purpose
Keep my workspace healthy by automatically cleaning up old cron sessions, archiving large transcripts, and monitoring disk usage.

## Triggers
- Every heartbeat (automatic health check)
- Manual trigger: "clean up" or "system health"

## What It Does

### 1. Session Cleanup
- Find cron sessions older than 24h
- Archive large transcript files (>1MB)
- Remove orphaned .reset.* and .deleted.* files

### 2. Disk Monitoring
- Check sessions.json size (warn if >500KB)
- Count total sessions (warn if >50)
- Check disk space

### 3. Reporting
- Log cleanup actions to daily memory
- Alert Dave if critical issues found

## Usage
```
- Auto-runs on heartbeat
- "run auto-cleaner" - manual run
- "check system health" - status only
```

## Thresholds
| Metric | Warn | Critical |
|--------|------|----------|
| sessions.json | >500KB | >1MB |
| Total sessions | >50 | >100 |
| Cron sessions | >30 | >80 |
| Transcript size | >1MB | >5MB |

## Output
- Summary logged to memory/YYYY-MM-DD.md
- Critical alerts sent to Telegram
