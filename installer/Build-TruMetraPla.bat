@echo off
setlocal

if "%~1"=="/?" goto :show_help
if "%~1"=="--help" goto :show_help

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR%"=="" set "SCRIPT_DIR=%CD%\\"
pushd "%SCRIPT_DIR%.."
set "REPO_ROOT=%CD%"

set "DIST_DIR="
set "ONEFILE_FLAG=--onefile"

:parse_args
if "%~1"=="" goto :args_done
if /I "%~1"=="--dist" (
    shift
    if "%~1"=="" (
        echo Errore: manca il percorso dopo --dist.
        goto :error_exit
    )
    set "DIST_DIR=%~f1"
    shift
    goto :parse_args
)
if /I "%~1"=="--portable" (
    set "ONEFILE_FLAG=--no-onefile"
    shift
    goto :parse_args
)
if /I "%~1"=="--onefile" (
    set "ONEFILE_FLAG=--onefile"
    shift
    goto :parse_args
)
echo Opzione sconosciuta: %~1
goto :error_exit

:args_done
if "%DIST_DIR%"=="" set "DIST_DIR=%REPO_ROOT%\\dist"
if not exist "%DIST_DIR%" mkdir "%DIST_DIR%" >nul

for %%I in (python.exe) do set "PYTHON_PATH=%%~$PATH:I"
if "%PYTHON_PATH%"=="" (
    echo Errore: Python 3.11+ non trovato nel PATH.
    echo Installa Python e riprova.
    goto :error_exit
)

set "VENV_DIR=%REPO_ROOT%\\.venv-trumetrapla-build"
set "VENV_PYTHON=%VENV_DIR%\\Scripts\\python.exe"
set "VENV_PIP=%VENV_DIR%\\Scripts\\pip.exe"

if not exist "%VENV_DIR%" (
    echo Creazione ambiente virtuale...
    "%PYTHON_PATH%" -m venv "%VENV_DIR%"
)

if not exist "%VENV_PYTHON%" (
    echo Errore: ambiente virtuale non valido (python.exe mancante).
    goto :error_exit
)

echo Aggiornamento pip...
"%VENV_PYTHON%" -m pip install --upgrade pip --quiet
if errorlevel 1 goto :error_exit

echo Installazione del progetto con dipendenze di build...
"%VENV_PIP%" install "%REPO_ROOT%[build]" --quiet
if errorlevel 1 goto :error_exit

echo Generazione eseguibile TruMetraPla.exe...
"%VENV_PYTHON%" -m trumetrapla.cli build-exe --dist "%DIST_DIR%" %ONEFILE_FLAG%
if errorlevel 1 goto :error_exit

if exist "%DIST_DIR%\\TruMetraPla.exe" (
    echo ^> Eseguibile creato in: "%DIST_DIR%\\TruMetraPla.exe"
) else (
    echo Avviso: TruMetraPla.exe non trovato in "%DIST_DIR%".
)

echo Operazione completata.
popd
endlocal
exit /b 0

:show_help
echo TruMetraPla build automatico
echo Uso: Build-TruMetraPla.bat [--dist cartella] [--portable^|--onefile]
echo    --dist      Imposta la cartella di output (default: dist\\)
echo    --portable  Genera la build in modalita^ portabile (cartella con dipendenze)
echo    --onefile   Forza la modalita^ onefile (default)
echo    --help, /?  Mostra questo messaggio
exit /b 0

:error_exit
popd
endlocal
exit /b 1
