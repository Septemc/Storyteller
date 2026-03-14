param(
    [int]$Port = 8010,
    [string]$PythonExe = "",
    [switch]$NoReload
)

$ErrorActionPreference = 'Stop'

function Write-Step($message) {
    Write-Host "[Storyteller] $message" -ForegroundColor Cyan
}

function Resolve-PythonExe {
    param([string]$Requested)

    if ($Requested -and (Test-Path $Requested)) {
        return $Requested
    }

    if ($env:STORYTELLER_PYTHON -and (Test-Path $env:STORYTELLER_PYTHON)) {
        return $env:STORYTELLER_PYTHON
    }

    $condaPython = Join-Path $env:USERPROFILE 'anaconda3\envs\pytorch2.2.2\python.exe'
    if (Test-Path $condaPython) {
        return $condaPython
    }

    $command = Get-Command python -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    throw 'Python executable not found. Pass -PythonExe or set STORYTELLER_PYTHON.'
}

function Stop-PortProcesses {
    param([int]$TargetPort)

    $connections = Get-NetTCPConnection -LocalPort $TargetPort -State Listen -ErrorAction SilentlyContinue
    if (-not $connections) {
        Write-Step "No existing listener found on port $TargetPort."
        return
    }

    $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($pid in $pids) {
        if (-not $pid -or $pid -eq $PID) {
            continue
        }
        try {
            $proc = Get-Process -Id $pid -ErrorAction Stop
            Write-Step "Stopping PID=${pid} ($($proc.ProcessName)) on port $TargetPort"
            Stop-Process -Id $pid -Force -ErrorAction Stop
        } catch {
            Write-Warning "Failed to stop PID=${pid}: $($_.Exception.Message)"
        }
    }

    Start-Sleep -Milliseconds 800
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Resolve-PythonExe -Requested $PythonExe

Write-Step "Repo root: $repoRoot"
Write-Step "Python: $python"

Stop-PortProcesses -TargetPort $Port

$args = @('-m', 'uvicorn', 'backend.main:app', '--host', '0.0.0.0', '--port', "$Port")
if (-not $NoReload) {
    $args += '--reload'
}

Write-Step "Starting backend at http://127.0.0.1:${Port}"
Push-Location $repoRoot
try {
    & $python @args
} finally {
    Pop-Location
}
