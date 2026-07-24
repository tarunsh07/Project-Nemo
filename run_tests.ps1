# Run Cognition Fabric Test Suite
Write-Host "Running Cognition Fabric Test Suite..." -ForegroundColor Cyan

# Attempt 1: Check if 'uv' is in the global PATH
if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host "Found 'uv' in PATH." -ForegroundColor Green
    uv run --with pytest pytest -v -s tests/test_fabric_contract.py
    exit $LASTEXITCODE
}

# Attempt 2: Check if 'uv' is installed locally in the user profile (default for Windows)
$localUv = "$env:USERPROFILE\.local\bin\uv.exe"
if (Test-Path $localUv) {
    Write-Host "Found 'uv' in local profile ($localUv)." -ForegroundColor Green
    & $localUv run --with pytest pytest -v -s tests/test_fabric_contract.py
    exit $LASTEXITCODE
}

# Attempt 3: Fallback to standard Python and pip
Write-Host "'uv' not found. Falling back to standard Python..." -ForegroundColor Yellow
Write-Host "Installing pytest if missing..."
python -m pip install pytest --quiet
python -m pytest -v -s tests/test_fabric_contract.py
exit $LASTEXITCODE
