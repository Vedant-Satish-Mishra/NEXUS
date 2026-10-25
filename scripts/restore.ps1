# NEXUS Data Restore Utility (Step 5.D.2)
# Restores data from a backup archive

param (
    [Parameter(Mandatory=$true)]
    [string]$BackupFile
)

if (-not (Test-Path $BackupFile)) {
    Write-Host "Backup file not found: $BackupFile" -ForegroundColor Red
    exit 1
}

Write-Host "Restoring NEXUS data from: $BackupFile" -ForegroundColor Cyan

$tempRestore = "data\temp_restore"
New-Item -ItemType Directory -Path $tempRestore -Force | Out-Null

Expand-Archive -Path $BackupFile -DestinationPath $tempRestore -Force

if (Test-Path "$tempRestore\nexus.db") {
    Copy-Item "$tempRestore\nexus.db" -Destination "data\nexus.db" -Force
    Write-Host "  Restored SQLite database" -ForegroundColor Green
}

if (Test-Path "$tempRestore\chroma") {
    Copy-Item "$tempRestore\chroma\*" -Destination "data\chroma" -Recurse -Force
    Write-Host "  Restored ChromaDB vectors" -ForegroundColor Green
}

if (Test-Path "$tempRestore\uploads") {
    Copy-Item "$tempRestore\uploads\*" -Destination "data\uploads" -Recurse -Force
    Write-Host "  Restored user uploads" -ForegroundColor Green
}

Remove-Item -Path $tempRestore -Recurse -Force
Write-Host "Restore complete!" -ForegroundColor Green
