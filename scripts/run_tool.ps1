param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Tool,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ToolArgs
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendPath = Join-Path $repoRoot "backend"

$allowlist = @{
    "compatibility_matrix" = "app.tools.compatibility_matrix"
    "generate_contract_docs" = "app.tools.generate_contract_docs"
    "v2_compatibility_checklist" = "app.tools.v2_compatibility_checklist"
    "v2_release_checklist" = "app.tools.v2_release_checklist"
    "v2_release_candidate_checklist" = "app.tools.v2_release_candidate_checklist"
    "project_quality_gate" = "app.tools.project_quality_gate"
    "mod_quality_gate" = "app.tools.mod_quality_gate"
    "module_quality_gate" = "app.tools.module_quality_gate"
    "module_quality_gate_v27" = "app.tools.module_quality_gate_v27"
    "quality_gate" = "app.tools.quality_gate"
    "validate_world" = "app.tools.validate_world"
    "validate_project" = "app.tools.validate_project"
    "validate_cross_mode" = "app.tools.validate_cross_mode"
    "provider_benchmark" = "app.tools.provider_benchmark"
    "playtest" = "app.tools.playtest"
    "playtest_batch" = "app.tools.playtest_batch"
    "benchmark" = "app.tools.benchmark"
    "prompt_regression" = "app.tools.prompt_regression"
    "release_checklist" = "app.tools.release_checklist"
}

if (-not $allowlist.ContainsKey($Tool)) {
    Write-Error "Unsupported tool '$Tool'. Supported tools: $($allowlist.Keys -join ', ')"
    exit 2
}

$env:PYTHONPATH = $backendPath
Set-Location $repoRoot

python -m $allowlist[$Tool] @ToolArgs
exit $LASTEXITCODE
