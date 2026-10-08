$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BundledPython = Join-Path ([Environment]::GetFolderPath("UserProfile")) ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$RuntimePython = if (Test-Path -LiteralPath $BundledPython) { $BundledPython } elseif (Test-Path -LiteralPath $VenvPython) { $VenvPython } else { "python" }
$env:PYTHONPATH = "$ProjectRoot\.deps;$ProjectRoot\src"
& $RuntimePython -m pytest
