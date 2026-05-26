# Stop any process on port 8000 and restart the backend with latest code
$port = 8000
$connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
foreach ($c in $connections) {
    Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
}
Set-Location $PSScriptRoot
& .\venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
