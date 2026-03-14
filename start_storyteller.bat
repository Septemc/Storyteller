@echo off
setlocal

set SCRIPT_DIR=%~dp0
powershell.exe -ExecutionPolicy Bypass -File "%SCRIPT_DIR%scripts\restart_backend.ps1"

endlocal
