#!/usr/bin/env bash
# 一键启动全部 worker；日志写入 logs/<name>.log，本终端 tail 合并显示
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="python3"
if [[ -x "../../.venv/bin/python" ]]; then
  PYTHON="../../.venv/bin/python"
fi

mkdir -p logs
PIDFILE=".workers.pids"
rm -f "$PIDFILE"

run_worker() {
  local name=$1
  shift
  local logfile="logs/${name}.log"
  : > "$logfile"
  PYTHONUNBUFFERED=1 "$PYTHON" -u "$@" >> "$logfile" 2>&1 &
  echo $! >> "$PIDFILE"
  echo "[*] ${name} -> ${logfile}"
}

echo "[*] Starting workers (Ctrl+C to stop all)"
echo "[*] Python: ${PYTHON}"
echo "[*] 另开终端跑: cd full && python place_order.py && python pay.py <order_id>"
echo ""

run_worker timeout      workers/timeout_worker.py
run_worker bridge       workers/inventory_bridge.py
run_worker inventory    workers/inventory_worker.py
run_worker restore      workers/restore_worker.py
run_worker shipping     workers/shipping_worker.py
run_worker notify_sms   workers/notify_sms.py
run_worker notify_email workers/notify_email.py
run_worker notify_app   workers/notify_app.py
run_worker dlx          workers/dead_letter_worker.py
run_worker unroutable   workers/unroutable_worker.py

# 等 worker 连上 Broker 并写出首行日志
sleep 1

echo ""
echo "[*] Tailing logs (macOS tail 会标注 ==> logs/xxx.log <==) ..."
echo ""

LOGS=(logs/*.log)
cleanup() {
  echo ""
  echo "[*] Stopping workers ..."
  if [[ -f "$PIDFILE" ]]; then
    while read -r pid; do
      kill "$pid" 2>/dev/null || true
    done < "$PIDFILE"
    rm -f "$PIDFILE"
  fi
  jobs -p | xargs kill 2>/dev/null || true
  wait 2>/dev/null || true
  echo "[*] Done. 日志仍保留在 logs/ 目录。"
}
trap cleanup EXIT INT TERM

tail -F "${LOGS[@]}"
