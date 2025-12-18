#!/usr/bin/env pwsh

# Stop on error
$ErrorActionPreference = 'Stop'

# Check that conan is available
if (-not (Get-Command conan -ErrorAction SilentlyContinue)) {
    Write-Error "conan not found. Install Conan and ensure it's on PATH."
    exit 1
}

try {
    Write-Host "Running: conan install conan/ --build=missing --settings=build_type=Debug"
    conan install conan/ --build=missing --settings=build_type=Debug

    Write-Host "Running: conan install conan/ --build=missing --settings=build_type=Release"
    conan install conan/ --build=missing --settings=build_type=Release

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