param(
    [string]$Python = ".\.venv\Scripts\python.exe",
    [string]$Workspace = (Get-Location).Path
)
$ErrorActionPreference = "Stop"
Set-Location $Workspace
$env:PYTHONPATH = "src"

# Daftar, salin, validasi, dan gambarkan contoh DAG.
& $Python -m amca_agent.cli examples
& $Python -m amca_agent.cli example valid_parallel_analysis --output machine.yaml
& $Python -m amca_agent.cli validate machine.yaml --output verification.json
& $Python -m amca_agent.cli graph machine.yaml --output machine-dag.dot

# Jalankan melalui CLI inti lalu baca laporan hasil.
& $Python -m amca.cli run machine.yaml --inputs examples/reference-input.json --output execution-record.json
& $Python -m amca.cli report execution-record.json

# Contoh invalid: perintah ini diharapkan exit code 1 atau 2 dan tidak mengeksekusi graph.
& $Python -m amca_agent.cli validate examples/invalid_missing_dependency.yaml
if ($LASTEXITCODE -notin @(1, 2)) { throw "Contoh negatif seharusnya ditolak." }
