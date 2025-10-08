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
    echo Errore: Python 3.11+ non trovato nel PATH.
    echo Installa Python da https://www.python.org/downloads/windows/ e abilita ^"Add Python to PATH^".
    goto :error
)

set "VENV_DIR=%REPO_ROOT%\.venv-trumetrapla-build"
if not exist "%VENV_DIR%" (
    echo Creazione ambiente virtuale dedicato...
    "%PYTHON_EXE%" -m venv "%VENV_DIR%"
    if errorlevel 1 goto :error
)

set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"
if not exist "%VENV_PYTHON%" (
    echo Errore: impossibile trovare python.exe nell'ambiente virtuale.
    goto :error
)

echo Aggiornamento di pip e installazione delle dipendenze di build...
"%VENV_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 goto :error
"%VENV_PIP%" install --upgrade ".[build]"
if errorlevel 1 goto :error

where makensis >nul 2>&1
if errorlevel 1 (
    winget --version >nul 2>&1
    if not errorlevel 1 (
        echo NSIS non rilevato: avvio installazione silenziosa tramite winget...
        winget install --id NSIS.NSIS -e --source winget --silent
    ) else (
        echo Avviso: NSIS non rilevato. Installalo manualmente se vuoi creare TruMetraPla_Setup.exe.
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

echo Generazione dell'eseguibile TruMetraPla.exe...
if defined BUILD_ARGS (
    "%VENV_PYTHON%" -m trumetrapla build-exe !BUILD_ARGS!
) else (
    "%VENV_PYTHON%" -m trumetrapla build-exe
)
if errorlevel 1 goto :error

if %INCLUDE_INSTALLER%==1 (
    echo Creazione dell'installer grafico TruMetraPla_Setup.exe...
    if defined BUILD_ARGS (
        "%VENV_PYTHON%" -m trumetrapla build-installer !BUILD_ARGS!
    ) else (
        "%VENV_PYTHON%" -m trumetrapla build-installer
    )
    if errorlevel 1 goto :error
)

echo.
echo Operazione completata. I pacchetti sono nella cartella dist\.
popd
endlocal
exit /b 0

:show_help
echo Setup-TruMetraPla.bat - prepara le dipendenze e genera l'eseguibile Windows

echo Uso: Setup-TruMetraPla.bat [opzioni_pyinstaller] [--include-installer]
echo    Qualsiasi parametro viene passato a ^"trumetrapla build-exe^".
echo    Usa --include-installer per creare anche TruMetraPla_Setup.exe.
popd
endlocal
exit /b 0

:error
echo.
echo Errore durante l'installazione o la build.
popd
endlocal
exit /b 1
