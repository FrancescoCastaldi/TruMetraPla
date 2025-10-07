@echo off
setlocal

if "%~1"=="/?" goto :show_help
if "%~1"=="--help" goto :show_help

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR%"=="" set "SCRIPT_DIR=%CD%\\"
pushd "%SCRIPT_DIR%.."
set "REPO_ROOT=%CD%"

for %%I in (python.exe) do set "PYTHON_PATH=%%~$PATH:I"
if "%PYTHON_PATH%"=="" (
    echo Errore: Python 3.11+ non trovato nel PATH.
    goto :error_exit
)

set "VENV_DIR=%REPO_ROOT%\\.venv-trumetrapla-run"
set "VENV_PYTHON=%VENV_DIR%\\Scripts\\python.exe"
set "VENV_PIP=%VENV_DIR%\\Scripts\\pip.exe"

if not exist "%VENV_DIR%" (
    echo Creazione ambiente virtuale per build e avvio...
    "%PYTHON_PATH%" -m venv "%VENV_DIR%"
)

if not exist "%VENV_PYTHON%" (
    echo Errore: ambiente virtuale non valido (python.exe mancante).
    goto :error_exit
)

echo Aggiornamento pip e installazione modulo build...
"%VENV_PYTHON%" -m pip install --upgrade pip build --quiet
if errorlevel 1 goto :error_exit

echo Costruzione del pacchetto TruMetraPla...
"%VENV_PYTHON%" -m build --wheel --sdist --outdir "%REPO_ROOT%\\dist"
if errorlevel 1 goto :error_exit

set "LATEST_WHEEL="
for %%F in ("%REPO_ROOT%\\dist\\TruMetraPla-*.whl") do set "LATEST_WHEEL=%%~fF"
if "%LATEST_WHEEL%"=="" (
    echo Errore: nessuna wheel trovata in dist\\.
    goto :error_exit
)

echo Installazione della build appena generata...
"%VENV_PIP%" install --upgrade --force-reinstall "%LATEST_WHEEL%" --quiet
if errorlevel 1 goto :error_exit

echo Avvio di TruMetraPla con l'interfaccia grafica...
"%VENV_DIR%\\Scripts\\trumetrapla.exe" %*
if errorlevel 1 (
    echo Avvio diretto fallito, provo con python -m trumetrapla.
    "%VENV_PYTHON%" -m trumetrapla %*
)

echo Operazione completata.
popd
endlocal
exit /b 0

:show_help
echo TruMetraPla - build pacchetto e avvio GUI

echo Uso: Build-And-Run-TruMetraPla.bat [argomenti_trumetrapla]
echo    Qualsiasi parametro viene passato al comando ^"trumetrapla^" finale.
exit /b 0

:error_exit
echo Operazione interrotta.
popd
endlocal
exit /b 1
