param(
    [ValidateSet('production', 'development')]
    [string]$Mode = 'production'
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendRoot = Join-Path $ProjectRoot 'frontend'
$RuntimeRoot = Join-Path $ProjectRoot 'runtime'
$NextCli = Join-Path $FrontendRoot 'node_modules\next\dist\bin\next'
$BackendUrl = 'http://127.0.0.1:8000/api/v1/health'
$FrontendUrl = 'http://127.0.0.1:3000/'

if (-not (Test-Path -LiteralPath $NextCli)) {
    throw 'Frontend dependencies are missing. Run npm ci inside frontend first.'
}
if ($Mode -eq 'production' -and -not (Test-Path -LiteralPath (Join-Path $FrontendRoot '.next\BUILD_ID'))) {
    throw 'Production bundle is missing. Run npm run build inside frontend first.'
}

$NodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
if (-not $NodeCommand) { throw 'Node.js is missing from PATH.' }
$NodeExecutable = $NodeCommand.Source

$PythonCandidates = @(
    (Join-Path $ProjectRoot '.venv\Scripts\python.exe'),
    (Join-Path ([Environment]::GetFolderPath('UserProfile')) '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe')
)
$PathPython = Get-Command python.exe -ErrorAction SilentlyContinue
if ($PathPython) { $PythonCandidates += $PathPython.Source }
$PythonExecutable = $null
$PreviousPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = if (Test-Path -LiteralPath (Join-Path $ProjectRoot '.deps')) {
    "$(Join-Path $ProjectRoot '.deps');$(Join-Path $ProjectRoot 'src')"
} else {
    Join-Path $ProjectRoot 'src'
}
foreach ($Candidate in $PythonCandidates) {
    if (-not (Test-Path -LiteralPath $Candidate)) { continue }
    & $Candidate -c 'import uvicorn, fastapi, aquasentinel' 2>$null
    if ($LASTEXITCODE -eq 0) { $PythonExecutable = $Candidate; break }
}
if (-not $PythonExecutable) {
    $env:PYTHONPATH = $PreviousPythonPath
    throw 'No Python environment with the backend dependencies was found. Install pip install -e ".[dev]" into .venv.'
}

foreach ($Port in @(8000, 3000)) {
    if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
        $env:PYTHONPATH = $PreviousPythonPath
        throw "Port $Port is already in use. Stop the existing service or use stop-integrated.ps1 for a session started by this script."
    }
}

New-Item -ItemType Directory -Force -Path $RuntimeRoot | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$BackendOut = Join-Path $RuntimeRoot "backend-$Stamp.out.log"
$BackendErr = Join-Path $RuntimeRoot "backend-$Stamp.err.log"
$FrontendOut = Join-Path $RuntimeRoot "frontend-$Stamp.out.log"
$FrontendErr = Join-Path $RuntimeRoot "frontend-$Stamp.err.log"
$BackendProcess = $null
$FrontendProcess = $null

try {
    $BackendProcess = Start-Process -FilePath $PythonExecutable -ArgumentList @('-m', 'uvicorn', 'aquasentinel.main:app', '--host', '127.0.0.1', '--port', '8000') -WorkingDirectory $ProjectRoot -PassThru -WindowStyle Hidden -RedirectStandardOutput $BackendOut -RedirectStandardError $BackendErr
    $NextMode = if ($Mode -eq 'production') { 'start' } else { 'dev' }
    $FrontendProcess = Start-Process -FilePath $NodeExecutable -ArgumentList @("`"$NextCli`"", $NextMode, '--hostname', '127.0.0.1', '--port', '3000') -WorkingDirectory $FrontendRoot -PassThru -WindowStyle Hidden -RedirectStandardOutput $FrontendOut -RedirectStandardError $FrontendErr

    foreach ($Entry in @(@('backend', $BackendUrl), @('frontend', $FrontendUrl))) {
        $Ready = $false
        for ($Attempt = 0; $Attempt -lt 40; $Attempt++) {
            Start-Sleep -Milliseconds 500
            try {
                $Response = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 $Entry[1]
                if ($Response.StatusCode -eq 200) { $Ready = $true; break }
            } catch { }
            if ($BackendProcess.HasExited -or $FrontendProcess.HasExited) { break }
        }
        if (-not $Ready) { throw "$($Entry[0]) failed its HTTP readiness check. Inspect $BackendErr and $FrontendErr." }
    }

    $State = [pscustomobject]@{
        mode = $Mode
        backend_pid = $BackendProcess.Id
        backend_started_utc = $BackendProcess.StartTime.ToUniversalTime().ToString('o')
        frontend_pid = $FrontendProcess.Id
        frontend_started_utc = $FrontendProcess.StartTime.ToUniversalTime().ToString('o')
        backend_error_log = $BackendErr
        frontend_error_log = $FrontendErr
    }
    $State | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $RuntimeRoot 'session.json') -Encoding utf8
    Write-Output "Backend:  $BackendUrl"
    Write-Output 'OpenAPI:  http://127.0.0.1:8000/api/docs'
    Write-Output "Frontend: $FrontendUrl"
    Write-Output "Mode:     $Mode"
    Write-Output "PIDs:     backend=$($BackendProcess.Id), frontend=$($FrontendProcess.Id)"
    Write-Output "Logs:     $RuntimeRoot"
} catch {
    if ($FrontendProcess -and -not $FrontendProcess.HasExited) { Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue }
    if ($BackendProcess -and -not $BackendProcess.HasExited) { Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue }
    throw
} finally {
    $env:PYTHONPATH = $PreviousPythonPath
}
