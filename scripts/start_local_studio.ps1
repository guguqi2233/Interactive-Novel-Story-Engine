param(
    [string]$BackendHost = "127.0.0.1",
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [switch]$UseBuiltFrontend,
    [switch]$NoBrowser,
    [switch]$SkipDependencyCheck,
    [switch]$PreflightOnly
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$FrontendRoot = Join-Path $RepoRoot "frontend"
$LogsRoot = Join-Path $RepoRoot "logs"
New-Item -ItemType Directory -Force -Path $LogsRoot | Out-Null

function Test-CommandAvailable {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Assert-Dependency {
    param(
        [string]$Name,
        [string]$InstallHint
    )
    if (-not (Test-CommandAvailable $Name)) {
        throw "Missing required command '$Name'. $InstallHint"
    }
}

function Assert-PathExists {
    param(
        [string]$Path,
        [string]$Message
    )
    if (-not (Test-Path $Path)) {
        throw $Message
    }
}

if (-not $env:DATABASE_URL) {
    $env:DATABASE_URL = "sqlite:///./world_engine.db"
}
if (-not $env:LLM_PROVIDER) {
    $env:LLM_PROVIDER = "mock"
}
if (-not $env:ENABLE_DEBUG_API) {
    $env:ENABLE_DEBUG_API = "true"
}
if (-not $env:ENABLE_AUTHORING_API) {
    $env:ENABLE_AUTHORING_API = "false"
}
if (-not $env:ENABLE_PERF_LOGGING) {
    $env:ENABLE_PERF_LOGGING = "false"
}
if (-not $env:VITE_API_BASE_URL) {
    $env:VITE_API_BASE_URL = "http://${BackendHost}:${BackendPort}"
}

if (-not $SkipDependencyCheck) {
    Assert-Dependency "python" "Install Python 3.11+ and make sure it is available on PATH."
    Assert-Dependency "npm" "Install Node.js/npm and run npm install in frontend/."
    Assert-PathExists (Join-Path $RepoRoot "pyproject.toml") "pyproject.toml was not found. Run the launcher from this repository."
    Assert-PathExists (Join-Path $FrontendRoot "package.json") "frontend/package.json was not found."
    Assert-PathExists (Join-Path $FrontendRoot "node_modules") "frontend/node_modules was not found. Run: cd frontend; npm install"
    if ($UseBuiltFrontend) {
        Assert-PathExists (Join-Path $FrontendRoot "dist/index.html") "frontend/dist was not found. Run: cd frontend; npm run build"
    }
}

$BackendOut = Join-Path $LogsRoot "desktop-backend.out.log"
$BackendErr = Join-Path $LogsRoot "desktop-backend.err.log"
$FrontendOut = Join-Path $LogsRoot "desktop-frontend.out.log"
$FrontendErr = Join-Path $LogsRoot "desktop-frontend.err.log"
$FrontendMode = if ($UseBuiltFrontend) { "built preview" } else { "vite dev" }

$BackendCommand = @"
`$env:PYTHONPATH='backend'
`$env:DATABASE_URL='$($env:DATABASE_URL)'
`$env:LLM_PROVIDER='$($env:LLM_PROVIDER)'
`$env:ENABLE_DEBUG_API='$($env:ENABLE_DEBUG_API)'
`$env:ENABLE_AUTHORING_API='$($env:ENABLE_AUTHORING_API)'
`$env:ENABLE_PERF_LOGGING='$($env:ENABLE_PERF_LOGGING)'
`$env:LOCAL_LLM_BASE_URL='$($env:LOCAL_LLM_BASE_URL)'
`$env:LOCAL_LLM_MODEL='$($env:LOCAL_LLM_MODEL)'
`$env:LOCAL_LLM_TIMEOUT_SECONDS='$($env:LOCAL_LLM_TIMEOUT_SECONDS)'
`$env:LOCAL_LLM_JSON_MODE='$($env:LOCAL_LLM_JSON_MODE)'
python -m uvicorn app.main:app --host $BackendHost --port $BackendPort
"@

if ($UseBuiltFrontend) {
    $FrontendCommand = @"
`$env:VITE_API_BASE_URL='$($env:VITE_API_BASE_URL)'
npm run preview -- --host 127.0.0.1 --port $FrontendPort
"@
} else {
    $FrontendCommand = @"
`$env:VITE_API_BASE_URL='$($env:VITE_API_BASE_URL)'
npm run dev -- --host 127.0.0.1 --port $FrontendPort
"@
}

$FrontendUrl = "http://127.0.0.1:$FrontendPort"
Write-Host "Local studio prototype starting."
Write-Host "Backend:  http://${BackendHost}:${BackendPort}"
Write-Host "Frontend: $FrontendUrl"
Write-Host "Frontend mode: $FrontendMode"
Write-Host "Logs:     $LogsRoot"
Write-Host "LLM_PROVIDER: $($env:LLM_PROVIDER)"
Write-Host "Authoring API: $($env:ENABLE_AUTHORING_API)"
Write-Host "Debug API:     $($env:ENABLE_DEBUG_API)"
Write-Host "Perf logging:  $($env:ENABLE_PERF_LOGGING)"
Write-Host "VITE_API_BASE_URL: $($env:VITE_API_BASE_URL)"
Write-Host "LLM_API_KEY is not read by this script and is never written to logs by the launcher."
Write-Host "Use -UseBuiltFrontend after running 'cd frontend; npm run build' to serve the built frontend."

if ($PreflightOnly) {
    Write-Host "Preflight complete. No processes were started because -PreflightOnly was set."
    exit 0
}

Start-Process powershell -WindowStyle Hidden -WorkingDirectory $RepoRoot `
    -RedirectStandardOutput $BackendOut `
    -RedirectStandardError $BackendErr `
    -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $BackendCommand

Start-Process powershell -WindowStyle Hidden -WorkingDirectory $FrontendRoot `
    -RedirectStandardOutput $FrontendOut `
    -RedirectStandardError $FrontendErr `
    -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $FrontendCommand

if (-not $NoBrowser) {
    Start-Process $FrontendUrl
}
