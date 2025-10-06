<#
.SYNOPSIS
    Automazione della build TruMetraPla per generare l'eseguibile Windows e, opzionalmente, l'installer NSIS.

.DESCRIPTION
    Lo script crea (o riutilizza) un ambiente virtuale isolato, installa il progetto con le dipendenze di build,
    esegue il comando CLI `trumetrapla build-exe` e, se richiesto, genera automaticamente l'installer grafico
    `TruMetraPla_Setup.exe` tramite `trumetrapla build-installer`.

.PARAMETER Output
    Cartella di destinazione per l'eseguibile generato (default: cartella dist/ alla radice del repository).

.PARAMETER Portable
    Se specificato, disabilita la modalità onefile di PyInstaller e mantiene la cartella portabile.

.PARAMETER IncludeInstaller
    Se specificato, invoca `trumetrapla build-installer` per produrre automaticamente l'installer grafico NSIS.

.PARAMETER ForceVenv
    Ricrea l'ambiente virtuale anche se già presente.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File installer/Setup-TruMetraPla.ps1

.NOTES
    Richiede Python 3.11+, PyInstaller (installato automaticamente) e, per l'installer, NSIS disponibile nel PATH.
#>
[CmdletBinding()]
param(
    [Parameter()]
    [string]$Output,

    [Parameter()]
    [switch]$Portable,

    [Parameter()]
    [switch]$IncludeInstaller,

    [Parameter()]
    [switch]$ForceVenv
)

$ErrorActionPreference = 'Stop'

function Resolve-RepositoryRoot {
    $scriptRoot = $PSScriptRoot
    if (-not $scriptRoot) {
        $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    }
    return (Resolve-Path (Join-Path $scriptRoot '..'))
}

$repoRoot = Resolve-RepositoryRoot
$distDirectory = $null
if ($Output) {
    $resolved = Resolve-Path -Path $Output -ErrorAction SilentlyContinue
    if ($resolved) {
        $distDirectory = $resolved.Path
    } else {
        $distDirectory = (Resolve-Path -Path (Join-Path (Get-Location) $Output) -ErrorAction SilentlyContinue)
        if ($distDirectory) {
            $distDirectory = $distDirectory.Path
        } else {
            $distDirectory = (Join-Path $repoRoot $Output)
        }
    }
}
if (-not $distDirectory) {
    $distDirectory = Join-Path $repoRoot 'dist'
}
if (-not (Test-Path $distDirectory)) {
    New-Item -ItemType Directory -Force -Path $distDirectory | Out-Null
}

$venvPath = Join-Path $repoRoot '.venv-trumetrapla-build'
$venvPython = Join-Path $venvPath 'Scripts' 'python.exe'
$venvPip = Join-Path $venvPath 'Scripts' 'pip.exe'

Write-Host '=== TruMetraPla Setup Automatico ===' -ForegroundColor Cyan
Write-Host "Radice repository: $repoRoot"
Write-Host "Cartella destinazione: $distDirectory"

if ($ForceVenv -and (Test-Path $venvPath)) {
    Write-Host 'Rimozione ambiente virtuale esistente...' -ForegroundColor Yellow
    Remove-Item -Recurse -Force $venvPath
}

if (-not (Test-Path $venvPath)) {
    Write-Host 'Creazione nuovo ambiente virtuale...' -ForegroundColor Cyan
    python -m venv $venvPath
}

if (-not (Test-Path $venvPython)) {
    throw 'Ambiente virtuale non valido: python.exe non trovato.'
}

Write-Host 'Aggiornamento pip...' -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip | Out-Null

Write-Host 'Installazione del progetto con dipendenze di build...' -ForegroundColor Cyan
$packageSpec = "${repoRoot}[build]"
& $venvPip install $packageSpec | Out-Null

try {
    $packageVersion = (& $venvPython -c "import trumetrapla; print(trumetrapla.__version__)" ).Trim()
} catch {
    Write-Warning 'Impossibile determinare la versione del pacchetto; uso 0.0.0 come fallback.'
    $packageVersion = '0.0.0'
}
if (-not $packageVersion) {
    $packageVersion = '0.0.0'
}
Write-Host "Versione pacchetto installata: $packageVersion" -ForegroundColor Cyan

$buildCommand = @('-m', 'trumetrapla.cli', 'build-exe', '--dist', $distDirectory)
if ($Portable) {
    $buildCommand += '--no-onefile'
}

Write-Host 'Generazione eseguibile TruMetraPla.exe...' -ForegroundColor Cyan
& $venvPython @buildCommand

$expectedExe = Join-Path $distDirectory 'TruMetraPla.exe'
if (Test-Path $expectedExe) {
    Write-Host "Eseguibile creato in: $expectedExe" -ForegroundColor Green
} else {
    Write-Warning "Eseguibile non trovato in $expectedExe. Verifica l'output del comando precedente."
}

if ($IncludeInstaller) {
    Write-Host 'Generazione installer grafico TruMetraPla...' -ForegroundColor Cyan
    $installerCommand = @('-m', 'trumetrapla.cli', 'build-installer', '--dist', $distDirectory)
    & $venvPython @installerCommand

    $installerPattern = Join-Path $distDirectory 'TruMetraPla_Setup_*.exe'
    $generatedInstaller = Get-ChildItem -Path $installerPattern -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($generatedInstaller) {
        Write-Host "Installer creato in: $($generatedInstaller.FullName)" -ForegroundColor Green
    } else {
        Write-Warning 'Verifica l\'output del comando precedente per eventuali errori NSIS.'
    }
}

Write-Host 'Operazione completata.' -ForegroundColor Cyan
