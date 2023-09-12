$targetPaths = @(
    "..\UnixScripts",
    "..\..\conanLibrariesInstall.sh"
)

foreach ($targetPath in $targetPaths) {
    if (-not (Test-Path -Path $targetPath)) {
        Write-Host "The target path '$targetPath' does not exist."
        continue
    }

    if ((Get-Item $targetPath).PSIsContainer) {
        # Process a directory
        Get-ChildItem -Path $targetPath | ForEach-Object {
            $file = $_.FullName
            Write-Host "Processing file: $file"

            # Read the content of the file and replace carriage return characters with empty strings
            $content = Get-Content -Path $file -Raw
            $content = $content -replace "\r", ""

            # Write the modified content back to the same file without adding a newline at the end
            Set-Content -Path $file -Value $content -NoNewline
        }

        Write-Host "All carriage return characters removed from files in $targetPath."
    }
    else {
        # Process a single file
        $file = $targetPath
        Write-Host "Processing file: $file"

        # Read the content of the file and replace carriage return characters with empty strings
        $content = Get-Content -Path $file -Raw
        $content = $content -replace "\r", ""

        # Write the modified content back to the same file without adding a newline at the end
        Set-Content -Path $file -Value $content -NoNewline

        Write-Host "All carriage return characters removed from $file."
    }
}
Pause
