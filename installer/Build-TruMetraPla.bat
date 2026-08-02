@echo off
setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR%"=="" set "SCRIPT_DIR=%CD%\\"
set "SETUP_SCRIPT=%SCRIPT_DIR%Setup-TruMetraPla.bat"

if not exist "%SETUP_SCRIPT%" (
    echo Error: unable to find Setup-TruMetraPla.bat next to this script.
    exit /b 1
)

pushd "%SCRIPT_DIR%.."
set "REPO_ROOT=%CD%"

set "VENV_DIR=%REPO_ROOT%\.venv-TruMetraPla-build"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo Build environment not initialized. Launching Setup-TruMetraPla.bat...
    call "%SETUP_SCRIPT%"
    if errorlevel 1 goto :error
)

set "ARGS="
set "INCLUDE_INSTALLER=0"
:parse_args
if "%~1"=="" goto :after_parse
set "ARG=%~1"
if /I "!ARG!"=="--include-installer" (
    set "INCLUDE_INSTALLER=1"
) else (
    set "ARGS=!ARGS! \"!ARG!\""
)
shift
goto :parse_args

:after_parse

echo Generating the TruMetraPla.exe executable...
if defined ARGS (
    "%VENV_PYTHON%" -m trumetrapla build-exe !ARGS!
) else (
    "%VENV_PYTHON%" -m trumetrapla build-exe
)
if errorlevel 1 goto :error

if %INCLUDE_INSTALLER%==1 (
    echo Creating the TruMetraPla_Setup.exe installer...
    if defined ARGS (
        "%VENV_PYTHON%" -m trumetrapla build-installer !ARGS!
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

:error
echo.
echo Error while generating the package.
popd
endlocal
exit /b 1
