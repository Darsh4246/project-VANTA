@echo off
setlocal
:: Resolve the parent directory (project root)
for %%i in ("%~dp0..") do set "PROJECT_ROOT=%%~fi"

:: Set PYTHONPATH to the project root so imports (e.g. 'import vanta') work
set "PYTHONPATH=%PROJECT_ROOT%"

:: Set Python UTF-8 modes to avoid console encoding crashes
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

:: Resolve the virtual environment directory (check local directory first, then parent)
set "VENV_PATH=%~dp0.venv"
if not exist "%VENV_PATH%\Scripts\python.exe" (
    if exist "%PROJECT_ROOT%\.venv\Scripts\python.exe" (
        set "VENV_PATH=%PROJECT_ROOT%\.venv"
    ) else (
        echo [VANTA] Virtual environment not found. Creating .venv...
        py -3.12 -m venv "%~dp0.venv"
        if errorlevel 1 (
            echo [VANTA] Failed with py -3.12. Trying default python...
            python -m venv "%~dp0.venv"
        )
        if not exist "%~dp0.venv\Scripts\python.exe" (
            echo [VANTA] Error: Failed to create virtual environment. Please install Python 3.12.
            pause
            exit /b 1
        )
        echo [VANTA] Installing dependencies from requirements.txt...
        "%~dp0.venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt"
        set "VENV_PATH=%~dp0.venv"
    )
)

:: Execute the virtual environment python with the entrypoint script
"%VENV_PATH%\Scripts\python.exe" "%~dp0main.py" %*
endlocal
