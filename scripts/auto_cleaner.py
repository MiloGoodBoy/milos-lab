#!/usr/bin/env python3
"""
Auto-Cleaner - Session and Workspace Health Automation
"""
import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

# Paths
OPENCLAW_DIR = Path("/Users/milogoodboy/.openclaw")
WORKSPACE = Path("/Users/milogoodboy/.openclaw/workspace")
SESSIONS_DIR = OPENCLAW_DIR / "agents" / "main" / "sessions"
ARCHIVE_DIR = OPENCLAW_DIR / "archive"
MEMORY_DIR = WORKSPACE / "memory"

# Thresholds
THRESHOLDS = {
    "sessions_json_kb": {"warn": 500, "critical": 1000},
    "total_sessions": {"warn": 50, "critical": 100},
    "cron_sessions": {"warn": 30, "critical": 80},
    "transcript_mb": {"warn": 1, "critical": 5},
}


def log(msg: str):
    print(f"[Auto-Cleaner] {msg}")


def get_sessions_json_size() -> int:
    """Get sessions.json size in KB"""
    f = SESSIONS_DIR / "sessions.json"
    if f.exists():
        return f.stat().st_size // 1024
    return 0


def count_sessions() -> Tuple[int, int]:
    """Count total and cron sessions"""
    with open(SESSIONS_DIR / "sessions.json") as f:
        data = json.load(f)
    
    total = len(data)
    cron = sum(1 for k in data if "cron" in k)
    return total, cron


def find_large_transcripts() -> List[Path]:
    """Find transcripts larger than threshold"""
    large = []
    threshold = THRESHOLDS["transcript_mb"]["warn"] * 1024 * 1024
    
    for f in SESSIONS_DIR.glob("*.jsonl"):
        if f.stat().st_size > threshold:
            large.append(f)
    
    return large


def archive_old_sessions():
    """Archive old reset/deleted sessions"""
    archived = []
    
    for f in SESSIONS_DIR.glob("*.reset.*"):
        # Move to archive with date
        date_dir = ARCHIVE_DIR / f"sessions-{datetime.now().strftime('%Y%m%d')}"
        date_dir.mkdir(exist_ok=True)
        new_path = date_dir / f.name
        f.rename(new_path)
        archived.append(str(new_path))
    
    for f in SESSIONS_DIR.glob("*.deleted.*"):
        date_dir = ARCHIVE_DIR / f"sessions-{datetime.now().strftime('%Y%m%d')}"
        date_dir.mkdir(exist_ok=True)
        new_path = date_dir / f.name
        f.rename(new_path)
        archived.append(str(new_path))
    
    return archived


def check_disk_space() -> Dict:
    """Check disk space"""
    result = subprocess.run(["df", "-h", str(OPENCLAW_DIR)], capture_output=True, text=True)
    lines = result.stdout.strip().split("\n")
    if len(lines) > 1:
        parts = lines[1].split()
        return {
            "total": parts[1],
            "used": parts[2],
            "available": parts[3],
            "percent": parts[4],
        }
    return {}


def run_health_check() -> Dict:
    """Run full health check"""
    result = {
        "timestamp": datetime.now().isoformat(),
        "sessions_json_kb": get_sessions_json_size(),
        "total_sessions": 0,
        "cron_sessions": 0,
        "large_transcripts": [],
        "disk_space": {},
        "alerts": [],
    }
    
    # Count sessions
    result["total_sessions"], result["cron_sessions"] = count_sessions()
    
    # Check thresholds
    if result["sessions_json_kb"] > THRESHOLDS["sessions_json_kb"]["critical"]:
        result["alerts"].append(f"CRITICAL: sessions.json is {result['sessions_json_kb']}KB")
    elif result["sessions_json_kb"] > THRESHOLDS["sessions_json_kb"]["warn"]:
        result["alerts"].append(f"WARNING: sessions.json is {result['sessions_json_kb']}KB")
    
    if result["total_sessions"] > THRESHOLDS["total_sessions"]["critical"]:
        result["alerts"].append(f"CRITICAL: {result['total_sessions']} total sessions")
    elif result["total_sessions"] > THRESHOLDS["total_sessions"]["warn"]:
        result["alerts"].append(f"WARNING: {result['total_sessions']} total sessions")
    
    # Find large transcripts
    result["large_transcripts"] = [str(f) for f in find_large_transcripts()]
    
    # Disk space
    result["disk_space"] = check_disk_space()
    
    return result


def main():
    log("Running auto-cleaner health check...")
    
    health = run_health_check()
    
    log(f"Sessions: {health['total_sessions']} total, {health['cron_sessions']} cron")
    log(f"sessions.json: {health['sessions_json_kb']}KB")
    log(f"Large transcripts: {len(health['large_transcripts'])}")
    
    # Archive old sessions
    archived = archive_old_sessions()
    if archived:
        log(f"Archived {len(archived)} old session files")
    
    # Report alerts
    for alert in health["alerts"]:
        log(f"ALERT: {alert}")
    
    # Log to memory
    memory_file = MEMORY_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.md"
    with open(memory_file, "a") as f:
        f.write(f"\n## Auto-Cleaner - {datetime.now().strftime('%H:%M')}\n")
        f.write(f"- sessions.json: {health['sessions_json_kb']}KB\n")
        f.write(f"- Sessions: {health['total_sessions']} total, {health['cron_sessions']} cron\n")
        if health["alerts"]:
            f.write(f"- Alerts: {', '.join(health['alerts'])}\n")
    
    if health["alerts"]:
        print("\nALERTS:", health["alerts"])
    
    log("Health check complete")


if __name__ == "__main__":
    main()
