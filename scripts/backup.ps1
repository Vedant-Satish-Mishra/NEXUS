# NEXUS Data Backup Utility (Step 5.D.2)
# Archives SQLite/Postgres DB, Chroma vector store, and user uploads

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "data\backups"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

$archiveName = "$backupDir\nexus_backup_$timestamp.zip"
Write-Host "Creating NEXUS system backup: $archiveName" -ForegroundColor Cyan

$tempBackup = "$backupDir\temp_$timestamp"
New-Item -ItemType Directory -Path $tempBackup -Force | Out-Null

# 1. Copy SQLite database if exists
if (Test-Path "data\nexus.db") {
    Copy-Item "data\nexus.db" -Destination "$tempBackup\nexus.db"
    Write-Host "  Backed up SQLite database" -ForegroundColor Green
}

# 2. Copy Chroma vector store
if (Test-Path "data\chroma") {
    Copy-Item "data\chroma" -Destination "$tempBackup\chroma" -Recurse
    Write-Host "  Backed up ChromaDB vector indices" -ForegroundColor Green
}

# 3. Copy user uploads
if (Test-Path "data\uploads") {
    Copy-Item "data\uploads" -Destination "$tempBackup\uploads" -Recurse
    Write-Host "  Backed up user uploads" -ForegroundColor Green
}

# Compress into zip
Compress-Archive -Path "$tempBackup\*" -DestinationPath $archiveName -Force
Remove-Item -Path $tempBackup -Recurse -Force

Write-Host "Backup successfully created: $archiveName" -ForegroundColor Green
