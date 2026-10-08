$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$StatePath = Join-Path $ProjectRoot 'runtime\session.json'
if (-not (Test-Path -LiteralPath $StatePath)) { throw 'No integrated session record exists.' }
$State = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json

function Stop-RecordedProcess([int]$ProcessId, [datetime]$StartedUtc) {
    $Root = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $Root) { return }
    if ([math]::Abs(($Root.StartTime.ToUniversalTime() - $StartedUtc.ToUniversalTime()).TotalSeconds) -gt 1) {
        throw "PID $ProcessId was reused; refusing to stop an unrelated process."
    }
    $Ids = @($ProcessId)
    do {
        $NewIds = @(Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -in $Ids -and $_.ProcessId -notin $Ids } | Select-Object -ExpandProperty ProcessId)
        $Ids += $NewIds
    } while ($NewIds.Count -gt 0)
    [array]::Reverse($Ids)
    foreach ($Id in $Ids) {
        Stop-Process -Id $Id -Force -ErrorAction SilentlyContinue
    }
}

Stop-RecordedProcess $State.frontend_pid $State.frontend_started_utc
Stop-RecordedProcess $State.backend_pid $State.backend_started_utc
Remove-Item -LiteralPath $StatePath
Write-Output 'Stopped the recorded NeroSentinel frontend and backend session.'
