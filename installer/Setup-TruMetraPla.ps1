<#
.SYNOPSIS
    Automazione della build TruMetraPla per generare l'eseguibile Windows e, opzionalmente, l'installer NSIS.

.DESCRIPTION
    Lo script crea (o riutilizza) un ambiente virtuale isolato, installa il progetto con le dipendenze di build,
    esegue il comando CLI `trumetrapla build-exe` e, se richiesto, compila l'installer grafico tramite NSIS.

.PARAMETER Output
    Cartella di destinazione per l'eseguibile generato (default: cartella dist/ alla radice del repository).

.PARAMETER Portable
    Se specificato, disabilita la modalità onefile di PyInstaller e mantiene la cartella portabile.

.PARAMETER IncludeInstaller
    Se specificato, invoca makensis per produrre l'installer grafico utilizzando TruMetraPla-Installer.nsi.

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
    Write-Host 'Compilazione installer NSIS...' -ForegroundColor Cyan
    $makensis = Get-Command makensis -ErrorAction SilentlyContinue
    if (-not $makensis) {
        throw 'makensis non trovato nel PATH. Installa NSIS o aggiorna la variabile di ambiente.'
    }

    $installerScript = Join-Path $repoRoot 'installer' 'TruMetraPla-Installer.nsi'
    if (-not (Test-Path $installerScript)) {
        throw "Script NSIS non trovato: $installerScript"
    }

    & $makensis.Path $installerScript
    Write-Host 'Installer generato con successo.' -ForegroundColor Green
}

Write-Host 'Operazione completata.' -ForegroundColor Cyan
