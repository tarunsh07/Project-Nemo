# Start Cognition Fabric API Server
Write-Host "Starting API Server..." -ForegroundColor Cyan

# Define the run arguments
$args = "run", "--with", "fastapi", "--with", "uvicorn", "--with", "pydantic", "uvicorn", "api.server:app", "--reload"

# Attempt 1: Check if 'uv' is in the global PATH
if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host "Found 'uv' in PATH." -ForegroundColor Green
    & uv $args
    exit $LASTEXITCODE
}

# Attempt 2: Check if 'uv' is installed locally in the user profile
$localUv = "$env:USERPROFILE\.local\bin\uv.exe"
if (Test-Path $localUv) {
    Write-Host "Found 'uv' in local profile ($localUv)." -ForegroundColor Green
    & $localUv $args
    exit $LASTEXITCODE
}

# Attempt 3: Fallback to standard Python
Write-Host "'uv' not found. Falling back to standard Python..." -ForegroundColor Yellow
python -m pip install fastapi uvicorn pydantic
python -m uvicorn api.server:app --reload
exit $LASTEXITCODE
