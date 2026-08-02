@echo off
setlocal EnableDelayedExpansion

if "%~1"=="/?" goto :show_help
if "%~1"=="--help" goto :show_help

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR%"=="" set "SCRIPT_DIR=%CD%\"
pushd "%SCRIPT_DIR%.."
set "REPO_ROOT=%CD%"

set "PYTHON_EXE="
for %%I in (python.exe) do if not defined PYTHON_EXE set "PYTHON_EXE=%%~$PATH:I"
if not defined PYTHON_EXE (
    echo Error: Python 3.11+ not found in PATH.
    echo Install Python from https://www.python.org/downloads/windows/ and enable ^"Add Python to PATH^".
    goto :error
)

set "VENV_DIR=%REPO_ROOT%\.venv-TruMetraPla-build"
if not exist "%VENV_DIR%" (
    echo Creating a dedicated virtual environment...
    "%PYTHON_EXE%" -m venv "%VENV_DIR%"
    if errorlevel 1 goto :error
)

set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"
if not exist "%VENV_PYTHON%" (
    echo Error: unable to find python.exe in the virtual environment.
    goto :error
)

echo Updating pip and installing the build dependencies...
"%VENV_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 goto :error
"%VENV_PIP%" install --upgrade ".[build]"
if errorlevel 1 goto :error

where makensis >nul 2>&1
if errorlevel 1 (
    winget --version >nul 2>&1
    if not errorlevel 1 (
        echo NSIS not detected: starting silent installation via winget...
        winget install --id NSIS.NSIS -e --source winget --silent
    ) else (
        echo Warning: NSIS not detected. Install it manually if you want to create TruMetraPla_Setup.exe.
    )
)

set "BUILD_ARGS="
set "INCLUDE_INSTALLER=0"
:parse_args
if "%~1"=="" goto :after_parse
set "ARG=%~1"
if /I "!ARG!"=="--include-installer" (
    set "INCLUDE_INSTALLER=1"
) else (
    set "BUILD_ARGS=!BUILD_ARGS! \"!ARG!\""
)
shift
goto :parse_args

:after_parse

echo Generating the TruMetraPla.exe executable...
if defined BUILD_ARGS (
    "%VENV_PYTHON%" -m trumetrapla build-exe !BUILD_ARGS!
) else (
    "%VENV_PYTHON%" -m trumetrapla build-exe
)
if errorlevel 1 goto :error

if %INCLUDE_INSTALLER%==1 (
    echo Creating the graphical TruMetraPla_Setup.exe installer...
    if defined BUILD_ARGS (
        "%VENV_PYTHON%" -m trumetrapla build-installer !BUILD_ARGS!
    ) else (
        "%VENV_PYTHON%" -m trumetrapla build-installer
    )
    if errorlevel 1 goto :error
)

echo.
echo Operation completed. The packages are in the dist\ folder.
popd
endlocal
exit /b 0

:show_help
echo Setup-TruMetraPla.bat - prepares the dependencies and generates the Windows executable
echo.
echo Usage: Setup-TruMetraPla.bat [pyinstaller_options] [--include-installer]
echo    Any parameter is passed to ^"trumetrapla build-exe^.
echo    Use --include-installer to also create TruMetraPla_Setup.exe.
popd
endlocal
exit /b 0

:error
echo.
echo Error during installation or build.
popd
endlocal
exit /b 1