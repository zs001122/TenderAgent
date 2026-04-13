#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
RUNTIME_DIR="$ROOT_DIR/.runtime"
VENV_DIR="$ROOT_DIR/venv"
mkdir -p "$RUNTIME_DIR"
BACKEND_PID_FILE="$RUNTIME_DIR/backend.pid"
FRONTEND_PID_FILE="$RUNTIME_DIR/frontend.pid"
BACKEND_LOG_FILE="$RUNTIME_DIR/backend.log"
FRONTEND_LOG_FILE="$RUNTIME_DIR/frontend.log"
BACKEND_STARTED=0
FRONTEND_STARTED=0

BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
API_TARGET="http://localhost:$BACKEND_PORT"

usage() {
  echo "usage: bash $0 [start|stop|status|restart]"
}

read_pid() {
  local pid_file="$1"
  if [[ -f "$pid_file" ]]; then
    cat "$pid_file"
  else
    echo ""
  fi
}

is_running() {
  local pid="$1"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

is_port_in_use() {
  local port="$1"
  python3 - "$port" <<'PY'
import socket, sys
port = int(sys.argv[1])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(0.2)
try:
    code = s.connect_ex(("127.0.0.1", port))
    print("1" if code == 0 else "0")
finally:
    s.close()
PY
}

find_free_port() {
  local start_port="$1"
  python3 - "$start_port" <<'PY'
import socket, sys
port = int(sys.argv[1])
for p in range(port, port + 200):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.2)
    try:
        if s.connect_ex(("127.0.0.1", p)) != 0:
            print(p)
            break
    finally:
        s.close()
PY
}

ensure_backend_env() {
  if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
  fi
}

ensure_frontend_env() {
  if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    cd "$FRONTEND_DIR"
    npm install
  fi
}

start_backend() {
  local pid
  pid="$(read_pid "$BACKEND_PID_FILE")"
  if is_running "$pid"; then
    echo "backend_running pid=$pid"
    return 0
  fi
  cd "$BACKEND_DIR"
  "$VENV_DIR/bin/python" -m uvicorn app.main:app --reload --host "$BACKEND_HOST" --port "$BACKEND_PORT" > "$BACKEND_LOG_FILE" 2>&1 &
  echo "$!" > "$BACKEND_PID_FILE"
  BACKEND_STARTED=1
}

start_frontend() {
  local pid
  pid="$(read_pid "$FRONTEND_PID_FILE")"
  if is_running "$pid"; then
    echo "frontend_running pid=$pid"
    return 0
  fi
  cd "$FRONTEND_DIR"
  VITE_API_TARGET="$API_TARGET" npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" > "$FRONTEND_LOG_FILE" 2>&1 &
  echo "$!" > "$FRONTEND_PID_FILE"
  FRONTEND_STARTED=1
}

stop_process() {
  local name="$1"
  local pid_file="$2"
  local pid
  pid="$(read_pid "$pid_file")"
  if ! is_running "$pid"; then
    rm -f "$pid_file"
    echo "${name}_stopped"
    return 0
  fi
  kill "$pid" || true
  sleep 1
  if is_running "$pid"; then
    kill -9 "$pid" || true
  fi
  rm -f "$pid_file"
  echo "${name}_stopped pid=$pid"
}

status_process() {
  local name="$1"
  local pid_file="$2"
  local pid
  pid="$(read_pid "$pid_file")"
  if is_running "$pid"; then
    echo "${name}_running pid=$pid"
    return 0
  fi
  echo "${name}_stopped"
  return 1
}

start_all() {
  BACKEND_STARTED=0
  FRONTEND_STARTED=0
  local requested_backend_port="$BACKEND_PORT"
  local requested_frontend_port="$FRONTEND_PORT"
  if [[ "$(is_port_in_use "$BACKEND_PORT")" == "1" ]]; then
    BACKEND_PORT="$(find_free_port "$BACKEND_PORT")"
    echo "backend_port_switched from=$requested_backend_port to=$BACKEND_PORT"
  fi
  if [[ "$(is_port_in_use "$FRONTEND_PORT")" == "1" ]]; then
    FRONTEND_PORT="$(find_free_port "$FRONTEND_PORT")"
    echo "frontend_port_switched from=$requested_frontend_port to=$FRONTEND_PORT"
  fi
  API_TARGET="http://localhost:$BACKEND_PORT"
  ensure_backend_env
  ensure_frontend_env
  start_backend || exit 1
  if ! status_process "backend" "$BACKEND_PID_FILE" >/dev/null 2>&1; then
    if [[ "$BACKEND_STARTED" == "1" ]]; then
      stop_process "backend" "$BACKEND_PID_FILE" >/dev/null 2>&1 || true
    fi
    status_process "backend" "$BACKEND_PID_FILE" || true
    exit 1
  fi
  start_frontend || {
    if [[ "$BACKEND_STARTED" == "1" ]]; then
      stop_process "backend" "$BACKEND_PID_FILE" >/dev/null 2>&1 || true
    fi
    exit 1
  }
  sleep 1
  local backend_ok=0
  local frontend_ok=0
  status_process "backend" "$BACKEND_PID_FILE" || backend_ok=1
  status_process "frontend" "$FRONTEND_PID_FILE" || frontend_ok=1
  echo "backend_url=http://localhost:$BACKEND_PORT"
  echo "frontend_url=http://localhost:$FRONTEND_PORT"
  echo "api_docs=http://localhost:$BACKEND_PORT/docs"
  echo "frontend_api_target=$API_TARGET"
  echo "backend_log=$BACKEND_LOG_FILE"
  echo "frontend_log=$FRONTEND_LOG_FILE"
  if [[ $backend_ok -ne 0 || $frontend_ok -ne 0 ]]; then
    if [[ "$FRONTEND_STARTED" == "1" ]]; then
      stop_process "frontend" "$FRONTEND_PID_FILE" >/dev/null 2>&1 || true
    fi
    if [[ "$BACKEND_STARTED" == "1" ]]; then
      stop_process "backend" "$BACKEND_PID_FILE" >/dev/null 2>&1 || true
    fi
    exit 1
  fi
}

stop_all() {
  stop_process "backend" "$BACKEND_PID_FILE"
  stop_process "frontend" "$FRONTEND_PID_FILE"
}

status_all() {
  local backend_ok=0
  local frontend_ok=0
  status_process "backend" "$BACKEND_PID_FILE" || backend_ok=1
  status_process "frontend" "$FRONTEND_PID_FILE" || frontend_ok=1
  if [[ $backend_ok -ne 0 || $frontend_ok -ne 0 ]]; then
    exit 1
  fi
}

case "${1:-start}" in
  start)
    start_all
    ;;
  stop)
    stop_all
    ;;
  status)
    status_all
    ;;
  restart)
    stop_all
    start_all
    ;;
  *)
    usage
    exit 2
    ;;
esac
