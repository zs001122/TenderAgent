param(
    [ValidateSet("start", "stop", "status", "restart")]
    [string]$Command = "start"
)

$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$RuntimeDir = Join-Path $RootDir ".runtime"
$VenvDir = Join-Path $RootDir "venv"
$BackendPidFile = Join-Path $RuntimeDir "backend.pid"
$FrontendPidFile = Join-Path $RuntimeDir "frontend.pid"
$BackendLogFile = Join-Path $RuntimeDir "backend.log"
$BackendErrorLogFile = Join-Path $RuntimeDir "backend.err.log"
$FrontendLogFile = Join-Path $RuntimeDir "frontend.log"
$FrontendErrorLogFile = Join-Path $RuntimeDir "frontend.err.log"
$NpmCacheDir = Join-Path $RuntimeDir "npm-cache"

$BackendHost = if ($env:BACKEND_HOST) { $env:BACKEND_HOST } else { "0.0.0.0" }
$FrontendHost = if ($env:FRONTEND_HOST) { $env:FRONTEND_HOST } else { "0.0.0.0" }
$BackendPort = if ($env:BACKEND_PORT) { [int]$env:BACKEND_PORT } else { 8000 }
$FrontendPort = if ($env:FRONTEND_PORT) { [int]$env:FRONTEND_PORT } else { 3000 }
$BackendReload = $env:BACKEND_RELOAD -in @("1", "true", "TRUE", "yes", "YES", "on", "ON")

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

function Read-Pid {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        return $null
    }
    $raw = (Get-Content $Path -ErrorAction SilentlyContinue | Select-Object -First 1)
    if ([string]::IsNullOrWhiteSpace($raw)) {
        return $null
    }
    $pidValue = 0
    if ([int]::TryParse($raw.Trim(), [ref]$pidValue)) {
        return $pidValue
    }
    return $null
}

function Test-ProcessRunning {
    param([Nullable[int]]$PidValue)
    if (-not $PidValue) {
        return $false
    }
    return $null -ne (Get-Process -Id $PidValue -ErrorAction SilentlyContinue)
}

function Test-PortInUse {
    param([int]$Port)
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $async = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        $connected = $async.AsyncWaitHandle.WaitOne(200, $false)
        if (-not $connected) {
            return $false
        }
        $client.EndConnect($async)
        return $true
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

function Find-FreePort {
    param([int]$StartPort)
    for ($port = $StartPort; $port -lt ($StartPort + 200); $port++) {
        if (-not (Test-PortInUse $port)) {
            return $port
        }
    }
    throw "No free port found from $StartPort to $($StartPort + 199)."
}

function Ensure-BackendEnv {
    $python = Join-Path $VenvDir "Scripts\python.exe"
    if (-not (Test-Path $python)) {
        python -m venv $VenvDir
    }

    $pip = Join-Path $VenvDir "Scripts\pip.exe"
    & $python -c "import fastapi, sqlmodel, uvicorn" 2>$null
    if ($LASTEXITCODE -ne 0) {
        & $pip install -r (Join-Path $BackendDir "requirements.txt")
    }
}

function Ensure-FrontendEnv {
    if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
        New-Item -ItemType Directory -Force -Path $NpmCacheDir | Out-Null
        Push-Location $FrontendDir
        try {
            npm install --cache $NpmCacheDir
        } finally {
            Pop-Location
        }
    }
}

function Start-Backend {
    $existingPid = Read-Pid $BackendPidFile
    if (Test-ProcessRunning $existingPid) {
        Write-Output "backend_running pid=$existingPid"
        return
    }

    $python = Join-Path $VenvDir "Scripts\python.exe"
    $args = @("-m", "uvicorn", "app.main:app", "--host", $BackendHost, "--port", "$script:BackendPort")
    if ($BackendReload) {
        $args = @("-m", "uvicorn", "app.main:app", "--reload", "--host", $BackendHost, "--port", "$script:BackendPort")
    }
    $process = Start-Process -FilePath $python -ArgumentList $args -WorkingDirectory $BackendDir -WindowStyle Hidden -RedirectStandardOutput $BackendLogFile -RedirectStandardError $BackendErrorLogFile -PassThru
    Set-Content -Path $BackendPidFile -Value $process.Id
    Write-Output "backend_started pid=$($process.Id)"
}

function Start-Frontend {
    $existingPid = Read-Pid $FrontendPidFile
    if (Test-ProcessRunning $existingPid) {
        Write-Output "frontend_running pid=$existingPid"
        return
    }

    $apiTarget = "http://localhost:$script:BackendPort"
    $commandLine = "set VITE_API_TARGET=$apiTarget&& npm run dev -- --host $FrontendHost --port $script:FrontendPort"
    $process = Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", $commandLine) -WorkingDirectory $FrontendDir -WindowStyle Hidden -RedirectStandardOutput $FrontendLogFile -RedirectStandardError $FrontendErrorLogFile -PassThru
    Set-Content -Path $FrontendPidFile -Value $process.Id
    Write-Output "frontend_started pid=$($process.Id)"
}

function Stop-AppProcess {
    param(
        [string]$Name,
        [string]$PidFile
    )

    $pidValue = Read-Pid $PidFile
    if (-not (Test-ProcessRunning $pidValue)) {
        Remove-Item -Path $PidFile -Force -ErrorAction SilentlyContinue
        Write-Output "${Name}_stopped"
        return
    }

    taskkill /PID $pidValue /T /F | Out-Null
    Remove-Item -Path $PidFile -Force -ErrorAction SilentlyContinue
    Write-Output "${Name}_stopped pid=$pidValue"
}

function Show-Status {
    $backendPid = Read-Pid $BackendPidFile
    $frontendPid = Read-Pid $FrontendPidFile
    $backendOk = Test-ProcessRunning $backendPid
    $frontendOk = Test-ProcessRunning $frontendPid

    if ($backendOk) {
        Write-Output "backend_running pid=$backendPid"
    } else {
        Remove-Item -Path $BackendPidFile -Force -ErrorAction SilentlyContinue
        Write-Output "backend_stopped"
    }

    if ($frontendOk) {
        Write-Output "frontend_running pid=$frontendPid"
    } else {
        Remove-Item -Path $FrontendPidFile -Force -ErrorAction SilentlyContinue
        Write-Output "frontend_stopped"
    }

    if (-not ($backendOk -and $frontendOk)) {
        exit 1
    }
}

function Start-All {
    $requestedBackendPort = $script:BackendPort
    $requestedFrontendPort = $script:FrontendPort

    if (Test-PortInUse $script:BackendPort) {
        $script:BackendPort = Find-FreePort $script:BackendPort
        Write-Output "backend_port_switched from=$requestedBackendPort to=$script:BackendPort"
    }
    if (Test-PortInUse $script:FrontendPort) {
        $script:FrontendPort = Find-FreePort $script:FrontendPort
        Write-Output "frontend_port_switched from=$requestedFrontendPort to=$script:FrontendPort"
    }

    Ensure-BackendEnv
    Ensure-FrontendEnv
    Start-Backend
    Start-Sleep -Seconds 2
    Start-Frontend
    Start-Sleep -Seconds 2

    Write-Output "backend_url=http://localhost:$script:BackendPort"
    Write-Output "frontend_url=http://localhost:$script:FrontendPort"
    Write-Output "api_docs=http://localhost:$script:BackendPort/docs"
    Write-Output "frontend_api_target=http://localhost:$script:BackendPort"
    Write-Output "backend_log=$BackendLogFile"
    Write-Output "backend_error_log=$BackendErrorLogFile"
    Write-Output "frontend_log=$FrontendLogFile"
    Write-Output "frontend_error_log=$FrontendErrorLogFile"
}

switch ($Command) {
    "start" {
        Start-All
    }
    "stop" {
        Stop-AppProcess "backend" $BackendPidFile
        Stop-AppProcess "frontend" $FrontendPidFile
    }
    "status" {
        Show-Status
    }
    "restart" {
        Stop-AppProcess "backend" $BackendPidFile
        Stop-AppProcess "frontend" $FrontendPidFile
        Start-All
    }
}
