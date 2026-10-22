param(
    [string]$Python = ".\.venv\Scripts\python.exe",
    [string]$RunId,
    [string]$File
)
$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src"
& $Python -m amca_agent.cli sessions
& $Python -m amca_agent.cli artifacts
if ($RunId) { & $Python -m amca_agent.cli artifacts --show $RunId }
if ($File) { & $Python -m amca_agent.cli show $File }
