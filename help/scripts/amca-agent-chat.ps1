param(
    [string]$Python = ".\.venv\Scripts\python.exe",
    [ValidateSet("Gemini", "xAI (Grok)", "OpenAI")][string]$Provider = "Gemini",
    [string]$Example = "valid_parallel_analysis",
    [string]$Session,
    [string]$Model
)
$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src"
$arguments = @("-m", "amca_agent.cli", "chat", "--provider", $Provider)
if ($Session) { $arguments += @("--session", $Session) }
else {
    if ($Example) { $arguments += @("--example", $Example) }
    if ($Model) { $arguments += @("--model", $Model) }
}
& $Python @arguments
exit $LASTEXITCODE
