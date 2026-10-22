param([string]$Python = ".\.venv\Scripts\python.exe")
$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src"
& $Python -m streamlit run app.py
