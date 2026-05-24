#!/usr/bin/env sh
set -eu

if [ "$#" -lt 1 ]; then
  echo "Usage: scripts/run_tool.sh <tool> [args...]" >&2
  exit 2
fi

TOOL="$1"
shift

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"

case "$TOOL" in
  compatibility_matrix) MODULE="app.tools.compatibility_matrix" ;;
  generate_contract_docs) MODULE="app.tools.generate_contract_docs" ;;
  v2_compatibility_checklist) MODULE="app.tools.v2_compatibility_checklist" ;;
  v2_release_checklist) MODULE="app.tools.v2_release_checklist" ;;
  v2_release_candidate_checklist) MODULE="app.tools.v2_release_candidate_checklist" ;;
  project_quality_gate) MODULE="app.tools.project_quality_gate" ;;
  mod_quality_gate) MODULE="app.tools.mod_quality_gate" ;;
  module_quality_gate) MODULE="app.tools.module_quality_gate" ;;
  module_quality_gate_v27) MODULE="app.tools.module_quality_gate_v27" ;;
  quality_gate) MODULE="app.tools.quality_gate" ;;
  validate_world) MODULE="app.tools.validate_world" ;;
  validate_project) MODULE="app.tools.validate_project" ;;
  validate_cross_mode) MODULE="app.tools.validate_cross_mode" ;;
  provider_benchmark) MODULE="app.tools.provider_benchmark" ;;
  playtest) MODULE="app.tools.playtest" ;;
  playtest_batch) MODULE="app.tools.playtest_batch" ;;
  benchmark) MODULE="app.tools.benchmark" ;;
  prompt_regression) MODULE="app.tools.prompt_regression" ;;
  release_checklist) MODULE="app.tools.release_checklist" ;;
  *)
    echo "Unsupported tool '$TOOL'." >&2
    echo "Supported tools: compatibility_matrix generate_contract_docs v2_compatibility_checklist v2_release_checklist v2_release_candidate_checklist project_quality_gate mod_quality_gate module_quality_gate module_quality_gate_v27 quality_gate validate_world validate_project validate_cross_mode provider_benchmark playtest playtest_batch benchmark prompt_regression release_checklist" >&2
    exit 2
    ;;
esac

cd "$REPO_ROOT"
PYTHONPATH="$REPO_ROOT/backend" python -m "$MODULE" "$@"
