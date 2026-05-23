param(
    [string]$BackendHost = "127.0.0.1",
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [switch]$UseBuiltFrontend,
    [switch]$NoBrowser,
    [switch]$SkipDependencyCheck,
    [switch]$SkipStartupDiagnostics,
    [switch]$PreflightOnly,
    [switch]$Help,
    [int]$HealthTimeoutSeconds = 30
)

$ErrorActionPreference = "Stop"

function Show-Help {
    Write-Host @"
Local Studio Launcher Pro

Usage:
  .\scripts\start_local_studio.ps1 [options]

Options:
  -BackendHost <host>             Backend host. Default: 127.0.0.1
  -BackendPort <port>             Backend port. Default: 8000
  -FrontendPort <port>            Frontend port. Default: 5173
  -UseBuiltFrontend               Serve frontend/dist with npm preview instead of Vite dev.
  -NoBrowser                      Do not open the browser automatically.
  -SkipDependencyCheck            Skip Python/npm/dependency/port checks.
  -SkipStartupDiagnostics         Skip the safe startup diagnostics CLI.
  -PreflightOnly                  Run checks and exit without starting processes.
  -HealthTimeoutSeconds <seconds> Health-check timeout. Default: 30
  -Help                           Show this help.

Safety:
  The launcher never reads, prints, or injects LLM_API_KEY into frontend env.
  It only passes VITE_API_BASE_URL to the frontend process.
  It writes logs to local logs/, which is ignored by git.
  It does not modify GameState, saves, databases, worlds, or content packs.

PowerShell note:
  If PowerShell prints a profile signing warning before this script starts,
  it is usually a local profile policy warning and not a launcher failure.
  Run with powershell -NoProfile -ExecutionPolicy Bypass when needed.
"@
}

if ($Help) {
    Show-Help
    exit 0
}

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

function Assert-PythonVersion {
    $version = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    $parts = $version.Trim().Split(".")
    $major = [int]$parts[0]
    $minor = [int]$parts[1]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
        throw "Python 3.11+ is required. Found Python $version."
    }
}

function Assert-NpmAvailable {
    $version = & npm --version
    if ([string]::IsNullOrWhiteSpace($version)) {
        throw "npm was found but did not report a version."
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

function Test-HttpOk {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
        return ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500)
    } catch {
        return $false
    }
}

function Wait-HttpOk {
    param(
        [string]$Url,
        [int]$TimeoutSeconds
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-HttpOk $Url) {
            return $true
        }
        Start-Sleep -Milliseconds 750
    }
    return $false
}

function Test-PortAvailable {
    param(
        [string]$HostName,
        [int]$Port
    )
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse($HostName), $Port)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

function Assert-PortAvailable {
    param(
        [string]$HostName,
        [int]$Port,
        [string]$ServiceName
    )
    if (-not (Test-PortAvailable $HostName $Port)) {
        throw "$ServiceName port ${Port} on ${HostName} is already in use. Stop the existing process or rerun with a different port."
    }
}

if (-not $env:DATABASE_URL) {
    $env:DATABASE_URL = "sqlite:///./world_engine.db"
}
if ([string]::IsNullOrWhiteSpace($env:DATABASE_URL)) {
    throw "DATABASE_URL is empty. Set DATABASE_URL or copy .env.example to .env and configure a local SQLite URL."
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

if (-not $SkipStartupDiagnostics) {
    Push-Location $RepoRoot
    try {
        $env:PYTHONPATH = "backend"
        Write-Host "Running safe startup diagnostics..."
        python -m backend.app.tools.startup_diagnostics --backend-port $BackendPort --frontend-port $FrontendPort
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Startup diagnostics reported blockers or warnings. Review the report above before continuing."
        }
    } catch {
        Write-Host "Startup diagnostics could not run: $($_.Exception.Message)"
        Write-Host "Continuing with launcher checks. No secrets were read or printed by the launcher."
    } finally {
        Pop-Location
    }
}

if (-not $SkipDependencyCheck) {
    Assert-Dependency "python" "Install Python 3.11+ and make sure it is available on PATH."
    Assert-PythonVersion
    Assert-Dependency "npm" "Install Node.js/npm and run npm install in frontend/."
    Assert-NpmAvailable
    Assert-PathExists (Join-Path $RepoRoot "pyproject.toml") "pyproject.toml was not found. Run the launcher from this repository."
    Assert-PathExists (Join-Path $FrontendRoot "package.json") "frontend/package.json was not found."
    Assert-PathExists (Join-Path $FrontendRoot "node_modules") "frontend/node_modules was not found. Run: cd frontend; npm install"
    Push-Location $RepoRoot
    try {
        $env:PYTHONPATH = "backend"
        python -c "import fastapi, uvicorn, pydantic; import app.main" | Out-Null
    } finally {
        Pop-Location
    }
    if ($UseBuiltFrontend) {
        Assert-PathExists (Join-Path $FrontendRoot "dist/index.html") "frontend/dist was not found. Run: cd frontend; npm run build"
    }
    Assert-PortAvailable $BackendHost $BackendPort "Backend"
    Assert-PortAvailable "127.0.0.1" $FrontendPort "Frontend"
}

if (-not (Test-Path (Join-Path $RepoRoot ".env"))) {
    Write-Host "No .env file found. Continuing with safe local defaults."
    Write-Host "To customize, copy .env.example to .env and keep it untracked: Copy-Item .env.example .env"
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
Write-Host "Local Studio Launcher Pro starting."
Write-Host "Backend:  http://${BackendHost}:${BackendPort}"
Write-Host "Frontend: $FrontendUrl"
Write-Host "Frontend mode: $FrontendMode"
Write-Host "Logs:     $LogsRoot"
Write-Host "LLM_PROVIDER: $($env:LLM_PROVIDER)"
Write-Host "DATABASE_URL configured: $([bool]$env:DATABASE_URL)"
Write-Host "Authoring API: $($env:ENABLE_AUTHORING_API)"
Write-Host "Debug API:     $($env:ENABLE_DEBUG_API)"
Write-Host "Perf logging:  $($env:ENABLE_PERF_LOGGING)"
Write-Host "VITE_API_BASE_URL: $($env:VITE_API_BASE_URL)"
Write-Host "LLM_API_KEY is not read by this script and is never written to logs by the launcher."
Write-Host "Frontend env safety: only VITE_API_BASE_URL is passed to the frontend process."
Write-Host "State safety: launcher does not modify GameState, saves, databases, worlds, or content packs."
Write-Host "Local-first: no account, no cloud sync, no online marketplace, no telemetry upload."
Write-Host "PowerShell profile note: profile signing warnings are non-blocking launcher environment warnings."
if ($env:LLM_PROVIDER -eq "openai" -and -not $env:LLM_API_KEY) {
    Write-Host "Warning: LLM_PROVIDER=openai but LLM_API_KEY is not set. Use mock/local_stub for offline local startup."
}
if ($env:LLM_PROVIDER -eq "local_http" -and -not $env:LOCAL_LLM_BASE_URL) {
    Write-Host "Warning: LLM_PROVIDER=local_http but LOCAL_LLM_BASE_URL is not set. The local model provider will fail until configured."
}
Write-Host "Use -UseBuiltFrontend after running 'cd frontend; npm run build' to serve the built frontend."
Write-Host "Safety: do not expose these local-only authoring/debug/perf APIs outside trusted localhost."

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

$BackendHealthUrl = "http://${BackendHost}:${BackendPort}/health"
$StudioStatusUrl = "http://${BackendHost}:${BackendPort}/studio/status"
Write-Host "Waiting for backend health: $BackendHealthUrl"
if (Wait-HttpOk $BackendHealthUrl $HealthTimeoutSeconds) {
    Write-Host "Backend /health: ok"
} else {
    Write-Host "Backend /health: not ready within ${HealthTimeoutSeconds}s. Check $BackendErr"
}

Write-Host "Checking studio status: $StudioStatusUrl"
if (Wait-HttpOk $StudioStatusUrl 5) {
    Write-Host "Studio status: reachable"
} else {
    Write-Host "Studio status: unavailable. Backend may still be starting."
}

Write-Host "Waiting for frontend: $FrontendUrl"
if (Wait-HttpOk $FrontendUrl $HealthTimeoutSeconds) {
    Write-Host "Frontend: reachable"
} else {
    Write-Host "Frontend: not ready within ${HealthTimeoutSeconds}s. Check $FrontendErr"
}

if (-not $NoBrowser) {
    Start-Process $FrontendUrl
}
