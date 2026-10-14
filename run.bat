@echo off
setlocal EnableDelayedExpansion EnableExtensions
cd /d "%~dp0"

REM ============================================================
REM  VoiceChat — one-click setup + run for Windows
REM  Usage:  run.bat [--http] [--port N]
REM    --http    run without TLS (localhost only for mic/camera)
REM    --port N  override the default port (8000 HTTP / 8443 HTTPS)
REM ============================================================

title VoiceChat

REM ---------- args ----------
set "USE_HTTP=0"
set "PORT_OVERRIDE="
:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="--http"  ( set "USE_HTTP=1" & shift & goto parse_args )
if /i "%~1"=="--port"  ( set "PORT_OVERRIDE=%~2" & shift & shift & goto parse_args )
if /i "%~1"=="-h"      goto show_help
if /i "%~1"=="--help"  goto show_help
echo Unknown option: %~1
exit /b 2
:show_help
echo.
echo VoiceChat launcher
echo.
echo Usage:
echo   run.bat              Start with HTTPS on port 8443 (recommended)
echo   run.bat --http       Start with HTTP on port 8000 (localhost only)
echo   run.bat --port 9000  Use a custom port
echo.
echo The first run creates venv\, installs dependencies, and (for HTTPS^)
echo generates a self-signed certificate with make_cert.py.
echo.
exit /b 0
:args_done

REM ---------- enable ANSI color (Windows 10+) ----------
for /f "tokens=4-5 delims=. " %%i in ('ver') do set "WINVER=%%i.%%j"
reg query "HKCU\Console" /v VirtualTerminalLevel >nul 2>&1
if errorlevel 1 (
    reg add "HKCU\Console" /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1
)
REM Force-enable for this window
>nul 2>&1 echo ;\033[0m

REM ANSI escape shortcuts (using ESC char via for /f)
for /f %%e in ('echo prompt $E^| cmd') do set "ESC=%%e"
set "BOLD=%ESC%[1m"
set "DIM=%ESC%[2m"
set "RED=%ESC%[31m"
set "GRN=%ESC%[32m"
set "YEL=%ESC%[33m"
set "CYA=%ESC%[36m"
set "RST=%ESC%[0m"

echo.
echo %CYA%%BOLD%==========================================%RST%
echo %CYA%%BOLD%   VoiceChat - Setup ^& Run%RST%
echo %CYA%%BOLD%==========================================%RST%
echo.

REM ---------- 1. find python ----------
set "PY="
REM Prefer py launcher (handles multiple installs correctly)
where py >nul 2>&1 && (
    py -3 -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>&1
    if not errorlevel 1 set "PY=py -3"
)
REM Fall back to python on PATH
if not defined PY (
    where python >nul 2>&1 && (
        python -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>&1
        if not errorlevel 1 set "PY=python"
    )
)
if not defined PY (
    echo %RED%%BOLD%[X]%RST% Python 3.10+ not found.
    echo     Install it from https://www.python.org/downloads/
    echo     Make sure "Add Python to PATH" is checked during install.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('%PY% --version 2^>^&1') do set "PYVER=%%v"
echo %GRN%%BOLD%[1/6]%RST% Python: %BOLD%%PY%%RST% ^(%PYVER%^)

REM ---------- 2. venv ----------
if exist "venv\Scripts\python.exe" (
    echo %GRN%%BOLD%[2/6]%RST% venv already exists - skipping
) else (
    echo %GRN%%BOLD%[2/6]%RST% Creating venv...
    %PY% -m venv venv
    if errorlevel 1 (
        echo %RED%%BOLD%[X]%RST% venv creation failed.
        pause
        exit /b 1
    )
)
set "VPY=%~dp0venv\Scripts\python.exe"
if not exist "%VPY%" (
    echo %RED%%BOLD%[X]%RST% venv python missing at %VPY%
    pause
    exit /b 1
)

REM ---------- 3. pip upgrade ----------
echo %GRN%%BOLD%[3/6]%RST% Upgrading pip...
"%VPY%" -m pip install --upgrade pip --quiet --disable-pip-version-check
if errorlevel 1 echo %YEL%%BOLD%[!]%RST% pip upgrade failed - continuing

REM ---------- 4. requirements ----------
if not exist "requirements.txt" (
    echo %YEL%%BOLD%[!]%RST% requirements.txt missing - writing default
    (
        echo fastapi==0.115.6
        echo uvicorn==0.34.0
        echo websockets==14.1
        echo python-multipart==0.0.20
        echo cryptography==44.0.0
    ) > requirements.txt
)
echo %GRN%%BOLD%[4/6]%RST% Installing dependencies...
"%VPY%" -m pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo %RED%%BOLD%[X]%RST% Dependency installation failed.
    echo     Run it manually to see the full error:
    echo       venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM ---------- 5. certs ----------
set "WANT_HTTPS=1"
if "%USE_HTTP%"=="1" set "WANT_HTTPS=0"

if "%WANT_HTTPS%"=="1" (
    if exist "cert.pem" if exist "key.pem" (
        echo %GRN%%BOLD%[5/6]%RST% TLS certs already exist - skipping
    ) else if exist "make_cert.py" (
        echo %GRN%%BOLD%[5/6]%RST% Generating self-signed TLS certificate...
        "%VPY%" make_cert.py
        if errorlevel 1 (
            echo %YEL%%BOLD%[!]%RST% Cert generation failed - falling back to HTTP
            set "WANT_HTTPS=0"
        )
    ) else (
        echo %YEL%%BOLD%[!]%RST% make_cert.py not found - falling back to HTTP
        set "WANT_HTTPS=0"
    )
) else (
    echo %GRN%%BOLD%[5/6]%RST% HTTP mode requested - no certs needed
)

REM ---------- detect LAN IP (best effort) ----------
set "LAN_IP="
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    if not defined LAN_IP (
        set "LANIP=%%a"
        set "LANIP=!LANIP: =!"
        REM Skip 127.x
        echo !LANIP! | findstr /b "127." >nul || set "LAN_IP=!LANIP!"
    )
)

REM ---------- 6. run ----------
set "SCHEME=http"
set "PORT=8000"
set "SERVER_ARGS=server.py"
if "%WANT_HTTPS%"=="1" (
    set "SCHEME=https"
    set "PORT=8443"
    set "SERVER_ARGS=server.py --ssl-keyfile key.pem --ssl-certfile cert.pem"
)
if defined PORT_OVERRIDE set "PORT=%PORT_OVERRIDE%"

echo.
echo %CYA%%BOLD%==========================================%RST%
echo %CYA%%BOLD%   Starting server...%RST%
echo %CYA%%BOLD%==========================================%RST%
echo.
echo    Mode       : %BOLD%%SCHEME%%RST%
echo    URL        : %BOLD%%SCHEME%://localhost:%PORT%%RST%
if defined LAN_IP echo    LAN        : %BOLD%%SCHEME%://%LAN_IP%:%PORT%%RST%
if "%SCHEME%"=="http" echo    %DIM%Note: mic/cam need https:// or http://localhost%RST%
echo.
echo    Press %BOLD%Ctrl+C%RST% to stop the server.
echo.

REM ---------- run (foreground) ----------
"%VPY%" %SERVER_ARGS% --port %PORT%

echo.
echo %YEL%%BOLD%Server stopped.%RST%
pause
endlocal