@echo off
setlocal enabledelayedexpansion

rem Posiziona il prompt nella radice del progetto
pushd "%~dp0.."

rem Determina il comando Python disponibile (py su Windows o python)
set "PYTHON=python"
where py >nul 2>nul && set "PYTHON=py"

echo ===============================================
echo   Preparazione ambiente TruMetraPla
echo ===============================================
"%PYTHON%" -m pip install --upgrade pip build
if errorlevel 1 goto :pip_error

"%PYTHON%" -m pip install -e .
if errorlevel 1 goto :install_error

echo.
echo ===============================================
echo   Avvio build pacchetto
echo ===============================================
"%PYTHON%" -m build
if errorlevel 1 goto :build_error

echo.
echo ===============================================
echo   Avvio interfaccia TruMetraPla
echo ===============================================
"%PYTHON%" -m trumetrapla
if errorlevel 1 goto :run_error

goto :success

:pip_error
echo Errore durante l'aggiornamento di pip o build.
goto :end

:install_error
echo Errore durante l'installazione del pacchetto TruMetraPla.
goto :end

:build_error
echo Errore durante la fase di build. Controlla i messaggi precedenti.
goto :end

:run_error
echo Errore durante l'avvio dell'interfaccia TruMetraPla.
goto :end

:success
echo.
echo Operazione completata. Buon lavoro!

:end
popd
endlocal
