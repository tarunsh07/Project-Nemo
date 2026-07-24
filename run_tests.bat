@echo off
echo Running Cognition Fabric Test Suite...

:: Attempt 1: Check if 'uv' is in the global PATH
where uv >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Found 'uv' in PATH.
    uv run --with pytest pytest -v -s tests/test_fabric_contract.py
    exit /b %ERRORLEVEL%
)

:: Attempt 2: Check if 'uv' is installed locally in the user profile
if exist "%USERPROFILE%\.local\bin\uv.exe" (
    echo Found 'uv' in local profile.
    "%USERPROFILE%\.local\bin\uv.exe" run --with pytest pytest -v -s tests/test_fabric_contract.py
    exit /b %ERRORLEVEL%
)

:: Attempt 3: Fallback to standard Python and pip
echo 'uv' not found. Falling back to standard Python...
python -m pip install pytest --quiet
python -m pytest -v -s tests/test_fabric_contract.py
exit /b %ERRORLEVEL%
