@echo off
setlocal

if "%~1"=="/?" goto :show_help
if "%~1"=="--help" goto :show_help

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR%"=="" set "SCRIPT_DIR=%CD%\\"
pushd "%SCRIPT_DIR%.."
set "REPO_ROOT=%CD%"

where py >nul 2>&1
if errorlevel 1 (
    echo Errore: interprete Python (py) non trovato nel PATH.
    goto :error_exit
)

echo Aggiornamento degli strumenti di packaging...
py -m pip install --upgrade pip build >nul
if errorlevel 1 goto :error_exit

echo Costruzione degli artefatti TruMetraPla...
py -m build --wheel --sdist --outdir "%REPO_ROOT%\\dist"
if errorlevel 1 goto :error_exit

set "LATEST_WHEEL="
for %%F in ("%REPO_ROOT%\\dist\\TruMetraPla-*.whl") do set "LATEST_WHEEL=%%~fF"
if "%LATEST_WHEEL%"=="" (
    echo Errore: nessun file wheel trovato nella cartella dist.
    goto :error_exit
)

echo Installazione della build appena generata...
py -m pip install --upgrade --force-reinstall "%LATEST_WHEEL%"
if errorlevel 1 goto :error_exit

echo Avvio dell'interfaccia TruMetraPla...
py -m trumetrapla %*
if errorlevel 1 goto :error_exit

echo Operazione completata con successo.
goto :cleanup

:show_help
echo TruMetraPla - build e avvio con interprete di sistema

echo Uso: PyBuild-And-Run-TruMetraPla.bat [argomenti_trumetrapla]
echo     Gli argomenti indicati verranno passati a ^"py -m trumetrapla^".
goto :cleanup

:error_exit
echo Operazione interrotta.

:cleanup
popd
endlocal
