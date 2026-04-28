@echo off
setlocal

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"

if "%LLM_PROVIDER%"=="" set "LLM_PROVIDER=mock"
if "%BACKEND_PORT%"=="" set "BACKEND_PORT=8010"
if "%FRONTEND_PORT%"=="" set "FRONTEND_PORT=3000"
if "%DATABASE_URL%"=="" set "DATABASE_URL=sqlite:///%ROOT:\=/%data/app.db"
if "%NEXT_PUBLIC_API_BASE_URL%"=="" set "NEXT_PUBLIC_API_BASE_URL=http://localhost:%BACKEND_PORT%"

call :find_free_port FRONTEND_PORT %FRONTEND_PORT%

if not exist "%ROOT%data" mkdir "%ROOT%data"

echo Starting Interactive Novel Story Engine...
echo.
echo Backend:  http://localhost:%BACKEND_PORT%/docs
echo Frontend: http://localhost:%FRONTEND_PORT%
echo Health:   http://localhost:%BACKEND_PORT%/api/health
echo.
echo Two terminal windows will open. Keep them running while using the app.
echo.

start "story-engine-backend" /D "%BACKEND%" cmd /k "python -m venv .venv && .venv\Scripts\python.exe -m pip install -r requirements.txt && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port %BACKEND_PORT%"
start "story-engine-frontend" /D "%FRONTEND%" cmd /k "npm.cmd install && set NEXT_PUBLIC_API_BASE_URL=%NEXT_PUBLIC_API_BASE_URL%&& npm.cmd run dev -- -p %FRONTEND_PORT%"

echo Startup commands sent. Open http://localhost:%FRONTEND_PORT% after the frontend finishes compiling.
pause
exit /b 0

:find_free_port
setlocal EnableDelayedExpansion
set "VAR_NAME=%~1"
set /a PORT=%~2
:check_port
netstat -ano | findstr /R /C:":!PORT! .*LISTENING" >nul
if not errorlevel 1 (
  set /a PORT+=1
  goto check_port
)
endlocal & set "%VAR_NAME%=%PORT%"
exit /b 0
