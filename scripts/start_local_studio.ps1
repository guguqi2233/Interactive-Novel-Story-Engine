param(
    [string]$BackendHost = "127.0.0.1",
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$FrontendRoot = Join-Path $RepoRoot "frontend"
$LogsRoot = Join-Path $RepoRoot "logs"
New-Item -ItemType Directory -Force -Path $LogsRoot | Out-Null

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
if (-not $env:VITE_API_BASE_URL) {
    $env:VITE_API_BASE_URL = "http://${BackendHost}:${BackendPort}"
}

$BackendOut = Join-Path $LogsRoot "desktop-backend.out.log"
$BackendErr = Join-Path $LogsRoot "desktop-backend.err.log"
$FrontendOut = Join-Path $LogsRoot "desktop-frontend.out.log"
$FrontendErr = Join-Path $LogsRoot "desktop-frontend.err.log"

$BackendCommand = @"
`$env:PYTHONPATH='backend'
`$env:DATABASE_URL='$($env:DATABASE_URL)'
`$env:LLM_PROVIDER='$($env:LLM_PROVIDER)'
`$env:ENABLE_DEBUG_API='$($env:ENABLE_DEBUG_API)'
`$env:ENABLE_AUTHORING_API='$($env:ENABLE_AUTHORING_API)'
python -m uvicorn app.main:app --host $BackendHost --port $BackendPort
"@

$FrontendCommand = @"
`$env:VITE_API_BASE_URL='$($env:VITE_API_BASE_URL)'
npm run dev -- --host 127.0.0.1 --port $FrontendPort
"@

Start-Process powershell -WindowStyle Hidden -WorkingDirectory $RepoRoot `
    -RedirectStandardOutput $BackendOut `
    -RedirectStandardError $BackendErr `
    -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $BackendCommand

Start-Process powershell -WindowStyle Hidden -WorkingDirectory $FrontendRoot `
    -RedirectStandardOutput $FrontendOut `
    -RedirectStandardError $FrontendErr `
    -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $FrontendCommand

$FrontendUrl = "http://127.0.0.1:$FrontendPort"
Write-Host "Local studio prototype starting."
Write-Host "Backend:  http://${BackendHost}:${BackendPort}"
Write-Host "Frontend: $FrontendUrl"
Write-Host "Logs:     $LogsRoot"
Write-Host "LLM_PROVIDER is read from your environment or defaults to mock."
Write-Host "LLM_API_KEY is not read by this script and is never written to logs by the launcher."

if (-not $NoBrowser) {
    Start-Process $FrontendUrl
}
