#!/usr/bin/env bash
# zsiga daemon control script
# Usage: ./zsigactl.sh {start|stop|restart|status|log|tail}

set -euo pipefail

REPO="/home/zsiga/repo"
PYTHON="$REPO/venv/bin/python"
PIDFILE="$REPO/data/lock.pid"
LOGFILE="$REPO/data/daemon.log"
ERRLOG="$REPO/data/daemon-err.log"
DAEMON_CMD="$PYTHON -u -m zsiga daemon --port=58175"
export PYTHONPATH="$REPO"
export ZSIGA_HOME="$REPO"
export PYTHONUNBUFFERED=1  # ensure daemon log shows print output in real time

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

get_pid() {
    if [ -f "$PIDFILE" ]; then
        cat "$PIDFILE" 2>/dev/null
    fi
}

is_running() {
    local pid
    pid=$(get_pid)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    fi
    # Also check by process pattern
    pgrep -f "zsiga daemon" 2>/dev/null | head -1
    return 1
}

do_start() {
    if is_running >/dev/null 2>&1; then
        local pid
        pid=$(pgrep -f "zsiga daemon" | head -1)
        echo -e "${YELLOW}zsiga already running (PID $pid)${NC}"
        return 1
    fi

    echo "Starting zsiga daemon..."
    mkdir -p "$REPO/data"
    cd $REPO && nohup $DAEMON_CMD >> "$LOGFILE" 2>> "$ERRLOG" &
    local pid=$!
    sleep 2

    if kill -0 "$pid" 2>/dev/null; then
        echo -e "${GREEN}✓ zsiga started (PID $pid)${NC}"
        echo "  Log: tail -f $LOGFILE"
        echo "  Dashboard: http://49.234.48.221:58175/dashboard.html"
    else
        echo -e "${RED}✗ Failed to start. Check $ERRLOG${NC}"
        return 1
    fi
}

do_stop() {
    local pid
    pid=$(pgrep -f "zsiga daemon" | head -1)
    if [ -z "$pid" ]; then
        echo -e "${YELLOW}zsiga not running${NC}"
        return 0
    fi

    echo "Stopping zsiga (PID $pid)..."
    kill "$pid" 2>/dev/null || true

    # Wait up to 30s for graceful shutdown
    local waited=0
    while kill -0 "$pid" 2>/dev/null && [ $waited -lt 30 ]; do
        sleep 1
        waited=$((waited + 1))
    done

    if kill -0 "$pid" 2>/dev/null; then
        echo "Force killing..."
        kill -9 "$pid" 2>/dev/null || true
    fi

    echo -e "${GREEN}✓ zsiga stopped${NC}"
}

do_restart() {
    do_stop
    sleep 2
    do_start
}

do_status() {
    local pid
    pid=$(pgrep -f "zsiga daemon" | head -1)
    if [ -n "$pid" ]; then
        echo -e "${GREEN}● zsiga running (PID $pid)${NC}"
        # Show state
        if [ -f "$REPO/data/daemon_state.json" ]; then
            python3 -c "
import json
s = json.load(open('$REPO/data/daemon_state.json'))
print(f\"  Cycle: {s.get('cycle', '?')}\")
print(f\"  State: {s.get('state', '?')}\")
print(f\"  Current: {s.get('current_change') or 'idle'}\")
print(f\"  Phase: {s.get('current_phase') or '-'}\")
print(f\"  Last heartbeat: {s.get('last_heartbeat', '?')[:19]}\")
print(f\"  Total processed: {s.get('total_changes_processed', '?')}\")
" 2>/dev/null || echo "  (state file unreadable)"
        fi
    else
        echo -e "${RED}○ zsiga not running${NC}"
    fi
}

do_log() {
    local n="${1:-50}"
    tail -n "$n" "$LOGFILE"
}

do_tail() {
    tail -f "$LOGFILE" "$ERRLOG" 2>/dev/null
}

case "${1:-}" in
    start)   do_start ;;
    stop)    do_stop ;;
    restart) do_restart ;;
    status)  do_status ;;
    log)     do_log "${2:-50}" ;;
    tail)    do_tail ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|log [N]|tail}"
        echo ""
        echo "  start    Start zsiga daemon"
        echo "  stop     Stop zsiga daemon (graceful SIGTERM, then SIGKILL)"
        echo "  restart  Stop + start"
        echo "  status   Show daemon PID, cycle, current change"
        echo "  log [N]  Show last N lines of log (default 50)"
        echo "  tail     Follow daemon log in real-time"
        exit 1
        ;;
esac
