$targetDir = "..\UnixScripts"

if (-not (Test-Path -Path $targetDir -PathType Container)) {
    Write-Host "The target directory does not exist."
    exit 1
}

Get-ChildItem -Path $targetDir | ForEach-Object {
    $file = $_.FullName
    Write-Host "Processing file: $file"

    # Read the content of the file and replace carriage return characters with empty strings
    $content = Get-Content -Path $file -Raw
    $content = $content -replace "\r", ""

    # Write the modified content back to the same file
    Set-Content -Path $file -Value $content -NoNewline
}

Write-Host "All carriage return characters removed from files in $targetDir."
Pause