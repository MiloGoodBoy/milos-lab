#!/bin/bash
# OpenClaw Daily Update Checker - macOS Version
# Uses launchctl instead of systemctl

LOG_FILE="/tmp/openclaw-update-check.log"
LOCK_FILE="/tmp/openclaw-update-check.lock"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Prevent concurrent runs
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        log "Update check already running (PID $PID), exiting"
        exit 0
    fi
    rm -f "$LOCK_FILE"
fi
echo $$ > "$LOCK_FILE"

OPENCLAW_DIR="/Users/milogoodboy/.npm-global/lib/node_modules/openclaw"
LAUNCHAGENT="ai.openclaw.gateway"

log "=== Starting daily update check (macOS) ==="

# Check if gateway is running via launchctl
if ! launchctl list | grep -q "$LAUNCHAGENT"; then
    log "Gateway not running, skipping update check"
    rm -f "$LOCK_FILE"
    exit 0
fi

# Check for outdated packages
log "Checking for updates..."
cd "$OPENCLAW_DIR" || exit 1

# Get current version
CURRENT_VERSION=$(node -p "require('./package.json').version" 2>/dev/null)
log "Current version: $CURRENT_VERSION"

# Check npm for updates (dry-run)
UPDATES=$(npm outdated --json 2>/dev/null | node -e "
const stdin = require('fs').readFileSync(0, 'utf-8');
const data = stdin.trim() ? JSON.parse(stdin) : {};
const updates = Object.keys(data).filter(k => data[k].current !== 'linked');
console.log(updates.length);
" 2>/dev/null)

if [ -z "$UPDATES" ] || [ "$UPDATES" = "0" ] || [ "$UPDATES" = "" ]; then
    log "No updates available"
    rm -f "$LOCK_FILE"
    exit 0
fi

log "Updates available: $UPDATES packages"

# Check sessions.json size
SESSIONS_FILE="/Users/milogoodboy/.openclaw/agents/main/sessions/sessions.json"
if [ -f "$SESSIONS_FILE" ]; then
    SESSION_SIZE=$(stat -f%z "$SESSIONS_FILE" 2>/dev/null)
    if [ "$SESSION_SIZE" -gt 50000 ]; then
        log "WARNING: sessions.json is ${SESSION_SIZE} bytes (over 50KB)"
    fi
fi

# Get Telegram bot token
TELEGRAM_TOKEN=$(cat /Users/milogoodboy/.openclaw/config/telegram-bot-token 2>/dev/null)

notify_telegram() {
    if [ -n "$TELEGRAM_TOKEN" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
            -d "chat_id=2008532658" -d "text=$1" >> "$LOG_FILE" 2>&1
    fi
}

# Run backup first
log "Running backup before update..."
if bash /Users/milogoodboy/.openclaw/skills/backup/backup.sh >> "$LOG_FILE" 2>&1; then
    log "Backup complete"
else
    log "WARNING: Backup may have failed"
fi

# Notify Dave
notify_telegram "🆙 Updating OpenClaw (v$CURRENT_VERSION → latest, $UPDATES packages)"

# Stop gateway using launchctl
log "Stopping gateway..."
launchctl unload -w ~/Library/LaunchAgents/"$LAUNCHAGENT".plist 2>/dev/null

# Wait for graceful shutdown
sleep 3

# Run npm install
log "Running npm install..."
if npm install --production >> "$LOG_FILE" 2>&1; then
    log "npm install succeeded"
else
    log "ERROR: npm install failed"
    notify_telegram "❌ OpenClaw update failed during npm install"
    launchctl load -w ~/Library/LaunchAgents/"$LAUNCHAGENT".plist 2>/dev/null
    rm -f "$LOCK_FILE"
    exit 1
fi

# Verify dist/index.js exists
if [ ! -f "dist/index.js" ]; then
    log "ERROR: dist/index.js not found after update"
    notify_telegram "❌ OpenClaw update failed: dist/index.js not found"
    launchctl load -w ~/Library/LaunchAgents/"$LAUNCHAGENT".plist 2>/dev/null
    rm -f "$LOCK_FILE"
    exit 1
fi

# Clear sessions to prevent state issues
log "Clearing sessions..."
echo '{}' > "$SESSIONS_FILE" 2>/dev/null
rm -f /Users/milogoodboy/.openclaw/agents/main/sessions/*.jsonl 2>/dev/null

# Start gateway using launchctl
log "Starting gateway..."
launchctl load -w ~/Library/LaunchAgents/"$LAUNCHAGENT".plist 2>/dev/null

# Wait and verify it's running
sleep 5
if launchctl list | grep -q "$LAUNCHAGENT"; then
    log "Gateway started successfully"
    NEW_VERSION=$(node -p "require('./package.json').version" 2>/dev/null)
    notify_telegram "✅ OpenClaw updated to v$NEW_VERSION, all systems go 🐾"
else
    log "ERROR: Gateway failed to start"
    notify_telegram "❌ OpenClaw update complete but gateway failed to start"
fi

log "=== Update check complete ==="
rm -f "$LOCK_FILE"
