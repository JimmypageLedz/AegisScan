$ProjectRoot = "E:\web-security-platform"
$BackendDir = "$ProjectRoot\backend"
$PythonExe = "$ProjectRoot\.venv\Scripts\python.exe"

Set-Location $ProjectRoot

# Ensure the Redis container exists and is running before starting app services.
$RedisContainer = docker ps -a -q -f name=aegisscan-redis
$RedisRunning = docker ps -q -f name=aegisscan-redis

if (-not $RedisContainer) {
    Write-Host "Redis container not found. Creating and starting aegisscan-redis..."
    docker run -d --name aegisscan-redis -p 6379:6379 redis:7
}
elseif (-not $RedisRunning) {
    Write-Host "Redis container exists but is stopped. Starting aegisscan-redis..."
    docker start aegisscan-redis
}
else {
    Write-Host "Redis container is already running."
}

Write-Host "Starting Celery worker in a new PowerShell window..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$BackendDir'; & '$PythonExe' -m celery -A app.celery_app:celery_app worker --loglevel=info --pool=solo"
)

Write-Host "Starting FastAPI server in a new PowerShell window..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$BackendDir'; & '$PythonExe' -m uvicorn app.main:app --reload"
)

Write-Host "Development services launch commands have been sent."
