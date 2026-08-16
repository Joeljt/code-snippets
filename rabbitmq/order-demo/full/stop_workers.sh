#!/usr/bin/env bash
# 停止 start_workers.sh 启动的后台 worker
set -euo pipefail
cd "$(dirname "$0")"

PIDFILE=".workers.pids"
if [[ ! -f "$PIDFILE" ]]; then
  echo "[*] No .workers.pids — workers not running?"
  exit 0
fi

while read -r pid; do
  kill "$pid" 2>/dev/null || true
done < "$PIDFILE"
rm -f "$PIDFILE"
echo "[*] Workers stopped."
