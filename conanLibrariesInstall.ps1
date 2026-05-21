#!/usr/bin/env pwsh

# Stop on error
$ErrorActionPreference = 'Stop'

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "python not found. Install Python and ensure it's on PATH."
    exit 1
}

python -m venv .venv

$pip   = '.\.venv\Scripts\pip.exe'
$conan = '.\.venv\Scripts\conan.exe'

if (-not (Test-Path $pip)) {
    Write-Error "pip not found in .venv. The venv may not have been created correctly."
    exit 1
}

& $pip install --upgrade pip
& $pip install conan

if (-not (Test-Path $conan)) {
    Write-Error "conan not found in .venv after installation."
    exit 1
}

& $conan profile detect

try {
    Write-Host "Running: conan install conan/ --build=missing --settings=build_type=Debug"
    & $conan install conan/ --build=missing --settings=build_type=Debug

    Write-Host "Running: conan install conan/ --build=missing --settings=build_type=Release"
    & $conan install conan/ --build=missing --settings=build_type=Release

    Write-Host "Conan installs finished successfully."
}
catch {
    Write-Error "An error occurred while running conan: $_"
    exit 1
}

# Pause (interactive friendly)
if ($Host.Name -ne 'ServerRemoteHost') {
    Read-Host -Prompt "Press Enter to continue"
}
