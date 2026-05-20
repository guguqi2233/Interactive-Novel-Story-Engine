#!/usr/bin/env bash
set -euo pipefail

BACKEND_HOST="127.0.0.1"
BACKEND_PORT="8000"
FRONTEND_PORT="5173"
NO_BROWSER="false"
USE_BUILT_FRONTEND="false"
SKIP_DEPENDENCY_CHECK="false"
SKIP_STARTUP_DIAGNOSTICS="false"
PREFLIGHT_ONLY="false"
HEALTH_TIMEOUT_SECONDS="30"

show_help() {
  cat <<'EOF'
Local Studio Launcher Pro

Usage:
  bash scripts/start_local_studio.sh [options]

Options:
  --backend-host <host>              Backend host. Default: 127.0.0.1
  --backend-port <port>              Backend port. Default: 8000
  --frontend-port <port>             Frontend port. Default: 5173
  --use-built-frontend               Serve frontend/dist with npm preview instead of Vite dev.
  --no-browser                       Do not open the browser automatically.
  --skip-dependency-check            Skip Python/npm/dependency/port checks.
  --skip-startup-diagnostics         Skip the safe startup diagnostics CLI.
  --preflight-only                   Run checks and exit without starting processes.
  --health-timeout-seconds <seconds> Health-check timeout. Default: 30
  --help                             Show this help.

Safety:
  The launcher never reads, prints, or injects LLM_API_KEY into frontend env.
  It only passes VITE_API_BASE_URL to the frontend process.
  It writes logs to local logs/, which is ignored by git.
  It does not modify GameState, saves, databases, worlds, or content packs.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --help|-h)
      show_help
      exit 0
      ;;
    --backend-host)
      BACKEND_HOST="${2:?missing backend host}"
      shift 2
      ;;
    --backend-port)
      BACKEND_PORT="${2:?missing backend port}"
      shift 2
      ;;
    --frontend-port)
      FRONTEND_PORT="${2:?missing frontend port}"
      shift 2
      ;;
    --use-built-frontend)
      USE_BUILT_FRONTEND="true"
      shift
      ;;
    --no-browser)
      NO_BROWSER="true"
      shift
      ;;
    --skip-dependency-check)
      SKIP_DEPENDENCY_CHECK="true"
      shift
      ;;
    --skip-startup-diagnostics)
      SKIP_STARTUP_DIAGNOSTICS="true"
      shift
      ;;
    --preflight-only)
      PREFLIGHT_ONLY="true"
      shift
      ;;
    --health-timeout-seconds)
      HEALTH_TIMEOUT_SECONDS="${2:?missing health timeout seconds}"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FRONTEND_ROOT="${REPO_ROOT}/frontend"
LOGS_ROOT="${REPO_ROOT}/logs"
mkdir -p "${LOGS_ROOT}"

require_command() {
  local name="$1"
  local hint="$2"
  if ! command -v "${name}" >/dev/null 2>&1; then
    echo "Missing required command '${name}'. ${hint}" >&2
    exit 1
  fi
}

require_path() {
  local path="$1"
  local message="$2"
  if [ ! -e "${path}" ]; then
    echo "${message}" >&2
    exit 1
  fi
}

require_python_version() {
  local version
  version="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' || {
    echo "Python 3.11+ is required. Found Python ${version}." >&2
    exit 1
  }
}

require_npm_available() {
  local version
  version="$(npm --version)"
  if [ -z "${version}" ]; then
    echo "npm was found but did not report a version." >&2
    exit 1
  fi
}

http_ok() {
  local url="$1"
  python -c "import sys, urllib.request; url=sys.argv[1]; req=urllib.request.Request(url); resp=urllib.request.urlopen(req, timeout=3); sys.exit(0 if 200 <= resp.status < 500 else 1)" "${url}" >/dev/null 2>&1
}

wait_http_ok() {
  local url="$1"
  local timeout_seconds="$2"
  local deadline=$(( $(date +%s) + timeout_seconds ))
  while [ "$(date +%s)" -lt "${deadline}" ]; do
    if http_ok "${url}"; then
      return 0
    fi
    sleep 0.75
  done
  return 1
}

port_available() {
  local host="$1"
  local port="$2"
  python -c "import socket, sys; host=sys.argv[1]; port=int(sys.argv[2]); sock=socket.socket(); sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); 
try:
    sock.bind((host, port))
except OSError:
    sys.exit(1)
finally:
    sock.close()
sys.exit(0)" "${host}" "${port}" >/dev/null 2>&1
}

require_port_available() {
  local host="$1"
  local port="$2"
  local service="$3"
  if ! port_available "${host}" "${port}"; then
    echo "${service} port ${port} on ${host} is already in use. Stop the existing process or rerun with a different port." >&2
    exit 1
  fi
}

export DATABASE_URL="${DATABASE_URL:-sqlite:///./world_engine.db}"
if [ -z "${DATABASE_URL}" ]; then
  echo "DATABASE_URL is empty. Set DATABASE_URL or copy .env.example to .env and configure a local SQLite URL." >&2
  exit 1
fi
export LLM_PROVIDER="${LLM_PROVIDER:-mock}"
export ENABLE_DEBUG_API="${ENABLE_DEBUG_API:-true}"
export ENABLE_AUTHORING_API="${ENABLE_AUTHORING_API:-false}"
export ENABLE_PERF_LOGGING="${ENABLE_PERF_LOGGING:-false}"
export VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://${BACKEND_HOST}:${BACKEND_PORT}}"
export PYTHONPATH="backend${PYTHONPATH:+:${PYTHONPATH}}"

if [ "${SKIP_STARTUP_DIAGNOSTICS}" != "true" ]; then
  echo "Running safe startup diagnostics..."
  if ! (
    cd "${REPO_ROOT}"
    PYTHONPATH="backend${PYTHONPATH:+:${PYTHONPATH}}" python -m backend.app.tools.startup_diagnostics --backend-port "${BACKEND_PORT}" --frontend-port "${FRONTEND_PORT}"
  ); then
    echo "Startup diagnostics reported blockers or warnings. Review the report above before continuing."
  fi
fi

if [ "${SKIP_DEPENDENCY_CHECK}" != "true" ]; then
  require_command "python" "Install Python 3.11+ and make sure it is available on PATH."
  require_python_version
  require_command "npm" "Install Node.js/npm and run npm install in frontend/."
  require_npm_available
  require_path "${REPO_ROOT}/pyproject.toml" "pyproject.toml was not found. Run the launcher from this repository."
  require_path "${FRONTEND_ROOT}/package.json" "frontend/package.json was not found."
  require_path "${FRONTEND_ROOT}/node_modules" "frontend/node_modules was not found. Run: cd frontend && npm install"
  (
    cd "${REPO_ROOT}"
    PYTHONPATH="backend${PYTHONPATH:+:${PYTHONPATH}}" python -c "import fastapi, uvicorn, pydantic; import app.main"
  )
  if [ "${USE_BUILT_FRONTEND}" = "true" ]; then
    require_path "${FRONTEND_ROOT}/dist/index.html" "frontend/dist was not found. Run: cd frontend && npm run build"
  fi
  require_port_available "${BACKEND_HOST}" "${BACKEND_PORT}" "Backend"
  require_port_available "127.0.0.1" "${FRONTEND_PORT}" "Frontend"
fi

if [ ! -f "${REPO_ROOT}/.env" ]; then
  echo "No .env file found. Continuing with safe local defaults."
  echo "To customize, copy .env.example to .env and keep it untracked: cp .env.example .env"
fi

BACKEND_OUT="${LOGS_ROOT}/desktop-backend.out.log"
BACKEND_ERR="${LOGS_ROOT}/desktop-backend.err.log"
FRONTEND_OUT="${LOGS_ROOT}/desktop-frontend.out.log"
FRONTEND_ERR="${LOGS_ROOT}/desktop-frontend.err.log"

if [ "${USE_BUILT_FRONTEND}" = "true" ]; then
  FRONTEND_MODE="built preview"
  FRONTEND_CMD=(npm run preview -- --host 127.0.0.1 --port "${FRONTEND_PORT}")
else
  FRONTEND_MODE="vite dev"
  FRONTEND_CMD=(npm run dev -- --host 127.0.0.1 --port "${FRONTEND_PORT}")
fi

FRONTEND_URL="http://127.0.0.1:${FRONTEND_PORT}"
echo "Local Studio Launcher Pro starting."
echo "Backend:  http://${BACKEND_HOST}:${BACKEND_PORT}"
echo "Frontend: ${FRONTEND_URL}"
echo "Frontend mode: ${FRONTEND_MODE}"
echo "Logs:     ${LOGS_ROOT}"
echo "LLM_PROVIDER: ${LLM_PROVIDER}"
echo "DATABASE_URL configured: yes"
echo "Authoring API: ${ENABLE_AUTHORING_API}"
echo "Debug API:     ${ENABLE_DEBUG_API}"
echo "Perf logging:  ${ENABLE_PERF_LOGGING}"
echo "VITE_API_BASE_URL: ${VITE_API_BASE_URL}"
echo "LLM_API_KEY is not read by this script and is never written to logs by the launcher."
echo "Frontend env safety: only VITE_API_BASE_URL is passed to the frontend process."
echo "State safety: launcher does not modify GameState, saves, databases, worlds, or content packs."
if [ "${LLM_PROVIDER}" = "openai" ] && [ -z "${LLM_API_KEY:-}" ]; then
  echo "Warning: LLM_PROVIDER=openai but LLM_API_KEY is not set. Use mock/local_stub for offline local startup."
fi
if [ "${LLM_PROVIDER}" = "local_http" ] && [ -z "${LOCAL_LLM_BASE_URL:-}" ]; then
  echo "Warning: LLM_PROVIDER=local_http but LOCAL_LLM_BASE_URL is not set. The local model provider will fail until configured."
fi
echo "Safety: do not expose these local-only authoring/debug/perf APIs outside trusted localhost."

if [ "${PREFLIGHT_ONLY}" = "true" ]; then
  echo "Preflight complete. No processes were started because --preflight-only was set."
  exit 0
fi

(
  cd "${REPO_ROOT}"
  python -m uvicorn app.main:app --host "${BACKEND_HOST}" --port "${BACKEND_PORT}"
) >"${BACKEND_OUT}" 2>"${BACKEND_ERR}" &

(
  cd "${FRONTEND_ROOT}"
  "${FRONTEND_CMD[@]}"
) >"${FRONTEND_OUT}" 2>"${FRONTEND_ERR}" &

BACKEND_HEALTH_URL="http://${BACKEND_HOST}:${BACKEND_PORT}/health"
STUDIO_STATUS_URL="http://${BACKEND_HOST}:${BACKEND_PORT}/studio/status"
echo "Waiting for backend health: ${BACKEND_HEALTH_URL}"
if wait_http_ok "${BACKEND_HEALTH_URL}" "${HEALTH_TIMEOUT_SECONDS}"; then
  echo "Backend /health: ok"
else
  echo "Backend /health: not ready within ${HEALTH_TIMEOUT_SECONDS}s. Check ${BACKEND_ERR}"
fi

echo "Checking studio status: ${STUDIO_STATUS_URL}"
if wait_http_ok "${STUDIO_STATUS_URL}" "5"; then
  echo "Studio status: reachable"
else
  echo "Studio status: unavailable. Backend may still be starting."
fi

echo "Waiting for frontend: ${FRONTEND_URL}"
if wait_http_ok "${FRONTEND_URL}" "${HEALTH_TIMEOUT_SECONDS}"; then
  echo "Frontend: reachable"
else
  echo "Frontend: not ready within ${HEALTH_TIMEOUT_SECONDS}s. Check ${FRONTEND_ERR}"
fi

if [ "${NO_BROWSER}" != "true" ]; then
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "${FRONTEND_URL}" >/dev/null 2>&1 || true
  elif command -v open >/dev/null 2>&1; then
    open "${FRONTEND_URL}" >/dev/null 2>&1 || true
  else
    echo "No browser opener found. Open ${FRONTEND_URL} manually."
  fi
fi
