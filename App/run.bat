@echo off
REM Get the directory of this batch file
set "SCRIPT_DIR=%~dp0"
echo Running Script "%SCRIPT_DIR%main.py"...
"%SCRIPT_DIR%venv\Scripts\python.exe" "%SCRIPT_DIR%main.py"

REM Path to the virtual environment's Python executable
set "VENV_PYTHON=%SCRIPT_DIR%venv\Scripts\python.exe"

REM Path to your Python script (replace "my_script.py" with your script name)
set "PYTHON_SCRIPT=%SCRIPT_DIR%main.py"

REM Check if the virtual environment exists
if not exist "%VENV_PYTHON%" (
    echo Error: Virtual environment not found in "%SCRIPT_DIR%venv\"
    echo Run Method 1's steps to set up the environment first.
    pause
    exit /b 1
)

REM Run the script using the virtual environment's Python
echo Running script "%PYTHON_SCRIPT%"...
"%VENV_PYTHON%" "%PYTHON_SCRIPT%" %*

REM Optional: Pause to see output (remove if not needed)
pause