#!/usr/bin/env bash
set -euo pipefail

BACKEND_HOST="127.0.0.1"
BACKEND_PORT="8000"
FRONTEND_PORT="5173"
NO_BROWSER="false"
USE_BUILT_FRONTEND="false"
SKIP_DEPENDENCY_CHECK="false"
PREFLIGHT_ONLY="false"

while [ "$#" -gt 0 ]; do
  case "$1" in
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
    --preflight-only)
      PREFLIGHT_ONLY="true"
      shift
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

export DATABASE_URL="${DATABASE_URL:-sqlite:///./world_engine.db}"
export LLM_PROVIDER="${LLM_PROVIDER:-mock}"
export ENABLE_DEBUG_API="${ENABLE_DEBUG_API:-true}"
export ENABLE_AUTHORING_API="${ENABLE_AUTHORING_API:-false}"
export ENABLE_PERF_LOGGING="${ENABLE_PERF_LOGGING:-false}"
export VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://${BACKEND_HOST}:${BACKEND_PORT}}"
export PYTHONPATH="backend${PYTHONPATH:+:${PYTHONPATH}}"

if [ "${SKIP_DEPENDENCY_CHECK}" != "true" ]; then
  require_command "python" "Install Python 3.11+ and make sure it is available on PATH."
  require_command "npm" "Install Node.js/npm and run npm install in frontend/."
  require_path "${REPO_ROOT}/pyproject.toml" "pyproject.toml was not found. Run the launcher from this repository."
  require_path "${FRONTEND_ROOT}/package.json" "frontend/package.json was not found."
  require_path "${FRONTEND_ROOT}/node_modules" "frontend/node_modules was not found. Run: cd frontend && npm install"
  if [ "${USE_BUILT_FRONTEND}" = "true" ]; then
    require_path "${FRONTEND_ROOT}/dist/index.html" "frontend/dist was not found. Run: cd frontend && npm run build"
  fi
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
echo "Local studio prototype starting."
echo "Backend:  http://${BACKEND_HOST}:${BACKEND_PORT}"
echo "Frontend: ${FRONTEND_URL}"
echo "Frontend mode: ${FRONTEND_MODE}"
echo "Logs:     ${LOGS_ROOT}"
echo "LLM_PROVIDER: ${LLM_PROVIDER}"
echo "Authoring API: ${ENABLE_AUTHORING_API}"
echo "Debug API:     ${ENABLE_DEBUG_API}"
echo "Perf logging:  ${ENABLE_PERF_LOGGING}"
echo "VITE_API_BASE_URL: ${VITE_API_BASE_URL}"
echo "LLM_API_KEY is not read by this script and is never written to logs by the launcher."

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

if [ "${NO_BROWSER}" != "true" ]; then
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "${FRONTEND_URL}" >/dev/null 2>&1 || true
  elif command -v open >/dev/null 2>&1; then
    open "${FRONTEND_URL}" >/dev/null 2>&1 || true
  else
    echo "No browser opener found. Open ${FRONTEND_URL} manually."
  fi
fi
